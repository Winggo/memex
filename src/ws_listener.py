import requests
import socketio
import os
from fastapi import HTTPException

from src.rag_engine import respond_with_retrieved_context


BLUEBUBBLES_HTTP_URL = f"http://localhost:{os.environ['BLUEBUBBLES_PORT']}"
BLUEBUBBLES_WS_URL = f"ws://localhost:{os.environ['BLUEBUBBLES_PORT']}"
BLUEBUBBLES_TOKEN = os.environ["BLUEBUBBLES_TOKEN"]
IMESSAGE_PHONE_NUMBER = os.environ["IMESSAGE_PHONE_NUMBER"]
IMESSAGE_EMAIL = os.environ["IMESSAGE_EMAIL"]
IMESSAGE_EMAILS = os.environ.get("IMESSAGE_EMAILS", []).split(",")
VALID_ADDRESSES = [*IMESSAGE_EMAILS]


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
    parsed_data = {
        "service": data.get("handle", {}).get("service"),
        "address": data.get("handle", {}).get("address"),
        "message": data.get("text"),
    }
    
    if (
        parsed_data["service"] != "iMessage" or
        parsed_data["address"] not in VALID_ADDRESSES or
        not data.get("isFromMe") or
        not isinstance(parsed_data["message"], str) or
        parsed_data["message"] == ""
    ):
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
                "addresses": [IMESSAGE_PHONE_NUMBER],
                "message": completion,
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
