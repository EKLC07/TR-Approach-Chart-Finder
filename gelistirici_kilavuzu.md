# Türkiye Chart Lab geliştirici kılavuzu

Bu kılavuz, projede hızlı değişiklik yapabilmek için hazırlanmış pratik dosya haritasıdır.
Amaç; “neyi değiştirmek için hangi dosyaya bakacağım?” sorusunu hızlı cevaplamaktır.


## 1. Projenin ana mantığı

Uygulama yerel çalışan bir Python web uygulamasıdır.

- Backend: Python `http.server`
- Frontend: tek HTML dosyası
- PDF kaynağı: DHMİ public AIP PDF linkleri
- AI yardımcısı: yerel Python tabanlı Ciguli motoru
- Çalışma adresi: `http://localhost:8787`

Ana giriş noktası:

```txt
app/main.py
```

Kullanıcının gördüğü ana arayüz:

```txt
outputs/turkiye-chart-finder.html
```


## 2. En kritik dosyalar

```txt
app/main.py
```

Local web server burada başlar. API endpointleri ve static dosya servis etme işi bu dosyadadır.

Buradan yönetilen ana endpointler:

- `/api/airports`
- `/api/airport-info`
- `/api/charts`
- `/api/runways`
- `/api/coverage`
- `/api/chart-analysis`
- `/api/chart-match`
- `/api/pdf/...`
- `/api/assist`
- `/api/assistant/capabilities`


```txt
outputs/turkiye-chart-finder.html
```

Ana arayüzün tamamı buradadır.
HTML, CSS ve JavaScript aynı dosyanın içindedir.

Buradan değişenler:

- tema ve renkler
- panel ölçüleri
- PDF viewer görünümü
- chart listesi görünümü
- harita alanı
- Ciguli sohbet arayüzü
- dil metinleri
- zoom / fit kontrolleri
- frontend state yönetimi


```txt
app/config.py
```

Uygulama ayarları buradadır.

Önemli değerler:

- `PORT`: uygulamanın çalıştığı port
- `DHMI_BASE`: DHMİ PDF taban adresi
- `PDF_SCAN_LIMIT`: bir meydan için kaç IAC PDF deneneceği
- `CACHE_TTL_SECONDS`: chart tarama cache süresi


```txt
app/data/airports.py
```

Türkiye meydan listesi buradadır.

Yeni meydan eklemek, meydan adı düzeltmek veya şehir/koordinat bilgisi değiştirmek için bu dosyaya bakılır.


```txt
app/services/runways.py
```

Pist verileri burada yüklenir.
Temel kaynak OurAirports datasıdır; fakat chartlarda görünen ama açık veri setinde eksik kalan pistler için manuel supplement alanı vardır.

Önemli alan:

- `MANUAL_RUNWAY_SUPPLEMENTS`

Örnek:

- LTAC için chartlarda görünen `RWY 03C` burada manuel eklenir.


## 3. Chart bulma ve PDF tarafı

```txt
app/services/charts.py
```

Chart PDF dosya adını üretir, DHMİ linkini oluşturur, PDF var mı diye kontrol eder ve PDF byte verisini indirir.

Burada önemli fonksiyonlar:

- `STATIC_CHART_INDEX`
- `pdf_name(icao, number)`
- `pdf_url(file_name)`
- `static_charts_for_runway(icao, runway)`
- `pdf_looks_valid(url)`
- `discover_charts(icao)`
- `validate_pdf_file(file_name)`
- `get_pdf_bytes(file_name)`

Şunu değiştirmek istersen:

- Daha fazla chart numarası taransın: `app/config.py` içindeki `PDF_SCAN_LIMIT`
- PDF adı formatı değişsin: `pdf_name`
- PDF doğrulama daha katı/gevşek olsun: `pdf_looks_valid`
- PDF indirme hatası davranışı değişsin: `get_pdf_bytes`
- Büyük meydanlarda pist seçimi daha hızlı olsun: `STATIC_CHART_INDEX`

Pist seçili chart taramasında akış şu şekildedir:

