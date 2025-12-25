
"""
Service for translating text using Google Gemini.
"""
import os
import logging
import google.generativeai as genai
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)

class TranslationService:
    def __init__(self):
        from app.config import settings
        
        # Try gemini_api_key first, fallback to google_api_key
        self.api_key = settings.gemini_api_key or settings.google_api_key
        
        if not self.api_key:
            logger.warning("GEMINI_API_KEY/GOOGLE_API_KEY not configured. Translation service will fail if called.")
            self.model = None
        else:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-2.5-flash')

    async def translate_text(self, text: str, target_language: str) -> str:
        """
        Translates text to the target language using Gemini.
        """
        if not self.model:
             raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Translation service is not configured (missing API key)."
            )

        try:
            prompt = f"Translate the following text to {target_language}. Return only the translated text, preserving the formatting and tone:\n\n{text}"
            
            response = await self.model.generate_content_async(prompt)
            
            if response.text:
                return response.text.strip()
            else:
                logger.error("Empty response from Gemini translation")
                raise ValueError("Received empty response from translation service")
                
        except Exception as e:
            logger.error(f"Translation failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Translation failed: {str(e)}"
            )

translation_service = TranslationService()
