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
- Generate embeddings for other data besides notes
- Showcase app on other spaces besides discord


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


## Usage

0. Create `.env` with required env variables (reference `.env.example`)
1. Generate embeddings from data directory, and store them in vector DB Chroma
    - `python3 src/scripts/generate_embeddings.py --folder_path ./data --chunking_strategy by_title --chunk_max_characters 1500`
2. Launch FastAPI server to handle requests between LLM and messaging services
    - `python3 src/server.py`


## Setup Issues

##### Upon executing `python3 src/parsing.py`, if you encounter the following error:
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