1. Pist butonuna basılınca frontend önce `/api/chart-match?icao=LTAC&runway=03C` çağrısı yapar.
2. `app/services/charts.py` içindeki `STATIC_CHART_INDEX` önce kontrol edilir.
3. Static index’te eşleşme varsa chart anında döner.
4. Static index yoksa `app/main.py` içindeki `first_chart_for_runway(...)` fallback olarak çalışır.
5. Fallback akışta PDF’ler küçük gruplar halinde kontrol edilir; ilk doğru chart bulununca frontend’e döner.
6. Her PDF için `app/services/chart_analysis.py` içindeki `chart_runways(...)` ile chart başlığından pist okunur.
7. Normal tüm liste taraması için `/api/charts?icao=LTAC` kullanılır.
8. Tam filtreli liste gerektiğinde `/api/charts?icao=LTAC&runway=03C` hâlâ desteklenir.

Hızlı index ilk dalga:

- LTAC
- LTFM
- LTAI

Sonraki hedef büyük meydanlar:

- LTFJ
- LTBS
- LTCG

Not:

Yanlış chart açmamak için pist okunamazsa o chart seçili pist filtresine dahil edilmez.


```txt
app/services/chart_analysis.py
```

Seçili PDF’den metin çıkarma ve operasyonel chart verilerini ayıklama dosyasıdır.

Burada çıkarılan kritik veriler:

- meydan
- pist
- yaklaşma tipi
- course
- frekanslar
- AD elevation
- threshold elevation
- transition altitude
- max holding speed
- profil / alçalma başlangıcı
- minima
- missed approach
- navigasyon yardımcıları

Şunu değiştirmek istersen:

- Yeni bir chart verisi yakalamak: `_extract_facts`
- Chartın hangi piste ait olduğunu filtrelemek: `chart_runways`, `chart_matches_runway`
- Frekans ayıklama: `_frequencies`
- İrtifa ayıklama: `_elevations`
- Holding bilgisi: `_holding`
- Alçalma profili: `_descent_profile`
- Course / baş değeri: `_courses`
- Minima: `_minimums`
- Missed approach: `_missed_approach`
- Analiz kartlarının sırası/görünür içeriği: `_sections_from_facts`
- Türkçeye çevrilen kısa chart metinleri: `_translate_short_chart_value`
- Missed approach Türkçeleştirme: `_translate_missed_approach`


## 4. Ciguli AI tarafı

```txt
app/services/assistant.py
```

Frontend ile AI motoru arasındaki servis katmanıdır.
Genelde bu dosya çok değişmez; istekleri `app/ai/engine.py` tarafına taşır.


```txt
app/ai/engine.py
```

Ciguli’nin ana giriş noktasıdır.
Aktif chart, meydan bilgisi, analiz sonucu, konuşma geçmişi ve lokal hafıza burada tek bağlam haline getirilir.

Önemli fonksiyonlar:

- `assist(...)`
- `_chart_context(...)`
- `_clean_history(...)`
- `capabilities()`

Şunu değiştirmek istersen:

- Ciguli’ye daha fazla bağlam vermek: `_chart_context`
- Sohbet geçmişi kaç mesaj taşınsın: `_clean_history`
- AI kapasite bilgisinde görünen alanlar: `capabilities`


```txt
app/ai/ciguli_core.py
```

Ciguli’nin cevap üretme mantığının ana dosyasıdır.

Şunu değiştirmek istersen:

- Kalıp cevapları azaltmak/artırmak
- Chart sorularına verilen cevapları değiştirmek
- Pist, şehir, meydan, yön gibi bağlam sorularını geliştirmek
- Course/minima/frekans/missed approach cevaplarını iyileştirmek
- Türkçe cevap tonunu düzenlemek

Önemli fonksiyonlar:

- `answer(...)`
- `_chart_answer(...)`
- `_chart_data_answer(...)`
- `_context_answer(...)`
- `_requested_chart_data_topic(...)`
- `_requested_context_topic(...)`
- `_analysis_value(...)`
- `_section_lines(...)`


```txt
app/ai/brain.py
```

Ciguli’nin soruyu nasıl yorumladığı ve düşünce tipini nasıl çıkardığı dosyadır.

Şunu değiştirmek istersen:

- Soru mu, sohbet mi, istek mi daha iyi ayrılsın
- Daha doğal cevap yönlendirmesi yapılsın
- Kullanıcının niyeti daha doğru yakalansın


