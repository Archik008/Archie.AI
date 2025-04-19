from aiogram import Router, Dispatcher, Bot, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo, Message, LabeledPrice
from aiogram.filters import Command

from pyconfig import DEV_BOT_TOKEN, ADMINS_LIST, PASSWORD, NGROK_URL

import asyncio
import httpx

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
    bot_url = f"{NGROK_URL}/bot"  # Ссылка на ваше веб-приложение
    bible_ai_button = InlineKeyboardButton(
        text="Библейский бот",
        web_app=WebAppInfo(url=bot_url)
    )

    quiz_url = f"{NGROK_URL}/quizes_app"
    quiz_ai_button = InlineKeyboardButton(
        text="ИИ викторина",
        web_app=WebAppInfo(url=quiz_url)
    )

    # Создаем клавиатуру
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[bible_ai_button], [quiz_ai_button]])

    await msg.answer(hello_user, reply_markup=keyboard, parse_mode="HTML")


@my_router.message(Command("ban"))
async def ban_user(msg: Message):
    if not msg.from_user.id in ADMINS_LIST:
        return
    
    list_banned_users = [int(id) for id in msg.text.removeprefix("/ban ").split()]
    
    async with httpx.AsyncClient() as client:
        data = {
            "password": PASSWORD,
            "list_users": list_banned_users
        }
        response = await client.post(f"http://localhost:8000/ban", json=data)
        await msg.answer(f"Ответ от бэкенда:\n\n{response.json()}")

async def startBot():
    print("Бот запущен")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(startBot())