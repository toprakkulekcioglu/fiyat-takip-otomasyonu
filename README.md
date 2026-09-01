# Fiyat Takip Otomasyonu

Türkiye'deki 6 e-ticaret sitesinden (Amazon.com.tr, Trendyol, incehesap, itopya,
n11, Pazarama) 1TB/2TB SSD fiyatlarını GitHub Actions ile her 10 dakikada bir
otomatik tarayan, bir ürün **gerçekten** ucuzladığında (önce yapay zam yapıp sonra
"indirim" gösterme numarasını eleyerek) e-posta, Telegram ve WhatsApp ile haber
veren bir sistem.

## Nasıl çalışır

```
check_and_notify.py  (GitHub Actions her 10 dakikada bir bunu çalıştırır)
  ├─ scrapers/*.py        → her siteden güncel fiyatları çeker
  ├─ storage.py           → fiyatları SQLite'a kaydeder, geçmişi okur
  ├─ discount_detector.py → güncel fiyatı son 45 günün MEDYANIYLA karşılaştırır
  └─ notifier.py          → gerçek bir indirimse e-posta/Telegram/WhatsApp gönderir
```

Neden medyan, ortalama değil: bir satıcı "indirimden" hemen önce fiyatı yapay olarak
yükseltirse, bu ortalamayı belirgin şekilde yukarı çeker ama medyanı çok daha az
etkiler. Detaylı açıklama ve test senaryoları için [docs/ogrenilenler.md](docs/ogrenilenler.md).

## Klasör yapısı

| Yol | İçerik |
|---|---|
| `check_and_notify.py` | Ana script - GitHub Actions'ın çalıştırdığı tek giriş noktası |
| `storage.py` | Fiyat geçmişi deposu (SQLite) |
| `discount_detector.py` | Sahte indirim tespiti (medyan karşılaştırma) |
| `notifier.py` | E-posta (SMTP) + Telegram + WhatsApp (CallMeBot) bildirimleri |
| `scrapers/` | Her site için ayrı scraper modülü |
| `data/price_history.db` | Biriken fiyat geçmişi (GitHub Actions her çalıştırmada geri commit'ler) |
| `scripts/` | Manuel test/demo scriptleri - otomasyonun parçası değil |
| `docs/` | Geliştirme sürecinde çıkan sorunlar, çözümler ve terimler |
| `.github/workflows/price-check.yml` | Zamanlama (cron) tanımı |

## Kurulum (yerelde çalıştırmak istersen)

```bash
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
playwright install chromium
cp .env.example .env           # doldur: SMTP, Telegram, CallMeBot bilgileri
python check_and_notify.py
```

## Otomasyon

`.github/workflows/price-check.yml`, GitHub'ın kendi sunucularında her 10 dakikada
bir `check_and_notify.py`'yi çalıştırır - yerel bilgisayarın açık olmasına gerek
yoktur. Gerekli SMTP/Telegram/CallMeBot bilgileri repo Settings → Secrets and
variables → Actions altında tanımlıdır, koda gömülü değildir.

## Kapsam dışı bırakılan: Hepsiburada

Hepsiburada, otomatik/tekrarlanan isteklerde Akamai bot korumasının CAPTCHA
sayfasına yönlendiriyor. CAPTCHA çözme veya parmak izi sahteciliği gibi bir bypass
yapılmadığı için bu site listeye dahil edilmedi (`scrapers/hepsiburada.py` referans
olarak duruyor ama kullanılmıyor). Detay: [docs/sorunlar-ve-cozumler.md](docs/sorunlar-ve-cozumler.md).
