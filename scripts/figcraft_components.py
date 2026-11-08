"""
figcraft_components.py (Fitur #6) - Reusable High-Level UI Component Library.
"""

from typing import Optional, List, Tuple
from figcraft_ui import FigCraftClient, NodeRef
from design_tokens import DesignTokens


class UIComponents:
    def __init__(self, client: FigCraftClient, tokens: Optional[DesignTokens] = None):
        self.client = client
        self.t = tokens or DesignTokens()

    def button(
        self,
        parent: NodeRef,
        label: str,
        variant: str = "primary",
        size: str = "md",
        width: Optional[float] = None,
        height: Optional[float] = None,
        name: Optional[str] = None
    ) -> NodeRef:
        """
        Renders a themed button (`variant`: 'primary' | 'secondary' | 'soft' | 'ghost').
        Uses `hug` sizing by default unless `width` / `height` are specified.
        """
        pad = [12, 24, 12, 24] if size == "lg" else ([6, 12, 6, 12] if size == "sm" else [10, 20, 10, 20])
        f_size = 15 if size == "lg" else (11 if size == "sm" else 13)

        if variant == "primary":
            fill, stroke, text_col, effects = self.t.accent_ruby, None, self.t.white, self.t.shadow_cta
        elif variant == "secondary":
            fill, stroke, text_col, effects = self.t.bg_card, self.t.text_muted, self.t.text_primary, None
        elif variant == "soft":
            fill, stroke, text_col, effects = self.t.accent_blush, self.t.accent_ruby, self.t.accent_ruby, None
        else:
            fill, stroke, text_col, effects = self.t.bg_canvas, self.t.accent_custard, self.t.text_primary, None

        btn = self.client.box(
            parent=parent,
            name=name or f"Btn_{label[:12]}",
            layout="horizontal",
            width=width,
            height=height,
            padding=pad,
            mainAlign="center",
            crossAlign="center",
            fill=fill,
            stroke=stroke,
            strokeWeight=1.5 if variant == "secondary" else 1,
            cornerRadius=self.t.radius_md if size != "sm" else self.t.radius_sm,
            effects=effects
        )
        self.client.create_text(
            parent=btn,
            text=label,
            fontSize=f_size,
            fontFamily=self.t.font_body,
            fontStyle="Bold" if variant in ("primary", "soft") else "SemiBold",
            fill=text_col,
            textAlign="center"
        )
        return btn

    def pill(
        self,
        parent: NodeRef,
        label: str,
        active: bool = False,
        variant: str = "filter",
        padding: Optional[List[float]] = None
    ) -> NodeRef:
        """Renders an auto-hugging interactive pill or tag."""
        pad = padding or ([8, 18, 8, 18] if variant == "filter" else [6, 14, 6, 14])
        if variant == "filter":
            fill = self.t.accent_ruby if active else self.t.accent_custard
            stroke = None
            text_col = self.t.white if active else self.t.text_primary
        else:
            fill = self.t.accent_blush if active else self.t.bg_canvas
            stroke = self.t.accent_ruby if active else self.t.accent_custard
            text_col = self.t.accent_ruby if active else self.t.text_primary

        p_box = self.client.box(
            parent=parent,
            name=f"Pill_{label[:10]}",
            layout="horizontal",
            padding=pad,
            mainAlign="center",
            crossAlign="center",
            fill=fill,
            stroke=stroke,
            strokeWeight=1.5 if (active and stroke) else 1,
            cornerRadius=self.t.radius_pill if variant == "filter" else self.t.radius_sm
        )
        self.client.create_text(
            parent=p_box,
            text=label,
            fontSize=12 if variant == "filter" else 11,
            fontFamily=self.t.font_body,
            fontStyle="Bold" if active else "Medium",
            fill=text_col
        )
        return p_box

    def badge(
        self,
        parent: NodeRef,
        label: str,
        variant: str = "ruby",
        x: float = 0,
        y: float = 0,
        floating: bool = False
    ) -> NodeRef:
        """Renders a status or promo badge. Set `floating=True` for absolute positioning."""
        palette = {
            "ruby": (self.t.accent_ruby, self.t.white),
            "blush": (self.t.accent_blush, self.t.accent_ruby),
            "custard": (self.t.accent_custard, self.t.text_primary),
            "dark": (self.t.text_primary, self.t.white),
        }
        fill, text_col = palette.get(variant, (self.t.accent_ruby, self.t.white))
        b_box = self.client.box(
            parent=parent,
            name=f"Badge_{label[:10]}",
            layout="horizontal",
            x=x,
            y=y,
            padding=[4, 10, 4, 10],
            mainAlign="center",
            crossAlign="center",
            fill=fill,
            cornerRadius=12,
            absolute=floating
        )
        self.client.create_text(
            parent=b_box,
            text=label,
            fontSize=11,
            fontFamily=self.t.font_body,
            fontStyle="Bold",
            fill=text_col
        )
        return b_box

    def input_field(
        self,
        parent: NodeRef,
        value: str,
        width: float = 400,
        height: Optional[float] = None,
        active: bool = False,
        multiline: bool = False
    ) -> NodeRef:
        """Renders a form input or multiline text box with automatic text wrapping."""
        pad_h = 14
        box = self.client.box(
            parent=parent,
            name=f"Input_{value[:10]}",
            layout="horizontal",
            width=width,
            height=height,
            padding=[10, pad_h, 10, pad_h],
            mainAlign="min",
            crossAlign="center",
            fill=self.t.bg_card if active else self.t.bg_canvas,
            stroke=self.t.accent_ruby if active else self.t.accent_custard,
            strokeWeight=1.5 if active else 1,
            cornerRadius=self.t.radius_sm
        )
        # Always pass inner width so long text wraps and never overflows the input box!
        inner_w = width - (pad_h * 2)
        self.client.create_text(
            parent=box,
            text=value,
            width=inner_w,
            fontSize=12 if multiline else 13,
            fontFamily=self.t.font_heading if active else self.t.font_body,
            fontStyle="Bold" if active else "Regular",
            fill=self.t.text_primary if active else self.t.text_muted
        )
        return box

    def card(
        self,
        parent: NodeRef,
        name: str = "Card",
        x: float = 0,
        y: float = 0,
        width: float = 295,
        height: Optional[float] = None,
        padding: float = 16,
        gap: float = 12,
        radius: Optional[float] = None
    ) -> NodeRef:
        """Renders a surface card container."""
        return self.client.box(
            parent=parent,
            name=name,
            layout="vertical",
            x=x,
            y=y,
            width=width,
            height=height,
            padding=padding,
            gap=gap,
            fill=self.t.bg_card,
            stroke=self.t.accent_custard,
            strokeWeight=1,
            cornerRadius=radius or self.t.radius_lg,
            effects=self.t.shadow_md
        )

    def divider(self, parent: NodeRef, width: float = 300) -> NodeRef:
        """Renders a 1px horizontal divider."""
        return self.client.create_rect(
            parent=parent,
            name="Divider",
            width=width,
            height=1,
            fill=self.t.accent_custard
        )
