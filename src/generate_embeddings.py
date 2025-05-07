"""
Script to generate embeddings from /data directory and store in Chroma vector DB
"""

import os
from dotenv import load_dotenv
from glob import glob

from unstructured_client import UnstructuredClient
from langchain_unstructured import UnstructuredLoader
from unstructured.cleaners.core import clean_extra_whitespace
from langchain_chroma import Chroma
from utils.helpers import get_file_metadata

load_dotenv(".env")
from ai_models import embedding_function

from utils.constants import CHROMA_PATH


folder_path = "./data/apple/notes"
file_paths = [
    path for path in glob(os.path.join(folder_path, "**/*"), recursive=True)
    if os.path.isfile(path)
]

if os.getenv("USE_UNSTRUCTURED_API") == "true":
    loader = UnstructuredLoader(
        file_paths,
        post_processors=[clean_extra_whitespace],
        client=UnstructuredClient(api_key_auth=os.getenv("UNSTRUCTURED_API_KEY")),
        partition_via_api=True,
        chunking_strategy="by_title",
        max_characters=1500,
    )
    print("Using Unstructured API")
else:
    loader = UnstructuredLoader(
        file_paths,
        post_processors=[clean_extra_whitespace],
        chunking_strategy="by_title",
        max_characters=1500,
    )
    print("Using Unstructured locally")


# Parsing, chunking, preprocessing
documents = loader.load()
processed_documents = []
for doc in documents:
    if len(doc.page_content.strip()) < 30:
        continue
    mtdata = get_file_metadata(doc.metadata["source"])
    doc.metadata = {
        **doc.metadata,
        **mtdata,
        "languages": ", ".join(doc.metadata["languages"]),
        "type": "apple/note",
    }
    processed_documents.append(doc)

print(f"{len(processed_documents)} documents loaded.")


# Generate embeddings and store in vector DB
vectorstore = Chroma.from_documents(
    processed_documents,
    embedding=embedding_function,
    persist_directory=CHROMA_PATH,
)

print("Embeddings generated and stored in vector store")
