from ai_dir.ai import BibleChatAi
from database.dao import ContextMessage

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

        assert "strong" in bot_msg, "Нету тега strong в сообщении бота"

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