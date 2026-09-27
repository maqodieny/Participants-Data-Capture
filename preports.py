# -*- coding: utf-8 -*-

import base64
import html
import io
from datetime import datetime

import pandas as pd
import requests
import streamlit as st

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


st.set_page_config(page_title="Participants' Data", page_icon="📊", layout="wide")

API_TOKEN = st.secrets.get(
    "KOBOTOOLBOX_API_TOKEN",
    "d87b11826e9b2b08b3fcdc72e63c6830d29579da"
)

CSV_URL = (
    "https://eu.kobotoolbox.org/api/v2/assets/"
    "aEFQaUj3cV7jjRzKoet8ax/export-settings/"
    "esBqoUaYY8XrKVT2cGbChgc/data.csv"
)

NAME_COLUMN = "Name"
DATE_COLUMN = "Activity Date"
SIGNATURE_URL_COLUMN = "Signature_URL"

DOCUSIGN_FIELDS = [
    ("Company and project logo", ""),
    ("Activity name", ""),
    ("Project name", ""),
    ("Facilitated by", "")
]


def download_signature_as_data_url(signature_url):
    if pd.isna(signature_url):
        return None
    signature_url = str(signature_url).strip()
    if not signature_url:
        return None
    try:
        response = requests.get(
            signature_url,
            headers={"Authorization": f"Token {API_TOKEN}"},
            timeout=30
        )
        response.raise_for_status()
        content_type = response.headers.get("Content-Type", "image/jpeg")
        encoded_image = base64.b64encode(response.content).decode("utf-8")
        return f"data:{content_type};base64,{encoded_image}"
    except requests.exceptions.RequestException:
        return None


@st.cache_data
def load_data():
    response = requests.get(
        CSV_URL,
        headers={"Authorization": f"Token {API_TOKEN}"},
        timeout=60
    )
    response.raise_for_status()
    loaded_df = pd.read_csv(io.StringIO(response.text), sep=";")
    return loaded_df.drop(
        columns=["start", "end", "_id", "_uuid", "meta/rootUuid"],
        errors="ignore"
    )


def add_header_footer(canvas, document):
    canvas.saveState()
    page_width, page_height = landscape(A4)

    canvas.setFillColor(colors.HexColor("#1F4E78"))
    canvas.rect(0, page_height - 22 * mm, page_width, 22 * mm, fill=1, stroke=0)

    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica-Bold", 12)
    canvas.drawString(10 * mm, page_height - 9 * mm, "PARTICIPANTS' DATA")

    canvas.setFont("Helvetica", 8)
    canvas.drawString(
        10 * mm,
        page_height - 15 * mm,
        "Participant records and submitted signatures"
    )

    generated_date = datetime.now().strftime("%d %B %Y, %H:%M")
    canvas.drawRightString(
        page_width - 10 * mm,
        page_height - 9 * mm,
        f"Generated: {generated_date}"
    )

    label_style = ParagraphStyle(
        "DocuSignLabel", fontName="Helvetica-Bold", fontSize=6,
        leading=7, textColor=colors.HexColor("#1F1F1F")
    )
    value_style = ParagraphStyle(
        "DocuSignValue", fontName="Helvetica", fontSize=6,
        leading=7, textColor=colors.HexColor("#1F1F1F")
    )

    docusign_data = [
        [
            Paragraph(html.escape(str(label)), label_style),
            Paragraph(html.escape(str(value)), value_style)
        ]
        for label, value in DOCUSIGN_FIELDS
    ]

    docusign_table = Table(
        docusign_data,
        colWidths=[34 * mm, 48 * mm],
        rowHeights=[7 * mm] * len(DOCUSIGN_FIELDS)
    )
    docusign_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.white),
        ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#1F4E78")),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#A6A6A6")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2)
    ]))

    table_width = 82 * mm
    table_height = 28 * mm
    docusign_table.wrapOn(canvas, table_width, table_height)
    docusign_table.drawOn(
        canvas,
        page_width - table_width - 10 * mm,
        page_height - table_height - 25 * mm
    )

    canvas.setStrokeColor(colors.HexColor("#1F4E78"))
    canvas.setLineWidth(0.5)
    canvas.line(10 * mm, 14 * mm, page_width - 10 * mm, 14 * mm)

    canvas.setFillColor(colors.HexColor("#555555"))
    canvas.setFont("Helvetica", 7)
    canvas.drawString(10 * mm, 8 * mm, "Confidential - For official use only")
    canvas.drawRightString(
        page_width - 10 * mm,
        8 * mm,
        f"Page {canvas.getPageNumber()}"
    )
    canvas.restoreState()


def create_approval_section():
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ApprovalTitle", parent=styles["Heading2"], alignment=TA_CENTER,
        fontSize=11, leading=14, spaceBefore=8, spaceAfter=6
    )
    role_style = ParagraphStyle(
        "ApprovalRole", parent=styles["BodyText"], alignment=TA_LEFT,
        fontSize=7, leading=9
    )
    field_style = ParagraphStyle(
        "ApprovalField", parent=styles["BodyText"], alignment=TA_LEFT,
        fontSize=7, leading=9
    )

    roles = [
        "Prepared by",
        "Checked by",
        "Approved by Manager",
        "Approved by Director"
    ]

    data = [[
        Paragraph("<b>Approval role</b>", role_style),
        Paragraph("<b>Name</b>", field_style),
        Paragraph("<b>Signature</b>", field_style),
        Paragraph("<b>Date</b>", field_style)
    ]]

    for role in roles:
        data.append([
            Paragraph(role, role_style),
            Paragraph("<br/><br/>", field_style),
            Paragraph("<br/><br/><br/>", field_style),
            Paragraph("<br/><br/>", field_style)
        ])

    available_width = landscape(A4)[0] - 16 * mm
    table = Table(
        data,
        colWidths=[
            available_width * 0.24,
            available_width * 0.25,
            available_width * 0.31,
            available_width * 0.20
        ],
        rowHeights=[10 * mm, 24 * mm, 24 * mm, 24 * mm, 24 * mm],
        repeatRows=1
    )
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F4E78")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#1F4E78")),
        ("INNERGRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#A6A6A6")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5)
    ]))

    return [Paragraph("DOCUMENT APPROVAL", title_style), table]


