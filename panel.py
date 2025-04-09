from fastapi import FastAPI, Request
from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend
from starlette.middleware.sessions import SessionMiddleware

import jwt, secrets, uvicorn

from database import engine
from models import Base
from config import settings
from pyconfig import URL

SECRET_KEY = secrets.token_urlsafe(16)
ALGORITHM = "HS256"

class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        username, password = form["username"], form["password"]
        if not (username == settings.DB_USER and password == settings.DB_PASSWORD):
            return False
        
        token = jwt.encode(
            {"sub": username, "token_type": "bearer"},
            SECRET_KEY,
            algorithm=ALGORITHM
        )

        request.session.update({"token": token})

        return True
    
    async def logout(self, request: Request):
        request.session.clear()
        return True
    
    async def authenticate(self, request: Request):
        token = request.session.get("token")  # Достаем токен из сессии
        if not token:
            return False

        return self.get_admin_by_key(token) is not None  # Проверяем токен
    
    def get_admin_by_key(self, authorization):
        try:
            payload = jwt.decode(authorization, SECRET_KEY, algorithms=[ALGORITHM])
            return payload.get("sub")
        except:
            return 


app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)  # Добавляем поддержку сессий

auth_backend = AdminAuth(SECRET_KEY)
admin = Admin(app, engine, authentication_backend=auth_backend)


for cls in Base.__subclasses__():
    if hasattr(cls, "__tablename__"):  # Проверяем, что это модель SQLAlchemy
        columns = [getattr(cls, col) for col in cls.__table__.columns.keys()]
        
        class DynamicAdmin(ModelView, model=cls):
            column_list = columns
        
        admin.add_view(DynamicAdmin)

if __name__ == '__main__':
    uvicorn.run(app, port=8080, host="0.0.0.0", proxy_headers=True, forwarded_allow_ips="*")