```txt
app/ai/language.py
```

Türkçe/İngilizce dil algılama ve basit konuşma tespit yardımcıları buradadır.

Şunu değiştirmek istersen:

- İngilizce/Türkçe algısı
- Selamlaşma algısı
- Günlük sohbet algısı


```txt
app/ai/daily_talk.py
```

Günlük konuşma, selamlaşma, teşekkür, nasılsın gibi cevaplar buradadır.

Kalıp cevaplardan rahatsızsan önce bu dosyaya bak.


```txt
app/ai/knowledge.py
```

Genel havacılık/simülasyon konu cevapları buradadır.

Örneğin:

- VOR nedir?
- ILS nedir?
- minima ne demek?
- approach briefing nasıl okunur?


```txt
app/ai/memory.py
```

Ciguli’nin lokal konuşma hafızası buradadır.

Not:

- Kullanıcı sohbet içeriğini dışarı göndermez.
- Lokal hafıza dosyası kullanıcının bilgisayarında kalır.


```txt
app/ai/training_data/
```

Ciguli’nin dil bankası, örnekleri ve notları buradadır.

Önemli dosyalar:

- `aviation_notes_tr.md`
- `aviation_notes_en.md`
- `chart_reading_rules.md`
- `conversation_examples.md`
- `daily_talk_tr.md`
- `daily_talk_en.md`
- `phrase_bank_tr.json`
- `phrase_bank_en.json`
- `vocabulary_tr.txt`
- `vocabulary_en.txt`

Şunu değiştirmek istersen:

- Ciguli daha iyi Türkçe konuşsun: `daily_talk_tr.md`, `phrase_bank_tr.json`
- İngilizce cevaplar gelişsin: `daily_talk_en.md`, `phrase_bank_en.json`
- Chart okuma kuralları gelişsin: `chart_reading_rules.md`
- Havacılık bilgisi artsın: `aviation_notes_tr.md`, `aviation_notes_en.md`


## 5. Frontend içinde en çok bakılacak yerler

Dosya:

```txt
outputs/turkiye-chart-finder.html
```

Bu dosyada üç ana bölüm var:

1. CSS tema/stil alanı
2. HTML layout alanı
3. JavaScript uygulama mantığı


### Dil metinleri

Yaklaşık şu bölgede:

```txt
messages.tr
messages.en
```

Buradan Türkçe/İngilizce arayüz metinleri değiştirilir.


### PDF açma

```txt
openPdf(chart)
renderPdfStage(...)
renderPdfPages(...)
rerenderActivePdf(...)
updateZoomControls()
showPdfFallback(...)
```

Şunu değiştirmek istersen:

- Chart seçilince PDF nasıl açılsın
- İlk zoom seviyesi ne olsun
- Fit-to-screen davranışı nasıl olsun
- PDF.js çalışmazsa iframe fallback nasıl görünsün


### Chart listesi

```txt
renderCharts()
fetchCharts()
fetchChartForRunway()
runCoverage()
```

Şunu değiştirmek istersen:

- Chart kart tasarımı
- Chart başlığı
- PDF OK etiketi
- Liste sırası
- Bulunamadı mesajları
- Pist butonuna basılınca doğru chartın hızlı açılması

Not:

Chart liste kartlarının kompakt görünümü CSS tarafında `.chartButton`, `.chartTitle`, `.chartMeta` ve `.tag` seçicileriyle yönetilir.


### Harita ve pistler

```txt
initMap()
renderMap()
loadRunways()
renderRunways()
selectRunway(runway)
runwayEndpoints(...)
drawRunways()
```

Şunu değiştirmek istersen:

- Harita yüksekliği/genişliği
- Pist butonları
- Pist çizimleri
- Seçili pist davranışı
- Dataset’te eksik kalan pistleri eklemek: `app/services/runways.py` içindeki `MANUAL_RUNWAY_SUPPLEMENTS`


### Ciguli sohbet arayüzü

```txt
addChatMessage(...)
resetAssistantChat()
askAssistant(...)
setThinking(...)
formatChatTime(...)
```

Şunu değiştirmek istersen:

