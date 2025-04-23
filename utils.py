import smtplib
import os
from email.message import EmailMessage
from dotenv import load_dotenv
import yagmail

# Load environment variables
load_dotenv()

EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

def send_email(recipient_email, subject, body):
    try:
        msg = EmailMessage()
        msg.set_content(body)
        msg["Subject"] = subject
        msg["From"] = EMAIL_SENDER
        msg["To"] = recipient_email

        yag = yagmail.SMTP("noreplybnac@gmail.com", "dbcypotjpfngpwpz")
        yag.send(
            to=recipient_email,
            subject=subject,
            contents=body
        )

        print(f"✅ Email sent to {recipient_email}")
        return True
    except Exception as e:
        print(f"❌ Error sending email: {e}")
        return False