from aiogram import Router
from app.bot.handlers.start import router as start_router
from app.bot.handlers.free_tier import router as free_tier_router
from app.bot.handlers.paid_tier import router as paid_tier_router

router = Router()
router.include_router(start_router)
router.include_router(free_tier_router)
router.include_router(paid_tier_router)
