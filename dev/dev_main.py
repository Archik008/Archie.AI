from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from app.routes import *
from configure.pyconfig import NGROK_URL, PROJ_LOG_TOKEN

import logfire

logfire.configure(token=PROJ_LOG_TOKEN)

app = FastAPI()
logfire.instrument_fastapi(app, capture_headers=True)

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