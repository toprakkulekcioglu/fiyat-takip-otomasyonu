"""Playwright ile JS render gerektiren sayfaları açıp HTML içeriğini döndürür."""
from playwright.sync_api import sync_playwright

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)

# Konteyner/düşük bellekli ortamlarda (örn. Render'ın 512MB ücretsiz katmanı)
# Chromium'un varsayılan davranışı bellek sorunlarına yol açabiliyor -
# /dev/shm konteynerlerde genelde çok küçük (64MB) olduğu için Chromium'a
# bunun yerine disk kullanmasını söylüyoruz, ayrıca GPU/uzantı gibi gereksiz
# bileşenleri kapatıyoruz.
LAUNCH_ARGS = ["--disable-dev-shm-usage", "--disable-gpu", "--disable-extensions"]


def fetch_rendered_html(url: str, wait_selector: str, timeout_ms: int = 30000) -> str:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=LAUNCH_ARGS)
        page = browser.new_page(user_agent=USER_AGENT, locale="tr-TR")
        # "load" yerine "domcontentloaded": reklam/izleyici scriptlerinin tamamının
        # bitmesini beklemeye gerek yok, zaten hemen altında ürün elementini bekliyoruz.
        page.goto(url, timeout=timeout_ms, wait_until="domcontentloaded")
        page.wait_for_selector(wait_selector, timeout=timeout_ms)
        html = page.content()
        browser.close()
        return html


def fetch_multiple_rendered_html(
    requests: list[tuple[str, str]], timeout_ms: int = 30000
) -> list[str | Exception]:
    """Birden fazla sayfayı TEK bir Chromium örneğiyle sırayla açar - her biri için
    ayrı tarayıcı başlatıp kapatmaktan (bellek/CPU açısından pahalı) daha hafif.
    Düşük bellekli sunucularda (örn. laptop-arama botunun çalıştığı Render) art
    arda birden fazla siteyi taramak gerektiğinde kullanılıyor.

    requests: [(url, wait_selector), ...]
    Döner: her istek için HTML string'i, o istek başarısız olduysa Exception nesnesi
    (tek bir sayfanın hatası diğerlerini engellemesin diye).
    """
    results: list[str | Exception] = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=LAUNCH_ARGS)
        for url, wait_selector in requests:
            try:
                page = browser.new_page(user_agent=USER_AGENT, locale="tr-TR")
                page.goto(url, timeout=timeout_ms, wait_until="domcontentloaded")
                page.wait_for_selector(wait_selector, timeout=timeout_ms)
                results.append(page.content())
                page.close()
            except Exception as e:
                results.append(e)
        browser.close()
    return results
