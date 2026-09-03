"""Selanik'te (Yunanistan) mağazaları olan büyük teknoloji zincirlerinin laptop
fiyatlarını Skroutz.gr üzerinden (Yunanistan'ın ana fiyat karşılaştırma sitesi -
Public, Kotsovolos, Plaisio gibi büyük zincirleri tek yerde topluyor) çeker.
Otomasyonun (core/) parçası değil, sadece bot tetiklemesiyle çalışır.

İki ayrı arama sunuyor:
- search_by_gpu(): RTX 5070 Ti / 5080 / 5090 (12GB+ VRAM) ekran kartlı laptoplar
- search_by_cpu(): Ryzen AI 9 365 ve üstü (365, HX 370, HX 375) işlemcili laptoplar

Not: Skroutz'un robots.txt'i özellikle "ClaudeBot" için ayrı bir bölüm
içeriyor - temiz kategori/ürün .html sayfalarına izin veriyor, sorgu
parametreli sayfalara (?...) izin vermiyor. Ben literal "ClaudeBot" kimliğiyle
gitmesem de gerçekten Claude olduğum için bu kurallara kendi politikam olarak
uyuyorum - sadece temiz .html kategori URL'leri kullanılıyor, arama sorgusu değil.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "core"))

from bs4 import BeautifulSoup

from scrapers._browser import fetch_multiple_rendered_html
from scrapers._price import parse_try

GPU_CATEGORY_URLS = [
    "https://www.skroutz.gr/c/25/laptop/f/2000033/GeForce-RTX-5070-Ti.html",
    "https://www.skroutz.gr/c/25/laptop/f/2000034/GeForce-RTX-5080.html",
    "https://www.skroutz.gr/c/25/laptop/f/2000035/GeForce-RTX-5090.html",
]
CPU_CATEGORY_URL = "https://www.skroutz.gr/c/25/laptop/f/1201076_1935033/AMD-Ryzen-9-Ryzen-AI-300-Series.html"

# "Ryzen AI 9 365" ve üstü (HX 370, HX 375 dahil) - Ryzen AI 300 serisinin en
# üst katmanı. Kategori filtresi "Ryzen AI 300-7 350" (AI7) ve "Ryzen AI
# 300-345" (AI5, "9" numarası yok) gibi daha düşük katmanları da döndürüyor -
# bu regex sadece AI9 katmanını (365/HX370/HX375) ayıklıyor.
_RYZEN_AI9_PATTERN = re.compile(r"ryzen ai (?:300-)?9\b", re.IGNORECASE)


def _parse_cards(html: str) -> list[dict]:
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


def search_by_gpu() -> list[dict]:
    requests_list = [(url, "li.card[data-skuid]") for url in GPU_CATEGORY_URLS]
    htmls = fetch_multiple_rendered_html(requests_list, timeout_ms=45000)

    seen_urls = set()
    results = []
    for url, html in zip(GPU_CATEGORY_URLS, htmls):
        if isinstance(html, Exception):
            print(f"  {url}: HATA - {html}", flush=True)
            continue
        found = _parse_cards(html)
        print(f"  {url}: {len(found)} urun", flush=True)
        for laptop in found:
            if laptop["url"] in seen_urls:
                continue
            seen_urls.add(laptop["url"])
            results.append(laptop)

    results.sort(key=lambda r: r["price_eur"])
    return results


def search_by_cpu() -> list[dict]:
    htmls = fetch_multiple_rendered_html([(CPU_CATEGORY_URL, "li.card[data-skuid]")], timeout_ms=45000)
    html = htmls[0]
    if isinstance(html, Exception):
        print(f"  {CPU_CATEGORY_URL}: HATA - {html}", flush=True)
        return []

    found = _parse_cards(html)
    results = [p for p in found if _RYZEN_AI9_PATTERN.search(p["name"])]
    print(f"  {CPU_CATEGORY_URL}: {len(found)} urun (filtre sonrasi {len(results)})", flush=True)

    results.sort(key=lambda r: r["price_eur"])
    return results


if __name__ == "__main__":
    print("=== GPU bazli (RTX 5070 Ti/5080/5090) ===")
    for laptop in search_by_gpu():
        print(f"{laptop['price_eur']:>10,.2f} EUR  {laptop['name'][:80]}")
        print(f"           {laptop['url']}")
    print()
    print("=== CPU bazli (Ryzen AI 9 365+) ===")
    for laptop in search_by_cpu():
        print(f"{laptop['price_eur']:>10,.2f} EUR  {laptop['name'][:80]}")
        print(f"           {laptop['url']}")
