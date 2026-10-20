"""Minimal pure-Python PDF writer — no dependencies.

Supports what a pentest report needs: titled pages, headings, body
text with word wrap, and multi-page overflow. Latin-1-safe text
(sadly the PDF standard's default) with a graceful strip for the rest.
"""
PAGE_W, PAGE_H = 595, 842  # A4 points
MARGIN = 56
LINE_GAP = 1.35

HELV = {"regular": "Helvetica", "bold": "Helvetica-Bold",
        "italic": "Helvetica-Oblique"}


def _escape(text):
    out = []
    for ch in text.replace("\t", " "):
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

    def heading(self, text, size=14):
        self.items.append(("heading", text, size, "bold"))

    def body(self, text, size=10, style="regular"):
        self.items.append(("body", text, size, style))


class PDF:
    def __init__(self, title, subtitle=""):
        self.title = title
        self.subtitle = subtitle
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
            if kind in ("title", "heading"):
                lines = [(kind, text, size, style)]
            else:
                lines = [("body", l, size, style)
                         for l in _wrap(text, size, PAGE_W - 2 * MARGIN)]
            for line in lines:
                line_height = size * LINE_GAP
                space_needed = line_height + (8 if kind in ("title", "heading") else 2)
                if y - space_needed < MARGIN:
                    flush(out)
                    y = PAGE_H - MARGIN
                if kind in ("title", "heading"):
                    y -= 8
                y -= line_height
                pending.append((line[0], line[1], line[2], line[3], y))
        if pending:
            flush(out)
        return out

    def _page_stream(self, page):
        ops = ["BT"]
        y = None
        for kind, text, size, style, y_pos in page.items:
            font = HELV.get(style, "Helvetica")
            if kind == "title":
                ops.append(f"/F1 {size} Tf 1 0 0 1 {MARGIN} {y_pos} Tm")
            elif kind == "heading":
                ops.append(f"/F1 {size} Tf 1 0 0 1 {MARGIN} {y_pos} Tm")
            else:
                ops.append(f"/F2 {size} Tf 1 0 0 1 {MARGIN} {y_pos} Tm")
            ops.append(f"({_escape(text)}) Tj")
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

        page_ids, content_ids = [], []
        pages_obj_id = 3 + 2 * len(laid)  # reserved: catalog + pages
        for i, page in enumerate(laid):
            content = self._page_stream(page).encode("latin-1", errors="replace")
            cid = add(f"<< /Length {len(content)} >>\nstream\n".encode() + content + b"\nendstream")
            content_ids.append(cid)
            pid = add(f"<< /Type /Page /Parent {pages_obj_id} 0 R "
                       f"/MediaBox [0 0 {PAGE_W} {PAGE_H}] "
                       f"/Resources << /Font << /F1 {font_bold} 0 R /F2 {font_reg} 0 R >> >> "
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