def create_pdf(filtered_data):
    pdf_buffer = io.BytesIO()
    document = SimpleDocTemplate(
        pdf_buffer,
        pagesize=landscape(A4),
        rightMargin=8 * mm,
        leftMargin=8 * mm,
        topMargin=58 * mm,
        bottomMargin=20 * mm
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "PDFTitle", parent=styles["Title"], alignment=TA_CENTER,
        fontSize=14, leading=18, spaceAfter=8
    )
    cell_style = ParagraphStyle(
        "PDFCell", parent=styles["BodyText"], fontSize=6,
        leading=7, wordWrap="CJK"
    )
    header_style = ParagraphStyle(
        "PDFHeader", parent=styles["BodyText"], fontSize=6,
        leading=7, textColor=colors.white, alignment=TA_CENTER
    )

    elements = [
        Paragraph("Participants' Data", title_style),
        Paragraph(f"Number of records: {len(filtered_data)}", cell_style),
        Spacer(1, 5 * mm)
    ]

    columns = [
        column for column in filtered_data.columns
        if column != SIGNATURE_URL_COLUMN
    ] + [SIGNATURE_URL_COLUMN]

    table_data = [[
        Paragraph(html.escape(str(column)), header_style)
        for column in columns
    ]]

    for _, row in filtered_data.iterrows():
        row_values = []
        for column in columns:
            if column == SIGNATURE_URL_COLUMN:
                image_data = row.get(SIGNATURE_URL_COLUMN)
                if pd.notna(image_data) and str(image_data).startswith("data:image"):
                    try:
                        image_bytes = base64.b64decode(str(image_data).split(",", 1)[1])
                        row_values.append(Image(
                            io.BytesIO(image_bytes), width=25 * mm, height=12 * mm
                        ))
                    except Exception:
                        row_values.append(Paragraph("Unavailable", cell_style))
                else:
                    row_values.append(Paragraph("No signature", cell_style))
            else:
                value = row.get(column, "")
                if pd.isna(value):
                    value = ""
                row_values.append(Paragraph(html.escape(str(value)), cell_style))
        table_data.append(row_values)

    available_width = landscape(A4)[0] - 16 * mm
    table = Table(
        table_data,
        colWidths=[available_width / max(len(columns), 1)] * len(columns),
        repeatRows=1
    )
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F4E78")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F2F6FA")]),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3)
    ]))

    elements.append(table)
    elements.extend(create_approval_section())

    document.build(
        elements,
        onFirstPage=add_header_footer,
        onLaterPages=add_header_footer
    )
    return pdf_buffer.getvalue()


try:
    df = load_data()
    st.success(f"Loaded {len(df)} records")
except requests.exceptions.RequestException as error:
    st.error(f"Unable to load data from KoboToolbox: {error}")
    st.stop()
except Exception as error:
    st.error(f"An error occurred while processing the data: {error}")
    st.stop()

required = [NAME_COLUMN, DATE_COLUMN, SIGNATURE_URL_COLUMN]
missing = [column for column in required if column not in df.columns]
if missing:
    st.error("Missing required columns: " + ", ".join(missing))
    st.stop()

with st.spinner("Loading signature images..."):
    df[SIGNATURE_URL_COLUMN] = df[SIGNATURE_URL_COLUMN].apply(
        download_signature_as_data_url
    )

df["_month"] = pd.to_datetime(df[DATE_COLUMN], errors="coerce").dt.strftime("%B %Y")
month_options = ["All"] + sorted(
    df["_month"].dropna().unique().tolist(),
    key=lambda x: pd.to_datetime(x, format="%B %Y")
)
name_options = ["All"] + sorted(df[NAME_COLUMN].dropna().astype(str).unique().tolist())

st.title("Participants' Data")
st.write("Use the filters below to search records by name and activity month.")

col1, col2, col3 = st.columns(3)
with col1:
    name_contains = st.text_input("Name contains:")
with col2:
    name_pick = st.selectbox("Or pick name:", name_options)
with col3:
    month = st.selectbox("Month:", month_options)

filtered = df.copy()
if name_contains:
    filtered = filtered[filtered[NAME_COLUMN].astype(str).str.contains(name_contains, case=False, na=False)]
elif name_pick != "All":
    filtered = filtered[filtered[NAME_COLUMN].astype(str).eq(name_pick)]
if month != "All":
    filtered = filtered[filtered["_month"] == month]

display_df = filtered.drop(columns=["_month"], errors="ignore")
st.write(f"### Showing {len(display_df)} matching records")

st.dataframe(
    display_df.head(100),
    use_container_width=True,
    hide_index=True,
    column_config={
        SIGNATURE_URL_COLUMN: st.column_config.ImageColumn(
            "Signature", help="Submitted signature", width="small"
        )
    }
)

excel_buffer = io.BytesIO()
with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
    display_df.to_excel(writer, index=False, sheet_name="Filtered Data")

st.download_button(
    "Download Excel",
    data=excel_buffer.getvalue(),
    file_name="Download.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

with st.spinner("Preparing PDF with signatures and approval fields..."):
    pdf_data = create_pdf(display_df)

st.download_button(
    "Download PDF with Signatures",
    data=pdf_data,
    file_name="Participants_Data_with_Signatures.pdf",
    mime="application/pdf"
)

