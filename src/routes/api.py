import requests
import os

from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel

from src.rag_engine import respond_with_retrieved_context
from src.utils.constants import MEMEX_MESSAGE_MARKER


BLUEBUBBLES_URL = f"http://localhost:{os.environ['BLUEBUBBLES_PORT']}"
BLUEBUBBLES_TOKEN = os.environ["BLUEBUBBLES_TOKEN"]
IMESSAGE_EMAIL = os.environ["IMESSAGE_EMAIL"]


router = APIRouter()

class CompletionRequest(BaseModel):
    prompt: str


@router.post("/api/v1/completion")
def generate_completion(data: CompletionRequest, request: Request):
    client_ip = request.client.host
    if client_ip != "127.0.0.1" or os.environ.get("ENABLE_REST_API") != "true":
        raise HTTPException(status_code=403, detail="Forbidden")

    return respond_with_retrieved_context(data.prompt)


@router.post("/api/v1/completion/imessage")
def send_imessaage(data: CompletionRequest, request: Request):
    client_ip = request.client.host
    if client_ip != "127.0.0.1" or os.environ.get("ENABLE_REST_API") != "true":
        raise HTTPException(status_code=403, detail="Forbidden")
    
    completion = respond_with_retrieved_context(data.prompt)

    headers = {
        "Content-Type": "application/json",
    }
    params = {
        "token": BLUEBUBBLES_TOKEN,
    }
    payload = {
        "addresses": [IMESSAGE_EMAIL],
        "message": completion + MEMEX_MESSAGE_MARKER,
    }

    try:
        res = requests.post(
            f"{BLUEBUBBLES_URL}/api/v1/chat/new",
            headers=headers, params=params, json=payload
        )

        if res.status_code != 200:
            raise HTTPException(status_code=500, detail="Sending iMessage failed. Please ensure the messaging server is running.")
        
        return {
            "status": 200,
            "contact": IMESSAGE_EMAIL,
            "prompt": data.prompt,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail="Sending iMessage failed. Please ensure the messaging server is running.")
