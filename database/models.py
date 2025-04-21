from sqlalchemy import ForeignKey, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.database import Base

from typing import Annotated, Optional
from datetime import datetime

def_false_an = Annotated[bool, mapped_column(default=False)]
pk_an = Annotated[int, mapped_column(primary_key=True)]

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    userName: Mapped[str]
    attempts: Mapped[int] = mapped_column(default=5)
    passed_quizes: Mapped[Optional[int]]
    subscribe_date: Mapped[Optional[datetime]]
    is_admin: Mapped[def_false_an]

    # Правильные связи с каскадом и корректным back_populates
    chats: Mapped[list["Chat"]] = relationship(
        "Chat",
        back_populates="user",  # Исправлено с "chats"
        cascade="all, delete-orphan"
    )
    messages: Mapped[list["Message"]] = relationship(
        "Message",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    quizes: Mapped[list["Quiz"]] = relationship(
        "Quiz",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    daily_verse: Mapped["DailyVerse"] = relationship(
        "DailyVerse",
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False
    )
    passed_questions: Mapped[list["PassedQuestions"]] = relationship(
        "PassedQuestions",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    banned: Mapped["BannedUser"] = relationship(
        "BannedUser",
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False
    )

class Chat(Base):
    __tablename__ = "chats"

    id: Mapped[pk_an]
    title: Mapped[Optional[str]]
    userId: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))

    user: Mapped["User"] = relationship("User", back_populates="chats")
    messages: Mapped[list["Message"]] = relationship(
        "Message",
        back_populates="chat",
        cascade="all, delete-orphan"
    )

class Message(Base):
    __tablename__ = "messages"

    id: Mapped[pk_an]
    text: Mapped[str]
    is_bot: Mapped[bool] = mapped_column(default=False)
    userId: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    chatId: Mapped[int] = mapped_column(ForeignKey("chats.id", ondelete="CASCADE"))

    user: Mapped["User"] = relationship("User", back_populates="messages")
    chat: Mapped["Chat"] = relationship("Chat", back_populates="messages")

def_points_an = Annotated[Optional[int], mapped_column(default=0)]

class Quiz(Base):
    __tablename__ = "ai_quizes"

    id: Mapped[pk_an]
    userId: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    topic: Mapped[Optional[str]]
    points: Mapped[def_points_an]
    max_points: Mapped[def_points_an]
    title: Mapped[Optional[str]]

    user: Mapped["User"] = relationship("User", back_populates="quizes")
    questions: Mapped[list["Question"]] = relationship(
        "Question",
        back_populates="quiz",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

class Question(Base):
    __tablename__ = "questions"

    id: Mapped[pk_an]
    question: Mapped[str]
    answered: Mapped[bool] = mapped_column(default=False)
    quiz_id: Mapped[int] = mapped_column(ForeignKey("ai_quizes.id", ondelete="CASCADE"))

    quiz: Mapped["Quiz"] = relationship("Quiz", back_populates="questions")
    answers: Mapped[list["Answer"]] = relationship(
        "Answer",
        back_populates="question",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

class Answer(Base):
    __tablename__ = "answers"

    id: Mapped[pk_an]
    answer: Mapped[str]
    is_true: Mapped[bool] = mapped_column(default=False)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id", ondelete="CASCADE"))

    question: Mapped["Question"] = relationship("Question", back_populates="answers")

class DailyVerse(Base):
    __tablename__ = "daily_verse"

    title: Mapped[str]
    verse: Mapped[str]
    userId: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))

    user: Mapped["User"] = relationship("User", back_populates="daily_verse")

class PassedQuestions(Base):
    __tablename__ = "passed_questions"

    question_name: Mapped[str] = mapped_column(unique=True)
    userId: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))

    user: Mapped["User"] = relationship("User", back_populates="passed_questions")

class BannedUser(Base):
    __tablename__ = "banned_users"

    userId: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))

    user: Mapped["User"] = relationship("User", back_populates="banned")

def get_db():
    Base.metadata.create_all()

def drop_db():
    Base.metadata.drop_all()