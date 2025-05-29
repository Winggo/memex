import os
import datetime
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.errors import HttpError

GOOGLE_OAUTH_SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

def main():
    creds = None
    if os.path.exists("google_oauth_token.json"):
        creds = Credentials.from_authorized_user_file("google_oauth_token.json", GOOGLE_OAUTH_SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("google_oauth_credentials.json", GOOGLE_OAUTH_SCOPES)
            creds = flow.run_local_server(port=0)

        with open("google_oauth_token.json", "w") as token:
            token.write(creds.to_json())

    try:
        service = build("calendar", "v3", credentials=creds)
        now = datetime.datetime.now(tz=datetime.timezone.utc).isoformat()

        events_result = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=now,
                maxResults=10,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        events = events_result.get("items", [])

        for event in events:
            start = event["start"].get("dateTime", event["start"].get("date"))
            print(start, event["summary"])

    except HttpError as error:
        print(f"A Google calendar http error occurred: {error}")


if __name__ == "__main__":
    main()
