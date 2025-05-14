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
import argparse
import os
import os.path
import sqlite3
from datetime import datetime

import Contacts
import pandas as pd
import numpy as np
from typedstream.stream import TypedStreamReader

from utils.helpers import normalize_phone_number


CHUNK_ROW_SIZE = 15
CHUNK_OVERLAP = 3


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
        

def request_contacts_access():
    contacts_store = Contacts.CNContactStore.alloc().init()

    def completion(granted, error):
        print(f"Access granted: {granted}")
        if error:
            print(f"Access error: {error}")

    contacts_store.requestAccessForEntityType_completionHandler_(0, completion)
        

def get_contacts_lookup():
    contacts_store = Contacts.CNContactStore.alloc().init()

    keys = [
        Contacts.CNContactPhoneNumbersKey,
        Contacts.CNContactEmailAddressesKey,
        Contacts.CNContactGivenNameKey,
        Contacts.CNContactFamilyNameKey
    ]
    request = Contacts.CNContactFetchRequest.alloc().initWithKeysToFetch_(keys)
    lookup = {}

    def handler(contact, _):
        full_name = f"{contact.givenName()} {contact.familyName()}".strip()
        if not full_name:
            return True

        for phone in contact.phoneNumbers():
            normalized = normalize_phone_number(str(phone.value().stringValue()))
            lookup[normalized] = full_name
        for email in contact.emailAddresses():
            lookup[str(email.value)] = full_name

        return True
    
    contacts_store.enumerateContactsWithFetchRequest_error_usingBlock_(request, None, handler)
    return lookup


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

        contacts_lookup = get_contacts_lookup()

        def resolve_contact(recipient_sender_id):
            if not isinstance(recipient_sender_id, str):
                return recipient_sender_id
            
            normalized = normalize_phone_number(recipient_sender_id)
            return contacts_lookup.get(normalized, recipient_sender_id)


        # Data trasformation
        msg_df["date"] = msg_df["date"].apply(convert_apple_timestamp)
        msg_df["sender"] = np.where(msg_df["is_from_me"] == 1, "me", msg_df["sender_or_recipient_id"].apply(resolve_contact))
        msg_df["recipient"] = np.where(msg_df["is_from_me"] == 0, "me", msg_df["sender_or_recipient_id"].apply(resolve_contact))
        msg_df["message"] = msg_df["text"]

        # Save to CSV
        export_columns = ["date", "sender", "recipient", "chat_name", "message"]

        # Chunk with overlap
        chunks = [msg_df[i:i+CHUNK_ROW_SIZE+CHUNK_OVERLAP] for i in range(0, len(msg_df), CHUNK_ROW_SIZE)]
        for i, chunk in enumerate(chunks):
            chunk[export_columns].to_csv(f"./data/apple/messages/data/imessage_{i+1}.csv", index=False)

        print(f"Exported successfully. {len(chunks)} chunks created.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Read imessage.db file and generate CSV files")
    parser.add_argument(
        "--request_contacts_access",
        action="store_true",
        help="Request contacts access on macOS"
    )
    args = parser.parse_args()

    if args.request_contacts_access:
        request_contacts_access()

    main()
