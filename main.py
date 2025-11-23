from playwright.sync_api import sync_playwright, TimeoutError
from dotenv import load_dotenv
import os
import getpass
from automate import (
    login,
    select_course,
    select_unit,
    open_first_slide,
    download_slides,
    navigate_through_pages,
)
from file_conversion import convert_pptx_to_pdf
from merge import ask_and_merge_pdfs

ENV_FILE = ".env"
downloaded_urls = set()


def main():
    if os.path.exists(ENV_FILE):
        load_dotenv(ENV_FILE)
        dont_ask_again = os.getenv("DONT_ASK_AGAIN", "0")
        username = os.getenv("USERNAME")
        password = os.getenv("PASSWORD")

        if dont_ask_again == "1" and (
            username == "NOT_SET" or password == "NOT_SET"
        ):
            username = input("Enter Username (SRN / PRN): ")
            password = getpass.getpass("Enter Pesu Password: ")
        elif dont_ask_again != "1":
            username = username or input("Enter Username (SRN / PRN): ")
            password = password or getpass.getpass("Enter Pesu Password: ")

    else:
        username = input("Enter Username (SRN / PRN): ")
        password = getpass.getpass("Enter Pesu Password: ")

        choice = input(
            "\nSave credentials locally?\n1. Yes\n2. No\n3. Don't ask again\n"
            "Select Option: "
        ).strip().lower()

        if choice == "1":
            with open(ENV_FILE, "w") as f:
                f.write(
                    "USERNAME={}\nPASSWORD={}\nDONT_ASK_AGAIN=0\n".format(
                        username, password
                    )
                )
            print("Credentials saved in {}".format(ENV_FILE))
        elif choice == "3":
            with open(ENV_FILE, "w") as f:
                f.write(
                    "USERNAME=NOT_SET\nPASSWORD=NOT_SET\nDONT_ASK_AGAIN=1\n"
                )
            print("Preference saved. Will not ask for credentials again.")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
            page.route(
                "**/*",
                lambda route: route.abort()
                if route.request.resource_type in ["image", "media", "font"]
                else route.continue_(),
            )

            login(page, username, password)
            course_name = select_course(page)
            unit_name = select_unit(page)
            open_first_slide(page)
            
            download_slides(page, course_name, unit_name, downloaded_urls)
            navigate_through_pages(
                page, course_name,
                unit_name, downloaded_urls)

            folder = "{} {}".format(course_name, unit_name)

        convert_pptx_to_pdf(folder)
        ask_and_merge_pdfs(folder)

    except TimeoutError:
        print("\nUnstable internet connection. Try again later.")
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as exc:
        print("\nAn unexpected error occurred: {}".format(exc))
    finally:
        try:
            browser.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()
