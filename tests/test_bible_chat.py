from ai_dir.ai import BibleChatAi
from database.dao import ContextMessage

import re, logging


def has_no_english_letters(text: str) -> bool:
    """
    Проверяет, что в строке нет английских букв (a-z, A-Z).
    Возвращает True, если английских букв нет, иначе False.
    """
    return re.search(r'[a-zA-Z]', text) is None

def is_list_used(text: str) -> bool:
    """
    Проверяет, используется ли в сообщении список (абзацы с номерами).
    """
    return bool(re.search(r'--Абзац--\s*\d+\.', text))

def test_Bible_bot_output(caplog):

    caplog.set_level(logging.INFO)

    name = "Артем"

    example_inputs = [
        "Привет, как мне избавиться от гнева?",
        "Как мне преодолеть страх?",
        "Расскажи об этом подробнее",
        "Если я использую chatgpt в проектах, то будет ли это честно?"
    ]
    context_msgs = []

    list_usage_count = 0

    for i, user_msg in enumerate(example_inputs):
        bot_msg = BibleChatAi.askBibleChat(user_msg, context_msgs, name)
        if is_list_used(bot_msg):
            list_usage_count += 1

        bot_context_msg = ContextMessage(bot_msg, True)

        if not i == len(example_inputs) - 1:
            assert "strong" in bot_msg, "Нету тега strong в сообщении бота"
        assert "p" in bot_msg, "Нету тега p в сообщении бота"

        bot_msg = bot_msg.replace("strong", "").replace("p", "").replace("\n", "")
        if not i == len(example_inputs) - 1:
            assert has_no_english_letters(bot_msg), f"Ответ содержит английские буквы:\n{bot_msg}"

        new_user_msg = ContextMessage(user_msg, False)
        context_msgs.append(new_user_msg)

        context_msgs.append(bot_context_msg)

    # Проверка приветствия в первом ответе бота
    first_bot_msg_text = context_msgs[1].text.lower()
    possible_greetings = [f"привет, {name.lower()}", "привет, артём"]

    assert any(greet in first_bot_msg_text for greet in possible_greetings), \
        f"Первый ответ не содержит ожидаемого приветствия. Ожидалось одно из {possible_greetings}, но получили:\n{first_bot_msg_text}"

    # Убедиться, что в следующих ответах нет приветствия
    repeated_greetings = [msg.text for msg in context_msgs[3::2] if "привет" in msg.text.lower()]
    assert not repeated_greetings, f"Повторное приветствие найдено в сообщениях:\n{repeated_greetings}"

    assert list_usage_count <= 1, f"Список использовался слишком часто: {list_usage_count} раз"