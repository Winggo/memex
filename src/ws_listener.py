import socketio
import os
import requests


BLUEBUBBLES_HTTP_URL = f"http://127.0.0.1:{os.environ['BLUEBUBBLES_PORT']}"
BLUEBUBBLES_WS_URL = f"ws://127.0.0.1:{os.environ['BLUEBUBBLES_PORT']}"
BLUEBUBBLES_TOKEN = os.environ["BLUEBUBBLES_TOKEN"]
IMESSAGE_PHONE_NUMBER = os.environ["IMESSAGE_PHONE_NUMBER"]


def test_socketio_handshake():
    try:
        handshake_url = f"{BLUEBUBBLES_HTTP_URL}/socket.io/?EIO=4&transport=polling&password={BLUEBUBBLES_TOKEN}"
        response = requests.get(handshake_url)
        
        return "sid" in response.text
    except Exception as e:
        print(f"Error testing handshake: {e}")
        return False


sio = socketio.AsyncClient(
    reconnection=False,
    logger=True,
    engineio_logger=True,
)

@sio.event
async def connect():
    print("[Websocket] Connected to websocket")

@sio.event
async def disconnect(reason):
    print(f"[Websocket] Disconnected from websocket. Reason: {reason}")

@sio.on("message")
async def handle_incoming_message(data):
    print(f"[Websocket] Message received: {data}")

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
