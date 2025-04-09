from pydantic import BaseModel

class AnswerQuestionClass(BaseModel):
    quiz_id: int
    question_id: int
    answer_id: int