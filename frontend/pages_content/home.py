"""
Home dashboard for Steel Plant Delay Analytics.

Displays high-level KPIs, department-wise analysis, equipment reliability,
agency distribution, material usage, and top delay reasons.

Components:
    - Hero banner with welcome message
    - 4 KPI cards: Total records, departments, equipment types, agencies
    - Department vs Equipment comparison charts
    - Agency and material distribution (pie chart & treemap)
    - Top 10 delay reasons ranking
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from pages_content.utils import api_request, render_hero_banner

def render():
    """
    Render the home dashboard with all KPI visualizations.
    
    Fetches data from /analytics/home-dashboard endpoint and displays
    charts. Handles empty data gracefully with info messages.
    """
    render_hero_banner()
    # ... rest of code