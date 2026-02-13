import streamlit as st
import pandas as pd
import io

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

from PIL import Image
import barcode
from barcode.writer import ImageWriter

LABEL_W = 5 * cm
LABEL_H = 3 * cm
PAGE_W, PAGE_H = A4

st.title("Sticker PDF Generator")

logo_file = st.file_uploader("Upload Logo", type=["png", "jpg", "jpeg"])
excel_file = st.file_uploader("Upload Excel", type=["xlsx"])

if logo_file and excel_file and st.button("Generate PDF"):

    df = pd.read_excel(excel_file)
    df.columns = df.columns.str.strip().str.lower()

    if not {"code", "name", "district"}.issubset(df.columns):
        st.error("Excel must contain code, name, district")
        st.stop()

    logo_img = Image.open(logo_file).convert("RGBA")
    logo_reader = ImageReader(logo_img)

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)

    col = row = 0
    COLS = int(PAGE_W // LABEL_W)
    ROWS = int(PAGE_H // LABEL_H)

    for _, r in df.iterrows():
        x = col * LABEL_W
        y = PAGE_H - (row + 1) * LABEL_H

        c.rect(x, y, LABEL_W, LABEL_H)

        # LOGO (ImageReader ONLY)
        c.drawImage(
            logo_reader,
            x + 0.2*cm,
            y + LABEL_H - 1.4*cm,
            width=1.2*cm,
            height=1.2*cm,
            mask="auto"
        )

        c.setFont("Times-Bold", 14)
        c.drawCentredString(x + LABEL_W/2, y + LABEL_H - 0.8*cm, str(r["code"]))
        c.drawCentredString(x + LABEL_W/2, y + LABEL_H - 1.4*cm, str(r["name"]))
        c.drawCentredString(x + LABEL_W/2, y + LABEL_H - 2.0*cm, str(r["district"]))

        code128 = barcode.get_barcode_class("code128")
        bc = code128(str(r["code"]), writer=ImageWriter())

        bc_buf = io.BytesIO()
        bc.write(bc_buf)
        bc_buf.seek(0)

        bc_img = ImageReader(Image.open(bc_buf))
        c.drawImage(
            bc_img,
            x + 0.4*cm,
            y + 0.2*cm,
            width=LABEL_W - 0.8*cm,
            height=0.8*cm
        )

        col += 1
        if col >= COLS:
            col = 0
            row += 1
        if row >= ROWS:
            c.showPage()
            row = 0

    c.save()
    buffer.seek(0)

    st.download_button(
        "Download PDF",
        buffer,
        "stickers_5x3cm.pdf",
        mime="application/pdf"
    )
