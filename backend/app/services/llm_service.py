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


class MistralClient(BaseLLMClient):
    """Mistral AI API client."""
    
    def __init__(self):
        self.api_key = settings.mistral_api_key
        self.model = settings.mistral_model
        self.base_url = "https://api.mistral.ai/v1"
    
    @property
    def provider_name(self) -> str:
        return "mistral"
    
    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """Generate response from Mistral."""
        if not self.api_key:
            logger.warning("Mistral API key not configured, skipping")
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


class GroqClient(BaseLLMClient):
    """Groq (fast inference) API client."""
    
    def __init__(self):
        self.api_key = settings.groq_api_key
        self.model = settings.groq_models
        self.base_url = "https://api.groq.com/openai/v1"
    
    @property
    def provider_name(self) -> str:
        return "groq"
    
    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """Generate response from Groq."""
        if not self.api_key:
            logger.warning("Groq API key not configured, skipping")
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
                            "temperature": 0.3,
                            "max_tokens": 2000
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
    """Unified service for managing multiple LLM providers with rate limiting."""
    
    def __init__(self):
        # Council members (for agents)
        self.openai = OpenAIClient() if settings.enable_openai else None
        self.mistral = MistralClient() if settings.enable_mistral and settings.mistral_api_key else None
        
        # Multiple Groq clients with different models
        self.groq_clients = []
        if settings.enable_groq and settings.groq_api_key:
            groq_models = [m.strip() for m in settings.groq_models.split(',')]
            for model_name in groq_models:
                client = GroqClient()
                client.model = model_name  # Override default model
                self.groq_clients.append(client)
                logger.info(f"✅ Added Groq client: {model_name}")
        
        # Referee (Gemini only - not in council)
        self.gemini_referee = GeminiClient()
        
        # Collect all enabled council clients
        self.clients = []
        if self.openai:
            self.clients.append(self.openai)
        if self.mistral:
            self.clients.append(self.mistral)
        self.clients.extend(self.groq_clients)  # Add all Groq clients
        
        # Semaphore to limit concurrent API calls (prevents rate limiting)
        self.semaphore = asyncio.Semaphore(settings.max_concurrent_llm_calls)
        
        logger.info(f"🚀 MultiLLMService initialized with {len(self.clients)} council providers")
        logger.info("🎯 Referee: Gemini (single LLM)")
    
    async def generate_with_retry(
        self,
        client: BaseLLMClient,
        prompt: str,
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate with retry logic and exponential backoff for rate limits."""
        
        # Use semaphore to limit concurrent calls
        async with self.semaphore:
            for attempt in range(settings.max_retries):
                result = await client.generate(prompt, system_prompt)
                
                if result["success"]:
                    return result
                
                # Check if it's a rate limit error (429)
                error_msg = result.get("error", "").lower()
                is_rate_limit = "429" in error_msg or "rate" in error_msg or "quota" in error_msg
                
                if attempt < settings.max_retries - 1:
                    if settings.exponential_backoff and is_rate_limit:
                        # Exponential backoff: 2s, 4s, 8s, etc.
                        wait_time = settings.retry_delay_seconds * (2 ** attempt)
                    else:
                        # Fixed delay
                        wait_time = settings.retry_delay_seconds
                    
                    logger.warning(
                        f"{client.provider_name} failed (attempt {attempt + 1}/{settings.max_retries}). "
                        f"Error: {result.get('error')}. Retrying in {wait_time}s..."
                    )
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(
                        f"{client.provider_name} failed after {settings.max_retries} attempts: {result.get('error')}"
                    )
            
            return result
    
    async def generate_parallel(
        self,
        prompt: str,
        system_prompt: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Generate responses from all enabled providers in parallel (with rate limiting)."""
        if not self.clients:
            logger.error("No LLM providers enabled!")
            return []
        
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
