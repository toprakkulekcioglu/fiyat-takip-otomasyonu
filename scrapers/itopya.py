"""itopya.com kategori sayfalarından SSD ürünlerini çeker (sunucu tarafında render ediliyor, JS gerekmiyor)."""
import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from scrapers._price import MIN_PLAUSIBLE_PRICE, parse_try

SITE = "itopya.com"
BASE_URL = "https://www.itopya.com"
URLS = {
    "1tb": "https://www.itopya.com/ssd_k20?kapasite=1tb-q3577",
    "2tb": "https://www.itopya.com/ssd_k20?kapasite=2tb-q3575",
}
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    )
}


def scrape(capacity: str) -> list[dict]:
    url = URLS[capacity]
    response = requests.get(url, headers=HEADERS, timeout=15)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    products = []
    for card in soup.select("div.product[data-urun-id]"):
        link_el = card.select_one("a.title[href]")
        price_el = card.select_one("span.product-price strong")
        if not link_el or not price_el:
            continue
        price = parse_try(price_el.get_text())
        if price is None or price < MIN_PLAUSIBLE_PRICE:
            continue
        products.append({
            "site": SITE,
            "name": link_el.get_text(strip=True),
            "price": price,
            "url": urljoin(BASE_URL, link_el.get("href")),
            "capacity": capacity,
        })
    return products


def scrape_all() -> list[dict]:
    results = []
    for capacity in URLS:
        results.extend(scrape(capacity))
        time.sleep(2)
    return results


if __name__ == "__main__":
    for p in scrape_all():
        print(p)
