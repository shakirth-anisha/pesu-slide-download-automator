from playwright.sync_api import sync_playwright, TimeoutError
from dotenv import load_dotenv, set_key, dotenv_values
import os
import re
import getpass

ENV_FILE = ".env"
downloaded_urls = set()

def sanitize(name: str):
    return re.sub(r"[^\w\- ]", "", name).strip()

# 1. LOGIN
def login(page, username, password):
    page.goto("https://www.pesuacademy.com/Academy/")
    page.fill("#j_scriptusername", username)
    page.fill("input[name='j_password']", password)
    page.click("button.btn.btn-lg.btn-primary.btn-block")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(800)
    print("Logged in successfully.")

# 2. SELECT COURSE
def select_course(page):
    page.wait_for_selector("span.menu-name:has-text('My Courses')", timeout=15000)
    page.click("span.menu-name:has-text('My Courses')")
    page.wait_for_selector("table.table.table-hover", timeout=15000)
    no_content = page.locator("h2:text('No subjects found')")

    rows = page.locator("table.table.table-hover tbody tr")
    count = rows.count()

    courses = []
    if no_content.is_visible():
        print("No courses found in this semester.")
    else:
        for i in range(count):
            title = rows.nth(i).locator("td:nth-child(2)").inner_text().strip()
            courses.append(title)

    print("\nAvailable Courses:")
    for index, course in enumerate(courses, 1):
        print(f"{index}. {course}")

    choice = int(input("\nEnter course number to open: "))
    selected_row = rows.nth(choice - 1)
    selected_row.click()

    course_name = sanitize(courses[choice - 1])
    print(f"Opening: {course_name}")

    return course_name

# 3. SELECT UNIT
def select_unit(page):
    page.wait_for_selector("#courselistunit li", timeout=15000)

    units = page.locator("#courselistunit li a")
    unit_count = units.count()

    names = []
    for i in range(unit_count):
        names.append(units.nth(i).inner_text().strip())

    print("\nAvailable Units:")
    for index, name in enumerate(names, 1):
        print(f"{index}. {name}")

    choice = int(input("\nEnter unit number to open: "))
    selected_unit = units.nth(choice - 1)

    unit_name = sanitize(names[choice - 1])
    selected_unit.click()

    print(f"Opening {unit_name}...")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(800)

    return unit_name

# 4. CLICK FIRST SLIDE
def open_first_slide(page):
    page.wait_for_selector("span.pesu-icon-presentation-graphs", timeout=15000)
    page.locator("a:has(span.pesu-icon-presentation-graphs)").first.click()
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(800)
    print("Clicked first slide entry.")

# 5. DOWNLOAD SLIDES
def download_slides(page, course_name, unit_name, downloaded_urls):
    page.wait_for_timeout(800)
    page.wait_for_selector(".link-preview a", timeout=15000)

    slide_links = page.locator(".link-preview a")
    slide_count = slide_links.count()
    print(f"\nFound {slide_count} files.")

    folder = f"{course_name} {unit_name}"
    os.makedirs(folder, exist_ok=True)

    existing = [
        int(f.split(".")[0]) for f in os.listdir(folder)
        if f.split(".")[0].isdigit()
    ]
    next_number = max(existing) + 1 if existing else 101

    for i in range(slide_count):
        link = slide_links.nth(i)
        onclick = link.get_attribute("onclick")
        matches = re.findall(r"loadIframe\('([^']+)", onclick)

        if not matches:
            print("Could not extract URL.")
            continue

        for url in matches:
            pdf_url = "https://www.pesuacademy.com" + url
            pdf_url = pdf_url.split("#")[0]

            if pdf_url in downloaded_urls:
                print(f"Skipping already downloaded: {pdf_url}")
                continue

            print(f"\nDownloading: {pdf_url}")
            response = page.request.get(pdf_url)
            if response.status != 200:
                print(f"Failed ({response.status})")
                continue

            filename = f"{next_number}.pdf"
            filepath = os.path.join(folder, filename)

            with open(filepath, "wb") as f:
                f.write(response.body())

            print(f"Saved → {filepath}")
            downloaded_urls.add(pdf_url)
            next_number += 1
            page.wait_for_timeout(300)

# 6. PAGE NAVIGATION
def navigate_through_pages(page, course_name, unit_name, downloaded_urls):
    while True:
        page.wait_for_selector(".coursecontent-navigation-area a.pull-right", timeout=15000)
        next_button = page.locator(".coursecontent-navigation-area a.pull-right")
        label = next_button.inner_text().strip()
        print("\nCurrent button:", label)

        # Open slides tab
        slides_tab = page.locator("#contentType_2")
        slides_tab.click()
        page.wait_for_timeout(600)

        no_slides = page.locator("h2:text('No Slides Content to Display')")

        if no_slides.is_visible():
            print("No slides available. Skipping download.")
        else:
            download_slides(page, course_name, unit_name, downloaded_urls)

        if "Back to Units" in label:
            print("Reached 'Back to Units'. Stopping navigation.")
            break

        next_button.click()
        print("Clicked next… waiting for next page load")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(800)

    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(500)

def main():
    if os.path.exists(ENV_FILE):
        load_dotenv(ENV_FILE)
        dont_ask_again = os.getenv("DONT_ASK_AGAIN", "0")
        username = os.getenv("USERNAME")
        password = os.getenv("PASSWORD")

        if dont_ask_again == "1" and (username == "NOT_SET" or password == "NOT_SET"):
            username = input("Enter Username (SRN / PRN): ")
            password = getpass.getpass("Enter Pesu Password: ")
        elif dont_ask_again != "1":
            username = username or input("Enter Username (SRN / PRN): ")
            password = password or getpass.getpass("Enter Pesu Password: ")

    else:
        username = input("Enter Username (SRN / PRN): ")
        password = getpass.getpass("Enter Pesu Password: ")

        choice = input("\nSave credentials locally?\n1. Yes\n2. No\n3. Don't ask again\nSelect Option: ").strip().lower()
        if choice == "1":
            with open(ENV_FILE, "w") as f:
                f.write(f"USERNAME={username}\nPASSWORD={password}\nDONT_ASK_AGAIN=0\n")
            print(f"Credentials saved in {ENV_FILE}")
        elif choice == "3":
            with open(ENV_FILE, "w") as f:
                f.write(f"USERNAME=NOT_SET\nPASSWORD=NOT_SET\nDONT_ASK_AGAIN=1\n")
            print(f"Preference saved. Will not ask for credentials again.")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
            page.route(
                "**/*",
                lambda route: route.abort() if route.request.resource_type in ["image", "media", "font"] else route.continue_()
            )

            login(page, username, password)
            course_name = select_course(page)
            unit_name = select_unit(page)
            open_first_slide(page)
            download_slides(page, course_name, unit_name, downloaded_urls)
            navigate_through_pages(page, course_name, unit_name, downloaded_urls)

    except TimeoutError:
        print("\nUnstable internet connection. Try again later.")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
    finally:
        try:
            browser.close()
        except:
            pass

if __name__ == "__main__":
    main()
