import io
import os
from datetime import date
from pathlib import Path

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader

import qrcode


DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "certificates"
DATA_DIR.mkdir(parents=True, exist_ok=True)


def _build_qr_image(payload: str) -> ImageReader:
    qr = qrcode.QRCode(version=None, box_size=4, border=1)
    qr.add_data(payload)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return ImageReader(buf)


def generate_certificate_pdf(
    full_name: str,
    course_title: str,
    certificate_number: str,
    issued_date: date,
    score_percent: int | None = None,
) -> str:
    filename = f"{certificate_number}.pdf"
    filepath = DATA_DIR / filename

    page_width, page_height = landscape(A4)
    c = canvas.Canvas(str(filepath), pagesize=landscape(A4))

    # Border
    c.setStrokeColor(HexColor("#1a237e"))
    c.setLineWidth(3)
    c.rect(1.5 * cm, 1.5 * cm, page_width - 3 * cm, page_height - 3 * cm)
    c.setLineWidth(1)
    c.rect(1.8 * cm, 1.8 * cm, page_width - 3.6 * cm, page_height - 3.6 * cm)

    # Title
    c.setFont("Helvetica-Bold", 36)
    c.setFillColor(HexColor("#1a237e"))
    c.drawCentredString(page_width / 2, page_height - 4 * cm, "SERTIFIKAT")

    # Subtitle
    c.setFont("Helvetica", 14)
    c.setFillColor(HexColor("#333333"))
    c.drawCentredString(
        page_width / 2, page_height - 5.5 * cm,
        "IIV Ta'lim Platformasi"
    )

    # Recipient
    c.setFont("Helvetica", 12)
    c.drawCentredString(
        page_width / 2, page_height - 7.5 * cm,
        "Ushbu sertifikat quyidagi shaxsga beriladi:"
    )

    c.setFont("Helvetica-Bold", 24)
    c.setFillColor(HexColor("#1a237e"))
    c.drawCentredString(page_width / 2, page_height - 9.5 * cm, full_name)

    # Course
    c.setFont("Helvetica", 14)
    c.setFillColor(HexColor("#333333"))
    c.drawCentredString(
        page_width / 2, page_height - 11.5 * cm,
        f'"{course_title}" kursini muvaffaqiyatli tugatganligi uchun'
    )

    if score_percent is not None:
        c.setFont("Helvetica", 12)
        c.drawCentredString(
            page_width / 2, page_height - 12.5 * cm,
            f"Natija: {score_percent}%"
        )

    # Footer
    c.setFont("Helvetica", 10)
    c.setFillColor(HexColor("#666666"))
    c.drawString(3 * cm, 3 * cm, f"Sana: {issued_date.strftime('%d.%m.%Y')}")
    c.drawRightString(
        page_width - 3 * cm, 3 * cm,
        f"Sertifikat raqami: {certificate_number}"
    )

    # QR code (verification): scanning shows "/verify <number>" deep link
    try:
        qr_payload = f"VERIFY:{certificate_number}"
        qr_img = _build_qr_image(qr_payload)
        qr_size = 3 * cm
        c.drawImage(
            qr_img,
            page_width - 3 * cm - qr_size,
            3.5 * cm,
            width=qr_size,
            height=qr_size,
            mask="auto",
        )
    except Exception:
        pass

    c.save()
    return str(filepath)
