import os

CHROMA_PATH = os.path.join(os.getcwd(), os.environ.get("CHROMA_DIRNAME", "chroma_db"))
DISCORD_APP_ID = 1369249100507123722
DISCORD_CHANNEL_ID = int(os.environ.get("DISCORD_CHANNEL_ID", "0"))
DISCORD_USER_ID = int(os.environ.get("DISCORD_USER_ID", "0"))
MEMEX_MESSAGE_MARKER = "\u200B\u200C\u200D"

BLUEBUBBLES_HTTP_URL = f"http://localhost:{os.environ['BLUEBUBBLES_PORT']}"
BLUEBUBBLES_WS_URL = f"ws://localhost:{os.environ['BLUEBUBBLES_PORT']}"
BLUEBUBBLES_TOKEN = os.environ["BLUEBUBBLES_TOKEN"]
VALID_IMESSAGE_SENDER_PHONE = os.environ["VALID_IMESSAGE_SENDER_PHONE"]
VALID_IMESSAGE_SENDERS = os.environ["VALID_IMESSAGE_SENDERS"].split(",")
IMESSAGE_RECIPIENT = os.environ["IMESSAGE_RECIPIENT"]

GOOGLE_OAUTH_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/calendar.events.owned"
]
