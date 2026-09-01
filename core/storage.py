"""Fiyat geçmişi deposu (SQLite).

JSON yerine SQLite seçildi: Adım 4'te her ürün için son 30-60 günlük fiyatların
medyanını hesaplamamız gerekiyor - bu, tarih aralığına göre filtrelenmiş bir sorgu.
SQLite bunu index'li bir WHERE ile yapar; JSON'da her seferinde tüm dosyayı okuyup
Python'da filtrelemek gerekirdi. Ekstra bağımlılık da yok, sqlite3 Python'da hazır.

Bir ürünün kimliği (site, url) ikilisi olarak kabul ediliyor - aynı ürünün fiyatı
zamanla değişse de URL'si sabit kalıyor.
"""
import sqlite3
from contextlib import closing
from datetime import datetime, timedelta, timezone
from pathlib import Path

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "price_history.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS price_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    site TEXT NOT NULL,
    capacity TEXT NOT NULL,
    name TEXT NOT NULL,
    url TEXT NOT NULL,
    price REAL NOT NULL,
    scraped_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_site_url ON price_history(site, url);
CREATE INDEX IF NOT EXISTS idx_scraped_at ON price_history(scraped_at);
"""


def _connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA)
    return conn


def save_snapshot(
    products: list[dict],
    db_path: Path = DEFAULT_DB_PATH,
    scraped_at: datetime | None = None,
) -> int:
    """Bir tarama turunda bulunan ürünleri geçmişe ekler. Her ürün sözlüğünde
    'capacity' alanı olmalı (scraper'lar bunu zaten ekliyor). Kaç satır
    eklendiğini döner."""
    scraped_at = scraped_at or datetime.now(timezone.utc)
    timestamp = scraped_at.isoformat()

    rows = [
        (p["site"], p["capacity"], p["name"], p["url"], p["price"], timestamp)
        for p in products
    ]
    with closing(_connect(db_path)) as conn:
        conn.executemany(
            "INSERT INTO price_history (site, capacity, name, url, price, scraped_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            rows,
        )
        conn.commit()
    return len(rows)


def get_price_history(
    site: str, url: str, days: int, db_path: Path = DEFAULT_DB_PATH
) -> list[tuple[str, float]]:
    """Bir ürünün son N gündeki (scraped_at, price) kayıtlarını eskiden yeniye döner."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    with closing(_connect(db_path)) as conn:
        cursor = conn.execute(
            "SELECT scraped_at, price FROM price_history "
            "WHERE site = ? AND url = ? AND scraped_at >= ? "
            "ORDER BY scraped_at ASC",
            (site, url, cutoff),
        )
        return cursor.fetchall()


def get_tracked_products(db_path: Path = DEFAULT_DB_PATH) -> list[tuple[str, str, str]]:
    """Geçmişte en az bir kaydı olan tüm (site, url, name) ürünlerini döner."""
    with closing(_connect(db_path)) as conn:
        cursor = conn.execute(
            "SELECT DISTINCT site, url, name FROM price_history ORDER BY site, name"
        )
        return cursor.fetchall()


def get_latest_price(site: str, url: str, db_path: Path = DEFAULT_DB_PATH) -> float | None:
    with closing(_connect(db_path)) as conn:
        cursor = conn.execute(
            "SELECT price FROM price_history WHERE site = ? AND url = ? "
            "ORDER BY scraped_at DESC LIMIT 1",
            (site, url),
        )
        row = cursor.fetchone()
        return row[0] if row else None
