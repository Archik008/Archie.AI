from aiogram import Router, Dispatcher, Bot, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo, Message, LabeledPrice
from aiogram.filters import Command

from fastapi import FastAPI
from contextlib import asynccontextmanager

from texts import *

from pyconfig import URL, MAIN_BOT_TOKEN


bot = Bot(MAIN_BOT_TOKEN)
my_router = Router()
dp = Dispatcher()

dp.include_router(my_router)

async def create_invoice_link_bot():
   payment_link = await bot.create_invoice_link(
       "Подписка",
       "Ежемесячная подписка 100 stars",
       "{}",
       "XTR",
       prices=[LabeledPrice(label="Подписка", amount=100)]
   )
   return payment_link

@asynccontextmanager
async def lifespan(app: FastAPI):
    url_webhook = f"{URL}/webhook"
    await bot.set_webhook(url=url_webhook,
                          allowed_updates=dp.resolve_used_update_types(),
                          drop_pending_updates=True)
    yield
    await bot.delete_webhook()

@my_router.pre_checkout_query(lambda query: True)
async def pre_checkout_query(pre_checkout_q: types.PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_q.id, ok=True)

hello_user = """Приветствую тебя в проекте <b>Archie.AI</b>!
Здесь ты можешь попробовать:
- <b>Библейский чат-бот</b>. Обученный бот на основе Chatgpt, готовый помочь и поддержать тебя Библейским советом, а также поможет изучить тебе Слово Божье!
- <b>ИИ генератор викторин</b>. Тоже бот, но уже обученный создавать викторины. Прокачать знания по Библии здесь ты точно сможешь!"""

@my_router.message(Command("start"))
async def answerWebApp(msg: Message):
    bot_url = f"{URL}/bot"  # Ссылка на ваше веб-приложение
    bible_ai_button = InlineKeyboardButton(
        text="Библейский бот",
        web_app=WebAppInfo(url=bot_url)
    )

    quiz_url = f"{URL}/quizes_app"
    quiz_ai_button = InlineKeyboardButton(
        text="ИИ викторина",
        web_app=WebAppInfo(url=quiz_url)
    )

    # Создаем клавиатуру
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[bible_ai_button], [quiz_ai_button]])
    await msg.answer(hello_user, reply_markup=keyboard, parse_mode="HTML")

@my_router.message(Command("test"))
async def answerSupport(msg: Message):
    await msg.answer(report % (7413826637, "Тестовая заявка"), parse_mode="HTML")