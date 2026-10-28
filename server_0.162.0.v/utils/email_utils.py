import os
import resend
from dotenv import load_dotenv

load_dotenv()

resend.api_key = os.getenv("RESEND_API_KEY")

MAIL_FROM = os.getenv("MAIL_FROM")
MAIL_FROM_NAME = os.getenv("MAIL_FROM_NAME")
FRONTEND_URL = os.getenv("FRONTEND_URL")

def send_password_reset_email(to_email: str, token: str) -> None:
    """sending a password reset email via Resend. called within BackgroundTasks."""
    reset_url = f"{FRONTEND_URL}?token={token}"

    params: resend.Emails.SendParams = {
        "from": f"{MAIL_FROM_NAME} <{MAIL_FROM}>",
        "to": [to_email],
        "subject": "Password reset",
        "html": f"""
            <div style="font-family:-apple-system,Arial,sans-serif;max-width:480px;margin:auto;">
              <h2>Password reset</h2>
              <p>Tap the button below to set a new password:</p>
              <p>
                <a href="{reset_url}"
                   style="background:#007AFF;color:#fff;padding:12px 20px;
                          border-radius:8px;text-decoration:none;display:inline-block;">
                   Reset password
                </a>
              </p>
              <p style="color:#888;font-size:13px;">
                The link is valid for 60 minutes.
                If you didn't request a reset, just ignore this email.
              </p>
            </div>
        """,
        "text": (
            f"To reset your password, open this link:\n\n{reset_url}\n\n"
            f"The link is valid for 60 minutes. "
            f"If you didn't request a reset, ignore this email."
        ),
    }

    try:
        email = resend.Emails.send(params)
        print(f"[Resend] sent to {to_email}, id={email.get('id')}")

    except Exception as e:
        
        # email is sent in the background log it so that the entire request doesnt fail
        print(f"[Resend] FAILED to send to {to_email}: {e}")