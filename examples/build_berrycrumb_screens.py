"""
build_berrycrumb_screens.py
Renders all 6 responsive web interface screens for BerryCrumb Patisserie in FigCraft.
Follows PRD design specifications, color palette, typography, and anti-glitch constraints.
"""

import sys
import os
import time
from pathlib import Path

# Import from canonical skill directory
SKILL_SCRIPTS = Path.home() / ".gemini" / "config" / "skills" / "figcraft-fast-skill" / "scripts"
sys.path.insert(0, str(SKILL_SCRIPTS))
from figcraft_ui import FigCraftClient
from design_tokens import DesignTokens
from figcraft_components import UIComponents

# ==============================================================================
# DESIGN SYSTEM CONSTANTS (PRD Compliant)
# ==============================================================================
COLOR_CANVAS        = "#FFF8F0"  # Vanilla Cream
COLOR_CARD          = "#FFFFFF"  # Vanilla Murni
COLOR_TEXT_PRIMARY  = "#3B2219"  # Coklat Tua
COLOR_TEXT_MUTED    = "#70483C"  # Coklat Susu
COLOR_CUSTARD       = "#F4E7D3"  # Vanilla Custard
COLOR_RUBY          = "#E04D68"  # Stroberi Ruby (CTA / Badge)
COLOR_BLUSH         = "#FFD6DC"  # Stroberi Blush (Hover / Pill Aktif)
COLOR_OVERLAY       = "#3B221980" # Semi-transparent dark overlay for modals/drawers

FONT_HEADING = "Playfair Display"
FONT_BODY    = "Plus Jakarta Sans"

# ==============================================================================
# REUSABLE COMPONENTS
# ==============================================================================

def render_header(client: FigCraftClient, parent: int, active_item: str = "home", cart_count: str = "3") -> int:
    """Renders the standard sticky navigation header."""
    header = client.box(
        parent=parent,
        name="Header",
        layout="horizontal",
        x=0, y=0, width=1440, height=80,
        padding=[0, 60, 0, 60],
        mainAlign="spaceBetween",
        crossAlign="center",
        fill=COLOR_CARD,
        stroke=COLOR_CUSTARD,
        strokeWeight=1,
        effects=[{"type": "dropShadow", "color": "#3B221910", "offset": [0, 2], "radius": 8}]
    )

    # Logo Brand Group
    brand_group = client.box(
        parent=header,
        name="BrandGroup",
        layout="vertical",
        gap=2,
        mainAlign="center",
        crossAlign="min"
    )
    client.create_text(
        parent=brand_group,
        text="BerryCrumb",
        name="BrandName",
        fontSize=24,
        fontFamily=FONT_HEADING,
        fontStyle="Bold",
        fill=COLOR_TEXT_PRIMARY
    )
    client.create_text(
        parent=brand_group,
        text="PATISSERIE D'ARTISAN",
        name="BrandTagline",
        fontSize=9,
        fontFamily=FONT_BODY,
        fontStyle="Bold",
        fill=COLOR_TEXT_MUTED
    )

    # Nav Links Group
    nav_links = client.box(
        parent=header,
        name="NavLinks",
        layout="horizontal",
        gap=28,
        mainAlign="center",
        crossAlign="center"
    )

    items = [
        ("home", "Beranda"),
        ("shop", "Menu & Katalog"),
        ("custom", "Custom Cake Builder"),
        ("about", "Kisah Kami"),
        ("location", "Lokasi Outlet")
    ]
    for key, label in items:
        is_active = (key == active_item)
        link_box = client.box(
            parent=nav_links,
            name=f"NavLink_{key}",
            layout="vertical",
            gap=4,
            mainAlign="center",
            crossAlign="center"
        )
        client.create_text(
            parent=link_box,
            text=label,
            fontSize=14,
            fontFamily=FONT_BODY,
            fontStyle="Bold" if is_active else "Medium",
            fill=COLOR_RUBY if is_active else COLOR_TEXT_PRIMARY
        )
        if is_active:
            client.create_rect(
                parent=link_box,
                name="ActiveIndicator",
                width=24, height=3,
                fill=COLOR_RUBY,
                cornerRadius=2
            )

    # Actions Right Group (Outlet Picker + Cart Pill)
    actions = client.box(
        parent=header,
        name="HeaderActions",
        layout="horizontal",
        gap=14,
        mainAlign="max",
        crossAlign="center"
    )

    # Outlet Selector Pill
    outlet_btn = client.box(
        parent=actions,
        name="OutletSelector",
        layout="horizontal",
        gap=6,
        padding=[8, 14, 8, 14],
        mainAlign="center",
        crossAlign="center",
        fill=COLOR_CUSTARD,
        cornerRadius=20
    )
    client.create_text(
        parent=outlet_btn,
        text="📍 Outlet Senopati, Jaksel ▾",
        fontSize=12,
        fontFamily=FONT_BODY,
        fontStyle="SemiBold",
        fill=COLOR_TEXT_PRIMARY
    )

    # Cart Button with Circle Badge
    cart_btn = client.box(
        parent=actions,
        name="CartButton",
        layout="horizontal",
        gap=8,
        padding=[8, 16, 8, 16],
        mainAlign="center",
        crossAlign="center",
        fill=COLOR_BLUSH,
        stroke=COLOR_RUBY,
        strokeWeight=1,
        cornerRadius=20
    )
    client.create_text(
        parent=cart_btn,
        text="🛒 Keranjang",
        fontSize=13,
        fontFamily=FONT_BODY,
        fontStyle="Bold",
        fill=COLOR_RUBY
    )
    
    # 2-Half-Arc Circle Badge for cart counter
    badge_container = client.box(
        parent=cart_btn,
        name="CartBadge",
        layout="horizontal",
        width=20, height=20,
        mainAlign="center",
        crossAlign="center",
        fill=COLOR_RUBY,
        cornerRadius=10
    )
    client.create_text(
        parent=badge_container,
        text=cart_count,
        fontSize=11,
        fontFamily=FONT_BODY,
        fontStyle="Bold",
        fill="#FFFFFF",
        textAlign="center"
    )

    return header


def render_cake_illustration(client: FigCraftClient, parent: int, width: float = 380, height: float = 240) -> int:
    """Renders an artisanal tiered cake illustration using vector/rect primitives."""
    box = client.box(
        parent=parent,
        name="CakeIllustrationBox",
        layout="vertical",
        width=width, height=height,
        mainAlign="center",
        crossAlign="center",
        fill=COLOR_CANVAS,
        cornerRadius=16
    )

    # Cake stand base
    client.create_rect(parent=box, name="CakeStandTop", width=220, height=8, fill=COLOR_CUSTARD, cornerRadius=4)
    
    # Bottom Tier: Chocolate Fudge Sponge + Strawberry Compote
    tier1 = client.box(parent=box, name="Tier1_Base", layout="vertical", width=200, height=60, cornerRadius=6, fill=COLOR_TEXT_PRIMARY)
    client.create_rect(parent=tier1, name="SpongeCake", width=200, height=35, fill=COLOR_TEXT_PRIMARY)
    client.create_rect(parent=tier1, name="StrawberryCompote", width=200, height=12, fill=COLOR_RUBY)
    client.create_rect(parent=tier1, name="ButtercreamLayer", width=200, height=13, fill=COLOR_CARD)

    # Middle Tier: Vanilla & Chocolate Ganache
    tier2 = client.box(parent=box, name="Tier2_Mid", layout="vertical", width=150, height=50, cornerRadius=6, fill=COLOR_TEXT_MUTED)
    client.create_rect(parent=tier2, name="GanacheSponge", width=150, height=28, fill=COLOR_TEXT_MUTED)
    client.create_rect(parent=tier2, name="PinkCream", width=150, height=22, fill=COLOR_BLUSH)

    # Top Drip Ganache & Fresh Strawberry Toppers
    toppers = client.box(parent=box, name="ToppersRow", layout="horizontal", gap=10, mainAlign="center", crossAlign="center", height=38)
    for i in range(4):
        # 2-half-arc circular strawberries
        client.circle_arc(parent=toppers, name=f"Berry_{i}", cx=12, cy=12, r=10, fill=COLOR_RUBY)

    return box


