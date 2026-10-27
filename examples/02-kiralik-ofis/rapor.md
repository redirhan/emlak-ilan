# Emlak ilanı kontrol raporu

**Bu bir hukuki görüş değildir; bilgilendirme amaçlıdır.**

- İlan: Kiralık Ofis · Kızılay, Çankaya / Ankara · 65.000 TL / ay
- Kanallar: portal, instagram · Yayın tarihi: 2026-11-05 · Kontrol tarihi: 2026-10-27
- Kural dosyası: sürüm 1.0.0, kaynaklar 2026-10-27 tarihinde okundu

## Sonuç: KONTROL LİSTESİNİ TAMAMLAYIN

| DÜZELT | UZMANA SOR | UYARI | GÖZLE KONTROL | BİLGİ | GEÇTİ | UYGULANMAZ |
|---|---|---|---|---|---|---|
| 0 | 0 | 1 | 0 | 2 | 33 | 6 |

## Yapılacaklar

### [UYARI] FYT-07 · 'Fiyat düştü' / indirim iddiası belgeli mi?

- **Bulgu:** Fiyat düşüşü 70.000 TL → 65.000 TL belgeli görünüyor; reklam_kontrol.yaml ile Reklam Etiketi Kontrolü'nü çalıştırın.
- **Ne yapmalı:** fiyat_gecmisi.onceki_fiyat, son_10_gun_en_dusuk, degisim_tarihi ve kanal alanlarını doldurun. Belgeleyemiyorsanız indirim dilini kaldırın, yalnız güncel fiyatı yazın.
- **Dayanak:** Reklam Etiketi Kontrolü (Ticari Reklam ve Haksız Ticari Uygulamalar Yön. m.14, RG 33297) m.14(1)-(3) (güven: orta)
- **Belirsizlik:** m.14'ün emlak işletmesinin (satıcı değil, aracı) ilanındaki fiyat düşüşüne uygulanıp uygulanmadığı net değil. 6502'de konut "mal" tanımına girer. Daha sıkı yorumla uygulanır.

## Ek dosyalar

- ilanlar.md: Sahibinden, Hepsiemlak, Emlakjet başlık + açıklama + özellik listesi + form alanları
- instagram.md: reels çekim planı + ekran yazıları + son kart + açıklama + story
- carousel_plan.yaml: Türkçe Carousel Üretici planı (7-8 slayt + açıklama)
- reklam_kontrol.yaml: Reklam Etiketi Kontrolü girdisi (indirim / yapay zekâ / iş birliği)
- Reklam Etiketi Kontrolü bulunamadı ya da kapalı; çalıştırmak için: python3 ~/.claude/skills/reklam-etiketi/scripts/kontrol.py reklam_kontrol.yaml

## Tüm kontroller

