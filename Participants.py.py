# -*- coding: utf-8 -*-

import pandas as pd
import requests
import io
import base64
import streamlit as st


# --- Page configuration ---
st.set_page_config(
    page_title="Participants' Data",
    page_icon="",
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
            "meta/rootUuid"
        ],
        errors="ignore"
    )

    return loaded_df


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


# --- Configure your specific columns here ---
NAME_COLUMN = "Name"
DATE_COLUMN = "Activity Date"
SIGNATURE_URL_COLUMN = "Signature URL"


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
        "The following required columns were not found in the dataset: "
        + ", ".join(missing_columns)
    )
    st.stop()


# --- Convert protected Signature URLs into displayable images ---
with st.spinner("Loading signature images..."):
    df[SIGNATURE_URL_COLUMN] = df[
        SIGNATURE_URL_COLUMN
    ].apply(
        download_signature_as_data_url
    )


# --- Pre-process the date column to extract months ---
df["_month"] = pd.to_datetime(
    df[DATE_COLUMN],
    errors="coerce"
).dt.strftime("%B %Y")


# --- Build sorted month options ---
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


# --- Build sorted name options ---
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


# --- Filter data ---
filtered = df.copy()


# --- Filter by Name ---
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

elif name_pick != "All":
    filtered = filtered[
        filtered[NAME_COLUMN]
        .astype(str)
        .eq(name_pick)
    ]


# --- Filter by Month ---
if month != "All":
    filtered = filtered[
        filtered["_month"] == month
    ]


# --- Drop helper column before display/export ---
display_df = filtered.drop(
    columns=["_month"],
    errors="ignore"
)


# --- Display record count ---
st.write(
    f"### Showing {len(display_df)} matching records"
)


# --- Configure Signature URL as an image column ---
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


# --- Save filtered data to Excel ---
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


# --- Download button ---
st.download_button(
    label="Download Excel",
    data=excel_data,
    file_name="Download.xlsx",
    mime=(
        "application/vnd.openxmlformats-officedocument."
        "spreadsheetml.sheet"
    )
)
