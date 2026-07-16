import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from pages_content.utils import api_request, render_hero_banner

# Helper for shift
def get_shift(t):
    if pd.isna(t): return 'Unknown'
    try:
        t = float(t)
        if 6.0 <= t < 14.0: return 'Morning'
        if 14.0 <= t < 22.0: return 'Evening'
        return 'Night'
    except:
        return 'Unknown'

@st.cache_data(ttl=300)
def fetch_delays_data():
    response = api_request("GET", "/delays", params={"limit": 5000})
    if not response or not response.get("items"):
        return pd.DataFrame()
    df = pd.DataFrame(response["items"])
    if not df.empty:
        # Data cleaning and prep
        df['delay_date'] = pd.to_datetime(df['delay_date'])
        df['durn'] = pd.to_numeric(df['durn'], errors='coerce').fillna(0)
        df['shift'] = df['from_time'].apply(get_shift)
        df['hour'] = pd.to_numeric(df['from_time'], errors='coerce').apply(lambda x: int(np.floor(x)) if pd.notna(x) else None)
        df.fillna({'shop': 'Unknown', 'agency_code': 'Unknown', 'material': 'Unknown', 'equipment_name': 'Unknown'}, inplace=True)
    return df

def render():
    render_hero_banner()
    
    st.markdown('<h2 class="page-title">Advanced Analytics Dashboard</h2>', unsafe_allow_html=True)
    
    with st.spinner("Loading analytics data..."):
        df = fetch_delays_data()
        
    if df.empty:
        st.info("No data available for the dashboard. Please upload a dataset first.")
        return

    # --- FILTERS ---
    st.markdown("### Filters")
    col_f1, col_f2, col_f3 = st.columns(3)
    
    departments = sorted(df['shop'].unique().tolist())
    agencies = sorted(df['agency_code'].unique().tolist())
    materials = sorted(df['material'].unique().tolist())
    
    with col_f1:
        sel_depts = st.multiselect("Department (Shop)", options=departments, default=st.session_state.get('dash_depts', []), key='dash_depts')
    with col_f2:
        sel_agencies = st.multiselect("Agency", options=agencies, default=st.session_state.get('dash_agencies', []), key='dash_agencies')
    with col_f3:
        sel_materials = st.multiselect("Material", options=materials, default=st.session_state.get('dash_materials', []), key='dash_materials')
        
    st.session_state["dashboard_filters"] = {
        "department": sel_depts,
        "agency": sel_agencies,
        "material": sel_materials
    }

    # Filter dataframe
    filtered_df = df.copy()
    if sel_depts:
        filtered_df = filtered_df[filtered_df['shop'].isin(sel_depts)]
    if sel_agencies:
        filtered_df = filtered_df[filtered_df['agency_code'].isin(sel_agencies)]
    if sel_materials:
        filtered_df = filtered_df[filtered_df['material'].isin(sel_materials)]
        
    if filtered_df.empty:
        st.warning("No records match the selected filters.")
        return

    # --- KPIs ---
    total_hours = filtered_df['durn'].sum()
    total_events = len(filtered_df)
    avg_delay_event = total_hours / total_events if total_events > 0 else 0
    
    dept_delays = filtered_df.groupby('shop')['durn'].sum().reset_index()
    worst_shop = dept_delays.sort_values(by='durn', ascending=False).iloc[0]['shop'] if not dept_delays.empty else "N/A"
    
    agency_delays = filtered_df.groupby('agency_code')['durn'].sum().reset_index()
    top_cause = agency_delays.sort_values(by='durn', ascending=False).iloc[0]['agency_code'] if not agency_delays.empty else "N/A"
    
    unique_days = filtered_df['delay_date'].nunique()
    avg_delay_day = total_hours / unique_days if unique_days > 0 else 0

    st.markdown("""
        <style>
        .kpi-row {
            display: flex;
            gap: 16px;
            margin-bottom: 32px;
        }
        .kpi-card {
            flex: 1;
            background: rgba(30, 41, 59, 0.7);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 16px;
            padding: 20px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            backdrop-filter: blur(10px);
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .kpi-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.2);
            border-color: rgba(255,255,255,0.15);
        }
        .kpi-title {
            font-size: 13px;
            color: #94A3B8;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .kpi-val {
            font-size: 28px;
            font-weight: 800;
            color: #F8FAFC;
        }
        .kpi-card.blue { border-top: 4px solid #3b82f6; }
        .kpi-card.orange { border-top: 4px solid #f97316; }
        .kpi-card.red { border-top: 4px solid #ef4444; }
        .kpi-card.yellow { border-top: 4px solid #f59e0b; }
        .kpi-card.green { border-top: 4px solid #22c55e; }
        
        .chart-title {
            font-size: 16px;
            font-weight: 600;
            color: #F8FAFC;
            margin-top: 24px;
            margin-bottom: 8px;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
        <div class="kpi-row">
            <div class="kpi-card blue">
                <div class="kpi-title">⏱️ Total Delay Hours</div>
                <div class="kpi-val">{total_hours:,.1f}</div>
            </div>
            <div class="kpi-card orange">
                <div class="kpi-title">⏳ Avg Delay / Event</div>
                <div class="kpi-val">{avg_delay_event:,.2f} h</div>
            </div>
            <div class="kpi-card red">
                <div class="kpi-title">🏭 Worst Shop</div>
                <div class="kpi-val">{worst_shop}</div>
            </div>
            <div class="kpi-card yellow">
                <div class="kpi-title">⚠️ Top Delay Cause</div>
                <div class="kpi-val">{top_cause}</div>
            </div>
            <div class="kpi-card green">
                <div class="kpi-title">📅 Avg Delay / Day</div>
                <div class="kpi-val">{avg_delay_day:,.1f} h</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    chart_config = {
        "paper_bgcolor": "#1E293B",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "font": {"color": "#94A3B8"},
        "margin": dict(l=10, r=10, t=40, b=10)
    }
    
    # ROW 1: Graph 1 & Graph 2
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="chart-title">Today\'s Delay Hours by Department</div>', unsafe_allow_html=True)
        df_g1 = filtered_df.groupby('shop').agg(durn=('durn', 'sum'), events=('id', 'count')).reset_index()
        top_causes = filtered_df.groupby(['shop', 'agency_code'])['durn'].sum().reset_index()
        top_causes = top_causes.sort_values('durn', ascending=False).drop_duplicates('shop')
        df_g1 = pd.merge(df_g1, top_causes[['shop', 'agency_code']], on='shop', how='left').rename(columns={'agency_code': 'Top Cause'})
        df_g1['Avg Delay/Event'] = df_g1['durn'] / df_g1['events']
        df_g1 = df_g1.sort_values('durn', ascending=True)
        
        def get_color(h):
            if h <= 2: return "#22C55E"
            if h <= 5: return "#F59E0B"
            if h <= 10: return "#F97316"
            return "#EF4444"
        df_g1['color'] = df_g1['durn'].apply(get_color)
        
        fig1 = px.bar(df_g1, x='durn', y='shop', orientation='h', 
                      custom_data=['events', 'Top Cause', 'Avg Delay/Event'],
                      color='color', color_discrete_map="identity")
        fig1.update_traces(hovertemplate="<b>%{y}</b><br>Delay Hours: %{x:.1f}<br>Events: %{customdata[0]}<br>Top Cause: %{customdata[1]}<br>Avg Delay: %{customdata[2]:.2f} h")
        fig1.update_layout(**chart_config, xaxis_title="Delay Hours", yaxis_title="Department")
        st.plotly_chart(fig1, use_container_width=True)

    with c2:
        st.markdown('<div class="chart-title">Delay Trend Throughout the Day</div>', unsafe_allow_html=True)
        df_g2 = filtered_df.dropna(subset=['hour']).groupby('hour')['durn'].sum().reset_index()
        all_hours = pd.DataFrame({'hour': range(24)})
        df_g2 = pd.merge(all_hours, df_g2, on='hour', how='left').fillna(0)
        
        fig2 = px.line(df_g2, x='hour', y='durn', markers=True, color_discrete_sequence=['#2563EB'])
        fig2.update_traces(fill='tozeroy', fillcolor='rgba(37, 99, 235, 0.1)')
        fig2.update_layout(**chart_config, xaxis_title="Hour of Day", yaxis_title="Delay Hours", xaxis=dict(tickmode='linear', tick0=0, dtick=1))
        st.plotly_chart(fig2, use_container_width=True)

    # ROW 2: Graph 3 & Graph 4
    c3, c4 = st.columns(2)
    with c3:
        st.markdown('<div class="chart-title">Pareto Analysis of Delay Causes</div>', unsafe_allow_html=True)
        df_g3 = filtered_df.groupby('agency_code')['durn'].sum().reset_index().sort_values('durn', ascending=False)
        df_g3['cum_pct'] = df_g3['durn'].cumsum() / df_g3['durn'].sum() * 100
        
        fig3 = go.Figure()
        fig3.add_trace(go.Bar(x=df_g3['agency_code'], y=df_g3['durn'], name="Delay Hours", marker_color="#3B82F6"))
        fig3.add_trace(go.Scatter(x=df_g3['agency_code'], y=df_g3['cum_pct'], name="Cumulative %", yaxis="y2", mode="lines+markers", marker_color="#F59E0B"))
        fig3.update_layout(**chart_config, yaxis=dict(title="Delay Hours"), yaxis2=dict(title="Cumulative %", overlaying="y", side="right", range=[0, 105]), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig3, use_container_width=True)

    with c4:
        st.markdown('<div class="chart-title">Delay Events by Shift</div>', unsafe_allow_html=True)
        df_g4 = filtered_df.groupby(['shift', 'agency_code']).size().reset_index(name='events')
        fig4 = px.bar(df_g4, x='shift', y='events', color='agency_code', 
                      category_orders={'shift': ['Morning', 'Evening', 'Night']},
                      color_discrete_sequence=px.colors.qualitative.Pastel)
        fig4.update_layout(**chart_config, xaxis_title="Shift", yaxis_title="Number of Delay Events", barmode='stack')
        st.plotly_chart(fig4, use_container_width=True)

    # ROW 3: Graph 5 & Graph 6
    c5, c6 = st.columns(2)
    with c5:
        st.markdown('<div class="chart-title">Shop vs Delay Cause Heatmap</div>', unsafe_allow_html=True)
        df_g5 = filtered_df.groupby(['shop', 'agency_code'])['durn'].sum().reset_index()
        fig5 = px.density_heatmap(df_g5, x='agency_code', y='shop', z='durn', color_continuous_scale="Blues", histfunc="sum")
        fig5.update_layout(**chart_config, xaxis_title="Delay Cause", yaxis_title="Department")
        st.plotly_chart(fig5, use_container_width=True)

    with c6:
        st.markdown('<div class="chart-title">Department Comparison</div>', unsafe_allow_html=True)
        df_g6 = filtered_df.groupby('shop').agg(durn=('durn', 'sum'), events=('id', 'count')).reset_index()
        df_g6['avg_delay'] = df_g6['durn'] / df_g6['events']
        df_g6 = df_g6.sort_values('durn', ascending=True)
        
        fig6 = go.Figure()
        fig6.add_trace(go.Bar(y=df_g6['shop'], x=df_g6['durn'], name="Total Delay Hours", orientation='h', marker_color="#3B82F6"))
        fig6.add_trace(go.Bar(y=df_g6['shop'], x=df_g6['events'], name="Total Events", orientation='h', marker_color="#10B981"))
        fig6.add_trace(go.Bar(y=df_g6['shop'], x=df_g6['avg_delay'], name="Avg Delay/Event", orientation='h', marker_color="#F59E0B"))
        
        fig6.update_layout(**chart_config, barmode='group', yaxis_title="Department", xaxis_title="Value", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig6, use_container_width=True)

    # ROW 4: Graph 7 & Graph 8
    c7, c8 = st.columns(2)
    with c7:
        st.markdown('<div class="chart-title">Delay Frequency Heatmap</div>', unsafe_allow_html=True)
        df_g7 = filtered_df.dropna(subset=['hour']).groupby([filtered_df['delay_date'].dt.date, 'hour']).size().reset_index(name='events')
        df_g7.rename(columns={'delay_date': 'Day'}, inplace=True)
        df_g7['Day'] = df_g7['Day'].astype(str)
        fig7 = px.density_heatmap(df_g7, x='hour', y='Day', z='events', color_continuous_scale=["#1E293B", "#3B82F6", "#F59E0B", "#EF4444"])
        fig7.update_layout(**chart_config, xaxis_title="Hour of Day", yaxis_title="Day")
        st.plotly_chart(fig7, use_container_width=True)

    with c8:
        st.markdown('<div class="chart-title">Equipment vs Agency Analysis</div>', unsafe_allow_html=True)
        df_g8 = filtered_df.groupby(['equipment_name', 'agency_code']).agg(durn=('durn', 'sum'), events=('id', 'count')).reset_index()
        eq_totals = df_g8.groupby('equipment_name')['durn'].sum().reset_index().sort_values('durn', ascending=True)
        top_eq = eq_totals.tail(15)['equipment_name']
        df_g8 = df_g8[df_g8['equipment_name'].isin(top_eq)]
        df_g8['avg'] = df_g8['durn'] / df_g8['events']
        
        fig8 = px.bar(df_g8, y='equipment_name', x='durn', color='agency_code', orientation='h', custom_data=['agency_code', 'events', 'avg'], color_discrete_sequence=px.colors.qualitative.Set3)
        fig8.update_traces(hovertemplate="<b>%{y}</b><br>Agency: %{customdata[0]}<br>Hours: %{x:.1f}<br>Events: %{customdata[1]}<br>Avg: %{customdata[2]:.2f} h")
        fig8.update_layout(**chart_config, xaxis_title="Total Delay Hours", yaxis_title="Equipment", barmode='stack', yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig8, use_container_width=True)