| Kod | Kontrol | Durum | Güven |
|---|---|---|---|
| EIDS-01 | EİDS yetki doğrulaması yapıldı mı? | GEÇTİ | yüksek |
| EIDS-02 | Sosyal medya paylaşımında EİDS doğrulamalı ilan linki var mı? | GEÇTİ | yüksek |
| EIDS-03 | Sosyal medya paylaşımında ilan fiyatı var mı? | GEÇTİ | yüksek |
| EIDS-04 | Görseller ve açıklama doğrulanmış ilandaki taşınmaza mı ait? | GEÇTİ | yüksek |
| YTK-01 | Yetki belgesi numarası ilanda mı? | GEÇTİ | yüksek |
| YTK-02 | Yetki belgesindeki işletme adı / unvanı ilanda mı? | GEÇTİ | yüksek |
| YTK-03 | Taşınmaz için yazılı yetkilendirme sözleşmesi var mı? | GEÇTİ | yüksek |
| YTK-04 | Yetki süresi yayın tarihinde geçerli mi? | GEÇTİ | yüksek |
| ZRN-01 | İl, ilçe, mahalle var mı? (açık adres yok mu?) | GEÇTİ | yüksek |
| ZRN-02 | Ada ve parsel var mı? | GEÇTİ | yüksek |
| ZRN-03 | İmar ve yapı kullanma izni (iskân) durumu yazılı mı? | GEÇTİ | orta |
| ZRN-04 | Tapu cinsi / durumu yazılı mı? | GEÇTİ | orta |
| ZRN-05 | Büyüklük, yaş ve fiili kullanım durumu yazılı mı? | GEÇTİ | orta |
| ZRN-06 | Kat, cephe ve manzara yazılı mı? | GEÇTİ | orta |
| ZRN-07 | Toplu taşıma duraklarına yaklaşık mesafe yazılı mı? | GEÇTİ | orta |
| ZRN-08 | Sosyal ve kültürel mekânlara yaklaşık mesafe yazılı mı? | GEÇTİ | orta |
| ZRN-09 | Oda, salon, banyo, tuvalet, balkon sayısı ve yaklaşık büyüklükleri yazılı mı? | GEÇTİ | orta |
| ZRN-10 | Apartman / site / müstakil durumu ve donatılar yazılı mı? | GEÇTİ | orta |
| ZRN-11 | Arazide hisse, emsal, öngörülen bina yüksekliği ve ekili/dikili ürün yazılı mı? | UYGULANMAZ | orta |
| ZRN-12 | İpotek, haciz ve benzeri kısıtlama durumu yazılı mı? | GEÇTİ | orta |
| ZRN-13 | İletişim bilgisi var mı? | GEÇTİ | yüksek |
| ZRN-14 | Enerji kimlik belgesi bilgisi (varsa) yazılı mı? | GEÇTİ | yüksek |
| FYT-01 | Fiyat girildi mi? | GEÇTİ | yüksek |
| FYT-02 | Fiyat toplam bedel mi? (peşinat, taksit ya da 'başlayan fiyat' değil) | GEÇTİ | yüksek |
| FYT-03 | Fiyat Türk lirası mı? | GEÇTİ | orta |
| FYT-04 | Fiyat gerçekçi mi? (yem fiyat) | GEÇTİ | orta |
| FYT-05 | KDV durumu açık mı? (yeni konut / iş yeri / müteahhit satışı) | UYGULANMAZ | düşük |
| FYT-06 | İlan fiyatı yükseltildi mi? (haklı sebep) | UYGULANMAZ | orta |
| FYT-07 | 'Fiyat düştü' / indirim iddiası belgeli mi? | UYARI | orta |
| KMS-01 | İlandaki hizmet bedeli (komisyon) yasal sınırın içinde mi? | GEÇTİ | yüksek |
| KMS-02 | Gösterme ücreti isteniyor mu? | GEÇTİ | yüksek |
| YNL-01 | Kırmızı bayrak ifadeler (garanti, kesin getiri, imar gelecek...) | GEÇTİ | orta |
| YNL-02 | Metindeki iddia girilen bilgilerle çelişiyor mu? | GEÇTİ | yüksek |
| YNL-03 | Hisseli tapu açıkça belirtilmiş mi? | UYGULANMAZ | yüksek |
| YNL-04 | Üstünlük ya da aciliyet iddiası belgeli mi? | GEÇTİ | orta |
| GRS-01 | Yapay zekâ ile üretilmiş ya da düzenlenmiş görsel var mı? (sanal mobilya, gökyüzü, render) | GEÇTİ | orta |
| GRS-02 | Proje / render görsellerinde 'temsili' ibaresi var mı? | UYGULANMAZ | düşük |
| SM-01 | Satıldı / kiralandı olunca 3 gün içinde ilan kaldırılacak mı? | BİLGİ | yüksek |
| REK-01 | İçerik üretici / iş birliği paylaşımı mı? | UYGULANMAZ | orta |
| PLT-01 | Başlık platform sınırına sığıyor mu? | GEÇTİ | düşük |
| PLT-02 | Başlık tamamen büyük harf ya da emoji/ünlem dolu mu? | GEÇTİ | düşük |
| CZA-01 | İdari para cezası aralığı (bilgi) | BİLGİ | orta |

## EİDS takvimi (bilgi)

- 2023-11-01: Kimlik doğrulama (ilan veren kişi/işletme) zorunlu (RG32295)
- 2024-09-15: Yetki doğrulama başladı; 31.12.2024'e kadar geçiş (doğrulamasız ilan mümkün, doğrulananlarda EİDS logosu) (TB-EIDS-2024)
- 2025-01-01: Kiralık taşınmaz ilanlarında yetki doğrulaması zorunlu (Bakanlığın 2024 duyurusu tüm ilanlar için bu tarihi veriyordu; uygulama kademeli yürüdü) (TB-EIDS-2024)
- 2025-04-07: Satılık iş yeri ilanları kapsama alındı **[kaynaklar çelişkili]** (KARAR-2025)
- 2026-02-01: Satılık konut ilanları: bir kaynağa göre ülke geneli, diğerine göre yalnız İzmir, Antalya, Sivas pilotu **[kaynaklar çelişkili]** (AA-SATILIK-2026)
- 2026-02-15: Satılık konut ilanları ülke genelinde zorunlu (AA/TRT) **[kaynaklar çelişkili]** (AA-SATILIK-2026)
- 2026-08-22: Bakanlık: zorunluluk Instagram, Facebook, WhatsApp dahil elektronik ortamdaki TÜM taşınmaz ilanlarını kapsar; sosyal medyada EİDS linki + fiyat zorunlu (TB-SOSYAL-2026)

