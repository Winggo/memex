import requests
import socketio
from fastapi import HTTPException

from ..ai.rag_engine import respond_with_retrieved_context
from ..utils.constants import (
    MEMEX_MESSAGE_MARKER,
    BLUEBUBBLES_HTTP_URL,
    BLUEBUBBLES_WS_URL,
    BLUEBUBBLES_TOKEN,
    VALID_IMESSAGE_SENDER_PHONE,
    VALID_IMESSAGE_SENDERS,
    IMESSAGE_RECIPIENT,
)


def test_socketio_handshake():
    try:
        handshake_url = f"{BLUEBUBBLES_HTTP_URL}/socket.io/?EIO=4&transport=polling&password={BLUEBUBBLES_TOKEN}"
        response = requests.get(handshake_url)
        
        return "sid" in response.text
    except Exception as e:
        print(f"Error testing handshake: {e}")
        return False


sio = socketio.AsyncClient()

@sio.event
async def connect():
    print("[Websocket] Connected to websocket")

@sio.event
async def disconnect(reason=None):
    print(f"[Websocket] Disconnected from websocket. Reason: {reason}")

@sio.on("new-message")
async def handle_incoming_message(data):
    print(f"[Websocket] Message received: {data}")
    if not data:
        return
    parsed_data = {
        "service": data.get("handle", {}).get("service"),
        "address": data.get("handle", {}).get("address"),
        "message": data.get("text"),
        "chats": data.get("chats"),
    }

    if (
        parsed_data["service"] != "iMessage" or
        parsed_data["address"] not in VALID_IMESSAGE_SENDERS or
        not isinstance(parsed_data["message"], str) or
        parsed_data["message"].endswith(MEMEX_MESSAGE_MARKER) # ignore message sent by itself
    ):
        return
    
    chat_id = parsed_data["chats"][0].get("chatIdentifier") if len(parsed_data["chats"]) else None
    if chat_id != IMESSAGE_RECIPIENT:
         # edgecase: allow handling this message
        if not data.get("isFromMe") and chat_id == VALID_IMESSAGE_SENDER_PHONE:
            pass
        else:
            return
    
    completion = respond_with_retrieved_context(parsed_data["message"])

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
                "message": completion + MEMEX_MESSAGE_MARKER,
            }
        )

        if res.status_code != 200:
            raise HTTPException(status_code=500, detail="Sending iMessage failed. Please ensure the messaging server is running.")

        print(f"[Websocket] Completion message sent: {res.status_code}")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Sending iMessage failed. Please ensure the messaging server is running.")


@sio.on("*")
async def catch_all(event, data):
    print(f"[Websocket] Event '{event}' received: {data}")


async def start_ws_listener():
    handshake_success = test_socketio_handshake()
    if not handshake_success:
        print("[Websocket] Handshake failed. Exiting.")
        return

    socket_url = f"{BLUEBUBBLES_WS_URL}/socket.io/?password={BLUEBUBBLES_TOKEN}&EIO=4"
    print(f"[Websocket] Connecting to {socket_url}")

    try:
        await sio.connect(
            socket_url,
            transports=["websocket"],
        )
        await sio.wait()
    except Exception as e:
        print(f"[Websocket] Error connecting: {e}")
