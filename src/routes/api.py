from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel

from rag_engine import respond_with_retrieved_context


router = APIRouter()

class CompletionRequest(BaseModel):
    prompt: str

@router.post("/api/v1/completion")
def generate_completion(data: CompletionRequest, request: Request):
    client_ip = request.client.host
    if client_ip != "127.0.0.1":
        raise HTTPException(status_code=403, detail="Forbidden")

    return respond_with_retrieved_context(data.prompt)
