"""
Script to generate embeddings from /data directory and store in Chroma vector DB
"""
import argparse
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


parser = argparse.ArgumentParser(description="Generate embeddings from data directory.")
parser.add_argument(
    "--folder_path",
    type=str,
    default="./data",
    help="Path to the folder containing data files"
)
parser.add_argument(
    "--chunking_strategy",
    type=str,
    default="by_title",
    help="Chunking strategy after parsing your files"
)
parser.add_argument(
    "--chunk_max_characters",
    type=int,
    default=1500,
    help="Max number of characters per chunk"
)
parser.add_argument(
    "--dry_run",
    action="store_true",
    help="Parse data without generating embeddings and storing in vector DB"
)
args = parser.parse_args()


folder_path = args.folder_path
chunking_strategy = args.chunking_strategy
chunk_max_characters = args.chunk_max_characters
dry_run = args.dry_run


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
        chunking_strategy=chunking_strategy,
        max_characters=chunk_max_characters,
    )
    print("Using Unstructured API")
else:
    loader = UnstructuredLoader(
        file_paths,
        post_processors=[clean_extra_whitespace],
        chunking_strategy=chunking_strategy,
        max_characters=chunk_max_characters,
    )
    print("Using Unstructured locally")


# Parsing, chunking, preprocessing
documents = loader.load()
processed_documents = []
for doc in documents:
    if len(doc.page_content.strip()) < 30:
        continue

    mtdata = get_file_metadata(doc.metadata["source"])
    type = "/".join(doc.metadata["file_directory"].split("/")[1:3])

    doc.metadata = {
        **doc.metadata,
        **mtdata,
        "languages": ", ".join(doc.metadata["languages"]),
        "type": type,
    }
    processed_documents.append(doc)

print(f"{len(processed_documents)} documents loaded.")


if not dry_run:
    # Generate embeddings and store in vector DB
    vectorstore = Chroma.from_documents(
        processed_documents,
        embedding=embedding_function,
        persist_directory=CHROMA_PATH,
    )

    print("Embeddings generated and stored in vector store")
