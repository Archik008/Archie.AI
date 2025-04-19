from routes import router
from fastapi import FastAPI, Depends

import os
import uvicorn

from aiogram.types import Update
from bot import bot, dp, lifespan

from starlette.responses import FileResponse 

import asyncio

from pydantic import BaseModel

from texts import *
from user_funcs import *
from fastapi.middleware.cors import CORSMiddleware

from starlette.requests import Request
from fastapi.staticfiles import StaticFiles

from pyconfig import ADMINS_LIST, URL

app = FastAPI(lifespan=lifespan,
              docs_url=None,
              redoc_url=None,
              openapi_url=None)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

class TechSupportModel(BaseModel):
    user_text: str

@router.post('/support')
async def forward_to_support(params: TechSupportModel, user: int = Depends(UserMethods.start_verifying)):
    tasks = [bot.send_message(admin, report % (user, user, params.user_text), parse_mode="HTML") for admin in ADMINS_LIST]
    await asyncio.gather(*tasks)
    return {"ok": True}

@router.post("/webhook")
async def webhook(request: Request, db: AsyncSession = Depends(get_db)) -> None:
    new_update_msg = await request.json()
    successful_payment = new_update_msg.get("message", {}).get("successful_payment")
    if successful_payment:
        user_id = new_update_msg.get("message", {}).get("from", {}).get("id")
        await UserMethods.subscribe_db(user_id, db)
    update = Update.model_validate(new_update_msg, context={"bot": bot})
    await dp.feed_update(bot, update)

frontend_dist = os.path.join(os.path.dirname(__file__), 'dist')
frontend_dist = os.path.abspath(frontend_dist)

router.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, 'assets')), name="assets")
router.mount("/css", StaticFiles(directory=os.path.join(frontend_dist, 'css')), name="css")
router.mount("/js", StaticFiles(directory=os.path.join(frontend_dist, 'js')), name="js")
    
@router.get("/{full_path:path}")
async def serve_vue_router(full_path: str):
    return FileResponse(os.path.join(frontend_dist, "index.html"))

if __name__ == "__main__":
    uvicorn.run(router, host="0.0.0.0", port=8000)