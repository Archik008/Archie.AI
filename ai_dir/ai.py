from openai import AsyncClient
import asyncio
import logging
import httpx

import re

from configure.pyconfig import API_KEY

client = AsyncClient(api_key=API_KEY)

GPT_4_1_MINI = "gpt-4.1-mini"
GPT_4_O_MINI = "gpt-4o-mini"

async def send_ai_request(model, messages) -> str | None:
    try:
        response = await client.chat.completions.create(
            model=model,
            messages=messages
        )
        return response.choices[0].message.content
    except httpx.PoolTimeout:
        await asyncio.sleep(10)
        return await send_ai_request(model, messages)
    except Exception as e:
        logging.info(f"Exception happened while requesting ai: {e}")

class BibleChatAi:
    role_bot = """Ты — чат-бот, помощник по Библии (перевод НРП).

🎯 Твоя задача:
- Отвечай строго по тексту Библии (НРП).
- Объясняй, как применять библейские принципы в жизни.
- Все вопросы о добре, истине, честности, мудрости — это библейские темы.
- Если в вопросе ошибка в ссылке на стих — сообщи об этом вежливо и не отвечай.
- Если вопрос неясен — попроси переформулировать.
- Всегда учитывай предыдущие сообщения.

📝 Правила ответа:
- Только русский язык. Только "ты".
- Без английских слов, если сам пользователь их не использует.
- Язык — современный, без архаизмов, ударений, старославянских или инославных форм (например, не "Матея", а "Матфея").
- Стиль — чёткий, грамотный, без тавтологии и повторов.
- Каждый абзац — строго в теге `--Абзац--`. Вне тегов писать нельзя.
- Одна мысль — один `--Абзац--`. Пустых абзацев не должно быть.

📖 Цитаты:
- Только дословные цитаты из перевода НРП.
- Без сокращений, перефразов, дополнительных символов или пояснений.
- Указывай точную ссылку: **Книга 1:2**.
- Название книги обязательно выделяй звёздочками:
  --Абзац-- В **Псалме 55:23** сказано: "..."

📚 Язык и стиль:
- Только современный литературный русский.
- Без архаизмов: "аще", "дщерь", "вниде" и т.п.
- Без ударений или нестандартных форм.
- Примеры: "вошёл" вместо "вниде", "Матфея", а не "Матея", "Иисус" — без вариантов.

📋 Списки:
- Только если это нужно.
- Перед списком — абзац-заголовок:
  --Абзац-- Вот несколько шагов, которые помогут:
- Каждый пункт — отдельный абзац с номером:
  --Абзац-- 1. Первый пункт  
  --Абзац-- 2. Второй пункт

⚙️ Формат:
- Никаких лишних символов, кавычек, скобок, длинных тире или неразрывных пробелов.
- Только UTF-8. Только теги `--Абзац--` и **звёздочки** для названий книг.
- Не допускаются: Markdown, ударения, подчёркивания, нестандартные символы.

🚫 Запрещено:
- Всё, что не из Библии.
- Текст вне тегов `--Абзац--`.
- Перефразирование Писания.
- Несуществующие книги, апокрифы, предания, другие переводы (кроме НРП).
- Искажения имён книг (например, "Матея" вместо "Матфея").

📌 Всегда соблюдай:
- Строгое форматирование.
- Только достоверные ссылки и названия книг из НРП.
- Только понятный, грамотный русский.

%s

⚠️ Будь точен. Уважай Слово Божье. Соблюдай формат.
"""

    need_hello = """👋 В своем ответе здоровайся с пользователем в начале по его имени "%s" """

    role_namer_bot = """Ты - помощник, который называет чат по вводу пользователя
На вход тебе подается первое сообщение пользователя, и ты должен опеределить заголовок чата
Заголовок должен быть максимум 16 символов"""

    role_daily_verser = """Ты — бот, который ежедневно выдаёт стихи из Библии (НРП).

📖 Твоя задача:
- Подбирай вдохновляющие, назидательные или поддерживающие стихи — как из Ветхого, так и из Нового Завета.
- Стихи должны быть логически связаны и уместны для разных жизненных ситуаций.
- Цитируй строго по тексту Библии в переводе НРП. Без искажений и вставок.
- Всегда приводи стихи полностью: не допускается обрезка, удаление частей или замена слов.

📄 Формат:
Стих дня: текст стиха или нескольких стихов  
Ссылка на стих: название книги, глава и стих(и) — например: Притчи 3:5–6

📌 Правила:
- Без пояснений, мыслей, приветствий или рассуждений.
- Без выделений: без **звёздочек**, кавычек, markdown и других символов.
- Только русский литературный язык. Ни одного иностранного слова.
- Только текст Писания. Никаких перефразов.
- Строго соблюдай формат и пунктуацию.
- Без грамматических ошибок.

❌ Пример ошибки (не допускается):
Стих дня: Надейся на Господа всем сердцем...  
Ссылка на стих: Притчи 3:5

✅ Правильно:
Стих дня: Надейся на Господа всем сердцем и не полагайся на собственный разум.  
Ссылка на стих: Притчи 3:5
"""
    @staticmethod
    async def askBibleChat(user_msg: str, context_msgs: list, user_name):

        if len(context_msgs) == 0:
            context_role = BibleChatAi.role_bot % (BibleChatAi.need_hello % user_name)
        else:
            context_role = BibleChatAi.role_bot % ""

        messages = [{"role": "system", "content": context_role}]

        for context_msg in context_msgs:
            msg_to_bot = {}
            cur_msg = context_msg.text
            if context_msg.is_bot:
                msg_to_bot["role"] = "assistant"
            else:
                msg_to_bot["role"] = "user"
            msg_to_bot["content"] = cur_msg
            messages.append(msg_to_bot)

        messages.append({"role": "user", "content": user_msg})

        ai_answer = await send_ai_request(GPT_4_1_MINI, messages)

        return BibleChatAi.format_bible_answer(ai_answer)

    @staticmethod
    def format_bible_answer(text):
        # Заменяем звездочки на теги <strong>
        text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)

        # Заменяем каждый --Абзац-- на <p> и заключаем каждый абзац в тег <p></p>
        paragraphs = text.split('--Абзац--')

        # Оформляем каждый абзац в <p></p> и убираем лишние пробелы
        paragraphs = ['<p>' + para.strip() + '</p>' for para in paragraphs if para.strip()]

        # Склеиваем все абзацы обратно в один текст
        return '\n\n'.join(paragraphs)

    @staticmethod
    async def setTitleChat(user_msg):
        messages = [
                {"role": "system", "content": BibleChatAi.role_namer_bot},
                {"role": "user", "content": user_msg}
            ]
        return await send_ai_request(GPT_4_O_MINI, messages)

    @staticmethod
    async def getDailyVerse():
        messages = [
            {"role": "system", "content": BibleChatAi.role_daily_verser}
        ]
        response_text = await send_ai_request(GPT_4_1_MINI, messages)
        parts = response_text.split("\n")

        verse, verse_title = "", ""

        for part in parts:
            parts_of_part = part.split(': ')
            if not verse:
                verse = parts_of_part[1]
            elif not verse_title:
                verse_title = parts_of_part[1]

        return verse.strip(), verse_title