- Mesaj balonları
- Saat/dakika formatı
- Otomatik mesaj davranışı
- Thinking mesajı
- Kullanıcı/Ciguli meta satırları


### Analiz kartları

```txt
renderAnalysis(payload)
analyzeSelectedChart()
```

Şunu değiştirmek istersen:

- Analiz butonu davranışı
- Kart başlıkları
- Kartların sırası
- Hangi analiz verileri gösterilsin
- Analiz sonrası Ciguli’ye mesaj düşsün mü


## 6. Tema ve görsel taraf

Ana tema dosyası ayrı değil; CSS doğrudan şurada:

```txt
outputs/turkiye-chart-finder.html
```

Arka plan uçağı:

```txt
outputs/assets/boeing-737-silhouette.png
```

Logo:

```txt
outputs/turkiye-chart-lab-logo.svg
outputs/tr-approach-chart-finder.ico
```

Şunu değiştirmek istersen:

- Genel renkler: CSS `:root` değişkenleri
- Panel cam efekti: `aside`, `.pane`, `.assistantPane`, `.viewerPane`
- PDF alanı: `.viewerPane`, `.pdfStage`, `.pdfFrame`, `.pdfPage`
- Butonlar: `button`, `.download`, `.askBtn`
- Arka plan uçağı: `.app::before`

Not:

CSS dosyanın sonunda daha yeni override blokları bulunabilir.
Bir stil değişmiyorsa, aynı seçici dosyanın daha aşağısında tekrar yazılmış olabilir.
Bu projede son yazılan CSS genelde kazanır.


## 7. Kurulum ve dağıtım

```txt
TR-Approach-Chart-Finder-Setup.cmd
```

Kullanıcının çalıştırdığı kurulum dosyasıdır.

Yaptıkları:

- eski çalışan local server varsa kapatır
- portable Python runtime hazırlar
- modül doğrulaması yapar
- masaüstüne shortcut oluşturur
- uygulamayı başlatır


```txt
outputs/start-chartlab.cmd
```

Uygulamayı başlatan asıl kısa yol hedefidir.


```txt
TR-Approach-Chart-Finder-Uninstall.cmd
```

Kısayol ve lokal runtime temizliği için kullanılır.


Paylaşımda dikkat:

- `owner-tools/` paylaşılmamalı.
- `.git/` paylaşılmamalı.
- `release-artifacts/` içindeki eski paketler tekrar pakete gömülmemeli.
- `app/vendor/pypdf/` kalabilir; PDF text extraction için işe yarar.
- `.runtime/` zorunlu değildir; setup yoksa kendisi hazırlayabilir.


## 8. Owner tools

```txt
owner-tools/
```

Bu klasör kullanıcıya verilmemelidir.
Geliştirici/owner tarafı eğitim ve özel araçlar için ayrılmıştır.

Owner trainer:

```txt
owner-tools/Ciguli-Trainer.cmd
owner-tools/ciguli-trainer.html
```

Bu panel sadece owner mod aktifken açılır.
Kontrol noktası:

```txt
owner-tools/.owner-mode
```

Bu dosya yoksa trainer endpointleri görünmez.


## 9. Sık değişiklik senaryoları

### Yeni meydan eklemek

```txt
app/data/airports.py
```

Meydan bilgisi eklendikten sonra arayüz `/api/airports` üzerinden bunu görür.


### DHMİ PDF formatı değişirse

```txt
app/services/charts.py
```

Önce `pdf_name`, `PDF_RE` ve `pdf_url` kontrol edilir.


### Chart bulunmuyor sorunu

Bakılacak sıra:

1. `app/config.py` içindeki `DHMI_BASE`
2. `app/services/charts.py` içindeki `pdf_name`
3. `app/services/charts.py` içindeki `pdf_looks_valid`
4. Pist filtresi varsa `app/main.py` içindeki `filter_charts_by_runway`
5. PDF text layer pist okuyorsa `app/services/chart_analysis.py` içindeki `chart_runways`
6. Tarayıcıda `/api/charts?icao=LTAC`
7. Pist filtresi için `/api/charts?icao=LTAC&runway=21R`


### Analiz yanlış veri çıkarıyorsa

```txt
app/services/chart_analysis.py
```

