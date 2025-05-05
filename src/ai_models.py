import os
from langchain_together import TogetherEmbeddings
from langchain_together import ChatTogether
from langchain.prompts import PromptTemplate

embedding_function = TogetherEmbeddings(
    model="BAAI/bge-large-en-v1.5",
    api_key=os.getenv("TOGETHER_API_KEY")
)

mistral_7b_together_model = ChatTogether(
    model="meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
    together_api_key=os.getenv("TOGETHER_API_KEY"),
    temperature=0.7,
)

rag_prompt_template = PromptTemplate(
    input_variables=["prompt", "context"],
    template="""I performed a similarity search from a vector store, which contains embeddings generated from my Apple notes, using the following prompt: {prompt}.
This process is called retrieval augmented generation (RAG), which you may be familiar with. But DO NOT MENTION RAG or querying the vector store in your response.

The data retrieved from the vector store is named "context". Given the following prompt and context, provide a helpful response.
If the context is helpful and relevant to the prompt, reference the context source(s) by its metadata details such as simplified filename (don't include phrase similar to "2024-03-24T00:55:18Z.txt"), date, or type. DO NOT describe the sources using phrases like "Context from Source 0".
If the context is not helpful or irrelevant, simply state that you cannot find relevant data on the subject. You do not need to apologize.

You're a close friend. Be casual, curious, and subtly funny. You don't need to be formal.
Seperate ideas into paragraphs, use bullet points, and use numbered lists for better readability.
Response must use LESS THAN 60 words.
*Context:*
{context}

*Prompt:*
{prompt}"""
)
