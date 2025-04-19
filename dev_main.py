from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import router
from pyconfig import NGROK_URL

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[NGROK_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)