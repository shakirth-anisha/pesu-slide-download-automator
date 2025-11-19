from playwright.sync_api import sync_playwright
import os
import re

def sanitize(name: str):
    return re.sub(r"[^\w\- ]", "", name).strip()

# 1. LOGIN
def login(page, username, password):
    page.goto("https://www.pesuacademy.com/Academy/")
    page.fill("#j_scriptusername", username)
    page.fill("input[name='j_password']", password)
    page.click("button.btn.btn-lg.btn-primary.btn-block")
    page.wait_for_load_state("networkidle")
    print("Logged in successfully.")


# 2. SELECT COURSE
def select_course(page):
    page.click("span.menu-name:has-text('My Courses')")
    page.wait_for_selector("select#semesters")
    page.wait_for_selector("table.table.table-hover")

    rows = page.locator("table.table.table-hover tbody tr")
    count = rows.count()

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

def main():
    username = input("Enter Username: ")
    password = input("Enter Password: ")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        login(page, username, password)
        course_name = select_course(page)

        page.wait_for_timeout(5000)


if __name__ == "__main__":
    main()
