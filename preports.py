# -*- coding: utf-8 -*-

import pandas as pd
import requests
import io
import base64
import html
import streamlit as st

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    Image
)
from reportlab.lib.enums import TA_LEFT

# --- Page configuration ---
st.set_page_config(
    page_title="Participants' Data",
    page_icon="psk logo.png",
    layout="wide"
)


# --- Load data ---
API_TOKEN = "d87b11826e9b2b08b3fcdc72e63c6830d29579da"

CSV_URL = (
    "https://eu.kobotoolbox.org/api/v2/assets/"
    "aEFQaUj3cV7jjRzKoet8ax/export-settings/"
    "esBqoUaYY8XrKVT2cGbChgc/data.csv"
)


def download_signature_as_data_url(signature_url):
    """
    Download a protected KoboToolbox image and convert it
    into a Base64 data URL for Streamlit ImageColumn.
    """

    if pd.isna(signature_url):
        return None

    signature_url = str(signature_url).strip()

    if not signature_url:
        return None

    try:
        response = requests.get(
            signature_url,
            headers={
                "Authorization": f"Token {API_TOKEN}"
            },
            timeout=30
        )

        response.raise_for_status()

        content_type = response.headers.get(
            "Content-Type",
            "image/jpeg"
        )

        encoded_image = base64.b64encode(
            response.content
        ).decode("utf-8")

        return f"data:{content_type};base64,{encoded_image}"

    except requests.exceptions.RequestException:
        return None


def add_header_footer(canvas, document):
    """
    Add the header, DocuSign guidance table, and footer
    to every page of the PDF.
    """

    canvas.saveState()

    page_width, page_height = landscape(A4)

    # --------------------------------
    # Main header
    # --------------------------------

    canvas.setFillColor(colors.HexColor("#1F4E78"))

    canvas.rect(
        0,
        page_height - 22 * mm,
        page_width,
        22 * mm,
        fill=1,
        stroke=0
    )

    canvas.setFillColor(colors.white)

    canvas.setFont(
        "Helvetica-Bold",
        12
    )

    canvas.drawString(
        10 * mm,
        page_height - 9 * mm,
        "PARTICIPANTS' DATA"
    )

    canvas.setFont(
        "Helvetica",
        8
    )

    canvas.drawString(
        10 * mm,
        page_height - 15 * mm,
        "Participant records and submitted signatures"
    )

    generated_date = datetime.now().strftime(
        "%d %B %Y, %H:%M"
    )

    canvas.drawRightString(
        page_width - 10 * mm,
        page_height - 9 * mm,
        f"Generated: {generated_date}"
    )

    # --------------------------------
    # DocuSign guidance table
    # --------------------------------

    docusign_table_data = []

    for field_label, field_value in DOCUSIGN_FIELDS:
        docusign_table_data.append(
            [
                Paragraph(
                    field_label,
                    ParagraphStyle(
                        "DocuSignLabel",
                        fontName="Helvetica-Bold",
                        fontSize=6,
                        leading=7,
                        textColor=colors.HexColor("#1F1F1F")
                    )
                ),
                Paragraph(
                    field_value,
                    ParagraphStyle(
                        "DocuSignValue",
                        fontName="Helvetica",
                        fontSize=6,
                        leading=7,
                        textColor=colors.HexColor("#1F1F1F")
                    )
                )
            ]
        )

    docusign_table = Table(
        docusign_table_data,
        colWidths=[
            34 * mm,
            48 * mm
        ],
        rowHeights=[
            7 * mm,
            7 * mm,
            7 * mm,
            7 * mm
        ]
    )

    docusign_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    colors.white
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.6,
                    colors.HexColor("#1F4E78")
                ),
                (
                    "INNERGRID",
                    (0, 0),
                    (-1, -1),
                    0.25,
                    colors.HexColor("#A6A6A6")
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE"
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    3
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    3
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    2
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    2
                )
            ]
        )
    )

    # Draw table at the top-right corner
    table_width = 82 * mm
    table_height = 28 * mm

    docusign_table.wrapOn(
        canvas,
        table_width,
        table_height
    )

    docusign_table.drawOn(
        canvas,
        page_width - table_width - 10 * mm,
        page_height - table_height - 25 * mm
    )

    # --------------------------------
    # Footer
    # --------------------------------

    canvas.setStrokeColor(
        colors.HexColor("#1F4E78")
    )

    canvas.setLineWidth(0.5)

    canvas.line(
        10 * mm,
        14 * mm,
        page_width - 10 * mm,
        14 * mm
    )

    canvas.setFillColor(
        colors.HexColor("#555555")
    )

    canvas.setFont(
        "Helvetica",
        7
    )

    canvas.drawString(
        10 * mm,
        8 * mm,
        "Confidential - For official use only"
    )

    canvas.drawRightString(
        page_width - 10 * mm,
        8 * mm,
        f"Page {canvas.getPageNumber()}"
    )

    canvas.restoreState()


