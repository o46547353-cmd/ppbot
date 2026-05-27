import logging
from sqlalchemy.future import select

from app.db.database import AsyncSessionLocal
from app.db.models import User, SubscriptionTier

logger = logging.getLogger(__name__)

class CrossSellEngine:
    """
    Engine to contextually suggest tier upgrades.
    """
    async def analyze_and_suggest(self, telegram_id: int, last_action: str) -> str | None:
        """
        Analyzes the user's tier and recent action to provide a contextual upsell message.
        """
        async with AsyncSessionLocal() as session:
            stmt = select(User).where(User.telegram_id == telegram_id)
            result = await session.execute(stmt)
            user = result.scalars().first()

            if not user:
                return None

            # Don't upsell VIPs
            if user.subscription_tier == SubscriptionTier.VIP:
                return None

            if last_action == 'workout_completed':
                if user.subscription_tier in (SubscriptionTier.FREE, SubscriptionTier.LITE):
                    return (
                        "\n\n<i>🔥 Тренировка прошла отлично? "
                        "Чтобы закрепить результат, нужен правильный рацион. "
                        "Переходите на тариф SPORT или PRO, чтобы разблокировать "
                        "нашего AI-диетолога и планы питания!</i> 🥗"
                    )

            # Other potential cross-sell logic can be added here
            return None

# Singleton instance
cross_sell_engine = CrossSellEngine()
