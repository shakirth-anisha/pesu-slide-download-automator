import os
import re
import time

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
    
    # Check for login error message
    error_div = page.locator("div.login-msg")
    if error_div.is_visible():
        error_text = error_div.inner_text().strip()
        raise ValueError(f"Login failed: {error_text}")
    
    print("Logged in successfully.")
    return True


# 2. OPEN MY COURSES
def open_my_courses(page):
    page.wait_for_selector(
        "span.menu-name:has-text('My Courses')",
        timeout=15000
        )
    page.click("span.menu-name:has-text('My Courses')")
    page.wait_for_selector("table.table.table-hover", timeout=15000)


# 3. SELECT SEMESTER
def course_table_signature(page):
    """Snapshot the course table so an AJAX refresh can be detected.

    Snapshot every row's text, not just the count and first row: two
    semesters can share a row count and first course, which would make the
    refresh look like it never happened.
    """
    rows = page.locator("table.table.table-hover tbody tr")
    return tuple(text.strip() for text in rows.all_text_contents())


def wait_for_course_table_change(page, previous, timeout=15000):
    """Poll until the course table differs from the snapshot in previous.

    Selecting a semester swaps the table in place without a page load, so
    there is no navigation or load state to wait on.
    """
    deadline = time.monotonic() + timeout / 1000
    while time.monotonic() < deadline:
        page.wait_for_timeout(200)
        if course_table_signature(page) != previous:
            return True

    print("Course list did not refresh in time. Continuing anyway.")
    return False


def select_semester(page):
    page.wait_for_selector("#semesters", timeout=15000)
    # Options in a closed <select> have no bounding box, so Playwright never
    # treats them as visible. Wait for them to be attached instead.
    page.wait_for_selector(
        "#semesters option",
        state="attached",
        timeout=15000
        )

    options = page.locator("#semesters option")
    option_count = options.count()

    semesters = []
    for i in range(option_count):
        option = options.nth(i)
        # text_content() rather than inner_text(), which is rendering-aware
        # and returns "" for unrendered elements.
        name = option.text_content().strip()
        semesters.append((name, option.get_attribute("value")))

    # Key by the semester's own number, not its position in the dropdown:
    # the site lists newest first, so position 3 is not Sem-3.
    numbered = {}
    unnumbered = []
    for name, value in semesters:
        match = re.search(r"\d+", name)
        if match:
            numbered[int(match.group())] = (name, value)
        else:
            unnumbered.append(name)

    if unnumbered:
        print("\nSkipping semesters without a number: {}".format(
            ", ".join(unnumbered)))

    print("\nAvailable Semesters:")
    for number in sorted(numbered):
        print(f"{number}. {numbered[number][0]}")

    valid = ", ".join(str(number) for number in sorted(numbered))
    while True:
        answer = input(f"\nEnter semester number to open ({valid}): ").strip()
        if answer.isdigit() and int(answer) in numbered:
            semester_name, value = numbered[int(answer)]
            break
        print(f"Please enter one of: {valid}")

    print(f"Opening {semester_name}...")

    # Re-selecting the current semester fires no onchange, so nothing to wait
    # for.
    if value != page.locator("#semesters").input_value():
        previous = course_table_signature(page)
        page.select_option("#semesters", value=value)
        wait_for_course_table_change(page, previous)

    return sanitize(semester_name)


# 4. SELECT COURSE
def select_course(page):
    page.wait_for_selector("table.table.table-hover", timeout=15000)
    no_content = page.locator(
            "h2:text('No subjects found')"
        )

    rows = page.locator("table.table.table-hover tbody tr")
    count = rows.count()

    if no_content.is_visible() or not count:
        print("No courses found in this semester.")
        return None

    courses = []
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


# 5. SELECT UNIT
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


# 6. CLICK FIRST SLIDE
def open_first_slide(page):
    page.wait_for_selector("span.pesu-icon-presentation-graphs", timeout=15000)
    page.locator("a:has(span.pesu-icon-presentation-graphs)").first.click()
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(800)
    print("Clicked first slide entry.")


def build_folder(semester_name, course_name, unit_name):
    """Folder for one unit, kept separate per semester."""
    return f"{semester_name} {course_name} {unit_name}"


# 7. DOWNLOAD SLIDES
def download_slides(page, folder, downloaded_urls):
    page.wait_for_timeout(800)
    page.wait_for_selector(".link-preview", timeout=15000)

    slide_items = page.locator(".link-preview")
    slide_count = slide_items.count()
    print(f"\nFound {slide_count} files.")

    os.makedirs(folder, exist_ok=True)

    existing = [
        int(f.split(".")[0]) for f in os.listdir(folder)
        if f.split(".")[0].isdigit()
    ]
    next_number = max(existing) + 1 if existing else 101

    for i in range(slide_count):
        item = slide_items.nth(i)

        # Case 1: <a onclick="loadIframe(...)">
        link = item.locator("a")
        onclick = link.get_attribute("onclick") if link.count() else None
        urls = []
        is_case2 = False

        if onclick:
            urls = re.findall(r"loadIframe\('([^']+)", onclick)

        # Case 2: <div onclick="downloadcoursedoc(...)">
        if not urls:
            onclick_div = item.get_attribute("onclick")
            if onclick_div:
                matches = re.findall(
                    r"downloadcoursedoc\('([^']+)'",
                    onclick_div
                )
                if matches:
                    urls = [
                        f"/Academy/a/referenceMeterials/downloadslidecoursedoc/{m}"
                        for m in matches
                    ]

                    is_case2 = True

        if not urls:
            print("Could not extract URL.")
            continue

        for url in urls:
            file_url = "https://www.pesuacademy.com" + url
            file_url = file_url.split("#")[0]

            if file_url in downloaded_urls:
                print(f"Skipping already downloaded: {file_url}")
                continue

            print(f"\nDownloading: {file_url}")
            response = page.request.get(file_url)
            if response.status != 200:
                print(f"Failed ({response.status})")
                continue

            # Force .pptx for case 2, .pdf otherwise
            ext = ".pptx" if is_case2 else ".pdf"
            filename = f"{next_number}{ext}"
            filepath = os.path.join(folder, filename)
            with open(filepath, "wb") as f:
                f.write(response.body())

            print(f"Saved → {filepath}")
            downloaded_urls.add(file_url)
            next_number += 1
            page.wait_for_timeout(300)


# 8. PAGE NAVIGATION
def navigate_through_pages(page, folder, downloaded_urls):
    while True:
        page.wait_for_selector(
            ".coursecontent-navigation-area a.pull-right",
            timeout=15000
            )
        next_button = page.locator(
            ".coursecontent-navigation-area a.pull-right"
            )
        label = next_button.inner_text().strip()
        print("\nCurrent button:", label)

        # Open slides tab
        slides_tab = page.locator("#contentType_2")
        slides_tab.click()
        page.wait_for_timeout(600)

        no_slides = page.locator(
            "h2:text('No Slides Content to Display')"
        )

        if no_slides.is_visible():
            print("No slides available. Skipping download.")
        else:
            download_slides(page, folder, downloaded_urls)

        if "Back to Units" in label:
            print("Reached 'Back to Units'. Stopping navigation.")
            break

        next_button.click()
        print("Clicked next… waiting for next page load")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(800)

    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(500)
