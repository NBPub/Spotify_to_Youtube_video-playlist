import os
from google.auth.exceptions import RefreshError
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/youtube"]
TOKEN_FILE = "token.json"
SECRETS_FILE = "client_secrets.json"


def get_youtube_client():
    creds = None

    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except RefreshError:
                raise SystemExit(
                    "YouTube token has expired and could not be refreshed.\n"
                    "Delete token.json and re-run to trigger a new login:\n"
                    "  rm token.json\n"
                    "See USAGE.md § Re-authentication for details."
                )
        else:
            if not os.path.exists(SECRETS_FILE):
                raise FileNotFoundError(
                    f"{SECRETS_FILE} not found. Download OAuth credentials "
                    "from Google Cloud Console and save as client_secrets.json"
                )
            flow = InstalledAppFlow.from_client_secrets_file(SECRETS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())

    return build("youtube", "v3", credentials=creds)
