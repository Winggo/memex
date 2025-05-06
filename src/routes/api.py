from langchain_chroma import Chroma
from fastapi import APIRouter
from pydantic import BaseModel

from ai_models import embedding_function, mistral_7b_together_model, rag_prompt_template
from utils.constants import CHROMA_PATH


vectorstore = Chroma(
    persist_directory=CHROMA_PATH,
    embedding_function=embedding_function,
)


router = APIRouter()

class CompletionRequest(BaseModel):
    prompt: str

@router.post("/api/v1/completion")
def generate_completion(data: CompletionRequest):
    query = data.prompt

    rag_documents = vectorstore.similarity_search(query, k=3)
    rag_str = ""
    for document in rag_documents:
        metadata = document.metadata
        rag_str += (
            f"{metadata['filename']} ({metadata['type']}): {document.page_content}\nCreated at: {metadata['created_at']}, Updated at: {metadata['updated_at']}\n\n"
        )
    print(f"RAG RESULTS: {rag_documents}")
    print(f"RAG STRING: {rag_str}")

    chain = rag_prompt_template | mistral_7b_together_model
    llm_response = chain.invoke({
        "prompt": query,
        "context": rag_str,
    })

    return llm_response.content if hasattr(llm_response, 'content') else str(llm_response)
