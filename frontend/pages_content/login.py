import base64
import os
from pathlib import Path

import requests
import streamlit as st

API = os.getenv("API_BASE_URL", "http://localhost:8000")


def _get_base64_image(image_path: Path) -> str:
    if not image_path.exists():
        return ""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def render():
    css_files = ["theme.css", "login.css"]
    css_content = ""
    for file in css_files:
        css_path = Path(__file__).parent.parent / "assets" / "styles" / file
        if css_path.exists():
            css_content += css_path.read_text(encoding="utf-8") + "\n"
    if css_content:
        st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)

    logo_path = Path(__file__).parent.parent / "assets" / "images" / "logo.png"
    logo_b64 = _get_base64_image(logo_path)

    bg_path = Path(__file__).parent.parent / "assets" / "images" / "background.png"
    bg_b64 = _get_base64_image(bg_path)

    st.markdown(
        f"""<style>
        .stApp, [data-testid="stAppViewContainer"], .login-page {{
            background-image: linear-gradient(rgba(3,10,18,0.72), rgba(3,10,18,0.82)), url("/app/static/images/background.png"), url("data:image/png;base64,{bg_b64}") !important;
            background-size: cover !important;
            background-position: center !important;
            background-repeat: no-repeat !important;
            background-attachment: fixed !important;
        }}
        </style>""",
        unsafe_allow_html=True,
    )

    st.markdown('<div class="login-page"></div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.container(key="login_card"):
            if logo_b64:
                st.markdown(
                    f'<div class="login-logo" style="text-align:center;margin-bottom:16px;">'
                    f'<img src="data:image/png;base64,{logo_b64}" style="width:72px;height:72px;object-fit:contain;">'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            st.markdown('<h1 class="login-title">Steel Plant Delay Analytics</h1>', unsafe_allow_html=True)
            st.markdown('<p class="login-description">Enterprise Operational Intelligence</p>', unsafe_allow_html=True)

            with st.form("login_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Sign In", use_container_width=True, type="primary")

            if submitted:
                if not username or not password:
                    st.error("Please enter both username and password.")
                else:
                    try:
                        resp = requests.post(
                            f"{API}/auth/login",
                            json={"username": username, "password": password},
                            timeout=15,
                        )
                    except requests.RequestException as exc:
                        st.error(f"Could not reach the backend at {API}. Is it running? ({exc})")
                        st.stop()

                    if resp.ok:
                        data = resp.json()
                        st.session_state["authenticated"] = True
                        st.session_state["token"] = data["access_token"]
                        st.session_state["username"] = data["username"]
                        st.session_state["role"] = data["role"]
                        st.session_state["shop_id"] = data.get("shop_id")
                        st.session_state["must_reset_password"] = data.get("must_reset_password", False)
                        st.rerun()
                    else:
                        detail = resp.json().get("detail", "Login failed.") if resp.content else "Login failed."
                        st.error(detail)