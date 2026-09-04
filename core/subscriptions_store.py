"""Kullanıcının web sayfasından (web/ssd-takip.html) takibe aldığı ürünlerin
listesi - `price_history.db`'den KASITLI olarak ayrı bir dosyada tutuluyor.

Neden ayrı: `price_history.db`'yi sadece GitHub Actions (CI) yazıp git'e geri
push ediyor. Bu dosyayı (subscriptions.json) ise sadece Render'daki canlı web
servisi (subscription_api.py) yazıp push ediyor. İkisi de aynı dosyaya paralel
yazıp push etseydi, biri diğerinin daha yeni verisini ezebilirdi (git commit
history'de "kaybolan" satırlar). Tek dosya = tek yazan kural, çakışma riski yok.

JSON seçildi, SQLite değil: bu liste kullanıcı başına birkaç, en fazla birkaç
düzine satır - sqlite3'ün sunduğu indeksli sorgu avantajına gerek yok, JSON
git diff'te okunabilir kalıyor.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_PATH = Path(__file__).resolve().parent.parent / "data" / "subscriptions.json"

# price_history.db'de aboneliğe ait fiyat kayıtları bu sabit "capacity"
# değeriyle işaretleniyor (check_and_notify.py bunu kullanıyor) - sabit
# 1tb/2tb/2tb-harici kategorileriyle karışmasın diye.
SUBSCRIPTION_CAPACITY = "abonelik"


def _load(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def _save(items: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")


def add_subscription(site: str, url: str, name: str, path: Path = DEFAULT_PATH) -> int:
    """Kullanıcının takibe aldığı bir ürünü kaydeder, yeni kaydın id'sini döner."""
    items = _load(path)
    next_id = max((item["id"] for item in items), default=0) + 1
    items.append({
        "id": next_id,
        "site": site,
        "url": url,
        "name": name,
        "active": True,
        "added_at": datetime.now(timezone.utc).isoformat(),
    })
    _save(items, path)
    return next_id


def get_active_subscriptions(path: Path = DEFAULT_PATH) -> list[dict]:
    return [item for item in _load(path) if item.get("active", True)]


def deactivate_subscription(subscription_id: int, path: Path = DEFAULT_PATH) -> bool:
    """Takibi bırakır (satırı silmez, sadece pasif işaretler). Bulunamadıysa False döner."""
    items = _load(path)
    found = False
    for item in items:
        if item["id"] == subscription_id and item.get("active", True):
            item["active"] = False
            found = True
    if found:
        _save(items, path)
    return found
