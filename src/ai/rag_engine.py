from langchain_chroma import Chroma
from langchain.prompts import PromptTemplate

from .ai_models import embedding_function, llama_3_70b_free_together_model_creative, qwen_2_5_7b_together_model
from ..utils.constants import CHROMA_PATH


vectorstore = Chroma(
    persist_directory=CHROMA_PATH,
    embedding_function=embedding_function,
)
print(f"[RAG] Vector store loaded from {CHROMA_PATH}")


determine_query_type_template = PromptTemplate(
    input_variables=["prompt"],
    template="""Given the prompt, determine what kind of data (notes, messages, contacts, and maps) would be most helpful in answering it. Only suggest one type of data.

Respond using 1 sentence or less, and DO NOT mention "RAG", "querying", or "vector store".

*Prompt:* {prompt}"""
)

def determine_query_type(prompt):
    chain = determine_query_type_template | qwen_2_5_7b_together_model
    llm_response = chain.invoke({"prompt": prompt})
    return llm_response.content if hasattr(llm_response, 'content') else str(llm_response)


rag_prompt_template = PromptTemplate(
    input_variables=["prompt", "context"],
    template="""You are a helpful personal assistant. Given the following prompt and context, provide a helpful response.
You communicate like a close friend. Be casual, curious, thoughtful, and subtly funny. You don't need to be formal or use unnecessary phrases such as "I can help you out" or "Let's dive into the context you've got". Be more straightforward.

Do not mention the provided context, but use the context contents to shape your response.
If the context is not helpful or irrelevant, simply state that you cannot find relevant data on the subject.

Do not include non-factual statements. No need to apologize. Only respond in a single short paragraph, bullet points, and numbered lists.
If you deem there is any sensitive info in the response such as passwords, api keys, or bank account details, censor it in your response.
If you deem there is duplicate information (such as same phone numbers but formatted differently), condense it.
Reply using LESS THAN 200 words.

*Context:*
{context}

*Prompt:* {prompt}"""
)

def respond_with_retrieved_context(prompt):
    try:
        rag_documents = vectorstore.similarity_search(prompt, k=8)
        print(f"[RAG] Retrieved {len(rag_documents)} documents")
    except Exception as e:
        print(f"[RAG] Error retrieving context: {e}")
        return "I'm sorry, I'm having trouble retrieving the context. Please try again later."

    rag_context = ""
    for document in rag_documents:
        metadata = document.metadata
        rag_context += (
            f"Content: {document.page_content}\nContent metadata: {metadata}\n\n"
        )

    chain = rag_prompt_template | llama_3_70b_free_together_model_creative
    llm_response = chain.invoke({
        "prompt": prompt,
        "context": rag_context,
    })

    return llm_response.content if hasattr(llm_response, 'content') else str(llm_response)