# ==============================================================================
# SCREEN 01: BERANDA (HOMEPAGE)
# ==============================================================================
def build_screen_01_beranda(client: FigCraftClient, offset_x: float = 0, offset_y: float = 0):
    print("-> Rendering Screen 01: Beranda (Homepage)...")
    screen = client.create_frame(
        name="Layar 01 - Beranda",
        x=offset_x, y=offset_y,
        width=1440, height=900,
        fill=COLOR_CANVAS
    )

    # Sticky Header
    render_header(client, screen, active_item="home", cart_count="3")

    # Hero Section Container
    hero_section = client.box(
        parent=screen,
        name="HeroSection",
        layout="horizontal",
        x=80, y=95, width=1280, height=415,
        padding=[10, 0, 10, 0],
        mainAlign="spaceBetween",
        crossAlign="center"
    )

    # Left Column: Copywriting & CTAs
    hero_left = client.box(
        parent=hero_section,
        name="HeroLeft",
        layout="vertical",
        gap=14,
        width=680,
        mainAlign="center",
        crossAlign="min"
    )

    # Tag Pill
    tag_pill = client.box(
        parent=hero_left,
        name="HeroPillTag",
        layout="horizontal",
        gap=6,
        padding=[6, 14, 6, 14],
        fill=COLOR_BLUSH,
        cornerRadius=16
    )
    client.create_text(
        parent=tag_pill,
        text="🍓 Artisanal French Pâtisserie & Custom Cake Studio",
        fontSize=12,
        fontFamily=FONT_BODY,
        fontStyle="Bold",
        fill=COLOR_RUBY
    )

    # Main Heading H1
    client.create_text(
        parent=hero_left,
        text="Artisanal Cakes Crafted with Pure Passion",
        name="HeroHeading",
        width=650,
        fontSize=42,
        fontFamily=FONT_HEADING,
        fontStyle="Bold",
        fill=COLOR_TEXT_PRIMARY,
        lineHeight=50
    )

    # Subtitle
    client.create_text(
        parent=hero_left,
        text="Setiap lapis kue dipanggang teliti menggunakan mentega Prancis Normandia, coklat Belgia murni 70%, dan buah stroberi segar petikan langsung dari kebun lokal.",
        name="HeroSubtitle",
        width=620,
        fontSize=14,
        fontFamily=FONT_BODY,
        fontStyle="Regular",
        fill=COLOR_TEXT_MUTED,
        lineHeight=22
    )

    # CTA Buttons Row
    cta_row = client.box(
        parent=hero_left,
        name="HeroCTARow",
        layout="horizontal",
        gap=16,
        mainAlign="min",
        crossAlign="center"
    )

    # Primary CTA
    btn_primary = client.box(
        parent=cta_row,
        name="BtnPrimary_Menu",
        layout="horizontal",
        padding=[12, 26, 12, 26],
        fill=COLOR_RUBY,
        cornerRadius=12,
        effects=[{"type": "dropShadow", "color": "#E04D6840", "offset": [0, 4], "radius": 12}]
    )
    client.create_text(
        parent=btn_primary,
        text="Eksplor Menu Katalog ➔",
        fontSize=14,
        fontFamily=FONT_BODY,
        fontStyle="Bold",
        fill="#FFFFFF"
    )

    # Secondary CTA
    btn_secondary = client.box(
        parent=cta_row,
        name="BtnSecondary_Custom",
        layout="horizontal",
        padding=[12, 22, 12, 22],
        fill=COLOR_CARD,
        stroke=COLOR_TEXT_MUTED,
        strokeWeight=1.5,
        cornerRadius=12
    )
    client.create_text(
        parent=btn_secondary,
        text="✨ Rancang Custom Cake",
        fontSize=14,
        fontFamily=FONT_BODY,
        fontStyle="SemiBold",
        fill=COLOR_TEXT_PRIMARY
    )

    # Social Proof Stats
    stats_row = client.box(
        parent=hero_left,
        name="StatsRow",
        layout="horizontal",
        gap=20,
        mainAlign="min",
        crossAlign="center"
    )
    client.create_text(parent=stats_row, text="⭐ 4.9/5 (2,400+ Ulasan)", fontSize=12, fontFamily=FONT_BODY, fontStyle="SemiBold", fill=COLOR_TEXT_PRIMARY)
    client.create_text(parent=stats_row, text="•", fontSize=12, fill=COLOR_TEXT_MUTED)
    client.create_text(parent=stats_row, text="❄ Kurir Chilled Box Aman", fontSize=12, fontFamily=FONT_BODY, fontStyle="SemiBold", fill=COLOR_TEXT_PRIMARY)
    client.create_text(parent=stats_row, text="•", fontSize=12, fill=COLOR_TEXT_MUTED)
    client.create_text(parent=stats_row, text="⚡ Ready Kirim 2 Jam", fontSize=12, fontFamily=FONT_BODY, fontStyle="SemiBold", fill=COLOR_TEXT_PRIMARY)

    # Right Column: Hero Visual Card with Floating Badge
    hero_card = client.box(
        parent=hero_section,
        name="HeroVisualCard",
        layout="vertical",
        width=500, height=375,
        padding=18,
        gap=14,
        mainAlign="center",
        crossAlign="center",
        fill=COLOR_CARD,
        stroke=COLOR_CUSTARD,
        strokeWeight=1,
        cornerRadius=22,
        effects=[{"type": "dropShadow", "color": "#3B221915", "offset": [0, 8], "radius": 24}]
    )

    # Cake illustration inside hero card
    render_cake_illustration(client, hero_card, width=460, height=250)

    # Card Bottom Info
    hero_card_info = client.box(
        parent=hero_card,
        name="HeroCardInfo",
        layout="horizontal",
        width=460,
        mainAlign="spaceBetween",
        crossAlign="center"
    )
    info_text = client.box(parent=hero_card_info, name="CakeTitle", layout="vertical", gap=3)
    client.create_text(parent=info_text, text="Signature Strawberry Ganache", fontSize=17, fontFamily=FONT_HEADING, fontStyle="Bold", fill=COLOR_TEXT_PRIMARY)
    client.create_text(parent=info_text, text="Dia. 18 cm • 8-10 Porsi • Belgian 70% Dark Cocoa", fontSize=12, fontFamily=FONT_BODY, fill=COLOR_TEXT_MUTED)
    client.create_text(parent=hero_card_info, text="Rp 385.000", fontSize=19, fontFamily=FONT_HEADING, fontStyle="Bold", fill=COLOR_RUBY)

    # Floating Best Seller Badge (Top Right of Hero Card)
    floating_badge = client.box(
        parent=hero_card,
        name="FloatingBestSellerBadge",
        layout="horizontal",
        x=320, y=28,
        padding=[6, 12, 6, 12],
        fill=COLOR_RUBY,
        cornerRadius=14,
        absolute=True,
        effects=[{"type": "dropShadow", "color": "#E04D6850", "offset": [0, 2], "radius": 6}]
    )
    client.create_text(parent=floating_badge, text="🔥 BEST SELLER NO. 1", fontSize=11, fontFamily=FONT_BODY, fontStyle="Bold", fill="#FFFFFF")

    # Trust Badges 3-Pillars Strip
    trust_strip = client.box(
        parent=screen,
        name="TrustBadgesStrip",
        layout="horizontal",
        x=80, y=525, width=1280, height=80,
        padding=[0, 32, 0, 32],
        mainAlign="spaceBetween",
        crossAlign="center",
        fill=COLOR_CARD,
        stroke=COLOR_CUSTARD,
        strokeWeight=1,
        cornerRadius=16,
        effects=[{"type": "dropShadow", "color": "#3B221908", "offset": [0, 4], "radius": 12}]
    )

    pillars = [
        ("🌿 Bahan Baku Premium Alami", "Mentega Normandia & Belgian Cocoa 100% murni tanpa perisa buatan."),
        ("❄ Pengiriman Berpendingin Aman", "Mobil berpendingin khusus menjaga kue tetap dingin, kokoh & utuh."),
        ("✨ Garansi Kesegaran Harian", "Dipanggang fresh di hari pengiriman, jaminan kepuasan rasa 100%.")
    ]
    for title, desc in pillars:
        pillar_box = client.box(parent=trust_strip, name="PillarItem", layout="vertical", gap=3, width=370)
        client.create_text(parent=pillar_box, text=title, fontSize=13, fontFamily=FONT_BODY, fontStyle="Bold", fill=COLOR_TEXT_PRIMARY)
        client.create_text(parent=pillar_box, text=desc, fontSize=11, fontFamily=FONT_BODY, fill=COLOR_TEXT_MUTED)

    # Best Seller Showcase Row
    showcase_header = client.box(
        parent=screen,
        name="ShowcaseHeader",
        layout="horizontal",
        x=80, y=625, width=1280, height=30,
        mainAlign="spaceBetween",
        crossAlign="center"
    )
    client.create_text(parent=showcase_header, text="Koleksi Favorit Pelanggan", fontSize=21, fontFamily=FONT_HEADING, fontStyle="Bold", fill=COLOR_TEXT_PRIMARY)
    client.create_text(parent=showcase_header, text="Lihat Semua Menu (28) ➔", fontSize=13, fontFamily=FONT_BODY, fontStyle="Bold", fill=COLOR_RUBY)

    # 4 Showcase Cards Row
    cards_container = client.box(
        parent=screen,
        name="BestSellerCardsRow",
        layout="horizontal",
        x=80, y=665, width=1280, height=195,
        gap=20,
        mainAlign="spaceBetween",
        crossAlign="center"
    )

    card_data = [
        ("Strawberry Ganache Noir", "Dia. 18cm / 8-10 Slice", "Rp 385.000", "⭐ 4.95", COLOR_RUBY),
        ("Vanilla Bean Madagaskar", "Dia. 20cm / 10-12 Slice", "Rp 340.000", "⭐ 4.88", COLOR_CUSTARD),
        ("Ruby Chiffon Berry Cloud", "Dia. 16cm / 6-8 Slice", "Rp 310.000", "⭐ 4.92", COLOR_BLUSH),
        ("Belgian Dark Truffle", "Dia. 20cm / 10-12 Slice", "Rp 420.000", "⭐ 4.98", COLOR_TEXT_PRIMARY)
    ]

    card_ids = []
    for title, size, price, rating, accent_color in card_data:
        card = client.box(
            parent=cards_container,
            name=f"Card_{title[:12]}",
            layout="vertical",
            width=295, height=185,
            padding=14,
            gap=8,
            fill=COLOR_CARD,
            stroke=COLOR_CUSTARD,
            strokeWeight=1,
            cornerRadius=14,
            effects=[{"type": "dropShadow", "color": "#3B221908", "offset": [0, 4], "radius": 8}]
        )
        card_ids.append(card)

        # Mini Graphic Bar
        mini_thumb = client.box(parent=card, name="Thumb", layout="horizontal", width=267, height=65, fill=COLOR_CANVAS, cornerRadius=8, mainAlign="spaceBetween", crossAlign="center", padding=[0, 12, 0, 12])
        client.circle_arc(parent=mini_thumb, name="MiniCakeIcon", cx=16, cy=16, r=14, fill=accent_color)
        badge = client.box(parent=mini_thumb, name="MiniRating", layout="horizontal", padding=[4, 8, 4, 8], fill=COLOR_CARD, cornerRadius=10)
        client.create_text(parent=badge, text=rating, fontSize=11, fontFamily=FONT_BODY, fontStyle="Bold", fill=COLOR_TEXT_PRIMARY)

        # Card Content
        client.create_text(parent=card, text=title, fontSize=14, fontFamily=FONT_HEADING, fontStyle="Bold", fill=COLOR_TEXT_PRIMARY)
        client.create_text(parent=card, text=size, fontSize=11, fontFamily=FONT_BODY, fill=COLOR_TEXT_MUTED)

        # Bottom Price & Quick Add Button
        card_bottom = client.box(parent=card, name="CardBottom", layout="horizontal", width=267, mainAlign="spaceBetween", crossAlign="center")
        client.create_text(parent=card_bottom, text=price, fontSize=14, fontFamily=FONT_BODY, fontStyle="Bold", fill=COLOR_TEXT_PRIMARY)
        
        btn_add = client.box(parent=card_bottom, name="QuickAdd", layout="horizontal", padding=[5, 12, 5, 12], fill=COLOR_RUBY, cornerRadius=8)
        client.create_text(parent=btn_add, text="+ Tambah", fontSize=11, fontFamily=FONT_BODY, fontStyle="Bold", fill="#FFFFFF")

    # Anti-glitch: equasize heights across cards using dynamic auto-measure
    client.equasize_heights(card_ids, target_height=None)
    print("  ✓ Screen 01 rendered successfully.")
    return screen


