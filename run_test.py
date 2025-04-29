from ai_dir.ai import QuizAi, BibleChatAi

def main():
    # prev_questions = ["Кто крестил Иисуса?", "Какое первое чудо совершил Иисус?"]
    # quiz = QuizAi.makeQuizAi(6, "Новый Завет", prev_questions)

    # print(quiz)
    bot_output = BibleChatAi.askBibleChat("Привет, как мне избавиться от гнева?", [], "Артем")

    print(bot_output)

if __name__ == '__main__':
    main()