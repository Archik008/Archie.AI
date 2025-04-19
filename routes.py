from fastapi import APIRouter

from fastapi import Depends, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from openai import RateLimitError

from sqlalchemy import select, update, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession

from database import *
from fastapi_models import *
from models import *
from schemas import *

from user_funcs import *

from pyconfig import ADMIN_ID, WHITE_LIST, AI_TEST_TOPICS, PASSWORD

from bot import create_invoice_link_bot
from ai import BibleChatAi

router = APIRouter()

class InfoUserException(HTTPException):
    def __init__(self, status_code, detail, title):
        super().__init__(status_code, detail)
        self.title = title

class InfoUserModel(BaseModel):
    status_code: int
    title: str
    detail: str

@router.exception_handler(InfoUserException)
async def wrap_info_user_exc(request, exc: InfoUserException):
    exception = jsonable_encoder(InfoUserModel(status_code=exc.status_code, title=exc.title, detail=exc.detail))
    return JSONResponse(status_code=exc.status_code, content=exception)

@router.post("/verify")
async def verifying(params: VerifyingUrl):
    return await UserMethods.verifyUser(params.init_data)

@router.post("/new_user")
async def add_new_user(user: NewUser, userId: int = Depends(UserMethods.start_verifying), db: AsyncSession = Depends(get_db)):
    isAdmin = False

    if user and userId == ADMIN_ID:
        isAdmin = True

    new_user = User(
        id=userId,
        userName=user.username,
        is_admin=isAdmin
        )
    
    db.add(new_user)

    await db.commit()
    await db.refresh(new_user)

    return {"username": new_user.userName, "attempts": new_user.attempts}

@router.get("/isNewUser")
async def checkUser(userId: int = Depends(UserMethods.start_verifying), db: AsyncSession = Depends(get_db)):
    is_exists = await UserMethods.is_user_exists(userId, db)
    if not is_exists:
        return {"is_new": True}
    return {"is_new": False}
    
@router.get("/user")
async def returnUserData(userId: int = Depends(UserMethods.start_verifying), db: AsyncSession = Depends(get_db)):
    user = await db.execute(select(User).where(User.id == userId))
    result = user.scalar_one_or_none()

    await UserMethods.update_user_attempts(userId, db)

    if result:
        return {"username": result.userName, "attempts": result.attempts}
    
    raise HTTPException(404)

@router.put("/new_username")
async def setNewName(newName: NameRequest, userId: int = Depends(UserMethods.start_verifying), db: AsyncSession = Depends(get_db)):
    await db.execute(update(User).where(User.id == userId).values(userName=newName.newName))
    await db.commit()
    return {"status": "ok"}

@router.get("/messages")
async def getMessages(chat_id: int, userId: int = Depends(UserMethods.start_verifying), db: AsyncSession = Depends(get_db)):
    if not await UserMethods.is_premium(userId, db) and userId not in WHITE_LIST:
        return HTTPException(403, "not allowed")

    messages = await db.execute(select(Message).filter(Message.chatId == chat_id, Message.userId == userId))
    results = messages.scalars().all()

    return [{"id": message.id, "text": message.text, "is_bot": message.is_bot} for message in results]

@router.get("/chats")
async def getChats(userId: int = Depends(UserMethods.start_verifying), db: AsyncSession = Depends(get_db)):
    if not await UserMethods.is_subscribed(userId, db) and userId not in WHITE_LIST:
        return []

    chats = await db.execute(select(Chat).where(Chat.userId == userId))
    results = chats.scalars().all()
    return [{"id": chat.id, "title": chat.title} for chat in results]

