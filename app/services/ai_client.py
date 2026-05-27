import logging
import asyncio
from openai import AsyncOpenAI, APIError, APITimeoutError
from app.core.config import settings

logger = logging.getLogger(__name__)

class AIAssistant:
    """
    AI Assistant client for interacting with AITunnel.
    """
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=settings.AITUNNEL_API_KEY,
            base_url="https://aitunnel.ru/v1"
        )

    async def generate_text(self, prompt: str, model: str = "deepseek-chat", response_format: dict = None) -> str:
        """
        Generates text using the specified model.
        Handles timeouts and generic API errors gracefully.
        """
        if not settings.AITUNNEL_API_KEY:
            logger.warning("AITUNNEL_API_KEY is not set. Cannot use AI Assistant.")
            return "AI временно недоступен. Пожалуйста, попробуйте позже."

        try:
            kwargs = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 1000,
                "temperature": 0.7
            }
            if response_format:
                kwargs["response_format"] = response_format

            # Set a timeout for the API call to prevent blocking indefinitely
            response = await asyncio.wait_for(
                self.client.chat.completions.create(**kwargs),
                timeout=30.0  # 30 second timeout for potentially longer generations
            )
            return response.choices[0].message.content.strip()
        except APITimeoutError:
            logger.error("AITunnel API timeout.")
            return "AI сервис не отвечает. Пожалуйста, попробуйте позже."
        except APIError as e:
            logger.error(f"AITunnel API error: {e}")
            return "Произошла ошибка при обращении к AI. Пожалуйста, попробуйте позже."
        except asyncio.TimeoutError:
            logger.error("Asyncio timeout while calling AITunnel.")
            return "Время ожидания ответа от AI истекло."
        except Exception as e:
            logger.exception(f"Unexpected error in AI Assistant: {e}")
            return "Произошла непредвиденная ошибка. Попробуйте еще раз."

    async def analyze_image(self, prompt: str, base64_image: str, model: str = "gpt-4o-mini") -> str:
        """
        Analyzes an image using the specified multimodal model.
        """
        if not settings.AITUNNEL_API_KEY:
            logger.warning("AITUNNEL_API_KEY is not set. Cannot use AI Assistant.")
            return "AI временно недоступен. Пожалуйста, попробуйте позже."

        try:
            response = await asyncio.wait_for(
                self.client.chat.completions.create(
                    model=model,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{base64_image}"
                                    }
                                }
                            ]
                        }
                    ],
                    max_tokens=300,
                ),
                timeout=30.0
            )
            return response.choices[0].message.content.strip()
        except APITimeoutError:
            logger.error("AITunnel API timeout.")
            return "AI сервис не отвечает. Пожалуйста, попробуйте позже."
        except APIError as e:
            logger.error(f"AITunnel API error: {e}")
            return "Произошла ошибка при обращении к AI. Пожалуйста, попробуйте позже."
        except asyncio.TimeoutError:
            logger.error("Asyncio timeout while calling AITunnel.")
            return "Время ожидания ответа от AI истекло."
        except Exception as e:
            logger.exception(f"Unexpected error in AI Assistant: {e}")
            return "Произошла непредвиденная ошибка. Попробуйте еще раз."

# Singleton instance
ai_client = AIAssistant()
