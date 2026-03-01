"""
Contract Q&A Service - Answer natural language questions about contracts.
"""

import logging
import json
import re
from typing import List, Dict, Any
from app.services.llm_service import llm_service
from app.models.schemas import ContractAnswerResponse, ContractQuote

logger = logging.getLogger(__name__)


class ContractQAService:
    """Service for answering questions about contracts using LLM."""
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for Q&A agent."""
        return """You are a legal expert specializing in contract analysis. Your task is to answer questions about employment contracts accurately and concisely.

Rules:
1. ONLY answer based on information in the contract
2. If the answer is not in the contract, say "This information is not specified in the contract"
3. Always quote relevant contract sections to support your answer
4. Be precise and avoid speculation
5. Use clear, non-technical language

Output Format (JSON):
{
  "answer": "Direct answer to the question",
  "quotes": [
    {"text": "Relevant contract excerpt", "confidence": 0.95}
  ],
  "answerable": true/false,
  "confidence": 0.85
}

Important:
- If answerable=false, quotes should be empty and confidence should reflect uncertainty
- Each quote should be an exact excerpt from the contract
- Confidence should reflect how certain you are about the answer
"""
    
    def _get_general_knowledge_prompt(self) -> str:
        """Get system prompt for general legal knowledge questions."""
        return """You are a legal expert and business advisor. Your task is to answer general questions about legal terms, market practices, and business norms.

Rules:
1. Answer based on general legal knowledge, not specific contract text
2. Be accurate and cite common legal standards when relevant
3. If asking about "standard practices", reference industry norms
4. For legal terminology, explain clearly in simple English
5. Use clear, non-technical language whenever possible

Output Format (JSON):
{
  "answer": "Direct, informative answer",
  "quotes": [],
  "answerable": true,
  "confidence": 0.85
}

Important:
- This is general knowledge, so quotes should typically be empty
- Confidence reflects how certain you are about the general principle
"""
    
    def _build_qa_prompt(
        self, 
        contract_text: str, 
        question: str, 
        contract_type: str
    ) -> str:
        """Build Q&A prompt for LLM."""
        return f"""CONTRACT TYPE: {contract_type}

CONTRACT:
{contract_text}

QUESTION: {question}

Analyze the contract and answer the question. Provide supporting quotes from the exact contract text.
Output ONLY the JSON response. No other text."""
    
    def _build_general_knowledge_prompt(self, question: str) -> str:
        """Build prompt for general knowledge questions."""
        return f"""QUESTION: {question}

Answer this legal or business-related question based on general knowledge and standard practices.
Output ONLY the JSON response. No other text."""
    
    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """
        Parse LLM JSON response.
        
        Expected format:
        {
          "answer": "...",
          "quotes": [{"text": "...", "confidence": 0.9}],
          "answerable": true,
          "confidence": 0.85
        }
        """
        try:
            # Extract JSON from response (handle markdown code blocks)
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Try to find raw JSON
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    raise ValueError("No JSON found in response")
            
            parsed = json.loads(json_str)
            
            # Validate required fields
            required_fields = ["answer", "answerable", "confidence"]
            for field in required_fields:
                if field not in parsed:
                    raise ValueError(f"Missing required field: {field}")
            
            # Ensure quotes is a list
            if "quotes" not in parsed:
                parsed["quotes"] = []
            
            return parsed
            
        except Exception as e:
            logger.error(f"Failed to parse LLM response: {e}")
            logger.error(f"Response was: {response}")
            
            # Fallback response
            return {
                "answer": "I encountered an error processing this question. Please try rephrasing it.",
                "quotes": [],
                "answerable": False,
                "confidence": 0.0
            }
    
    async def answer_question(
        self,
        contract_text: str,
        question: str,
        contract_type: str = "employment",
        is_general_knowledge: bool = False
    ) -> ContractAnswerResponse:
        """
        Answer a question about the contract using LLM.
        
        Args:
            contract_text: Full contract text
            question: User's question
            contract_type: Type of contract
            is_general_knowledge: If True, answer based on general knowledge not contract
        
        Returns:
            ContractAnswerResponse with answer and supporting quotes
        """
        logger.info(f"Answering question: '{question}' (contract type: {contract_type}, general_knowledge={is_general_knowledge})")
        
        try:
            # Query Gemini directly (use Gemini for Q&A)
            from app.services.llm_service import GeminiClient
            
            gemini = GeminiClient()
            
            if is_general_knowledge:
                # Answer based on general knowledge, not contract context
                system_prompt = self._get_general_knowledge_prompt()
                user_prompt = self._build_general_knowledge_prompt(question)
            else:
                # Answer based on contract text
                system_prompt = self._get_system_prompt()
                user_prompt = self._build_qa_prompt(contract_text, question, contract_type)
            
            response_dict = await gemini.generate(
                prompt=user_prompt,
                system_prompt=system_prompt
            )
            
            if not response_dict.get("success"):
                raise Exception(f"LLM generation failed: {response_dict.get('error')}")
            
            response = response_dict["content"]
            
            # Parse response
            parsed = self._parse_llm_response(response)
            
            # Convert quotes to ContractQuote objects
            supporting_quotes = [
                ContractQuote(
                    text=quote.get("text", ""),
                    confidence=quote.get("confidence", 0.5)
                )
                for quote in parsed.get("quotes", [])
            ]
            
            result = ContractAnswerResponse(
                question=question,
                answer=parsed["answer"],
                supporting_quotes=supporting_quotes,
                confidence=parsed["confidence"],
                answerable=parsed["answerable"]
            )
            
            logger.info(
                f"Q&A completed: answerable={result.answerable}, "
                f"confidence={result.confidence:.2f}, "
                f"quotes={len(result.supporting_quotes)}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Q&A failed for question '{question}': {e}", exc_info=True)
            
            # Return error response
            return ContractAnswerResponse(
                question=question,
                answer="I encountered an error while processing your question. Please try again or rephrase your question.",
                supporting_quotes=[],
                confidence=0.0,
                answerable=False
            )


# Global instance
contract_qa_service = ContractQAService()
