from playwright.sync_api import sync_playwright, TimeoutError
import os
import getpass
from automate import (download_slides, login, navigate_through_pages,
    open_first_slide, select_course, select_unit)
from file_conversion import convert_pptx_to_pdf
from merge import ask_and_merge_pdfs
from config import Config

downloaded_urls = set()


def main():
    # Load environment configuration
    Config.load_env()
    
    # Check if credentials are already saved
    dont_ask_again = Config.get_dont_ask_again()
    username = Config.get_username()
    password = Config.get_password()

    # Determine if we need to ask for credentials
    needs_credentials = not username or username == "NOT_SET" or not password or password == "NOT_SET"
    newly_entered_credentials = False
    
    if needs_credentials:
        username = input("Enter Username (SRN / PRN): ")
        password = getpass.getpass("Enter Pesu Password: ")
        newly_entered_credentials = True

    max_attempts = 3
    attempt = 0
    debug_mode = Config.is_debug_enabled()
    
    try:
        while attempt < max_attempts:
            attempt += 1
            
            try:
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=False)
                    context = browser.new_context()
                    page = context.new_page()
                    # page.route(
                    #     "**/*",
                    #     lambda route: route.abort()
                    #     if route.request.resource_type in ["image", "media", "font"]
                    #     else route.continue_(),
                    # )

                    login(page, username, password)
                    
                    # Debug checkpoint after successful login
                    if debug_mode:
                        print("\n[DEBUG] Login successful!")
                        print("[DEBUG] About to fetch course names...")
                        proceed = input("[DEBUG] Proceed to fetch courses? (yes/no): ").strip().lower()
                        if proceed not in ("yes", "y", "1"):
                            print("[DEBUG] Exiting before course fetch.")
                            return
                    
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
                
                # Login was successful - ask to save credentials if they were newly entered
                if newly_entered_credentials and not dont_ask_again:
                    choice = input(
                        "\nSave credentials locally?\n1. Yes\n2. No\n3. Don't ask again\n"
                        "Select Option: "
                    ).strip().lower()

                    if choice == "1":
                        Config.set_credentials(username, password)
                        Config.set_env("DONT_ASK_AGAIN", "0")
                        print("Credentials saved in {}".format(Config.get_env_file()))
                    elif choice == "3":
                        Config.clear_credentials()
                        Config.set_dont_ask_again(True)
                        print("Preference saved. Will not ask for credentials again.")
                
                break  # Success, exit the retry loop
                
            except ValueError as e:
                # Login failure - credentials are invalid
                if attempt < max_attempts:
                    print("\n{}\nAttempt {} of {}.".format(str(e), attempt, max_attempts))
                    username = input("Enter Username (SRN / PRN): ")
                    password = getpass.getpass("Enter Pesu Password: ")
                    newly_entered_credentials = True
                else:
                    print("\n{}\nMax login attempts reached. Exiting.".format(str(e)))
                    return
                    
    except TimeoutError:
        print("\nUnstable internet connection. Try again later. If issue persists, please contact the developer.")
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
