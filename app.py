import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Page Configuration
st.set_page_config(page_title="SAF Department Dashboard", layout="wide")

# 2. Custom CSS Function to replicate the exact progress bars from your photos
def kpi_card(title, actual, target, unit, inverse=False):
    # Calculate achievement percentage safely
    if target > 0:
        pct = (actual / target) * 100
    else:
        pct = 100
        
    # Determine Status Color (Standard vs Inverse Logic like lower power is better)
    if inverse:
        is_good = pct <= 100
    else:
        is_good = pct >= 95
        
    color = "#22c55e" if is_good else "#ef4444" # Green vs Red
    pct_clamped = min(max(pct, 0), 100) # Keep progress bar between 0-100%
    
    # Custom HTML Container block
    html_code = f"""
    <div style="background-color: #1e293b; border-radius: 8px; padding: 16px; margin: 10px 0px; border-left: 5px solid {color};">
        <div style="color: #94a3b8; font-size: 12px; font-weight: bold; text-transform: uppercase; letter-spacing: 0.5px;">{title}</div>
        <div style="display: flex; justify-content: space-between; align-items: baseline; margin-top: 8px;">
            <div style="color: #f8fafc; font-size: 24px; font-weight: bold;">{actual:,.1f} <span style="font-size: 14px; color: #64748b;">{unit}</span></div>
            <div style="color: #94a3b8; font-size: 13px;">Target: {target:,.1f}</div>
        </div>
        <div style="background-color: #334155; border-radius: 4px; height: 8px; width: 100%; margin-top: 12px; overflow: hidden;">
            <div style="background-color: {color}; width: {pct_clamped}%; height: 100%; border-radius: 4px; transition: width 0.5s ease-in-out;"></div>
        </div>
        <div style="display: flex; justify-content: flex-end; margin-top: 8px;">
            <span style="background-color: rgba({ '34, 197, 94' if is_good else '239, 68, 68' }, 0.15); color: {color}; font-size: 13px; font-weight: bold; padding: 2px 8px; border-radius: 4px;">{pct:.1f}%</span>
        </div>
    </div>
    """
    return st.markdown(html_code, unsafe_allow_html=True)


# 3. Sidebar Navigation
st.sidebar.title("⚙️ SAF-II MIS")
menu = st.sidebar.radio(
    "Navigation",
    ["Dashboard Overview", "KPI Trends", "Monthly Analysis"]
)

# 4. Load Data Sheets
df_summary = pd.read_excel("MIS 26-27.xlsx", sheet_name="Summary", header=None)
df_timeline = pd.read_excel("MIS 26-27.xlsx", sheet_name="DATA_entry", skiprows=2)

# Clean and parse timeline columns
df_timeline.columns.values[0] = "Date"
df_timeline.columns.values[1] = "SAF1_Prod"
df_timeline.columns.values[4] = "Oprn_Delay"   
df_timeline.columns.values[5] = "Mech_Delay"   
df_timeline.columns.values[6] = "EI_Delay"     
df_timeline.columns.values[7] = "Mgmt_Delay"   
df_timeline.columns.values[35] = "SAF2_Prod"  

# Filter out empty dates or text aggregates
df_timeline = df_timeline[df_timeline['Date'].notna()]
df_timeline = df_timeline[df_timeline['Date'] != 'Total']
df_timeline['Date'] = pd.to_datetime(df_timeline['Date'])

# Ensure numeric values
df_timeline['SAF1_Prod'] = pd.to_numeric(df_timeline['SAF1_Prod'], errors='coerce').fillna(0)
df_timeline['SAF2_Prod'] = pd.to_numeric(df_timeline['SAF2_Prod'], errors='coerce').fillna(0)
df_timeline['Oprn_Delay'] = pd.to_numeric(df_timeline['Oprn_Delay'], errors='coerce').fillna(0)
df_timeline['Mech_Delay'] = pd.to_numeric(df_timeline['Mech_Delay'], errors='coerce').fillna(0)
df_timeline['EI_Delay'] = pd.to_numeric(df_timeline['EI_Delay'], errors='coerce').fillna(0)
df_timeline['Mgmt_Delay'] = pd.to_numeric(df_timeline['Mgmt_Delay'], errors='coerce').fillna(0)

