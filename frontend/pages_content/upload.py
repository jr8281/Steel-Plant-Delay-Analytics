import streamlit as st
import requests

from pages_content.utils import API, render_hero_banner


def render():
    render_hero_banner()

    st.markdown('<div class="upload-intro">', unsafe_allow_html=True)
    st.markdown('<div class="upload-icon">🏭</div>', unsafe_allow_html=True)
    st.markdown('<h2 class="upload-title">Welcome to Steel Plant Delay Analytics</h2>', unsafe_allow_html=True)
    st.markdown(
        '<p class="upload-subtitle">Upload your dataset below to begin exploring interactive '
        'delay analytics, KPI metrics, and visual insights.</p>',
        unsafe_allow_html=True,
    )
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown(
        """
        <div class="upload-columns-box">
            <div class="upload-columns-header">📄 Expected Columns</div>
            <p class="upload-columns-list">
                Delay Date, Shop Code, Shop, Eqpt, Sub Eqpt, From, Upto, Durn, agency, Descr, Material, Delay Code, Contd
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        uploaded_file = st.file_uploader("Upload Excel/CSV File", type=["csv", "xlsx", "xls"])

        mode = st.radio(
            "Ingestion mode",
            options=["replace", "append"],
            format_func=lambda m: "Replace all existing data" if m == "replace" else "Append to existing data",
            help="Replace wipes all current delay records before importing this file. "
                 "Append adds these rows without touching existing data.",
        )
        if mode == "replace":
            st.warning("⚠️ Replace mode will permanently delete all existing delay records before importing.")

        if uploaded_file is not None:
            if st.button("Ingest Data", type="primary", use_container_width=True):
                with st.spinner("Processing and ingesting data..."):
                    headers = {}
                    if st.session_state.get("token"):
                        headers["Authorization"] = f"Bearer {st.session_state['token']}"

                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}

                    try:
                        resp = requests.post(
                            f"{API}/upload", headers=headers, files=files, params={"mode": mode}, timeout=60
                        )
                        if resp.ok:
                            data = resp.json()
                            st.success(f"{data.get('message')} ({data.get('records_ingested')} records, {mode} mode)")
                        else:
                            err = resp.json().get("detail", "Failed to upload")
                            st.error(err)
                    except requests.RequestException as e:
                        st.error(f"Failed to connect to backend: {e}")