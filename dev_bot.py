from aiogram import Router, Dispatcher, Bot, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo, Message, LabeledPrice
from aiogram.filters import Command

from pyconfig import DEV_BOT_TOKEN

import asyncio


URL = "MY_URL_HERE"
bot = Bot(DEV_BOT_TOKEN)
my_router = Router()
dp = Dispatcher()

dp.include_router(my_router)

async def create_invoice_link_bot():
   payment_link = await bot.create_invoice_link(
       "Подписка",
       "Ежемесячная подписка 100 stars",
       "{}",
       "XTR",
       prices=[LabeledPrice(label="Подписка", amount=1)]
   )
   return payment_link

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

async def startBot():
    print("Бот запущен")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(startBot())