def create_pdf(filtered_data):
    """
    Create a PDF containing filtered records and
    the corresponding signature images.
    """

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
        "PDFTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=14,
        leading=18,
        spaceAfter=8
    )

    cell_style = ParagraphStyle(
        "PDFCell",
        parent=styles["BodyText"],
        fontSize=6,
        leading=7,
        wordWrap="CJK"
    )

    header_style = ParagraphStyle(
        "PDFHeader",
        parent=styles["BodyText"],
        fontSize=6,
        leading=7,
        textColor=colors.white,
        alignment=TA_CENTER
    )

    pdf_elements = []

    pdf_elements.append(
        Paragraph(
            "Participants' Data",
            title_style
        )
    )

    pdf_elements.append(
        Paragraph(
            f"Number of records: {len(filtered_data)}",
            cell_style
        )
    )

    pdf_elements.append(
        Spacer(1, 5 * mm)
    )

    # Arrange all columns, with the signature column last
    pdf_columns = [
        column
        for column in filtered_data.columns
        if column != SIGNATURE_URL_COLUMN
    ]

    pdf_columns.append(SIGNATURE_URL_COLUMN)

    table_header = [
        Paragraph(
            html.escape(str(column)),
            header_style
        )
        for column in pdf_columns
    ]

    table_data = [table_header]

    for _, row in filtered_data.iterrows():

        row_values = []

        for column in pdf_columns:

            # Add signature image
            if column == SIGNATURE_URL_COLUMN:

                signature_data_url = row.get(
                    SIGNATURE_URL_COLUMN
                )

                if (
                    pd.notna(signature_data_url)
                    and str(signature_data_url).startswith(
                        "data:image"
                    )
                ):
                    try:
                        encoded_part = str(
                            signature_data_url
                        ).split(",", 1)[1]

                        image_bytes = base64.b64decode(
                            encoded_part
                        )

                        image_file = io.BytesIO(
                            image_bytes
                        )

                        signature_image = Image(
                            image_file,
                            width=25 * mm,
                            height=12 * mm
                        )

                        row_values.append(
                            signature_image
                        )

                    except Exception:
                        row_values.append(
                            Paragraph(
                                "Unavailable",
                                cell_style
                            )
                        )

                else:
                    row_values.append(
                        Paragraph(
                            "No signature",
                            cell_style
                        )
                    )

            # Add ordinary text cell
            else:
                value = row.get(column, "")

                if pd.isna(value):
                    value = ""

                row_values.append(
                    Paragraph(
                        html.escape(str(value)),
                        cell_style
                    )
                )

        table_data.append(row_values)

    # Calculate widths for the landscape A4 page
    available_width = (
        landscape(A4)[0] - 16 * mm
    )

    column_count = len(pdf_columns)

    column_widths = [
        available_width / column_count
        for _ in range(column_count)
    ]

    table = Table(
        table_data,
        colWidths=column_widths,
        repeatRows=1
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#1F4E78")
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.white
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.25,
                    colors.grey
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE"
                ),
                (
                    "ALIGN",
                    (0, 0),
                    (-1, 0),
                    "CENTER"
                ),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [
                        colors.white,
                        colors.HexColor("#F2F6FA")
                    ]
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    3
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    3
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    3
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    3
                )
            ]
        )
    )

    pdf_elements.append(table)

    document.build(pdf_elements)

    return pdf_buffer.getvalue()


@st.cache_data
def load_data():

    response = requests.get(
        CSV_URL,
        headers={
            "Authorization": f"Token {API_TOKEN}"
        }
    )

    response.raise_for_status()

    loaded_df = pd.read_csv(
        io.StringIO(response.text),
        sep=";"
    )

    # Drop unwanted columns
    loaded_df = loaded_df.drop(
        columns=[
            "start",
            "end",
            "_id",
            "_uuid",
            "Signature",
            "meta/rootUuid"
        ],
        errors="ignore"
    )

    return loaded_df


