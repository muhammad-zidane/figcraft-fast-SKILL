---
name: figcraft-fast-skill
description: "High-performance batch UI/UX automation skill for FigCraft using atomic JSON-RPC over TCP port 7979 with strict error handling, design tokens, reusable components, and automated layout auditing."
---

# FigCraft Fast Automation Skill (v3.0)

Gunakan skill ini untuk merancang, membuat komponen, dan merender antarmuka UI/UX di FigCraft dengan kecepatan maksimal dan tanpa glitch visual.

## Lokasi Modul Resmi
Modul Python skill ini terpusat di:
```python
from pathlib import Path
import sys
SKILL_SCRIPTS = Path.home() / ".gemini" / "config" / "skills" / "figcraft-fast-skill" / "scripts"
sys.path.insert(0, str(SKILL_SCRIPTS))

from figcraft_ui import FigCraftClient, FigCraftError
from design_tokens import DesignTokens
from figcraft_components import UIComponents
```

## Arsitektur & Fitur Utama (v3.0)

1. **Strict Batch TCP JSON-RPC (`FigCraftClient`)**:
   - Berkomunikasi langsung via Raw TCP Socket (`127.0.0.1:7979`, `engine.execute`).
   - Default `strict=True` (`onError="abort"`). Setiap kesalahan RPC langsung memicu `FigCraftError`.
   - Mengukur waktu latensi transmisi batch nyata via `client.last_flush_ms` dan `client.total_rpc_ms`.

2. **Design Tokens & Native Styles (`design_tokens.py`)**:
   - Standarisasi warna palet, skala tipografi, border radius, dan drop shadow.
   - Pendaftaran otomatis ke panel *Styles* native FigCraft via `tokens.sync_to_figcraft_styles(client)`.

3. **Komponen Siap Pakai (`figcraft_components.py`)**:
   - `ui.button(parent, label, variant='primary'|'secondary'|'soft', size='sm'|'md'|'lg')`
   - `ui.pill(parent, label, active=False)`
   - `ui.badge(parent, label, variant='ruby'|'blush'|'custard'|'dark', floating=False)`
   - `ui.input_field(parent, value, width=400, multiline=False)` (Otomatis membungkus teks sehingga tidak pernah *overflow*)
   - `ui.card(parent, name, width=295, padding=16)`
   - `ui.divider(parent, width=300)`

4. **Pencegahan Glitch & Verifikasi Tata Letak Otomatis**:
   - `client.equasize_heights(card_refs, target_height=None)`: Menyelaraskan tinggi kartu dengan mengukur tinggi tertinggi (`max(height)`) secara dinamis.
   - `client.verify_layout(frame_refs, tolerance=2.0)`: Mengaudit pohon layer dari *overflow* batas parent atau ukuran 0px. **Wajib menghasilkan `0 violations`**.
   - `client.save_file(output_path)`: Menyimpan kanvas aktif ke file binary `.figcraft`.
   - `client.export_frames(frame_refs, output_dir)`: Mengekspor frame layar satu per satu ke direktori gambar PNG resolusi penuh.

## Pola Dasar Skrip Otomasi

```python
from pathlib import Path
import sys

SKILL_SCRIPTS = Path.home() / ".gemini" / "config" / "skills" / "figcraft-fast-skill" / "scripts"
sys.path.insert(0, str(SKILL_SCRIPTS))

from figcraft_ui import FigCraftClient
from design_tokens import DesignTokens
from figcraft_components import UIComponents

def main():
    client = FigCraftClient(host="127.0.0.1", port=7979, auto_batch=True, strict=True)
    tokens = DesignTokens()
    ui = UIComponents(client, tokens)

    # 1. Bersihkan kanvas & daftarkan styles
    client.clear_canvas()
    tokens.sync_to_figcraft_styles(client)

    # 2. Bangun screen frame
    screen = client.create_frame("Desktop_Screen", x=0, y=0, width=1440, height=900, fill=tokens.bg_canvas)
    
    # 3. Bangun layout & komponen
    row = client.box(parent=screen, name="Container", layout="horizontal", x=80, y=80, gap=24)
    c1 = ui.card(parent=row, name="Card_1", width=320)
    client.create_text(parent=c1, text="Judul Kartu", fontSize=18, fontStyle="Bold")
    ui.button(parent=c1, label="Beli Sekarang", variant="primary")

    # 4. Audit tata letak (Wajib 0 violations)
    report = client.verify_layout([screen])
    assert report["ok"], f"Layout violations found: {report['violations']}"

    # 5. Simpan & Ekspor
    client.save_file("./design_project.figcraft")
    client.export_page("./preview_all.png")
    client.export_frames([screen], output_dir="./exports")
    client.close()

if __name__ == "__main__":
    main()
```
