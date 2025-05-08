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
if args.dry_run:
    print(f"{len(mbox)} emails found")
else:
    for i, message in enumerate(mbox):
        with open(os.path.join(args.output_dir, f"email_{i}.eml"), "w", encoding="utf-8") as f:
            f.write(message.as_string())