Bu kit daha sıkı yorumu uygular: bugün her ilan türü ve her kanal için EİDS yetki doğrulaması şart sayılır.

## İdari para cezası aralıkları (bilgi)

- **Emlak işletmesi (ilan veren); Yönetmeliğin 12/2 dışındaki hükümleri (zorunlu bilgiler, yanıltıcı ilan, yetkisiz ilan, sosyal medya kuralları)**
  - Dayanak: Taşınmaz Ticareti Hakkında Yönetmelik m.22(4) → 6585 s. Kanun m.18(1)(i)
  - Kanundaki tutar: 10.000 TL - 300.000 TL (her bir aykırılık)
  - 2026: 28.620 TL - 858.620 TL (her bir aykırılık) (yeniden değerleme oranlarıyla hesaplandı; Bakanlığın ilan ettiği tablo bulunamadı)
  - Aynı takvim yılında tekrar: önceki cezanın iki katı (6585 m.18(5)). Düzeltilmezse ya da yıl içinde tekrarlanırsa yetki belgesi iptal edilebilir, bir yıl yeni belge verilmez (Yön. m.9(1)(ç), 9(5)).
  - Uygulama örnekleri: 100.000 TL/işletme (sosyal medyada mevzuata aykırı ilan, Ağustos 2026; fahiş fiyat artışı, 2023-2024); 28.620 TL (peşinatın fiyat gibi gösterilmesi, Ekim 2026 haberi)
- **İlan platformu (Sahibinden, Hepsiemlak, Emlakjet vb.); Yönetmelik m.12(2) (kimlik ve yetki doğrulama dahil)**
  - Dayanak: Taşınmaz Ticareti Hakkında Yönetmelik m.22(4) → 6563 s. Kanun m.12(1)(d)
  - Kanundaki tutar: 10.000 TL - 100.000 TL (her bir aykırılık)
  - 2026: 28.620 TL - 286.206 TL (her bir aykırılık) (yeniden değerleme oranlarıyla hesaplandı; Bakanlığın ilan ettiği tablo bulunamadı)
  - Uygulama örnekleri: Bakan 06.09.2024: 'her bir aykırılık için 158 bin 460 liraya kadar' (2024 üst sınırı)

## Kaynaklar

