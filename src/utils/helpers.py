import os
from datetime import datetime

def get_file_metadata(path):
    try:
        stats = os.stat(path)

        mtdata = {}
        if not stats:
            return mtdata

        if stats.st_birthtime:
            mtdata["created_at"] = datetime.fromtimestamp(stats.st_birthtime).date().isoformat()
        if stats.st_mtime:
            mtdata["updated_at"] = datetime.fromtimestamp(stats.st_mtime).date().isoformat()

        return mtdata
    except:
        return {}
