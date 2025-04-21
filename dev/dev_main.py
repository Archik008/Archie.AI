from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import *
from configure.pyconfig import NGROK_URL

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[NGROK_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

@app.exception_handler(InfoUserException)
async def wrap_info_user_exc(request, exc: InfoUserException):
    exception = jsonable_encoder(InfoUserModel(status_code=exc.status_code, title=exc.title, detail=exc.detail))
    return JSONResponse(status_code=exc.status_code, content=exception)