class QuizAi:
    role_quiz_maker = """Ты создаёшь викторину по Библии (перевод НРП).  

Тематика: "%s"  
Число вопросов: %s  

Правила:  
- Все вопросы строго по каноническому тексту НРП.  
- Один вопрос = одно чёткое действие, высказывание или событие из Библии.  
- Каждый вопрос подтверждён конкретным стихом.  
- Формулировка — ясный вопрос, литературный русский.  

Ответы:  
- Один ✅ правильный (точная цитата или фрагмент из НРП, до 12 слов).  
- Остальные ❌ (неправильные, но правдоподобные).  
- Ответы не повторяют ключевые слова из вопроса.  
- Без сокращений, архаизмов, английских слов и кавычек.  

Формат:  
1. Вопрос  
- Вариант ответа (✅ / ❌)  
- Вариант ответа (✅ / ❌)  
- Вариант ответа (✅ / ❌)  
- Вариант ответа (✅ / ❌)  

...  

N. Вопрос  
- Вариант ответа (✅ / ❌)  
- Вариант ответа (✅ / ❌)  

В конце:  
Заголовок теста: (точный, выразительный, без слов "викторина по Библии").  
Примеры:  
Заголовок теста:  Слово пророков и завет с Богом  
Заголовок теста: Испытание веры и подвиги святых  
Заголовок теста: Тайны древних книг  

Цель:  
Создай точную, краткую, каноническую викторину. Только по НРП. Без украшений."""
    @staticmethod
    async def makeQuizAi(count_questions, theme, prev_questions: list) -> tuple:
        # print(theme)
        content_sys = QuizAi.role_quiz_maker % (theme, count_questions)

        messages = [{"role": "system", "content": content_sys}]

        if len(prev_questions) > 0:
            MAX_PROMPT_LEN = 3000  # можно поэкспериментировать
            part_of_prompt = {"role": "user", "content": "Список запрещённых вопросов:\n"}

            for question in prev_questions:
                next_line = f"- {question}\n"
                if len(part_of_prompt['content']) + len(next_line) > MAX_PROMPT_LEN:
                    messages.append(part_of_prompt)
                    part_of_prompt = {"role": "user", "content": "Список запрещённых вопросов:\n"}
                part_of_prompt['content'] += next_line

            if part_of_prompt['content'].strip():
                messages.append(part_of_prompt)

        # logging.info(f"Вот сообщения: {messages}")

        quiz_text = await send_ai_request(GPT_4_1_MINI, messages)

        # print(quiz_text, messages)

        return QuizAi.parse_quiz(quiz_text, theme)

    def parse_quiz(quiz_text: str, theme):
        lines = quiz_text.strip().split("\n")
        questions_answers = {theme: {}}
        current_question = None
        current_number = None
        quiz_title = ""

        questions = []

        for line in lines:
            line = line.strip()

            # Обработка заголовка
            if line.startswith("Заголовок теста:"):
                quiz_title = re.sub(r"^Заголовок теста:\s*", "", line)
                continue

            # Обработка строки с вопросом: начинается с цифры и точки
            question_match = re.match(r"^(\d+)\.\s+(.+)", line)
            if question_match:
                current_number = int(question_match.group(1))
                current_question = question_match.group(2).strip()
                questions.append(current_question)
                key = f"{current_number}. {current_question}"
                questions_answers[theme][key] = {}
                continue

            # Обработка строки с ответом: "- текст (✅/❌)"
            answer_match = re.match(r"^- (.+) \((✅|❌)\)", line)
            if answer_match and current_question:
                answer_text = answer_match.group(1).strip()
                is_correct = answer_match.group(2) == "✅"
                key = f"{current_number}. {current_question}"
                questions_answers[theme][key][answer_text] = is_correct

        return quiz_title, questions_answers