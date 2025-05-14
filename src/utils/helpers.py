import re
import os
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