# ==============================================================================
# SCREEN 02: KATALOG MENU & SHOP
# ==============================================================================
def build_screen_02_katalog(client: FigCraftClient, offset_x: float = 1600, offset_y: float = 0):
    print("-> Rendering Screen 02: Katalog Menu & Shop...")
    screen = client.create_frame(
        name="Layar 02 - Katalog Menu & Shop",
        x=offset_x, y=offset_y,
        width=1440, height=900,
        fill=COLOR_CANVAS
    )

    # Sticky Header
    render_header(client, screen, active_item="shop", cart_count="3")

    # Page Header Banner
    header_box = client.box(
        parent=screen,
        name="PageHeaderBox",
        layout="vertical",
        x=80, y=95, width=1280, height=75,
        gap=6,
        mainAlign="center",
        crossAlign="min"
    )
    client.create_text(parent=header_box, text="Beranda  /  Katalog Menu & Shop", fontSize=12, fontFamily=FONT_BODY, fill=COLOR_TEXT_MUTED)
    client.create_text(parent=header_box, text="Katalog Kue Artisanal & Pâtisserie", fontSize=28, fontFamily=FONT_HEADING, fontStyle="Bold", fill=COLOR_TEXT_PRIMARY)

    # Filter Pills Row
    filter_bar = client.box(
        parent=screen,
        name="FilterPillsBar",
        layout="horizontal",
        x=80, y=180, width=1280, height=45,
        mainAlign="spaceBetween",
        crossAlign="center"
    )

    pills_container = client.box(parent=filter_bar, name="PillsContainer", layout="horizontal", gap=12, mainAlign="min", crossAlign="center")
    
    pills = [
        ("Semua Menu (28)", True),
        ("🍫 Pure Coklat (8)", False),
        ("🍦 Vanilla Bean (6)", False),
        ("🍓 Fresh Strawberry (7)", False),
        ("✨ Kombinasi Rasa (5)", False),
        ("🌾 Bebas Gluten (4)", False)
    ]
    for label, is_active in pills:
        pill = client.box(
            parent=pills_container,
            name=f"Pill_{label[:8]}",
            layout="horizontal",
            padding=[8, 18, 8, 18],
            fill=COLOR_RUBY if is_active else COLOR_CUSTARD,
            cornerRadius=20
        )
        client.create_text(
            parent=pill,
            text=label,
            fontSize=13,
            fontFamily=FONT_BODY,
            fontStyle="Bold" if is_active else "Medium",
            fill="#FFFFFF" if is_active else COLOR_TEXT_PRIMARY
        )

    # Sort Dropdown Selector
    sort_dropdown = client.box(
        parent=filter_bar,
        name="SortDropdown",
        layout="horizontal",
        gap=8,
        padding=[8, 16, 8, 16],
        fill=COLOR_CARD,
        stroke=COLOR_TEXT_MUTED,
        strokeWeight=1,
        cornerRadius=10
    )
    client.create_text(parent=sort_dropdown, text="Urutkan: Terpopuler ▾", fontSize=13, fontFamily=FONT_BODY, fontStyle="SemiBold", fill=COLOR_TEXT_PRIMARY)

    # Grid 4 Kolom Kartu Produk (W: 1280, 4 cards each W: 295, Gap: 24)
    grid_container = client.box(
        parent=screen,
        name="ProductGridContainer",
        layout="horizontal",
        x=80, y=240, width=1280, height=540,
        gap=24,
        mainAlign="spaceBetween",
        crossAlign="center"
    )

    products = [
        {
            "name": "Signature Strawberry Ganache",
            "tag": "Best Seller",
            "tag_color": COLOR_RUBY,
            "category": "WHOLE CAKE • COKLAT & STROBERI",
            "size": "Dia. 18 cm / 8-10 Slice",
            "rating": "★ 4.95 (420)",
            "price": "Rp 385.000",
            "desc": "Belgian 70% dark chocolate ganache dengan strawberry compote alami."
        },
        {
            "name": "Madagascar Vanilla Custard",
            "tag": "Chef's Pick",
            "tag_color": COLOR_CUSTARD,
            "category": "WHOLE CAKE • VANILLA",
            "size": "Dia. 20 cm / 10-12 Slice",
            "rating": "★ 4.88 (310)",
            "price": "Rp 340.000",
            "desc": "Vanilla bean Madagaskar asli dengan krim custard lembut Normandia."
        },
        {
            "name": "Ruby Chiffon Berry Cloud",
            "tag": "Fresh Berry",
            "tag_color": COLOR_BLUSH,
            "category": "WHOLE CAKE • STROBERI",
            "size": "Dia. 16 cm / 6-8 Slice",
            "rating": "★ 4.92 (185)",
            "price": "Rp 310.000",
            "desc": "Chiffon cake super lembut dengan potongan buah stroberi segar berlimpah."
        },
        {
            "name": "Belgian Dark Velvet Truffle",
            "tag": "Rich Cocoa",
            "tag_color": COLOR_TEXT_PRIMARY,
            "category": "WHOLE CAKE • COKLAT MURNI",
            "size": "Dia. 20 cm / 10-12 Slice",
            "rating": "★ 4.98 (560)",
            "price": "Rp 420.000",
            "desc": "Truffle ganache kaya rasa berpadu dengan dark velvet sponge lembab."
        }
    ]

    card_ids = []
    for item in products:
        card = client.box(
            parent=grid_container,
            name=f"ProductCard_{item['name'][:12]}",
            layout="vertical",
            width=295, height=520,
            padding=16,
            gap=12,
            fill=COLOR_CARD,
            stroke=COLOR_CUSTARD,
            strokeWeight=1,
            cornerRadius=18,
            effects=[{"type": "dropShadow", "color": "#3B221910", "offset": [0, 6], "radius": 16}]
        )
        card_ids.append(card)

        # Image Visual Container (Ratio 1:1, H: 200)
        img_container = client.box(
            parent=card,
            name="ImageArea",
            layout="vertical",
            width=263, height=190,
            padding=12,
            mainAlign="spaceBetween",
            crossAlign="center",
            fill=COLOR_CANVAS,
            cornerRadius=12
        )
        # Floating badge inside image
        badge_row = client.box(parent=img_container, name="BadgeRow", layout="horizontal", width=239, mainAlign="spaceBetween")
        badge = client.box(parent=badge_row, name="Badge", layout="horizontal", padding=[4, 10, 4, 10], fill=item["tag_color"], cornerRadius=12)
        client.create_text(parent=badge, text=item["tag"], fontSize=11, fontFamily=FONT_BODY, fontStyle="Bold", fill="#FFFFFF" if item["tag_color"] in [COLOR_RUBY, COLOR_TEXT_PRIMARY] else COLOR_TEXT_PRIMARY)
        
        # Center Cake Art Circle
        client.circle_arc(parent=img_container, name="ProductArtCircle", cx=32, cy=32, r=28, fill=COLOR_RUBY if "Strawberry" in item["name"] or "Ruby" in item["name"] else COLOR_TEXT_MUTED)

        # Category subtitle
        client.create_text(parent=card, text=item["category"], fontSize=10, fontFamily=FONT_BODY, fontStyle="Bold", fill=COLOR_TEXT_MUTED)

        # Title
        client.create_text(parent=card, text=item["name"], fontSize=17, fontFamily=FONT_HEADING, fontStyle="Bold", fill=COLOR_TEXT_PRIMARY)

        # Size & Rating Row
        meta_row = client.box(parent=card, name="MetaRow", layout="horizontal", width=263, mainAlign="spaceBetween", crossAlign="center")
        client.create_text(parent=meta_row, text=item["size"], fontSize=12, fontFamily=FONT_BODY, fill=COLOR_TEXT_MUTED)
        client.create_text(parent=meta_row, text=item["rating"], fontSize=12, fontFamily=FONT_BODY, fontStyle="Bold", fill=COLOR_RUBY)

        # Description
        client.create_text(parent=card, text=item["desc"], width=263, fontSize=12, fontFamily=FONT_BODY, fill=COLOR_TEXT_MUTED, lineHeight=18)

        # Price
        client.create_text(parent=card, text=item["price"], fontSize=19, fontFamily=FONT_HEADING, fontStyle="Bold", fill=COLOR_TEXT_PRIMARY)

        # Quick Add CTA Button
        btn_quick_add = client.box(
            parent=card,
            name="BtnQuickAdd",
            layout="horizontal",
            width=263, height=42,
            mainAlign="center",
            crossAlign="center",
            fill=COLOR_RUBY,
            cornerRadius=10
        )
        client.create_text(parent=btn_quick_add, text="+ Tambah Cepat", fontSize=13, fontFamily=FONT_BODY, fontStyle="Bold", fill="#FFFFFF")

    # Anti-glitch: Uniform card height using dynamic auto-measure
    client.equasize_heights(card_ids, target_height=None)

    # Pagination Footer Bar
    pagination = client.box(
        parent=screen,
        name="PaginationFooter",
        layout="horizontal",
        x=80, y=810, width=1280, height=50,
        mainAlign="spaceBetween",
        crossAlign="center"
    )
    client.create_text(parent=pagination, text="Menampilkan 1 - 4 dari 28 varian kue artisanal", fontSize=13, fontFamily=FONT_BODY, fill=COLOR_TEXT_MUTED)

    page_btns = client.box(parent=pagination, name="PageButtons", layout="horizontal", gap=8, mainAlign="center", crossAlign="center")
    p1 = client.box(parent=page_btns, name="Page1", layout="horizontal", padding=[6, 12, 6, 12], fill=COLOR_RUBY, cornerRadius=8)
    client.create_text(parent=p1, text="1", fontSize=12, fontStyle="Bold", fill="#FFFFFF")
    p2 = client.box(parent=page_btns, name="Page2", layout="horizontal", padding=[6, 12, 6, 12], fill=COLOR_CARD, stroke=COLOR_CUSTARD, cornerRadius=8)
    client.create_text(parent=p2, text="2", fontSize=12, fill=COLOR_TEXT_PRIMARY)
    p3 = client.box(parent=page_btns, name="Page3", layout="horizontal", padding=[6, 12, 6, 12], fill=COLOR_CARD, stroke=COLOR_CUSTARD, cornerRadius=8)
    client.create_text(parent=p3, text="3", fontSize=12, fill=COLOR_TEXT_PRIMARY)
    client.create_text(parent=page_btns, text="Halaman Selanjutnya ➔", fontSize=13, fontFamily=FONT_BODY, fontStyle="Bold", fill=COLOR_RUBY)

    print("  ✓ Screen 02 rendered successfully.")
    return screen


