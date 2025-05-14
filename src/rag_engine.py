from langchain_chroma import Chroma
from langchain.prompts import PromptTemplate

from ai_models import embedding_function, mistral_7b_together_model
from utils.constants import CHROMA_PATH


vectorstore = Chroma(
    persist_directory=CHROMA_PATH,
    embedding_function=embedding_function,
)


rag_prompt_template = PromptTemplate(
    input_variables=["prompt", "context"],
    template="""I performed a similarity search from a vector store, which contains embeddings generated from my Apple notes, using the following prompt: {prompt}.
This process is called retrieval augmented generation (RAG), which you may be familiar with. But DO NOT MENTION RAG or querying the vector store in your response.

The data retrieved from the vector store is named "context". Given the following prompt and context, provide a helpful response.
Do not mention the context, but use the context contents to shape your response.
If the context is not helpful or irrelevant, simply state that you cannot find relevant data on the subject. Do not include non-factual statements. No need to apologize.

You communicate like a close friend. Be casual, curious, thoughtful, and subtly funny. You don't need to be formal or use unnecessary phrases such as "I can help you out" or "Let's dive into the context you've got". Be more straightforward.
Seperate ideas into paragraphs, use bullet points, and use numbered lists for better readability.
If you deem there is any sensitive info in the response such as passwords, api keys, or bank account details, censor it in your response.
Reply using LESS THAN 200 words.
*Context:*
{context}

*Prompt:*
{prompt}"""
)


def respond_with_retrieved_context(prompt):
    rag_documents = vectorstore.similarity_search(prompt, k=5)

    rag_context = ""
    for document in rag_documents:
        metadata = document.metadata
        rag_context += (
            f"Content: {document.page_content}\nContent metadata: {metadata}\n\n"
        )

    chain = rag_prompt_template | mistral_7b_together_model
    llm_response = chain.invoke({
        "prompt": prompt,
        "context": rag_context,
    })

    return llm_response.content if hasattr(llm_response, 'content') else str(llm_response)
