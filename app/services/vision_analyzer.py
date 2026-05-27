import base64
from app.services.ai_client import ai_client

class PhotoDietologist:
    """
    Service for analyzing food photos to estimate calories and macros.
    """
    def __init__(self):
        self.prompt = (
            "Проанализируй блюдо. Оцени скрытые калории по текстуре "
            "(масло, соусы), дай оценку насыщения (1-10) и краткую сводку КБЖУ"
        )

    async def analyze_food(self, photo_bytes: bytes) -> str:
        """
        Converts image bytes to base64 and analyzes it using the AI client.
        """
        base64_image = base64.b64encode(photo_bytes).decode('utf-8')
        result = await ai_client.analyze_image(prompt=self.prompt, base64_image=base64_image)
        return result

# Singleton instance
photo_dietologist = PhotoDietologist()
