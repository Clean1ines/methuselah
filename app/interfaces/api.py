from fastapi import FastAPI, Request, Header, HTTPException
from aiogram import Bot, Dispatcher
from aiogram.types import Update
from app.core.config import settings
from app.infrastructure.database import Database
from app.core.config_registry import config_registry
from app.interfaces.telegram_handlers import router
from app.infrastructure.repositories import UserRepository # ADDED
from contextlib import asynccontextmanager
from app.core.logger import logger

bot = Bot(token=settings.BOT_TOKEN)
dp = Dispatcher()
dp.include_router(router)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await Database.connect()
    config_registry.reload() 
    
    webhook_info = await bot.get_webhook_info()
    if webhook_info.url != settings.WEBHOOK_URL:
        await bot.set_webhook(url=settings.WEBHOOK_URL)
        logger.info(f"Webhook set to {settings.WEBHOOK_URL}")
    else:
        logger.info("Webhook is already set. Skipping.")
        
    yield
    await bot.delete_webhook()
    await Database.disconnect()

app = FastAPI(lifespan=lifespan)

@app.post("/webhook")
async def webhook(request: Request):
    # ADDED: Базовая обработка ошибок парсинга вебхука
    try:
        json_data = await request.json()
        update = Update.model_validate(json_data, context={"bot": bot})
        await dp.feed_update(bot, update)
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
    return {"status": "ok"}

@app.post("/admin/reload")
async def hot_reload_config(x_admin_token: str = Header(...)):
    if x_admin_token != settings.BOT_TOKEN:
        raise HTTPException(status_code=403, detail="Forbidden")
    config_registry.reload()
    return {"status": "Configs hot-reloaded successfully"}

# ADDED: Endpoint аналитики продукта
@app.get("/stats")
async def get_product_stats(x_admin_token: str = Header(...)):
    if x_admin_token != settings.BOT_TOKEN:
        raise HTTPException(status_code=403, detail="Forbidden")
    
    stats = await UserRepository.get_stats()
    return stats

@app.get("/health")
async def health():
    return {"status": "alive"}