from ai_dir.ai import QuizAi, BibleChatAi

def main():
    prev_questions = ["Кто крестил Иисуса?", "Какое первое чудо совершил Иисус?", 'Где родился Иисус?']
    quiz = QuizAi.makeQuizAi(6, "Новый Завет", prev_questions)

    # bot_output = BibleChatAi.askBibleChat("Честно ли будет использовать chatgpt в моем учебном проекте?", [], "Артем")
    pass
    # print(bot_output)

if __name__ == '__main__':
    main()