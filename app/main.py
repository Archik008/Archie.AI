from app.routes import *
from fastapi import FastAPI, Depends

import os
import uvicorn

from aiogram.types import Update
from bot import bot, dp, lifespan

from starlette.responses import FileResponse 

from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder


from database.dao import *
from fastapi.middleware.cors import CORSMiddleware

from starlette.requests import Request

from configure.pyconfig import URL, PROJ_LOG_TOKEN

from mimetypes import guess_type

import logfire

logfire.configure(token=PROJ_LOG_TOKEN)

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
logfire.instrument_fastapi(app, capture_headers=True)

FRONTEND_DIST = os.path.abspath(os.path.join(os.path.dirname(__file__), "dist"))

# Безопасный путь (на всякий случай)
def safe_join(base: str, *paths: str) -> str:
    final_path = os.path.abspath(os.path.join(base, *paths))
    if not final_path.startswith(base):
        raise HTTPException(status_code=403, detail="Access Denied")
    return final_path

@app.get("/static/{file_path:path}")
async def serve_static(file_path: str):
    try:
        file_full_path = safe_join(FRONTEND_DIST, file_path)
        if not os.path.isfile(file_full_path):
            raise HTTPException(status_code=404, detail="Static file not found")

        mime_type, _ = guess_type(file_full_path)
        return FileResponse(file_full_path, media_type=mime_type or "application/octet-stream")

    except Exception as e:
        if file_path == "favicon.ico":
            raise  HTTPException(status_code=404, detail="Icon not found")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/{full_path:path}")
async def serve_spa(full_path: str, request: Request):
    """
    Любой маршрут (в том числе SPA-маршруты как /quiz/44) → отдаем index.html
    """
    index_path = safe_join(FRONTEND_DIST, "index.html")
    if not os.path.isfile(index_path):
        raise HTTPException(status_code=500, detail="index.html not found")
    return FileResponse(index_path, media_type="text/html")

@app.exception_handler(InfoUserException)
async def wrap_info_user_exc(request, exc: InfoUserException):
    exception = jsonable_encoder(InfoUserModel(status_code=exc.status_code, title=exc.title, detail=exc.detail))
    return JSONResponse(status_code=exc.status_code, content=exception)

@app.post("/webhook")
async def webhook(request: Request, db: AsyncSession = Depends(get_db)) -> None:
    new_update_msg = await request.json()
    successful_payment = new_update_msg.get("message", {}).get("successful_payment")
    if successful_payment:
        user_id = new_update_msg.get("message", {}).get("from", {}).get("id")
        await DAOModel.subscribe_db(user_id, db)
    update = Update.model_validate(new_update_msg, context={"bot": bot})
    await dp.feed_update(bot, update)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)