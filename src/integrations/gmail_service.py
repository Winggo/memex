import os
import base64
from datetime import datetime
from typing import List, Dict
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow
from bs4 import BeautifulSoup
from ..utils.constants import GOOGLE_OAUTH_SCOPES


class GmailService:
    def __init__(self, credentials_file="google_oauth_credentials.json", token_file="google_oauth_token.json"):
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.service = None
        self._authenticate()


    def _authenticate(self):
        """Authenticate with Gmail API"""
        print(f"[Gmail Client] Authenticating...")
        creds = None
        
        # Load existing token if available
        if os.path.exists(self.token_file):
            creds = Credentials.from_authorized_user_file(self.token_file, GOOGLE_OAUTH_SCOPES)
        
        # If there are no (valid) credentials available, let the user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                print(f"[Gmail Client] Refreshing token...")
                creds.refresh(Request())
                print(f"[Gmail Client] Refreshing token completed")
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, GOOGLE_OAUTH_SCOPES
                )
                creds = flow.run_local_server(port=0)
            
            # Save the credentials for the next run
            with open(self.token_file, "w") as token:
                token.write(creds.to_json())
        
        print(f"[Gmail Client] Creds validity: {creds.valid}")
        self.service = build("gmail", "v1", credentials=creds)
    

    def get_emails(self, query: str = "", max_results: int = 10, user_id: str = "me") -> List[Dict]:
        """
        Retrieve emails from Gmail
        
        Args:
            query (str): Gmail search query (e.g., "is:unread", "from:example@gmail.com")
            max_results (int): Maximum number of emails to retrieve
            user_id (str): Gmail user ID (default: "me" for authenticated user)
        
        Returns:
            list: List of email messages
        """
        try:
            # Get list of message IDs
            results = self.service.users().messages().list(
                userId=user_id, 
                q=query, 
                maxResults=max_results
            ).execute()
            
            messages = results.get("messages", [])
            email_list = []
            
            for message in messages:
                # Get full message details
                msg = self.service.users().messages().get(
                    userId=user_id, 
                    id=message["id"]
                ).execute()
                
                email_data = self._parse_email(msg)
                email_list.append(email_data)
            
            return email_list
            
        except HttpError as error:
            print(f"An error occurred: {error}")
            return []
    

    def _parse_email(self, message: Dict) -> Dict:
        """Parse email message and extract relevant information"""
        headers = message["payload"].get("headers", [])
        
        # Extract common headers
        email_data = {
            "id": message["id"],
            "thread_id": message["threadId"],
            "subject": "",
            "from": "",
            "to": "",
            "date": "",
            "snippet": message.get("snippet", ""),
            "body": "",
            "labels": message.get("labelIds", [])
        }
        
        # Parse headers
        for header in headers:
            name = header["name"].lower()
            value = header["value"]
            
            if name == "subject":
                email_data["subject"] = value
            elif name == "from":
                email_data["from"] = value
            elif name == "to":
                email_data["to"] = value
            elif name == "date":
                email_data["date"] = value
        
        # Extract body content
        email_data["body"] = self._extract_body(message["payload"])
        
        return email_data
    

    def _extract_body(self, payload: Dict) -> str:
        """Extract email body content"""
        body = ""
        
        if "parts" in payload:
            # Multipart message
            for part in payload["parts"]:
                if part["mimeType"] == "text/html":
                    if "data" in part["body"]:
                        html_body = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8")
                        soup = BeautifulSoup(html_body, 'html.parser')
                        body = soup.get_text()
                        break
                elif part["mimeType"] == "text/plain":
                    if "data" in part["body"]:
                        body = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8")
                
        else:
            # Single part message
            if payload["mimeType"] == "text/html" and "data" in payload["body"]:
                html_body = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8")
                soup = BeautifulSoup(html_body, 'html.parser')
                body = soup.get_text()
            elif payload["mimeType"] == "text/plain" and "data" in payload["body"]:
                body = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8")
        
        return body
    

    def get_daily_emails_from_newsletter(self, sender_email: str, max_results: int = 1) -> List[Dict]:
        """Get emails from a specific sender"""
        today = datetime.now().strftime('%Y/%m/%d')
        query = f"from:{sender_email} after:{today}"
        return self.get_emails(query=query, max_results=max_results)
    

    def mark_as_read(self, message_id: str, user_id: str = "me") -> bool:
        """Mark an email as read"""
        try:
            self.service.users().messages().modify(
                userId=user_id,
                id=message_id,
                body={"removeLabelIds": ["UNREAD"]}
            ).execute()
            print(f"Email {message_id} marked as read")
            return True
        except HttpError as error:
            print(f"Error marking email as read: {error}")
            return False


# Global instance
gmail_service = None

def get_gmail_service() -> GmailService:
    """Get or create Gmail service instance"""
    global gmail_service
    if gmail_service is None:
        gmail_service = GmailService()
    return gmail_service