@router.post("/sendMsg")
async def sendMsg(msg_data: NewMessage, userId: int = Depends(UserMethods.start_verifying), db: AsyncSession = Depends(get_db)):
    is_exists = await UserMethods.is_user_exists(userId, db)
    if not is_exists:
        raise HTTPException("no user!", 404)
    
    is_subscribed = await UserMethods.is_subscribed(userId, db)
    if not userId in WHITE_LIST and not is_subscribed:
        await UserMethods.update_user_attempts(userId, db)
        await UserMethods.minus_attempts(userId, db)

    cur_chat_id = msg_data.chatId

    # 🛠 Ищем чат в БД
    chat = await db.get(Chat, cur_chat_id)

    if cur_chat_id == -1 or not chat:
        new_chat = Chat(userId=userId)  
        db.add(new_chat)
        await db.flush()
        cur_chat_id = new_chat.id

    # 🛠 Создаем сообщение, используя существующий или новый chatId
    msg = Message(userId=userId, chatId=cur_chat_id, text=msg_data.text.strip(), is_bot=msg_data.is_bot)
    db.add(msg)
    await db.flush()

    await db.commit()

    return {
        "user": {"is_bot": msg.is_bot, "text": msg.text, "id": msg.id},
        "chat": {"id": cur_chat_id}
    }

@router.get("/chat")
async def set_chat_title(chat_id: int, user_msg: str, userId: int  = Depends(UserMethods.start_verifying), db: AsyncSession = Depends(get_db)):
    if not await UserMethods.is_subscribed(userId, db) and userId not in WHITE_LIST:
        raise HTTPException(status.HTTP_426_UPGRADE_REQUIRED, "нельзя!!")
    chat_search = await db.execute(select(Chat).filter(Chat.userId == userId, Chat.id == chat_id))
    result = chat_search.scalar_one_or_none()

    if not result:
        raise HTTPException(404)
    
    if not result.title:
        try:
            chat_title = BibleChatAi.setTitleChat(user_msg)
        except RateLimitError:
            raise InfoUserException(status_code=500, detail="Превышен лимит запросов или закончилась квота. Отправь эту ошибку нам в чат.", title="Лимит запросов")
        except Exception as e:
            raise InfoUserException(status_code=501, detail=f"Неизвестная ошибка: {e}. Отправь скриншот ошибки в наш телеграм чат", title="Неизвестная ошибка")

        result.title = chat_title

        await db.commit()

    return result

@router.get("/botMsg")
async def getBotMsg(chat_id: int, userId: int = Depends(UserMethods.start_verifying), db: AsyncSession = Depends(get_db)):
    last_msg = await UserMethods.get_last_msg(userId, chat_id, db)

    if not last_msg or last_msg.is_bot:
        raise HTTPException(406, "Not allowed using")
        
    message_search = await db.execute(select(Message).where(and_(Message.userId == userId, Message.chatId == chat_id)))

    results = message_search.scalars().all()

    results = results[:5] if not (await UserMethods.allow_not_premium_using(userId, db) or await UserMethods.is_premium(userId, db)) else results

    if len(results) == 0:
        raise HTTPException(403, "Not allowed using")
    
    context_msgs = [ContextMessage(message.text, message.is_bot) for message in results]

    username_search = await db.execute(select(User.userName).filter(User.id == userId))
    username = username_search.scalar_one()

    try:
        bot_msg_text = BibleChatAi.askBibleChat(last_msg.text, context_msgs, username)
    except RateLimitError:
        raise InfoUserException(status_code=500, detail="Превышен лимит запросов или закончилась квота. Отправь скриншот нам в чат", title="Лимит запросов")
    except Exception as e:
        raise InfoUserException(status_code=501, detail=f"Неизвестная ошибка: {e}. Отправь скриншот ошибки в наш телеграм чат", title="Неизвестная ошибка")

    msg = Message(userId=userId, chatId=chat_id, text=bot_msg_text, 
                is_bot=True)
    
    db.add(msg)
    await db.commit()
    await db.refresh(msg)

    return {"is_bot": msg.is_bot, "text": msg.text, "id": msg.id}

