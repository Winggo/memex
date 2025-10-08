import os
from langchain_together import TogetherEmbeddings
from langchain_together import ChatTogether

# Used for embedding
embedding_function = TogetherEmbeddings(
    model="BAAI/bge-large-en-v1.5",
    api_key=os.getenv("TOGETHER_API_KEY")
)

# Used for response generation
llama_3_70b_free_together_model_creative = ChatTogether(
    model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
    together_api_key=os.getenv("TOGETHER_API_KEY"),
    temperature=0.4,
    max_tokens=1024,
)

llama_3_70b_free_together_model_deterministic = ChatTogether(
    model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
    together_api_key=os.getenv("TOGETHER_API_KEY"),
    temperature=0,
    max_tokens=1024,
)


# Used for determining query type. Currently not used for response generation.
qwen_2_5_7b_together_model = ChatTogether(
    model="Qwen/Qwen2.5-7B-Instruct-Turbo",
    together_api_key=os.getenv("TOGETHER_API_KEY"),
    temperature=0,
    max_tokens=1024,
)
