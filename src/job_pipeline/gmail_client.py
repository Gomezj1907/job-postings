import os.path
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
TOKEN = Path("credentials/token.json")
CREDS = Path("credentials/credentials.json")


def connect_gmail(creds, days = 7):
  """Connects to my email account
  """
  creds = None
  # The file token.json stores the user's access and refresh tokens, and is
  # created automatically when the authorization flow completes for the first
  # time.
  if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
  # If there are no (valid) credentials available, let the user log in.
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file(
          "credentials.json", SCOPES
      )
      creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open("token.json", "w") as token:
      token.write(creds.to_json())

  try:
    # Call the Gmail API
    service = build("gmail", "v1", credentials=creds)
    results = service.users().labels().list(userId="me").execute()
    labels = results.get("labels", [])
 
    if not labels:
      print("No labels found.")
      return
    print("labels are available Yay!")
    print("Labels:")
    for label in labels:
      print(label["name"])

  except HttpError as error:
    # TODO(developer) - Handle errors from gmail API.
    print(f"An error occurred: {error}")


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