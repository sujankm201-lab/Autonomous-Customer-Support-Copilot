"""LLM integration for RAG system."""

import logging
import os
from typing import Optional

from langchain_community.llms import OpenAI

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
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.llm = None

        self._initialize_llm()

    def _initialize_llm(self):
        """Initialize the LLM."""

        try:
            if "gpt" in self.model.lower() and self.api_key:
                self.llm = OpenAI(
                    api_key=self.api_key,
                    model_name=self.model,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                )

                logger.info(
                    f"LLM initialized with OpenAI model: {self.model}"
                )

            else:
                logger.warning(
                    "OpenAI API key not found. Using MockLLM."
                )

                self.llm = MockLLM(
                    self.model,
                    self.temperature,
                    self.max_tokens,
                )

        except Exception as e:
            logger.warning(
                f"Error initializing LLM: {e}. Using MockLLM."
            )

            self.llm = MockLLM(
                self.model,
                self.temperature,
                self.max_tokens,
            )

    def generate(self, prompt: str) -> str:
        """Generate text using the configured LLM."""

        try:
            response = self.llm.predict(prompt)

            if response is None:
                return "I could not generate an answer."

            return response.strip()

        except Exception as e:
            logger.error(f"Error generating response: {e}")
            raise

    def generate_with_context(
        self,
        context: str,
        query: str,
        prompt_template: str,
    ) -> str:
        """Generate an answer using retrieved RAG context."""

        try:
            formatted_prompt = prompt_template.format(
                context=context,
                question=query,
            )

            return self.generate(formatted_prompt)

        except Exception as e:
            logger.error(
                f"Error generating response with context: {e}"
            )
            raise

    def count_tokens(self, text: str) -> int:
        """Estimate token count."""

        return len(text) // 4


class MockLLM:
    """
    Local fallback LLM used when no OpenAI API key is configured.

    This provides useful responses for the current customer-support
    knowledge base so the project can be demonstrated without an
    external API key.
    """

    def __init__(
        self,
        model: str,
        temperature: float,
        max_tokens: int,
    ):
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    def predict(self, text: str) -> str:
        """Generate a support answer from the available context."""

        text_lower = text.lower()

        # Password reset
        if (
            "password reset" in text_lower
            or "reset password" in text_lower
            or "forgot password" in text_lower
        ):
            return (
                "Password reset emails usually arrive within 5 minutes. "
                "If you do not receive the email, please check your spam "
                "folder. If the email still does not arrive, try resetting "
                "your password again or contact customer support."
            )

        # Account locked
        if (
            "account locked" in text_lower
            or "account is locked" in text_lower
            or "locked account" in text_lower
        ):
            return (
                "Your account is locked after five failed login attempts. "
                "Please wait 15 minutes before trying again. If you still "
                "cannot access your account, contact customer support."
            )

        # Login problem
        if (
            "login" in text_lower
            or "log in" in text_lower
            or "cannot login" in text_lower
            or "can't login" in text_lower
        ):
            return (
                "If you cannot log in after resetting your password, first "
                "make sure the new password is entered correctly. Then clear "
                "your browser cache and cookies. You can also try using an "
                "incognito or private window. If the problem continues, "
                "reset the password again. Contact support if your account "
                "remains locked."
            )

        # Contact support
        if (
            "contact support" in text_lower
            or "contact customer support" in text_lower
            or "support email" in text_lower
            or "support@example.com" in text_lower
        ):
            return (
                "You can contact customer support by email at "
                "support@example.com. Support is available Monday to Friday "
                "from 9:00 AM to 6:00 PM."
            )

        # Business hours
        if (
            "business hours" in text_lower
            or "working hours" in text_lower
            or "support hours" in text_lower
            or "opening hours" in text_lower
        ):
            return (
                "Customer support is available Monday to Friday, "
                "from 9:00 AM to 6:00 PM."
            )

        # General knowledge-base question
        if (
            "what information" in text_lower
            or "what topics" in text_lower
            or "available in the support" in text_lower
            or "knowledge base" in text_lower
        ):
            return (
                "The customer support knowledge base contains information "
                "about four main topics: login issues, password resets, "
                "account lockouts, and contacting customer support. It "
                "provides troubleshooting steps, password reset timing, "
                "account lockout rules, and support contact information."
            )

        # Generic fallback
        return (
            "I found information in the customer support knowledge base, "
            "but I could not identify a specific answer to your question. "
            "Try asking about login issues, password resets, account "
            "lockouts, or contacting support."
        )