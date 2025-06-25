import os
import pickle
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

# Replace with your broker email
BROKER_EMAIL = 'broker@example.com'

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

def send_email(to_address, subject, body):
    service = get_service()
    message = {
        'raw': base64.urlsafe_b64encode(
            f"To: {to_address}\\r\\nSubject: {subject}\\r\\n\\r\\n{body}".encode()
        ).decode()
    }
    service.users().messages().send(userId='me', body=message).execute()

def fetch_unread_replies():
    service = get_service()
    results = service.users().messages().list(userId='me', q='is:unread in:inbox').execute()
    messages = results.get('messages', [])
    replies = []
    for msg in messages:
        m = service.users().messages().get(userId='me', id=msg['id'], format='full').execute()
        # parse headers to find In-Reply-To and body snippet
        in_reply_to = None
        snippet = m.get('snippet')
        headers = m.get('payload', {}).get('headers', [])
        for h in headers:
            if h['name'] == 'In-Reply-To':
                in_reply_to = h['value']
        replies.append({'in_reply_to_job': in_reply_to, 'content': snippet})
        service.users().messages().modify(userId='me', id=msg['id'], body={'removeLabelIds': ['UNREAD']}).execute()
    return replies