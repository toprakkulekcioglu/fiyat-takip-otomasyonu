"""Selanik'te (Yunanistan) mağazaları olan büyük teknoloji zincirlerinin laptop
fiyatlarını Skroutz.gr üzerinden (Yunanistan'ın ana fiyat karşılaştırma sitesi -
Public, Kotsovolos, Plaisio gibi büyük zincirleri tek yerde topluyor) çeker.
Otomasyonun (core/) parçası değil, sadece bot tetiklemesiyle çalışır.

İki ayrı arama sunuyor:
- search_by_gpu(): RTX 5070 Ti / 5080 / 5090 (12GB+ VRAM) ekran kartlı, Zephyrus
  serisi (G14/G16) laptoplar
- search_by_cpu(): Ryzen AI 9 365 ve üstü (365, HX 370, HX 375), en az 32GB RAM
  ve en az 1TB SSD'li laptoplar

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
_ZEPHYRUS_PATTERN = re.compile(r"zephyrus", re.IGNORECASE)

# Skroutz ürün adında geçen "GB"/"TB" birimli sayılar hep aynı sırada: önce RAM,
# hemen ardından depolama (kategoriye göre "32GB/1TB SSD/..." ya da kısaltılmış
# "32GB/1TB)" hâlinde olabiliyor - ikisi de aynı iki sayı sırasını izliyor, bu
# yüzden sabit bir "/../ SSD" kalıbı yerine ilk iki GB/TB sayısını alıyoruz.
_SIZE_TOKEN_PATTERN = re.compile(r"(\d+(?:[.,]\d+)?)\s*(GB|TB)", re.IGNORECASE)

# search_by_cpu() "taşınabilir/hafif" bir ultrabook arıyor - ama Ryzen AI 9 CPU
# kategorisi hem ultrabook'ları hem oyun laptoplarını (ki ağır ve büyük olur)
# birlikte listeliyor, kart başlıklarında da "gaming" gibi bir alan yok. Bilinen
# oyun laptop serisi isimlerini eleyerek ayırıyoruz.
_GAMING_LINE_KEYWORDS = (
    "nitro", "predator", "stealth", "raider", "vector", "titan", "katana",
    "legion", "omen", "rog ", "helios", "sword", "crosshair",
)


def _is_gaming_laptop(name: str) -> bool:
    lowered = name.lower()
    return any(keyword in lowered for keyword in _GAMING_LINE_KEYWORDS)


def _meets_min_specs(name: str, min_ram_gb: int, min_storage_gb: int) -> bool:
    tokens = _SIZE_TOKEN_PATTERN.findall(name)
    if len(tokens) < 2:
        return False
    ram_value, ram_unit = tokens[0]
    storage_value, storage_unit = tokens[1]
    ram_gb = float(ram_value.replace(",", ".")) * (1000 if ram_unit.upper() == "TB" else 1)
    storage_gb = float(storage_value.replace(",", ".")) * (1000 if storage_unit.upper() == "TB" else 1)
    return ram_gb >= min_ram_gb and storage_gb >= min_storage_gb


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
        found = [p for p in _parse_cards(html) if _ZEPHYRUS_PATTERN.search(p["name"])]
        print(f"  {url}: {len(found)} Zephyrus urunu", flush=True)
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
    results = [
        p for p in found
        if _RYZEN_AI9_PATTERN.search(p["name"])
        and _meets_min_specs(p["name"], min_ram_gb=32, min_storage_gb=1000)
        and not _is_gaming_laptop(p["name"])
    ]
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
