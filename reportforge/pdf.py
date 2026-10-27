"""Minimal pure-Python PDF writer — no dependencies.

Supports what a pentest report needs: titled pages, headings, body
text with word wrap, multi-page overflow, custom branding (accent colors,
subtitles, footers). Latin-1-safe text with a graceful strip for the rest.
"""
PAGE_W, PAGE_H = 595, 842  # A4 points
MARGIN = 56
LINE_GAP = 1.35

HELV = {"regular": "Helvetica", "bold": "Helvetica-Bold",
        "italic": "Helvetica-Oblique"}


def parse_hex_color(hex_str):
    """Parse hex color string (e.g. #0055ff or 0055ff) to RGB float tuple."""
    if not hex_str:
        return None
    cleaned = hex_str.lstrip("#").strip()
    if len(cleaned) == 3:
        cleaned = "".join(c * 2 for c in cleaned)
    if len(cleaned) != 6:
        raise ValueError(f"Invalid hex color: '{hex_str}'")
    try:
        r = int(cleaned[0:2], 16) / 255.0
        g = int(cleaned[2:4], 16) / 255.0
        b = int(cleaned[4:6], 16) / 255.0
        return (r, g, b)
    except ValueError:
        raise ValueError(f"Invalid hex color: '{hex_str}'")


def _escape(text):
    out = []
    for ch in str(text).replace("\t", " "):
        try:
            ch.encode("latin-1")
            out.append(ch if ch not in "()\\" else "\\" + ch)
        except UnicodeEncodeError:
            out.append("?")
    return "".join(out)


def _wrap(text, size, max_width):
    """Greedy word wrap using Helvetica's approximate widths."""
    approx = size * 0.5
    max_chars = max(10, int(max_width / approx))
    words, lines, current = text.split(), [], ""
    for word in words:
        candidate = (current + " " + word).strip()
        if len(candidate) <= max_chars or not current:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or [""]


class Page:
    def __init__(self):
        self.items = []  # (kind, text, size, style)

    def title(self, text, size=20):
        self.items.append(("title", text, size, "bold"))

    def subtitle(self, text, size=12):
        self.items.append(("subtitle", text, size, "italic"))

    def heading(self, text, size=14):
        self.items.append(("heading", text, size, "bold"))

    def body(self, text, size=10, style="regular"):
        self.items.append(("body", text, size, style))


class PDF:
    def __init__(self, title, subtitle="", footer="", accent=None):
        self.title = title
        self.subtitle = subtitle
        self.footer = footer
        self.accent_hex = accent
        self.accent_rgb = parse_hex_color(accent) if accent else None
        self.pages = []

    def add_page(self):
        page = Page()
        self.pages.append(page)
        return page

    def _layout_page(self, page):
        """Lay out one Page of items, overflowing onto new pages."""
        flow, y = [], PAGE_H - MARGIN
        pending = []

        def flush(pages_out):
            new = Page()
            new.items = list(pending)
            pending.clear()
            pages_out.append(new)

        out = []
        for kind, text, size, style in page.items:
            if kind in ("title", "subtitle", "heading"):
                lines = [(kind, text, size, style)]
            else:
                lines = [("body", l, size, style)
                         for l in _wrap(text, size, PAGE_W - 2 * MARGIN)]
            for line in lines:
                line_height = size * LINE_GAP
                space_needed = line_height + (8 if kind in ("title", "subtitle", "heading") else 2)
                if y - space_needed < MARGIN:
                    flush(out)
                    y = PAGE_H - MARGIN
                if kind in ("title", "subtitle", "heading"):
                    y -= 8
                y -= line_height
                pending.append((line[0], line[1], line[2], line[3], y))
        if pending:
            flush(out)
        return out

    def _page_stream(self, page):
        ops = []
        accent_op = None
        black_op = None
        if self.accent_rgb:
            r, g, b = self.accent_rgb
            accent_op = f"{r:.3f} {g:.3f} {b:.3f} rg"
            black_op = "0 0 0 rg"

        ops.append("BT")
        for kind, text, size, style, y_pos in page.items:
            if kind in ("title", "heading"):
                if accent_op:
                    ops.append(accent_op)
                ops.append(f"/F1 {size} Tf 1 0 0 1 {MARGIN} {y_pos} Tm")
                ops.append(f"({_escape(text)}) Tj")
                if black_op:
                    ops.append(black_op)
            elif kind == "subtitle":
                if accent_op:
                    ops.append(accent_op)
                ops.append(f"/F3 {size} Tf 1 0 0 1 {MARGIN} {y_pos} Tm")
                ops.append(f"({_escape(text)}) Tj")
                if black_op:
                    ops.append(black_op)
            else:
                ops.append(f"/F2 {size} Tf 1 0 0 1 {MARGIN} {y_pos} Tm")
                ops.append(f"({_escape(text)}) Tj")

        if self.footer:
            ops.append(f"/F2 8 Tf 1 0 0 1 {MARGIN} 25 Tm")
            ops.append(f"({_escape(self.footer)}) Tj")

        ops.append("ET")
        return " ".join(ops)

    def build(self):
        """Return PDF bytes for the whole document."""
        laid = []
        for page in self.pages:
            laid.extend(self._layout_page(page))

        objects = []
        def add(body):
            objects.append(body)
            return len(objects)

        font_reg = add("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
        font_bold = add("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>")
        font_ital = add("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Oblique >>")

        page_ids, content_ids = [], []
        pages_obj_id = 4 + 2 * len(laid)  # reserved: catalog + pages + fonts
        for i, page in enumerate(laid):
            content = self._page_stream(page).encode("latin-1", errors="replace")
            cid = add(f"<< /Length {len(content)} >>\nstream\n".encode() + content + b"\nendstream")
            content_ids.append(cid)
            pid = add(f"<< /Type /Page /Parent {pages_obj_id} 0 R "
                       f"/MediaBox [0 0 {PAGE_W} {PAGE_H}] "
                       f"/Resources << /Font << /F1 {font_bold} 0 R /F2 {font_reg} 0 R /F3 {font_ital} 0 R >> >> "
                       f"/Contents {cid} 0 R >>")
            page_ids.append(pid)

        kids = " ".join(f"{p} 0 R" for p in page_ids)
        pages_body = f"<< /Type /Pages /Kids [{kids}] /Count {len(page_ids)} >>"
        assert len(objects) + 1 == pages_obj_id
        add(pages_body)
        add(f"<< /Type /Catalog /Pages {pages_obj_id} 0 R >>")

        out = bytearray(b"%PDF-1.4\n")
        offsets = [0]
        for i, obj in enumerate(objects, start=1):
            offsets.append(len(out))
            out += f"{i} 0 obj\n".encode()
            if isinstance(obj, bytes):
                out += obj
            else:
                out += obj.encode()
            out += b"\nendobj\n"
        xref_at = len(out)
        out += f"xref\n0 {len(objects) + 1}\n".encode()
        out += b"0000000000 65535 f \n"
        for off in offsets[1:]:
            out += f"{off:010d} 00000 n \n".encode()
        out += (f"trailer\n<< /Size {len(objects) + 1} /Root {len(objects)} 0 R >>\n"
                f"startxref\n{xref_at}\n%%EOF").encode()
        return bytes(out)
