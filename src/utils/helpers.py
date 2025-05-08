import os
from datetime import datetime


def get_date_from_str(timestamp: str):
    """Ex timestamp: 'Sun, 01 Dec 2013 23:24::3 -0600'"""
    date_format = "%a, %d %b %Y %H:%M:%S %z"
    try:
        dt = datetime.strptime(timestamp, date_format)
        return dt.date().isoformat()
    except:
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
