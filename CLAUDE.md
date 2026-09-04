# CLAUDE.md

Bu depo iki bağımsız sistem içeriyor. Detaylı geçmiş için `docs/yapilanlar.md`
(baştan sona anlatım), `docs/sorunlar-ve-cozumler.md` (karşılaşılan engeller ve
çözümleri), `docs/ogrenilenler.md` (terim/kavram sözlüğü), `docs/dosya-yapisi.md`
(dosya haritası) - bu dosya sadece hızlı bağlam kazanmak için özet.

## Sistem 1: SSD/Harici Disk Fiyat Takibi (`core/`, tam otomatik)

**Ne yapıyor:** 6 Türkiye e-ticaret sitesini (Amazon.com.tr, Trendyol,
incehesap, itopya, n11, Pazarama) GitHub Actions ile her 10 dakikada bir
tarar, bir ürün son 45 günün medyanına göre gerçekten (%25+) ucuzladıysa
veya sabit bir hedef fiyata düştüyse e-posta + Telegram + WhatsApp ile
bildirim gönderir.

**Giriş noktası:** `core/check_and_notify.py` - GitHub Actions
(`.github/workflows/price-check.yml`) bunu çalıştırır.

**Akış:** `core/scrapers/*.py` (tara) → filtrele (kapasite doğru mu, aksesuar
mı, hariç tutulmuş mu - `core/excluded_products.py`) → `core/storage.py`'den
geçmişi oku → `core/discount_detector.py` ile medyan/hedef fiyat karşılaştır
→ gerçekse `core/notifier.py` ile bildir → `core/storage.py`'ye bugünün
fiyatını kaydet.

**Kategoriler:** `1tb` (NVMe şart, 6500 TL hedef), `2tb` (NVMe şart, 12000 TL
hedef), `2tb-harici` (taşınabilir SSD, 5000 TL hedef). Hepsiburada CAPTCHA
duvarına takıldığı için kapsam dışı (`core/scrapers/hepsiburada.py` referans
olarak duruyor, kullanılmıyor).

**Önemli kurallar:**
- Site engelleriyle karşılaşınca (CAPTCHA, bot koruması) ASLA bypass/aşma
  yöntemi denenmedi - o site listeden çıkarıldı. Bu prensip korunmalı.
- Fiyat için MEDYAN kullanılıyor, ORTALAMA değil (yapay zam-sahte indirim
  numarasına karşı dayanıklı olsun diye).