# ==============================================================================
# SCREEN 03: MODAL QUICK VIEW PRODUK
# ==============================================================================
def build_screen_03_modal_quick_view(client: FigCraftClient, offset_x: float = 3200, offset_y: float = 0):
    print("-> Rendering Screen 03: Modal Quick View...")
    screen = client.create_frame(
        name="Layar 03 - Modal Quick View",
        x=offset_x, y=offset_y,
        width=1440, height=900,
        fill=COLOR_CANVAS
    )

    # Render background catalog underneath
    render_header(client, screen, active_item="shop", cart_count="3")

    # Dark backdrop overlay for modal
    client.create_rect(
        parent=screen,
        name="ModalBackdropOverlay",
        x=0, y=0, width=1440, height=900,
        fill=COLOR_OVERLAY
    )

    # Center Modal Container (W: 1040, H: 760, centered)
    modal = client.box(
        parent=screen,
        name="ModalWindow",
        layout="horizontal",
        x=200, y=70, width=1040, height=760,
        padding=36,
        gap=36,
        mainAlign="spaceBetween",
        crossAlign="center",
        fill=COLOR_CARD,
        cornerRadius=24,
        effects=[{"type": "dropShadow", "color": "#3B221940", "offset": [0, 16], "radius": 36}]
    )

    # Floating Close Button (Top Right of Modal)
    btn_close = client.box(
        parent=modal,
        name="FloatingCloseButton",
        layout="horizontal",
        x=984, y=20,
        width=36, height=36,
        mainAlign="center",
        crossAlign="center",
        fill=COLOR_CANVAS,
        stroke=COLOR_CUSTARD,
        strokeWeight=1,
        cornerRadius=18,
        absolute=True
    )
    client.create_text(parent=btn_close, text="✕", fontSize=14, fontStyle="Bold", fill=COLOR_TEXT_PRIMARY)

    # Left Column: Product Showcase Visual & Thumbnails (W: 450)
    left_col = client.box(
        parent=modal,
        name="ModalLeftShowcase",
        layout="vertical",
        width=450,
        gap=16,
        mainAlign="center",
        crossAlign="min"
    )

    # Main Visual Box
    main_img = client.box(
        parent=left_col,
        name="MainImageBox",
        layout="vertical",
        width=450, height=380,
        padding=16,
        mainAlign="spaceBetween",
        crossAlign="center",
        fill=COLOR_CANVAS,
        cornerRadius=18
    )
    badge = client.box(parent=main_img, name="FreshTag", layout="horizontal", padding=[6, 12, 6, 12], fill=COLOR_BLUSH, cornerRadius=12)
    client.create_text(parent=badge, text="🍓 Freshly Baked Daily", fontSize=12, fontStyle="Bold", fill=COLOR_RUBY)
    
    # Cake Graphic Inside Modal
    render_cake_illustration(client, main_img, width=410, height=260)

    # Mini Thumbnails Strip
    thumb_strip = client.box(parent=left_col, name="ThumbStrip", layout="horizontal", gap=12, mainAlign="min", crossAlign="center")
    for idx, label in enumerate(["Tampilan Utuh", "Potongan Slice", "Kotak Kemasan Eksklusif"]):
        thumb = client.box(
            parent=thumb_strip,
            name=f"Thumb_{idx}",
            layout="horizontal",
            width=142, height=70,
            padding=8,
            mainAlign="center",
            crossAlign="center",
            fill=COLOR_CANVAS,
            stroke=COLOR_RUBY if idx == 0 else COLOR_CUSTARD,
            strokeWeight=1.5 if idx == 0 else 1,
            cornerRadius=10
        )
        client.create_text(parent=thumb, text=label, fontSize=11, fontStyle="Bold" if idx == 0 else "Regular", fill=COLOR_TEXT_PRIMARY)

    # Storage Guide Callout
    storage_box = client.box(
        parent=left_col,
        name="StorageNotice",
        layout="horizontal",
        width=450,
        padding=[12, 16, 12, 16],
        gap=10,
        fill=COLOR_CANVAS,
        stroke=COLOR_CUSTARD,
        strokeWeight=1,
        cornerRadius=12
    )
    client.create_text(parent=storage_box, text="❄ Simpan di suhu 2°C - 6°C dalam chiller. Terbaik dinikmati dalam 4 hari.", fontSize=12, fontFamily=FONT_BODY, fill=COLOR_TEXT_MUTED)

    # Right Column: Product Details, Portion Selectors, Add-Ons & CTA (W: 480)
    right_col = client.box(
        parent=modal,
        name="ModalRightDetails",
        layout="vertical",
        width=480,
        gap=14,
        mainAlign="center",
        crossAlign="min"
    )

    # Category & Rating
    cat_rating = client.box(parent=right_col, name="CategoryRating", layout="horizontal", width=480, mainAlign="spaceBetween", crossAlign="center")
    client.create_text(parent=cat_rating, text="WHOLE CAKE • ARTISANAL SIGNATURE", fontSize=11, fontStyle="Bold", fill=COLOR_RUBY)
    client.create_text(parent=cat_rating, text="⭐ 4.95 (420 Ulasan Terverifikasi)", fontSize=12, fontStyle="Bold", fill=COLOR_TEXT_PRIMARY)

    # Product Title
    client.create_text(parent=right_col, text="Signature Strawberry Ganache", fontSize=26, fontFamily=FONT_HEADING, fontStyle="Bold", fill=COLOR_TEXT_PRIMARY)

    # Price
    client.create_text(parent=right_col, text="Rp 385.000", fontSize=24, fontFamily=FONT_HEADING, fontStyle="Bold", fill=COLOR_RUBY)

    # Description
    client.create_text(
        parent=right_col,
        text="Perpaduan mewah dark chocolate fudge sponge 70% kakao Belgia murni, dilapisi selai strawberry compote segar asli tanpa pengawet, disempurnakan drip ganache coklat halus berkilau.",
        width=480,
        fontSize=13,
        fontFamily=FONT_BODY,
        fill=COLOR_TEXT_MUTED,
        lineHeight=19
    )

    # Allergen Tags Pill Container
    client.create_text(parent=right_col, text="Informasi Alergen Makanan:", fontSize=12, fontStyle="Bold", fill=COLOR_TEXT_PRIMARY)
    allergen_row = client.box(parent=right_col, name="Allergens", layout="horizontal", gap=8)
    for tag in ["🥛 Susu Sapi Murni", "🥚 Telur Omega", "🥜 Kacang Almond Halus"]:
        pill = client.box(parent=allergen_row, name=f"Allergen_{tag[:3]}", layout="horizontal", padding=[5, 10, 5, 10], fill=COLOR_CUSTARD, cornerRadius=12)
        client.create_text(parent=pill, text=tag, fontSize=11, fontStyle="Medium", fill=COLOR_TEXT_PRIMARY)

    # Portion Diameter Selector
    client.create_text(parent=right_col, text="Pilih Ukuran Diameter Porsi:", fontSize=12, fontStyle="Bold", fill=COLOR_TEXT_PRIMARY)
    size_selector = client.box(parent=right_col, name="SizeSelector", layout="horizontal", gap=10, width=480)
    sizes = [
        ("Dia. 16 cm (6-8 Slice)", "Rp 310k", False),
        ("Dia. 18 cm (8-10 Slice)", "Rp 385k", True),
        ("Dia. 24 cm (16-20 Slice)", "Rp 520k", False)
    ]
    for s_name, s_price, is_selected in sizes:
        s_box = client.box(
            parent=size_selector,
            name=f"Size_{s_price}",
            layout="vertical",
            gap=2,
            padding=[8, 12, 8, 12],
            width=150,
            fill=COLOR_BLUSH if is_selected else COLOR_CANVAS,
            stroke=COLOR_RUBY if is_selected else COLOR_CUSTARD,
            strokeWeight=1.5 if is_selected else 1,
            cornerRadius=10
        )
        client.create_text(parent=s_box, text=s_name, fontSize=11, fontStyle="Bold" if is_selected else "Medium", fill=COLOR_RUBY if is_selected else COLOR_TEXT_PRIMARY)
        client.create_text(parent=s_box, text=s_price, fontSize=12, fontStyle="Bold", fill=COLOR_RUBY if is_selected else COLOR_TEXT_MUTED)

    # Add-Ons Checklist
    client.create_text(parent=right_col, text="Tambahan Pelengkap Acara (Add-Ons):", fontSize=12, fontStyle="Bold", fill=COLOR_TEXT_PRIMARY)
    addon_list = client.box(parent=right_col, name="AddOnList", layout="vertical", gap=8, width=480)
    addons = [
        ("✔ Lilin Angka Emas Metallic (+Rp 15.000)", True),
        ("✔ Topper Akrilik Ucapan Ulang Tahun (+Rp 25.000)", True),
        ("✔ Kartu Ucapan Kaligrafi Elegan (Gratis)", True)
    ]
    for a_text, checked in addons:
        a_row = client.box(parent=addon_list, name="AddonRow", layout="horizontal", gap=8, padding=[6, 12, 6, 12], fill=COLOR_CANVAS, cornerRadius=8)
        client.create_text(parent=a_row, text=a_text, fontSize=12, fontStyle="Medium", fill=COLOR_TEXT_PRIMARY)

    # Bottom Actions: Stepper + Add to Cart CTA
    action_row = client.box(parent=right_col, name="ModalActionRow", layout="horizontal", gap=16, width=480, crossAlign="center")
    
    # Quantity Stepper
    stepper = client.box(parent=action_row, name="Stepper", layout="horizontal", gap=14, padding=[10, 16, 10, 16], stroke=COLOR_TEXT_MUTED, strokeWeight=1, cornerRadius=10)
    client.create_text(parent=stepper, text="−", fontSize=16, fontStyle="Bold", fill=COLOR_TEXT_PRIMARY)
    client.create_text(parent=stepper, text="1", fontSize=15, fontStyle="Bold", fill=COLOR_TEXT_PRIMARY)
    client.create_text(parent=stepper, text="+", fontSize=16, fontStyle="Bold", fill=COLOR_TEXT_PRIMARY)

    # Primary Add to Cart Button
    btn_add_modal = client.box(
        parent=action_row,
        name="BtnModalAddToCart",
        layout="horizontal",
        height=48,
        width=340,
        mainAlign="center",
        crossAlign="center",
        fill=COLOR_RUBY,
        cornerRadius=12,
        effects=[{"type": "dropShadow", "color": "#E04D6840", "offset": [0, 4], "radius": 12}]
    )
    client.create_text(parent=btn_add_modal, text="Tambah ke Keranjang • Rp 425.000 ➔", fontSize=14, fontStyle="Bold", fill="#FFFFFF")

    print("  ✓ Screen 03 rendered successfully.")
    return screen


