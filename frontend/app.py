import streamlit as st
import datetime
import base64
from pathlib import Path

from pages_content import assistant, dataset_overview, export_csv, graphs, home, login

st.set_page_config(page_title="Steel Plant Delay Analytics", page_icon="SP", layout="wide", initial_sidebar_state="expanded")

def load_css():
    css_files = ["theme.css", "dashboard.css", "sidebar.css", "components.css"]
    css_content = ""
    for file in css_files:
        css_path = Path(__file__).parent / "assets" / "styles" / file
        if css_path.exists():
            css_content += css_path.read_text(encoding='utf-8') + "\n"
    if css_content:
        st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)

if not st.session_state.get("authenticated"):
    login.render()
    st.stop()

# Load Dashboard CSS
load_css()

# Dynamic Theme Override
if st.session_state.get("theme") == "light":
    st.markdown("""<style>
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
    </style>""", unsafe_allow_html=True)

# Load Logo Base64
def get_base64_image(image_path):
    if not image_path.exists():
        return ""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

logo_path = Path(__file__).parent / "assets" / "images" / "logo.png"
logo_b64 = get_base64_image(logo_path)
logo_html = f'<img src="data:image/png;base64,{logo_b64}" style="width:100%;height:100%;object-fit:contain;">' if logo_b64 else "SP"

# Header
now = datetime.datetime.now().strftime("%d %b %Y, %H:%M")
role_label = "Administrator" if st.session_state.get("role") == "admin" else "Operator"
username = st.session_state.get("username", "User")

st.markdown(f"""
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
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color:var(--text-secondary);"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
        </div>
        <form action="javascript:void(0);" style="display:none;">
            <!-- Logout action is handled in sidebar, this is just visual consistency if needed -->
        </form>
    </div>
</div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown(f"""
        <div style="padding: 0 16px;">
            <div style="display:flex;align-items:center;gap:12px;margin-bottom:8px;">
                <div style="width:42px;height:42px;display:flex;justify-content:center;align-items:center;">{logo_html}</div>
                <div style="font-weight:700;font-size:16px;color:var(--text-primary);line-height:1.2;">VIZAG STEEL PLANT<br><span style="font-size:12px;color:var(--text-secondary);font-weight:500;">Delay Analytics</span></div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="sidebar-nav-container">', unsafe_allow_html=True)
    
    options = ["Home", "Dashboard", "Dataset Overview", "AI Assistant"]
    if st.session_state.get("role") == "admin":
        options.insert(2, "Upload CSV")
        
    choice = st.radio("Navigation", options, label_visibility="collapsed")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Theme toggle and Logout at bottom
    st.markdown('<div class="theme-toggle-container">', unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1])
    with col1:
        theme_icon = "☀️ Light Mode" if st.session_state.get("theme") == "dark" or not st.session_state.get("theme") else "🌙 Dark Mode"
        if st.button(theme_icon, use_container_width=True, key="theme_toggle"):
            st.session_state["theme"] = "light" if st.session_state.get("theme", "dark") == "dark" else "dark"
            st.rerun()
    with col2:
        if st.button("Logout", use_container_width=True, key="logout_btn"):
            st.session_state.clear()
            st.rerun()
            
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="sidebar-footer">© 2026 Steel Plant Delay Analytics</div>', unsafe_allow_html=True)


# Main Content Routing
# Removed manual div wrappers because they interfere with Streamlit layout

if choice == "Home":
    home.render()
elif choice == "Dashboard":
    graphs.render()
elif choice == "Upload CSV":
    export_csv.render()
elif choice == "Dataset Overview":
    dataset_overview.render()
elif choice == "AI Assistant":
    assistant.render()