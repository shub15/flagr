"""
Multi-LLM service wrapper providing unified interface for OpenAI, Gemini, and Grok.
"""

import asyncio
import logging
from typing import Optional, Dict, Any, List
from abc import ABC, abstractmethod
import openai
import google.generativeai as genai
import httpx
from app.config import settings

logger = logging.getLogger(__name__)


class BaseLLMClient(ABC):
    """Abstract base class for LLM clients."""
    
    @abstractmethod
    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """Generate response from LLM."""
        pass
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return provider name."""
        pass


class OpenAIClient(BaseLLMClient):
    """OpenAI API client."""
    
    def __init__(self):
        self.client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model
    
    @property
    def provider_name(self) -> str:
        return "openai"
    
    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """Generate response from OpenAI."""
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = await asyncio.wait_for(
                self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.3,
                    timeout=settings.llm_timeout_seconds
                ),
                timeout=settings.llm_timeout_seconds
            )
            
            content = response.choices[0].message.content
            return {
                "success": True,
                "content": content,
                "provider": self.provider_name,
                "model": self.model
            }
        except asyncio.TimeoutError:
            logger.error(f"{self.provider_name} request timed out")
            return {"success": False, "error": "timeout", "provider": self.provider_name}
        except Exception as e:
            logger.error(f"{self.provider_name} error: {str(e)}")
            return {"success": False, "error": str(e), "provider": self.provider_name}


class GeminiClient(BaseLLMClient):
    """Google Gemini API client."""
    
    def __init__(self):
        genai.configure(api_key=settings.google_api_key)
        self.model = genai.GenerativeModel(settings.gemini_model)
    
    @property
    def provider_name(self) -> str:
        return "gemini"
    
    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """Generate response from Gemini."""
        try:
            full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            
            # Gemini doesn't have native async, so we run in executor
            loop = asyncio.get_event_loop()
            response = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: self.model.generate_content(full_prompt)
                ),
                timeout=settings.llm_timeout_seconds
            )
            
            return {
                "success": True,
                "content": response.text,
                "provider": self.provider_name,
                "model": settings.gemini_model
            }
        except asyncio.TimeoutError:
            logger.error(f"{self.provider_name} request timed out")
            return {"success": False, "error": "timeout", "provider": self.provider_name}
        except Exception as e:
            logger.error(f"{self.provider_name} error: {str(e)}")
            return {"success": False, "error": str(e), "provider": self.provider_name}


class GrokClient(BaseLLMClient):
    """Grok (xAI) API client."""
    
    def __init__(self):
        self.api_key = settings.grok_api_key
        self.model = settings.grok_model
        self.base_url = "https://api.x.ai/v1"
    
    @property
    def provider_name(self) -> str:
        return "grok"
    
    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """Generate response from Grok."""
        if not self.api_key:
            logger.warning("Grok API key not configured, skipping")
            return {"success": False, "error": "no_api_key", "provider": self.provider_name}
        
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            async with httpx.AsyncClient() as client:
                response = await asyncio.wait_for(
                    client.post(
                        f"{self.base_url}/chat/completions",
                        headers={
                            "Authorization": f"Bearer {self.api_key}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": self.model,
                            "messages": messages,
                            "temperature": 0.3
                        },
                        timeout=settings.llm_timeout_seconds
                    ),
                    timeout=settings.llm_timeout_seconds
                )
                
                if response.status_code == 200:
                    data = response.json()
                    content = data["choices"][0]["message"]["content"]
                    return {
                        "success": True,
                        "content": content,
                        "provider": self.provider_name,
                        "model": self.model
                    }
                else:
                    logger.error(f"{self.provider_name} returned status {response.status_code}")
                    return {
                        "success": False,
                        "error": f"http_{response.status_code}",
                        "provider": self.provider_name
                    }
        except asyncio.TimeoutError:
            logger.error(f"{self.provider_name} request timed out")
            return {"success": False, "error": "timeout", "provider": self.provider_name}
        except Exception as e:
            logger.error(f"{self.provider_name} error: {str(e)}")
            return {"success": False, "error": str(e), "provider": self.provider_name}


class MultiLLMService:
    """Unified service for managing multiple LLM providers."""
    
    def __init__(self):
        self.openai = OpenAIClient()
        self.gemini = GeminiClient()
        self.grok = GrokClient()
        self.clients = [self.openai, self.gemini, self.grok]
    
    async def generate_with_retry(
        self,
        client: BaseLLMClient,
        prompt: str,
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate with retry logic."""
        for attempt in range(settings.max_retries):
            result = await client.generate(prompt, system_prompt)
            if result["success"]:
                return result
            
            if attempt < settings.max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                logger.info(f"Retrying {client.provider_name} after {wait_time}s")
                await asyncio.sleep(wait_time)
        
        return result
    
    async def generate_parallel(
        self,
        prompt: str,
        system_prompt: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Generate responses from all providers in parallel."""
        tasks = [
            self.generate_with_retry(client, prompt, system_prompt)
            for client in self.clients
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions
        valid_results = []
        for result in results:
            if isinstance(result, dict):
                valid_results.append(result)
            else:
                logger.error(f"Exception in parallel generation: {result}")
        
        return valid_results


# Global instance
llm_service = MultiLLMService()
