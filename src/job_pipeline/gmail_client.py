import base64
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
TOKEN = Path("credentials/token.json")
CREDS = Path("credentials/credentials.json")


def fetch_alert_emails(
      gmail,
      senders: list[str],
      exclude_subjects: list[str],
      days:int = 7,
) -> list[dict]:
    """Fetches emails from Gmail based on the provided criteria.

    Args:
        gamail: Authenticated Gmail service instance.
        senders: List of sender email addresses to filter by.
        exclude_subjects: List of subject lines to exclude from results.
        days: Number of days to look back for emails.
    """

    query = f"from:({' OR '.join(senders)}) newer_than:{days}d"
    for subject in exclude_subjects:
        query += f" -subject:'{subject}'"

    ids, page_token = [], None

    while True:

       res = gmail.users().messages.list(
           userId = "me", q = query, pageToken = page_token
           ).execute()

       ids += [msg["id"] for msg in res.get("messages", [])]
       page_token = res.get("nextPageToken")

       if not page_token:
           break

    emails = []
    for msg_id in ids:

      msg = gmail.users().messages().get(user = "me", id = msg_id, format = "full").execute()
      headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}
      emails.append({
         "id":msg_id,
         "date": int(msg["internalDate"]),
         "sender" : headers.get("From", ""),
         "subject": headers.get("Subject", ""),
         "body": _plain_text(msg["payload"])
      })
    return emails
      
       

def _plain_text(payload: dict) -> str:
    """Find the text/plain part of a message, however deeply nested."""

    if payload.get("mimeType") == "text/plain" and payload["body"].get("data"):
        
        return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", "replace")
    
    for part in payload.get("parts", []):
        
        text = _plain_text(part)

        if text:
            return text
        
    return ""


def _connect(interactive: bool = False):

  """ Returns authenticated Gmail service"""

  creds = _cred_check(interactive = interactive)

  return build("gmail", "v1", credentials=creds)

def _cred_check(interactive: bool = True) -> Credentials:

  """Checks if the credentials are available and valid.
  """

  creds = None
  if TOKEN.exists():
    creds = Credentials.from_authorized_user_file(TOKEN, SCOPES)

  if creds and creds.valid:
    return creds

  if creds and creds.expired and creds.refresh_token:
    creds.refresh(Request())

  elif interactive:
    flow = InstalledAppFlow.from_client_secrets_file(CREDS, SCOPES)
    creds = flow.run_local_server(port=0)

  else:
    raise RuntimeError("No valid email Gmail Token or creds found. Run script in interactive")

  TOKEN.write_text(creds.to_json())
  return creds
 
if __name__ == "__main__":
  print("main")
  #main()