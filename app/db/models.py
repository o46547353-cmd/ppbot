from enum import Enum
from datetime import date
from typing import Optional

from sqlalchemy import String, Integer, BigInteger, Date
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class SubscriptionTier(str, Enum):
    FREE = "FREE"
    LITE = "LITE"
    SPORT = "SPORT"
    PRO = "PRO"
    VIP = "VIP"


class User(Base):
    """
    User model.
    """
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    subscription_tier: Mapped[SubscriptionTier] = mapped_column(default=SubscriptionTier.FREE)
    xp_points: Mapped[int] = mapped_column(Integer, default=0)
    league: Mapped[Optional[str]] = mapped_column(String, nullable=True)


class HabitStreak(Base):
    """
    Habit Streak model.
    """
    __tablename__ = "habit_streaks"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    habit_name: Mapped[str] = mapped_column(String)
    start_date: Mapped[date] = mapped_column(Date)
    last_checkin: Mapped[date] = mapped_column(Date)


class WorkoutLog(Base):
    """
    Workout Log model.
    """
    __tablename__ = "workout_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    date: Mapped[date] = mapped_column(Date)
    duration_min: Mapped[int] = mapped_column(Integer)
    rpe_score: Mapped[int] = mapped_column(Integer)
