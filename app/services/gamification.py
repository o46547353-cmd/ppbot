import logging
from sqlalchemy.future import select

from app.db.database import AsyncSessionLocal
from app.db.models import User

logger = logging.getLogger(__name__)

# Define league thresholds
LEAGUES = {
    "Новичок 👶": 0,
    "Любитель 🏃‍♂️": 100,
    "Атлет 🏋️‍♀️": 500,
    "Киборг 🦾": 1500
}

def get_league_for_xp(xp: int) -> str:
    """
    Determines the league based on XP points.
    """
    current_league = "Новичок 👶"
    for league, threshold in sorted(LEAGUES.items(), key=lambda item: item[1]):
        if xp >= threshold:
            current_league = league
        else:
            break
    return current_league

async def award_xp(telegram_id: int, xp_amount: int) -> tuple[int, str, bool]:
    """
    Awards XP to a user and updates their league if necessary.
    Returns a tuple of (new_total_xp, new_league, league_changed).
    """
    async with AsyncSessionLocal() as session:
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await session.execute(stmt)
        user = result.scalars().first()

        if not user:
            logger.warning(f"Attempted to award XP to non-existent user {telegram_id}")
            return 0, "Новичок 👶", False

        # Add XP
        user.xp_points += xp_amount
        new_xp = user.xp_points

        # Determine new league
        new_league = get_league_for_xp(new_xp)

        league_changed = False
        if user.league != new_league:
            user.league = new_league
            league_changed = True

        await session.commit()
        return new_xp, new_league, league_changed
