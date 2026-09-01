"""Amazon.com.tr arama sonuçlarından SSD ürünlerini çeker (JS render gerekiyor, Playwright kullanılıyor)."""
from bs4 import BeautifulSoup

from scrapers._browser import fetch_rendered_html
from scrapers._price import MIN_PLAUSIBLE_PRICE, is_nvme, is_ssd, parse_try

SITE = "Amazon.com.tr"
URLS = {
    "1tb": "https://www.amazon.com.tr/s?k=1tb+nvme+ssd",
    "2tb": "https://www.amazon.com.tr/s?k=2tb+ssd",
    "2tb-harici": "https://www.amazon.com.tr/s?k=2tb+harici+ssd",
}


def scrape(capacity: str) -> list[dict]:
    url = URLS[capacity]
    html = fetch_rendered_html(url, wait_selector='div[data-component-type="s-search-result"]')
    soup = BeautifulSoup(html, "html.parser")

    products = []
    for card in soup.select('div[data-component-type="s-search-result"]'):
        asin = card.get("data-asin")
        name_el = card.select_one("h2 span")
        price_el = card.select_one(".a-price .a-offscreen")
        if not asin or not name_el or not price_el:
            continue
        name = name_el.get_text(strip=True)
        if capacity in ("1tb", "2tb") and not is_nvme(name):
            continue
        if capacity == "2tb-harici" and not is_ssd(name):
            continue
        price = parse_try(price_el.get_text())
        if price is None or price < MIN_PLAUSIBLE_PRICE:
            continue
        products.append({
            "site": SITE,
            "name": name,
            "price": price,
            "url": f"https://www.amazon.com.tr/dp/{asin}",
            "capacity": capacity,
        })
    return products


def scrape_all() -> list[dict]:
    results = []
    for capacity in URLS:
        results.extend(scrape(capacity))
    return results


if __name__ == "__main__":
    for p in scrape_all():
        print(p)
