"""
Script to generate embeddings from /data directory and store in Chroma vector DB

Notes:
python3 src/scripts/generate_embeddings.py --folder_path data/apple/notes

Contacts:
python3 src/scripts/generate_embeddings.py --folder_path data/apple/contacts/data --file_type txt

Messages:
python3 src/scripts/generate_embeddings.py --folder_path data/apple/messages/data --file_type csv

Emails:
python3 src/scripts/generate_embeddings.py --folder_path data/google/gmail/data --file_type eml
"""

import argparse
import re
import os
from dotenv import load_dotenv
from glob import glob

from unstructured_client import UnstructuredClient
from langchain_unstructured import UnstructuredLoader
from unstructured.cleaners.core import clean_extra_whitespace
from langchain_chroma import Chroma
from utils.helpers import get_file_metadata, get_date_from_str, remove_image_references

load_dotenv(".env")
from ai_models import embedding_function

from utils.constants import CHROMA_PATH


def get_loader(_file_type, _file_paths, _chunk_max_characters):
    if os.getenv("USE_UNSTRUCTURED_API") == "true":
        print("Using Unstructured API")
        if _file_type == "txt":
            loader = UnstructuredLoader(
                _file_paths,
                post_processors=[clean_extra_whitespace],
                client=UnstructuredClient(api_key_auth=os.getenv("UNSTRUCTURED_API_KEY")),
                partition_via_api=True,
                max_characters=_chunk_max_characters,
                chunking_strategy="by_title",
            )
        elif _file_type == "eml":
            loader = UnstructuredLoader(
                _file_paths,
                post_processors=[clean_extra_whitespace],
                client=UnstructuredClient(api_key_auth=os.getenv("UNSTRUCTURED_API_KEY")),
                partition_via_api=True,
                max_characters=_chunk_max_characters,
                process_attachments=True,
            )
        elif _file_type == "csv":
            loader = UnstructuredLoader(
                _file_paths,
                post_processors=[clean_extra_whitespace],
                client=UnstructuredClient(api_key_auth=os.getenv("UNSTRUCTURED_API_KEY")),
                partition_via_api=True,
            )
    else:
        print("Using Unstructured locally")
        if _file_type == "txt":
            loader = UnstructuredLoader(
                _file_paths,
                post_processors=[clean_extra_whitespace],
                max_characters=_chunk_max_characters,
                chunking_strategy="by_title",
            )
        elif _file_type == "eml":
            loader = UnstructuredLoader(
                _file_paths,
                post_processors=[clean_extra_whitespace],
                max_characters=_chunk_max_characters,
                process_attachments=True,
            )
        elif _file_type == "csv":
            loader = UnstructuredLoader(
                _file_paths,
                post_processors=[clean_extra_whitespace],
            )
    
    return loader


def skip_processing_document(_doc):
    content = _doc.page_content.strip()
    if len(content) < 50:
        return True
    return False


def process_doc(_doc, _file_type):
    if _file_type == "txt":
        mtdata = get_file_metadata(_doc.metadata["source"])
        type = "/".join(_doc.metadata["file_directory"].split("/")[1:3])

        content = _doc.page_content
        content = remove_image_references(content)
        content = re.sub(r'\[{.*?}]', '', content) # remove text like [{type:ADMINISTRATOR,acceptanceStatus:ACCEPTED}]
        _doc.page_content = content

        _doc.metadata = {
            **mtdata,
            "type": type,
        }

    elif _file_type == "eml":
        type = "/".join(_doc.metadata["file_directory"].split("/")[1:3])
        sent_from = _doc.metadata.get("sent_from", "")
        _doc.metadata = {
            "sent_from": str(sent_from) if isinstance(sent_from, list) else sent_from,
            "last_modified": get_date_from_str(_doc.metadata.get("last_modified", "")),
            "subject": _doc.metadata.get("subject", ""),
            "type": type,
        }

    elif _file_type == "csv":
        type = "/".join(_doc.metadata["file_directory"].split("/")[1:3])
        _doc.metadata = {
            "type": type,
        }

    else:
        raise ValueError(f"Invalid file type: {_file_type}")
    
    return _doc



def main():
    parser = argparse.ArgumentParser(description="Generate embeddings from data directory.")
    parser.add_argument(
        "--folder_path",
        type=str,
        required=True,
        help="Path to the folder containing data files"
    )
    parser.add_argument(
        "--file_type",
        type=str,
        default="txt",
        help="Specify file type to parse accordingly"
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
    file_type = args.file_type
    chunk_max_characters = args.chunk_max_characters
    dry_run = args.dry_run


    file_paths = [
        path for path in glob(os.path.join(folder_path, "**/*"), recursive=True)
        if os.path.isfile(path)
    ]


    # Parsing, chunking, preprocessing
    loader = get_loader(file_type, file_paths, chunk_max_characters)
    documents = loader.load()
    processed_documents = []
    for doc in documents:
        if skip_processing_document(doc):
            continue
        processed_doc = process_doc(doc, file_type)
        processed_documents.append(processed_doc)

    print(f"{len(processed_documents)} documents loaded.")


    if dry_run:
        print(f"Dry run: documents embeddings not stored in DB.")
        print(processed_documents[0])
    else:
        # Generate embeddings and store in vector DB
        vectorstore = Chroma.from_documents(
            processed_documents,
            embedding=embedding_function,
            persist_directory=CHROMA_PATH,
        )

        print("Embeddings generated and stored in vector store")


main()
