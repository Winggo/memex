import os
from langchain_together import TogetherEmbeddings
from langchain_together import ChatTogether
from langchain.prompts import PromptTemplate

embedding_function = TogetherEmbeddings(
    model="togethercomputer/m2-bert-80M-2k-retrieval",
    api_key=os.getenv("TOGETHER_API_KEY")
)

mistral_7b_together_model = ChatTogether(
    model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
    together_api_key=os.getenv("TOGETHER_API_KEY"),
    temperature=0.7,
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
