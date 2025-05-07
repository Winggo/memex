import os
from langchain_together import TogetherEmbeddings
from langchain_together import ChatTogether


embedding_function = TogetherEmbeddings(
    model="togethercomputer/m2-bert-80M-2k-retrieval",
    api_key=os.getenv("TOGETHER_API_KEY")
)

mistral_7b_together_model = ChatTogether(
    model="NousResearch/Nous-Hermes-2-Mixtral-8x7B-DPO",
    together_api_key=os.getenv("TOGETHER_API_KEY"),
    temperature=0.7,
)
