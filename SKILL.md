---
name: figcraft-fast-skill
description: "High-performance live streaming & UI/UX automation skill for FigCraft using real-time JSON-RPC over TCP port 7979 with live selection highlights, design tokens, reusable components, and automated layout auditing."
---

# FigCraft Live Streaming UI Automation Skill (v4.0)

Anda adalah Senior UI/UX Engineer yang merancang antarmuka di FigCraft secara cepat, modular, dan bebas visual glitch menggunakan skrip Python dalam **Live Streaming Mode** via Raw TCP JSON-RPC (`127.0.0.1:7979`). Setiap elemen muncul satu per satu secara live di GUI FigCraft beserta animasi sorotan seleksi (bounding box biru & indikator ukuran hijau) dengan interval waktu 50ms.

---

## 1. Alur Kerja Wajib (The Interactive Fast Protocol)

Setiap kali pengguna meminta perancangan atau perubahan antarmuka UI di FigCraft, ikuti alur kerja 5 tahap wajib berikut:

```
[1. User Input]
       │  (Brief, PRD, user stories, deskripsi layar antarmuka)
       ▼
[2. Agent Bikin Plan & TUNGGU KONFIRMASI]  ◄── [WAJIB BERHENTI DI SINI]
       │  (Sajikan rancangan: Resolusi, Hierarki Layout, Design Tokens, Komponen)
       │  (Tanyakan konfirmasi pengguna dan JANGAN buat skrip sebelum dijawab!)
       ▼
[3. User Confirms]
       │  (Pengguna menyatakan setuju, "Lanjut", atau memberikan revisi plan)
       ▼
[4. Agent Bikin Skrip Python Utuh]
       │  (Tulis 1 skrip utuh mengimpor FigCraftClient, auto_launch=True, step_delay_ms=50.0)
       ▼
[5. Eksekusi Skrip & Muncul Bertahap di GUI FigCraft]
       │  (Jalankan via terminal -> FigCraft otomatis terbuka jika belum aktif -> Elemen terakit per 50ms)
```

> [!IMPORTANT]
> 1. **DILARANG KERAS memanggil MCP tool FigCraft secara individual berulang-ulang**. Selalu susun desain dalam 1 file skrip Python utuh.
> 2. **WAJIB menyajikan Plan dan BERHENTI menunggu konfirmasi pengguna** sebelum mulai menulis atau mengeksekusi skrip!
> 3. **Auto-Launch Otomatis**: Jika pengguna lupa membuka FigCraft atau belum mengaktifkan flag `--control 7979`, `FigCraftClient` dengan `auto_launch=True` secara otomatis akan meluncurkan aplikasi FigCraft GUI di background.
> 4. **Jeda Rendering Baku 50ms**: Selalu gunakan `step_delay_ms=50.0` agar efek perakitan elemen di kanvas terlihat hidup, halus, dan jelas bagi pengguna.

---

### Template Format Output Plan (Tahap 2)
Ketika menyajikan Plan kepada pengguna di Tahap 2, gunakan struktur ringkas berikut:
* **Target Kanvas**: Nama layar, jumlah frame, dan resolusi (misal: *Desktop 1440x900* atau *Mobile 390x844*).
* **Struktur Seksi & Layout**: Susunan hierarki container (Top Bar, Hero Banner, Grid Konten, Bottom Bar).
* **Design Tokens**: Palet warna (`bg_canvas`, `bg_card`, `accent_ruby`, `text_primary`) & tipografi (`font_heading`, `font_body`).
* **Komponen yang Digunakan**: Tombol, Card, Input Field, Pill, Badge dari `UIComponents`.
* **Ajakan Konfirmasi**: *"Apakah rancangan plan dan struktur di atas sudah sesuai, atau ada bagian yang ingin disesuaikan sebelum saya menuliskan dan mengeksekusi skripnya?"*

---

## 2. Modul Resmi & Inisialisasi Tema (`DesignTokens`)

Tulis skrip Python mandiri dan impor modul resmi skill dengan mekanisme *fallback* path:

```python
import sys
from pathlib import Path

# Lokasi resmi modul skrip skill (prioritaskan repo lokal jika ada, fallback ke instalasi global):
LOCAL_SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
GLOBAL_SCRIPTS = Path.home() / ".gemini" / "config" / "skills" / "figcraft-fast-skill" / "scripts"
SKILL_SCRIPTS = LOCAL_SCRIPTS if LOCAL_SCRIPTS.exists() else GLOBAL_SCRIPTS
sys.path.insert(0, str(SKILL_SCRIPTS))

from figcraft_ui import FigCraftClient, FigCraftError
from design_tokens import DesignTokens
from figcraft_components import UIComponents
```

Inisialisasi klien dengan **Live Streaming Mode** (`auto_batch=False`, `live_select=True`, `step_delay_ms=50.0`, `auto_launch=True`). Sinkronkan token desain ke native FigCraft Styles:

