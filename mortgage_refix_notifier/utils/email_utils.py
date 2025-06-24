# utils/email_utils.py

from email.message import EmailMessage

def create_email(to_email: str, subject: str, body: str) -> EmailMessage:
    msg = EmailMessage()
    msg['To'] = to_email
    msg['From'] = "noreply@mortgagebot.com"
    msg['Subject'] = subject
    msg.set_content(body)
    return msg
