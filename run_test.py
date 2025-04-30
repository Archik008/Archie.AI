from ai_dir.ai import QuizAi, BibleChatAi

def main():
    # prev_questions = ["Кто крестил Иисуса?", "Какое первое чудо совершил Иисус?"]
    # quiz = QuizAi.makeQuizAi(6, "Новый Завет", prev_questions)

    # print(quiz)
    bot_output = BibleChatAi.askBibleChat("Честно ли будет использовать chatgpt в моем учебном проекте?", [], "Артем")

    print(bot_output)

if __name__ == '__main__':
    main()