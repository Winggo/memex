import re
import os
import unicodedata
from datetime import datetime


def get_date_from_str(timestamp: str):
    """Ex timestamp: 'Sun, 01 Dec 2013 23:24::3 -0600'"""
    date_formats = [
        "%a, %d %b %Y %H:%M:%S %z",
        "%Y-%m-%dT%H:%M:%S%z",
    ]

    for fmt in date_formats:
        try:
            dt = datetime.strptime(timestamp, fmt)
            return dt.date().isoformat()
        except:
            continue

    return timestamp


def get_date_from_epoch(epoch):
    return datetime.fromtimestamp(epoch).date().isoformat()


def get_file_metadata(path):
    try:
        stats = os.stat(path)

        mtdata = {}
        if not stats:
            return mtdata

        if stats.st_birthtime:
            mtdata["created_at"] = get_date_from_epoch(stats.st_birthtime)
        if stats.st_mtime:
            mtdata["updated_at"] = get_date_from_epoch(stats.st_mtime)

        return mtdata
    except:
        return {}


def remove_image_references(text):
    """
    Remove image references from text
    """
    text = re.sub(r"!\[.*?\]\(.*?\)", "", text) #![Alt text](image_url)
    text = re.sub(r"data:image\/[a-zA-Z]+;base64,[^\s'\"]+", "", text) # base64 data
    text = re.sub(r"<img[^>]*>", "", text) # <img src="image_url" />
    
    return text.strip()


def normalize_phone_number(phone_number):
    return phone_number.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")


def clean_text(text: str)->str:
    """Clean unnecessary characters in text like emails"""
    # Normalize Unicode characters
    text = unicodedata.normalize("NFKC", text)
    
    # Remove common invisible/zero-width characters
    text = re.sub(r'[\u0000-\u001F\u200b-\u200f\u202a-\u202e\u2060\uFEFF]', '', text)
    
    # Replace non-breaking spaces (\xa0) with regular spaces
    text = text.replace('\xa0', ' ')
    
    # Collapse multiple spaces or newlines into a single space
    text = re.sub(r'\s+', ' ', text)
    
    # Strip leading/trailing whitespace
    return text.strip()
