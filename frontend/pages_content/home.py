import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from pages_content.utils import api_request, render_hero_banner

def render():
    render_hero_banner()
    
    with st.spinner("Loading dashboard data..."):
        data = api_request("GET", "/analytics/home-dashboard")
        
    if not data:
        st.info("No data available. Please upload a dataset in the Upload CSV page.")
        return

    kpis = data.get("kpis", {})
    
    # Custom CSS for KPI cards to match screenshot
    st.markdown("""
        <style>
        .kpi-card {
            background-color: var(--card-bg);
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            margin-bottom: 24px;
            border-left: 6px solid;
            position: relative;
        }
        .kpi-card.blue { border-left-color: #3b82f6; }
        .kpi-card.orange { border-left-color: #f97316; }
        .kpi-card.green { border-left-color: #10b981; }
        .kpi-card.purple { border-left-color: #8b5cf6; }
        
        .kpi-title {
            font-size: 13px;
            font-weight: 700;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .kpi-value {
            font-size: 36px;
            font-weight: 800;
            color: var(--text-primary);
            margin-bottom: 4px;
            line-height: 1;
        }
        .kpi-subtitle {
            font-size: 13px;
            color: var(--text-secondary);
        }
        </style>
    """, unsafe_allow_html=True)

    # KPI Row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="kpi-card blue">
            <div class="kpi-title">📄 TOTAL DELAY RECORDS</div>
            <div class="kpi-value">{kpis.get('total_records', 0)}</div>
            <div class="kpi-subtitle">After applied filters</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="kpi-card orange">
            <div class="kpi-title">🏭 DEPARTMENTS</div>
            <div class="kpi-value">{kpis.get('departments', 0)}</div>
            <div class="kpi-subtitle">Unique shops / departments</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="kpi-card green">
            <div class="kpi-title">⚙️ EQUIPMENT TYPES</div>
            <div class="kpi-value">{kpis.get('equipment_types', 0)}</div>
            <div class="kpi-subtitle">Distinct equipment</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="kpi-card purple">
            <div class="kpi-title">👨‍🔧 AGENCIES</div>
            <div class="kpi-value">{kpis.get('agencies', 0)}</div>
            <div class="kpi-subtitle">Responsible agencies</div>
        </div>
        """, unsafe_allow_html=True)

    # Shared Chart config for dark theme
    chart_config = {
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "font": {"color": "#a1a1aa"}
    }
    
    # ROW 1: Department-wise vs Top 10 Equipment
    col_left, col_right = st.columns(2)
    with col_left:
        st.markdown('<h3 style="font-size: 16px; font-weight: 600; margin-bottom: 16px; display: flex; align-items: center; gap: 8px;">📊 Department-wise Delay Count</h3>', unsafe_allow_html=True)
        st.markdown('<hr style="border-color: #3f3f46; margin-top: 0;">', unsafe_allow_html=True)
        dept_data = data.get("department_delays", [])
        if dept_data:
            df_dept = pd.DataFrame(dept_data)
            fig1 = px.bar(df_dept, x="name", y="count", text_auto=True, color_discrete_sequence=["#60a5fa"])
            fig1.update_layout(**chart_config, margin=dict(l=0, r=0, t=30, b=0), xaxis_title="Department", yaxis_title="Delay Count")
            st.plotly_chart(fig1, use_container_width=True)
        else:
            st.info("No department data.")

    with col_right:
        st.markdown('<h3 style="font-size: 16px; font-weight: 600; margin-bottom: 16px; display: flex; align-items: center; gap: 8px;">⚙️ Top 10 Equipment — Maximum Delays</h3>', unsafe_allow_html=True)
        st.markdown('<hr style="border-color: #3f3f46; margin-top: 0;">', unsafe_allow_html=True)
        eqpt_data = data.get("top_equipment", [])
        if eqpt_data:
            df_eqpt = pd.DataFrame(eqpt_data).sort_values(by="count", ascending=True)
            fig2 = px.bar(df_eqpt, x="count", y="name", orientation='h', text_auto=True, color_discrete_sequence=["#fbbf24"])
            fig2.update_layout(**chart_config, margin=dict(l=0, r=0, t=30, b=0), xaxis_title="Delay Count", yaxis_title="")
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No equipment data.")

    # ROW 2: Agency Distribution vs Material Distribution
    col_left2, col_right2 = st.columns(2)
    with col_left2:
        st.markdown('<h3 style="font-size: 16px; font-weight: 600; margin-bottom: 16px; display: flex; align-items: center; gap: 8px;">🏢 Agency Distribution</h3>', unsafe_allow_html=True)
        st.markdown('<hr style="border-color: #3f3f46; margin-top: 0;">', unsafe_allow_html=True)
        agency_data = data.get("agency_distribution", [])
        if agency_data:
            df_agency = pd.DataFrame(agency_data)
            fig3 = px.pie(df_agency, names="name", values="count", hole=0.5, color_discrete_sequence=px.colors.qualitative.Pastel)
            fig3.update_layout(**chart_config, margin=dict(l=0, r=0, t=30, b=0))
            fig3.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig3, use_container_width=True)
        else:
            st.info("No agency data.")

    with col_right2:
        st.markdown('<h3 style="font-size: 16px; font-weight: 600; margin-bottom: 16px; display: flex; align-items: center; gap: 8px;">🧱 Material-wise Distribution</h3>', unsafe_allow_html=True)
        st.markdown('<hr style="border-color: #3f3f46; margin-top: 0;">', unsafe_allow_html=True)
        material_data = data.get("material_distribution", [])
        if material_data:
            df_mat = pd.DataFrame(material_data)
            fig4 = px.treemap(df_mat, path=["name"], values="count", color_discrete_sequence=["#60a5fa"])
            fig4.update_layout(**chart_config, margin=dict(l=0, r=0, t=30, b=0))
            st.plotly_chart(fig4, use_container_width=True)
        else:
            st.info("No material data.")

    # ROW 3: Top 10 Delay Reasons
    st.markdown('<h3 style="font-size: 16px; font-weight: 600; margin-bottom: 16px; display: flex; align-items: center; gap: 8px;">📋 Top 10 Delay Reasons</h3>', unsafe_allow_html=True)
    st.markdown('<hr style="border-color: #3f3f46; margin-top: 0;">', unsafe_allow_html=True)
    reason_data = data.get("top_delay_reasons", [])
    if reason_data:
        df_reason = pd.DataFrame(reason_data).sort_values(by="count", ascending=True)
        fig5 = px.bar(df_reason, x="count", y="name", orientation='h', text_auto=True, color_discrete_sequence=["#34d399"])
        fig5.update_layout(**chart_config, margin=dict(l=0, r=0, t=30, b=0), xaxis_title="Count", yaxis_title="")
        st.plotly_chart(fig5, use_container_width=True)
    else:
        st.info("No delay reasons data.")
