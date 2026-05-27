from datetime import date
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.future import select

from app.db.database import AsyncSessionLocal
from app.db.models import User, SubscriptionTier
from app.services.ai_client import ai_client
from app.services.gamification import award_xp

router = Router()

class BMIQuickStates(StatesGroup):
    waiting_for_height = State()
    waiting_for_weight = State()

class HabitCheckinStates(StatesGroup):
    waiting_for_response = State()

@router.message(Command("bmi_quick"))
async def cmd_bmi_quick(message: Message, state: FSMContext):
    """
    Initiates the quick BMI calculation flow.
    """
    await message.answer("Пожалуйста, введите ваш рост в сантиметрах (например, 175):")
    await state.set_state(BMIQuickStates.waiting_for_height)

@router.message(BMIQuickStates.waiting_for_height)
async def process_height(message: Message, state: FSMContext):
    """
    Processes the height input and asks for weight.
    """
    try:
        height = float(message.text.replace(',', '.'))
        if height <= 0 or height > 300:
            raise ValueError
    except ValueError:
        await message.answer("Пожалуйста, введите корректный рост в сантиметрах (число).")
        return

    await state.update_data(height=height)
    await message.answer("Отлично! Теперь введите ваш вес в килограммах (например, 70):")
    await state.set_state(BMIQuickStates.waiting_for_weight)

@router.message(BMIQuickStates.waiting_for_weight)
async def process_weight(message: Message, state: FSMContext):
    """
    Processes the weight input, calculates BMI, and displays the result.
    """
    try:
        weight = float(message.text.replace(',', '.'))
        if weight <= 0 or weight > 500:
            raise ValueError
    except ValueError:
        await message.answer("Пожалуйста, введите корректный вес в килограммах (число).")
        return

    data = await state.get_data()
    height_cm = data['height']
    height_m = height_cm / 100

    bmi = weight / (height_m ** 2)

    # Determine category
    if bmi < 18.5:
        category = "Недовес 🧊"
        description = "Ваш вес ниже нормы. Рекомендуется проконсультироваться с врачом или нутрициологом."
    elif 18.5 <= bmi < 24.9:
        category = "Норма 🟢"
        description = "У вас отличный вес! Поддерживайте текущий образ жизни."
    elif 25 <= bmi < 29.9:
        category = "Избыточный вес 🟡"
        description = "Есть небольшой избыток веса. Обратите внимание на питание и физическую активность."
    else:
        category = "Ожирение 🔴"
        description = "Ваш вес значительно превышает норму. Рекомендуется обратиться к специалистам."

    result_text = (
        f"📊 Ваш индекс массы тела (BMI): <b>{bmi:.1f}</b>\n"
        f"🏷 Категория: <b>{category}</b>\n\n"
        f"{description}"
    )

    teaser_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Узнать идеальный вес (LITE)", callback_data="upgrade_lite")]
        ]
    )

    await message.answer(result_text, parse_mode="HTML", reply_markup=teaser_keyboard)

    # Award XP for BMI check
    new_xp, new_league, league_changed = await award_xp(message.from_user.id, 10)
    if league_changed:
        await message.answer(f"🎉 Поздравляем! Вы перешли в новую лигу: <b>{new_league}</b>!\nТекущий опыт: {new_xp} XP", parse_mode="HTML")

    await state.clear()


@router.message(HabitCheckinStates.waiting_for_response)
async def process_habit_checkin_response(message: Message, state: FSMContext):
    """
    Handles the user's response to the daily habit check-in.
    Uses AI to generate a supportive and motivating reply.
    """
    user_response = message.text
    data = await state.get_data()
    streak_days = data.get('streak_days', 0)
    saved_money = data.get('saved_money', 0)

    prompt = (
        f"Пользователь ответил на ежедневный чекин привычки: '{user_response}'. "
        f"Его стрик без срывов составляет {streak_days} дней. Он уже сэкономил {saved_money} рублей. "
        f"Напиши короткий, мотивирующий и поддерживающий ответ (максимум 2-3 предложения), "
        f"чтобы он продолжал в том же духе. Обратись к нему как к чемпиону."
    )

    loading_message = await message.answer("Печатаю ответ... ✍️")
    ai_reply = await ai_client.generate_text(prompt=prompt)

    await loading_message.edit_text(ai_reply)
    await state.clear()


@router.message(Command("tip_day"))
async def cmd_tip_day(message: Message):
    """
    Provides a daily tip using AI.
    Rate limited to once per day for FREE tier users.
    """
    telegram_id = message.from_user.id
    today = date.today()

    async with AsyncSessionLocal() as session:
        # Fetch user
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await session.execute(stmt)
        user = result.scalars().first()

        if not user:
            await message.answer("Пожалуйста, сначала зарегистрируйтесь с помощью команды /start.")
            return

        # Check rate limit for FREE tier
        if user.subscription_tier == SubscriptionTier.FREE:
            if user.last_tip_date == today:
                await message.answer("Вы уже получали совет сегодня. Возвращайтесь завтра или улучшите подписку! 😉")
                return

        # Fetch tip from AI
        prompt = "Ты эксперт по ЗОЖ. Дай 1 короткий, научный и небанальный совет. Максимум 3 предложения."
        loading_message = await message.answer("Генерирую совет... 🧠")

        tip = await ai_client.generate_text(prompt=prompt)

        # Update last tip date
        user.last_tip_date = today
        await session.commit()

        await loading_message.edit_text(f"💡 <b>Совет дня:</b>\n\n{tip}", parse_mode="HTML")
