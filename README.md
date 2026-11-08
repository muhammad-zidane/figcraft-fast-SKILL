# FigCraft Fast Skill (v3.1) 🚀

> **High-Performance Batch UI/UX Automation Skill for FigCraft using atomic JSON-RPC over TCP port 7979 with strict error handling, design tokens, reusable components, and automated layout auditing.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FigCraft Compatibility](https://img.shields.io/badge/FigCraft-Engine%20v1.0%2B-orange.svg)](https://figcraft.app/)

---

## 📌 Latar Belakang & Masalah yang Diselesaikan

Merancang antarmuka (UI/UX) di canvas FigCraft melalui AI Agent sering kali menghadapi tantangan:
1. **Panggilan RPC Sekuensial**: Mengirim command pembuatan layer satu per satu memakan waktu lama (~6+ detik untuk ratusan layer) dan memenuhi riwayat Undo.
2. **Glitch Ukuran & Hug-Content**: Parameter default sering kali membuat elemen teks, badge, dan pill tag berubah menjadi kotak persegi kaku (`100x100px`).
3. **Anomali Container Bersudut Siku (*Ghost White Box*)**: Engine FigCraft otomatis memberikan warna latar putih solid (`#FFFFFF`) pada frame pembungkus flexbox jika tidak dikirimkan `"fills": []` secara eksplisit, menyebabkan elemen di dalamnya tampak menempel tanpa margin.
4. **Child Overflow & Text Clipping**: Teks panjang sering meluap dari batas parent tanpa terdeteksi jika tidak ada auditor tata letak.

**`figcraft-fast-SKILL`** hadir sebagai solusi produksi terpadu:
- ⚡ **Atomic Batching**: Merender seluruh halaman web (~400 layer) dalam **< 0.3 detik** lewat 1 langkah Undo.
- 🎨 **Design Tokens & Native Styles**: Sinkronisasi warna dan tipografi langsung ke panel *Styles* FigCraft.
- 🧩 **UI Components Library**: Komponen tombol, pill tag, badge status, form input, dan card siap pakai yang otomatis *hug-content*.
- 🛡️ **Automated Layout Auditor (`verify_layout`)**: Mendeteksi *child overflow*, *zero-size layer*, *sibling overlap*, dan *unpadded visual box* secara otomatis.
- 💾 **File Persistence & Per-Frame Export**: Menyimpan ke format binary `.figcraft` dan mengekspor setiap top-level frame ke PNG beresolusi penuh.

---

## 📁 Struktur Repository

```text
figcraft-fast-SKILL/
├── SKILL.md                       # Instruksi skill resmi untuk AI Agent / Antigravity
├── Evaluasi.md                    # Laporan evaluasi teknis, analisis root cause, dan PRD audit
├── scripts/                       # Modul Python inti skill
│   ├── figcraft_ui.py             # Core TCP JSON-RPC client, batching, styles & layout auditor
│   ├── design_tokens.py          # Palet warna, tipografi, radii, shadow & style sync
│   ├── figcraft_components.py     # Library komponen: Button, Pill, Badge, Input, Card, Divider
│   └── smoke_test.py              # Test suite otomatis memvalidasi seluruh fitur #1-#8
├── examples/                      # Contoh implementasi end-to-end
│   ├── build_berrycrumb_screens.py # Skrip 6 layar responsif toko kue BerryCrumb Patisserie
│   ├── PRDBerryCrumbPatisserie.pdf # Acuan PRD lengkap
│   └── berrycrumb_preview.png      # Hasil render gabungan 6 layar
├── .gitignore
├── LICENSE
└── README.md
```

---

## 🚀 Panduan Memulai Cepat

### 1. Prasyarat
- Python 3.10 atau lebih baru.
- Aplikasi Desktop **FigCraft** berjalan dengan argumen control port:
  ```powershell
  figcraft --control 7979
  ```

### 2. Instalasi Skill ke Antigravity / Gemini CLI
Salin isi folder repository ini ke direktori skill kustom Anda:
- **Windows**: `%USERPROFILE%\.gemini\config\skills\figcraft-fast-skill\`
- **Linux / macOS**: `~/.gemini/config/skills/figcraft-fast-skill/`

Atau impor langsung modul `scripts/` di dalam skrip Python proyek Anda:
```python
from pathlib import Path
import sys

# Tambahkan path scripts
SKILL_DIR = Path.home() / ".gemini" / "config" / "skills" / "figcraft-fast-skill" / "scripts"
sys.path.insert(0, str(SKILL_DIR))

from figcraft_ui import FigCraftClient
from design_tokens import DesignTokens
from figcraft_components import UIComponents
```

---

## 💡 Contoh Penggunaan

```python
from figcraft_ui import FigCraftClient
from design_tokens import DesignTokens
from figcraft_components import UIComponents

def main():
    # 1. Inisialisasi klien (koneksi TCP ke 127.0.0.1:7979)
    client = FigCraftClient(host="127.0.0.1", port=7979, auto_batch=True, strict=True)
    tokens = DesignTokens()
    ui = UIComponents(client, tokens)

    # 2. Bersihkan canvas & daftarkan Styles native
    client.clear_canvas()
    tokens.sync_to_figcraft_styles(client)

    # 3. Buat Frame Layar Utama (1440x900)
    screen = client.create_frame("Desktop_Screen", x=0, y=0, width=1440, height=900, fill=tokens.bg_canvas)

    # 4. Bangun Layout & Komponen
    row = client.box(parent=screen, name="CardRow", layout="horizontal", x=80, y=100, gap=24)
    
    card1 = ui.card(parent=row, name="ProductCard", width=300)
    client.create_text(parent=card1, text="Artisanal French Pastry", fontSize=18, fontStyle="Bold")
    ui.button(parent=card1, label="Beli Sekarang", variant="primary")

    # 5. Audit Layout (Wajib 0 Violations)
    report = client.verify_layout([screen])
    assert report["ok"], f"Layout violations found: {report['violations']}"
    print(f"✓ Layout verified with 0 violations!")

    # 6. Simpan File Desain & Ekspor PNG
    client.save_file("./output_design.figcraft")
    client.export_page("./preview.png")
    client.export_frames([screen], output_dir="./exports")

    client.close()

if __name__ == "__main__":
    main()
```

---

## 🧪 Menjalankan Verifikasi Suite (Smoke Test)

Pastikan aplikasi FigCraft aktif di port `7979`, lalu jalankan:
```powershell
python scripts/smoke_test.py
```

Jika berhasil, output akan menampilkan:
```text
=== Running figcraft-fast-skill v3.0 Smoke Test ===
  [OK] equasize_heights auto-measured height = 156.0px
  [OK] verify_layout passed with 0 violations
  [OK] verify_layout accurately detected unpadded_visual_box violation
  [OK] save_file written to .../smoke_test.figcraft
  [OK] export_frames written ...
=== ALL SMOKE TESTS PASSED SUCCESSFULLY ===
```

---

## 📄 Lisensi

Proyek ini dilisensikan di bawah [MIT License](LICENSE).
