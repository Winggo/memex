"""
Script to convert .mbox to individual .eml files
"""
import argparse
import mailbox
import re
import os


def remove_xml_processing_instructions(text):
    """Remove <?xml...?> and <?php...?> tags in eml files, as it breaks unstructured's parser"""
    patterns = [
        # r'<\?xml[^>]*>',  # XML processing instructions
        # r'<xml[^>]*\s*>',   # Self-closing <xml ... />
        # r'<xml[^>]*>.*?xml[^>]*>',  # Opening <xml> tags, their contents, and closing xml> tags
        # r'</xml>',
        # r'<\?php[^>]*?>',
        r'<\?xml[^>]*?>',
        r'<\?php[^>]*?>',
    ]
    for pattern in patterns:
        text = re.sub(pattern, '', text, flags=re.MULTILINE | re.IGNORECASE | re.DOTALL)
    return text


def main():
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
                processed_message = remove_xml_processing_instructions(message.as_string())
                f.write(processed_message)
            email_id += 1


main()