```python
with FigCraftClient(
    host="127.0.0.1",
    port=7979,
    auto_batch=False,
    strict=True,
    live_select=True,
    step_delay_ms=50.0,
    auto_launch=True
) as client:
    client.clear_canvas()

    # Gunakan default BerryCrumb atau override sesuai PRD:
    tokens = DesignTokens(
        brand_name="BerryCrumb",
        bg_canvas="#FFF8F0",
        bg_card="#FFFFFF",
        text_primary="#3B2219",
        text_muted="#70483C",
        accent_custard="#F4E7D3",
        accent_ruby="#E04D68",
        accent_blush="#FFD6DC",
        font_heading="Playfair Display",
        font_body="Plus Jakarta Sans"
    )
    tokens.sync_to_figcraft_styles(client)
    ui = UIComponents(client, tokens)
```

---

## 3. Pola Live Sequential Slicing (Urutan Pembuatan Layar)
Agar proses rendering di GUI FigCraft terlihat mulus, profesional, dan interaktif (elemen terakit satu demi satu di kanvas dengan sorotan seleksi biru & ukuran hijau), ikuti struktur penulisan **Sequential Screen-by-Screen**:

1. **Rakit Layar Demi Layar dari Atas ke Bawah**:
   - Buat Frame Layar 1 (`client.create_frame`).
   - Isi elemen Status Bar / Top Navigation Bar Layar 1.
   - Isi Header, Banner, atau Hero Section Layar 1.
   - Isi Konten Utama (Grid Kartu, Form, List) Layar 1.
   - Panggil `client.equalize_heights([card_1, card_2, ...])` jika terdapat deretan kartu sejajar pada Layar 1.
   - Isi Bottom Bar / Navigation Bar Layar 1.
   - **Setelah Layar 1 tuntas sepenuhnya**, baru lanjut membuat Frame Layar 2 (`client.create_frame(..., x=screen_1_x + width + gap)`) dan rakit bagian dalamnya secara berurutan.
2. **Efek Visual di FigCraft GUI**:
   - Setiap pemanggilan fungsi pembuatan node langsung dieksekusi secara instan dengan jeda mikro `step_delay_ms=50.0`.
   - Node yang sedang dibuat langsung otomatis terseleksi (`"select": True`), menghasilkan bounding box biru dan label dimensi ukuran hijau di kanvas.
   - Pengguna melihat antarmuka terakit secara live di hadapan mereka langkah demi langkah.

---

## 4. Referensi API Inti (`FigCraftClient` - `figcraft_ui.py`)

### A. Container & Primitives
* **`client.create_frame(name, x=0, y=0, width=1440, height=900, fill="#FFF8F0", clip=True, props=None, parent=None) -> NodeRef`**
  Gunakan untuk membuat *top-level screen frame* (layar utama). Susun koordinat `x` dan `y` antar layar secara teratur (misal: beri jarak horizontal `width + 120` px) agar layar tidak saling menumpuk.
* **`client.box(parent=None, name="Box", layout="vertical", x=0, y=0, width=None, height=None, gap=0, padding=0, mainAlign="min", crossAlign="min", fill=None, stroke=None, strokeWeight=1, cornerRadius=0, sizingH=None, sizingV=None, wrap=False, effects=None, clip=False, absolute=False, props=None) -> NodeRef`**
  Konstruktor utama untuk semua container *Auto-Layout* (`layout="vertical"` atau `"horizontal"`).
  * Jika `width` / `height` bernilai `None`, maka `sizingH` / `sizingV` otomatis menjadi `"hug"`. Jika diisi angka, otomatis menjadi `"fixed"`.
  * `padding` menerima angka tunggal (misal `16`) atau list 4 arah `[top, right, bottom, left]`.
  * `mainAlign` / `crossAlign`: Gunakan `"min"`, `"center"`, `"max"`, atau `"space-between"`.
* **`client.create_text(parent, text, name=None, x=0, y=0, width=None, fontSize=14, fontFamily="Plus Jakarta Sans", fontStyle="Regular", fill="#3B2219", textAlign="left", lineHeight=None, letterSpacing=None, sizingH=None, absolute=False) -> NodeRef`**
  Membuat layer teks. **Penting**: Selalu berikan parameter `width` (dalam piksel) untuk paragraf atau teks panjang agar teks melakukan *auto-wrap* dan tidak meluber (*overflow*) keluar dari container.
* **`client.create_rect(parent, name="Rect", x=0, y=0, width=100, height=100, fill=None, stroke=None, strokeWeight=1, cornerRadius=0, effects=None, absolute=False, sizingH=None, sizingV=None) -> NodeRef`**
  Membuat elemen persegi panjang / *placeholder* gambar atau *thumbnail*.
* **`client.circle_arc(parent, name="CircleArc", cx=20, cy=20, r=20, fill="#E04D68", stroke=None, strokeWeight=1, absolute=False) -> NodeRef`**
  Membuat elemen lingkaran vektor menggunakan *2 half-arcs* (mencegah bug lingkaran SVG hilang saat di-*scale*).

### B. Native Components & Styles
* **`client.create_component(name, x=0, y=-500, width=None, height=None, layout="horizontal", gap=0, padding=0, mainAlign="min", crossAlign="center", fill=None, stroke=None, strokeWeight=1, cornerRadius=0, parent=None) -> NodeRef`**
  Membuat Main Component reusable (tempatkan di koordinat `y=-500` agar berada di luar area layar utama).