@router.get("/subscribed")
async def is_premium_endpoint(userId: int = Depends(UserMethods.start_verifying), db: AsyncSession = Depends(get_db)):
    premium_user = await UserMethods.is_premium(userId, db)

    if premium_user:
        return {"status": True}
    
    return {"status": False}

@router.put("/changeChat")
async def changeChat(params: ChangeChat, userId: int = Depends(UserMethods.start_verifying), db: AsyncSession = Depends(get_db)):
    if not await UserMethods.is_premium(userId, db) and userId not in WHITE_LIST:
        raise HTTPException(404, "restricted")

    await db.execute(update(Chat).where(Chat.id == params.chat_id and Chat.userId == userId).values(title=params.new_text))
    await db.commit()
    return {"status": 200}

@router.delete("/deleteChat")
async def deleteChat(chatId: int, userId: int = Depends(UserMethods.start_verifying), db: AsyncSession = Depends(get_db)):
    if not await UserMethods.is_premium(userId, db) and userId not in WHITE_LIST:
        raise HTTPException(404, "restricted")

    await db.execute(delete(Chat).filter(Chat.id == chatId, Chat.userId == userId))
    await db.commit()
    return {"status": 200}

@router.delete("/clearMsgs")
async def deletingChatsMsg(userId: int = Depends(UserMethods.start_verifying), db: AsyncSession = Depends(get_db)):
    if await UserMethods.is_premium(userId, db) or userId in WHITE_LIST:
        raise HTTPException(status.HTTP_406_NOT_ACCEPTABLE, "subscribers not allowed to clear!")

    await db.execute(delete(Chat).filter(Chat.userId == userId))
    await db.execute(delete(Message).filter(Message.userId == userId))
    await db.commit()

    return {"status": "cleared"}

@router.get("/topics")
async def get_topics(user: int = Depends(UserMethods.start_verifying), db: AsyncSession = Depends(get_db)):
    if not await UserMethods.is_user_exists(user, db):
        raise HTTPException(403, "not allowed")
    return {"topics": AI_TEST_TOPICS}

class PostQuiz(BaseModel):
    topic: str

@router.post("/quiz")
async def create_quiz(params: PostQuiz, user: int = Depends(UserMethods.start_verifying), db: AsyncSession = Depends(get_db)):
    is_exists = await UserMethods.is_user_exists(user, db)
    if not is_exists:
        raise HTTPException(404)
    
    try:
        new_quiz = await UserMethods.make_quiz(user, params.topic, db)
    except RateLimitError:
        raise InfoUserException(status_code=500, detail="Превышен лимит запросов или закончилась квота. Отправь скриншот ошибки нам в чат", title="Лимит запросов")
    except Exception as e:
        raise InfoUserException(status_code=501, detail=f"Неизвестная ошибка: {e}. Отправь скриншот ошибки в наш телеграм чат", title="Неизвестная ошибка")
    
    is_subscribed  = await UserMethods.is_subscribed(user, db)
    if not user in WHITE_LIST and not is_subscribed:
        await UserMethods.update_user_attempts(user, db)
        await UserMethods.minus_attempts(user, db)

    return new_quiz

@router.get("/quiz")
async def get_quiz(quiz_id: int, user: int = Depends(UserMethods.start_verifying), db: AsyncSession = Depends(get_db)):
    question_data = await UserMethods.get_quiz_db(user, quiz_id, db)
    return question_data
    
@router.post("/answer")
async def answer_question(params: AnswerQuestionClass, user: int = Depends(UserMethods.start_verifying), db: AsyncSession = Depends(get_db)):
    correct_answers = await UserMethods.answer_question_db(user, params, db)
    return correct_answers

