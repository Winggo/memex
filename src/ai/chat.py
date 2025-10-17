import asyncio
from langchain.prompts import PromptTemplate

from .ai_models import qwen_2_5_7b_together_model
from .rag_engine import respond_with_retrieved_context
from .ai_agent import get_ai_agent


intent_prompt = PromptTemplate(
    input_variables=["message"],
    template="""Classify the user message intent into one of:
    - "rag_query": when user is asking questions or chatting about their own data, memories, or notes.
    - "tool_action": when user is requesting an action (create event, send email, fetch newsletter, etc.)

    Message: "{message}"
    Intent:"""
)

def detect_intent(message: str) -> str:
    """
    Two possible intents of a prompt: "rag_query" or "tool_action
    """
    chain = intent_prompt | qwen_2_5_7b_together_model
    result = chain.invoke({"message": message})
    intent = result.content.strip().lower()
    if "tool" in intent:
        return "tool_action"
    else:
        return "rag_query"


async def process_message(message: str):
    """
    Determine how to handle incoming message (a.k.a. prompt)
    """
    print(f"[Chat] Processing incoming message: {message}")

    try:
        intent = detect_intent(message)

        completion = "Encountered error processing message"
        if intent == "tool_action":
            agent = get_ai_agent()
            llm_response = await asyncio.wait_for(
                agent.arun(message),
                timeout=120
            )
            completion = llm_response if isinstance(llm_response, str) else str(llm_response)
        else:
            completion = respond_with_retrieved_context(message)
    except asyncio.TimeoutError as e:
        print(f"[Chat] Timed out processing message: {e}")
        raise e
    except Exception as e:
        print(f"[Chat] Error processing message: {e}")
        raise e

    return completion
