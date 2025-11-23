from playwright.sync_api import Page


def enable_debug(page: Page):
    page.on("console", lambda msg: print(f"[Console] {msg.type}: {msg.text}"))
    page.on("request", lambda req: print(f"[Request] {req.method} {req.url}"))
    page.on("response", lambda res: print(f"[Response] {res.status} {res.url}"))
    page.on("pageerror", lambda err: print(f"[PageError] {err}"))
    page.on("domcontentloaded", lambda: print("[DOM] DOMContentLoaded fired"))
    page.on("load", lambda: print("[DOM] Page fully loaded"))
