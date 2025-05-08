from ai_dir.ai import QuizAi, BibleChatAi
import asyncio

async def main():
    prev_questions = ["Кто крестил Иисуса?", "Какое первое чудо совершил Иисус?", 'Где родился Иисус?']
    quiz = await QuizAi.makeQuizAi(6, "Новый Завет", prev_questions)
    print(quiz)

    # bot_output = BibleChatAi.askBibleChat("""Если я использую chatgpt в проектах, то будет ли это честно?""", [], "Артем")
    # print(bot_output)

    pass

if __name__ == '__main__':
    asyncio.run(main())