import os
from datetime import datetime
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from ..utils.constants import GOOGLE_OAUTH_SCOPES


class GcalendarService:
    def __init__(self, credentials_file="google_oauth_credentials.json", token_file="google_oauth_token.json"):
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.service = None
        self._authenticate()


    def _authenticate(self):
        """Authenticate with GCalendar API"""
        print(f"[Google Calendar Client] Authenticating...")
        creds = None
        
        # Load existing token if available
        if os.path.exists(self.token_file):
            creds = Credentials.from_authorized_user_file(self.token_file, GOOGLE_OAUTH_SCOPES)
        
        # If there are no (valid) credentials available, let the user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                print(f"[Google Calendar Client] Refreshing token...")
                creds.refresh(Request())
                print(f"[Google Calendar Client] Refreshing token completed")
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, GOOGLE_OAUTH_SCOPES
                )
                creds = flow.run_local_server(port=0)
            
            # Save the credentials for the next run
            with open(self.token_file, "w") as token:
                token.write(creds.to_json())
        
        print(f"[Google Calendar Client] Creds validity: {creds.valid}")
        self.service = build("calendar", "v3", credentials=creds)


    def get_events_for_date(self, calendar_id="primary", date=None, max_results=10):
        """
        Retrieve all events for given calendar & given date
        Defaults to primary calendar & today
        """
        if not date:
            date = datetime.now().astimezone()
        start = date.replace(hour=0, minute=0, second=0, microsecond=0)            
        end = date.replace(hour=23, minute=59, second=50, microsecond=999999)

        events_result = self.service.events().list(
            calendarId=calendar_id,
            maxResults=max_results,
            singleEvents=True,
            orderBy="startTime",
            timeMin=start.isoformat(),
            timeMax=end.isoformat(),
            fields="items(id,summary,location,description,start,end,attendees,status,creator,organizer),nextPageToken"
        ).execute()
        events = events_result.get("items", [])
        for event in events:
            event["description"] = event.get("description", "")[:150] # roughly 25 words

        return events


# Global instance
gcal_service = None

def get_gcal_service() -> GcalendarService:
    """Get or create GCal service instance"""
    global gcal_service
    if gcal_service is None:
        gcal_service = GcalendarService()
    return gcal_service
