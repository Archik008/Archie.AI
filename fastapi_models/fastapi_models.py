from pydantic import BaseModel

class NewUser(BaseModel):
    username: str

class NewChat(BaseModel):
    init_data: str

class NewMessage(BaseModel):
    chatId: int
    text: str
    is_bot: bool

class NameRequest(BaseModel):
    newName: str

class ChangeChat(BaseModel):
    chat_id: int
    new_text: str

class DeleteChat(BaseModel):
    chatId: int
    init_data: str

class VerifyingUrl(BaseModel):
    init_data: str