- [TTHY] Taşınmaz Ticareti Hakkında Yönetmelik (RG 05.06.2018, sayı 30442), değişiklikler işlenmiş metin. https://www.mevzuat.gov.tr/mevzuat?MevzuatNo=24645&MevzuatTur=7&MevzuatTertip=5 (belge tarihi 2026-10-01, okunma 2026-10-27)
- [RG32295] Taşınmaz Ticareti Hakkında Yönetmelikte Değişiklik Yapılmasına Dair Yönetmelik (RG 31.08.2023, sayı 32295). https://www.resmigazete.gov.tr/eskiler/2023/08/20230831-6.htm (belge tarihi 2023-08-31, okunma 2026-10-27)
- [TB-EIDS-2024] Ticaret Bakanlığı duyurusu: Elektronik İlan Doğrulama Sistemi (EİDS) Yetki Doğrulama Uygulaması Hayata Geçirildi. https://ticaret.gov.tr/kurumsal-haberler/elektronik-ilan-dogrulama-sistemi-eids-yetki-dogrulama-uygulamasi-hayata-gecirildi (belge tarihi 2024-09-17, okunma 2026-10-27)
- [TB-BOLAT-2024] Ticaret Bakanlığı haberi: Bakan Bolat, Emlakta Doğrulanmış İlan Uygulamasına İlişkin Detayları Paylaştı. https://ticaret.gov.tr/haberler/bakan-bolat-emlakta-dogrulanmis-ilan-uygulamasina-iliskin-detaylari-paylasti (belge tarihi 2024-09-06, okunma 2026-10-27)
- [TB-SOSYAL-2026] Ticaret Bakanlığı haberi: EİDS kapsamında kimlik ve yetki doğrulaması zorunluluğu Instagram, Facebook ve WhatsApp dahil elektronik ortamda verilen tüm taşınmaz ve taşıt ilanlarını kapsar. https://ticaret.gov.tr/haberler/ticaret-bakanligi-tasinmaz-ve-tasit-ticaretinde-uygulanmakta-olan-elektronik-ilan-dogrulama-sistemi-eids-kapsaminda-kimlik-ve-yetki-dogrulamasi-zorunlulugunu-instagram-facebook-ve-whatsapp-da-dahil-olmak-uzere-elektronik-ortamda-verilen-tum-tasinmaz-ve-tasi (belge tarihi 2026-08-22, okunma 2026-10-27)
- [AA-SATILIK-2026] TRT Haber (kaynak AA): Satılık konut ilanlarında yeni dönem. https://www.trthaber.com/haber/ekonomi/satilik-konut-ilanlarinda-yeni-donem-933076.html (belge tarihi 2026-01-31, okunma 2026-10-27)
- [KARAR-2025] Karar gazetesi: Emlak ilanlarında yeni dönem, 1 Şubat 2026'dan itibaren yetki doğrulaması zorunlu. https://www.karar.com/ekonomi-haberleri/emlak-ilanlarinda-yeni-donem-1-subat-2026dan-itibaren-yetki-2017537 (belge tarihi 2025-12-28, okunma 2026-10-27)
- [K6585] 6585 sayılı Perakende Ticaretin Düzenlenmesi Hakkında Kanun. https://www.mevzuat.gov.tr/mevzuatmetin/1.5.6585.pdf (belge tarihi 2024-05-29, okunma 2026-10-27)
- [K6563] 6563 sayılı Elektronik Ticaretin Düzenlenmesi Hakkında Kanun. https://www.mevzuat.gov.tr/mevzuatmetin/1.5.6563.pdf (belge tarihi 2022-07-01, okunma 2026-10-27)
- [K5326] 5326 sayılı Kabahatler Kanunu. https://www.mevzuat.gov.tr/mevzuatmetin/1.5.5326.pdf (belge tarihi 2022-07-01, okunma 2026-10-27)
- [VUK585] VUK Genel Tebliği Sıra No 585 (RG 27.11.2025, sayı 33090): 2025 yılı yeniden değerleme oranı %25,49 (2026'da uygulanır). https://www.cnbce.com/son-dakika/yeniden-degerleme-orani-yuzde-2549-oldu-h20261 (belge tarihi 2025-11-27, okunma 2026-10-27)
- [HABER-28620] Yeni Alanya: Emlak ilanının bedeli ağır oldu, 28 bin TL ceza (toplam satış bedeli yerine peşinatın ilan fiyatı gibi gösterilmesi). https://www.yenialanya.com/emlak-ilaninin-bedeli-agir-oldu-28-bin-tl-ceza-yedi (belge tarihi 2026-10-26, okunma 2026-10-27)
- [TB-BASIN-2024] Ticaret Bakanlığı: Emlak Sektörüne Yönelik Faaliyetler ve Uygulanan İdari Para Cezalarına İlişkin Basın Açıklaması. https://ticaret.gov.tr/haberler/emlak-sektorune-yonelik-faaliyetler-ve-uygulanan-idari-para-cezalarina-iliskin-basin-aciklamasi (belge tarihi 2024-06-28, okunma 2026-10-27)
- [K32] Türk Parası Kıymetini Koruma Hakkında 32 Sayılı Karar m.4(g) (Cumhurbaşkanı Kararı 85, RG 13.09.2018, sayı 30534) ve Tebliğ 2008-32/34. https://www.alomaliye.com/2018/09/13/turk-parasi-kiymetini-korumu-sayi-85/amp/ (belge tarihi 2018-09-13, okunma 2026-10-27)
- [REKLAM-ETIKETI] Reklam Etiketi Kontrolü skill'i (MIT, Redirhan Studio): Ticari Reklam ve Haksız Ticari Uygulamalar Yönetmeliği, RG 33297 (01.07.2026, yürürlük 01.08.2026) kontrolleri. https://github.com/redirhan/reklam-etiketi (belge tarihi 2026-10-27, okunma 2026-10-27)

---

**Bu bir hukuki görüş değildir; bilgilendirme amaçlıdır.** Mevzuat ve Bakanlık uygulaması değişebilir; yayından önce Resmî Gazete ve Ticaret Bakanlığı duyurularını kontrol edin. Emin olmadığınız durumda bir avukata ya da ticaret il müdürlüğüne danışın.
