"""
Script to convert .mbox to individual .eml files
"""
import argparse
import mailbox
import os

parser = argparse.ArgumentParser(description="Create .eml files from .mbox file")
parser.add_argument(
    "--file_path",
    type=str,
)
parser.add_argument(
    "--output_dir",
    type=str,
)
parser.add_argument(
    "--dry_run",
    action="store_true",
    help="Load mbox file without processing it"
)
args = parser.parse_args()

mbox = mailbox.mbox(args.file_path)
print(f"{len(mbox)} emails found")

if not args.dry_run:
    email_id = 1
    for message in mbox:
        if message.get_content_type() == "multipart/mixed":
            continue
        
        with open(os.path.join(args.output_dir, f"email_{email_id}.eml"), "w", encoding="utf-8") as f:
            f.write(message.as_string())
        email_id += 1
