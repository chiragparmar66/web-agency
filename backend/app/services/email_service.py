"""
Email Notification Service for Nexus Studio.
Dispatches formatted notifications to studio administration upon inquiry submission.
Fails gracefully when SMTP credentials are not configured in environment.
"""
import asyncio
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
from typing import Any, Dict, Optional

from app.core.config import settings
from app.core.logging import logger


class EmailService:
    @classmethod
    async def send_inquiry_notification(cls, inquiry_data: Dict[str, Any]) -> bool:
        """
        Asynchronously dispatch a notification email to the configured studio admin email.
        Runs synchronously in a thread pool to avoid blocking the async event loop.
        """
        return await asyncio.to_thread(cls._send_inquiry_sync, inquiry_data)

    @classmethod
    def _send_inquiry_sync(cls, inquiry_data: Dict[str, Any]) -> bool:
        sender_name = inquiry_data.get("name", "Prospective Client")
        sender_email = inquiry_data.get("email") or "Not provided"
        sender_phone = inquiry_data.get("phone") or "Not provided"
        subject_line = inquiry_data.get("subject") or "Project Consultation Inquiry"
        message_content = inquiry_data.get("message", "")
        pkg = inquiry_data.get("selected_package") or "General Inquiry"
        timestamp = inquiry_data.get("created_at")
        if isinstance(timestamp, datetime):
            timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")
        else:
            timestamp_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        recipient_email = settings.CONTACT_NOTIFICATION_EMAIL

        # Check if SMTP configuration is present
        if not settings.SMTP_HOST:
            logger.info(
                f"[EmailService] SMTP_HOST not configured. Notification for new inquiry from "
                f"'{sender_name}' ({sender_email}) recorded locally without external dispatch."
            )
            return False

        from_email = settings.SMTP_FROM_EMAIL or settings.SMTP_USER or "notifications@nexusstudio.dev"

        # Build Multipart Email (Plain text + HTML)
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"[Nexus Studio] New Lead: {sender_name} - {subject_line}"
        msg["From"] = f"Nexus Studio Alerts <{from_email}>"
        msg["To"] = recipient_email

        plain_text = f"""Nexus Studio — New Client Inquiry

A new project consultation has been received via the Nexus Studio website:

• Name: {sender_name}
• Email: {sender_email}
• Phone / WhatsApp: {sender_phone}
• Subject: {subject_line}
• Selected Package: {pkg}
• Received At: {timestamp_str}

Message / Project Scope:
--------------------------------------------------
{message_content}
--------------------------------------------------

Access the Studio Operations Console to review and manage this lead:
http://localhost:3000/dashboard/admin
"""

        html_content = f"""<!DOCTYPE html>
<html>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f8fafc; margin: 0; padding: 24px; color: #0f172a;">
  <div style="max-width: 600px; margin: 0 auto; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
    <div style="background-color: #0f172a; padding: 20px 24px; border-bottom: 3px solid #2563eb;">
      <h1 style="color: #ffffff; margin: 0; font-size: 18px; font-weight: 700; letter-spacing: -0.02em;">NEXUS STUDIO</h1>
      <p style="color: #94a3b8; margin: 4px 0 0 0; font-size: 12px;">New Client Project Inquiry</p>
    </div>
    <div style="padding: 24px;">
      <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px; font-size: 13px;">
        <tr style="border-bottom: 1px solid #f1f5f9;">
          <td style="padding: 8px 0; color: #64748b; font-weight: 600; width: 140px;">Client Name:</td>
          <td style="padding: 8px 0; color: #0f172a; font-weight: 600;">{sender_name}</td>
        </tr>
        <tr style="border-bottom: 1px solid #f1f5f9;">
          <td style="padding: 8px 0; color: #64748b; font-weight: 600;">Email Address:</td>
          <td style="padding: 8px 0; color: #2563eb;"><a href="mailto:{sender_email}" style="color: #2563eb; text-decoration: none;">{sender_email}</a></td>
        </tr>
        <tr style="border-bottom: 1px solid #f1f5f9;">
          <td style="padding: 8px 0; color: #64748b; font-weight: 600;">Phone / WhatsApp:</td>
          <td style="padding: 8px 0; color: #0f172a;">{sender_phone}</td>
        </tr>
        <tr style="border-bottom: 1px solid #f1f5f9;">
          <td style="padding: 8px 0; color: #64748b; font-weight: 600;">Subject:</td>
          <td style="padding: 8px 0; color: #0f172a;">{subject_line}</td>
        </tr>
        <tr style="border-bottom: 1px solid #f1f5f9;">
          <td style="padding: 8px 0; color: #64748b; font-weight: 600;">Scope / Package:</td>
          <td style="padding: 8px 0; color: #0f172a;">{pkg}</td>
        </tr>
        <tr>
          <td style="padding: 8px 0; color: #64748b; font-weight: 600;">Received At:</td>
          <td style="padding: 8px 0; color: #64748b;">{timestamp_str}</td>
        </tr>
      </table>

      <div style="background-color: #f8fafc; border-left: 3px solid #2563eb; padding: 16px; border-radius: 4px; margin-top: 16px;">
        <h3 style="margin: 0 0 8px 0; font-size: 12px; text-transform: uppercase; color: #475569; letter-spacing: 0.05em;">Client Message</h3>
        <p style="margin: 0; font-size: 13px; line-height: 1.6; color: #1e293b; white-space: pre-wrap;">{message_content}</p>
      </div>
    </div>
    <div style="background-color: #f1f5f9; padding: 12px 24px; text-align: center; font-size: 11px; color: #64748b;">
      Sent automatically by Nexus Studio Lead Notification Engine
    </div>
  </div>
</body>
</html>
"""
        msg.attach(MIMEText(plain_text, "plain"))
        msg.attach(MIMEText(html_content, "html"))

        try:
            port = settings.SMTP_PORT
            if port == 465:
                with smtplib.SMTP_SSL(settings.SMTP_HOST, port, timeout=10) as server:
                    if settings.SMTP_USER and settings.SMTP_PASSWORD:
                        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                    server.send_message(msg)
            else:
                with smtplib.SMTP(settings.SMTP_HOST, port, timeout=10) as server:
                    if settings.SMTP_USE_TLS:
                        server.starttls()
                    if settings.SMTP_USER and settings.SMTP_PASSWORD:
                        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                    server.send_message(msg)

            logger.info(f"[EmailService] Notification successfully dispatched for inquiry from '{sender_name}' to {recipient_email}")
            return True
        except Exception as e:
            # Never leak SMTP credentials or raw passwords in logs
            logger.warning(f"[EmailService] Failed to dispatch email notification via {settings.SMTP_HOST}:{port}: {type(e).__name__}")
            return False
