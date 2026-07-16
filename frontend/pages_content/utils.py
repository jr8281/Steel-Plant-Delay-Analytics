import os
from datetime import date

import requests
import streamlit as st

API = os.getenv("API_BASE_URL", "http://localhost:8000")


def api_request(method: str, path: str, **kwargs):
    headers = kwargs.pop("headers", {})
    token = st.session_state.get("token")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        response = requests.request(method, f"{API}{path}", headers=headers, timeout=20, **kwargs)
    except requests.RequestException as exc:
        st.error(f"The API is unavailable at {API}. Start the FastAPI service first. ({exc})")
        return None
    if response.status_code == 401:
        st.session_state.clear()
        st.rerun()
    if not response.ok:
        detail = response.json().get("detail", response.text) if response.content else "Request failed"
        st.error(str(detail))
        return None
    return response.json()


def page_heading(title: str, subtitle: str):
    st.markdown(f"<div class='page-heading'><h1>{title}</h1><p>{subtitle}</p></div>", unsafe_allow_html=True)


def selected_dates(filter_data: dict):
    start = date.fromisoformat(str(filter_data["date_min"])) if filter_data.get("date_min") else date.today()
    end = date.fromisoformat(str(filter_data["date_max"])) if filter_data.get("date_max") else date.today()
    result = st.date_input("Delay date", value=(start, end))
    return result if isinstance(result, tuple) and len(result) == 2 else (start, end)


def query_params(shop_ids=None, equipment=None, cause=None, dates=None):
    params = []
    for shop_id in shop_ids or []:
        params.append(("shop_ids", shop_id))
    if equipment:
        params.append(("equipment", equipment))
    if cause:
        params.append(("cause", cause))
    if dates:
        params.extend([("start_date", dates[0].isoformat()), ("end_date", dates[1].isoformat())])
    return params

def render_hero_banner():
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1e3a8a, #d97706); padding: 32px 40px; border-radius: 16px; margin-bottom: 32px; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.2);">
        <div style="display: flex; align-items: center; gap: 16px; margin-bottom: 12px;">
            <div style="font-size: 32px;">🏭</div>
            <h1 style="color: white !important; font-size: 32px !important; font-weight: 800 !important; margin: 0 !important; line-height: 1.2 !important;">Steel Plant Delay Analytics Dashboard</h1>
        </div>
        <p style="color: rgba(255,255,255,0.9) !important; font-size: 16px !important; margin: 0 !important;">Interactive visual analytics for operational delay monitoring and decision support</p>
    </div>
    """, unsafe_allow_html=True)
