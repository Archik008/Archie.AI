from sqlalchemy import select, update, and_
from sqlalchemy.orm import selectinload
from database.database import get_db
from fastapi import Depends, HTTPException, Header, status
from database.models import *
from configure.pyconfig import WHITE_LIST, ADMINS_LIST
from ai_dir.ai import QuizAi, BibleChatAi
from encryption.encrypt import is_safe
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_models.schemas import AnswerQuestionClass

from datetime import timedelta

import random

class DAOModel:

    @staticmethod
    async def verifyUser(init_data: str, db: AsyncSession):
        if not init_data:
            return {"status": "missing"}
                        
        is_valid, userId = is_safe(init_data)

        if is_valid and not await DAOModel.search_banned_user(userId, db):
            return {"userId": userId, "status": "valid"}
        
        return {"status": "invalid"}
    
    @staticmethod
    async def search_banned_user(userId, db: AsyncSession):
        search_user = await db.execute(select(BannedUser).filter(BannedUser.userId == userId))
        user = search_user.scalar_one_or_none()

        if not user: 
            return
        
        return True
    
    @staticmethod
    async def add_banned_users(userIds: list, db: AsyncSession):
        for userId in userIds:
            cur_user = await DAOModel.search_banned_user(userId, db)
            if not cur_user:
                new_banned_user = BannedUser(userId=userId)
                db.add(new_banned_user)
                await db.flush()
        else:
            await db.commit()

    @staticmethod
    async def is_user_exists(userId: int, db: AsyncSession):
        user = await db.execute(select(User).where(User.id == userId))
        result_user = user.scalars().first()
        if result_user:
            return True
        
    @staticmethod
    async def get_date_subscribe(userId: int, db: AsyncSession):
        date_search = await db.execute(select(User.subscribe_date).filter(User.id == userId))
        result_date = date_search.scalar_one_or_none()
        if not result_date:
            return result_date
        return result_date.date()
    
    @staticmethod
    async def is_premium(userId: int, db: AsyncSession):
        result_date = await DAOModel.get_date_subscribe(userId, db)
        if result_date:
            return True
        
    @staticmethod
    async def is_subscribed(userId: int, db: AsyncSession):
        result_date = await DAOModel.get_date_subscribe(userId, db)

        now_date = datetime.now().date()

        if result_date and result_date >= now_date:
            return True
        
    @staticmethod
    async def get_attempts(userId, db: AsyncSession):
        result_user = await db.execute(select(User.attempts).where(User.id == userId))
        user_attempts = result_user.unique().scalar_one()
        return user_attempts
    
    @staticmethod
    async def update_attempts_db(userId, attempts, db: AsyncSession):
        await db.execute(update(User).where(User.id == userId).values(attempts=attempts))
        await db.commit()

    @staticmethod
    async def update_user_attempts(userId, db: AsyncSession):
        search_user = await db.execute(select(User).filter(User.id == userId))
        user = search_user.scalar_one_or_none()
        if not user:
            raise HTTPException(404)
        
        cur_date = datetime.now().date()
        
        if cur_date > user.updated_at.date():
            user.attempts = 5
            await db.commit()

    @staticmethod 
    async def allow_not_premium_using(userId, db: AsyncSession):
        if userId in WHITE_LIST:
            return True
        attempts = await DAOModel.get_attempts(userId, db)
        premium_user = await DAOModel.is_premium(userId, db)
        if attempts <= 0 or premium_user:
            return 
        return True
    
    @staticmethod
    async def subscribe_db(userId, db: AsyncSession):
        user_search = await db.execute(select(User).filter(User.id == userId))
        user = user_search.scalar_one_or_none()
        if not user:
            raise HTTPException(404)
        
        if not user.subscribe_date:
            user.subscribe_date = datetime.now().date()
        
        user.subscribe_date += timedelta(days=31)
        await db.commit()

    @staticmethod
    async def start_verifying(init_data: str = Header(...), db: AsyncSession = Depends(get_db)):
        result_verify = await DAOModel.verifyUser(init_data, db)

        if result_verify['status'] == 'invalid':
            raise HTTPException(status.HTTP_406_NOT_ACCEPTABLE, "Not allowed. God bless you!")
        elif result_verify['status'] == 'missing':
            raise HTTPException(404, "Missing important data! >:(")
        
        userId = result_verify['userId']

        return userId
    
    @staticmethod
    async def get_passed_questions(userId, db: AsyncSession):
        questions_search = await db.execute(select(PassedQuestions.question_name).filter(PassedQuestions.userId == userId))
        results_questions = questions_search.scalars().all()
        return results_questions
    
    @staticmethod
    async def make_quiz(userId, topic, db: AsyncSession):
        my_points = 6

        prev_questions = await DAOModel.get_passed_questions(userId, db)
    
        prev_questions = [" ".join(question.split()[1:]) for question in prev_questions]

        quiz_title, questions_answers = await QuizAi.makeQuizAi(my_points, topic, prev_questions)

        new_quiz = Quiz(
            userId=userId,
            topic=topic,
            max_points=my_points,
            title=quiz_title
        )

        db.add(new_quiz)

        await db.flush()

        dict_question_answers = None
        
        # Проход по вопросам выбранной темы
        quiz_questions = questions_answers.get(topic, {})

        for quiz_question, answers in quiz_questions.items():
            question = Question(question=quiz_question, quiz_id=new_quiz.id)
            passed_question = PassedQuestions(userId=userId, question_name=quiz_question)
            db.add(question)
            db.add(passed_question)

            await db.flush()

            if not dict_question_answers:
                question_pare = {"question": {"text": question.question, "id": question.id}, "answers": []}

            for answer, is_true in answers.items():
                new_answer = Answer(answer=answer, is_true=is_true, question_id=question.id)
                db.add(new_answer)
                await db.flush()

                if not dict_question_answers:
                    question_pare["answers"].append({"text": answer, "id": new_answer.id})

            if not dict_question_answers:
                dict_question_answers = question_pare

        new_quiz.max_points = my_points

        await db.flush()

        dict_question_answers['quiz_id'] = new_quiz.id

        await db.commit()

        return dict_question_answers
    
    @staticmethod
    async def get_quizes_db(userId, db: AsyncSession):
        search_quizes = await db.execute(select(Quiz).filter(Quiz.userId == userId).options(selectinload(Quiz.questions)))
        result_quizes = search_quizes.scalars().all()

        ls_quiz = [{"id": quiz.id, "title": quiz.title, "points": quiz.points, "max_points": quiz.max_points} for quiz in result_quizes if quiz.points != quiz.max_points and any(not question.answered for question in quiz.questions)]
        
        return ls_quiz
    
    @staticmethod
    async def get_caption(userId, userText, db: AsyncSession):
        if not await DAOModel.is_premium(userId, db) and userId not in WHITE_LIST:
            return
        
        listCaptions = ['Как довериться Богу', "Заповедь Божья", "Вера в Бога"]

        caption = random.choice(listCaptions)

        return caption

    @staticmethod
    async def minus_attempts(userId, db: AsyncSession):
        allowed_using = await DAOModel.allow_not_premium_using(userId, db)
        if not allowed_using:
            raise HTTPException(403, {"status": "not allowed"})
        attempts = await DAOModel.get_attempts(userId, db)
        attempts -= 1
        await DAOModel.update_attempts_db(userId, attempts, db)

    @staticmethod
    async def get_last_msg(userId, chatId, db: AsyncSession):
        user_msg_search = await db.execute(select(Message).filter(Message.userId == userId, Message.chatId == chatId))
        result_msg = user_msg_search.scalars().all()
        result_msgs = list(result_msg)
        result_msgs.sort(key=lambda msg: msg.id)
        if len(result_msgs) == 0:
            return
        return result_msgs[-1]

    @staticmethod
    async def get_question_answers_unanswered(userId, quizId, db: AsyncSession):
        q_a_search = await db.execute(
            select(Question)
            .filter(
                Question.quiz_id == quizId,
                ~Question.answered,
                Question.quiz.has(Quiz.userId == userId)  # Оптимизированная проверка связи
            )
            .options(selectinload(Question.answers))  # Ленивая загрузка ответов
        )

        result = q_a_search.scalars().first()

        if not result:
            raise HTTPException(404, "not found question")
                
        return result, result.answers

    @staticmethod
    async def is_quiz_answered(userId, quizId, db: AsyncSession):
        questions_search = await db.execute(select(Question).join(Quiz).where(and_(Question.quiz_id == quizId, Quiz.userId == userId)))
        result_questions = questions_search.scalars().all()
        if len(result_questions) == 0:
            raise HTTPException(404, "not found")
        
        is_passed = all(question.answered for question in result_questions)

        return is_passed

    @staticmethod
    async def get_quiz_db(userId, quizId, db: AsyncSession):
        result_question, result_answers = await DAOModel.get_question_answers_unanswered(userId, quizId, db)

        quiz_search = await db.execute(select(Quiz).where(Quiz.id == quizId))
        result_quiz = quiz_search.scalars().first()

        if not result_quiz:
            raise HTTPException(404, "not found quizes")
        
        return {"answers": [{"id": answer.id, "text": answer.answer} for answer in result_answers], "question": {"text": result_question.question, "id": result_question.id}, "quiz": {"points": result_quiz.points, "max_points": result_quiz.max_points}}
    
    @staticmethod
    async def answer_question_db(user, params: AnswerQuestionClass, db: AsyncSession):
        quiz_search = await db.execute(select(Quiz).where(and_(Quiz.userId == user, Quiz.id == params.quiz_id)))
        result_quiz = quiz_search.scalars().first()

        if not result_quiz:
            raise HTTPException(404, "not found quiz")

        q_a_search = await db.execute(
            select(Question)
            .filter(
                Question.quiz_id == params.quiz_id,
                Question.id == params.question_id,
                ~Question.answered,
                Question.quiz.has(Quiz.userId == user)
            )
            .options(selectinload(Question.answers))
        )

        result_search = q_a_search.scalars().all()

        if len(result_search) == 0:
            raise HTTPException(404, "not found question")

        question = result_search[0]

        for answer in question.answers:
            if answer.id == params.answer_id and answer.is_true:
                result_quiz.points += 1
                await db.flush()
                break

        question.answered = True

        await db.flush()
        
        await db.commit()

        return {"correct_answers": [{"id": answer.id} for answer in question.answers if answer.is_true], "quiz": {"points": result_quiz.points, "max_points": result_quiz.max_points}}
    
    @staticmethod
    async def get_new_daily_verse(userId, db: AsyncSession):
        async def add_new_user_verse_model(daily_verse, verse_title):
            new_daily_verse_user = DailyVerse(verse=daily_verse, title=verse_title, userId=userId)
            db.add(new_daily_verse_user)
            return new_daily_verse_user

        verse_model_search = await db.execute(select(DailyVerse).filter(DailyVerse.userId == userId))
        verse_model = verse_model_search.scalars().first()
        now_date = datetime.now().date()

        if not verse_model:
            verse, verse_title = await BibleChatAi.getDailyVerse()
            verse_model = await add_new_user_verse_model(verse, verse_title)
        elif verse_model.updated_at and verse_model.updated_at.date() < now_date:
            verse, verse_title = BibleChatAi.getDailyVerse()
            verse_model.verse = verse
            verse_model.title = verse_title
            await db.flush()
        else:
            return {"has_seen": True}
        
        await db.commit()

        return {"daily_verse": {"title": verse_model.title, "verse": verse_model.verse}}
    
    @staticmethod
    async def get_users(db: AsyncSession):
        users_search = await db.execute(select(User.id).where(User.id.not_in(ADMINS_LIST)))
        if len(ADMINS_LIST) < 1:
            users_search = await db.execute(select(User.id))
        users = users_search.scalars().all()
        return users


class ContextMessage:
    def __init__(self, text, is_bot):
        self.text = text
        self.is_bot = is_bot