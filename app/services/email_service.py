"""
Email service for sending verification emails via Resend
"""
import resend
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Email service using Resend"""

    def __init__(self):
        resend.api_key = settings.RESEND_API_KEY
        self.sender_email = settings.RESEND_SENDER_EMAIL

    def _get_verification_email_html(self, code: str) -> str:
        """Generate HTML template for verification email"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .container {{
                    background-color: #f9fafb;
                    border-radius: 12px;
                    padding: 40px;
                }}
                .logo {{
                    font-size: 28px;
                    font-weight: bold;
                    color: #6366f1;
                    margin-bottom: 24px;
                }}
                .title {{
                    font-size: 24px;
                    font-weight: 600;
                    margin-bottom: 16px;
                }}
                .code-box {{
                    background-color: #ffffff;
                    border: 2px solid #e5e7eb;
                    border-radius: 8px;
                    padding: 20px;
                    text-align: center;
                    margin: 24px 0;
                }}
                .code {{
                    font-size: 32px;
                    font-weight: bold;
                    letter-spacing: 8px;
                    color: #6366f1;
                }}
                .note {{
                    font-size: 14px;
                    color: #6b7280;
                    margin-top: 24px;
                }}
                .footer {{
                    margin-top: 32px;
                    padding-top: 16px;
                    border-top: 1px solid #e5e7eb;
                    font-size: 12px;
                    color: #9ca3af;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="logo">CodePath</div>
                <div class="title">이메일 인증</div>
                <p>안녕하세요! CodePath에 가입해 주셔서 감사합니다.</p>
                <p>아래 인증 코드를 입력하여 이메일 인증을 완료해 주세요.</p>
                <div class="code-box">
                    <div class="code">{code}</div>
                </div>
                <p class="note">
                    이 코드는 5분 동안 유효합니다.<br>
                    본인이 요청하지 않은 경우 이 이메일을 무시하세요.
                </p>
                <div class="footer">
                    이 이메일은 CodePath에서 자동 발송되었습니다.
                </div>
            </div>
        </body>
        </html>
        """

    async def send_verification_code(self, email: str, code: str) -> bool:
        """
        Send verification code email via Resend

        Args:
            email: Recipient email address
            code: 6-digit verification code

        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            params = {
                "from": self.sender_email,
                "to": [email],
                "subject": "[CodePath] 이메일 인증 코드",
                "html": self._get_verification_email_html(code),
            }

            response = resend.Emails.send(params)
            logger.info(f"Verification email sent to {email}, ID: {response.get('id')}")
            return True
        except Exception as e:
            logger.error(f"Failed to send verification email to {email}: {str(e)}")
            return False


# Global email service instance
email_service = EmailService()
