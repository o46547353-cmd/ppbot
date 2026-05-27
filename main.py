from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from aiogram import Bot, Dispatcher
from aiogram.types import Update

from app.core.config import settings
from app.db.database import init_models
from app.bot.handlers import router as main_router
from app.services.habit_tracker import habit_tracker

# Initialize bot and dispatcher
bot = Bot(token=settings.BOT_TOKEN)
dp = Dispatcher()
dp.include_router(main_router)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan event handler for FastAPI.
    Initializes database and sets the webhook on startup.
    Cleans up the webhook and bot session on shutdown.
    """
    # Startup: Set webhook
    await bot.set_webhook(url=settings.WEBHOOK_URL)

    # Startup: Start habit tracker scheduler
    habit_tracker.setup(bot, dp)

    yield

    # Shutdown: Stop habit tracker scheduler
    habit_tracker.shutdown()

    # Shutdown: Remove webhook and close bot session
    await bot.delete_webhook()
    await bot.session.close()


# Initialize FastAPI app
app = FastAPI(title="ПП-Помощник v2.0", lifespan=lifespan)


@app.post("/webhook")
async def webhook(request: Request):
    """
    Webhook endpoint to receive updates from Telegram.
    """
    update_data = await request.json()
    update = Update(**update_data)
    await dp.feed_update(bot=bot, update=update)
    return {"status": "ok"}


@app.get("/")
async def root():
    """
    Health check endpoint.
    """
    return {"message": "ПП-Помощник v2.0 is running!"}
