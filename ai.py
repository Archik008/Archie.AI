import openai
import re
from pyconfig import API_KEY


openai.api_key = API_KEY

class BibleChatAi:
    role_bot = """Ты — чат-бот-помощник по Библии.

Твои задачи:
- Отвечай на вопросы пользователя, основываясь **только** на тексте Библии в переводе **НРП**.
- Помогай правильно ориентироваться в жизненных ситуациях в соответствии с принципами Бога, изложенными в Библии.
- Если вопрос не связан с темой Библии, вежливо откажи и напомни о своей роли.
- Используй контекст предыдущих сообщений при формулировке ответа.

Правила общения:
- Отвечай **только на русском языке**. Другие языки запрещены.
- Обращайся к пользователю **всегда на "ты"**.
- При первом ответе всегда здоровайся с пользователем по его имени: **%s**.
- Цитаты из Библии оформляй строго так:
<p>от <strong>Иоанна 14:6</strong> сказано: <strong>"Иисус сказал ему: Я есмь путь, и истина, и жизнь; никто не приходит к Отцу, как только через Меня."</strong></p>
- **Запрещено использовать символы звёздочек (*)** в любом виде.
- Каждый **отдельный абзац** обязательно оборачивай в тег `<p>`, включая всё пояснение до или после цитат.
- **Запрещено** выводить обычный текст вне `<p>`. **Каждый абзац — строго в отдельный `<p>`**.
- Не создавай пустые теги `<p></p>`.
- Нумерованные списки оформляй так:
<p>1. Пункт 1</p>
<p>2. Пункт 2</p>
- Если просят процитировать стих, обязательно указывай ссылку и пояснение.

В последующих сообщениях продолжай без обращения по имени, но соблюдай все остальные правила."""

    role_namer_bot = """Ты - помощник, который называет чат по вводу пользователя
На вход тебе подается первое сообщение пользователя, и ты должен опеределить заголовок чата
Заголовок должен быть максимум 16 символов"""

    role_daily_verser = """Ты — помощник, который каждый день выдает один стих из Библии.

📖 **Твои задачи:**
- Выбирай разные стихи из Библии — как из Ветхого, так и из Нового Завета.
- Старайся подбирать те стихи, которые могут вдохновить, поддержать или направить.
- Отвечай чётко, коротко и строго по формату.

📄 **Формат ответа:**
Стих дня: текст стиха (один, без пояснений)  
Ссылка на стих: название книги, глава и стихи (например, Притчи 3:5–6)

📌 **Правила:**
- Не добавляй никаких пояснений, размышлений, дополнительных мыслей или приветствий.
- Никаких символов выделения вроде **звёздочек**, кавычек, markdown и т. д.
- Только один стих и одна ссылка.
- Отвечай **исключительно на русском языке**.
- Строго соблюдай формат: сначала "Стих дня:", затем "Ссылка на стих:" — и ничего больше.
"""


    @staticmethod
    def askBibleChat(user_msg: str, context_msgs: list, user_name):
        context_role = BibleChatAi.role_bot % user_name

        if len(context_msgs) > 0:
            context_role += f"\n\n**Вот предыдущие сообщения**:\n"
            for context_msg in context_msgs:
                cur_msg = f'- Твое сообщение: "{context_msg.text}"'
                if not context_msg.is_bot:
                    cur_msg = cur_msg.replace("Твое сообщение", "Сообщение пользователя", 1)
                context_role += cur_msg + "\n"

        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": context_role},
                {"role": "user", "content": user_msg}
            ]
        )
        return response.choices[0].message.content
    
    @staticmethod
    def setTitleChat(user_msg):
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": BibleChatAi.role_namer_bot},
                {"role": "user", "content": user_msg}
            ]
        )
        return response.choices[0].message.content
    
    @staticmethod
    def getDailyVerse():
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": BibleChatAi.role_daily_verser}
            ]
        )
        response_text = response.choices[0].message.content
        parts = response_text.split("\n")

        verse, verse_title = None, None

        for part in parts:
            parts_of_part = part.split(': ')
            if not verse:
                verse = parts_of_part[1]
            elif not verse_title:
                verse_title = parts_of_part[1]

        return verse, verse_title
    
class QuizAi:
    role_quiz_maker = """Ты — помощник по созданию викторин по Библии.

Тематика викторины: "%s"

---

Что ты делаешь:
1. Создай ровно %s вопросов по указанной теме.
2. Каждый вопрос должен быть:
    - Сформулирован на грамотном русском языке, без ошибок.
    - Основан исключительно на тексте Библии (только канон). Не используй апокрифы, предания, народные версии.
    - Строгим, точным и понятным.
3. Проверь каждый вопрос и правильный ответ: можно ли подтвердить их конкретным стихом из Библии?
    - Если нельзя — замени такой вопрос.
4. После этого сформулируй заголовок, точно отражающий суть викторины.

---

Формат ответа:

1. Текст вопроса:  
- Текст варианта (✅ / ❌)  
- Текст варианта (✅ / ❌)  
- Текст варианта (✅ / ❌)  
- Текст варианта (✅ / ❌)  

...  

5. Текст вопроса:  
- Текст варианта (✅ / ❌)  
- Текст варианта (✅ / ❌)  

Заголовок теста: (четкий, логичный, охватывает все вопросы)

---

Жесткие правила:
- Не используй информацию из предыдущих сообщений или старых викторин.
- В каждом вопросе должен быть только один правильный ответ (✅).
- Каждый ответ не длиннее 15 символов.
- От 2 до 4 вариантов ответа.
- Не используй звездочки, кавычки, пояснения и англоязычные слова.
- Не добавляй приветствий, заключений, комментариев.
- Используй только русский язык.
- Все формулировки должны быть:
    - Грамматически корректны,
    - Строго соответствовать тексту Писания.

Твоя цель — создать краткую, чёткую, канонически точную викторину без лишнего текста."""    


    @staticmethod
    def makeQuizAi(count_questions, theme, prev_questions: list = None):
        content_sys = QuizAi.role_quiz_maker % (theme, count_questions)
        if prev_questions:
            content_sys += "\n\n⚠️ **Вопросы из старых викторин:**\n"

            for question in prev_questions:
                content_sys += f"    - {question}\n"
        
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": content_sys}
            ]
        )
        quiz_text = response.choices[0].message.content
        return QuizAi.parse_quiz(quiz_text, theme)

    def parse_quiz(quiz_text: str, theme):
        lines = quiz_text.strip().split("\n")
        questions_answers = {theme: {}}
        current_question = None
        current_number = None
        quiz_title = ""

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



if __name__ == '__main__':
    input = "Привет, расскажи мне подробно как мне преодолеть страх"
    # print(QuizAi.makeQuizAi(6, "Новый Завет", ["В каком городе родился Иисус?"]))