"""
Read vcf files to process Apple contacts

Usage:
`python3 src/scripts/read_vcards.py`

"""
import os
from glob import glob
import vobject


def unfold_lines(content):
    lines = content.splitlines()
    if not lines:
        return ""
    
    unfolded = [lines[0]]
    for line in lines[1:]:
        if line and (line[0].isspace()):
            unfolded[-1] += line.lstrip()
        else:
            unfolded.append(line)

    return "\n".join(unfolded)


def clean_vcard(content):
    content = content.replace('"', '')
    return content


def main():
    vcf_file_paths = [
        path for path in glob(os.path.join("data/apple/contacts", "**/*.vcf"), recursive=True)
        if os.path.isfile(path)
    ]
    contacts = []

    for vcf_file_path in vcf_file_paths:
        with open(vcf_file_path, "r") as f:
            content = f.read()
            unfolded_content = unfold_lines(content)
            cleaned_content = clean_vcard(unfolded_content)
            vcard = vobject.readOne(cleaned_content)

            contact_info = {}
            if hasattr(vcard, "fn"):
                contact_info["name"] = vcard.fn.value
            if hasattr(vcard, "tel_list"):
                contact_info["phone_numbers"] = ", ".join([tel.value for tel in vcard.tel_list]).replace("\xa0", " ")
            if hasattr(vcard, "email_list"):
                contact_info["emails"] = ", ".join([email.value for email in vcard.email_list])
            if hasattr(vcard, "bday"):
                contact_info["birthday"] = vcard.bday.value
            if hasattr(vcard, "adr"):
                contact_info["address"] = str(vcard.adr.value).replace("\n", "; ")

            contact_str = ""
            for k, v in contact_info.items():
                if k == "name":
                    contact_str += f"Contact info for {v}\n"
                else:
                    contact_str += f"{k}: {v}\n"
            contacts.append(contact_str)


    for i, contact in enumerate(contacts):
        with open(os.path.join("data/apple/contacts/data", f"contact_{i+1}.txt"), "w", encoding="utf-8") as new_file:
            new_file.write(contact)

    print(f"Processed {len(contacts)} contacts successfully")


if __name__ == "__main__":
    main()
