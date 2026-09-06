"""Skroutz.gr kategori sayfalarındaki ürün kartlarını (li.card[data-skuid])
ayrıştıran ortak yardımcı - hem laptop hem SSD karşılaştırması aynı kart
yapısını kullanıyor, bu yüzden ayrı ayrı yazılmadı.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "core"))

from bs4 import BeautifulSoup

from scrapers._price import parse_try


def parse_cards(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    results = []
    for card in soup.select("li.card[data-skuid]"):
        name_el = card.select_one("a.js-sku-link.pic")
        price_el = card.select_one("a.js-sku-link.sku-link")
        if not name_el or not price_el:
            continue
        name = name_el.get("title", "").strip()
        price = parse_try(price_el.get_text())
        href = name_el.get("href", "").split("?")[0]
        if not name or price is None or not href:
            continue
        results.append({
            "name": name,
            "price_eur": price,
            "url": "https://www.skroutz.gr" + href,
        })
    return results
