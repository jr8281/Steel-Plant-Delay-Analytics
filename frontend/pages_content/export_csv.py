import streamlit as st
import requests
import io
from pages_content.utils import render_hero_banner, API

def render():
    render_hero_banner()
    
    st.markdown("""
        <div style="text-align: center; margin: 40px 0;">
            <div style="font-size: 48px; margin-bottom: 16px;">🏭</div>
            <h2 style="font-size: 28px; font-weight: 800; margin-bottom: 16px; color: var(--text-primary);">Welcome to Steel Plant Delay Analytics</h2>
            <p style="color: var(--text-secondary); max-width: 600px; margin: 0 auto; line-height: 1.6; font-size: 15px;">
                Upload your dataset below to begin exploring interactive delay analytics, KPI metrics, and visual insights.
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # Expected Columns Box
    st.markdown("""
        <div style="max-width: 700px; margin: 0 auto 40px auto; border: 1px dashed var(--accent-blue); background: rgba(37,99,235,0.05); padding: 24px; border-radius: 12px; text-align: center;">
            <div style="display: flex; align-items: center; justify-content: center; gap: 8px; margin-bottom: 12px;">
                <span style="font-size: 18px;">📄</span>
                <span style="font-weight: 700; color: var(--text-primary);">Expected Columns</span>
            </div>
            <p style="color: var(--text-secondary); font-size: 14px; margin: 0;">
                Delay Date, Shop Code, Shop, Eqpt, Sub Eqpt, From, Upto, Durn, agency, Descr, Material, Delay Code, Contd
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        uploaded_file = st.file_uploader("Upload Excel/CSV File", type=["csv", "xlsx", "xls"])
        
        if uploaded_file is not None:
            if st.button("Ingest Data", kind="primary", use_container_width=True):
                with st.spinner("Processing and ingesting data..."):
                    # Send to backend API
                    headers = {}
                    if st.session_state.get("token"):
                        headers["Authorization"] = f"Bearer {st.session_state['token']}"
                        
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                    
                    try:
                        resp = requests.post(f"{API}/upload", headers=headers, files=files, timeout=60)
                        if resp.ok:
                            data = resp.json()
                            st.success(f"{data.get('message')} ({data.get('records_ingested')} records)")
                        else:
                            err = resp.json().get("detail", "Failed to upload")
                            st.error(err)
                    except requests.RequestException as e:
                        st.error(f"Failed to connect to backend: {e}")
