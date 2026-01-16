"""Core Providers - Email and LLM abstractions"""

from .email_provider import EmailProvider, EmailMessage
from .imap_smtp_provider import IMAPSMTPProvider
from .llm_provider import LLMProvider, LLMResponse
from .ollama_provider import OllamaProvider

__all__ = [
    'EmailProvider',
    'EmailMessage',
    'IMAPSMTPProvider',
    'LLMProvider',
    'LLMResponse',
    'OllamaProvider',
]
