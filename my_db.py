from sqlalchemy import ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from datetime import datetime

from config import USER, DATABASE, PASSWORD, HOST

DATABASE_URL = f"postgresql+asyncpg://{USER}:{PASSWORD}@{HOST}/{DATABASE}"

engine = create_async_engine(DATABASE_URL)
SessionLocal = async_sessionmaker(engine)

class Base(DeclarativeBase):
    pass

# Модель пользователя
class User(Base):
    __tablename__ = "users"

    userId: Mapped[int] = mapped_column(unique=True, primary_key=True)
    userName: Mapped[str] = mapped_column()
    attempts: Mapped[int] = mapped_column(default=5)
    subscribe_date: Mapped[datetime] = mapped_column(nullable=True)
    is_admin: Mapped[bool] = mapped_column(default=False)
    has_verse: Mapped[bool] = mapped_column(default=False)

    # Связь с чатами (Один ко многим)
    chats = relationship("Chat", back_populates="user", cascade="all, delete-orphan", lazy="selectin")
    # Связь с сообщениями (Один ко многим)
    messages = relationship("Message", back_populates="user", cascade="all, delete-orphan", lazy="selectin")
    # Связь с викторинами (Один ко многим)
    quizes = relationship("Quiz", back_populates="user", lazy="selectin", cascade="all, delete-orphan")

# Модель чата
class Chat(Base):
    __tablename__ = "chats"

    chatId: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(nullable=True)
    userId: Mapped[int] = mapped_column(ForeignKey("users.userId", ondelete="CASCADE"))

    # Связь с пользователем (Многие к одному)
    user = relationship("User", back_populates="chats", lazy="selectin")
    # Связь с сообщениями (Один ко многим)
    messages = relationship("Message", back_populates="chat", cascade="all, delete-orphan", lazy="selectin")

# Модель сообщения
class Message(Base):
    __tablename__ = "messages"

    message_id: Mapped[int] = mapped_column(primary_key=True)
    text: Mapped[str] = mapped_column()
    is_bot: Mapped[bool] = mapped_column()
    userId: Mapped[int] = mapped_column(ForeignKey("users.userId", ondelete="CASCADE"))
    chatId: Mapped[int] = mapped_column(ForeignKey("chats.chatId", ondelete="CASCADE"))

    # Связь с пользователем (Многие к одному)
    user = relationship("User", back_populates="messages", lazy="selectin")
    # Связь с чатом (Многие к одному)
    chat = relationship("Chat", back_populates="messages", lazy="selectin")

# Модель викторины
class Quiz(Base):
    __tablename__ = "ai_quizes"

    id: Mapped[int] = mapped_column(primary_key=True)
    userId: Mapped[int] = mapped_column(ForeignKey("users.userId", ondelete="CASCADE"))
    topic: Mapped[str] = mapped_column()
    points: Mapped[int] = mapped_column(default=0)
    max_points: Mapped[int] = mapped_column(nullable=True)
    title: Mapped[str] = mapped_column(nullable=True)

    # Связь с пользователем (Многие к одному)
    user = relationship("User", back_populates="quizes", lazy="selectin")
    # Связь с вопросами (Один ко многим)
    questions = relationship("Question", back_populates="quiz", lazy="selectin", cascade="all, delete-orphan")

# Модель вопроса
class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(primary_key=True)
    question: Mapped[str] = mapped_column()
    quiz_id: Mapped[int] = mapped_column(ForeignKey("ai_quizes.id", ondelete="CASCADE"))
    answered: Mapped[bool] = mapped_column(default=False)

    # Связь с викториной (Многие к одному)
    quiz = relationship("Quiz", back_populates="questions", lazy="selectin")
    # Связь с ответами (Один ко многим)
    answers = relationship("Answer", back_populates="question", lazy="selectin", cascade="all, delete-orphan")

# Модель ответа
class Answer(Base):
    __tablename__ = "answers"

    id: Mapped[int] = mapped_column(primary_key=True)
    answer: Mapped[str] = mapped_column()
    is_true: Mapped[bool] = mapped_column(default=False)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id", ondelete="CASCADE"))

    # Связь с вопросом (Многие к одному)
    question = relationship("Question", back_populates="answers", lazy="selectin")

# Получение сессии
async def get_db():
    async with SessionLocal() as db:
        yield db