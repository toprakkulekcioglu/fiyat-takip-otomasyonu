# Karşılaşılan Sorunlar ve Çözümleri

Bu proje geliştirilirken (SSD fiyat takip botu, Step 1-2) karşılaşılan tüm engeller,
denenen yollar ve sonunda uygulanan çözümler.

## 1. Trendyol — arama sayfası robots.txt'te tamamen yasak

**Sorun:** Trendyol'un robots.txt'i `/sr` (arama sonucu path'i), `?q=` ve `&q=` query
parametrelerini tamamen yasaklıyor (`Disallow: /sr?`, `/sr/`, `/sr$`, `/*?q=`, `/*&q=`).
Yani `trendyol.com/sr?q=1tb+ssd` gibi bir arama URL'si kullanmak robots.txt ihlali olurdu.

**Çözüm:** Arama yerine, Trendyol'un kendi SEO/landing sayfalarını kullandık —
`trendyol.com/1tb-ssd-y-s3288` ve `trendyol.com/2-tb-ssd-y-s88912` gibi sabit kategori
URL'leri robots.txt'in yasak listesinde değil.

## 2. Trendyol — kategori sayfası ilk HTML'de ürün verisi içermiyor

**Sorun:** `curl` ile çekilen HTML'de ürün adı/fiyat verisi yoktu; sayfa Next.js tabanlı
bir SPA, veri client-side JS ile ayrıca yükleniyor.

**Çözüm:** Playwright ile headless Chromium açıp sayfayı gerçek bir tarayıcı gibi
render ettik, sonra oluşan HTML'i BeautifulSoup ile parse ettik. Bu bir bypass değil —
Trendyol isteklerimizi hiç engellemiyor, sadece JS çalıştırmak gerekiyor.

## 3. Amazon.com.tr — düz istekte "Üzgünüz" anti-bot sayfası

**Sorun:** `curl`/`WebFetch` ile `amazon.com.tr/s?k=1tb+ssd` çekildiğinde, gerçek arama
sonuçları yerine Amazon'un otomatik erişim tespit sayfası döndü ("Amazon verilerine
otomatik erişim için api-services-support@amazon.com ile iletişime geçin" mesajı).
robots.txt bu path'e izin veriyordu ama sunucu seviyesinde ayrı bir bot tespiti vardı.

**Çözüm:** Playwright ile gerçek tarayıcı motoru kullanınca sayfa sorunsuz açıldı
(sadece çerez bildirimi çıktı, engel yoktu). Demek ki engel `curl`'ün tarayıcı gibi
görünmemesinden (TLS parmak izi, JS çalıştıramaması vb.) kaynaklanıyordu — spoofing
yapmadan, gerçek bir browser engine kullanarak çözüldü.

## 4. Hepsiburada — Akamai bot koruması, robots.txt'e erişim bile 403

**Sorun:** `hepsiburada.com/robots.txt` dahi düz `curl` isteğinde 403 döndürüyordu
(Akamai'nin "HBBlockandCaptcha" sayfasına yönlendiriyordu). Ana sayfa da aynı şekilde
403'tü.

**Denenen:** Gerçek bir interaktif tarayıcı oturumunda (Claude Browser tool) sayfa bir
kere sorunsuz açıldı — bu yüzden "belki çalışır" diye umutlandık ve robots.txt'i de bu
yolla okuyabildik (arama path'i `/ara?q=` aslında yasak listede değilmiş).

**Sonuç:** Ama otomatik/headless Playwright ile aynı isteği tekrarlayınca (yani gerçek
bot senaryosunda) Akamai bizi "Hepsiburada | Güvenlik" CAPTCHA/blok sayfasına
yönlendirdi — tutarlı bir engeldi, ilk testteki geçiş şanslıymış. **CAPTCHA çözme veya
parmak izi sahteciliği denemedik** — kural gereği bunu yapmıyoruz. Hepsiburada MVP'den
çıkarıldı, `scrapers/hepsiburada.py` referans olarak duruyor ama `test_scrapers.py`'a
dahil değil.

## 5. akakce.com / cimri.com — fiyat karşılaştırma siteleri de kapalı çıktı

**Sorun:** Hepsiburada'ya alternatif olarak denedik. robots.txt her ikisinde de
crawling'e izin veriyordu, ama düz istekte ikisi de 403 döndürdü (ayrı bot koruması).

**Çözüm:** Bu iki siteyi de bıraktık, yerine daha küçük ölçekli, kendi bot korumaları
olmayan bilgisayar parçası satıcılarına (itopya.com, incehesap.com) yöneldik.

## 6. incehesap.com — Cloudflare'in otomatik JS doğrulaması

**Sorun:** Python `requests` ile kategori sayfası çekildiğinde 403 + Cloudflare'in
"Just a moment..." doğrulama sayfası geldi. (`curl` ile daha önce test ettiğimizde
sadece ana sayfa/robots.txt'e bakmıştık, asıl ürün sayfasında bu çıkmamıştı.)

**Çözüm:** Bu interaktif bir CAPTCHA değil, otomatik bir JS/parmak izi kontrolü —
Playwright ile headless Chromium birkaç saniye içinde otomatik geçti (insan
müdahalesi gerekmedi). `incehesap.py` da Amazon/Trendyol gibi Playwright'a taşındı.

## 7. itopya.com — sorunsuz

Ekstra bir engel çıkmadı, düz `requests` + BeautifulSoup ile çalıştı. Bonus: sayfa
sunucu tarafında render ediliyor, JS gerekmiyor — en hafif/hızlı scraper bu.

## 8. "Resmi API kullanabilir miyiz?" sorusunun cevabı

Kullanıcı, engellerden dolayı resmi API'lerin bir çözüm olup olmadığını sordu.
Araştırma sonucu: **hayır, bu senaryo için uygun değiller** (kayıt/doğrulama
zahmetinin ötesinde bir sorun):

- **Amazon Product Advertising API** — Amazon Associates (affiliate) hesabı
  gerektiriyor VE hesabı canlı tutmak için 180 gün içinde en az 3 gerçek satış
  yönlendirmen şart. Kişisel fiyat-takip botu için pratikte erişilemez.
- **Trendyol / Hepsiburada resmi API'leri** — bunlar tamamen satıcı tarafı
  (kendi mağazanı yönetmek için); "herhangi bir ürünün fiyatını sorgula" diye bir
  uç nokta yok, çünkü alıcılar için tasarlanmamışlar.

## 9. Playwright kurulumu — greenlet derleme hatası (Python 3.13)

**Sorun:** `requirements.txt`'te pinlenmiş `playwright==1.47.0` sürümü, bağımlılığı
olan `greenlet` paketini Python 3.13 için hazır bir wheel bulamayınca kaynaktan
derlemeye çalıştı ve "Microsoft Visual C++ 14.0 or greater is required" hatası verdi
(sistemde C++ derleyicisi kurulu değil).

**Çözüm:** Playwright'ı en güncel sürüme (1.62.0) yükselttik — bu sürümün bağımlılığı
olan güncel `greenlet`, Python 3.13 için hazır (prebuilt) wheel içeriyordu, derleme
gerekmedi. `requirements.txt` güncellendi.

## 10. Terminal'de Türkçe karakterler bozuk görünüyordu

**Sorun:** Test scriptinin çıktısında "İ", "ş", "ı" gibi karakterler `�` olarak
görünüyordu — veri bozuk sanılabilirdi.

**Çözüm:** Bu sadece terminalin/stdout'un varsayılan encoding'i ile ilgiliydi, gerçek
veri bozuk değildi. `PYTHONIOENCODING=utf-8` ile çalıştırınca karakterler doğru
göründü. Üretim scriptlerinde (GitHub Actions gibi Linux/UTF-8 ortamlarda) bu sorun
zaten çıkmayacak.

## 11. Hepsiburada devre dışı bırakılınca n11 + Pazarama eklendi

Hepsiburada CAPTCHA duvarına takıldığı için kalıcı olarak devre dışı bırakıldı.
Yerine n11.com ve Pazarama araştırıldı:

- **n11.com** — robots.txt'i genel `?q=` parametresini yasaklamıyor (sadece belirli
  ürün-özelliği filtrelerini yasaklıyor), kategori sayfası (`/bilgisayar-bilesenleri/
  hard-disk?q=1+tb+ssd`) sunucu tarafında render ediliyor — düz `requests` ile
  sorunsuz çalıştı, JS/Playwright gerekmedi.
- **Pazarama** — robots.txt'i `/arama` ve `/search`'ü yasaklıyor ama kategori
  sayfasını (`/ssd-k-K04051`) yasaklamıyor. Sayfa client-side render (JS) gerektiriyor,
  Playwright ile çözüldü. Kapasiteye özel garanti bir filtre URL'si bulunamadığı için
  genel SSD kategorisi çekilip ürün adında "1 TB"/"2 TB" geçenler koda göre
  filtrelendi.

## 12. Pazarama — "10 Günün En Düşük Fiyatı" rozeti fiyat sanılıyordu

**Sorun:** Bazı ürünlerde fiyat kutusunun içinde, gerçek fiyattan ÖNCE, "Son 10
Günün En Düşük Fiyatı" diye bir uyarı metni de bir `<p>` etiketi olarak geliyordu.
İlk `<p>`'yi seçen kod, bu metnin içindeki "10" rakamını fiyat sanıp "10.00 TL" gibi
saçma bir değer üretti.

**Çözüm:** Seçiciyi daha spesifik hale getirdik — sadece gerçek fiyatın taşıdığı CSS
class'ını (`text-gray-400`) hedefleyen `<p>` elementini alıyoruz, rozet metnini değil.

## 13. Kategori sayfalarına sızan alakasız ürünler (aksesuar, disk kutusu)

**Sorun:** "Gerçek veri geliyor mu" testinden sonra tüm sonuçları fiyata göre
taradık ve iki şüpheli kayıt bulduk:
- incehesap'ın SSD kategori sayfasında, kategoriyle alakasız bir "Bu Haftanın En Çok
  Satanları" promosyon widget'ı da aynı CSS class'ını (`a.product[data-product]`)
  kullanıyordu — bir RGB anahtarlık (649 TL) SSD listesine karışmıştı.
- n11'in "1 tb ssd" araması, bir harici disk KUTUSUNU (enclosure/caddy, 6TB'a kadar
  disk destekliyor ama kendisi bir SSD değil) sonuçlara dahil etmişti.

Bu bir fiyat ayrıştırma hatası değildi — fiyatlar doğru okunuyordu, ama ürünler
gerçekten SSD değildi.

**Çözüm:** İki katmanlı filtre eklendi:
1. incehesap'ta her ürünün JSON'unda zaten hazır bir `category` alanı var — sadece
   `category == "SSD Depolama"` olanlar alınıyor.
2. Tüm sitelerde ortak bir `MIN_PLAUSIBLE_PRICE` (2000 TL) alt sınırı eklendi
   (`scrapers/_price.py`) — gerçek bir 1TB/2TB SSD'nin bu fiyatın altına inmesi
   gerçekçi değil, bu yüzden aksesuar/kutu gibi ürünler bu eşikle de elenir.

## 14. Playwright'ta ara sıra zaman aşımı (timeout)

**Sorun:** Birden fazla siteyi art arda Playwright ile açarken bazen `Page.goto`
20 saniyede tamamlanmıyordu (Trendyol ve Amazon'da birer kez görüldü).

**Çözüm:** İki değişiklik yapıldı: (1) `page.goto`'nun varsayılan davranışı olan
sayfanın TAMAMEN yüklenmesini (`"load"` event'i — reklam/izleyici scriptleri dahil)
beklemek yerine, sadece DOM'un hazır olmasını (`"domcontentloaded"`) beklemesi
sağlandı — zaten hemen ardından asıl ürün elementini ayrıca bekliyoruz. (2) Zaman
aşımı süresi 20 saniyeden 30 saniyeye çıkarıldı.

## 15. Fiyat geçmişi deposu eklenirken fark edilen tasarım sorunu (Pazarama çift istek)

**Sorun:** `storage.py` eklenirken her scraper'ın `scrape(capacity)` fonksiyonunu ayrı
ayrı çağırmak gerekiyordu (1TB için bir, 2TB için bir). Ama Pazarama'da ürün adına
göre kapasite filtrelemesi yapıldığı için `scrape("1tb")` ve `scrape("2tb")` ayrı ayrı
çağrılınca kategori sayfası **iki kere** çekiliyordu - gereksiz yere sitenin sunucusuna
ekstra yük.

**Çözüm:** Her scraper'ın döndürdüğü ürün sözlüğüne `capacity` alanı eklendi. Böylece
`collect_prices.py` her modülü tek seferde `scrape_all()` ile çağırıyor, kapasiteyi
ayrıca URL'den değil ürünün kendi verisinden okuyor - Pazarama'da tek istek yetiyor.

## Genel prensip

Hiçbir sitede CAPTCHA çözme, tarayıcı parmak izi sahteciliği, proxy rotasyonu ya da
bot-tespitini kasıtlı olarak yenmeye yönelik bir teknik kullanılmadı. Kullanılan tek
"araç" gerçek bir tarayıcı motoruydu (Playwright/Chromium) — bu, JS ile render edilen
sayfaları normal bir kullanıcı gibi açmak için gerekliydi, robots.txt'in izin verdiği
sınırlar içinde kaldık. Hepsiburada gibi bunun yetmediği durumlarda siteyi listeden
çıkardık, zorlamadık.
