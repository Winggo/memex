# Memex

A personal LLM leveraging my corpus as its knowledge base.

Data sources:
- Google
    - Emails (mbox)
    - Calendar (ics)
    - Google Search Histroy (html, json)
    - Youtube Search History (html)
    - Contacts (vcf)
    - Drive (docx)
    - Maps (csv)
- Apple
    - Notes (txt)
    - Contacts (vcf)
    - Calendar (ics)


## TODO
- Generate embeddings for other data besides Apple notes/contacts/messages, Google Maps
- Showcase app on other spaces besides Discord


## Implementation Steps

1. Download data from sources Google Takeout & iCloud Exports
2. Data processing: clean, chunk, and generating embeddings
3. Store embeddings into a vector DB
4. Leverage an open-source LLM for inference and to perform RAG
5. Use Discord or HuggingFace Spaces as the Memex's user interface


## Architecture

1. Parsing, chunking, preprocessing
    - langchain + unstructured.io
2. Embedding
    - BAAI/bge-large-en-v1.5 + together.ai
3. Vector DB
    - chroma
4. Retriever & RAG Model
    - togethercomputer/m2-bert-80M-2k-retrieval + together.ai
5. Optional UI
    - discord / gradio
6. Backend hosting
    - fly.io


## Usage

0. Create `.env` with required env variables (reference `.env.example`)
1. Generate embeddings from data directory, and store them in vector DB Chroma
    - `python3 src/scripts/generate_embeddings.py --folder_path ./data --chunk_max_characters 1500`
2. Launch FastAPI server to handle requests between LLM and messaging services
    - `python3 src/app.py`


## Deployment

To deploy onto fly.io:
1. `fly auth login`
2. `fly deploy` (`fly launch` if first time)
    - volume should be provisioned alongside
3. Transfer local chroma_db data into volume
    1. Copy sqlite3 file
        1. `fly ssh sftp shell`
        2. `put ./chroma_db/chroma.sqlite3 /chroma_db/chroma.sqlite3`
        3. exit
    2. Create `36e27b04-a9...` directory
        1. `fly ssh console`
        2. `mkdir -p /chroma_db/36e27b04-a9...`
        3. exit
    3. Copy remaining files
        1. `fly ssh sftp shell`
        2. `put ./chroma_db/…/data_level0.bin`
        3. repeat

If connection lost:
1) restart machine on fly.io dashboard OR
2) exit and then `fly ssh sftp shell`


## Setup Issues

##### Upon executing `python3 src/generate_embeddings.py`, if you encounter the following error:
```
[nltk_data] Error loading punkt_tab: <urlopen error [SSL:
[nltk_data]     CERTIFICATE_VERIFY_FAILED] certificate verify failed:
[nltk_data]     unable to get local issuer certificate (_ssl.c:1000)>
```

Fix: `sudo /Applications/Python\ 3.12/Install\ Certificates.command`


##### `pdf2image.exceptions.PDFInfoNotInstalledError: Unable to get page count. Is poppler installed and in PATH?`

Fix: `brew install poppler`


## Attribution

This project idea was inspired by this post from Linus: https://x.com/thesephist/status/1629272600156176386
