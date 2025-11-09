import os
import dateutil.parser
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


    def create_event(self, calendar_id, fields):
        """
        Create an event with specified details

        Args:
            calendar_id: (str - required) Calendar to insert into
            fields: dict with optional keys:
                - summary (str - required)
                - start_datetime (string - required)
                - end_datetime (string - required)
                - description (str)
                - location (str)
                - timezone (str, e.g. "America/Los_Angeles")
        """
        fields = fields or {}
        if not calendar_id or "summary" not in fields or "start_datetime" not in fields or "end_datetime" not in fields:
            print(f"[GCal] Required fields not found. Event not created.")
            return

        try:
            start_dt = dateutil.parser.parse(fields["start_datetime"])
            end_dt = dateutil.parser.parse(fields["end_datetime"])

            event = {
                "summary": fields["summary"],
                "start": {
                    "dateTime": start_dt,
                    "timeZone": fields.get("timezone", "America/Los_Angeles"),
                },
                "end": {
                    "dateTime": end_dt,
                    "timeZone": fields.get("timezone", "America/Los_Angeles"),
                },
                "description": fields.get("description", "Created by Memex"),
                "location": fields.get("location"),
            }

            created_event = self.service.events().insert(
                calendarId=calendar_id,
                body=event,
            ).execute()
            
            return created_event

        except (ValueError, TypeError) as e:
            print(f"[GCal] Error parsing datetime: {e}")
            return {"error": f"Invalid datetime format: {e}"}



# Global instance
gcal_service = None

def get_gcal_service() -> GcalendarService:
    """Get or create GCal service instance"""
    global gcal_service
    if gcal_service is None:
        gcal_service = GcalendarService()
    return gcal_service
