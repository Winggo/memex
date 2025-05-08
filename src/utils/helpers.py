import os
from datetime import datetime


def get_date_from_timestamp(timestamp):
    return datetime.fromtimestamp(timestamp).date().isoformat()


def get_file_metadata(path):
    try:
        stats = os.stat(path)

        mtdata = {}
        if not stats:
            return mtdata

        if stats.st_birthtime:
            mtdata["created_at"] = get_date_from_timestamp(stats.st_birthtime)
        if stats.st_mtime:
            mtdata["updated_at"] = get_date_from_timestamp(stats.st_mtime)

        return mtdata
    except:
        return {}
