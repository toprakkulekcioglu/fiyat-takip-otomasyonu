# Kullanılan API'ler, Siteler ve Servisler

Otomasyonun (her iki sistemin) veri çekmek veya bildirim göndermek için
kullandığı tüm dış kaynakların listesi - ne için kullanıldığı, nasıl
kimlik doğrulaması yapıldığı ve bilinen özellikleriyle.

## SSD / Harici Disk Sistemi (`core/`)

### Taranan siteler (veri kaynağı)

| Site | URL | Yöntem | Not |
|---|---|---|---|
| Amazon.com.tr | amazon.com.tr | Playwright | JS render + hafif bot koruması var, gerçek tarayıcı gerekiyor |
| Trendyol | trendyol.com | Playwright | Arama sayfası robots.txt'te yasak, sabit kategori sayfaları kullanılıyor |
| incehesap.com | incehesap.com | Playwright | Cloudflare'in otomatik JS doğrulaması var (CAPTCHA değil) |
| itopya.com | itopya.com | Düz `requests` | Sunucu tarafında render ediliyor, JS gerekmiyor |
| n11.com | n11.com | Düz `requests` | Sunucu tarafında render ediliyor |
| Pazarama | pazarama.com | Playwright | JS ile render ediliyor |
| ~~Hepsiburada~~ | hepsiburada.com | - | **Kullanılmıyor** - Akamai bot koruması CAPTCHA'ya yönlendiriyor, aşılmadı |

Hiçbiri API key/hesap gerektirmiyor - genel (public) sayfalar taranıyor,
robots.txt kurallarına uyularak.

### Bildirim servisleri

| Servis | Ne için | Kimlik doğrulama | Not |
|---|---|---|---|
| Gmail SMTP (`smtp.gmail.com:587`) | E-posta bildirimi | Uygulama Şifresi (App Password) - normal şifre değil | `SMTP_USER`, `SMTP_PASSWORD` secret'ları |
| [Telegram Bot API](https://core.telegram.org/bots/api) | Telegram bildirimi | Bot token (BotFather'dan) | Bot adı: `ssdfiyat_bot`. `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` |
| [CallMeBot](https://www.callmebot.com/) | WhatsApp bildirimi | API key (WhatsApp üzerinden bota mesaj atarak alınıyor) | Ücretsiz servis, zaman zaman yeni kayıtlara kapanabiliyor. `CALLMEBOT_PHONE`, `CALLMEBOT_APIKEY` |

### Altyapı

| Servis | Ne için |
|---|---|
| [GitHub](https://github.com) | Kod deposu (`toprakkulekcioglu/fiyat-takip-otomasyonu`), her 10 dakikada bir otomatik çalıştırma (GitHub Actions), hassas bilgi saklama (Secrets) |

---

## Laptop Fiyat Karşılaştırma Botu (`laptop-arama/`)

### Veri kaynakları

| Kaynak | URL | Yöntem | Not |
|---|---|---|---|
| Amazon.com.tr | amazon.com.tr | Playwright | Türkiye laptop fiyatları |
| n11.com | n11.com | Playwright | Türkiye laptop fiyatları - düz `requests` Render'ın IP'sinden 403 alıyordu, Playwright'a geçildi |
| [PriceRunner](https://www.pricerunner.com/) | pricerunner.com | Playwright | İngiltere merkezli, çoklu mağaza fiyat karşılaştırma sitesi - "yurtdışı/Avrupa" fiyat kaynağı |

### Yardımcı API'ler

| API | Ne için | Kimlik doğrulama | Not |
|---|---|---|---|
| [Frankfurter API](https://www.frankfurter.dev/) (`api.frankfurter.app`) | Güncel GBP→TL döviz kuru | Yok (ücretsiz, key gerektirmiyor) | Avrupa Merkez Bankası verisine dayanıyor |
| [Telegram Bot API](https://core.telegram.org/bots/api) | Anlık soru-cevap botu (webhook) | Bot token (BotFather'dan, `ssdfiyat_bot`'tan AYRI bir bot) | Bot kullanıcı adı için sana sorulmalı - `LAPTOP_TELEGRAM_BOT_TOKEN`, `LAPTOP_TELEGRAM_ALLOWED_CHAT_IDS` |

### Altyapı

| Servis | Ne için |
|---|---|
| [Render.com](https://render.com) | `webhook_app.py`'yi 7/24 çalışır tutan ücretsiz web servisi barındırma (URL: `fiyat-takip-otomasyonu.onrender.com`) |
| [Docker Hub / Microsoft Container Registry](https://mcr.microsoft.com/) (`mcr.microsoft.com/playwright/python`) | Render'daki deploy için kullanılan hazır Playwright+Chromium imajı |

---

## Ortak kütüphaneler (Python, `requirements.txt`)

| Kütüphane | Ne için |
|---|---|
| `requests` | Düz HTTP istekleri (itopya, n11 SSD taraması, API çağrıları) |
| `beautifulsoup4` | HTML ayrıştırma |
| `playwright` | Gerçek tarayıcı motoruyla (Chromium) sayfa render etme |
| `flask` | Laptop botunun webhook sunucusu |
| `gunicorn` | Flask'ı Render'da üretim seviyesinde çalıştıran sunucu |
