"""
smoke_test.py - Automated Verification Suite for figcraft-fast-skill v3.0 (Fitur #1-#8).
"""

import os
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from figcraft_ui import FigCraftClient, FigCraftError
from design_tokens import DesignTokens
from figcraft_components import UIComponents


def run_smoke_test():
    print("=== Running figcraft-fast-skill v3.0 Smoke Test ===")
    client = FigCraftClient(host="127.0.0.1", port=7979, auto_batch=True, strict=True)
    tokens = DesignTokens()
    ui = UIComponents(client, tokens)

    client.clear_canvas()

    # 1. Test Native Styles (#7) & Tokens (#5)
    tokens.sync_to_figcraft_styles(client)

    # 2. Test Native Component & Instance (#8)
    master_badge = client.create_component(
        name="MasterPromoBadge",
        x=0, y=-200,
        padding=[6, 14, 6, 14],
        fill=tokens.accent_ruby,
        cornerRadius=12
    )
    client.create_text(parent=master_badge, text="★ PROMO", fontSize=11, fontStyle="Bold", fill="#FFFFFF")

    # 3. Test Frame, Reusable Components (#6), and Auto-Measure equasize_heights
    screen = client.create_frame("SmokeTest_Screen", x=0, y=0, width=800, height=500, fill=tokens.bg_canvas)
    row = client.box(parent=screen, name="CardRow", layout="horizontal", x=40, y=40, gap=20)

    c1 = ui.card(parent=row, name="ShortCard", width=240, height=None)
    client.create_text(parent=c1, text="Short Card", fontSize=16, fontStyle="Bold")
    ui.button(parent=c1, label="Action", variant="primary", size="sm")

    c2 = ui.card(parent=row, name="TallCard", width=240, height=None)
    client.create_text(parent=c2, text="Tall Card With Extra Lines", width=208, fontSize=16, fontStyle="Bold")
    ui.input_field(parent=c2, value="Wrapped multiline text inside input field so it never overflows.", width=208, multiline=True)
    client.create_instance(component=master_badge, parent=c2)

    # Auto-measure equalization (target_height=None)
    eq_h = client.equasize_heights([c1, c2], target_height=None)
    assert eq_h > 100.0, f"Expected auto-measured height > 100, got {eq_h}"
    print(f"  [OK] equasize_heights auto-measured height = {eq_h}px")

    # 4. Test Automated Layout Verifier (#3 - v3.1 with unpadded_visual_box & sibling_overlap)
    report = client.verify_layout([screen])
    assert report["ok"], f"Layout verification failed: {report['violations']}"
    print(f"  [OK] verify_layout passed with {report['violation_count']} violations")

    # Verify that unpadded_visual_box is caught if a filled box has 0 padding around text
    bad_box = client.box(parent=screen, name="BadUnpaddedBox", x=40, y=380, padding=0, fill="#FFFFFF")
    client.create_text(parent=bad_box, text="Flush Text Without Padding", fontSize=12)
    bad_report = client.verify_layout([screen])
    assert not bad_report["ok"] and any(v["kind"] == "unpadded_visual_box" for v in bad_report["violations"]), (
        f"Expected unpadded_visual_box violation, got: {bad_report}"
    )
    client.execute("edit.delete", {"ids": [client.resolve_id(bad_box)]})
    print("  [OK] verify_layout accurately detected unpadded_visual_box violation")

    # 5. Test Save File (#1) & Export Frames (#4)
    tmp_dir = SCRIPT_DIR.parent / "examples" / "_tmp_test"
    save_res = client.save_file(str(tmp_dir / "smoke_test.figcraft"))
    assert os.path.exists(save_res["path"]), "Saved .figcraft file not found"
    print(f"  [OK] save_file written to {save_res['path']}")

    frames_res = client.export_frames([screen], output_dir=str(tmp_dir / "exports"))
    assert len(frames_res) == 1 and os.path.exists(frames_res[0]["path"]), "Exported frame PNG not found"
    print(f"  [OK] export_frames written ({frames_res[0]['bytes']} bytes) | Last batch flush: {client.last_flush_ms:.1f} ms")

    client.clear_canvas()
    client.close()
    print("=== ALL SMOKE TESTS PASSED SUCCESSFULLY ===")


if __name__ == "__main__":
    run_smoke_test()