# ==============================================================================
# SCREEN 04: CUSTOM CAKE BUILDER (CONFIGURATOR)
# ==============================================================================
def build_screen_04_custom_builder(client: FigCraftClient, offset_x: float = 0, offset_y: float = 1050):
    print("-> Rendering Screen 04: Custom Cake Builder...")
    screen = client.create_frame(
        name="Layar 04 - Custom Cake Builder",
        x=offset_x, y=offset_y,
        width=1440, height=900,
        fill=COLOR_CANVAS
    )

    # Builder Sub-Header
    builder_header = client.box(
        parent=screen,
        name="BuilderHeader",
        layout="horizontal",
        x=0, y=0, width=1440, height=75,
        padding=[0, 60, 0, 60],
        mainAlign="spaceBetween",
        crossAlign="center",
        fill=COLOR_CARD,
        stroke=COLOR_CUSTARD,
        strokeWeight=1
    )
    brand_sub = client.box(parent=builder_header, name="BrandSub", layout="horizontal", gap=12, crossAlign="center")
    client.create_text(parent=brand_sub, text="BerryCrumb", fontSize=22, fontFamily=FONT_HEADING, fontStyle="Bold", fill=COLOR_TEXT_PRIMARY)
    client.create_text(parent=brand_sub, text="|  Custom Cake Studio Interactive", fontSize=14, fontFamily=FONT_BODY, fontStyle="SemiBold", fill=COLOR_TEXT_MUTED)

    # Step Progress Indicator
    step_indicator = client.box(parent=builder_header, name="StepProgress", layout="horizontal", gap=8, crossAlign="center")
    client.create_text(parent=step_indicator, text="Konfigurasi Aktif: Langkah 1 s/d 6 Lengkap", fontSize=13, fontStyle="Bold", fill=COLOR_RUBY)

    # Close/Exit Link
    client.create_text(parent=builder_header, text="Simpan & Keluar ✕", fontSize=13, fontStyle="SemiBold", fill=COLOR_TEXT_MUTED)

    # Main 2-Column Area (H: 700)
    # Left Column: Interactive 3D Real-Time Cake Preview (W: 540, H: 690)
    left_preview = client.box(
        parent=screen,
        name="BuilderLeftPreview",
        layout="vertical",
        x=60, y=88, width=540, height=690,
        padding=24,
        gap=14,
        mainAlign="spaceBetween",
        crossAlign="center",
        fill=COLOR_CARD,
        stroke=COLOR_CUSTARD,
        strokeWeight=1,
        cornerRadius=20,
        effects=[{"type": "dropShadow", "color": "#3B22190C", "offset": [0, 8], "radius": 20}]
    )

    # Title Bar
    preview_title = client.box(parent=left_preview, name="TitleBar", layout="horizontal", width=492, mainAlign="spaceBetween", crossAlign="center")
    client.create_text(parent=preview_title, text="Live Cake Preview (Real-Time)", fontSize=17, fontFamily=FONT_HEADING, fontStyle="Bold", fill=COLOR_TEXT_PRIMARY)
    badge_3d = client.box(parent=preview_title, name="Badge3D", layout="horizontal", padding=[4, 10, 4, 10], fill=COLOR_BLUSH, cornerRadius=10)
    client.create_text(parent=badge_3d, text="Model: Bulat Dia. 20 cm", fontSize=11, fontStyle="Bold", fill=COLOR_RUBY)

    # 3D Visual Rendering Box (H: 380)
    visual_box = client.box(
        parent=left_preview,
        name="CakeVisualSimulation",
        layout="vertical",
        width=492, height=380,
        padding=20,
        mainAlign="center",
        crossAlign="center",
        fill=COLOR_CANVAS,
        cornerRadius=16
    )

    # Calligraphy Text Ribbon on Cake
    ribbon = client.box(
        parent=visual_box,
        name="CalligraphyRibbon",
        layout="horizontal",
        padding=[8, 20, 8, 20],
        fill=COLOR_CUSTARD,
        stroke=COLOR_TEXT_MUTED,
        strokeWeight=1,
        cornerRadius=20
    )
    client.create_text(parent=ribbon, text="✨ Happy Sweet 17th Kirana! ✨", fontSize=14, fontFamily=FONT_HEADING, fontStyle="Bold", fill=COLOR_TEXT_PRIMARY)

    # Cake illustration representation
    render_cake_illustration(client, visual_box, width=440, height=240)

    # Recipe / Selected Breakdown Box
    recipe_box = client.box(
        parent=left_preview,
        name="SelectedRecipeSummary",
        layout="vertical",
        width=492,
        padding=14,
        gap=6,
        fill=COLOR_CANVAS,
        cornerRadius=12
    )
    client.create_text(parent=recipe_box, text="Rincian Komposisi Kue Terpilih:", fontSize=12, fontStyle="Bold", fill=COLOR_TEXT_PRIMARY)
    client.create_text(parent=recipe_box, text="• Sponge: Coklat Fudge Belgia  |  Filling: Selai Strawberry Compote Asli", fontSize=11, fill=COLOR_TEXT_MUTED)
    client.create_text(parent=recipe_box, text="• Frosting: Buttercream Pink Strawberry  |  Topping: Buah Stroberi & Macaron", fontSize=11, fill=COLOR_TEXT_MUTED)

    # Right Column: 6-Step Interactive Configurator Options (W: 760, H: 690)
    right_controls = client.box(
        parent=screen,
        name="BuilderRightControls",
        layout="vertical",
        x=620, y=88, width=760, height=690,
        padding=22,
        gap=14,
        fill=COLOR_CARD,
        stroke=COLOR_CUSTARD,
        strokeWeight=1,
        cornerRadius=20,
        effects=[{"type": "dropShadow", "color": "#3B22190C", "offset": [0, 8], "radius": 20}]
    )

    # Step 1: Bentuk & Ukuran
    step1_box = client.box(parent=right_controls, name="Step1_Size", layout="vertical", gap=6, width=716)
    client.create_text(parent=step1_box, text="1. Bentuk & Ukuran Kue", fontSize=13, fontStyle="Bold", fill=COLOR_TEXT_PRIMARY)
    step1_opts = client.box(parent=step1_box, name="Step1Opts", layout="horizontal", gap=10)
    for opt, active in [("Bulat 16cm (6-8p)", False), ("Bulat 20cm (10-12p) ★", True), ("Bulat 24cm (16-20p)", False), ("Persegi 20cm", False)]:
        btn = client.box(parent=step1_opts, name=f"Opt_{opt[:6]}", layout="horizontal", padding=[6, 12, 6, 12], fill=COLOR_BLUSH if active else COLOR_CANVAS, stroke=COLOR_RUBY if active else COLOR_CUSTARD, cornerRadius=8)
        client.create_text(parent=btn, text=opt, fontSize=11, fontStyle="Bold" if active else "Medium", fill=COLOR_RUBY if active else COLOR_TEXT_PRIMARY)

    # Step 2: Sponge Base
    step2_box = client.box(parent=right_controls, name="Step2_Sponge", layout="vertical", gap=6, width=716)
    client.create_text(parent=step2_box, text="2. Sponge Cake Base", fontSize=13, fontStyle="Bold", fill=COLOR_TEXT_PRIMARY)
    step2_opts = client.box(parent=step2_box, name="Step2Opts", layout="horizontal", gap=10)
    for opt, active in [("Coklat Fudge Belgia ✔", True), ("Sponge Vanilla Bean", False), ("Chiffon Stroberi", False)]:
        btn = client.box(parent=step2_opts, name=f"Opt_{opt[:6]}", layout="horizontal", padding=[6, 14, 6, 14], fill=COLOR_BLUSH if active else COLOR_CANVAS, stroke=COLOR_RUBY if active else COLOR_CUSTARD, cornerRadius=8)
        client.create_text(parent=btn, text=opt, fontSize=11, fontStyle="Bold" if active else "Medium", fill=COLOR_RUBY if active else COLOR_TEXT_PRIMARY)

    # Step 3: Filling Tengah
    step3_box = client.box(parent=right_controls, name="Step3_Filling", layout="vertical", gap=6, width=716)
    client.create_text(parent=step3_box, text="3. Filling Lapisan Tengah", fontSize=13, fontStyle="Bold", fill=COLOR_TEXT_PRIMARY)
    step3_opts = client.box(parent=step3_box, name="Step3Opts", layout="horizontal", gap=10)
    for opt, active in [("Selai Strawberry Compote Asli ✔", True), ("Vanilla Custard Cream", False), ("Chocolate Silk Ganache", False)]:
        btn = client.box(parent=step3_opts, name=f"Opt_{opt[:6]}", layout="horizontal", padding=[6, 14, 6, 14], fill=COLOR_BLUSH if active else COLOR_CANVAS, stroke=COLOR_RUBY if active else COLOR_CUSTARD, cornerRadius=8)
        client.create_text(parent=btn, text=opt, fontSize=11, fontStyle="Bold" if active else "Medium", fill=COLOR_RUBY if active else COLOR_TEXT_PRIMARY)

    # Step 4: Frosting Luar
    step4_box = client.box(parent=right_controls, name="Step4_Frosting", layout="vertical", gap=6, width=716)
    client.create_text(parent=step4_box, text="4. Frosting & Krim Luar", fontSize=13, fontStyle="Bold", fill=COLOR_TEXT_PRIMARY)
    step4_opts = client.box(parent=step4_box, name="Step4Opts", layout="horizontal", gap=10)
    for opt, active in [("Buttercream Vanilla", False), ("Buttercream Pink Strawberry ✔", True), ("Drip Ganache Coklat Leleh", False)]:
        btn = client.box(parent=step4_opts, name=f"Opt_{opt[:6]}", layout="horizontal", padding=[6, 14, 6, 14], fill=COLOR_BLUSH if active else COLOR_CANVAS, stroke=COLOR_RUBY if active else COLOR_CUSTARD, cornerRadius=8)
        client.create_text(parent=btn, text=opt, fontSize=11, fontStyle="Bold" if active else "Medium", fill=COLOR_RUBY if active else COLOR_TEXT_PRIMARY)

    # Step 5: Topping Pilihan
    step5_box = client.box(parent=right_controls, name="Step5_Topping", layout="vertical", gap=6, width=716)
    client.create_text(parent=step5_box, text="5. Topping & Hiasan Permukaan", fontSize=13, fontStyle="Bold", fill=COLOR_TEXT_PRIMARY)
    step5_opts = client.box(parent=step5_box, name="Step5Opts", layout="horizontal", gap=10)
    for opt, active in [("Buah Stroberi Segar ✔", True), ("Serpihan Coklat Serut", False), ("Macaron Mini ✔", True), ("Edible Flowers", False)]:
        btn = client.box(parent=step5_opts, name=f"Opt_{opt[:6]}", layout="horizontal", padding=[6, 12, 6, 12], fill=COLOR_BLUSH if active else COLOR_CANVAS, stroke=COLOR_RUBY if active else COLOR_CUSTARD, cornerRadius=8)
        client.create_text(parent=btn, text=opt, fontSize=11, fontStyle="Bold" if active else "Medium", fill=COLOR_RUBY if active else COLOR_TEXT_PRIMARY)

    # Step 6: Input Teks Kaligrafi (Maks 30 Karakter)
    step6_box = client.box(parent=right_controls, name="Step6_Calligraphy", layout="vertical", gap=6, width=716)
    step6_header = client.box(parent=step6_box, name="Step6Header", layout="horizontal", width=716, mainAlign="spaceBetween")
    client.create_text(parent=step6_header, text="6. Pesan di Atas Kue (Font Kaligrafi Khusus)", fontSize=13, fontStyle="Bold", fill=COLOR_TEXT_PRIMARY)
    client.create_text(parent=step6_header, text="24 / 30 Karakter", fontSize=11, fontStyle="Bold", fill=COLOR_RUBY)
    
    text_input = client.box(
        parent=step6_box,
        name="CalligraphyTextInput",
        layout="horizontal",
        width=716, height=42,
        padding=[8, 16, 8, 16],
        fill=COLOR_CARD,
        stroke=COLOR_RUBY,
        strokeWeight=1.5,
        cornerRadius=10
    )
    client.create_text(parent=text_input, text="Happy Sweet 17th Kirana!", fontSize=14, fontFamily=FONT_HEADING, fontStyle="Bold", fill=COLOR_TEXT_PRIMARY)

    # Sticky Bottom Real-Time Price Bar (Y: 795, W: 1440)
    bottom_bar = client.box(
        parent=screen,
        name="StickyBottomPriceBar",
        layout="horizontal",
        x=0, y=795, width=1440, height=105,
        padding=[0, 60, 0, 60],
        mainAlign="spaceBetween",
        crossAlign="center",
        fill=COLOR_CARD,
        stroke=COLOR_CUSTARD,
        strokeWeight=1,
        effects=[{"type": "dropShadow", "color": "#3B221915", "offset": [0, -4], "radius": 16}]
    )

    # Price info left
    price_info = client.box(parent=bottom_bar, name="PriceInfoGroup", layout="horizontal", gap=24, crossAlign="center")
    price_col = client.box(parent=price_info, name="PriceCol", layout="vertical", gap=2)
    client.create_text(parent=price_col, text="Total Biaya Custom Kue:", fontSize=12, fontStyle="Bold", fill=COLOR_TEXT_MUTED)
    client.create_text(parent=price_col, text="Rp 385.000", fontSize=26, fontFamily=FONT_HEADING, fontStyle="Bold", fill=COLOR_RUBY)
    
    time_badge = client.box(parent=price_info, name="TimeBadge", layout="horizontal", padding=[8, 14, 8, 14], fill=COLOR_CANVAS, cornerRadius=10)
    client.create_text(parent=time_badge, text="⏱ Estimasi Pengerjaan: 24 Jam (Siap Kirim Besok)", fontSize=12, fontStyle="SemiBold", fill=COLOR_TEXT_PRIMARY)

    # Actions right
    bottom_actions = client.box(parent=bottom_bar, name="BottomActions", layout="horizontal", gap=14, crossAlign="center")
    
    btn_save = client.box(parent=bottom_actions, name="BtnSaveDraft", layout="horizontal", padding=[12, 18, 12, 18], fill=COLOR_CARD, stroke=COLOR_TEXT_MUTED, strokeWeight=1, cornerRadius=12)
    client.create_text(parent=btn_save, text="Simpan Draf", fontSize=13, fontStyle="SemiBold", fill=COLOR_TEXT_PRIMARY)

    btn_finish = client.box(
        parent=bottom_actions,
        name="BtnFinishAddToCart",
        layout="horizontal",
        padding=[12, 24, 12, 24],
        fill=COLOR_RUBY,
        cornerRadius=12,
        effects=[{"type": "dropShadow", "color": "#E04D6850", "offset": [0, 4], "radius": 12}]
    )
    client.create_text(parent=btn_finish, text="Selesai & Masukkan Keranjang ➔", fontSize=14, fontStyle="Bold", fill="#FFFFFF")

    print("  ✓ Screen 04 rendered successfully.")
    return screen


