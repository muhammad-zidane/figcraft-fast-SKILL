# Evaluasi & Peningkatan (Upgrade) `figcraft-fast-skill` (v1.0 → v2.0 → v3.0 → v3.1)

Dokumen ini berisi evaluasi menyeluruh atas pengembangan antarmuka **BerryCrumb Patisserie**, dengan fokus utama pada **evolusi teknis, temuan bug/celah visual, dan peningkatan arsitektur `figcraft-fast-skill`** hingga versi **v3.1**, dilengkapi evaluasi PRD dan Prompt.

---

## 1. Bedah Awal `figcraft-fast-skill` (v1.0 → v2.0)

Lokasi Resmi Skill (Single Source of Truth):
- [`SKILL.md`](file:///C:/Users/muhammmad-zidane/.gemini/config/skills/figcraft-fast-skill/SKILL.md)
- [`scripts/figcraft_ui.py`](file:///C:/Users/muhammmad-zidane/.gemini/config/skills/figcraft-fast-skill/scripts/figcraft_ui.py)
- [`scripts/design_tokens.py`](file:///C:/Users/muhammmad-zidane/.gemini/config/skills/figcraft-fast-skill/scripts/design_tokens.py)
- [`scripts/figcraft_components.py`](file:///C:/Users/muhammmad-zidane/.gemini/config/skills/figcraft-fast-skill/scripts/figcraft_components.py)
- [`scripts/smoke_test.py`](file:///C:/Users/muhammmad-zidane/.gemini/config/skills/figcraft-fast-skill/scripts/smoke_test.py)

### 1.1 Masalah Kritis pada `figcraft-fast-SKILL` Versi Awal (v1.0)

Berdasarkan analisis transkrip percakapan dan inspeksi hasil render awal, ditemukan **7 kelemahan mendasar** pada versi awal `figcraft-fast-SKILL`:

| No | Masalah pada Skill Lama (v1.0) | Dampak Saat Agen Mengeksekusi Tugas | Solusi yang Diterapkan |
| :-: | :--- | :--- | :--- |
| **1** | **Phantom Dependency (`figcraft_ui` tidak ada)**<br>`SKILL.md` menginstruksikan import `figcraft_ui`, namun tidak ada folder `scripts/` atau file `figcraft_ui.py` di dalam direktori skill. | Agen terpaksa menghabiskan ~10 langkah untuk membongkar binary `figcraft-cli.exe` & `figcraft.exe` demi mencari tahu protokol RPC, lalu membuat `figcraft_ui.py` secara mendadak (*on-the-fly*). | Menyediakan modul resmi [`scripts/figcraft_ui.py`](file:///C:/Users/muhammmad-zidane/.gemini/config/skills/figcraft-fast-skill/scripts/figcraft_ui.py) langsung di dalam folder skill resmi. |
| **2** | **Dokumentasi Protokol & Flag CLI Keliru**<br>Tertulis `figcraft-cli -app --network 7979` dan tidak disebutkan format protokolnya. | Percobaan pertama menggunakan HTTP POST gagal (`bad JSON`), karena port `7979` (`figcraft --control 7979`) menggunakan **Raw TCP Socket (JSON-Lines)** dengan method tunggal `"engine.execute"`. | Mendokumentasikan arsitektur Raw TCP `engine.execute` dan flag `--control 7979`. |
| **3** | **Eksekusi Sekuensial vs Atomic `command.batch`**<br>Klien awal mengirim `node.create` satu per satu lewat TCP (370+ round-trip). | Waktu render memakan **6.31 detik** dan memenuhi riwayat *Undo* dengan ratusan langkah *"Create layer"*. | Mengimplementasikan **Atomic Batch Queue (`auto_batch=True`)** dengan resolusi otomatis `{"$ref": "step_n"}`. |
| **4** | **Jebakan Default `width=100, height=100` (`fixed`) pada `box()`**<br>Tidak ada aturan default `hug` ketika `width`/`height` dikosongkan. | Semua *pill filter*, *badge*, *tag alergen*, dan *tombol opsi* yang tidak diberi ukuran eksplisit berubah menjadi **kotak persegi 100×100 px** dan memotong teks di dalamnya. | Mengubah default `box()` menjadi `width=None, height=None` yang otomatis memetakan `sizingH="hug"` dan `sizingV="hug"` apabila dimensi tidak ditentukan secara eksplisit. |
| **5** | **Properti Floating (`absolute: True`) Tidak Spesifik**<br>Skill lama hanya menulis *"set dengan properti floating / absolute"* tanpa menyebut nama key di engine FigCraft. | `FloatingBestSellerBadge` (Layar 01) dan `FloatingCloseButton` (Layar 03) ikut terdorong oleh aliran *auto-layout* parent-nya alih-alih melayang di pojok kanan atas. | Menambahkan parameter `absolute: bool = False` pada `box()`, `create_rect()`, `create_text()`, dan `circle_arc()` yang menyuntikkan `"absolute": True` ke `props` engine FigCraft. |
| **6** | **`equasize_heights()` Harus Menebak Tinggi Manual**<br>Pada versi awal, pengguna harus memberikan angka `target_height` secara manual. | Jika `target_height` terlalu kecil, isi kartu terpotong; jika terlalu besar, menyisakan ruang kosong berlebih. | `equasize_heights(card_ids, target_height=None)` kini otomatis mem-flush batch, memanggil `node.get` (`fields=["height"]`) untuk mengukur tinggi aktual tiap kartu (`hug`), mencari `max(height)`, dan menyamakan tinggi seluruh kartu secara dinamis. |
| **7** | **Jebakan Seleksi pada `export_page()` & `circle_arc` Offset**<br>Setiap `node.create` secara default memilih layer baru (`select=True`), sehingga `file.export` hanya mengekspor 1 layer terakhir. | Export pertama hanya menghasilkan gambar berukuran 6 KB (1 tombol terakhir). Selain itu, path SVG lingkaran yang tidak dimulai dari `(0,0)` terkena *double-offset*. | Menetapkan `"select": False` pada seluruh pembuatan node, menormalisasi path `circle_arc` ke bounding box `(0,0)`, serta memanggil `flush()` + `select.none` secara otomatis di dalam `export_page()`. |

---

## 2. Evaluasi Pasca-Implementasi `figcraft-fast-skill` v3.0 & Perbaikan ke v3.1

Setelah mengimplementasikan fitur-fitur baru pada **v3.0** (`strict=True`, `verify_layout()`, `save_file()`, `export_frames()`, `DesignTokens`, `UIComponents`, Native Styles & Master Components) dan memeriksa 6 gambar PNG hasil ekspor di [`exports/`](file:///C:/dev/TokoKue/exports/), dilakukan audit kedua dengan temuan penting berikut:

### 2.1 Analisis Temuan Visual Utama: "Elemen Mepet ke Tepi Container Bersudut Siku"

- **Gejala Visual yang Ditemukan**:
  Pada hasil render v3.0, terlihat banyak elemen (teks judul, daftar pill, hingga jajaran kartu produk) yang **menempel rapat (0px margin/padding) ke tepi container induk berwarna putih yang memiliki sudut siku (`cornerRadius = 0`)**. Sebaliknya, pada container yang memiliki sudut melengkung (`cornerRadius > 0`), seluruh elemen di dalamnya tampak rapi dan memiliki jarak (*padding*) yang proporsional.
- **Akar Masalah Teknis (*Root Cause*)**:
  1. Di engine FigCraft, perintah `node.create(type="frame")` secara default memberikan **warna latar Putih Solid (`#FFFFFF`)** dan sudut siku (`cornerRadius = 0`) apabila properti `"fill"` tidak dikirimkan di dalam `props`. Agar sebuah frame menjadi transparan, properti `"fill": "none"` wajib dikirim secara eksplisit.
  2. Pada [`figcraft_ui.py`](file:///C:/Users/muhammmad-zidane/.gemini/config/skills/figcraft-fast-skill/scripts/figcraft_ui.py) v3.0, metode `box(..., fill: Optional[str] = None)` dan `create_component(..., fill: Optional[str] = None)` hanya menulis:
     ```python
     if fill is not None:
         p["fill"] = fill
     ```
  3. Akibatnya, setiap kali skrip membuat **container pembungkus tata letak (*invisible layout wrapper*)** seperti baris/kolom flexbox (`HeroSection`, `HeroLeft`, `ShowcaseHeader`, `BestSellerCardsRow`, `TitleSection`, `FilterBar`, `ProductGridContainer`, `MidCol` di Cart Drawer, `MainSplit` & `PayText` di Checkout) dengan `fill=None` dan `padding=0`, Python **tidak mengirimkan key `"fill"`** ke JSON-RPC.
  4. Engine FigCraft pun merender seluruh *layout wrapper* transparan tersebut sebagai **kotak putih solid (`#FFFFFF`) bersudut siku tanpa padding (`padding=0`)**, sehingga elemen-elemen di dalamnya tampak menempel persis di garis tepi kotak putih tersebut.
- **Perbaikan di v3.1**:
  Mengubah penanganan `fill` pada `box()` dan `create_component()` di [`figcraft_ui.py`](file:///C:/Users/muhammmad-zidane/.gemini/config/skills/figcraft-fast-skill/scripts/figcraft_ui.py) menjadi:
  ```python
  p["fill"] = fill if fill is not None else "none"
  ```
  Dengan perubahan ini, setiap wrapper tata letak (`fill=None`) dijamin **100% transparan (`fills: []`)** dan tidak lagi memunculkan kotak putih siku bayangan (*ghost white box*).

---

### 2.2 Evaluasi Kelebihan & Celah (*Blind Spots*) pada `figcraft-fast-skill` v3.0

#### A. Keberhasilan Arsitektur v3.0
1. **Strict Error Handling (`strict=True` & `FigCraftError`)**:
   Terbukti sangat efektif. Saat pengujian *smoke test*, mode `strict=True` langsung menangkap 2 error nyata dari engine (`edit.delete` saat kanvas kosong & parameter `depth` yang tidak valid pada `node.get`) yang pada v2 diabaikan secara diam-diam.
2. **Perbaikan Text Wrapping & Auto-Measure `equasize_heights`**:
   Teks kartu ucapan di Layar 05 sudah membungkus 2 baris dengan utuh (`width=376`), dan `equasize_heights(card_ids, target_height=None)` berhasil membaca tinggi aktual dari engine secara otomatis.
3. **Penyimpanan `.figcraft` & Export Per Layar (`exports/*.png`)**:
   Menghasilkan file proyek [`berrycrumb_patisserie.figcraft`](file:///C:/dev/TokoKue/berrycrumb_patisserie.figcraft) dan 6 PNG resolusi penuh per layar yang sangat memudahkan inspeksi visual.

#### B. 4 Celah (*Blind Spots*) di v3.0 & Solusi Peningkatan di v3.1

| No | Celah / Kelemahan pada v3.0 | Mengapa Terjadi | Peningkatan pada v3.1 |
| :-: | :--- | :--- | :--- |
| **1** | **Bug `fill=None` pada `box()` memunculkan "Ghost White Box" bersudut siku** | `node.create(type="frame")` memberi fill `#FFFFFF` jika key `"fill"` tidak dikirim. | Mengirim `"fill": "none"` secara eksplisit ketika `fill is None` pada `box()` dan `create_component()`. |
| **2** | **`verify_layout()` tidak mendeteksi elemen yang mepet (`0px` padding) pada container berlatar/berborder** | `verify_layout()` v3.0 hanya mengecek apakah anak *keluar* melewati batas parent (`> 2.0px`), sehingga `x_child == x_parent` (`0.0px`) dianggap lulus walaupun container memiliki warna latar/border. | Menambahkan pemeriksaan **`unpadded_visual_box`** di `verify_layout()`: jika sebuah frame memiliki fill/stroke visual tetapi `padding == 0` dan `cornerRadius == 0` (indikasi *ghost wrapper*), atau teks menempel `< 2px` ke tepi container berborder/berlatar, auditor melaporkannya sebagai pelanggaran. |
| **3** | **Pemeriksaan *Sibling Overlap* di `verify_layout()` belum diimplementasikan** | Fungsi `_audit_node()` di v3.0 baru memeriksa *Child Overflow* dan *Zero-Size Node*. | Menambahkan deteksi **`sibling_overlap`** di `_audit_node()` yang menguji irisan *bounding box* (`absoluteBounds`) antar elemen sejajar (non-`absolute`) di dalam satu parent. |
| **4** | **Duplikasi Native Styles & File Legacy `C:\dev\TokoKue\figcraft_ui.py` (v2)** | `sync_to_figcraft_styles()` selalu memanggil `style.create` tanpa mengecek style yang sudah ada di dokumen, dan file `figcraft_ui.py` v2 masih tertinggal di folder proyek. | Memeriksa `style.list` sebelum membuat style baru (*idempotent sync*) di [`design_tokens.py`](file:///C:/Users/muhammmad-zidane/.gemini/config/skills/figcraft-fast-skill/scripts/design_tokens.py) serta menghapus file legacy `C:\dev\TokoKue\figcraft_ui.py`. |

---

## 3. Evaluasi terhadap PRD (`PRDBerryCrumbPatisserie.pdf`)

File referensi: [`PRDBerryCrumbPatisserie.pdf`](file:///C:/dev/TokoKue/PRDBerryCrumbPatisserie.pdf)

### 3.1 Kelebihan
- **Design Tokens Warna Sangat Lengkap**: Menyediakan Hex Code, nama token (`chocolate-dark`, `vanilla-cream`, `strawberry-ruby`, `strawberry-blush`, dll.), serta aturan penggunaannya pada komponen UI.
- **Spesifikasi Konten Realistis**: Seluruh opsi di *Custom Cake Builder* (Langkah 1–6), *Date & Slot Picker* (`09.00-12.00`, `13.00-16.00`, `16.00-19.00`), *Info Alergen*, hingga *Instruksi Kurir Kue Dingin* sudah tertulis konkret sehingga agen tidak perlu mengarang *dummy text* generik.

### 3.2 Catatan Perbaikan PRD
1. **Sinkronisasi Sitemap (Bagian 4) vs Spesifikasi Layar (Bagian 5)**:
   - Di Sitemap tertulis `6.0 Pelacak Status Pesanan (Live Order Tracker)`, namun di Bagian 5 hanya ada 5 sub-bagian (berhenti di `5.5 Checkout`). Sebaiknya ditambahkan bagian `5.6 Live Order Tracker` atau disesuaikan dengan 6 layar utama.
2. **Penambahan Tabel Skala Tipografi (Type Scale)**:
   - Mencantumkan ukuran font eksplisit (misal: `H1 = 42px/50px`, `H2 = 28px`, `Card Title = 17px`, `Body = 13px–14px`, `Badge = 11px`) akan membuat hasil render antar-layar semakin konsisten.

---

## 4. Evaluasi terhadap Prompt Pengguna

### 4.1 Kelebihan
- **Sangat Jelas & Terstruktur**: Memisahkan aturan eksekusi (*Fast Batch Rendering*), aturan warna, daftar 6 layar, batasan *Anti-Glitch*, dan langkah verifikasi (`export_page`).
- **Mengoreksi Celah PRD secara Efektif**: Menetapkan 6 layar spesifik (dengan menjadikan *Modal Quick View* sebagai Layar 03 tersendiri).
- **Feedback Visual yang Tajam**: Mengidentifikasi anomali visual spesifik (*"terjadi pada container yang memiliki sudut siku saja, yang memiliki sudut agak melengkung tidak terjadi hal ini"*) yang langsung mengarahkan ke akar masalah `fill="none"` pada `node.create(type="frame")`.
