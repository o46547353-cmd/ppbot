import io
from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.future import select

from app.db.database import AsyncSessionLocal
from app.db.models import User, SubscriptionTier
from app.services.vision_analyzer import photo_dietologist
from app.services.workout_generator import iron_coach

router = Router()

class WorkoutPlanStates(StatesGroup):
    waiting_for_experience = State()
    waiting_for_equipment = State()


async def check_paid_tier(message: Message) -> bool:
    """
    Helper function to check if a user is on a paid tier.
    """
    async with AsyncSessionLocal() as session:
        stmt = select(User).where(User.telegram_id == message.from_user.id)
        result = await session.execute(stmt)
        user = result.scalars().first()

        if not user or user.subscription_tier == SubscriptionTier.FREE:
            await message.answer("Эта функция доступна только в платных тарифах (LITE и выше). ⭐️")
            return False
        return True


@router.message(F.photo)
async def handle_food_photo(message: Message, bot: Bot):
    """
    Handles uploaded photos, analyzing them using PhotoDietologist if the user is on a paid tier.
    """
    if not await check_paid_tier(message):
        return

    loading_message = await message.answer("Анализирую ваше блюдо... 📸")

    try:
        # Get the largest available photo size
        photo = message.photo[-1]
        file = await bot.get_file(photo.file_id)

        # Download the file into memory
        file_io = io.BytesIO()
        await bot.download_file(file.file_path, destination=file_io)
        photo_bytes = file_io.getvalue()

        # Analyze using the service
        analysis_result = await photo_dietologist.analyze_food(photo_bytes)

        await loading_message.edit_text(f"🍽 <b>Результат анализа:</b>\n\n{analysis_result}", parse_mode="HTML")

    except Exception as e:
        await loading_message.edit_text("Произошла ошибка при анализе фото. Попробуйте загрузить изображение еще раз.")


@router.message(Command("workout_plan"))
async def cmd_workout_plan(message: Message, state: FSMContext):
    """
    Initiates the workout generation flow.
    """
    if not await check_paid_tier(message):
        return

    await message.answer("Давайте составим вам программу! Какой у вас опыт тренировок (новичок, средний, продвинутый)?")
    await state.set_state(WorkoutPlanStates.waiting_for_experience)


@router.message(WorkoutPlanStates.waiting_for_experience)
async def process_experience(message: Message, state: FSMContext):
    """
    Saves experience and asks for equipment.
    """
    await state.update_data(experience=message.text)
    await message.answer("Какой инвентарь вам доступен? (Например: гантели, турник, фитнес-резинки или 'без инвентаря')")
    await state.set_state(WorkoutPlanStates.waiting_for_equipment)


@router.message(WorkoutPlanStates.waiting_for_equipment)
async def process_equipment(message: Message, state: FSMContext):
    """
    Saves equipment, generates the plan using IronCoach, and formats it as Markdown.
    """
    await state.update_data(equipment=message.text)
    profile = await state.get_data()

    loading_message = await message.answer("Создаю вашу персональную программу... 🏋️‍♂️")

    program = await iron_coach.generate_program(profile)

    if not program:
        await loading_message.edit_text("Не удалось сгенерировать программу. Попробуйте еще раз позже.")
        await state.clear()
        return

    # Format the program into Markdown
    markdown_text = f"📋 <b>{program.program_name}</b>\n\n"

    for day in program.days:
        markdown_text += f"📅 <b>{day.day_name}</b>\n"
        for ex in day.exercises:
            markdown_text += f"  • {ex.name}: {ex.sets} подходов x {ex.reps} повторений (RPE: {ex.rpe})\n"
        markdown_text += "\n"

    await loading_message.edit_text(markdown_text, parse_mode="HTML")
    await state.clear()
