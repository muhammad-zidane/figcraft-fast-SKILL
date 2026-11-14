# FigCraft Fast Skill (v4.0)

> **High-performance Live Streaming & Atomic Batch UI/UX automation skill for FigCraft over TCP JSON-RPC (port `7979`) with auto-launch, live selection highlights, design tokens, reusable components, and automated layout auditing.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![CI](https://github.com/muhammad-zidane/figcraft-fast-SKILL/actions/workflows/ci.yml/badge.svg)](https://github.com/muhammad-zidane/figcraft-fast-SKILL/actions/workflows/ci.yml)

---

## Ringkasan Fitur Utama (v4.0)

`figcraft-fast-SKILL` menyediakan library Python zero-dependency (`stdlib` only) dan protokol instruksi AI Agent ([SKILL.md](SKILL.md)) untuk merancang antarmuka UI/UX di **FigCraft** tanpa visual glitch:

- **Live Streaming Mode (Default v4.0)**: `auto_batch=False`, `live_select=True`, dan `step_delay_ms=50.0` merakit elemen satu per satu secara langsung di kanvas GUI dengan sorotan seleksi aktif.
- **Auto-Launch Engine (`auto_launch=True`)**: Secara otomatis mendeteksi dan meluncurkan aplikasi FigCraft dengan `--control <port>` jika engine belum berjalan.
- **Atomic Batch Mode (`auto_batch=True`)**: Mendukung eksekusi ratusan layer dalam satu panggilan `command.batch` (`onError="abort" | "continue"`) dengan 1 langkah Undo.
- **Hardened Transport & Error Diagnostics**: Korelasi ID JSON-RPC, validasi buffer stream, rollback/snapshot `last_failed_batch`, serta `last_error` & `last_failure_stage`.
- **Design Tokens & Native Styles**: Sinkronisasi warna dan tipografi langsung ke panel *Styles* FigCraft via [design_tokens.py](scripts/design_tokens.py).
- **UI Components Library**: Widget siap pakai (`button`, `pill`, `badge`, `input_field`, `card`, `divider`) dengan *hug-content* otomatis di [figcraft_components.py](scripts/figcraft_components.py).
- **Automated Layout Auditor (`verify_layout`)**: Pemeriksaan rekursif untuk *child overflow*, *zero-size layer*, *sibling overlap*, dan *unpadded visual box*.
- **File Persistence & Per-Frame Export**: Penyimpanan proyek `.figcraft` dan ekspor PNG per layar (`export_frames`) maupun seluruh kanvas (`export_page`).

---

## Struktur Repository

```text
figcraft-fast-SKILL/
├── .github/
│   ├── workflows/ci.yml               # GitHub Actions CI (unittest & py_compile)
│   └── PULL_REQUEST_TEMPLATE.md
├── SKILL.md                           # Protokol resmi v4.0 untuk AI Agent / Antigravity
├── README.md                          # Dokumentasi utama repository
├── CHANGELOG.md                       # Riwayat rilis (v3.1 -> v4.0)
├── CONTRIBUTING.md                    # Panduan kontribusi & pengujian
├── Evaluasi.md                        # Evaluasi teknis & analisis root cause awal
├── scripts/
│   ├── figcraft_ui.py                 # Core TCP JSON-RPC client, auto-launch, live/batch & verify_layout
│   ├── design_tokens.py               # Palet warna, tipografi, radii, shadow & style sync
│   ├── figcraft_components.py         # Library komponen UI high-level
│   ├── smoke_test.py                  # End-to-end smoke test terhadap engine FigCraft aktif
│   ├── test_socket_lifecycle.py       # Unit test lifecycle soket & auto-launch (mock)
│   ├── test_transport_reliability.py  # Unit test transport & korelasi ID JSON-RPC (mock)
│   ├── test_batch_reliability.py      # Unit test batch queue, strict/loose & live mode (mock)
│   └── test_verify_layout.py          # Unit test auditor verify_layout & validasi bounds (mock)
├── examples/
│   ├── login_web_blue.py              # Contoh v4.0 Live Streaming (SaaS Web Login Blue Theme)
│   ├── build_berrycrumb_screens.py    # Contoh v3.1 Atomic Batch (6 layar BerryCrumb Patisserie)
│   ├── PRDBerryCrumbPatisserie.pdf    # Dokumen acuan PRD contoh BerryCrumb
│   ├── berrycrumb_preview.png         # Preview hasil ekspor BerryCrumb
│   └── exports/
│       └── 01_Web_Login_Screen.png    # Preview hasil ekspor login_web_blue.py
├── .gitattributes
├── .gitignore
└── LICENSE
```

---

## Panduan Memulai Cepat

### 1. Prasyarat
- **Python 3.10+** (tanpa paket pihak ketiga tambahan).
- **FigCraft Desktop App** (terpasang di mesin untuk auto-launch, atau berjalan manual dengan `figcraft --control 7979`).

### 2. Instalasi Skill ke Antigravity / Gemini CLI
Salin isi repository ini ke direktori skill kustom Anda:
- **Windows**: `%USERPROFILE%\.gemini\config\skills\figcraft-fast-skill\`
- **Linux / macOS**: `~/.gemini/config/skills/figcraft-fast-skill/`

### 3. Contoh Penggunaan (v4.0 Live Streaming Mode)

```python
from pathlib import Path
import sys

LOCAL_SCRIPTS = Path(__file__).resolve().parent / "scripts"
GLOBAL_SCRIPTS = Path.home() / ".gemini" / "config" / "skills" / "figcraft-fast-skill" / "scripts"
sys.path.insert(0, str(LOCAL_SCRIPTS if LOCAL_SCRIPTS.exists() else GLOBAL_SCRIPTS))

from figcraft_ui import FigCraftClient
from design_tokens import DesignTokens
from figcraft_components import UIComponents


def main():
    # Default v4.0: Live Streaming (50ms) + auto_launch=True
    with FigCraftClient(
        host="127.0.0.1",
        port=7979,
        auto_batch=False,
        strict=True,
        live_select=True,
        step_delay_ms=50.0,
        auto_launch=True,
    ) as client:
        tokens = DesignTokens()
        ui = UIComponents(client, tokens)

        client.clear_canvas()
        tokens.sync_to_figcraft_styles(client)

        screen = client.create_frame("Desktop_Screen", x=0, y=0, width=1440, height=900, fill=tokens.bg_canvas)
        row = client.box(parent=screen, name="CardRow", layout="horizontal", x=80, y=100, gap=24)

        card = ui.card(parent=row, name="ProductCard", width=300)
        client.create_text(parent=card, text="Artisanal French Pastry", fontSize=18, fontStyle="Bold")
        ui.button(parent=card, label="Beli Sekarang", variant="primary")

        report = client.verify_layout([screen])
        assert report["ok"], f"Layout violations found: {report['violations']}"

        client.save_file("./output/output_design.figcraft")
        client.export_frames([screen], output_dir="./output/exports")


if __name__ == "__main__":
    main()
```

Untuk **Atomic Batch Mode** (eksekusi massal dalam 1 transaksi Undo), kirim `auto_batch=True` dan akhiri dengan `client.flush()`.

---

## Pengujian (Testing)

### Unit Test Suite (Tanpa Memerlukan FigCraft Engine)
Seluruh unit test menggunakan mock socket/process dan berjalan di CI:

```powershell
python -m unittest discover -s scripts -p "test_*.py" -v
```

### Live Smoke Test (Memerlukan FigCraft Engine di Port `7979`)

```powershell
python scripts/smoke_test.py
```

---

## Lisensi

Proyek ini dilisensikan di bawah [MIT License](LICENSE).
