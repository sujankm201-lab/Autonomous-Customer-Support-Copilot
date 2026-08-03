"""LLM integration for RAG system."""
import logging
from typing import Optional
from langchain_core.language_models.llms import LLM
from langchain_core.callbacks.manager import CallbackManagerForLLMRun
from langchain_core.outputs import LLMResult
from langchain_community.llms import OpenAI
import os

logger = logging.getLogger(__name__)


class LLMService:
    """Service for managing LLM interactions."""

    def __init__(
        self,
        model: str = "gpt-3.5-turbo",
        temperature: float = 0.7,
        max_tokens: int = 1000,
        api_key: Optional[str] = None,
    ):
        """
        Initialize LLMService.
        
        Args:
            model: Model name/identifier
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
            api_key: API key for the LLM service
        """
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.llm = None
        self._initialize_llm()

    def _initialize_llm(self):
        """Initialize the LLM."""
        try:
            if "gpt" in self.model.lower():
                # Use OpenAI
                if not self.api_key:
                    logger.warning("OpenAI API key not found. Set OPENAI_API_KEY environment variable.")
                    # Create a mock LLM for testing
                    self.llm = MockLLM(self.model, self.temperature, self.max_tokens)
                else:
                    self.llm = OpenAI(
                        api_key=self.api_key,
                        model_name=self.model,
                        temperature=self.temperature,
                        max_tokens=self.max_tokens,
                    )
                logger.info(f"LLM initialized with model: {self.model}")
            else:
                logger.warning(f"Unsupported model: {self.model}. Using MockLLM for testing.")
                self.llm = MockLLM(self.model, self.temperature, self.max_tokens)
        except Exception as e:
            logger.warning(f"Error initializing LLM: {str(e)}. Using MockLLM for testing.")
            self.llm = MockLLM(self.model, self.temperature, self.max_tokens)

    def generate(self, prompt: str) -> str:
        """
        Generate text using the LLM.
        
        Args:
            prompt: Input prompt
        
        Returns:
            Generated text
        """
        try:
            response = self.llm.predict(prompt)
            return response.strip()
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            raise

    def generate_with_context(self, context: str, query: str, prompt_template: str) -> str:
        """
        Generate response using context and query.
        
        Args:
            context: Context/knowledge base information
            query: User query
            prompt_template: Prompt template string
        
        Returns:
            Generated response
        """
        try:
            # Format the prompt with context and query
            formatted_prompt = prompt_template.format(context=context, question=query)
            response = self.generate(formatted_prompt)
            return response
        except Exception as e:
            logger.error(f"Error generating response with context: {str(e)}")
            raise

    def count_tokens(self, text: str) -> int:
        """
        Estimate token count for text.
        
        Args:
            text: Text to count tokens for
        
        Returns:
            Approximate token count
        """
        # Simple estimation: approximately 1 token per 4 characters
        return len(text) // 4


class MockLLM:
    """Mock LLM for testing without API keys."""

    def __init__(self, model: str, temperature: float, max_tokens: int):
        """Initialize MockLLM."""
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    def predict(self, text: str) -> str:
        """Generate mock response."""
        # Return a generic response based on the input
        if "confidence" in text.lower():
            return '{"confidence_score": 0.85, "explanation": "Good match with context"}'
        elif "follow" in text.lower():
            return "1. What are other common issues?\n2. How to prevent this?\n3. Where to find more help?"
        elif "summary" in text.lower():
            return "This is a summary of the provided context."
        else:
            # Try to extract question and provide a reasonable answer
            if "?" in text:
                return f"Based on the provided information, I can help you with that question about customer support. This is a helpful response that addresses your needs using the available knowledge base."
            return f"Thank you for your question. Based on the available information, I would like to provide you with a comprehensive answer."
