"""
Reads the chat.db file found in `~/Library/Messages/chat.db` on macOs to retrieve all iMessages
Decoding is required to get text from all messages, as some messages are encoded in the attributedBody column

Create imessage.db file on macOS by:
1. Going to Settings -> Privacy & Security -> Full Disk Access -> Add Terminal to the list
2. Running `cp ~/Library/Messages/chat.db ./data/apple/messages/imessage.db`

Usage:
`python3 src/scripts/read_imessages_db.py`

Source: https://www.reddit.com/r/osx/comments/uevy32/texts_are_missing_from_mac_chatdb_file_despite/
"""

import os
import os.path
import sqlite3
from datetime import datetime

import pandas as pd
import numpy as np
from typedstream.stream import TypedStreamReader


def convert_apple_timestamp(tstamp):
    jan_2001_timestamp = datetime(2001, 1, 1).timestamp()
    tstamp_in_seconds = tstamp / 1000000000
    return datetime.fromtimestamp(jan_2001_timestamp + tstamp_in_seconds)


# The textual contents of some messages are encoded in a special attributedBody
# column on the message row; this attributedBody value is in Apple's proprietary
# typedstream format, but can be parsed with the pytypedstream package
# (<https://pypi.org/project/pytypedstream/>)
def decode_message_attributedbody(data):
    if not data:
        return None
    for event in TypedStreamReader.from_data(data):
        # The first bytes object is the one we want
        if type(event) is bytes:
            return event.decode("utf-8")


def main():
    db_path = os.path.join(os.getcwd(), "./data/apple/messages/imessage.db")
    with sqlite3.connect(db_path) as connection:
        msg_df = pd.read_sql_query(
            sql=(
                "SELECT date, is_from_me, handle.id AS sender_or_recipient_id, text, attributedBody, chat.display_name AS chat_name "
                "FROM message "
                "LEFT JOIN handle ON message.handle_id = handle.rowid "
                "LEFT JOIN chat_message_join cmj ON message.rowid = cmj.message_id "
                "LEFT JOIN chat ON cmj.chat_id = chat.rowid "
                "ORDER BY date ASC"
            ),
            con=connection,
            parse_dates={"datetime": "ISO8601"},
        )

        # Decode any attributedBody values and merge them into the 'text' column
        msg_df["text"] = msg_df["text"].fillna(
            msg_df["attributedBody"].apply(decode_message_attributedbody)
        )
        print(f"Messages processed: {len(msg_df)}")
        msg_df = msg_df.drop(columns=["attributedBody"])

        # Data trasformation
        msg_df["date"] = msg_df["date"].apply(convert_apple_timestamp)
        msg_df["sender"] = np.where(msg_df["is_from_me"] == 1, "me", msg_df["sender_or_recipient_id"])
        msg_df["recipient"] = np.where(msg_df["is_from_me"] == 0, "me", msg_df["sender_or_recipient_id"])
        msg_df["message"] = msg_df["text"]

        # Save to CSV
        export_columns = ["date", "sender", "recipient", "chat_name", "message"]
        msg_df[export_columns].to_csv("./data/apple/messages/data/imessage.csv", index=False)
        print(f"Exported successfully")


if __name__ == "__main__":
    main()