from ai_dir.ai import BibleChatAi
import re
import pytest

def has_no_english_letters(text: str) -> bool:
    """
    Проверяет, что в строке нет английских букв (a-z, A-Z).
    Возвращает True, если английских букв нет, иначе False.
    """
    return re.search(r'[a-zA-Z]', text) is None

@pytest.mark.parametrize(
    "input, result",
    [
        ("Привет, как мне избавиться от гнева?", True),
        ("Как мне предолеть страх?", True),
        ("Расскажи об этом подробнее", True)
    ]
)


def test_bot_output(input, result):
    bot_msg = BibleChatAi.askBibleChat(input, [], "Артем")