"""
IMAP/SMTP Email Provider

Implementation of EmailProvider using IMAP for receiving emails
and SMTP for sending emails. This is the standard email protocol
used by services like Gmail, QQ Mail, Outlook, etc.
"""

import imaplib
import smtplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any
from datetime import datetime
import logging

from .email_provider import EmailProvider, EmailMessage


class IMAPSMTPProvider(EmailProvider):
    """IMAP/SMTP email provider implementation"""

    def __init__(self, config: Dict[str, Any], logger: logging.Logger):
        """
        Initialize IMAP/SMTP provider

        Args:
            config: Configuration dictionary with keys:
                - imap_server: IMAP server address
                - smtp_server: SMTP server address
                - smtp_port: SMTP server port
                - username: Email username
                - password: Email password
                - allowed_senders: List of allowed sender emails
            logger: Logger instance
        """
        self.config = config
        self.logger = logger

        self.imap_server = config['imap_server']
        self.smtp_server = config['smtp_server']
        self.smtp_port = config['smtp_port']
        self.username = config['username']
        self.password = config['password']
        self.allowed_senders = config.get('allowed_senders', [])

        self.imap_conn = None

    def connect(self) -> bool:
        """
        Connect to IMAP server

        Returns:
            True if connection successful
        """
        try:
            self.logger.info(f"Connecting to IMAP server: {self.imap_server}")
            self.imap_conn = imaplib.IMAP4_SSL(self.imap_server)
            self.imap_conn.login(self.username, self.password)
            self.logger.info("IMAP connection established")
            return True
        except Exception as e:
            self.logger.error(f"IMAP connection failed: {e}")
            return False

    def get_unread_messages(self, limit: int = 10) -> List[EmailMessage]:
        """
        Fetch unread messages from inbox

        Args:
            limit: Maximum number of messages to fetch

        Returns:
            List of EmailMessage objects
        """
        messages = []

        try:
            if not self.imap_conn:
                self.logger.error("IMAP connection not established")
                return messages

            # Select inbox
            self.imap_conn.select("inbox")

            # Search for unseen emails
            status, message_ids = self.imap_conn.search(None, 'UNSEEN')
            if status != 'OK' or not message_ids[0]:
                self.logger.debug("No unread messages found")
                return messages

            # Get message IDs
            id_list = message_ids[0].split()

            # Limit number of messages
            id_list = id_list[-limit:] if len(id_list) > limit else id_list

            # Fetch each message
            for msg_id in id_list:
                try:
                    email_msg = self._fetch_message(msg_id)
                    if email_msg:
                        # Check sender whitelist
                        if self.allowed_senders and email_msg.sender not in self.allowed_senders:
                            self.logger.warning(f"Blocked email from non-whitelisted sender: {email_msg.sender}")
                            # Mark as read to avoid processing again
                            self.mark_as_read(msg_id.decode())
                            continue

                        messages.append(email_msg)
                except Exception as e:
                    self.logger.error(f"Error processing message {msg_id}: {e}")
                    continue

            self.logger.info(f"Fetched {len(messages)} unread messages")
            return messages

        except Exception as e:
            self.logger.error(f"Error fetching unread messages: {e}")
            return messages

    def _fetch_message(self, msg_id: bytes) -> EmailMessage:
        """
        Fetch and parse a single message

        Args:
            msg_id: Message ID

        Returns:
            EmailMessage object or None
        """
        try:
            status, data = self.imap_conn.fetch(msg_id, '(RFC822)')
            if status != 'OK':
                return None

            msg = email.message_from_bytes(data[0][1])

            # Parse sender
            sender = email.utils.parseaddr(msg.get("From"))[1]

            # Parse subject
            subject = msg.get("Subject", "")

            # Parse body
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    if content_type == "text/plain":
                        try:
                            body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                            break
                        except Exception as e:
                            self.logger.warning(f"Error decoding message body: {e}")
            else:
                try:
                    body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
                except Exception as e:
                    self.logger.warning(f"Error decoding message body: {e}")

            # Create EmailMessage object
            email_message = EmailMessage(
                message_id=msg_id.decode(),
                sender=sender,
                recipient=self.username,
                subject=subject,
                body=body.strip(),
                timestamp=datetime.now(),
                raw_data={"msg": msg}
            )

            return email_message

        except Exception as e:
            self.logger.error(f"Error parsing message: {e}")
            return None

    def send_message(self, to: str, subject: str, body: str) -> bool:
        """
        Send an email message via SMTP

        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body (plain text)

        Returns:
            True if message sent successfully
        """
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.username
            msg['To'] = to
            msg['Subject'] = subject

            msg.attach(MIMEText(body, 'plain', 'utf-8'))

            # Connect to SMTP server and send
            self.logger.debug(f"Connecting to SMTP server: {self.smtp_server}:{self.smtp_port}")
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.username, self.password)

            text = msg.as_string()
            server.sendmail(self.username, to, text)
            server.quit()

            self.logger.info(f"Email sent successfully to {to}: {subject}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to send email: {e}")
            return False

    def mark_as_read(self, message_id: str) -> bool:
        """
        Mark message as read

        Args:
            message_id: Message ID

        Returns:
            True if marked successfully
        """
        try:
            if not self.imap_conn:
                self.logger.error("IMAP connection not established")
                return False

            # Convert message_id to bytes if it's a string
            if isinstance(message_id, str):
                message_id = message_id.encode()

            self.imap_conn.store(message_id, '+FLAGS', '\\Seen')
            self.logger.debug(f"Marked message {message_id} as read")
            return True

        except Exception as e:
            self.logger.error(f"Error marking message as read: {e}")
            return False

    def disconnect(self):
        """Close IMAP connection"""
        try:
            if self.imap_conn:
                self.imap_conn.logout()
                self.imap_conn = None
                self.logger.info("IMAP connection closed")
        except Exception as e:
            self.logger.error(f"Error closing IMAP connection: {e}")

    def test_connection(self) -> bool:
        """
        Test if IMAP connection is alive

        Returns:
            True if connection is healthy
        """
        try:
            if not self.imap_conn:
                return False

            # Try to select inbox as a test
            status, _ = self.imap_conn.select("inbox")
            return status == 'OK'

        except Exception as e:
            self.logger.error(f"Connection test failed: {e}")
            return False

    def reconnect(self) -> bool:
        """
        Reconnect to IMAP server

        Returns:
            True if reconnection successful
        """
        self.logger.info("Attempting to reconnect to IMAP server")
        self.disconnect()
        return self.connect()
