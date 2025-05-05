from ai_dir.ai import QuizAi, BibleChatAi

def main():
    # prev_questions = ["Кто крестил Иисуса?", "Какое первое чудо совершил Иисус?", 'Где родился Иисус?']
    # quiz = QuizAi.makeQuizAi(6, "Новый Завет", prev_questions)

    bot_output = BibleChatAi.askBibleChat("""Слушай, то что мне говорят постоянно неверующие часто на прощание "удачи", действительно ли удача есть или это ложь дьявола? Как мне это воспринимать?""", [], "Артем")
    print(bot_output)

    pass

if __name__ == '__main__':
    main()