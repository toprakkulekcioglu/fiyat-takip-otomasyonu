"""Playwright ile JS render gerektiren sayfaları açıp HTML içeriğini döndürür."""
from playwright.sync_api import sync_playwright

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)


def fetch_rendered_html(url: str, wait_selector: str, timeout_ms: int = 30000) -> str:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(user_agent=USER_AGENT, locale="tr-TR")
        # "load" yerine "domcontentloaded": reklam/izleyici scriptlerinin tamamının
        # bitmesini beklemeye gerek yok, zaten hemen altında ürün elementini bekliyoruz.
        page.goto(url, timeout=timeout_ms, wait_until="domcontentloaded")
        page.wait_for_selector(wait_selector, timeout=timeout_ms)
        html = page.content()
        browser.close()
        return html