Önce ilgili extractor fonksiyonuna bak:

- frekans: `_frequencies`
- pist/course: `_procedure`, `_courses`
- irtifa: `_elevations`, `_descent_profile`
- minima: `_minimums`
- missed approach: `_missed_approach`


### Ciguli soruyu yanlış anlıyorsa

Bakılacak sıra:

1. `app/ai/ciguli_core.py`
2. `app/ai/brain.py`
3. `app/ai/language.py`
4. `app/ai/training_data/conversation_examples.md`
5. `app/ai/training_data/chart_reading_rules.md`


### Ciguli fazla kalıp konuşuyorsa

Bakılacak sıra:

1. `app/ai/daily_talk.py`
2. `app/ai/training_data/phrase_bank_tr.json`
3. `app/ai/training_data/phrase_bank_en.json`
4. `app/ai/ciguli_core.py`


### Arayüz dili değişmiyorsa

```txt
outputs/turkiye-chart-finder.html
```

Bakılacak alanlar:

- `messages.tr`
- `messages.en`
- `applyLanguage()`
- `chartStatusMode`
- `refreshChartStatusText()`
- HTML içindeki `data-i18n` alanları

Not: Chart durum satırı doğrudan string olarak bırakılmamalı. Dil değişince `idle`, `scanning`, `found`, `empty`, `failed` durumlarına göre `refreshChartStatusText()` yeniden metin üretir.


### Tema eklemek

İlk önerilen yapı:

1. CSS değişkenlerini `:root` veya tema class altında tanımla.
2. `body` veya `.app` üzerine tema class ekle.
3. Kullanıcı seçimini `localStorage` içinde sakla.

İlgili dosya:

```txt
outputs/turkiye-chart-finder.html
```


## 10. Hızlı test komutları

Proje kökünde çalış:

```powershell
cd C:\Users\Enes\Desktop\TR-Approach-Chart-Finder
```

Python import testi:

```powershell
.\.runtime\python\python.exe -c "from app.services.chart_analysis import analyze_chart; print('ok')"
```

Server başlatma:

```powershell
.\.runtime\python\python.exe -m app.main
```

Tarayıcı:

```txt
http://localhost:8787
```

Frontend JavaScript syntax testi:

```powershell
C:\Users\Enes\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe -e "const fs=require('fs'); const html=fs.readFileSync('outputs/turkiye-chart-finder.html','utf8'); [...html.matchAll(/<script[^>]*>([\s\S]*?)<\/script>/gi)].map(m=>m[1]).forEach(s=>new Function(s)); console.log('js-ok')"
```


## 11. Geliştirme önceliği önerisi

Kısa vadede en mantıklı sıra:

1. Ayarlar sayfası
2. Tema seçici
3. Hakkımızda / iletişim / destek sayfaları
4. Anonim kullanım analitiği
5. Chart analysis extractor iyileştirmeleri
6. Ciguli cevap kalitesi ve briefing modu
7. Setup ve paketleme stabilizasyonu


## 12. Ürün güvenliği ve sınır notu

Bu uygulama chart okuma, simülasyon ve eğitim desteği içindir.
Gerçek uçuşta resmi AIP, güncel chart, NOTAM, ATC talimatı ve geçerli havacılık kuralları esas alınmalıdır.

PDF içerikleri bize ait değildir.
Uygulama, public kaynaklara erişimi kolaylaştıran ve seçili chart üzerinden yardımcı analiz sunan bir araç olarak konumlandırılmalıdır.


## 13. Uçuş/test sonrası hızlı not formatı

Uygulamayı gerçek kullanımda denerken şu format yeterli:

```txt
Meydan:
Chart:
Ne yaptım:
Sorun:
Eksik:
Fazla:
Ciguli cevabı iyi miydi:
Öncelik:
```

Örnek:

```txt
Meydan: LTAC
Chart: IAC 02
Ne yaptım: PDF açtım, Ciguli'ye minima sordum.
Sorun: Minima CAT ayrımı net gelmedi.
Eksik: Missed approach özeti daha kısa olmalı.
Fazla: Meydan notları fazla yer kaplıyor.
Ciguli cevabı iyi miydi: Kısmen
Öncelik: Yüksek
```
