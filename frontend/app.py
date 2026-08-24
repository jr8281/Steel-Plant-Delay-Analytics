import streamlit as st
import datetime
import base64
from pathlib import Path

from pages_content import assistant, dataset_overview, upload, graphs, home, login, predictions, utils

st.set_page_config(page_title="Steel Plant Delay Analytics", page_icon="SP", layout="wide", initial_sidebar_state="expanded")


def load_css():
    css_files = ["theme.css", "dashboard.css", "sidebar.css", "components.css", "assistant.css", "upload.css"]
    css_content = ""
    for file in css_files:
        css_path = Path(__file__).parent / "assets" / "styles" / file
        if css_path.exists():
            css_content += css_path.read_text(encoding="utf-8") + "\n"
    if css_content:
        st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)


if not st.session_state.get("authenticated"):
    login.render()
    st.stop()

load_css()

if st.session_state.get("theme") == "light":
    st.markdown(
        """<style>
    :root {
        --bg-primary: #F1F5F9;
        --bg-sidebar: #FFFFFF;
        --bg-card: #FFFFFF;
        --accent-blue: #2563EB;
        --accent-blue-hover: #1D4ED8;
        --accent-green: #16A34A;
        --status-warning: #D97706;
        --status-danger: #DC2626;
        --text-primary: #0F172A;
        --text-secondary: #475569;
        --border-color: rgba(0, 0, 0, 0.08);
        --border-hover: rgba(0, 0, 0, 0.15);
        --glass-bg: rgba(255, 255, 255, 0.8);
        --shadow-soft: 0 2px 5px rgba(0,0,0,0.05);
        --shadow-hover: 0 10px 15px -3px rgba(0, 0, 0, 0.08);
    }
    </style>""",
        unsafe_allow_html=True,
    )


def get_base64_image(image_path):
    if not image_path.exists():
        return ""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


logo_path = Path(__file__).parent / "assets" / "images" / "logo.png"
logo_b64 = get_base64_image(logo_path)
logo_html = (
    f'<img src="data:image/png;base64,{logo_b64}" style="width:100%;height:100%;object-fit:contain;">'
    if logo_b64 else "SP"
)

now = datetime.datetime.now().strftime("%d %b %Y, %H:%M")
role_label = "Administrator" if st.session_state.get("role") == "admin" else "Operator"
username = st.session_state.get("username", "User")

st.markdown(
    f"""
<div class="custom-header">
    <div class="header-left">
        <div style="width:48px;height:48px;display:flex;justify-content:center;align-items:center;">{logo_html}</div>
        <div class="header-titles">
            <div class="header-title">Steel Plant Delay Analytics</div>
            <div class="header-subtitle">Enterprise Operational Intelligence</div>
        </div>
    </div>
    <div class="header-right">
        <div class="header-datetime">{now}</div>
        <div class="header-user-chip">
            <div class="header-user-info">
                <div class="header-username">{username}</div>
                <div class="header-role">{role_label}</div>
            </div>
        </div>
    </div>
</div>
""",
    unsafe_allow_html=True,
)



options = ["Home", "Dashboard", "Dataset Overview", "Predictions", "AI Assistant"]
if st.session_state.get("role") == "admin":
    options.insert(2, "Upload CSV")

if "nav_choice" not in st.session_state or st.session_state["nav_choice"] not in options:
    st.session_state["nav_choice"] = "Home"

# Top Navigation Bar — Full Page Layout
nav_cols = st.columns(len(options) + 2)
for idx, opt in enumerate(options):
    is_selected = (st.session_state["nav_choice"] == opt)
    btn_type = "primary" if is_selected else "secondary"
    if nav_cols[idx].button(opt, key=f"topnav_{opt}", type=btn_type, use_container_width=True):
        st.session_state["nav_choice"] = opt
        st.rerun()

with nav_cols[-2]:
    theme_icon = "☀️ Light Mode" if st.session_state.get("theme") == "dark" or not st.session_state.get("theme") else "🌙 Dark Mode"
    if st.button(theme_icon, use_container_width=True, key="top_theme_toggle"):
        st.session_state["theme"] = "light" if st.session_state.get("theme", "dark") == "dark" else "dark"
        st.rerun()

with nav_cols[-1]:
    if st.button("Logout", use_container_width=True, key="top_logout_btn"):
        utils.logout()
        st.rerun()

current_page = st.session_state["nav_choice"]

if current_page == "Home":
    home.render()
elif current_page == "Dashboard":
    graphs.render()
elif current_page == "Upload CSV":
    upload.render()
elif current_page == "Dataset Overview":
    dataset_overview.render()
elif current_page == "Predictions":
    predictions.render()
elif current_page == "AI Assistant":
    assistant.render()