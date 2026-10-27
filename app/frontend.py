"""Streamlit UI for ReviewClean. Uses the FastAPI backend."""
import io
import os

import pandas as pd
import requests
import streamlit as st

API_URL = os.getenv(
    "REVIEWCLEAN_API_URL",
    "https://review-clean.onrender.com"
).rstrip("/")

st.set_page_config(page_title="ReviewClean | Data Quality Studio", page_icon="🧹", layout="wide")
st.markdown("""
<style>
.block-container {padding-top: 2rem; max-width: 1250px;}
[data-testid="stAppViewContainer"] {background: linear-gradient(135deg,#0b1020 0%,#111827 55%,#151525 100%);}
[data-testid="stMetric"] {background: rgba(255,255,255,.045); border: 1px solid rgba(255,255,255,.09); padding: 16px; border-radius: 14px;}
section[data-testid="stSidebar"] {background: #0b1020;}
[data-testid="stFileUploader"] small,
[data-testid="stFileUploaderDropzoneInstructions"] {
    display: none;
}
</style>
""", unsafe_allow_html=True)

st.title("ReviewClean")
st.caption("DATA QUALITY STUDIO  /  Clean customer-review CSVs with transparent, testable rules.")
with st.sidebar:
    st.header("Cleaning rules")
    trim = st.toggle("Trim surrounding whitespace", value=True)
    dedupe = st.toggle("Remove exact duplicate rows", value=True)
    st.divider()
    # st.caption("Empty rows are always removed. Partially completed reviews are preserved.")
    # st.caption(f"Backend: `{API_URL}`")

uploaded = st.file_uploader("Upload a customer reviews CSV", type=["csv"], help="Maximum file size: 10 MB")
st.caption("Maximum 10 MB per file • CSV")
if uploaded:
    raw = uploaded.getvalue()
    st.write(f"**File:** {uploaded.name} · **Size:** {len(raw):,} bytes")
    try:
        source_preview = pd.read_csv(io.BytesIO(raw), encoding="utf-8-sig")
        st.subheader("Source preview")
        st.dataframe(source_preview.head(8), use_container_width=True, hide_index=True)
    except Exception as exc:
        st.error(f"The preview could not read this CSV: {exc}")

    if st.button("✨ Clean CSV", type="primary", use_container_width=True):
        with st.spinner("Validating and cleaning your file..."):
            try:
                response = requests.post(
                    f"{API_URL}/clean",
                    files={"file": (uploaded.name, raw, "text/csv")},
                    data={"trim_whitespace": str(trim).lower(), "drop_duplicates": str(dedupe).lower()},
                    timeout=45,
                )
                if not response.ok:
                    try:
                        detail = response.json().get("detail", response.text)
                    except ValueError:
                        detail = response.text
                    st.error(f"Cleaning failed ({response.status_code}): {detail}")
                else:
                    cleaned = pd.read_csv(io.BytesIO(response.content))
                    pairs = dict(item.split("=", 1) for item in response.headers.get("X-ReviewClean-Stats", "").split(";") if "=" in item)
                    stats = {key: int(value) for key, value in pairs.items()}
                    st.session_state["cleaned_bytes"] = response.content
                    st.session_state["cleaned_df"] = cleaned
                    st.session_state["stats"] = stats
            except requests.RequestException as exc:
                st.error(f"Could not reach the API. Start FastAPI and check the backend URL. Details: {exc}")

if "stats" in st.session_state:
    stats = st.session_state["stats"]
    st.divider()
    st.subheader("Cleaning report")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Original rows", f"{stats['original_rows']:,}")
    c2.metric("Clean rows", f"{stats['cleaned_rows']:,}")
    c3.metric("Empty rows removed", f"{stats['empty_rows_removed']:,}")
    c4.metric("Duplicates removed", f"{stats['duplicate_rows_removed']:,}")
    removed = stats["rows_removed"]
    total = max(stats["original_rows"], 1)
    st.progress(min(removed / total, 1.0), text=f"{removed:,} of {stats['original_rows']:,} rows removed ({removed / total:.1%})")
    st.subheader("Cleaned data preview")
    st.dataframe(st.session_state["cleaned_df"].head(25), use_container_width=True, hide_index=True)
    st.download_button("⬇ Download cleaned_reviews.csv", data=st.session_state["cleaned_bytes"], file_name="cleaned_reviews.csv", mime="text/csv", type="primary")
else:
    st.info("Upload a CSV to begin. Use the sample below to try it quickly.")
    sample = b"review_id,customer,review,rating\n1,Asha,Great product,5\n2,Ravi,  ,3\n1,Asha,Great product,5\n3,Meera,Works well,4\n,,,\n"
    st.download_button("Download sample dirty CSV", sample, "sample_reviews.csv", "text/csv")

st.divider()
# st.caption("ReviewClean · FastAPI + Streamlit + pandas + pytest")
