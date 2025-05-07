from fastapi import APIRouter
from pydantic import BaseModel

from rag_engine import respond_with_retrieved_context


router = APIRouter()

class CompletionRequest(BaseModel):
    prompt: str

@router.post("/api/v1/completion")
def generate_completion(data: CompletionRequest):
    return respond_with_retrieved_context(data.prompt)
