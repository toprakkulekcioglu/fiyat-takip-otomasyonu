"""notifier.py'yi gerçek bir e-posta + WhatsApp mesajıyla test etmek için.

Çalıştırmadan önce .env dosyasını doldurmuş olman lazım (bkz. .env.example).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from discount_detector import DiscountCheck
from notifier import load_dotenv, notify_discount

load_dotenv()

fake_product = {
    "name": "Kingston NV3 1TB Test SSD",
    "site": "TestSite",
    "url": "https://example.com/test-urun",
}
fake_check = DiscountCheck(
    is_genuine_discount=True,
    current_price=5800.0,
    reference_median=8000.0,
    discount_pct=0.275,
    reason="Test bildirimi",
)

if __name__ == "__main__":
    print("Test bildirimi gönderiliyor...")
    notify_discount(fake_product, fake_check)
    print("Gönderildi. E-posta ve Telegram'ı kontrol et (WhatsApp key yoksa atlanır).")