- Yanlış eşleşmeleri önlemek için sürekli yeni filtreler eklendi
  (`matches_capacity`, `is_accessory`, `is_external`, `is_nvme`, `is_ssd` -
  hepsi `core/scrapers/_price.py`'de). Yeni bir yanlış eşleşme fark edilirse
  aynı dosyaya benzer bir filtre eklenmeli.
- Hatalı/yanıltıcı tek bir ürün fark edilirse `core/excluded_products.py`'ye
  URL'sini ekle - kod değiştirmeye gerek yok.
- Hassas bilgiler (SMTP şifresi, API key'ler) hiçbir zaman koda yazılmaz -
  GitHub Secrets kullanılır, yerelde test için `.env` (git'e girmez).
- Repo **public** - GitHub Actions'ın ücretsiz dakika kotası private
  repolarda sınırlı, 10 dakikalık bir cron için yetmiyordu.

**Genişletme - kullanıcı bazlı ürün takibi (`web/ssd-takip.html`):** Sabit 3
kategorinin ÖTESİNDE, kullanıcı 6 desteklenen siteden herhangi bir ürün
linkini web sayfasından yapıştırıp takibe alabiliyor (`core/subscription_api.py`,
Flask Blueprint, `laptop-arama/webhook_app.py`'nin Render servisine ekleniyor).
Her sitede kategori kartlarından farklı bir `scrape_product(url)` fonksiyonu
var (site bazlı detaylar için `docs/yapilanlar.md` → "Sistem 1 Genişletmesi").
Abonelikler `data/price_history.db`'den KASITLI ayrı bir dosyada
(`data/subscriptions.json`, `core/subscriptions_store.py`) - o dosyayı sadece
CI, bunu sadece Render yazıyor, çakışma riski yok. Render'ın bu dosyayı git'e
geri yazması için `core/git_sync.py` (GitHub REST Contents API, `GITHUB_PAT`
ortam değişkeni Render'da tanımlı olmalı - tanımlı değilse özellik web
sayfasında çalışır ama eklenen ürünler CI'nin periyodik taramasına yansımaz).

## Sistem 2: Laptop Arama Botu (`laptop-arama/`, isteğe bağlı)

**Şu an AKTİF olan:** Selanik (Yunanistan) laptop araması, `search_laptops_greece.py`
üzerinden Skroutz.gr'de. İki ayrı sorgu var, `webhook_app.py`'de mesaj
içeriğine göre dallanıyor:
- Mesajda **"ryzen"** geçiyorsa → `search_by_cpu()` - Ryzen AI 9 365+ işlemcili laptoplar
- Mesajda **"teşekkür"** geçiyorsa → `search_by_gpu()` - RTX 5070 Ti/5080/5090 laptoplar
- Başka bir şey yazılırsa → kısa bir yönlendirme mesajı, arama yapılmaz

Sonuç formatı: mani + her laptop için ad, EUR fiyatı, güncel kurla TL
karşılığı, link. TR ile karşılaştırma YOK - sadece Selanik fiyatlarının
düz listesi.

**Devre dışı (kod duruyor ama bota bağlı değil):** Eski Türkiye vs.
İngiltere (PriceRunner) karşılaştırma sistemi - `search_laptops.py`,
`search_laptops_tr.py`, `matcher.py`. Kullanıcı "eskisi dursun ama aktif
olmasın, istediğimizde devreye alırız" dedi - silinmedi, sadece
`webhook_app.py` artık bunları çağırmıyor. Geri almak istenirse
`webhook_app.py`'ye bu üçünü tekrar import edip bir üçüncü anahtar kelimeye
bağlamak yeterli.

**Neden ayrı klasör:** Kullanıcı isteği - iki sistem (SSD/harici disk ve
laptop) birbirinden bağımsız olsun, biri kapatılırsa/silinirse diğeri
etkilenmesin.

**Mimari:** Telegram → webhook (anlık, POST isteği) → `laptop-arama/
webhook_app.py` (Flask, Render.com'da 7/24 çalışıyor) → arka planda
`search_laptops_greece.py` çalışır → `currency.py` ile güncel EUR→TL kuru
çekilir → `manis.py`'den rastgele bir mani eklenir → sonuç Telegram'a
gönderilir (4096 karakteri aşan sonuçlar `send_long_message` ile bölünüp
gönderiliyor).

**Neden webhook, polling değil:** İlk kurulan sistem GitHub Actions ile
5 dakikada bir "yeni mesaj var mı" diye soruyordu (polling) - ama GitHub'ın
kendi zamanlayıcısı bu sıklıkta güvenilir çalışmadı (bazen saatlerce hiç
tetiklenmedi). Kullanıcı "anlık" cevap istediği için webhook mimarisine
geçildi - bunun için 7/24 açık bir sunucu (Render.com, ücretsiz katman)
gerekiyor. **Telegram bir bota aynı anda hem webhook hem polling
kullandırmıyor** - biri seçilince diğeri tamamen kapatılmalı.

**Deploy detayı:** Render'ın ücretsiz build ortamı `playwright install
--with-deps` için root yetkisi vermiyor (`su: Authentication failure`
hatası). Çözüm: `laptop-arama/Dockerfile`, Playwright'ın resmi Docker
imajını (`mcr.microsoft.com/playwright/python`) kullanıyor - Chromium'un
ihtiyaç duyduğu sistem kütüphaneleri zaten kurulu geliyor. Render'da
Environment/Language **Docker** olarak seçilmeli (Render dashboard'u
mevcut bir servisin runtime'ını sonradan değiştirmeyi desteklemiyor -
yanlış seçilirse servisi silip yeniden oluşturmak gerekiyor).

**Skroutz.gr ve ClaudeBot:** Skroutz'un robots.txt'inde özellikle ClaudeBot
için bir bölüm var - temiz `/c/*.html` kategori sayfalarına izin veriyor,
sorgu parametreli (`?...`) sayfalara vermiyor. Gerçekten Claude olduğumuz
için bu kurallara (literal "ClaudeBot" User-Agent'ı göndermesek de) kendi
politikamız olarak uyuyoruz - `search_laptops_greece.py`'deki tüm URL'ler
temiz `.html` kategori sayfaları, arama sorgusu değil.

**(Devre dışı sistemdeki) eşleştirme mantığı (`matcher.py`):** Marka +
bilinen ürün serisi adı (Stealth/Vector/Legion/ROG Strix vb.) aynıysa
eşleşme kabul edilir; model kodu da (örn. "A2XWHG") örtüşüyorsa "kesin",
örtüşmüyorsa "yaklaşık" olarak etiketlenir. Sadece model koduna güvenmek
YANLIŞ eşleşmeler üretmişti (farklı seri, tesadüfen aynı kod parçası) - bu
yüzden marka+seri şartı eklendi. Aktif Selanik sisteminde eşleştirme YOK,
sadece düz listeleme var.

**Bilinen sınırlamalar / geçmişte çözülen Render sorunları:**
- Amazon.com.tr ve n11 arama sonuçları istekten isteğe değişkenlik
  gösterebiliyor (reklam/sıralama rotasyonu).
- Render'ın ücretsiz katmanı 15 dakika hareketsizlikten sonra uykuya geçiyor
  - ilk mesajda ~30-50 saniyelik "uyanma" gecikmesi olabilir.
- **512MB RAM sınırında OOM (bellek yetersizliği) çöküşü yaşandı** - art
  arda 5 ayrı Chromium açıp kapatmak süreci çökertiyordu (loglarda uzun
  sessizlik + otomatik yeniden başlama görülür). Çözüm:
  `core/scrapers/_browser.py`'deki `fetch_multiple_rendered_html()` TEK
  Chromium'u paylaşarak birden fazla sayfa açıyor, ayrıca
  `--disable-dev-shm-usage` gibi konteyner-dostu launch bayrakları eklendi.
  Yeni bir çoklu-sayfa taraması eklenecekse bu fonksiyonu kullan, her sayfa
  için ayrı `fetch_rendered_html()` çağırma.
- **Telegram'ın 4096 karakter/mesaj sınırı** aşılınca mesaj sessizce
  kayboluyordu (Telegram reddediyor, `requests.post()` HTTP açısından
  başarılı görünüyordu). Çözüm: `send_message()` artık Telegram'ın JSON
  cevabındaki `ok` alanını kontrol ediyor, `send_long_message()` uzun
  sonuçları ürün bloklarını bölmeden parçalara ayırıyor. Yeni bir mesaj
  gönderme noktası eklenirse `send_message` yerine `send_long_message`
  kullan (veya en azından `ok` kontrolü yap).

## Genel kod kuralları (her iki sistem için)

- Kod içi yorumlar **Türkçe**, değişken/fonksiyon isimleri **İngilizce**.
- Değişiklik yaptıktan sonra gerçek veriyle test et (mock değil) - hem yerelde
  hem mümkünse gerçek ortamda (GitHub Actions / Render) doğrula.
- Basitlik önce: gereksiz soyutlama, kullanılmayan esneklik ekleme. Ölü kod
  fark edilirse (örn. `collect_prices.py` silindiği gibi) kaldır.
- Git commit'lerinde Türkçe/İngilizce karışık mesaj kullanılıyor, sorun değil.
- `data/price_history.db` her GitHub Actions çalıştırmasında otomatik commit
  leniyor - yerelde çalışırken `git pull` yapmadan push etmeye çalışırsan
  çakışma alırsın, önce pull et.
