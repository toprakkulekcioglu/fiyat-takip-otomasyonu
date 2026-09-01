"""Türk Lirası fiyat metinlerini (örn. '16.396,49 TL', '8.399 TL') float'a çevirir."""
import re

# 1TB/2TB SSD'lerin gerçekçi olarak bu fiyatın altına inmeyeceği varsayımıyla, kategori/arama
# sayfalarına sızan alakasız ürünleri (aksesuar, disk kutusu vb.) elemek için kullanılıyor.
MIN_PLAUSIBLE_PRICE = 2000.0


def is_nvme(name: str) -> bool:
    """1TB kategorisi sadece NVMe disklerle sınırlı tutuluyor - SATA hariç."""
    return "nvme" in name.lower()


def is_ssd(name: str) -> bool:
    """Harici disk kategorileri hem SSD hem HDD karışık listeleyebiliyor - HDD'leri elemek için."""
    return "ssd" in name.lower()


# Arama sonuçlarına/kategorilere sızan, disk OLMAYAN ama "NVMe"/"SSD" geçen ürünler
# (muhafaza, disk istasyonu, adaptör vb.) - bunlar disk değil aksesuar.
_ACCESSORY_KEYWORDS = (
    "muhafaza", "disk istasyon", "istasyonu", "aparat", "adaptör", "adapter",
    "çevirici", "converter", "kutu", "case", "enclosure", "dock", "hub",
    "kablo", "cable", "yuva", "klon", "kopyalama", "bracket",
)


def is_accessory(name: str) -> bool:
    lowered = name.lower()
    return any(keyword in lowered for keyword in _ACCESSORY_KEYWORDS)


_CAPACITY_PATTERNS = {
    "1tb": re.compile(r"\b1\s*[.,]?\s*tb\b|\b1000\s*gb\b|\b1024\s*gb\b", re.IGNORECASE),
    "2tb": re.compile(r"\b2\s*[.,]?\s*tb\b|\b2000\s*gb\b|\b2048\s*gb\b", re.IGNORECASE),
    "2tb-harici": re.compile(r"\b2\s*[.,]?\s*tb\b|\b2000\s*gb\b|\b2048\s*gb\b", re.IGNORECASE),
}


def matches_capacity(name: str, capacity: str) -> bool:
    """Ürün adında gerçekten beklenen kapasite geçiyor mu - sadece arama sorgusunun
    alaka düzeyine güvenmemek için (örn. '1tb ssd' araması bazen 500GB ürün de döndürebiliyor)."""
    pattern = _CAPACITY_PATTERNS.get(capacity)
    return pattern.search(name) is not None if pattern else True


_EXTERNAL_KEYWORDS = ("taşınabilir", "harici", "portable", "external")


def is_external(name: str) -> bool:
    lowered = name.lower()
    return any(keyword in lowered for keyword in _EXTERNAL_KEYWORDS)


def parse_try(text: str) -> float | None:
    if not text:
        return None
    match = re.search(r"[\d.,]+", text)
    if not match:
        return None
    number = match.group(0).strip(".,")
    if "," in number:
        number = number.replace(".", "").replace(",", ".")
    else:
        number = number.replace(".", "")
    try:
        return float(number)
    except ValueError:
        return None
