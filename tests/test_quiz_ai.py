from ai_dir.ai import QuizAi
from .qdrant_db import QdrantTesting
from .test_bible_chat import has_no_english_letters

import pytest

qdrant = QdrantTesting()
COLLECTION_NAME = "quiz_questions"

def assert_questions_answers(questions_answers: dict, has_prev: bool = False):
    prev_questions_per_loop = []
    for quiz_question, answers in questions_answers.items():
        assert has_no_english_letters(quiz_question), f"Вопрос содержит английские буквы: {quiz_question}"
        if has_prev:
            assert not qdrant.search_data(quiz_question, COLLECTION_NAME), f"Есть вопросы похожие с этим: {quiz_question}"
        prev_questions_per_loop.append(quiz_question)
        for answer, _ in answers.items():
            assert has_no_english_letters(answer), f"Ответ содержит английские буквы: {answer}"
    return prev_questions_per_loop

@pytest.mark.asyncio
async def test_quiz_ai():
    topic = "Новый Завет"
    title, quiz = await QuizAi.makeQuizAi(6, topic, [])
    questions_answers_from_bot = quiz.get(topic)

    prev_questions = assert_questions_answers(questions_answers_from_bot)

    prev_questions = [" ".join(question.split()[1:]) for question in prev_questions]

    qdrant.create_collection(COLLECTION_NAME, prev_questions)
    qdrant.insert_data(COLLECTION_NAME, prev_questions)
    
    title, prev_questions_quiz = await QuizAi.makeQuizAi(6, topic, prev_questions)
    get_quiz_with_prev_questions = prev_questions_quiz.get(topic)

    assert_questions_answers(get_quiz_with_prev_questions, True)