# Filter for production timeline entries
df_filtered = df_timeline[(df_timeline['SAF1_Prod'] > 0) & (df_timeline['SAF2_Prod'] > 0)]
df_filtered['Total_Production'] = df_filtered['SAF1_Prod'] + df_filtered['SAF2_Prod']


# 5. Navigation Control
if menu == "Dashboard Overview":
    st.title("🖥️ Target vs Actual Performance")
    st.write("Last 7 Days Operational Status Matrix")
    st.markdown("---")
    
    # Extract dynamic production data from Summary sheet
    target_prod = float(df_summary.iloc[3, 7])   
    actual_prod = float(df_summary.iloc[3, 8])   
    
    # Extract operational efficiency targets and actual parameters
    total_power = float(df_summary.iloc[28, 5])
    spec_power = float(df_summary.iloc[28, 6])
    total_fuel = float(df_summary.iloc[24, 5])
    spec_fuel = float(df_summary.iloc[24, 6])

    # --- ROW 1: CORE INDICES GRID (3 COLUMN CARDS) ---
    col1, col2, col3 = st.columns(3)
    
    with col1:
        kpi_card("Daily Producer Gas Production", actual_prod, target_prod, "Nm³/Day")
    with col2:
        kpi_card("Hourly Producer Gas Rate", actual_prod / 24, target_prod / 24, "Nm³/Hr")
    with col3:
        kpi_card("Net Coal Consumption", total_fuel, 185.0, "MT/Day")

    st.markdown("<br>", unsafe_allow_html=True)

    # --- ROW 2: SPECIFIC INDUSTRIAL TARGET INDEX CARDS ---
    col_a, col_b, col_c = st.columns(3)
    
    with col_a:
        kpi_card("Specific Coal Consumption", spec_fuel, 0.62, "Kg/Nm³", inverse=True)
    with col_b:
        kpi_card("Electric Power Consumption", total_power, 8500.0, "KWH", inverse=True)
    with col_c:
        kpi_card("Number of Gasifiers Running", 5.0, 5.0, "Nos.")

elif menu == "KPI Trends":
    st.title("📈 Operational Performance & Delay Analytics")
    st.markdown("---")
    
    st.subheader("Daily Individual Furnace Performance Trends")
    fig_prod = px.line(
        df_filtered,
        x="Date",
        y=["SAF1_Prod", "SAF2_Prod", "Total_Production"],
        labels={"value": "Production Yield (MT)", "variable": "Furnace Unit"},
        template="plotly_dark",
        color_discrete_map={"SAF1_Prod": "#00f2fe", "SAF2_Prod": "#ff9f43", "Total_Production": "#ffffff"}
    )
    fig_prod.update_traces(line_width=3)
    fig_prod.update_layout(hovermode="x unified", plot_bgcolor="#0f172a", paper_bgcolor="rgba(0,0,0,0)", margin=dict(l=20, r=20, t=30, b=20))
    st.plotly_chart(fig_prod, use_container_width=True)
    
    st.markdown("---")
    
    st.subheader("⚠️ Furnace Downtime & Delay Log (Hours Lost)")
    fig_delay = px.bar(
        df_filtered,
        x="Date",
        y=["Oprn_Delay", "Mech_Delay", "EI_Delay", "Mgmt_Delay"],
        labels={"value": "Downtime (Hours)", "variable": "Delay Category"},
        template="plotly_dark",
        color_discrete_map={"Oprn_Delay": "#a855f7", "Mech_Delay": "#ef4444", "EI_Delay": "#3b82f6", "Mgmt_Delay": "#6b7280"}
    )
    fig_delay.update_layout(barmode="stack", hovermode="x unified", plot_bgcolor="#0f172a", paper_bgcolor="rgba(0,0,0,0)", margin=dict(l=20, r=20, t=50, b=20), legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="center", x=0.5))
    st.plotly_chart(fig_delay, use_container_width=True)

elif menu == "Monthly Analysis":
    st.title("📅 Monthly Analysis")
    st.write("This section will compare month-on-month targets.")