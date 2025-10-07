import asyncio
import requests
from fastapi import HTTPException

from .constants import (
    BLUEBUBBLES_HTTP_URL,
    BLUEBUBBLES_TOKEN,
    IMESSAGE_RECIPIENT,
    MEMEX_MESSAGE_MARKER,
    DISCORD_CHANNEL_ID,
    DISCORD_USER_ID,
)


async def send_discord_message(message: str, retries: int = 3):
    """
    Send a message to the configured Discord channel or user DM
    """
    if DISCORD_USER_ID == 0 and DISCORD_CHANNEL_ID == 0:
        print("[Discord] No Discord channel ID and user ID configured, skipping message send")
        return
    
    try:
        # Get the Discord client from the app
        from ..integrations.discord_client import discord_client
        
        if not discord_client.is_ready():
            print("[Discord] Discord client not ready, skipping message send")
            if retries > 0:
                await asyncio.sleep(5)
                await send_discord_message(message, retries-1)
            return
            
        if DISCORD_USER_ID:
            dm_channel = await discord_client.fetch_user(DISCORD_USER_ID)
            if dm_channel:
                await dm_channel.send(message)
                print(f"[Discord] Message sent to user {DISCORD_USER_ID}")

        if DISCORD_CHANNEL_ID:
            channel = discord_client.get_channel(DISCORD_CHANNEL_ID)
            if channel:
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