# --- Load data safely ---
try:

    df = load_data()

    st.success(
        f"Loaded {len(df)} records"
    )

except requests.exceptions.RequestException as error:

    st.error(
        f"Unable to load data from KoboToolbox: {error}"
    )

    st.stop()

except Exception as error:

    st.error(
        f"An error occurred while processing the data: {error}"
    )

    st.stop()


# --- Configure your columns ---
NAME_COLUMN = "Name"
DATE_COLUMN = "Activity Date"
SIGNATURE_URL_COLUMN = "Signature_URL"


# --- Validate required columns ---
missing_columns = [
    column
    for column in [
        NAME_COLUMN,
        DATE_COLUMN,
        SIGNATURE_URL_COLUMN
    ]
    if column not in df.columns
]

if missing_columns:

    st.error(
        "The following required columns were not found in "
        "the dataset: "
        + ", ".join(missing_columns)
    )

    st.stop()


# --- Convert protected signature URLs into images ---
with st.spinner("Loading signature images..."):

    df[SIGNATURE_URL_COLUMN] = df[
        SIGNATURE_URL_COLUMN
    ].apply(
        download_signature_as_data_url
    )


# --- Extract month and year ---
df["_month"] = pd.to_datetime(
    df[DATE_COLUMN],
    errors="coerce"
).dt.strftime("%B %Y")


# --- Build month options ---
month_options = ["All"] + sorted(
    df["_month"]
    .dropna()
    .unique()
    .tolist(),
    key=lambda x: pd.to_datetime(
        x,
        format="%B %Y"
    )
)


# --- Build name options ---
name_options = ["All"] + sorted(
    df[NAME_COLUMN]
    .dropna()
    .astype(str)
    .unique()
    .tolist()
)


# --- Application title ---
st.title("Participants' Data")

st.write(
    "Use the filters below to search records by name and activity month."
)


# --- Filters ---
filter_column_1, filter_column_2, filter_column_3 = st.columns(3)


with filter_column_1:

    name_contains = st.text_input(
        "Name contains:",
        value=""
    )


with filter_column_2:

    name_pick = st.selectbox(
        "Or pick name:",
        options=name_options
    )


with filter_column_3:

    month = st.selectbox(
        "Month:",
        options=month_options
    )


# --- Copy the complete dataset ---
filtered = df.copy()


# --- Filter by name text ---
if name_contains:

    filtered = filtered[
        filtered[NAME_COLUMN]
        .astype(str)
        .str.contains(
            name_contains,
            case=False,
            na=False
        )
    ]


# --- Otherwise filter by selected name ---
elif name_pick != "All":

    filtered = filtered[
        filtered[NAME_COLUMN]
        .astype(str)
        .eq(name_pick)
    ]


# --- Filter by month ---
if month != "All":

    filtered = filtered[
        filtered["_month"] == month
    ]


# --- Remove helper column ---
display_df = filtered.drop(
    columns=["_month"],
    errors="ignore"
)


# --- Display count ---
st.write(
    f"### Showing {len(display_df)} matching records"
)


# --- Configure image column ---
column_config = {
    SIGNATURE_URL_COLUMN: st.column_config.ImageColumn(
        "Signature",
        help="Submitted signature",
        width="small"
    )
}


# --- Display first 100 records ---
st.dataframe(
    display_df.head(100),
    use_container_width=True,
    hide_index=True,
    column_config=column_config
)


# --- Create Excel file ---
excel_buffer = io.BytesIO()

with pd.ExcelWriter(
    excel_buffer,
    engine="openpyxl"
) as writer:

    display_df.to_excel(
        writer,
        index=False,
        sheet_name="Filtered Data"
    )

excel_data = excel_buffer.getvalue()


# --- Download Excel ---
st.download_button(
    label="Download Excel",
    data=excel_data,
    file_name="Download.xlsx",
    mime=(
        "application/vnd.openxmlformats-officedocument."
        "spreadsheetml.sheet"
    )
)


# --- Create PDF file ---
    # --- define table ---
DOCUSIGN_FIELDS = [
    ("Company and project logo", ""),
    ("Activity name", ""),
    ("Project name", ""),
    ("Facilitated by", "")
]


with st.spinner("Preparing PDF with signatures..."):

    pdf_data = create_pdf(
        display_df
    )


# --- Download PDF ---
st.download_button(
    label="Download PDF with Signatures",
    data=pdf_data,
    file_name="Participants_Data_with_Signatures.pdf",
    mime="application/pdf"
)
