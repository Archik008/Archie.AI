from app.routes import *
from fastapi import FastAPI, Depends

import os
import uvicorn

from aiogram.types import Update
from bot import bot, dp, lifespan

from starlette.responses import FileResponse 

from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

import asyncio

from pydantic import BaseModel

from texts import *
from database.dao import *
from fastapi.middleware.cors import CORSMiddleware


from starlette.requests import Request
from fastapi.staticfiles import StaticFiles
from starlette.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware

from configure.pyconfig import ADMINS_LIST, URL

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

class NoCacheStaticMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response: Response = await call_next(request)
        if request.url.path.endswith("css") or request.url.path.endswith("js"):
            response.headers["Cache-Control"] = "no-store"
        return response

app.include_router(router)
app.add_middleware(NoCacheStaticMiddleware)

frontend_dist = os.path.join(os.path.dirname(__file__), 'dist')
frontend_dist = os.path.abspath(frontend_dist)

app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, 'assets')), name="assets")
app.mount("/css", StaticFiles(directory=os.path.join(frontend_dist, 'css')), name="css")
app.mount("/js", StaticFiles(directory=os.path.join(frontend_dist, 'js')), name="js")

class TechSupportModel(BaseModel):
    user_text: str

@app.exception_handler(InfoUserException)
async def wrap_info_user_exc(request, exc: InfoUserException):
    exception = jsonable_encoder(InfoUserModel(status_code=exc.status_code, title=exc.title, detail=exc.detail))
    return JSONResponse(status_code=exc.status_code, content=exception)

@app.post('/support')
async def forward_to_support(params: TechSupportModel, user: int = Depends(DAOModel.start_verifying)):
    tasks = [bot.send_message(admin, report % (user, user, params.user_text), parse_mode="HTML") for admin in ADMINS_LIST]
    await asyncio.gather(*tasks)
    return {"ok": True}

@app.post("/webhook")
async def webhook(request: Request, db: AsyncSession = Depends(get_db)) -> None:
    new_update_msg = await request.json()
    successful_payment = new_update_msg.get("message", {}).get("successful_payment")
    if successful_payment:
        user_id = new_update_msg.get("message", {}).get("from", {}).get("id")
        await DAOModel.subscribe_db(user_id, db)
    update = Update.model_validate(new_update_msg, context={"bot": bot})
    await dp.feed_update(bot, update)
    
@app.get("/{full_path:path}")
async def serve_vue_router(full_path: str):
    return FileResponse(os.path.join(frontend_dist, "index.html"))

if __name__ == "__main__":
    uvicorn.run(router, host="0.0.0.0", port=8000)