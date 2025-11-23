import os
import argparse
from PyPDF2 import PdfMerger
from dotenv import set_key, dotenv_values

ENV_FILE = ".env"


def get_unique_output_path(folder, base_name):
    name, ext = os.path.splitext(base_name)
    ext = ext or ".pdf"

    candidate = f"{name}{ext}"
    counter = 1
    while os.path.exists(os.path.join(folder, candidate)):
        candidate = f"{name}[{counter}]{ext}"
        counter += 1

    return os.path.join(folder, candidate)


def merge(folder, output_name=None):
    if not os.path.exists(folder) or not os.path.isdir(folder):
        print(f"Folder doesn't exist: {folder}")
        return

    pdfs = [f for f in os.listdir(folder) if f.lower().endswith(".pdf")]
    if len(pdfs) < 2:
        print("Nothing to merge.")
        return

    pdfs = sorted(
        pdfs,
        key=lambda x: (
            int(os.path.splitext(x)[0])
            if x.split(".")[0].isdigit()
            else float("inf")
        ),
    )

    if not output_name:
        output_name = "merged.pdf"
    if not output_name.lower().endswith(".pdf"):
        output_name += ".pdf"

    output_path = get_unique_output_path(folder, output_name)

    merger = PdfMerger()
    for pdf in pdfs:
        merger.append(os.path.join(folder, pdf))

    merger.write(output_path)
    merger.close()

    print(f"Merged PDF created → {output_path}")


# 7. MERGE PDFs
def ask_and_merge_pdfs(folder, output_name = None):
    values = dotenv_values(ENV_FILE) if os.path.exists(ENV_FILE) else {}
    pref = values.get("MERGE_PDFS", None)

    other_files = [
        f for f in os.listdir(folder)
        if os.path.isfile(os.path.join(folder, f)) and not f.lower().endswith(".pdf")
    ]

    if other_files:
        print("\n--- The following files are NOT PDFs ---")
        for f in other_files:
            print("  •", f)
        print("--- These will NOT be included in merging ---")

    if pref == "-1":
        return
    if pref == "1":
        merge(folder)
        return

    print("\nMerge all PDFs into a single file?")
    print("1. Always")
    print("2. Yes")
    print("3. No")
    print("4. Don't ask again (always no)")
    choice = input("Select option: ").strip()

    if choice == "1":
        merge(folder, output_name)
        set_key(ENV_FILE, "MERGE_PDFS", "1")
    elif choice == "2":
        merge(folder, output_name)
        set_key(ENV_FILE, "MERGE_PDFS", "0")
    elif choice == "3":
        set_key(ENV_FILE, "MERGE_PDFS", "0")
    elif choice == "4":
        set_key(ENV_FILE, "MERGE_PDFS", "-1")
        print("Preference saved. Will not merge.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Merge PDFs in a folder")
    parser.add_argument(
        "--folder",
        required=True,
        help="Folder containing PDF files"
    )
    parser.add_argument("--output", help="Output PDF name (optional)")
    args = parser.parse_args()

    ask_and_merge_pdfs(args.folder, args.output)
