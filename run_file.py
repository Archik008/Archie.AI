from ai_dir.ai import QuizAi

def main():
    prev_questions = ["Кто крестил Иисуса?", "Какое первое чудо совершил Иисус?"]
    quiz = QuizAi.makeQuizAi(6, "Новый Завет", prev_questions)

    print(quiz)

if __name__ == '__main__':
    main()