# PESU Academy Slide Download Automation

---

## Index

1. [Overview](#overview)
2. [Installation](#installation)
3. [Auto Download Slides](#auto-download-slides)
4. [Features for Pre-Existing Folders](#features-for-pre-existing-folders)

   * [Converting PPTX to PDF](#converting-pptx-to-pdf)
   * [Merge PDFs](#merge-pdfs)
5. [View Playwright Automation](#view-playwright-automation)
6. [Notes](#notes)

---

## Overview

This Python script automates the process of logging into PESU Academy, selecting a course, selecting a unit, opening the first slide, downloading and optionally merging available files using Playwright. All session data is stored only in memory, and the script prompts for your credentials at runtime. It is designed to simplify navigation inside PESU Academy without saving any user data locally.

---

## Installation

1. Install requirements:

   ```bash
   pip install -r requirements.txt
   ```

2. Install Playwright browsers:

   ```bash
   playwright install
   ```

---

## Auto Download Slides

1. Run the main script:

   ```bash
   python main.py
   ```

2. Enter your SRN/PRN and password when prompted.

3. Follow the on-screen prompts to select a course and unit.

4. The script will open the first slide, download available files, automatically convert pptx to ppt files, and optionally merge them.

---

## Features for Pre-Existing Folders

### Converting PPTX to PDF

You can automatically convert PPTX files to PDF using **`file_conversion.py`** for pre existing folders:

```bash
python file_conversion.py --folder "FolderName"
```

### Merge PDFs

You can merge PDFs from any folder using the `merge.py` script:

```bash
python merge.py --folder "FolderName" --output "merged.pdf"
```

* If `merged.pdf` already exists, the script will automatically create `merged[1].pdf`, `merged[2].pdf`, etc.
* `--folder` is required, `--output` is optional.

---

## View Playwright Automation

To see the browser while automating (for debugging):

1. Change headless mode in `main.py` and `file_conversion.py`:

```python
browser = p.chromium.launch(headless=False)
```

2. Optionally comment out resource blocking:

```python
# page.route(
#     "**/*",
#     lambda route: route.abort()
#     if route.request.resource_type in ["image", "media", "font"]
#     else route.continue_()
# )
```

This will allow you to watch the downloads live in the browser.

---

## Notes

* All scripts are designed to **keep your credentials in memory only**.
* PDF ordering after conversion relies on **existing filenames**, no renaming is done automatically.
* iLovePDF free version limits batch conversion to **3 files at a time**; `file_conversion.py` automatically batches files.

---
