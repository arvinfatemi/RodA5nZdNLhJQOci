"""
Email notification service using SMTP.

Provides simple email sending functionality as an alternative to Telegram.
Supports common email providers (Gmail, Outlook, etc.) via SMTP.
"""

import logging
import smtplib
from email.message import EmailMessage
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


def send_email(
    subject: str,
    body: str,
    *,
    smtp_host: str,
    smtp_port: int = 587,
    email_from: str,
    email_password: str,
    email_to: str,
    use_tls: bool = True,
) -> Dict[str, Any]:
    """
    Send an email via SMTP.

    Args:
        subject: Email subject line
        body: Email body (plain text)
        smtp_host: SMTP server hostname (e.g., smtp.gmail.com)
        smtp_port: SMTP server port (default: 587 for TLS)
        email_from: Sender email address
        email_password: Email password or app password
        email_to: Recipient email address
        use_tls: Whether to use TLS (default: True)

    Returns:
        Dict with success status and message

    Raises:
        Exception: If email sending fails
    """
    try:
        # Create message
        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = email_from
        msg['To'] = email_to
        msg.set_content(body)

        # Connect and send
        if use_tls:
            with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as smtp:
                smtp.starttls()
                smtp.login(email_from, email_password)
                smtp.send_message(msg)
        else:
            # For non-TLS (usually port 465 with SSL)
            with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=10) as smtp:
                smtp.login(email_from, email_password)
                smtp.send_message(msg)

        logger.info(f"Email sent successfully to {email_to}: {subject}")
        return {
            "success": True,
            "message": "Email sent successfully",
            "to": email_to,
            "subject": subject,
        }

    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        raise Exception(f"Email send failed: {str(e)}")


def send_notification_email(
    text: str,
    *,
    smtp_host: Optional[str] = None,
    smtp_port: Optional[int] = None,
    email_from: Optional[str] = None,
    email_password: Optional[str] = None,
    email_to: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Send a notification email with default subject.

    This is a convenience wrapper around send_email() for bot notifications.

    Args:
        text: Notification message body
        smtp_host: SMTP server hostname
        smtp_port: SMTP server port (default: 587)
        email_from: Sender email address
        email_password: Email password
        email_to: Recipient email address

    Returns:
        Dict with success status and message

    Raises:
        ValueError: If required email settings are missing
        Exception: If email sending fails
    """
    # Validate required settings
    if not all([smtp_host, email_from, email_password, email_to]):
        missing = []
        if not smtp_host:
            missing.append("smtp_host")
        if not email_from:
            missing.append("email_from")
        if not email_password:
            missing.append("email_password")
        if not email_to:
            missing.append("email_to")

        raise ValueError(
            f"Missing required email configuration: {', '.join(missing)}. "
            "Please set EMAIL_SMTP_HOST, EMAIL_FROM, EMAIL_PASSWORD, and EMAIL_TO in your .env file."
        )

    # Use default port if not specified
    smtp_port = smtp_port or 587

    # Create subject from first line of text or truncate
    subject = text.split('\n')[0][:50]
    if len(text.split('\n')[0]) > 50:
        subject += "..."

    # Add bot prefix to subject
    subject = f"[BTC Trading Bot] {subject}"

    return send_email(
        subject=subject,
        body=text,
        smtp_host=smtp_host,
        smtp_port=smtp_port,
        email_from=email_from,
        email_password=email_password,
        email_to=email_to,
    )


def send_html_email(
    subject: str,
    html_body: str,
    plain_text_body: str,
    *,
    smtp_host: str,
    smtp_port: int = 587,
    email_from: str,
    email_password: str,
    email_to: str,
    use_tls: bool = True,
) -> Dict[str, Any]:
    """
    Send an HTML email with plain text fallback via SMTP.

    Args:
        subject: Email subject line
        html_body: Email body (HTML formatted)
        plain_text_body: Plain text version (fallback)
        smtp_host: SMTP server hostname (e.g., smtp.gmail.com)
        smtp_port: SMTP server port (default: 587 for TLS)
        email_from: Sender email address
        email_password: Email password or app password
        email_to: Recipient email address
        use_tls: Whether to use TLS (default: True)

    Returns:
        Dict with success status and message

    Raises:
        Exception: If email sending fails
    """
    try:
        # Create message with both HTML and plain text
        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = email_from
        msg['To'] = email_to

        # Set plain text content as default
        msg.set_content(plain_text_body)

        # Add HTML alternative
        msg.add_alternative(html_body, subtype='html')

        # Connect and send
        if use_tls:
            with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as smtp:
                smtp.starttls()
                smtp.login(email_from, email_password)
                smtp.send_message(msg)
        else:
            # For non-TLS (usually port 465 with SSL)
            with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=10) as smtp:
                smtp.login(email_from, email_password)
                smtp.send_message(msg)

        logger.info(f"HTML email sent successfully to {email_to}: {subject}")
        return {
            "success": True,
            "message": "HTML email sent successfully",
            "to": email_to,
            "subject": subject,
        }

    except Exception as e:
        logger.error(f"Failed to send HTML email: {e}")
        raise Exception(f"HTML email send failed: {str(e)}")


def validate_email_config(
    smtp_host: Optional[str] = None,
    email_from: Optional[str] = None,
    email_password: Optional[str] = None,
    email_to: Optional[str] = None,
) -> bool:
    """
    Check if email configuration is complete.

    Args:
        smtp_host: SMTP server hostname
        email_from: Sender email address
        email_password: Email password
        email_to: Recipient email address

    Returns:
        True if all required settings are present, False otherwise
    """
    return all([smtp_host, email_from, email_password, email_to])