# ==============================================================================
# SCREEN 05: SLIDE-OVER CART DRAWER
# ==============================================================================
def build_screen_05_cart_drawer(client: FigCraftClient, offset_x: float = 1600, offset_y: float = 1050):
    print("-> Rendering Screen 05: Slide-Over Cart Drawer...")
    screen = client.create_frame(
        name="Layar 05 - Slide-Over Cart Drawer",
        x=offset_x, y=offset_y,
        width=1440, height=900,
        fill=COLOR_CANVAS
    )

    # Background shop content underneath
    render_header(client, screen, active_item="shop", cart_count="3")

    # Dark backdrop overlay for drawer
    client.create_rect(
        parent=screen,
        name="DrawerBackdropOverlay",
        x=0, y=0, width=1440, height=900,
        fill=COLOR_OVERLAY
    )

    # Slide-Over Right Drawer (W: 460, H: 900, X: 980)
    drawer = client.box(
        parent=screen,
        name="SlideOverCartDrawer",
        layout="vertical",
        x=980, y=0, width=460, height=900,
        padding=0,
        mainAlign="spaceBetween",
        crossAlign="center",
        fill=COLOR_CARD,
        effects=[{"type": "dropShadow", "color": "#3B221940", "offset": [-12, 0], "radius": 32}]
    )

    # Drawer Header (H: 70)
    d_header = client.box(
        parent=drawer,
        name="DrawerHeader",
        layout="horizontal",
        width=460, height=70,
        padding=[0, 24, 0, 24],
        mainAlign="spaceBetween",
        crossAlign="center",
        stroke=COLOR_CUSTARD,
        strokeWeight=1
    )
    client.create_text(parent=d_header, text="Keranjang Belanja (3 Item)", fontSize=18, fontFamily=FONT_HEADING, fontStyle="Bold", fill=COLOR_TEXT_PRIMARY)
    
    btn_close_d = client.box(parent=d_header, name="BtnCloseDrawer", layout="horizontal", width=32, height=32, mainAlign="center", crossAlign="center", fill=COLOR_CANVAS, cornerRadius=16)
    client.create_text(parent=btn_close_d, text="✕", fontSize=13, fontStyle="Bold", fill=COLOR_TEXT_PRIMARY)

    # Drawer Scrollable Content Area (H: 645)
    d_content = client.box(
        parent=drawer,
        name="DrawerContentList",
        layout="vertical",
        width=460, height=645,
        padding=[12, 22, 12, 22],
        gap=12,
        mainAlign="min",
        crossAlign="center"
    )

    # Item 1: Signature Strawberry Ganache
    item1 = client.box(parent=d_content, name="CartItem_1", layout="horizontal", width=416, padding=[8, 12, 8, 12], gap=10, fill=COLOR_CANVAS, cornerRadius=10)
    client.circle_arc(parent=item1, name="Thumb1", cx=20, cy=20, r=16, fill=COLOR_RUBY)
    item1_info = client.box(parent=item1, name="Item1Info", layout="vertical", gap=2, width=290)
    client.create_text(parent=item1_info, text="Signature Strawberry Ganache", fontSize=12, fontStyle="Bold", fill=COLOR_TEXT_PRIMARY)
    client.create_text(parent=item1_info, text="Dia. 18cm • +Lilin Angka & Topper", fontSize=10, fill=COLOR_TEXT_MUTED)
    client.create_text(parent=item1_info, text="Rp 425.000", fontSize=12, fontStyle="Bold", fill=COLOR_RUBY)
    client.create_text(parent=item1, text="1x 🗑", fontSize=11, fill=COLOR_TEXT_MUTED)

    # Item 2: Custom Cake Kirana
    item2 = client.box(parent=d_content, name="CartItem_2", layout="horizontal", width=416, padding=[8, 12, 8, 12], gap=10, fill=COLOR_CANVAS, cornerRadius=10)
    client.circle_arc(parent=item2, name="Thumb2", cx=20, cy=20, r=16, fill=COLOR_TEXT_PRIMARY)
    item2_info = client.box(parent=item2, name="Item2Info", layout="vertical", gap=2, width=290)
    client.create_text(parent=item2_info, text="Custom Cake: Kirana Sweet 17", fontSize=12, fontStyle="Bold", fill=COLOR_TEXT_PRIMARY)
    client.create_text(parent=item2_info, text="Bulat 20cm • Coklat Fudge • Pink Frosting", fontSize=10, fill=COLOR_TEXT_MUTED)
    client.create_text(parent=item2_info, text="Rp 385.000", fontSize=12, fontStyle="Bold", fill=COLOR_RUBY)
    client.create_text(parent=item2, text="1x 🗑", fontSize=11, fill=COLOR_TEXT_MUTED)

    # Item 3: Madagascar Vanilla Slice
    item3 = client.box(parent=d_content, name="CartItem_3", layout="horizontal", width=416, padding=[8, 12, 8, 12], gap=10, fill=COLOR_CANVAS, cornerRadius=10)
    client.circle_arc(parent=item3, name="Thumb3", cx=20, cy=20, r=16, fill=COLOR_CUSTARD)
    item3_info = client.box(parent=item3, name="Item3Info", layout="vertical", gap=2, width=290)
    client.create_text(parent=item3_info, text="Madagascar Vanilla Slice Cake", fontSize=12, fontStyle="Bold", fill=COLOR_TEXT_PRIMARY)
    client.create_text(parent=item3_info, text="Ready Stock Instan (2 Potong)", fontSize=10, fill=COLOR_TEXT_MUTED)
    client.create_text(parent=item3_info, text="Rp 90.000 (2x @45k)", fontSize=12, fontStyle="Bold", fill=COLOR_RUBY)
    client.create_text(parent=item3, text="2x 🗑", fontSize=11, fill=COLOR_TEXT_MUTED)

    # Date & Slot Picker Box
    date_box = client.box(
        parent=d_content,
        name="DateSlotPickerBox",
        layout="vertical",
        width=416,
        padding=12,
        gap=6,
        fill=COLOR_CANVAS,
        stroke=COLOR_CUSTARD,
        strokeWeight=1,
        cornerRadius=10
    )
    client.create_text(parent=date_box, text="📅 Pilih Jadwal Pengantaran Kue:", fontSize=12, fontStyle="Bold", fill=COLOR_TEXT_PRIMARY)
    
    # Date Pills
    date_pills = client.box(parent=date_box, name="DatePills", layout="horizontal", gap=8)
    d1 = client.box(parent=date_pills, name="D1", layout="horizontal", padding=[5, 10, 5, 10], fill=COLOR_BLUSH, stroke=COLOR_RUBY, cornerRadius=8)
    client.create_text(parent=d1, text="Besok, 8 Nov ★", fontSize=11, fontStyle="Bold", fill=COLOR_RUBY)
    d2 = client.box(parent=date_pills, name="D2", layout="horizontal", padding=[5, 10, 5, 10], fill=COLOR_CARD, cornerRadius=8)
    client.create_text(parent=d2, text="Senin, 9 Nov", fontSize=11, fill=COLOR_TEXT_PRIMARY)
    d3 = client.box(parent=date_pills, name="D3", layout="horizontal", padding=[5, 10, 5, 10], fill=COLOR_CARD, cornerRadius=8)
    client.create_text(parent=d3, text="Kalender ▾", fontSize=11, fill=COLOR_TEXT_PRIMARY)

    # Time Slot Pills
    client.create_text(parent=date_box, text="Slot Jam Pengantaran:", fontSize=11, fontStyle="SemiBold", fill=COLOR_TEXT_MUTED)
    time_pills = client.box(parent=date_box, name="TimePills", layout="horizontal", gap=8)
    for slot, active in [("09.00 - 12.00", False), ("13.00 - 16.00 ✔", True), ("16.00 - 19.00", False)]:
        t_box = client.box(parent=time_pills, name=f"Slot_{slot[:4]}", layout="horizontal", padding=[4, 8, 4, 8], fill=COLOR_BLUSH if active else COLOR_CARD, stroke=COLOR_RUBY if active else COLOR_CUSTARD, cornerRadius=6)
        client.create_text(parent=t_box, text=slot, fontSize=10, fontStyle="Bold" if active else "Regular", fill=COLOR_RUBY if active else COLOR_TEXT_PRIMARY)

    # Free Greeting Card Form
    card_form = client.box(
        parent=d_content,
        name="FreeGreetingCardBox",
        layout="vertical",
        width=416,
        padding=12,
        gap=6,
        fill=COLOR_CARD,
        stroke=COLOR_CUSTARD,
        strokeWeight=1,
        cornerRadius=10
    )
    card_title_row = client.box(parent=card_form, name="TitleRow", layout="horizontal", width=392, mainAlign="spaceBetween")
    client.create_text(parent=card_title_row, text="💌 Kartu Ucapan Personal", fontSize=12, fontStyle="Bold", fill=COLOR_TEXT_PRIMARY)
    free_tag = client.box(parent=card_title_row, name="FreeTag", layout="horizontal", padding=[2, 8, 2, 8], fill=COLOR_BLUSH, cornerRadius=6)
    client.create_text(parent=free_tag, text="GRATIS", fontSize=10, fontStyle="Bold", fill=COLOR_RUBY)

    # Input Fields
    client.create_text(parent=card_form, text="Kepada: Kirana Pramudita  |  Dari: Mama & Papa", fontSize=11, fontStyle="Medium", fill=COLOR_TEXT_PRIMARY)
    msg_box = client.box(parent=card_form, name="MsgBox", layout="horizontal", width=392, padding=8, fill=COLOR_CANVAS, cornerRadius=6)
    client.create_text(parent=msg_box, text="\"Selamat sweet 17th Kirana sayang! Semoga harimu semanis kue ini.\" (Cetak Kaligrafi)", width=376, fontSize=11, fontStyle="Regular", fill=COLOR_TEXT_MUTED)

    # Drawer Sticky Footer (H: 180)
    d_footer = client.box(
        parent=drawer,
        name="DrawerFooterSummary",
        layout="vertical",
        width=460, height=180,
        padding=[14, 24, 18, 24],
        gap=10,
        stroke=COLOR_CUSTARD,
        strokeWeight=1,
        fill=COLOR_CARD
    )
    
    # Subtotal breakdown
    subtotal_row = client.box(parent=d_footer, name="SubtotalRow", layout="horizontal", width=412, mainAlign="spaceBetween")
    client.create_text(parent=subtotal_row, text="Subtotal Produk (3 item)", fontSize=12, fill=COLOR_TEXT_MUTED)
    client.create_text(parent=subtotal_row, text="Rp 900.000", fontSize=12, fontStyle="Bold", fill=COLOR_TEXT_PRIMARY)

    discount_row = client.box(parent=d_footer, name="DiscountRow", layout="horizontal", width=412, mainAlign="spaceBetween")
    client.create_text(parent=discount_row, text="Diskon Promo Sweet 17", fontSize=12, fill=COLOR_RUBY)
    client.create_text(parent=discount_row, text="- Rp 50.000", fontSize=12, fontStyle="Bold", fill=COLOR_RUBY)

    total_row = client.box(parent=d_footer, name="TotalRow", layout="horizontal", width=412, mainAlign="spaceBetween", crossAlign="center")
    client.create_text(parent=total_row, text="Total Belanja:", fontSize=14, fontStyle="Bold", fill=COLOR_TEXT_PRIMARY)
    client.create_text(parent=total_row, text="Rp 850.000", fontSize=21, fontFamily=FONT_HEADING, fontStyle="Bold", fill=COLOR_RUBY)

    # Checkout CTA Button
    btn_checkout = client.box(
        parent=d_footer,
        name="BtnDrawerCheckout",
        layout="horizontal",
        width=412, height=46,
        mainAlign="center",
        crossAlign="center",
        fill=COLOR_RUBY,
        cornerRadius=12,
        effects=[{"type": "dropShadow", "color": "#E04D6840", "offset": [0, 4], "radius": 12}]
    )
    client.create_text(parent=btn_checkout, text="Lanjut ke Pembayaran Checkout ➔", fontSize=14, fontStyle="Bold", fill="#FFFFFF")

    print("  ✓ Screen 05 rendered successfully.")
    return screen


