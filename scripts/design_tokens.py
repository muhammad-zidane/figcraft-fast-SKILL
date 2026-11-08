"""
design_tokens.py (Fitur #5) - Reusable Design System Tokens & Native Style Sync.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List
from figcraft_ui import FigCraftClient


@dataclass
class DesignTokens:
    brand_name: str = "BerryCrumb"
    # Colors
    bg_canvas: str = "#FFF8F0"       # Vanilla Cream
    bg_card: str = "#FFFFFF"         # Vanilla Murni
    text_primary: str = "#3B2219"    # Coklat Tua
    text_muted: str = "#70483C"      # Coklat Susu
    accent_custard: str = "#F4E7D3"  # Vanilla Custard
    accent_ruby: str = "#E04D68"     # Stroberi Ruby
    accent_blush: str = "#FFD6DC"    # Stroberi Blush
    overlay_dark: str = "#3B221980"  # Backdrop Overlay
    white: str = "#FFFFFF"

    # Typography
    font_heading: str = "Playfair Display"
    font_body: str = "Plus Jakarta Sans"

    # Type Scale (px)
    size_h1: float = 42.0
    size_h2: float = 28.0
    size_h3: float = 20.0
    size_title: float = 17.0
    size_body: float = 13.0
    size_caption: float = 11.0

    # Radii
    radius_sm: float = 8.0
    radius_md: float = 12.0
    radius_lg: float = 18.0
    radius_xl: float = 24.0
    radius_pill: float = 20.0

    # Shadows
    shadow_sm: List[Dict[str, Any]] = field(default_factory=lambda: [
        {"type": "dropShadow", "color": "#3B22190A", "offset": [0, 3], "radius": 8}
    ])
    shadow_md: List[Dict[str, Any]] = field(default_factory=lambda: [
        {"type": "dropShadow", "color": "#3B221912", "offset": [0, 6], "radius": 16}
    ])
    shadow_cta: List[Dict[str, Any]] = field(default_factory=lambda: [
        {"type": "dropShadow", "color": "#E04D6840", "offset": [0, 4], "radius": 12}
    ])

    def sync_to_figcraft_styles(self, client: FigCraftClient):
        """Registers core color and text tokens as native FigCraft styles idempotently (Fitur #7)."""
        existing_names = set()
        try:
            res = client.execute("style.list", {})
            styles_list = res.get("styles", res) if isinstance(res, dict) else res
            if isinstance(styles_list, list):
                for s in styles_list:
                    if isinstance(s, dict) and "name" in s:
                        existing_names.add(s["name"])
        except Exception:
            pass

        color_map = {
            f"{self.brand_name}/Canvas Vanilla Cream": self.bg_canvas,
            f"{self.brand_name}/Card Vanilla Pure": self.bg_card,
            f"{self.brand_name}/Text Chocolate Dark": self.text_primary,
            f"{self.brand_name}/Text Chocolate Milk": self.text_muted,
            f"{self.brand_name}/Accent Vanilla Custard": self.accent_custard,
            f"{self.brand_name}/CTA Strawberry Ruby": self.accent_ruby,
            f"{self.brand_name}/Highlight Strawberry Blush": self.accent_blush,
        }
        for style_name, hex_val in color_map.items():
            if style_name not in existing_names:
                client.create_color_style(style_name, hex_val)

        text_styles = [
            (f"{self.brand_name}/H1 Display", self.font_heading, "Bold", self.size_h1, 50),
            (f"{self.brand_name}/H2 Section", self.font_heading, "Bold", self.size_h2, 36),
            (f"{self.brand_name}/Card Title", self.font_heading, "Bold", self.size_title, 24),
            (f"{self.brand_name}/Body Regular", self.font_body, "Regular", self.size_body, 20),
        ]
        for s_name, f_fam, f_style, f_size, l_height in text_styles:
            if s_name not in existing_names:
                client.create_text_style(s_name, f_fam, f_style, f_size, l_height)
