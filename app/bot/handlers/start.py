from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from sqlalchemy.future import select

from app.db.database import AsyncSessionLocal
from app.db.models import User

router = Router()

def get_main_menu() -> ReplyKeyboardMarkup:
    """
    Returns the main menu keyboard.
    """
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🏋️ Тренировки"), KeyboardButton(text="🥗 Питание")],
            [KeyboardButton(text="🏆 Профиль"), KeyboardButton(text="⚙️ Настройки")],
        ],
        resize_keyboard=True
    )
    return keyboard

@router.message(CommandStart())
async def cmd_start(message: Message):
    """
    Handles the /start command.
    Registers the user if they don't exist and shows the main menu.
    """
    telegram_id = message.from_user.id
    username = message.from_user.username

    async with AsyncSessionLocal() as session:
        # Check if user exists
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await session.execute(stmt)
        user = result.scalars().first()

        if not user:
            # Register new user
            new_user = User(telegram_id=telegram_id, username=username)
            session.add(new_user)
            await session.commit()
            welcome_text = (
                f"Привет, {message.from_user.full_name}! 👋\n"
                "Добро пожаловать в «ПП-Помощник v2.0».\n"
                "Я помогу тебе достичь твоих фитнес-целей!"
            )
        else:
            welcome_text = f"С возвращением, {message.from_user.full_name}! 👋"

    await message.answer(welcome_text, reply_markup=get_main_menu())