# ==============================================================================
# SCREEN 06: CHECKOUT & REVIEW PESANAN
# ==============================================================================
def build_screen_06_checkout(client: FigCraftClient, offset_x: float = 3200, offset_y: float = 1050):
    print("-> Rendering Screen 06: Checkout & Review...")
    screen = client.create_frame(
        name="Layar 06 - Checkout & Review Pesanan",
        x=offset_x, y=offset_y,
        width=1440, height=900,
        fill=COLOR_CANVAS
    )

    # Checkout Minimalist Header
    c_header = client.box(
        parent=screen,
        name="CheckoutHeader",
        layout="horizontal",
        x=0, y=0, width=1440, height=75,
        padding=[0, 60, 0, 60],
        mainAlign="spaceBetween",
        crossAlign="center",
        fill=COLOR_CARD,
        stroke=COLOR_CUSTARD,
        strokeWeight=1
    )
    client.create_text(parent=c_header, text="BerryCrumb  •  Checkout Aman & Terenkripsi", fontSize=18, fontFamily=FONT_HEADING, fontStyle="Bold", fill=COLOR_TEXT_PRIMARY)

    # Step Progress Tracker
    stepper = client.box(parent=c_header, name="CheckoutSteps", layout="horizontal", gap=16, crossAlign="center")
    client.create_text(parent=stepper, text="1. Keranjang ✔", fontSize=12, fontStyle="Bold", fill=COLOR_TEXT_MUTED)
    client.create_text(parent=stepper, text="➔", fontSize=12, fill=COLOR_TEXT_MUTED)
    client.create_text(parent=stepper, text="2. Alamat & Pengiriman ●", fontSize=12, fontStyle="Bold", fill=COLOR_RUBY)
    client.create_text(parent=stepper, text="➔", fontSize=12, fill=COLOR_TEXT_MUTED)
    client.create_text(parent=stepper, text="3. Pembayaran Instan", fontSize=12, fontStyle="Bold", fill=COLOR_TEXT_MUTED)

    # 2-Column Checkout Layout (W: 1320, X: 60, Y: 95)
    # Left Column: Forms (W: 760, H: 770)
    left_form = client.box(
        parent=screen,
        name="CheckoutLeftForms",
        layout="vertical",
        x=60, y=95, width=760, height=770,
        gap=14,
        mainAlign="min",
        crossAlign="center"
    )

    # Card 1: Alamat Pengiriman & Titik GPS Pinpoint
    addr_card = client.box(
        parent=left_form,
        name="ShippingAddressCard",
        layout="vertical",
        width=760,
        padding=18,
        gap=10,
        fill=COLOR_CARD,
        stroke=COLOR_CUSTARD,
        strokeWeight=1,
        cornerRadius=16,
        effects=[{"type": "dropShadow", "color": "#3B221908", "offset": [0, 4], "radius": 12}]
    )
    addr_header = client.box(parent=addr_card, name="AddrHeader", layout="horizontal", width=724, mainAlign="spaceBetween")
    client.create_text(parent=addr_header, text="📍 Alamat Tujuan Pengiriman Kue", fontSize=15, fontStyle="Bold", fill=COLOR_TEXT_PRIMARY)
    client.create_text(parent=addr_header, text="Ubah Alamat", fontSize=12, fontStyle="Bold", fill=COLOR_RUBY)

    client.create_text(parent=addr_card, text="Penerima: Kirana Pramudita  •  0812-3456-7890", fontSize=13, fontStyle="Bold", fill=COLOR_TEXT_PRIMARY)
    client.create_text(parent=addr_card, text="Jl. Gunawarman No. 42, RT 05 / RW 02, Kebayoran Baru, Jakarta Selatan, DKI Jakarta 12180", fontSize=13, fill=COLOR_TEXT_MUTED)

    # Mockup Map Pinpoint Box
    map_box = client.box(
        parent=addr_card,
        name="MapPinpointBox",
        layout="horizontal",
        width=724, height=85,
        padding=[10, 16, 10, 16],
        gap=12,
        mainAlign="min",
        crossAlign="center",
        fill=COLOR_CANVAS,
        stroke=COLOR_CUSTARD,
        strokeWeight=1,
        cornerRadius=10
    )
    client.circle_arc(parent=map_box, name="GpsPinIcon", cx=16, cy=16, r=13, fill=COLOR_RUBY)
    map_text = client.box(parent=map_box, name="MapText", layout="vertical", gap=2)
    client.create_text(parent=map_text, text="Pin Point GPS Akurat Kurir: -6.23841, 106.80912 (Akurasi ±2 meter)", fontSize=12, fontStyle="Bold", fill=COLOR_TEXT_PRIMARY)
    client.create_text(parent=map_text, text="Titik gerbang utama terdeteksi. Kurir instan mobil dingin akan meluncur tepat di lobby.", fontSize=11, fill=COLOR_TEXT_MUTED)

    # Card 2: Special Chilled Handling Courier Instruction
    courier_note = client.box(
        parent=left_form,
        name="SpecialCourierInstructionCard",
        layout="horizontal",
        width=760,
        padding=[12, 18, 12, 18],
        gap=12,
        crossAlign="center",
        fill=COLOR_CANVAS,
        stroke=COLOR_CUSTARD,
        strokeWeight=1.5,
        cornerRadius=14
    )
    client.circle_arc(parent=courier_note, name="ColdIcon", cx=16, cy=16, r=13, fill=COLOR_RUBY)
    c_note_text = client.box(parent=courier_note, name="CNoteText", layout="vertical", gap=2, width=660)
    client.create_text(parent=c_note_text, text="❄ Instruksi Khusus Kurir Penanganan Kue Dingin:", fontSize=12, fontStyle="Bold", fill=COLOR_TEXT_PRIMARY)
    client.create_text(parent=c_note_text, text="\"Bawa mobil perlahan, dilarang ditumpuk/miring. Wajib simpan dalam cooler box bersuhu chiller 4°C selama pengantaran.\"", fontSize=11, fontStyle="Medium", fill=COLOR_RUBY)

    # Card 3: Payment Method Selector
    pay_card = client.box(
        parent=left_form,
        name="PaymentMethodCard",
        layout="vertical",
        width=760,
        padding=18,
        gap=12,
        fill=COLOR_CARD,
        stroke=COLOR_CUSTARD,
        strokeWeight=1,
        cornerRadius=16,
        effects=[{"type": "dropShadow", "color": "#3B221908", "offset": [0, 4], "radius": 12}]
    )
    client.create_text(parent=pay_card, text="💳 Pilih Metode Pembayaran Terverifikasi", fontSize=15, fontStyle="Bold", fill=COLOR_TEXT_PRIMARY)

    # Method 1: QRIS Instant (Selected)
    qris_opt = client.box(parent=pay_card, name="PayQRIS", layout="horizontal", width=724, padding=12, gap=12, fill=COLOR_BLUSH, stroke=COLOR_RUBY, strokeWeight=1.5, cornerRadius=12, crossAlign="center")
    client.create_text(parent=qris_opt, text="◉", fontSize=15, fontStyle="Bold", fill=COLOR_RUBY)
    q_info = client.box(parent=qris_opt, name="QInfo", layout="vertical", gap=2, width=620)
    client.create_text(parent=q_info, text="QRIS Instant (GoPay, OVO, ShopeePay, DANA, BCA Mobile)", fontSize=13, fontStyle="Bold", fill=COLOR_TEXT_PRIMARY)
    client.create_text(parent=q_info, text="Verifikasi otomatis tanpa perlu upload bukti transfer. Kode QR langsung muncul.", fontSize=11, fill=COLOR_TEXT_MUTED)

    # Method 2: Virtual Account Bank
    va_opt = client.box(parent=pay_card, name="PayVA", layout="horizontal", width=724, padding=12, gap=12, fill=COLOR_CANVAS, stroke=COLOR_CUSTARD, strokeWeight=1, cornerRadius=12, crossAlign="center")
    client.create_text(parent=va_opt, text="○", fontSize=15, fill=COLOR_TEXT_MUTED)
    va_info = client.box(parent=va_opt, name="VAInfo", layout="vertical", gap=2, width=620)
    client.create_text(parent=va_info, text="Virtual Account (BCA, Mandiri, BRI, BNI)", fontSize=13, fontStyle="Bold", fill=COLOR_TEXT_PRIMARY)
    client.create_text(parent=va_info, text="Nomor rekening virtual unik dibuat otomatis.", fontSize=11, fill=COLOR_TEXT_MUTED)

    # Method 3: Credit/Debit Card
    cc_opt = client.box(parent=pay_card, name="PayCC", layout="horizontal", width=724, padding=12, gap=12, fill=COLOR_CANVAS, stroke=COLOR_CUSTARD, strokeWeight=1, cornerRadius=12, crossAlign="center")
    client.create_text(parent=cc_opt, text="○", fontSize=15, fill=COLOR_TEXT_MUTED)
    cc_info = client.box(parent=cc_opt, name="CCInfo", layout="vertical", gap=2, width=620)
    client.create_text(parent=cc_info, text="Kartu Kredit / Debit Online (Visa, Mastercard, JCB)", fontSize=13, fontStyle="Bold", fill=COLOR_TEXT_PRIMARY)
    client.create_text(parent=cc_info, text="Dilindungi 3D-Secure OTP Bank.", fontSize=11, fill=COLOR_TEXT_MUTED)

    # Right Column: Order Review & Final Payment (W: 520, X: 840, Y: 95)
    review_card = client.box(
        parent=screen,
        name="CheckoutRightSummary",
        layout="vertical",
        x=840, y=95, width=540, height=770,
        padding=24,
        gap=16,
        mainAlign="spaceBetween",
        crossAlign="center",
        fill=COLOR_CARD,
        stroke=COLOR_CUSTARD,
        strokeWeight=1,
        cornerRadius=20,
        effects=[{"type": "dropShadow", "color": "#3B221915", "offset": [0, 8], "radius": 24}]
    )

    # Summary Header
    summary_top = client.box(parent=review_card, name="SummaryTop", layout="vertical", width=492, gap=14)
    client.create_text(parent=summary_top, text="Ringkasan Pesanan (3 Item)", fontSize=19, fontFamily=FONT_HEADING, fontStyle="Bold", fill=COLOR_TEXT_PRIMARY)

    # Items Mini List
    items_list = client.box(parent=summary_top, name="ReviewItemsList", layout="vertical", gap=10, width=492)
    
    r_item1 = client.box(parent=items_list, name="R1", layout="horizontal", width=492, mainAlign="spaceBetween")
    client.create_text(parent=r_item1, text="1x Signature Strawberry Ganache (18cm)", fontSize=12, fill=COLOR_TEXT_PRIMARY)
    client.create_text(parent=r_item1, text="Rp 425.000", fontSize=12, fontStyle="Bold", fill=COLOR_TEXT_PRIMARY)

    r_item2 = client.box(parent=items_list, name="R2", layout="horizontal", width=492, mainAlign="spaceBetween")
    client.create_text(parent=r_item2, text="1x Custom Cake Sweet 17 Kirana (20cm)", fontSize=12, fill=COLOR_TEXT_PRIMARY)
    client.create_text(parent=r_item2, text="Rp 385.000", fontSize=12, fontStyle="Bold", fill=COLOR_TEXT_PRIMARY)

    r_item3 = client.box(parent=items_list, name="R3", layout="horizontal", width=492, mainAlign="spaceBetween")
    client.create_text(parent=r_item3, text="2x Madagascar Vanilla Slice Cake", fontSize=12, fill=COLOR_TEXT_PRIMARY)
    client.create_text(parent=r_item3, text="Rp 90.000", fontSize=12, fontStyle="Bold", fill=COLOR_TEXT_PRIMARY)

    # Divider Line
    client.create_rect(parent=summary_top, name="Divider", width=492, height=1, fill=COLOR_CUSTARD)

    # Financial Cost Breakdown
    cost_box = client.box(parent=summary_top, name="CostBreakdown", layout="vertical", gap=8, width=492)
    
    c_sub = client.box(parent=cost_box, name="CSub", layout="horizontal", width=492, mainAlign="spaceBetween")
    client.create_text(parent=c_sub, text="Total Belanja Produk", fontSize=13, fill=COLOR_TEXT_MUTED)
    client.create_text(parent=c_sub, text="Rp 900.000", fontSize=13, fontStyle="SemiBold", fill=COLOR_TEXT_PRIMARY)

    c_ship = client.box(parent=cost_box, name="CShip", layout="horizontal", width=492, mainAlign="spaceBetween")
    client.create_text(parent=c_ship, text="Ongkir Kurir Mobil Chilled Box", fontSize=13, fill=COLOR_TEXT_MUTED)
    client.create_text(parent=c_ship, text="Rp 25.000", fontSize=13, fontStyle="SemiBold", fill=COLOR_TEXT_PRIMARY)

    c_ins = client.box(parent=cost_box, name="CIns", layout="horizontal", width=492, mainAlign="spaceBetween")
    client.create_text(parent=c_ins, text="Asuransi Garansi Kue Utuh & Dingin", fontSize=13, fill=COLOR_TEXT_MUTED)
    client.create_text(parent=c_ins, text="GRATIS", fontSize=12, fontStyle="Bold", fill=COLOR_RUBY)

    c_disc = client.box(parent=cost_box, name="CDisc", layout="horizontal", width=492, mainAlign="spaceBetween")
    client.create_text(parent=c_disc, text="Voucher Diskon Peluncuran Web", fontSize=13, fill=COLOR_RUBY)
    client.create_text(parent=c_disc, text="- Rp 50.000", fontSize=13, fontStyle="Bold", fill=COLOR_RUBY)

    # Final Total Box
    total_banner = client.box(
        parent=review_card,
        name="TotalBanner",
        layout="vertical",
        width=492,
        padding=16,
        gap=4,
        fill=COLOR_CANVAS,
        stroke=COLOR_CUSTARD,
        strokeWeight=1,
        cornerRadius=14
    )
    t_row = client.box(parent=total_banner, name="TRow", layout="horizontal", width=460, mainAlign="spaceBetween", crossAlign="center")
    client.create_text(parent=t_row, text="Total Tagihan:", fontSize=15, fontStyle="Bold", fill=COLOR_TEXT_PRIMARY)
    client.create_text(parent=t_row, text="Rp 875.000", fontSize=26, fontFamily=FONT_HEADING, fontStyle="Bold", fill=COLOR_RUBY)
    client.create_text(parent=total_banner, text="Sudah termasuk PPN 11% & Kemasan Cold-Lock Bag", fontSize=11, fill=COLOR_TEXT_MUTED)

    # Bottom Actions: Pay Button & Security Badges
    bottom_action_area = client.box(parent=review_card, name="BottomActionArea", layout="vertical", width=492, gap=12, crossAlign="center")
    
    btn_pay = client.box(
        parent=bottom_action_area,
        name="BtnPayNow",
        layout="horizontal",
        width=492, height=54,
        mainAlign="center",
        crossAlign="center",
        fill=COLOR_RUBY,
        cornerRadius=14,
        effects=[{"type": "dropShadow", "color": "#E04D6850", "offset": [0, 6], "radius": 16}]
    )
    client.create_text(parent=btn_pay, text="Bayar Sekarang (Rp 875.000) 🔒", fontSize=16, fontStyle="Bold", fill="#FFFFFF")

    # Security Assurance
    client.create_text(parent=bottom_action_area, text="🔒 256-Bit SSL Enkripsi Perbankan  •  Garansi 100% Kue Tiba Dingin", fontSize=11, fontStyle="Medium", fill=COLOR_TEXT_MUTED)

    print("  ✓ Screen 06 rendered successfully.")
    return screen


