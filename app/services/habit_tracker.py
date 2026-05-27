import logging
from datetime import date, timedelta
from sqlalchemy.future import select
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot, Dispatcher
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey

from app.db.database import AsyncSessionLocal
from app.db.models import User, HabitStreak
from app.bot.handlers.free_tier import HabitCheckinStates

logger = logging.getLogger(__name__)

class NewLifeTracker:
    """
    Manages habit tracking, interval check-ins, and retention mechanics.
    """
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.bot: Bot | None = None
        self.dp: Dispatcher | None = None

    def setup(self, bot: Bot, dp: Dispatcher):
        """
        Sets up the scheduler and starts it.
        Should be called during app lifespan startup.
        """
        self.bot = bot
        self.dp = dp
        # Run daily at 10:00 AM (server time)
        self.scheduler.add_job(self.check_streaks, 'cron', hour=10, minute=0)
        self.scheduler.start()
        logger.info("NewLifeTracker scheduler started.")

    def shutdown(self):
        """
        Shuts down the scheduler.
        """
        self.scheduler.shutdown()
        logger.info("NewLifeTracker scheduler shut down.")

    async def check_streaks(self):
        """
        Checks all active habits and sends interval check-in messages.
        """
        logger.info("Running daily streak check...")
        if not self.bot:
            logger.error("Bot instance not set in NewLifeTracker.")
            return

        today = date.today()
        yesterday = today - timedelta(days=1)

        async with AsyncSessionLocal() as session:
            # Get all active streaks
            stmt = select(HabitStreak, User).join(User, HabitStreak.user_id == User.id)
            result = await session.execute(stmt)
            rows = result.all()

            for habit, user in rows:
                if habit.last_checkin == yesterday:
                    # User maintained the streak yesterday
                    streak_days = (today - habit.start_date).days

                    # Assume average savings of 150 rubles per day of avoiding a bad habit (e.g. smoking/sweets)
                    # or 150 rubles of "value" gained
                    saved_money = streak_days * 150

                    message_text = (
                        f"🌟 <b>День {streak_days}!</b>\n"
                        f"Сэкономлено {saved_money} рублей. Как самочувствие?"
                    )

                    try:
                        await self.bot.send_message(
                            chat_id=user.telegram_id,
                            text=message_text,
                            parse_mode="HTML"
                        )

                        # Set FSM state to wait for response
                        state_with_context = FSMContext(
                            storage=self.dp.storage,
                            key=StorageKey(
                                bot_id=self.bot.id,
                                chat_id=user.telegram_id,
                                user_id=user.telegram_id
                            )
                        )
                        await state_with_context.set_state(HabitCheckinStates.waiting_for_response)
                        await state_with_context.update_data(streak_days=streak_days, saved_money=saved_money)

                        logger.info(f"Sent streak check-in to user {user.telegram_id}")
                    except Exception as e:
                        logger.error(f"Failed to send streak check-in to {user.telegram_id}: {e}")

                elif habit.last_checkin < yesterday:
                    # User broke the streak
                    # Reset the streak in a real app, but for now just log it
                    logger.info(f"User {user.telegram_id} broke streak for {habit.habit_name}")

# Singleton instance
habit_tracker = NewLifeTracker()
