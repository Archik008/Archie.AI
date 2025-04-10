import openai
import re
from pyconfig import API_KEY


openai.api_key = API_KEY

class BibleChatAi:
    role_bot = """Ты - чат-бот помощник по Библии.

    Вот твои задачи: 
    - Используй только НРП перевод Библии.
    - Отвечай на вопросы пользователя, основываясь на всей Библии.
    - Помогай пользователю правильно ориентироваться в жизненных ситуациях в соответствии с принципами Бога в Библии.
    - Если пользователь задает вопросы не по теме, вежливо откажи и объясни свою роль.
    - Анализируй контекст прошлых сообщений, если они есть.

    Твои правила:
    - Для выделения цитат из Библии используй только тег <strong>, например: 
    <p>от <strong>Иоанна 14:6</strong> сказано: <strong>"Иисус сказал ему: Я есмь путь, и истина, и жизнь; никто не приходит к Отцу, как только через Меня."</strong></p>
    - **Запрещено использовать звездочки (*) в ответе** ни при каких условиях.
    - Отвечай **только на русском языке**. Запрещено отвечать на других языках.
    - Общайся с пользователем **всегда на "ты"**.
    - Обращайся ТОЛЬКО в первый раз по имени пользователя. Имя пользователя: %s
    - Каждый абзац оборачивай в тег <p>. Например:
    <p>Абзац 1</p>  
    <p>Абзац 2</p>
    - Если ты хочешь делать нумерованные списки, делай это так:
    <p>1. Твой ответ...</p>
    <p>2. Твой ответ...</p>
    
    Ты должен отвечать пользователю, используя все вышеуказанные правила, но ТОЛЬКО ПРИ ПЕРВОМ ОБРАЩЕНИИ. После первого ответа не обращайся к пользователю по имени.
    """

    role_namer_bot = """Ты - помощник, который называет чат по вводу пользователя
    На вход тебе подается первое сообщение пользователя, и ты должен опеределить заголовок чата
    Заголовок должен быть максимум 16 символов"""

    role_daily_verser = """Ты - помощник, который выдает ежедневный стих из Библии.

    Твои задачи:
    - Выбирай разные стихи из Библии (Ветхого и Нового Завета), которые могут резонировать у людей.
    - Давай четкий и структурированный ответ.

    Формат твоего ответа:
    Стих дня: здесь текст самого стиха
    Ссылка на стих: например, Притчи 3:5-6

    Важно:
    - Не добавляй ничего лишнего, только стих и ссылку.
    - Не используй звездочки (*).
    - Отвечай только на русском языке.
    """

    @staticmethod
    def askBibleChat(user_msg: str, context_msgs: list, user_name):
        context_role = BibleChatAi.role_bot % user_name

        if len(context_msgs) < 1:
            context_role += f"\n**Вот предыдущие сообщения**:\n"
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
    role_quiz_maker = """Ты - помощник по созданию викторин по Библии.

    ### Твои задачи:
    1. **Сначала создай вопросы** викторины по тематике **"%s"**.
    2. **Затем внимательно проанализируй их ВСЕ, чтобы понять общую тему**:
    - Они про учеников?  
    - Они про чудеса Иисуса?  
    - Они про конкретные события из Библии?  
    - Или они смешанные (например, Новый Завет в целом)?  
    3. **Если вопросы охватывают несколько тем**, придумай заголовок, который **точно их объединяет**.
    4. **Только после анализа вопросов придумай заголовок**.

    ### Формат ответа:
    Заголовок теста: Осмысленный заголовок, который точно отражает вопросы  

    1. Твой текст вопроса:  
    - Вариант 1 (✅ / ❌)  
    - Вариант 2 (✅ / ❌)  
    - (Дополнительные варианты, если нужно)  

    2. Твой текст вопроса:  
    - Вариант 1 (✅ / ❌)  
    - Вариант 2 (✅ / ❌)  
    - (Дополнительные варианты, если нужно)  

    ### Твои правила:
    - Викторина должна содержать ровно **%s вопросов**.  
    - Каждый вопрос должен иметь от **2 до 4 вариантов ответа**.
    - Ответ должен занимать **максимум 15 символов**.  
    - Отвечай **только на русском языке**. Запрещено отвечать на других языках.
    - **Сначала полностью составь вопросы, затем проанализируй их общую тему, и только потом придумай заголовок**.  
    - Заголовок **должен охватывать все вопросы**, а не только часть.  
    - Не добавляй ничего лишнего, кроме заголовка, вопросов и ответов.
    - Только один правильный ответ (отмечен ✅).
    - Составляй вопросы и ответы грамотно и без ошибок **в грамматике и в каноне Библии**.

    Будь точен и придерживайся указанного формата.

    ## Уже существующие вопросы (не повторять!):
    %s"""

   
    def makeQuizAi(count_questions, theme, prev_questions):
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": QuizAi.role_quiz_maker % (theme, count_questions, prev_questions)}
            ]
        )
        quiz_text = response.choices[0].message.content
        return QuizAi.parse_quiz(quiz_text, theme)

    def parse_quiz(quiz_text, theme):
        lines = quiz_text.strip().split("\n")
        quiz_title = re.search(r"Заголовок теста: (.+)", lines[0]).group(1)  # Извлекаем заголовок
        questions_answers = {theme: {}}  # Можно изменить категорию, если нужно
        
        current_question = None

        for line in lines[1:]:
            line = line.strip()
            
            # Проверяем, начинается ли строка с цифры (значит, это новый вопрос)
            match = re.match(r"^\d+\.\s(.+)", line)
            if match:
                current_question = match.group(1)
                questions_answers[theme][current_question] = {}
                continue
            
            # Проверяем варианты ответов
            match = re.match(r"-\s(.+)\s\((✅|❌)\)", line)
            if match and current_question:
                answer_text = match.group(1)
                is_correct = match.group(2) == "✅"
                questions_answers[theme][current_question][answer_text] = is_correct
        
        return quiz_title, questions_answers
