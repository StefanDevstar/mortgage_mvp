import os
import pickle
import base64
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from dotenv import load_dotenv

load_dotenv()

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

def get_service():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return build('gmail', 'v1', credentials=creds)

def send_email(to_address, subject, body, job_id=None, is_html=False, is_client_email=False):
    service = get_service()

    # If HTML email requested
    if is_html:
        if is_client_email:
            # 🧑‍💼 Clean client version (no buttons)
            html_body = f"""
            <html>
                <body style="font-family:Arial,sans-serif;line-height:1.6">
                    {body}
                </body>
            </html>
            """
        else:
            # 👨‍💼 Broker version with buttons
            html_body = f"""
            <html>
                <body style="font-family:Arial,sans-serif;line-height:1.6">
                    {body}
                    <br><br>
                    <a href="{os.getenv("APP_URL")}/send-email?job_id={job_id}"
                       style="display:inline-block;padding:10px 20px;background-color:#28a745;color:white;text-decoration:none;border-radius:5px">
                       ✅ Send to Client
                    </a>
                    &nbsp;
                    <a href="{os.getenv("APP_URL")}/edit-email?job_id={job_id}"
                       style="display:inline-block;padding:10px 20px;background-color:#007bff;color:white;text-decoration:none;border-radius:5px">
                       ✏️ Edit Email
                    </a>
                </body>
            </html>
            """
        message_text = f"To: {to_address}\r\n" \
                       f"Subject: {subject}\r\n" \
                       f"Content-Type: text/html; charset=UTF-8\r\n\r\n{html_body}"
    else:
        # Plain text fallback
        message_text = f"To: {to_address}\r\n" \
                       f"Subject: {subject}\r\n\r\n{body}"

    message = {
        'raw': base64.urlsafe_b64encode(message_text.encode("utf-8")).decode("utf-8")
    }

    service.users().messages().send(userId='me', body=message).execute()
    print(f"📨 Email sent to {to_address} | Subject: {subject}")

def fetch_unread_replies():
    service = get_service()
    results = service.users().messages().list(userId='me', labelIds=['INBOX'], q="is:unread").execute()
    messages = results.get('messages', [])
    replies = []

    for msg in messages:
        msg_data = service.users().messages().get(userId='me', id=msg['id'], format='full').execute()
        payload = msg_data.get('payload', {})
        headers = payload.get('headers', [])
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
        from_email = next((h['value'] for h in headers if h['name'] == 'From'), '')
        snippet = msg_data.get('snippet', '')

        replies.append({
            "from": from_email,
            "subject": subject,
            "snippet": snippet,
            "message_id": msg['id'],
            "in_reply_to_job": extract_job_id_from_subject(subject)
        })

        # ✅ Mark message as read
        service.users().messages().modify(
            userId='me',
            id=msg['id'],
            body={'removeLabelIds': ['UNREAD']}
        ).execute()

    return replies

# ✅ Utility: Extract job_id if encoded in subject like "Job #abc123..."
def extract_job_id_from_subject(subject):
    if "job_id=" in subject:
        try:
            return subject.split("job_id=")[-1].split()[0].strip()
        except Exception:
            return None
    return None
