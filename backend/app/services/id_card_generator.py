"""
Professional corporate ID card PDF: branded header, photo placeholder, typography, QR.
Uses reportlab for PDF and qrcode for QR.
"""
import io
import logging
from uuid import UUID
from datetime import date

from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib.colors import HexColor

logger = logging.getLogger(__name__)

# Corporate colors
HEADER_BG = HexColor("#1a365d")      # Navy blue
HEADER_TEXT = HexColor("#ffffff")
ACCENT = HexColor("#2c5282")        # Lighter blue accent
LABEL_COLOR = HexColor("#4a5568")   # Gray for labels
TEXT_COLOR = HexColor("#1a202c")    # Dark for values
BORDER_COLOR = HexColor("#e2e8f0")
CARD_BORDER = HexColor("#cbd5e0")

BRAND_MAIN = "JP SECURE STAFF"
BRAND_SUB = "AKSHAR CONSULTANCY SERVICES"


def _qr_image_bytes(data: str, size_px: int = 120) -> bytes:
    """Generate QR code as PNG bytes."""
    import qrcode
    qr = qrcode.QRCode(version=1, box_size=4, border=2)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img = img.resize((size_px, size_px))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.read()


def generate_id_card_pdf(
    person_id: UUID,
    name: str,
    employee_code: str | None = None,
    department_name: str | None = None,
    designation: str | None = None,
    joining_date: date | None = None,
) -> bytes:
    """
    Generate a professional corporate-style ID card PDF. Returns PDF bytes.
    Layout: branded header, photo placeholder, name + details, QR in bordered box.
    """
    buffer = io.BytesIO()
    w, h = 85.6 * mm, 53.98 * mm
    c = canvas.Canvas(buffer, pagesize=(w, h))

    # ----- Card border -----
    c.setStrokeColor(CARD_BORDER)
    c.setLineWidth(0.4 * mm)
    c.roundRect(0.5 * mm, 0.5 * mm, w - 1 * mm, h - 1 * mm, 2 * mm, fill=0, stroke=1)

    # ----- Header bar -----
    header_h = 10 * mm
    c.setFillColor(HEADER_BG)
    c.rect(0, h - header_h, w, header_h, fill=1, stroke=0)
    c.setFillColor(HEADER_TEXT)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(4 * mm, h - 5.5 * mm, BRAND_MAIN)
    c.setFont("Helvetica", 6)
    c.setFillColor(HexColor("#a0aec0"))
    c.drawString(4 * mm, h - 7.5 * mm, BRAND_SUB)

    # ----- Photo placeholder -----
    photo_x, photo_y = 4 * mm, h - header_h - 2 * mm
    photo_w, photo_h = 18 * mm, 22 * mm
    c.setFillColor(BORDER_COLOR)
    c.setStrokeColor(ACCENT)
    c.setLineWidth(0.3 * mm)
    c.roundRect(photo_x, photo_y - photo_h, photo_w, photo_h, 1.5 * mm, fill=1, stroke=1)
    c.setFillColor(LABEL_COLOR)
    c.setFont("Helvetica", 6)
    c.drawCentredString(photo_x + photo_w / 2, photo_y - photo_h / 2 - 1.5 * mm, "PHOTO")

    # ----- Employee name (prominent) -----
    name_x = photo_x + photo_w + 3 * mm
    name_top = photo_y - 2 * mm
    c.setFillColor(TEXT_COLOR)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(name_x, name_top, name)

    # ----- Details: label + value rows -----
    row_h = 5 * mm
    y = name_top - 5 * mm

    def _row(label: str, value: str) -> None:
        nonlocal y
        c.setFillColor(LABEL_COLOR)
        c.setFont("Helvetica", 5.5)
        c.drawString(name_x, y, label)
        c.setFillColor(TEXT_COLOR)
        c.setFont("Helvetica-Bold", 6)
        c.drawString(name_x + 18 * mm, y, value[:24] if value else "—")
        y -= row_h

    _row("Emp Code", employee_code or "—")
    _row("Department", (department_name or "—")[:24])
    _row("Designation", (designation or "—")[:24])
    _row("Joining", joining_date.strftime("%d-%b-%Y") if joining_date else "—")

    # ----- QR code in bordered box -----
    qr_box = 20 * mm
    qr_x = w - qr_box - 5 * mm
    qr_y = photo_y - photo_h
    c.setStrokeColor(ACCENT)
    c.setLineWidth(0.25 * mm)
    c.roundRect(qr_x, qr_y, qr_box, qr_box, 1 * mm, fill=0, stroke=1)
    qr_data = str(person_id)
    qr_bytes = _qr_image_bytes(qr_data, size_px=100)
    c.drawImage(
        ImageReader(io.BytesIO(qr_bytes)),
        qr_x + 1.5 * mm, qr_y + 1.5 * mm,
        width=qr_box - 3 * mm, height=qr_box - 3 * mm
    )

    # ----- Footer line -----
    c.setStrokeColor(BORDER_COLOR)
    c.setLineWidth(0.2 * mm)
    c.line(4 * mm, 4 * mm, w - 4 * mm, 4 * mm)
    c.setFillColor(LABEL_COLOR)
    c.setFont("Helvetica", 4.5)
    c.drawCentredString(w / 2, 2.5 * mm, "Authorized ID • JP Secure Staff")

    c.save()
    buffer.seek(0)
    return buffer.read()
