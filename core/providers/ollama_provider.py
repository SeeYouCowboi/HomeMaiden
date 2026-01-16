"""
Ollama LLM Provider

Implementation of LLMProvider using Ollama - a local LLM runner.
Ollama allows running models like Llama, Mistral, Qwen, etc. locally.
"""

import ollama
import json
import re
from typing import Dict, Any
import logging

from .llm_provider import LLMProvider, LLMResponse


class OllamaProvider(LLMProvider):
    """Ollama LLM provider implementation"""

    def __init__(self, config: Dict[str, Any], logger: logging.Logger):
        """
        Initialize Ollama provider

        Args:
            config: Configuration dictionary with keys:
                - model: Model name (e.g., 'qwen3:8b', 'llama2')
                - system_prompt: Default system prompt
                - host: Optional Ollama host (default: localhost)
            logger: Logger instance
        """
        self.config = config
        self.logger = logger

        self.model = config.get('model', 'qwen3:8b')
        self.system_prompt = config.get('system_prompt', '')
        self.host = config.get('host', None)  # None = use default

        self.logger.info(f"Ollama provider initialized with model: {self.model}")

    def parse_command(
        self,
        prompt: str,
        system_prompt: str = None
    ) -> LLMResponse:
        """
        Parse natural language into structured commands using Ollama

        Args:
            prompt: User's natural language input
            system_prompt: Optional system prompt override

        Returns:
            LLMResponse with parsed commands or error
        """
        # Use provided system prompt or default
        sys_prompt = system_prompt if system_prompt is not None else self.system_prompt

        try:
            self.logger.debug(f"Calling Ollama model: {self.model}")

            # Prepare messages
            messages = [
                {'role': 'system', 'content': sys_prompt},
                {'role': 'user', 'content': prompt},
            ]

            # Call Ollama
            response = ollama.chat(
                model=self.model,
                messages=messages,
                options={'host': self.host} if self.host else {}
            )

            # Extract content
            content = response['message']['content']
            self.logger.debug(f"LLM raw output: {content}")

            # Clean and parse JSON
            parsed_data = self._parse_json_response(content)

            if parsed_data is not None:
                self.logger.info(f"LLM parsing succeeded: {len(parsed_data)} commands")
                return LLMResponse(
                    success=True,
                    data=parsed_data,
                    error="",
                    raw=content,
                    model=self.model
                )
            else:
                error_msg = "Failed to parse JSON from LLM output"
                self.logger.error(error_msg)
                return LLMResponse(
                    success=False,
                    data=[],
                    error=error_msg,
                    raw=content,
                    model=self.model
                )

        except json.JSONDecodeError as e:
            error_msg = f"JSON decode error: {str(e)}"
            self.logger.error(error_msg)
            return LLMResponse(
                success=False,
                data=[],
                error=error_msg,
                raw=content if 'content' in locals() else "",
                model=self.model
            )

        except Exception as e:
            error_msg = f"LLM call failed: {str(e)}"
            self.logger.error(error_msg)
            return LLMResponse(
                success=False,
                data=[],
                error=error_msg,
                raw="",
                model=self.model
            )

    def _parse_json_response(self, content: str) -> list:
        """
        Parse JSON from LLM response, handling various formats

        The LLM might wrap JSON in markdown code blocks or add extra text.
        This method tries to extract and parse the JSON.

        Args:
            content: Raw LLM output

        Returns:
            Parsed list of commands, or None if parsing failed
        """
        try:
            # Try direct parse first
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        # Try removing markdown code blocks
        # Pattern: ```json ... ``` or ``` ... ```
        patterns = [
            r'```json\s*(.*?)\s*```',
            r'```\s*(.*?)\s*```',
        ]

        for pattern in patterns:
            match = re.search(pattern, content, re.DOTALL)
            if match:
                try:
                    json_str = match.group(1).strip()
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    continue

        # Try finding JSON array pattern
        # Look for [ ... ] in the text
        match = re.search(r'\[.*\]', content, re.DOTALL)
        if match:
            try:
                json_str = match.group(0)
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass

        # All parsing attempts failed
        return None

    def test_connection(self) -> bool:
        """
        Test if Ollama service is available

        Returns:
            True if service is accessible
        """
        try:
            # Try to list models as a connection test
            ollama.list()
            self.logger.debug("Ollama connection test successful")
            return True
        except Exception as e:
            self.logger.error(f"Ollama connection test failed: {e}")
            return False

    def get_model_name(self) -> str:
        """
        Get the name of the model being used

        Returns:
            Model name
        """
        return self.model

    def set_model(self, model: str):
        """
        Change the model being used

        Args:
            model: New model name
        """
        self.logger.info(f"Switching Ollama model from {self.model} to {model}")
        self.model = model

    def list_available_models(self) -> list:
        """
        List all available models in Ollama

        Returns:
            List of model names
        """
        try:
            models = ollama.list()
            model_names = [m['name'] for m in models.get('models', [])]
            self.logger.debug(f"Available Ollama models: {model_names}")
            return model_names
        except Exception as e:
            self.logger.error(f"Failed to list Ollama models: {e}")
            return []
