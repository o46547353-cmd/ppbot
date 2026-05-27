import json
import logging
from typing import List
from pydantic import BaseModel, Field

from app.services.ai_client import ai_client

logger = logging.getLogger(__name__)

class Exercise(BaseModel):
    name: str = Field(..., description="Name of the exercise")
    sets: int = Field(..., description="Number of sets")
    reps: str = Field(..., description="Number of repetitions (e.g., '8-10', '12')")
    rpe: float = Field(..., description="Rate of Perceived Exertion (1-10)")

class WorkoutDay(BaseModel):
    day_name: str = Field(..., description="Name of the day (e.g., 'Понедельник' or 'День 1')")
    exercises: List[Exercise] = Field(..., description="List of exercises for this day")

class WorkoutProgram(BaseModel):
    program_name: str = Field(..., description="Name of the overall program")
    days: List[WorkoutDay] = Field(..., description="List of workout days")

class IronCoach:
    """
    AI Coach service for generating personalized workout programs.
    """
    async def generate_program(self, profile: dict) -> WorkoutProgram | None:
        """
        Generates a workout program based on user profile and parses it into a Pydantic model.
        """
        experience = profile.get("experience", "новичок")
        equipment = profile.get("equipment", "без инвентаря")

        prompt = (
            f"Создай программу тренировок для пользователя. "
            f"Опыт: {experience}. Инвентарь: {equipment}. "
            f"Верни ответ строго в формате JSON, соответствующем следующей структуре: "
            f'{{"program_name": "Название", "days": [{{"day_name": "День 1", "exercises": [{{"name": "Приседания", "sets": 3, "reps": "10-15", "rpe": 7.5}}]}}]}}'
        )

        raw_json = await ai_client.generate_text(
            prompt=prompt,
            response_format={"type": "json_object"}
        )

        try:
            # Parse the JSON and validate it with Pydantic
            data = json.loads(raw_json)
            program = WorkoutProgram(**data)
            return program
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON from IronCoach: {e}\nRaw output: {raw_json}")
            return None
        except ValueError as e:
            logger.error(f"Pydantic validation failed for IronCoach output: {e}\nRaw output: {raw_json}")
            return None

# Singleton instance
iron_coach = IronCoach()
