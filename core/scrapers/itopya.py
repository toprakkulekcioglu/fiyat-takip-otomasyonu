"""itopya.com kategori sayfalarından SSD ürünlerini çeker (sunucu tarafında render ediliyor, JS gerekmiyor)."""
import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from scrapers._price import MIN_PLAUSIBLE_PRICE, is_nvme, is_ssd, parse_try

SITE = "itopya.com"
BASE_URL = "https://www.itopya.com"
URLS = {
    "1tb": "https://www.itopya.com/ssd_k20?kapasite=1tb-q3577",
    "2tb": "https://www.itopya.com/ssd_k20?kapasite=2tb-q3575",
    "2tb-harici": "https://www.itopya.com/tasinabilir-disk_k89?kapasite=2tb-q3575",
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
        name = link_el.get_text(strip=True)
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


def scrape_product(url: str) -> dict | None:
    """Kullanıcının verdiği tekil bir ürün linkinden ad+fiyat çeker.

    Ürün sayfasında kategori kartlarından farklı bir yapı var: fiyat
    ".product-price-warning-detail" içinde "Sepette X TL" formatında (kampanyalı
    ürünlerde sepet indirimi öne çıkarılıyor - bu asıl ödenecek fiyat, parse_try
    baştaki "Sepette" kelimesini yok sayıp sayıyı çıkarıyor).
    """
    response = requests.get(url, headers=HEADERS, timeout=15)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    name_el = soup.select_one("h1")
    price_el = soup.select_one(".product-price-warning-detail")
    if not name_el or not price_el:
        return None
    price = parse_try(price_el.get_text())
    if price is None:
        return None
    return {"name": name_el.get_text(strip=True), "price": price}


if __name__ == "__main__":
    for p in scrape_all():
        print(p)
