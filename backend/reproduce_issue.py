
import sys
import os
import asyncio
from pathlib import Path

# Add backend to sys.path
sys.path.append(os.getcwd())

from app.services.translation_service import translation_service

async def main():
    print(f"GEMINI_API_KEY env var: {os.getenv('GEMINI_API_KEY')}")
    try:
        print("Testing translation...")
        result = await translation_service.translate_text("Hello", "Hindi")
        print(f"Translation result: {result}")
    except Exception as e:
        print(f"Translation failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
