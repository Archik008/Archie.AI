from ai_dir.ai import BibleChatAi
from .test_bible_chat import has_no_english_letters
import logging
import pytest

@pytest.mark.asyncio
async def test_daily_verse_output(caplog):
    caplog.set_level(logging.INFO)

    verse, title = await BibleChatAi.getDailyVerse()

    assert has_no_english_letters(verse), f"Стих имеет английские буквы: {verse}"
    assert has_no_english_letters(title), f"Название имеет английские буквы: {title}"