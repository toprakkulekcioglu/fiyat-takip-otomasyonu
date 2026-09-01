"""Türkiye ve yurtdışı (İngiltere/PriceRunner) laptop listelerini aynı ürün
serisine göre eşleştirir.

Yöntem: marka (ilk kelime, örn. "MSI") ve bilinen ürün serisi adı (Stealth,
Vector, Legion, ROG Strix gibi) her iki isimde de aynıysa eşleşme kabul edilir.
Ayrıca bir model kodu (5+ karakterli, harf+rakam karışık token, örn. "A2XWHG")
her iki isimde de bulunup örtüşüyorsa bu "kesin" (high) güven seviyesi olarak
işaretlenir - bulunamazsa "yaklaşık" (approx) olarak işaretlenir.

Neden sadece marka+seri yeterli görülüyor: testte aynı seri (MSI Vector) için
TR ilanında işlemci kodu ("255HX"), UK ilanında şasi kodu ("A2XWHG") gibi FARKLI
TÜRDE kodlar geçtiği için kod eşleştirmesi tek başına gerçek eşleşmeleri
kaçırıyordu. Ama marka+seri TEK BAŞINA da riskli - aynı seri farklı ekran boyutu/
yapılandırmada olabilir. Bu yüzden sonuçlar "yaklaşık" etiketiyle gösterilmeli,
kesin sanılmamalı.
"""
import re

_CODE_PATTERN = re.compile(r"\b(?=[A-Z0-9]{5,}\b)(?=[A-Z0-9]*[A-Z])(?=[A-Z0-9]*[0-9])[A-Z0-9]{5,}\b")

_KNOWN_SERIES = (
    "stealth", "vector", "raider", "titan", "katana", "sword", "cyborg",  # MSI
    "strix", "zephyrus", "tuf", "scar", "flow",  # ASUS
    "legion", "loq",  # Lenovo
    "omen", "victus",  # HP
    "nitro", "predator", "helios", "triton",  # Acer
    "blade",  # Razer
    "alienware",  # Dell
)

# Model kodu sanılmaması gereken, ürün adında sık geçen teknik token'lar
# (CPU/GPU model numaraları, RAM/SSD boyutları, panel çözünürlüğü vb.)
_CODE_IGNORE_SUBSTRINGS = ("5070", "5080", "5090", "RTX", "HX", "GB", "TB", "HZ", "FHD", "WUXGA", "WQXGA")


def _brand(name: str) -> str:
    return name.strip().split()[0].lower() if name.strip() else ""


def _series(name: str) -> str | None:
    lowered = name.lower()
    for series in _KNOWN_SERIES:
        if series in lowered:
            return series
    return None


def _model_codes(name: str) -> set[str]:
    upper = name.upper()
    codes = set()
    for m in _CODE_PATTERN.finditer(upper):
        code = m.group(0)
        if any(ignore in code for ignore in _CODE_IGNORE_SUBSTRINGS):
            continue
        codes.add(code)
    return codes


def _codes_overlap(a_codes: set[str], b_codes: set[str]) -> bool:
    return any(
        a == b or a.startswith(b) or b.startswith(a)
        for a in a_codes for b in b_codes
        if len(a) >= 5 and len(b) >= 5
    )


def match(tr_laptops: list[dict], global_laptops: list[dict]) -> list[dict]:
    """Her eşleşen çift için {'tr': ..., 'global': ..., 'confidence': 'high'|'approx'} döner."""
    pairs = []
    used_global = set()

    for tr in tr_laptops:
        tr_brand = _brand(tr["name"])
        tr_series = _series(tr["name"])
        if not tr_series:
            continue
        tr_codes = _model_codes(tr["name"])

        for idx, glb in enumerate(global_laptops):
            if idx in used_global:
                continue
            if _brand(glb["name"]) != tr_brand or _series(glb["name"]) != tr_series:
                continue

            glb_codes = _model_codes(glb["name"])
            confidence = "high" if _codes_overlap(tr_codes, glb_codes) else "approx"

            pairs.append({"tr": tr, "global": glb, "confidence": confidence})
            used_global.add(idx)
            break

    return pairs
