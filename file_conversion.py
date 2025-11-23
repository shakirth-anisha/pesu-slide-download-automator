import argparse
import os
import shutil
import zipfile
from playwright.sync_api import sync_playwright


# File Helpers
def unzip_and_flatten(zip_path, destination):
    extract_dir = os.path.join(destination, "unzipped_temp")
    os.makedirs(extract_dir, exist_ok=True)

    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)

        for root, _, files in os.walk(extract_dir):
            for f in files:
                src = os.path.join(root, f)
                dst = os.path.join(destination, f)
                shutil.move(src, dst)
                print(f"Moved: {f}")

        print(f"Cleaning ZIP and temp folder...")
        os.remove(zip_path)
        shutil.rmtree(extract_dir)

    except Exception as e:
        print(f"Error extracting ZIP: {e}")


def delete_pptx_files(files):
    for f in files:
        try:
            os.remove(f)
            print(f"Deleted: {os.path.basename(f)}")
        except Exception as e:
            print(f"Error deleting {os.path.basename(f)}: {e}")


# Batch Handling
def get_batches(folder, batch_size=3):  # can increase or decrease batch size but ilovepdf needs premium for >3 files
    pptx_files = [
        os.path.join(folder, f)
        for f in os.listdir(folder) if f.lower().endswith(".pptx")
    ]
    for i in range(0, len(pptx_files), batch_size):
        yield pptx_files[i:i + batch_size]


# Main Converter
def convert_batch_with_ilovepdf(pptx_files, folder):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()
        page.route(
                "**/*",
                lambda route: route.abort()
                if route.request.resource_type in ["image", "media", "font"]
                else route.continue_(),
            )
        
        page.goto("https://www.ilovepdf.com/powerpoint_to_pdf", timeout=90_000)

        upload_input = page.locator("input[type='file']")
        upload_input.set_input_files(pptx_files)

        page.wait_for_selector("#fileGroups .file", timeout=200_000)

        page.wait_for_function(
            """() => {
                const b = document.querySelector('button[class*="process"]');
                return b && !b.disabled;
            }""",
            timeout=240_000
        )

        page.locator('button[class*="process"]').click()
        page.wait_for_selector('a.downloader__btn.active', timeout=600_000)

        with page.expect_download() as dl_info:
            page.click('a.downloader__btn.active')

        download = dl_info.value
        downloaded_path = os.path.join(folder, download.suggested_filename)
        download.save_as(downloaded_path)
        browser.close()

    print(f"Downloaded: {downloaded_path}")

    if downloaded_path.lower().endswith(".zip"):
        unzip_and_flatten(downloaded_path, folder)

    delete_pptx_files(pptx_files)


# Main conversion controller
def convert_pptx_to_pdf(folder):
    print(f"Scanning folder: {folder}")

    batches = list(get_batches(folder))
    total_batches = len(batches)

    if total_batches == 0:
        print("No PPTX files found.")
        return

    for batch_num, batch in enumerate(batches, start=1):
        print(f"\n--- Batch {batch_num} / {total_batches} | {len(batch)} files ---\n")
        convert_batch_with_ilovepdf(batch, folder)

    print("\nAll PPTX files converted successfully.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert PPTX to PDF using iLovePDF")
    parser.add_argument("--folder", "--f", dest="folder", required=True, help="Folder path containing .pptx files")
    args = parser.parse_args()

    folder_path = args.folder

    if not os.path.isdir(folder_path):
        print(f"Error: Directory not found: {folder_path}")
        exit(1)

    convert_pptx_to_pdf(folder_path)
