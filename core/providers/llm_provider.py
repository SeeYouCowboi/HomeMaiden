"""
LLM Provider Abstraction

Abstract base class for LLM (Large Language Model) providers.
This allows the system to support different LLM services
(Ollama, OpenAI, Claude, etc.) without changing core logic.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
from dataclasses import dataclass


@dataclass
class LLMResponse:
    """Standardized LLM response structure"""
    success: bool  # Whether parsing succeeded
    data: List[Dict[str, Any]]  # Parsed commands (list of dicts)
    error: str  # Error message if failed
    raw: str  # Raw LLM output
    model: str = ""  # Model used for generation

    def __repr__(self):
        if self.success:
            return f"LLMResponse(success=True, commands={len(self.data)})"
        else:
            return f"LLMResponse(success=False, error='{self.error}')"


class LLMProvider(ABC):
    """
    Abstract base class for LLM providers

    Implementations must provide methods for:
    - Parsing natural language into structured commands
    - Testing connection/availability
    """

    @abstractmethod
    def parse_command(
        self,
        prompt: str,
        system_prompt: str = None
    ) -> LLMResponse:
        """
        Parse natural language into structured commands

        The LLM should convert user input into a JSON array of commands.
        Expected format: [{"action": "command_name", "param1": "value1", ...}]

        Args:
            prompt: User's natural language input
            system_prompt: Optional system prompt override

        Returns:
            LLMResponse with parsed commands or error
        """
        pass

    @abstractmethod
    def test_connection(self) -> bool:
        """
        Test if LLM service is available

        Returns:
            True if service is accessible
        """
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """
        Get the name of the model being used

        Returns:
            Model name/identifier
        """
        pass
