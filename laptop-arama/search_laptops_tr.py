"""Türkiye'de satılan, 12GB+ VRAM'li RTX 50 serisi laptopları (5070 Ti, 5080,
5090) Amazon.com.tr üzerinden anlık çeker. Diğer laptop-arama script'leri gibi
otomasyonun (core/) parçası değil, sadece elle/bot tetiklemesiyle çalışır.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "core"))

from bs4 import BeautifulSoup

from scrapers._browser import fetch_rendered_html
from scrapers._price import parse_try

SEARCH_URL = "https://www.amazon.com.tr/s?k=rtx+5070+ti+5080+5090+laptop"
# Taban 5070 (8GB) hariç: "5070 ti" ya da düz "5080"/"5090" (bunlar zaten 12GB+).
_GPU_PATTERN = re.compile(r"5070\s?ti|5080|5090", re.IGNORECASE)


def search() -> list[dict]:
    html = fetch_rendered_html(SEARCH_URL, wait_selector='div[data-component-type="s-search-result"]')
    soup = BeautifulSoup(html, "html.parser")

    results = []
    for card in soup.select('div[data-component-type="s-search-result"]'):
        asin = card.get("data-asin")
        name_el = card.select_one("h2 span")
        price_el = card.select_one(".a-price .a-offscreen")
        if not asin or not name_el or not price_el:
            continue
        name = name_el.get_text(strip=True)
        if not _GPU_PATTERN.search(name):
            continue
        price = parse_try(price_el.get_text())
        if price is None:
            continue
        results.append({
            "name": name,
            "price_try": price,
            "url": f"https://www.amazon.com.tr/dp/{asin}",
        })

    results.sort(key=lambda r: r["price_try"])
    return results


if __name__ == "__main__":
    for laptop in search():
        print(f"{laptop['price_try']:>10,.2f} TL  {laptop['name'][:80]}")
        print(f"           {laptop['url']}")
