import streamlit as st
import pandas as pd
from pages_content.utils import api_request, render_hero_banner

def render():
    render_hero_banner()
    
    st.markdown('<h2 class="page-title">Dataset Overview</h2>', unsafe_allow_html=True)

    with st.spinner("Loading dataset..."):
        # Fetch data from backend
        response = api_request("GET", "/delays", params={"limit": 1000})
        
    if not response or not response.get("items"):
        st.info("No data available. Please upload a CSV to see the dataset overview.")
        return
    
    items = response.get("items", [])
    
    # Load into dataframe
    df = pd.DataFrame(items)
    
    # If the date doesn't have time, add it to match screenshot
    if "delay_date" in df.columns:
        df["delay_date"] = pd.to_datetime(df["delay_date"]).dt.strftime('%Y-%m-%d 00:00:00')
        
    # Rename columns to match screenshot exactly
    column_mapping = {
        "delay_date": "Delay Date",
        "shop_code": "Shop Code",
        "shop": "Shop",
        "from_time": "From",
        "upto_time": "Upto",
        "durn": "Durn",
        "equipment_name": "Eqpt",
        "sub_eqpt": "Sub Eqpt",
        "agency_code": "Agency",
        "descr": "Descr",
        "contd": "Contd",
        "material": "Material"
    }
    
    # Filter only mapped columns and rename them
    cols_to_keep = [c for c in column_mapping.keys() if c in df.columns]
    df = df[cols_to_keep].rename(columns=column_mapping)
    
    # Fill missing values with 'None' for display purposes (matching screenshot)
    df.fillna('None', inplace=True)
    
    # Custom styling for the dataframe to make it take full width
    st.markdown("""
        <style>
        /* Force dataframe to take full width */
        [data-testid="stDataFrame"] {
            width: 100%;
        }
        [data-testid="stDataFrame"] > div {
            width: 100%;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.dataframe(df, use_container_width=True, hide_index=True, height=600)

