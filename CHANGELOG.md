# Değişiklik günlüğü

## 1.0 — 2026-10-27
İlk sürüm. Bu bir hukuki görüş değildir; bilgilendirme amaçlıdır.
- `ilan.py uret`: YAML/JSON ilan girdisinden Sahibinden, Hepsiemlak, Emlakjet başlık + açıklama + özellik listesi +
  form alanları; Instagram reels çekim planı (ekran yazıları, kalıcı fiyat + EİDS rozeti, son kart, kapak, açıklama,
  story); Türkçe Carousel Üretici formatında carousel planı; gerekirse Reklam Etiketi Kontrolü girdisi; Markdown ve
  JSON rapor.
- `ilan.py kontrol`, `sablon` (satılık daire, kiralık ofis, arsa), `doctor`, `kurallari-dogrula`.
- 42 kural (EİDS, yetki, m.14/2-i ve 15/3 zorunlu bilgileri, fiyat, hizmet bedeli, yanıltıcı ifade, görsel, sosyal medya,
  reklam, platform, ceza bilgisi); her kuralda kaynak URL'si, belge tarihi, okunma tarihi, güven düzeyi, gerekirse
  belirsizlik. EİDS takvimi ve 2026 ceza aralıkları (hesaplanmış, işaretli).
- Kaynaklar 27.10.2026'da okundu: Taşınmaz Ticareti Hakkında Yönetmelik (mevzuat.gov.tr, RG 33387 dahil), RG 32295,
  Ticaret Bakanlığı EİDS duyuruları (2024, 2026), 6585 ve 6563 s. Kanunlar, 5326 s. Kabahatler Kanunu m.17(7).
- Sorunlu kullanıcı ifadeleri metne alınmaz; DÜZELT varsa metinler TASLAK başlığı ve `[GEREKLİ]` yer tutucularıyla yazılır;
  EİDS doğrulaması yoksa hiçbir metinde "EİDS doğrulamalı" yazmaz.
- 3 kurgusal örnek (biri bilerek uyumsuz), 23 birim testi, dahili YAML okuyucuya düz akış eşlemesi (`{a: 1}`) desteği.
