# Dosya Yapısı

Bu depodaki her dosyanın/klasörün ne işe yaradığının tam dökümü.

## `core/` — Otomasyonun çalışan kodu

Bu klasördeki dosyalar birbirine sıkı bağlı, tek başlarına anlamsız - hepsi
birlikte, `check_and_notify.py`'nin çağırdığı tek bir zincir oluşturuyor.

| Dosya | Ne işe yarar |
|---|---|
| `check_and_notify.py` | **Ana giriş noktası.** GitHub Actions'ın çalıştırdığı tek script. Sırasıyla: her siteyi tarar → her ürünün geçmişini okur → medyanla karşılaştırır → gerçek indirimse bildirim gönderir → bugünün fiyatını geçmişe kaydeder. |
| `storage.py` | Fiyat geçmişi deposu. SQLite veritabanına (`data/price_history.db`) fiyat kaydeder, tarih aralığına göre geçmiş okur. Bir ürün `(site, url)` ikilisiyle tanımlanıyor. |
| `discount_detector.py` | Sahte indirim tespit mantığı. Güncel fiyatı, son 45 günün **medyan** fiyatıyla karşılaştırır (ortalama değil - kısa süreli yapay zamdan etkilenmemesi için). %25+ ucuzsa "gerçek indirim" der. |
| `notifier.py` | Bildirim gönderme. E-posta (SMTP/Gmail), Telegram Bot API, WhatsApp (CallMeBot) - üçü de bağımsız, biri eksikse sessizce atlanır. Ayrıca `.env` dosyasını okuyan `load_dotenv()` fonksiyonu burada. |
| `scrapers/__init__.py` | Boş dosya - `scrapers` klasörünü bir Python paketi yapmak için gerekli (içeriği yok, sadece varlığı önemli). |
| `scrapers/_browser.py` | Ortak yardımcı: Playwright ile headless Chromium açıp bir sayfayı gerçek tarayıcı gibi render eden `fetch_rendered_html()` fonksiyonu. JS ile veri yükleyen siteler (Amazon, Trendyol, incehesap, Pazarama) bunu kullanıyor. |
| `scrapers/_price.py` | Ortak yardımcı: Türkçe fiyat metinlerini (`"16.396,49 TL"` gibi) sayıya çeviren `parse_try()`, ve alakasız/aksesuar ürünleri elemek için kullanılan `MIN_PLAUSIBLE_PRICE` eşiği. |
| `scrapers/amazon.py` | Amazon.com.tr scraper'ı (Playwright kullanıyor). |
| `scrapers/trendyol.py` | Trendyol scraper'ı (Playwright kullanıyor, arama değil sabit kategori sayfası üzerinden - robots.txt arama sayfasını yasaklıyor). |
| `scrapers/incehesap.py` | incehesap.com scraper'ı (Playwright kullanıyor - Cloudflare'in otomatik JS doğrulamasını geçmek için). |
| `scrapers/itopya.py` | itopya.com scraper'ı (düz `requests` yeterli - sunucu tarafında render ediliyor, JS gerekmiyor). |
| `scrapers/n11.py` | n11.com scraper'ı (düz `requests` yeterli). |
| `scrapers/pazarama.py` | Pazarama scraper'ı (Playwright kullanıyor). Kapasiteye özel bir kategori URL'si olmadığı için genel SSD kategorisi çekilip ürün adına göre 1TB/2TB filtreleniyor. |
| `scrapers/hepsiburada.py` | **Kullanılmıyor.** Hepsiburada'nın Akamai bot koruması, otomatik isteklerde CAPTCHA sayfasına yönlendiriyor. Kod referans olarak duruyor, `check_and_notify.py` bunu çağırmıyor. |

## `data/` — Biriken veri

| Dosya | Ne işe yarar |
|---|---|
| `price_history.db` | Her taramada bulunan fiyatların biriktiği SQLite veritabanı. GitHub Actions her çalıştırmanın sonunda bu dosyayı güncelleyip repoya geri commit'liyor - böylece geçmiş, çalıştırmalar arasında kaybolmuyor. |

## `scripts/` — Manuel test/demo araçları

Bunlar otomasyonun bir parçası değil, geliştirme sırasında elle çalıştırılıp
doğrulama yapmak için yazıldı. GitHub Actions bunları hiç çağırmıyor.

| Dosya | Ne işe yarar |
|---|---|
| `test_scrapers.py` | Her scraper'ı tek tek çalıştırıp gerçek veri çektiğini terminalde gösterir. |
| `test_notify.py` | Uydurma bir ürün/indirim bilgisiyle e-posta+Telegram+WhatsApp gönderimini test eder - gerçek tarama yapmaz. |
| `demo_storage.py` | `storage.py`'nin, zaman içinde biriken geçmişle nasıl davrandığını 45 günlük simüle veriyle gösterir. Ayrı bir demo veritabanı kullanır, gerçek `price_history.db`'ye dokunmaz. |

## `docs/` — Yazılı notlar

| Dosya | Ne işe yarar |
|---|---|
| `sorunlar-ve-cozumler.md` | Geliştirme sürecinde karşılaşılan tüm engeller (bot korumaları, robots.txt kısıtları, kurulum hataları vb.) ve nasıl çözüldükleri. |
| `ogrenilenler.md` | Proje boyunca sorulan sorulardan çıkan terimlerin/kavramların (robots.txt, medyan vs ortalama, App Password, GitHub Actions vb.) kısa açıklamaları. |
| `dosya-yapisi.md` | Bu dosyanın kendisi. |

## Kök dizin

| Dosya | Ne işe yarar |
|---|---|
| `README.md` | Projenin genel tanıtımı, kurulum ve çalışma mantığı özeti. |
| `requirements.txt` | Python bağımlılıkları (`requests`, `beautifulsoup4`, `playwright`). |
| `.env.example` | Hangi ortam değişkenlerinin gerektiğinin şablonu (gerçek değerler değil). |
| `.env` | Gerçek şifre/API key'lerin durduğu dosya - **git'e girmez** (`.gitignore`'da). |
| `.gitignore` | git'in takip etmemesi gereken dosyalar (`.env`, `venv/`, `__pycache__/`). |
| `.github/workflows/price-check.yml` | GitHub Actions zamanlama tanımı - her 10 dakikada bir `core/check_and_notify.py`'yi çalıştırır, sonra güncellenen veritabanını repoya geri commit'ler. |
