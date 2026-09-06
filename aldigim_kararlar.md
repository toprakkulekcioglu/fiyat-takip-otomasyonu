# Aldığım Kararlar

Bana sorulmadan, kendi takdirimle aldığım kararların günlüğü - neden öyle
karar verdiğimi de yazıyorum ki sonradan sorgulanabilsin.

## 2026-09-04/05 — Kullanıcı bazlı ürün takibi (web/ssd-takip.html)

- **Abonelikleri `price_history.db` yerine ayrı `data/subscriptions.json`'da tuttum.**
  Neden: O dosyayı sadece GitHub Actions yazıp push ediyor; Render'daki canlı
  sunucu da aynı dosyaya paralel yazsaydı, biri diğerinin daha yeni verisini
  ezme riski vardı. Ayrı dosya = tek yazan kuralı.
- **Render'dan git'e yazmak için `git push` yerine GitHub REST Contents API
  kullandım.** Neden: Render'ın Docker imajında çalışan bir git deposu +
  kimlik doğrulaması olduğundan emin olamadım; Contents API yerel git'e hiç
  ihtiyaç duymuyor.
- **Abonelik sistemini tek kullanıcılı (login yok) tasarladım.** Neden: Mevcut
  sistem zaten tek kişiye bildirim gönderiyor (sabit e-posta/Telegram), kapsamı
  büyütmemek için aynı model korundu.

## 2026-09-05 — Selanik laptop aramasını sıkılaştırma

- **CPU aramasına (Ryzen AI9 365+) "oyun laptobu değil" filtresi (bilinen
  seri isimleri - Nitro/Stealth/ROG/Legion/Omen vb. - elenerek) ekledim.**
  Neden: Kategori sayfası ultrabook'ları ve oyun laptoplarını birlikte
  listeliyor, kullanıcı açıkça "taşınabilir hafif" istemişti.
- **RAM/depolama sayılarını sabit bir "/../ SSD" kalıbı yerine başlıktaki ilk
  iki GB/TB sayısına bakarak çıkardım.** Neden: Aynı Skroutz kategorisinde
  bile başlık formatı kısa/uzun değişebiliyor, sabit kalıp bazı ürünleri
  sessizce atlıyordu (canlı veriyle test ederken fark ettim).

## 2026-09-06 — Selanik / Türkiye SSD fiyat karşılaştırması

- **Ürün bazlı (SKU) eşleştirme yerine kapasite bazlı (1TB/2TB/2TB-harici)
  karşılaştırma yaptım.** Neden: Yunanistan ve Türkiye'de satılan SSD
  markaları/modelleri büyük ölçüde farklı - aynı ürünü iki ülkede de bulup
  eşleştirmeye çalışmak güvenilmez olurdu. Kapasite bazlı karşılaştırma
  kullanıcının asıl sorusuna ("Selanik'te ucuz mu") daha dürüst bir cevap.
- **Türkiye tarafı için "son 24 saatteki en ucuz fiyat" ölçütünü kullandım**
  (tüm sitelerin en güncel taramasından minimum). Neden: Sistem 1 zaten
  medyan/geçmiş tutuyor ama "şu an ne kadar" sorusuna en doğru cevap en son
  taramadaki en ucuz fiyat.
- **"ssd" kelimesini üçüncü Telegram tetikleyicisi olarak seçtim**, mevcut
  "ryzen"/"teşekkür" desenine uyacak şekilde.