# ==============================================================================
# MAIN BATCH RENDER EXECUTOR
# ==============================================================================
def main():
    print("==================================================================")
    print("   BerryCrumb Patisserie - Fast Batch UI Screen Generator (v3.0)  ")
    print("   Connecting to FigCraft via JSON-RPC port 7979...               ")
    print("==================================================================")

    client = FigCraftClient(host="127.0.0.1", port=7979, auto_batch=True, strict=True)
    tokens = DesignTokens()

    print("\n[Step 1/4] Preparing Canvas & Syncing Design Tokens...")
    client.clear_canvas()
    tokens.sync_to_figcraft_styles(client)

    print("\n[Step 2/4] Rendering 6 Responsive Desktop Screens (1440x900)...")
    start_time = time.time()

    # Layout Grid: 3 Columns x 2 Rows
    s1 = build_screen_01_beranda(client, offset_x=0, offset_y=0)
    s2 = build_screen_02_katalog(client, offset_x=1600, offset_y=0)
    s3 = build_screen_03_modal_quick_view(client, offset_x=3200, offset_y=0)

    s4 = build_screen_04_custom_builder(client, offset_x=0, offset_y=1050)
    s5 = build_screen_05_cart_drawer(client, offset_x=1600, offset_y=1050)
    s6 = build_screen_06_checkout(client, offset_x=3200, offset_y=1050)

    all_screens = [s1, s2, s3, s4, s5, s6]
    build_time = time.time() - start_time
    print(f"\nAll 6 screens generated in {build_time:.2f} seconds!")

    print("\n[Step 3/4] Running Automated Layout Auditor (verify_layout)...")
    report = client.verify_layout(all_screens, tolerance=2.0)
    print(f"Layout Audit Result: ok={report['ok']}, violations={report['violation_count']}")
    if not report["ok"]:
        for v in report["violations"]:
            print(f"  [VIOLATION] Screen: {v.get('screen')}, Kind: {v.get('kind')}, Detail: {v}")
    assert report["ok"], f"Layout verification failed with {report['violation_count']} violations"

    print("\n[Step 4/4] Saving Design File & Exporting High-Res PNGs...")
    figcraft_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "berrycrumb_patisserie.figcraft")
    save_res = client.save_file(figcraft_file)
    print(f"  ✓ Saved to: {save_res['path']}")

    output_png = os.path.join(os.path.dirname(os.path.abspath(__file__)), "berrycrumb_preview.png")
    export_result = client.export_page(output_png)
    print(f"  ✓ Canvas Preview PNG saved to: {output_png} (result: {export_result})")

    exports_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "exports")
    frames_exported = client.export_frames(all_screens, output_dir=exports_dir)
    print(f"  ✓ Exported {len(frames_exported)} individual screen frames to: {exports_dir}")
    for item in frames_exported:
        print(f"     - {os.path.basename(item['path'])} ({item['bytes']} bytes)")

    print(f"\nEngine Performance: Total RPC Time = {client.total_rpc_ms:.1f} ms | Last Batch Flush = {client.last_flush_ms:.1f} ms")
    client.close()
    print("\n==================================================================")
    print("   BATCH RENDERING & AUDIT COMPLETED SUCCESSFULLY!                ")
    print("==================================================================")


if __name__ == "__main__":
    main()
