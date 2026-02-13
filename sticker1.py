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

# -------------------------------------------------
# LABEL SIZE (EXACT)
# -------------------------------------------------
LABEL_W = 5 * cm
LABEL_H = 3 * cm

# -------------------------------------------------
# CUTTING GAP BETWEEN STICKERS
# -------------------------------------------------
H_GAP = 0.3 * cm
V_GAP = 0.3 * cm

# -------------------------------------------------
# PAGE MARGINS (LEFT / RIGHT / TOP / BOTTOM)
# -------------------------------------------------
LEFT_MARGIN   = 1.0 * cm
RIGHT_MARGIN  = 1.0 * cm
TOP_MARGIN    = 1.0 * cm
BOTTOM_MARGIN = 1.0 * cm

# -------------------------------------------------
# PAGE
# -------------------------------------------------
PAGE_W, PAGE_H = A4

AVAILABLE_W = PAGE_W - LEFT_MARGIN - RIGHT_MARGIN
AVAILABLE_H = PAGE_H - TOP_MARGIN - BOTTOM_MARGIN

COLS = int(AVAILABLE_W // (LABEL_W + H_GAP))
ROWS = int(AVAILABLE_H // (LABEL_H + V_GAP))

# -------------------------------------------------
# UI
# -------------------------------------------------
st.set_page_config(page_title="Sticker PDF Generator")
st.title("🖨️ Sticker PDF Generator (5 cm × 3 cm)")

logo_file = st.file_uploader("Upload Logo (PNG/JPG)", type=["png", "jpg", "jpeg"])
excel_file = st.file_uploader("Upload Excel File", type=["xlsx"])

# -------------------------------------------------
# PROCESS
# -------------------------------------------------
if logo_file and excel_file and st.button("Generate PDF"):

    # -------- Excel --------
    df = pd.read_excel(excel_file)
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(r"\s+", "", regex=True)
    )

    if not {"code", "name", "district"}.issubset(df.columns):
        st.error(f"Excel columns found: {list(df.columns)}")
        st.stop()

    # -------- Logo --------
    logo_img = Image.open(logo_file).convert("RGBA")
    logo_reader = ImageReader(logo_img)

    # -------- PDF --------
    pdf_buffer = io.BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=A4)

    col = row = 0

    for _, r in df.iterrows():

        x = LEFT_MARGIN + col * (LABEL_W + H_GAP)
        y = PAGE_H - TOP_MARGIN - ((row + 1) * (LABEL_H + V_GAP))

        # Optional border (cut guide)
        c.rect(x, y, LABEL_W, LABEL_H)

        # -------- LOGO --------
        c.drawImage(
            logo_reader,
            x + 0.2 * cm,
            y + LABEL_H - 1.4 * cm,
            width=1.2 * cm,
            height=1.2 * cm,
            mask="auto"
        )

        # -------- TEXT (Times Bold, 14pt) --------
        c.setFont("Times-Bold", 14)

        c.drawCentredString(x + LABEL_W / 2, y + LABEL_H - 0.8 * cm, str(r["code"]))
        c.drawCentredString(x + LABEL_W / 2, y + LABEL_H - 1.4 * cm, str(r["name"]))
        c.drawCentredString(x + LABEL_W / 2, y + LABEL_H - 2.0 * cm, str(r["district"]))

        # -------- BARCODE --------
        CODE128 = barcode.get_barcode_class("code128")
        bc = CODE128(str(r["code"]), writer=ImageWriter())

        bc_buffer = io.BytesIO()
        bc.write(bc_buffer, {"quiet_zone": 1, "module_height": 8})
        bc_buffer.seek(0)

        bc_img = Image.open(bc_buffer)
        bc_reader = ImageReader(bc_img)

        c.drawImage(
            bc_reader,
            x + 0.4 * cm,
            y + 0.2 * cm,
            width=LABEL_W - 0.8 * cm,
            height=0.8 * cm,
            mask="auto"
        )

        # -------- GRID CONTROL --------
        col += 1
        if col >= COLS:
            col = 0
            row += 1

        if row >= ROWS:
            c.showPage()
            row = 0

    c.save()
    pdf_buffer.seek(0)

    # -------- DOWNLOAD --------
    st.success("PDF generated successfully ✅")

    st.download_button(
        label="⬇️ Download Sticker PDF",
        data=pdf_buffer,
        file_name="stickers_5x3cm_with_margins.pdf",
        mime="application/pdf"
    )
