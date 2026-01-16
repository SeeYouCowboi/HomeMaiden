"""
Email Provider Abstraction

Abstract base class for email providers. This allows the system to
support different email services (IMAP/SMTP, Gmail API, etc.) without
changing core logic.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class EmailMessage:
    """Standardized email message structure"""
    message_id: str  # Unique message identifier
    sender: str  # Sender email address
    recipient: str  # Recipient email address
    subject: str  # Email subject
    body: str  # Email body (plain text)
    timestamp: datetime  # When email was received
    raw_data: Dict[str, Any] = None  # Provider-specific raw data

    def __repr__(self):
        return f"EmailMessage(from={self.sender}, subject='{self.subject}')"


class EmailProvider(ABC):
    """
    Abstract base class for email providers

    Implementations must provide methods for:
    - Connecting to email service
    - Fetching unread messages
    - Sending messages
    - Marking messages as read
    - Disconnecting
    """

    @abstractmethod
    def connect(self) -> bool:
        """
        Establish connection to email service

        Returns:
            True if connection successful
        """
        pass

    @abstractmethod
    def get_unread_messages(self, limit: int = 10) -> List[EmailMessage]:
        """
        Fetch unread messages

        Args:
            limit: Maximum number of messages to fetch

        Returns:
            List of EmailMessage objects
        """
        pass

    @abstractmethod
    def send_message(self, to: str, subject: str, body: str) -> bool:
        """
        Send an email message

        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body (plain text)

        Returns:
            True if message sent successfully
        """
        pass

    @abstractmethod
    def mark_as_read(self, message_id: str) -> bool:
        """
        Mark message as read

        Args:
            message_id: Message identifier

        Returns:
            True if marked successfully
        """
        pass

    @abstractmethod
    def disconnect(self):
        """Close connection to email service"""
        pass

    @abstractmethod
    def test_connection(self) -> bool:
        """
        Test if connection is alive and working

        Returns:
            True if connection is healthy
        """
        pass
