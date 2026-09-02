"""Türkiye'de satılan, 12GB+ VRAM'li RTX 50 serisi laptopları (5070 Ti, 5080,
5090) Amazon.com.tr + n11.com üzerinden anlık çeker. Diğer laptop-arama
script'leri gibi otomasyonun (core/) parçası değil, sadece elle/bot
tetiklemesiyle çalışır.

İki kaynak kullanılıyor çünkü tek bir sitenin arama sonuçları istekten isteğe
değişkenlik gösterebiliyor (reklam/sıralama rotasyonu) - bu da yurtdışı
kataloğuyla örtüşme ihtimalini gereksiz yere düşürüyor.
"""
import re
import sys
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "core"))

from scrapers._browser import fetch_rendered_html
from scrapers._price import parse_try

AMAZON_URL = "https://www.amazon.com.tr/s?k=rtx+5070+ti+5080+5090+laptop"
N11_URL = "https://www.n11.com/bilgisayar/dizustu-bilgisayar?q=rtx+5070+ti+5080+5090"
N11_BASE = "https://www.n11.com"
N11_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    )
}

# Taban 5070 (8GB) hariç: "5070 ti" ya da düz "5080"/"5090" (bunlar zaten 12GB+).
_GPU_PATTERN = re.compile(r"5070\s?ti|5080|5090", re.IGNORECASE)
# Arama, masaüstü ekran kartlarını da (laptop değil) döndürebiliyor - bunları eleriz.
_LAPTOP_INDICATOR = re.compile(r"dizüstü|laptop|notebook", re.IGNORECASE)
_DESKTOP_CARD_INDICATOR = re.compile(r"ekran kart[ıi]|\bvga\b", re.IGNORECASE)


def _is_laptop(name: str) -> bool:
    return bool(_LAPTOP_INDICATOR.search(name)) and not _DESKTOP_CARD_INDICATOR.search(name)


def _from_amazon() -> list[dict]:
    html = fetch_rendered_html(AMAZON_URL, wait_selector='div[data-component-type="s-search-result"]')
    soup = BeautifulSoup(html, "html.parser")

    results = []
    for card in soup.select('div[data-component-type="s-search-result"]'):
        asin = card.get("data-asin")
        name_el = card.select_one("h2 span")
        price_el = card.select_one(".a-price .a-offscreen")
        if not asin or not name_el or not price_el:
            continue
        name = name_el.get_text(strip=True)
        if not _GPU_PATTERN.search(name) or not _is_laptop(name):
            continue
        price = parse_try(price_el.get_text())
        if price is None:
            continue
        results.append({"name": name, "price_try": price, "url": f"https://www.amazon.com.tr/dp/{asin}"})
    return results


def _from_n11() -> list[dict]:
    response = requests.get(N11_URL, headers=N11_HEADERS, timeout=15)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    results = []
    for card in soup.select("a.product-item[href]"):
        name_el = card.select_one("h2.product-item-title")
        price_el = card.select_one("h3.price-currency")
        if not name_el or not price_el:
            continue
        name = name_el.get_text(strip=True)
        if not _GPU_PATTERN.search(name) or not _is_laptop(name):
            continue
        price = parse_try(price_el.get_text())
        if price is None:
            continue
        results.append({"name": name, "price_try": price, "url": urljoin(N11_BASE, card.get("href"))})
    return results


def search() -> list[dict]:
    results = []
    for fetch in (_from_amazon, _from_n11):
        try:
            found = fetch()
            print(f"  {fetch.__name__}: {len(found)} urun", flush=True)
            results.extend(found)
        except Exception as e:
            print(f"  {fetch.__name__}: HATA - {e}", flush=True)

    results.sort(key=lambda r: r["price_try"])
    return results


if __name__ == "__main__":
    for laptop in search():
        print(f"{laptop['price_try']:>10,.2f} TL  {laptop['name'][:80]}")
        print(f"           {laptop['url']}")
