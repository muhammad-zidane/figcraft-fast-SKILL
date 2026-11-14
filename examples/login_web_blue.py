"""
login_web_blue.py - Modern SaaS Web Login Page in Blue Theme for FigCraft.
Built using figcraft-fast-skill (v4.0) with Live Streaming mode (50ms),
auto-launch, Design Tokens, reusable UI components, and automated layout verification.
"""

from pathlib import Path
import sys
import os

# 1. Official Skill Modules Import (Prioritizes local development repo, fallbacks to global)
LOCAL_SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
GLOBAL_SCRIPTS = Path.home() / ".gemini" / "config" / "skills" / "figcraft-fast-skill" / "scripts"
SKILL_SCRIPTS = LOCAL_SCRIPTS if LOCAL_SCRIPTS.exists() else GLOBAL_SCRIPTS
sys.path.insert(0, str(SKILL_SCRIPTS))

from figcraft_ui import FigCraftClient, FigCraftError
from design_tokens import DesignTokens
from figcraft_components import UIComponents


def build_login_screen():
    print("=== Initializing FigCraft Client (Live Streaming 50ms, auto_launch=True) ===")
    client = FigCraftClient(
        host="127.0.0.1",
        port=7979,
        auto_batch=False,
        strict=True,
        live_select=True,
        step_delay_ms=50.0,
        auto_launch=True
    )

    # 2. Design Tokens - Modern Blue Theme
    blue_tokens = DesignTokens(
        brand_name="CloudPulse",
        bg_canvas="#F8FAFC",          # Slate 50 clean backdrop
        bg_card="#FFFFFF",            # Pure crisp white card surface
        text_primary="#0F172A",       # Slate 900
        text_muted="#64748B",         # Slate 500
        accent_custard="#E2E8F0",     # Slate 200 border / subtle divider
        accent_ruby="#2563EB",        # Royal Blue 600 (Primary Blue CTA)
        accent_blush="#DBEAFE",       # Soft Blue 100
        overlay_dark="#0F172A80",     # Dark Slate Overlay
        white="#FFFFFF",
        font_heading="Plus Jakarta Sans",
        font_body="Plus Jakarta Sans",
        size_h1=32.0,
        size_h2=24.0,
        size_h3=18.0,
        size_title=15.0,
        size_body=13.0,
        size_caption=11.0,
        radius_sm=8.0,
        radius_md=12.0,
        radius_lg=16.0,
        radius_xl=24.0,
        radius_pill=20.0,
        shadow_sm=[{"type": "dropShadow", "color": "#0F172A0A", "offset": [0, 2], "radius": 6}],
        shadow_md=[{"type": "dropShadow", "color": "#0F172A10", "offset": [0, 8], "radius": 24}],
        shadow_cta=[{"type": "dropShadow", "color": "#2563EB33", "offset": [0, 4], "radius": 12}],
    )

    ui = UIComponents(client, blue_tokens)

    # 3. Handle "Halaman FigCraft Baru"
    # Ensure or create a new dedicated page for this design
    page_name = "Login Web - Blue Theme"
    pages = client.execute("page.list", {})
    target_page = next((p for p in pages if p.get("name") == page_name), None) if isinstance(pages, list) else None

    if target_page:
        client.execute("page.select", {"id": target_page["id"]})
    else:
        new_p = client.execute("page.add", {"name": page_name})
        if isinstance(new_p, dict) and "id" in new_p:
            client.execute("page.select", {"id": new_p["id"]})

    # Clear canvas on this page & sync design tokens to native styles
    client.clear_canvas()
    blue_tokens.sync_to_figcraft_styles(client)
    print(f"  [OK] Page '{page_name}' prepared and styles synced.")

    # 4. Master Screen Frame (1440 x 900 Desktop Resolution)
    # Using horizontal layout with 2 columns: Hero Branding (580px) + Auth Form (860px)
    screen = client.create_frame(
        name="Web_Login_Screen",
        x=0,
        y=0,
        width=1440,
        height=900,
        fill=blue_tokens.bg_canvas
    )

    screen_row = client.box(
        parent=screen,
        name="Screen_Split_Layout",
        layout="horizontal",
        x=0,
        y=0,
        width=1440,
        height=900,
        gap=0,
        padding=0
    )

    # =========================================================================
    # LEFT COLUMN: Branding & Social Proof Hero Panel (580px x 900px)
    # =========================================================================
    left_hero = client.box(
        parent=screen_row,
        name="Hero_Branding_Panel",
        layout="vertical",
        width=580,
        height=900,
        padding=[48, 48, 48, 48],
        gap=32,
        mainAlign="space-between",
        crossAlign="min",
        fill="#1E3A8A"  # Deep Royal Blue
    )
    inner_hero_w = 580 - 48 - 48  # 484px

    # --- Hero Top: Brand Header ---
    brand_row = client.box(
        parent=left_hero,
        name="Brand_Header_Row",
        layout="horizontal",
        width=inner_hero_w,
        gap=14,
        crossAlign="center"
    )

    logo_icon = client.box(
        parent=brand_row,
        name="Logo_Badge",
        layout="horizontal",
        width=38,
        height=38,
        padding=[8, 8, 8, 8],
        mainAlign="center",
        crossAlign="center",
        cornerRadius=10,
        fill="#2563EB"
    )
    client.create_text(
        parent=logo_icon,
        text="✦",
        fontSize=18,
        fontStyle="Bold",
        fill="#FFFFFF",
        textAlign="center"
    )

    client.create_text(
        parent=brand_row,
        text="CloudFlow",
        fontSize=22,
        fontFamily="Plus Jakarta Sans",
        fontStyle="Bold",
        fill="#FFFFFF"
    )

    ui.badge(parent=brand_row, label="ENTERPRISE", variant="blush")

    # --- Hero Middle: Headline & Value Propositions ---
    hero_middle = client.box(
        parent=left_hero,
        name="Hero_Value_Prop",
        layout="vertical",
        width=inner_hero_w,
        gap=22
    )

    ui.pill(parent=hero_middle, label="🚀 Next-Gen Cloud Platform", active=True, variant="filter")

    client.create_text(
        parent=hero_middle,
        text="Manage multi-cloud infrastructure with unified intelligence.",
        width=inner_hero_w,
        fontSize=28,
        fontFamily="Plus Jakarta Sans",
        fontStyle="Bold",
        fill="#FFFFFF",
        lineHeight=36
    )

    client.create_text(
        parent=hero_middle,
        text="Automate deployment cycles, observe live cluster telemetry, and eliminate downtime with autonomous failover.",
        width=inner_hero_w,
        fontSize=13,
        fontFamily="Plus Jakarta Sans",
        fontStyle="Regular",
        fill="#BFDBFE",
        lineHeight=20
    )

    # Feature Checklist
    checklist_box = client.box(
        parent=hero_middle,
        name="Feature_Checklist",
        layout="vertical",
        width=inner_hero_w,
        gap=12
    )

    features = [
        "Instant zero-config Kubernetes clusters orchestration",
        "Sub-millisecond global edge telemetry & smart alerts",
        "SOC2 Type II, ISO 27001, and HIPAA compliant security"
    ]
    for feat_text in features:
        item_row = client.box(
            parent=checklist_box,
            name="Check_Item",
            layout="horizontal",
            width=inner_hero_w,
            gap=10,
            crossAlign="center"
        )
        chk_icon = client.box(
            parent=item_row,
            name="Check_Bullet",
            layout="horizontal",
            width=20,
            height=20,
            padding=[2, 4, 2, 4],
            mainAlign="center",
            crossAlign="center",
            cornerRadius=10,
            fill="#2563EB"
        )
        client.create_text(parent=chk_icon, text="✓", fontSize=10, fontStyle="Bold", fill="#FFFFFF")
        client.create_text(parent=item_row, text=feat_text, fontSize=12, fill="#E0E7FF")

    # --- Hero Bottom: Testimonial Proof Card ---
    proof_card = client.box(
        parent=left_hero,
        name="Testimonial_Card",
        layout="vertical",
        width=inner_hero_w,
        padding=[18, 20, 18, 20],
        gap=12,
        fill="#172554",       # Deep Navy Surface
        stroke="#2563EB",     # Electric Blue Border
        strokeWeight=1,
        cornerRadius=14
    )
    inner_card_w = inner_hero_w - 40  # 444px

    client.create_text(
        parent=proof_card,
        text="“CloudFlow cut our incident resolution latency by 72% across 14 global regions. It has become essential to our engineering reliability.”",
        width=inner_card_w,
        fontSize=12,
        fontStyle="Regular",
        fill="#E2E8F0",
        lineHeight=18
    )

    author_row = client.box(
        parent=proof_card,
        name="Author_Meta",
        layout="horizontal",
        width=inner_card_w,
        gap=10,
        crossAlign="center"
    )
    avatar = client.box(
        parent=author_row,
        name="Avatar_Circle",
        layout="horizontal",
        width=32,
        height=32,
        padding=[4, 4, 4, 4],
        mainAlign="center",
        crossAlign="center",
        cornerRadius=16,
        fill="#3B82F6"
    )
    client.create_text(parent=avatar, text="SC", fontSize=11, fontStyle="Bold", fill="#FFFFFF")

    author_txt = client.box(
        parent=author_row,
        name="Author_Info",
        layout="vertical",
        gap=2
    )
    client.create_text(parent=author_txt, text="Sarah Chen", fontSize=12, fontStyle="Bold", fill="#FFFFFF")
    client.create_text(parent=author_txt, text="VP Infrastructure, GlobalScale Ltd.", fontSize=10, fill="#93C5FD")


    # =========================================================================
    # RIGHT COLUMN: Authentication Form Panel (860px x 900px)
    # =========================================================================
    right_auth = client.box(
        parent=screen_row,
        name="Auth_Form_Panel",
        layout="vertical",
        width=860,
        height=900,
        padding=[40, 60, 40, 60],
        gap=24,
        mainAlign="space-between",
        crossAlign="center",
        fill="#F8FAFC"
    )
    inner_right_w = 860 - 60 - 60  # 740px

    # --- Top Navigation Bar ---
    top_nav = client.box(
        parent=right_auth,
        name="Top_Nav_Bar",
        layout="horizontal",
        width=inner_right_w,
        mainAlign="space-between",
        crossAlign="center"
    )

    sys_pill = client.box(
        parent=top_nav,
        name="System_Status",
        layout="horizontal",
        gap=6,
        padding=[6, 12, 6, 12],
        cornerRadius=14,
        fill="#EFF6FF",
        stroke="#BFDBFE",
        strokeWeight=1,
        crossAlign="center"
    )
    status_dot = client.box(
        parent=sys_pill,
        name="Green_Dot",
        width=8,
        height=8,
        cornerRadius=4,
        fill="#10B981"
    )
    client.create_text(parent=sys_pill, text="All systems operational", fontSize=11, fontStyle="Medium", fill="#1E40AF")

    signup_prompt = client.box(
        parent=top_nav,
        name="Signup_Prompt",
        layout="horizontal",
        gap=8,
        crossAlign="center"
    )
    client.create_text(parent=signup_prompt, text="Don't have an account?", fontSize=13, fill="#64748B")
    ui.button(parent=signup_prompt, label="Create Account", variant="soft", size="sm")

    # --- Center Login Card ---
    card_w = 440
    login_card = client.box(
        parent=right_auth,
        name="Login_Card",
        layout="vertical",
        width=card_w,
        padding=[36, 36, 36, 36],
        gap=18,
        fill="#FFFFFF",
        stroke="#E2E8F0",
        strokeWeight=1,
        cornerRadius=16,
        effects=blue_tokens.shadow_md
    )
    inner_card_w = card_w - 36 - 36  # 368px

    # Card Title Group
    card_head = client.box(
        parent=login_card,
        name="Card_Header",
        layout="vertical",
        width=inner_card_w,
        gap=6
    )
    client.create_text(
        parent=card_head,
        text="Welcome back",
        fontSize=24,
        fontFamily="Plus Jakarta Sans",
        fontStyle="Bold",
        fill="#0F172A",
        width=inner_card_w
    )
    client.create_text(
        parent=card_head,
        text="Please enter your enterprise credentials to continue.",
        fontSize=13,
        fontFamily="Plus Jakarta Sans",
        fontStyle="Regular",
        fill="#64748B",
        width=inner_card_w
    )

    # Social SSO Buttons Row
    sso_row = client.box(
        parent=login_card,
        name="SSO_Buttons_Row",
        layout="horizontal",
        width=inner_card_w,
        gap=12
    )
    btn_half_w = (inner_card_w - 12) / 2  # 178px

    btn_google = client.box(
        parent=sso_row,
        name="Btn_Google",
        layout="horizontal",
        width=btn_half_w,
        height=40,
        padding=[8, 12, 8, 12],
        mainAlign="center",
        crossAlign="center",
        fill="#FFFFFF",
        stroke="#CBD5E1",
        strokeWeight=1,
        cornerRadius=8
    )
    client.create_text(parent=btn_google, text="Google", fontSize=12, fontStyle="SemiBold", fill="#334155")

    btn_sso = client.box(
        parent=sso_row,
        name="Btn_SSO",
        layout="horizontal",
        width=btn_half_w,
        height=40,
        padding=[8, 12, 8, 12],
        mainAlign="center",
        crossAlign="center",
        fill="#FFFFFF",
        stroke="#CBD5E1",
        strokeWeight=1,
        cornerRadius=8
    )
    client.create_text(parent=btn_sso, text="Single Sign-On", fontSize=12, fontStyle="SemiBold", fill="#334155")

    # Divider Row
    div_row = client.box(
        parent=login_card,
        name="Divider_Row",
        layout="horizontal",
        width=inner_card_w,
        gap=10,
        crossAlign="center"
    )
    line_w = (inner_card_w - 150) / 2  # ~109px
    client.create_rect(parent=div_row, name="Div_Left", width=line_w, height=1, fill="#E2E8F0")
    client.create_text(parent=div_row, text="or sign in with email", fontSize=11, fill="#94A3B8")
    client.create_rect(parent=div_row, name="Div_Right", width=line_w, height=1, fill="#E2E8F0")

    # Form Fields
    form_fields = client.box(
        parent=login_card,
        name="Form_Fields_Group",
        layout="vertical",
        width=inner_card_w,
        gap=14
    )

    # Email Field
    email_group = client.box(parent=form_fields, name="Field_Email", layout="vertical", width=inner_card_w, gap=6)
    client.create_text(parent=email_group, text="Work Email", fontSize=12, fontStyle="SemiBold", fill="#1E293B", width=inner_card_w)
    ui.input_field(parent=email_group, value="alex.morgan@company.com", width=inner_card_w, active=True)

    # Password Field
    pass_group = client.box(parent=form_fields, name="Field_Password", layout="vertical", width=inner_card_w, gap=6)
    pass_label_row = client.box(parent=pass_group, name="Pass_Label_Row", layout="horizontal", width=inner_card_w, mainAlign="space-between", crossAlign="center")
    client.create_text(parent=pass_label_row, text="Password", fontSize=12, fontStyle="SemiBold", fill="#1E293B")
    client.create_text(parent=pass_label_row, text="Forgot password?", fontSize=12, fontStyle="SemiBold", fill="#2563EB")
    ui.input_field(parent=pass_group, value="••••••••••••", width=inner_card_w, active=False)

    # Remember Me Checkbox Row
    rem_row = client.box(
        parent=login_card,
        name="Remember_Me_Row",
        layout="horizontal",
        width=inner_card_w,
        gap=8,
        crossAlign="center"
    )
    chk_box = client.box(
        parent=rem_row,
        name="Checkbox",
        layout="horizontal",
        width=18,
        height=18,
        padding=[2, 2, 2, 2],
        mainAlign="center",
        crossAlign="center",
        cornerRadius=4,
        fill="#2563EB"
    )
    client.create_text(parent=chk_box, text="✓", fontSize=10, fontStyle="Bold", fill="#FFFFFF")
    client.create_text(parent=rem_row, text="Remember me on this trusted device (30 days)", fontSize=12, fill="#475569")

    # Primary Action Button
    ui.button(
        parent=login_card,
        label="Sign In to Dashboard",
        variant="primary",
        size="lg",
        width=inner_card_w
    )

    # Security Notice Under Card
    sec_row = client.box(
        parent=login_card,
        name="Security_Notice",
        layout="horizontal",
        width=inner_card_w,
        padding=[4, 0, 4, 0],
        mainAlign="center",
        crossAlign="center"
    )
    client.create_text(
        parent=sec_row,
        text="🔒 Protected by 256-bit TLS & Enterprise Identity Guard",
        fontSize=11,
        fill="#64748B",
        textAlign="center"
    )

    # --- Bottom Footer Links ---
    footer_bar = client.box(
        parent=right_auth,
        name="Footer_Links_Row",
        layout="horizontal",
        width=inner_right_w,
        gap=16,
        padding=[8, 12, 8, 12],
        mainAlign="center",
        crossAlign="center"
    )
    footer_items = ["Privacy Policy", "•", "Terms of Service", "•", "Trust Center", "•", "System Status"]
    for item in footer_items:
        color = "#94A3B8" if item == "•" else "#64748B"
        client.create_text(parent=footer_bar, text=item, fontSize=11, fill=color)

    # 5. Layout Audit Verification (MANDATORY: must achieve 0 violations)
    print("=== Running Layout Audit Verification ===")
    report = client.verify_layout([screen])
    print(f"Audit result: ok={report['ok']}, violation_count={report['violation_count']}")
    if not report["ok"]:
        for v in report["violations"]:
            print(f"  [VIOLATION] {v['kind']} in {v['node_name']}: {v['detail']}")
        raise FigCraftError(f"Layout audit failed with {report['violation_count']} violations")
    print("  [OK] 0 Violations! Layout verification passed flawlessly.")

    # 6. Save & Export Artifacts
    export_dir = Path(__file__).resolve().parent / "exports"
    export_dir.mkdir(parents=True, exist_ok=True)
    
    figcraft_file = export_dir / "login_web_blue.figcraft"
    save_res = client.save_file(str(figcraft_file))
    print(f"  [OK] Project saved to: {save_res['path']}")

    frame_exports = client.export_frames([screen], output_dir=str(export_dir))
    for fe in frame_exports:
        print(f"  [OK] Exported frame to: {fe['path']} ({fe['bytes']} bytes)")

    client.close()
    print("=== Execution Complete! Last flush latency: {:.1f} ms, Total RPC: {:.1f} ms ===".format(
        client.last_flush_ms, client.total_rpc_ms
    ))
    return frame_exports[0]["path"]


if __name__ == "__main__":
    build_login_screen()
