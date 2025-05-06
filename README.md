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


## Implementation Steps

1. Download data from sources Google Takeout & iCloud Exports
2. Data processing: clean, chunk, and generating embeddings
3. Store embeddings into a vector DB
4. Leverage an open-source LLM for inference and to perform RAG
5. Use iMessage as the LLM's user interface


## Architecture

1. Parsing, chunking, preprocessing
    - langchain + unstructured
2. Embedding
    - BAAI/bge-large-en-v1.5 + together.ai
3. Vector DB
    - chroma
4. Retriever & RAG Model
    - Meta-Llama-3.1-8B-Instruct-Turbo + together.ai
5. Optional UI
    - discord / streamlit / gradio


## Attribution

This project idea was inspired by this post from Linus: https://x.com/thesephist/status/1629272600156176386


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