@router.get("/next_question")
async def get_next_question(quiz_id: int, user: int = Depends(UserMethods.start_verifying), db: AsyncSession = Depends(get_db)):
    is_passed_quiz = await UserMethods.is_quiz_answered(user, quiz_id, db)

    if is_passed_quiz:
        user_search = await db.execute(select(User).filter(User.id == user))
        user_result = user_search.scalar_one()

        if not user_result.passed_quizes:
            user_result.passed_quizes = 0

        user_result.passed_quizes += 1

        await db.flush()

        await db.execute(delete(Quiz).filter(Quiz.userId == user, Quiz.id == quiz_id))

        await db.commit()

        return {"ended": True}
    
    question, answers = await UserMethods.get_question_answers_unanswered(user, quiz_id, db)

    return {"question": {"id": question.id, "text": question.question}, "answers": [{"id": answer.id, "text": answer.answer} for answer in answers]}

@router.get("/quizes")
async def get_quizes(user: int = Depends(UserMethods.start_verifying), db: AsyncSession = Depends(get_db)):
    quizes = await UserMethods.get_quizes_db(user, db)
    return quizes

@router.get("/user_quiz")
async def get_user_quiz_data(user_id: int = Depends(UserMethods.start_verifying), db: AsyncSession = Depends(get_db)):
    search_user = await db.execute(select(User).filter(User.id == user_id))
    user_data = search_user.scalars().first()
    if not user_data:
        raise HTTPException(404, "not found user")
    
    username, passed_tests = user_data.userName, user_data.passed_quizes

    if not passed_tests:
        passed_tests = 0
    
    return {"user_name": username, "passed_tests": passed_tests}

class EditQuizBody(BaseModel):
    quiz_id: int
    quiz_name: str

@router.put("/quiz_name")
async def get_quiz_name(params: EditQuizBody, user_id: int = Depends(UserMethods.start_verifying), db: AsyncSession = Depends(get_db)):
    search_quiz = await db.execute(select(Quiz).filter(Quiz.id == params.quiz_id, Quiz.userId == user_id))
    quiz_obj = search_quiz.scalars().first()

    if not quiz_obj:
        raise HTTPException(404, "not found quiz")
    
    quiz_obj.title = params.quiz_name
    await db.commit()

    return {"title": quiz_obj.title}

@router.delete("/quiz")
async def delete_quiz(quiz_id: int, user_id: int = Depends(UserMethods.start_verifying), db: AsyncSession = Depends(get_db)):
    await db.execute(delete(Quiz).filter(Quiz.id == quiz_id, Quiz.userId == user_id))
    await db.commit()
    return {"message": "quiz deleted"}
    
@router.get("/daily_verse")
async def get_daily_verse(user_id: int = Depends(UserMethods.start_verifying), db: AsyncSession = Depends(get_db)):
    try:
        getting_daily_verse = await UserMethods.get_new_daily_verse(user_id, db)
    except RateLimitError:
        raise InfoUserException(status_code=500, detail="Превышен лимит запросов или закончилась квота. Отправь скриншот ошибки нам в чат.", title="Лимит запросов")
    except Exception as e:
        raise InfoUserException(status_code=501, detail=f"Неизвестная ошибка: {e}. Отправь скриншот ошибки в наш телеграм чат", title="Неизвестная ошибка")
    return getting_daily_verse

@router.get("/get_invoice")
async def get_payment_invoice():
    invoice_link = await create_invoice_link_bot()
    return {"pay_link": invoice_link}

@router.get("/in_whiteList")
async def is_user_in_whitelist(user_id: int = Depends(UserMethods.start_verifying)):
    if user_id in WHITE_LIST:
        return {"status": True}
    return {"status": False}

class BanUserClass(BaseModel):
    password: str
    list_users: list

@router.post("/ban")
async def ban_user(params: BanUserClass, db: AsyncSession = Depends(get_db)):
    if params.password != PASSWORD:
        raise HTTPException(status_code=status.HTTP_418_IM_A_TEAPOT, detail="Доступ запрещен!!")
    await UserMethods.add_banned_users(params.list_users, db)
    return {"ok": True}