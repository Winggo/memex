import os
from langchain_together import TogetherEmbeddings
from langchain_together import ChatTogether


embedding_function = TogetherEmbeddings(
    model="togethercomputer/m2-bert-80M-2k-retrieval",
    api_key=os.getenv("TOGETHER_API_KEY")
)

nous_hermes_model = ChatTogether(
    model="NousResearch/Nous-Hermes-2-Mixtral-8x7B-DPO",
    together_api_key=os.getenv("TOGETHER_API_KEY"),
    temperature=0.4,
)

mistral_7b_together_model = ChatTogether(
    model="mistralai/Mistral-7B-Instruct-v0.3",
    together_api_key=os.getenv("TOGETHER_API_KEY"),
    temperature=0,
)

llama_3_70b_free_together_model_creative = ChatTogether(
    model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
    together_api_key=os.getenv("TOGETHER_API_KEY"),
    temperature=0.4,
)

llama_3_70b_free_together_model_deterministic = ChatTogether(
    model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
    together_api_key=os.getenv("TOGETHER_API_KEY"),
    temperature=0,
)