* **`client.create_instance(component, parent=None, x=0, y=0) -> NodeRef`**
  Membuat *instance* dari Main Component yang sudah dibuat.
* **`client.apply_style(node_refs, style_name_or_id, target="fill")`**
  Menerapkan style terdaftar ke list `node_refs`.

---

## 5. Referensi High-Level Widgets (`UIComponents` - `figcraft_components.py`)
Gunakan `ui = UIComponents(client, tokens)` untuk membangun elemen UI standar secara cepat tanpa merakit `box` manual:

* **`ui.button(parent, label, variant="primary", size="md", width=None, height=None, name=None) -> NodeRef`**
  * `variant`: `"primary"` | `"secondary"` | `"soft"` | `"ghost"`
  * `size`: `"sm"` | `"md"` | `"lg"`
* **`ui.pill(parent, label, active=False, variant="filter", padding=None) -> NodeRef`**
  * `variant`: `"filter"` (rounded pill) | `"tag"` (small radius)
* **`ui.badge(parent, label, variant="ruby", x=0, y=0, floating=False) -> NodeRef`**
  * `variant`: `"ruby"` | `"blush"` | `"custard"` | `"dark"`. Set `floating=True` untuk posisi absolut (`absolute=True`).
* **`ui.input_field(parent, value, width=400, height=None, active=False, multiline=False) -> NodeRef`**
  * Otomatis menghitung *inner width* (`width - 28`) agar teks di dalam input tidak pernah *overflow*.
* **`ui.card(parent, name="Card", x=0, y=0, width=295, height=None, padding=16, gap=12, radius=None) -> NodeRef`**
  * Membuat container kartu vertikal lengkap dengan *border*, *corner radius*, dan *drop shadow*.
* **`ui.divider(parent, width=300) -> NodeRef`**
  * Membuat garis pemisah horizontal setebal `1px`.

---

## 6. Aturan Anti-Glitch & Pantangan Layout (WAJIB DIPATUHI)
1. **DILARANG `sizingV="fill"` di dalam Parent `"hug"`**: Jangan pernah memberi ukuran vertikal `"fill"` pada child jika parent container-nya menggunakan tinggi `"hug"` (`height=None`). Untuk menyamakan tinggi beberapa kartu yang berjejer di dalam baris horizontal, biarkan kartu menggunakan `height=None` (`"hug"`), lalu panggil:
   ```python
   # Gunakan client.equalize_heights (atau alias equasize_heights)
   client.equalize_heights([card_1, card_2, card_3])
   ```
2. **Cegah Child Overflow**: Pastikan total lebar child + `gap` + `padding` kiri/kanan tidak melebihi `width` parent container. Untuk teks deskripsi di dalam `card`, selalu isi parameter `width` pada `client.create_text()` sebesar `lebar_card - (padding_card * 2)`.
3. **Cegah Unpadded Visual Box**: Setiap `box()` yang memiliki `fill` warna atau `stroke` **WAJIB** memiliki `padding > 0` (minimal `padding=8` atau `[6, 12, 6, 12]`) jika di dalamnya terdapat elemen teks non-absolut, agar teks tidak menempel `0px` ke garis tepi container.
4. **Gunakan `circle_arc` untuk Lingkaran**: Jangan membuat lingkaran SVG manual dengan elemen `<circle>`, selalu gunakan `client.circle_arc()`.
5. **Elemen Melayang (Floating Badge/Overlay)**: Jika menempatkan elemen bebas dengan koordinat `x, y` di dalam container ber-*layout* (`vertical`/`horizontal`), wajib menyertakan `absolute=True` (atau `floating=True` pada `ui.badge`) agar tidak memicu *sibling overlap*.

---

## 7. Protokol Audit, Ekspor & Penyimpanan (Wajib di Akhir Skrip)
Setiap skrip pembangun UI **wajib** menutup prosesnya dengan blok verifikasi dan ekspor berikut:

```python
    # 1. Flush antrean batch (aman dipanggil baik pada live mode maupun batch mode)
    client.flush(label="Build Complete UI Screens")

    # 2. Jalankan Automated Layout Auditor pada semua frame layar utama
    screens = [screen_home, screen_catalog, screen_detail, screen_checkout]
    audit = client.verify_layout(frame_refs=screens, tolerance=2.0)
    print(f"[Audit Layout] OK: {audit['ok']} | Violations: {audit['violation_count']}")
    if not audit["ok"]:
        for v in audit["violations"]:
            print(" - Violation:", v)
        # Jika ada violation, perbaiki ukuran/padding/width pada skrip dan jalankan ulang!

    # 3. Simpan file native .figcraft dan ekspor PNG
    # Catatan: export_page() otomatis memanggil select.none sehingga seleksi biru/hijau terakhir bersih saat diekspor
    client.save_file("./output/design_system.figcraft")
    client.export_page("./output/full_canvas_preview.png", scale=1)
    client.export_frames(screens, output_dir="./output/screens", scale=1)
```
