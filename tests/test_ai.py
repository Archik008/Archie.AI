from database.dao import ContextMessage
from ai_dir.ai import BibleChatAi, QuizAi
from .qdrant_db import QdrantTesting
import re

def has_no_english_letters(text: str) -> bool:
    """
    Проверяет, что в строке нет английских букв (a-z, A-Z).
    Возвращает True, если английских букв нет, иначе False.
    """
    return re.search(r'[a-zA-Z]', text) is None

def test_Bible_bot_output():
    name = "Артeм"
    example_inputs = [
        "Привет, как мне избавиться от гнева?",
        "Как мне преодолеть страх?",
        "Расскажи об этом подробнее",
        "Что говорит 1 Коринфянам 4:6?"
    ]
    context_msgs = []

    for i, user_msg in enumerate(example_inputs):
        # Добавляем сообщение пользователя
        new_user_msg = ContextMessage(user_msg, False)
        context_msgs.append(new_user_msg)

        # Получаем ответ бота
        bot_msg = BibleChatAi.askBibleChat(user_msg, context_msgs[:-1], name)
        bot_context_msg = ContextMessage(bot_msg, True)

        context_msgs.append(bot_context_msg)

        bot_msg = bot_msg.replace("strong", "").replace("p", "")

        # Проверка на отсутствие английских букв
        assert has_no_english_letters(bot_msg), f"Ответ содержит английские буквы:\n{bot_msg}"

        # Добавляем ответ бота в контекст
        context_bot_msg = ContextMessage(bot_msg, True)
        context_msgs.append(context_bot_msg)

    # Проверка приветствия в первом ответе бота
    first_bot_msg_text = context_msgs[1].text.lower()
    possible_greetings = [f"привет, {name.lower()}", "привет, артём"]

    assert any(greet in first_bot_msg_text for greet in possible_greetings), \
        f"Первый ответ не содержит ожидаемого приветствия. Ожидалось одно из {possible_greetings}, но получили:\n{first_bot_msg_text}"

    # Убедиться, что в следующих ответах нет приветствия
    repeated_greetings = [msg.text for msg in context_msgs[3::2] if "привет" in msg.text.lower()]
    assert not repeated_greetings, f"Повторное приветствие найдено в сообщениях:\n{repeated_greetings}"

qdrant = QdrantTesting()
COLLECTION_NAME = "quiz_questions"
qdrant.drop_collection(COLLECTION_NAME)

def assert_questions_answers(questions_answers: dict, prev_questions: list):
    for quiz_question, answers in questions_answers.items():
        assert has_no_english_letters(quiz_question), f"Вопрос содержит английские буквы: {quiz_question}"
        if len(prev_questions) > 0:
            assert not qdrant.search_data(quiz_question, COLLECTION_NAME), f"Есть вопросы похожие с этим: {quiz_question}"
        prev_questions.append(quiz_question)
        for answer, _ in answers.items():
            assert has_no_english_letters(answer), f"Ответ содержит английские буквы: {answer}"
    return prev_questions

def test_quiz_ai():
    topic = "Новый Завет"
    title, quiz = QuizAi.makeQuizAi(6, topic, [])
    questions_answers_from_bot = quiz.get(topic)

    prev_questions = assert_questions_answers(questions_answers_from_bot, [])

    prev_questions = [" ".join(question.split()[1:]) for question in prev_questions]

    qdrant.create_collection(COLLECTION_NAME, prev_questions)
    qdrant.insert_data(COLLECTION_NAME, prev_questions)
    
    title, prev_questions_quiz = QuizAi.makeQuizAi(6, topic, prev_questions)
    get_quiz_with_prev_questions = prev_questions_quiz.get(topic)

    assert_questions_answers(get_quiz_with_prev_questions, prev_questions)