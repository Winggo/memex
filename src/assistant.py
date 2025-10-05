from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from langchain.prompts import PromptTemplate
from langchain_core.tools import tool
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.errors import HttpError
from fastapi import HTTPException
import datetime
import os
import requests

from .utils.constants import (
    BLUEBUBBLES_HTTP_URL,
    BLUEBUBBLES_TOKEN,
    IMESSAGE_RECIPIENT,
    MEMEX_MESSAGE_MARKER,
    DISCORD_CHANNEL_ID,
)
from .ai_models import llama_3_70b_free_together_model_deterministic


GOOGLE_OAUTH_SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]


async def send_discord_message(message: str):
    """
    Send a message to the configured Discord channel
    """
    if DISCORD_CHANNEL_ID == 0:
        print("[Discord] No Discord channel ID configured, skipping message send")
        return
    
    try:
        # Get the Discord client from the app
        from .discord_client import discord_client
        
        if not discord_client.is_ready():
            print("[Discord] Discord client not ready, skipping message send")
            return
            
        channel = discord_client.get_channel(DISCORD_CHANNEL_ID)
        if channel is None:
            print(f"[Discord] Channel with ID {DISCORD_CHANNEL_ID} not found")
            return
            
        await channel.send(message)
        print(f"[Discord] Message sent to channel {DISCORD_CHANNEL_ID}")
        
    except Exception as e:
        print(f"[Discord] Failed to send message: {e}")


def send_imessage(message: str):
    try:
        res = requests.post(
            f"{BLUEBUBBLES_HTTP_URL}/api/v1/chat/new",
            headers={
                "Content-Type": "application/json",
            },
            params={
                "token": BLUEBUBBLES_TOKEN,
            },
            json={
                "addresses": [IMESSAGE_RECIPIENT],
                "message": message + MEMEX_MESSAGE_MARKER,
            }
        )

        if res.status_code != 200:
            raise HTTPException(status_code=500, detail="Sending iMessage failed. Please ensure the messaging server is running.")

        print(f"[Websocket] Completion message sent: {res.status_code}")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Sending iMessage failed. Please ensure the messaging server is running.")


@tool
def get_calendar_events():
    """
    Get today's events from Google Calendar
    """
    creds = None
    if os.path.exists("google_oauth_credentials.json"):
        creds = Credentials.from_authorized_user_file("google_oauth_credentials.json", GOOGLE_OAUTH_SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("google_oauth_credentials.json", GOOGLE_OAUTH_SCOPES)
            creds = flow.run_local_server(port=0)

        with open("google_oauth_credentials.json", "w") as token:
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


daily_summary_template = PromptTemplate(
    input_variables=[],
    template="""Create a summary of today's calendar events, emails, weather, and stock performance, with each data group as its own paragraph.
Each paragraph should be less than 100 words.
The response should be in the following format:
```
Events:
[calendar events of the day]

Emails:
[emails summary of the day]

Weather:
[weather forecast of the day]

Stocks:
[stock performance of the day]
```"""
)

async def generate_daily_summary():
    chain = daily_summary_template | llama_3_70b_free_together_model_deterministic
    llm_response = chain.invoke({})

    completion = llm_response.content if hasattr(llm_response, 'content') else str(llm_response)
    print(f"[Assistant] Daily summary generated: {completion}")

    # Send to summary to Discord
    if os.environ.get("ENABLE_DISCORD_CLIENT") == "true":
        await send_discord_message(completion)

    # Send to summary to iMessage
    if os.environ.get("ENABLE_WEBSOCKET_LISTENER") == "true":
        send_imessage(completion)


def start_assistant():
    """
    Start assistant to perform following tasks daily at 8am PT:
    - Get events of the day from calendar
    - Get emails summary for the previous to current day
    - Get weather forecast for the day
    - Get stock performance for the previous to current day
    """
    scheduler = AsyncIOScheduler()
    scheduler.add_job(generate_daily_summary, CronTrigger(hour=8, minute=0), id="daily_completion")
    scheduler.start()
    return scheduler
