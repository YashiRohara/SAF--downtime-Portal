import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
from datetime import datetime

# 1. Page Configuration
st.set_page_config(page_title="SAF Department Dashboard", layout="wide")

# 2. Database Initialization
def init_db():
    conn = sqlite3.connect("saf_production.db")
    cursor = conn.cursor()
    # FIXED: String literal perfectly formatted and terminated here
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS saf_daily_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_date DATE UNIQUE,
            saf1_prod REAL,
            saf2_prod REAL,
            oprn_delay REAL,
            mech_delay REAL,
            ei_delay REAL,
            mgmt_delay REAL
        )
    """)
    conn.commit()
    conn.close()

init_db()

# Helper function to push data to Database
def insert_or_replace_entry(date, saf1, saf2, oprn, mech, ei, mgmt):
    conn = sqlite3.connect("saf_production.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO saf_daily_entries (entry_date, saf1_prod, saf2_prod, oprn_delay, mech_delay, ei_delay, mgmt_delay)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(entry_date) DO UPDATE SET
            saf1_prod=excluded.saf1_prod,
            saf2_prod=excluded.saf2_prod,
            oprn_delay=excluded.oprn_delay,
            mech_delay=excluded.mech_delay,
            ei_delay=excluded.ei_delay,
            mgmt_delay=excluded.mgmt_delay
    """, (date, saf1, saf2, oprn, mech, ei, mgmt))
    conn.commit()
    conn.close()

# 3. Sidebar Navigation
st.sidebar.title("⚙️ SAF-II MIS Portal")
menu = st.sidebar.radio(
    "Navigation",
    ["Dashboard Overview", "KPI Trends", "Manual Data Entry", "Bulk Data Upload"]
)

# Load Static Summary targets from baseline excel
df_summary = pd.read_excel("MIS 26-27.xlsx", sheet_name="Summary", header=None)

# Load Data from Database
conn = sqlite3.connect("saf_production.db")
df_timeline = pd.read_sql_query("SELECT * FROM saf_daily_entries", conn)
conn.close()

# Parse Dates for Plots
if not df_timeline.empty:
    df_timeline['entry_date'] = pd.to_datetime(df_timeline['entry_date'])
    df_filtered = df_timeline[(df_timeline['saf1_prod'] > 0) & (df_timeline['saf2_prod'] > 0)]
    if not df_filtered.empty:
        df_filtered['Total_Production'] = df_filtered['saf1_prod'] + df_filtered['saf2_prod']

# Custom CSS for KPI Cards
def kpi_card(title, actual, target, unit, inverse=False):
    pct = (actual / target) * 100 if target > 0 else 100
    is_good = pct <= 100 if inverse else pct >= 95
    color = "#22c55e" if is_good else "#ef4444"
    pct_clamped = min(max(pct, 0), 100)
    
    html_code = f"""
    <div style="background-color: #1e293b; border-radius: 8px; padding: 16px; margin: 10px 0px; border-left: 5px solid {color};">
        <div style="color: #94a3b8; font-size: 12px; font-weight: bold; text-transform: uppercase;">{title}</div>
        <div style="display: flex; justify-content: space-between; align-items: baseline; margin-top: 8px;">
            <div style="color: #f8fafc; font-size: 24px; font-weight: bold;">{actual:,.1f} <span style="font-size: 14px; color: #64748b;">{unit}</span></div>
            <div style="color: #94a3b8; font-size: 13px;">Target: {target:,.1f}</div>
        </div>
        <div style="background-color: #334155; border-radius: 4px; height: 8px; width: 100%; margin-top: 12px; overflow: hidden;">
            <div style="background-color: {color}; width: {pct_clamped}%; height: 100%; border-radius: 4px;"></div>
        </div>
        <div style="display: flex; justify-content: flex-end; margin-top: 8px;">
            <span style="background-color: rgba({ '34, 197, 94' if is_good else '239, 68, 68' }, 0.15); color: {color}; font-size: 13px; font-weight: bold; padding: 2px 8px; border-radius: 4px;">{pct:.1f}%</span>
        </div>
    </div>
    """
    return st.markdown(html_code, unsafe_allow_html=True)


# --- ROUTING ---

if menu == "Dashboard Overview":
    st.title("🖥️ Target vs Actual Performance")
    st.markdown("---")
    
    target_prod = float(df_summary.iloc[3, 7])   
    actual_prod = float(df_summary.iloc[3, 8])   
    total_power = float(df_summary.iloc[28, 5])
    total_fuel = float(df_summary.iloc[24, 5])

    col1, col2, col3 = st.columns(3)
    with col1:
        kpi_card("Daily Producer Gas Production", actual_prod, target_prod, "Nm³/Day")
    with col2:
        kpi_card("Hourly Producer Gas Rate", actual_prod / 24, target_prod / 24, "Nm³/Hr")
    with col3:
        kpi_card("Net Coal Consumption", total_fuel, 185.0, "MT/Day")

elif menu == "KPI Trends":
    st.title("📈 Operational Performance & Delay Analytics")
    st.markdown("---")
    
    if df_timeline.empty or 'df_filtered' not in locals() or df_filtered.empty:
        st.warning("⚠️ Database abhi khali hai. Kripya pehle data entry ya Excel bulk upload kijiye!")
    else:
        st.subheader("Daily Individual Furnace Performance Trends")
        fig_prod = px.line(
            df_filtered, x="entry_date", y=["saf1_prod", "saf2_prod", "Total_Production"],
            labels={"value": "Production Yield (MT)", "variable": "Furnace Unit"},
            template="plotly_dark",
            color_discrete_map={"saf1_prod": "#00f2fe", "saf2_prod": "#ff9f43", "Total_Production": "#ffffff"}
        )
        st.plotly_chart(fig_prod, use_container_width=True)
        
        st.markdown("---")
        st.subheader("⚠️ Furnace Downtime & Delay Log (Hours Lost)")
        fig_delay = px.bar(
            df_filtered, x="entry_date", y=["oprn_delay", "mech_delay", "ei_delay", "mgmt_delay"],
            labels={"value": "Downtime (Hours)", "variable": "Delay Category"},
            template="plotly_dark",
            color_discrete_map={"oprn_delay": "#a855f7", "mech_delay": "#ef4444", "ei_delay": "#3b82f6", "mgmt_delay": "#6b7280"}
        )
        fig_delay.update_layout(barmode="stack")
        st.plotly_chart(fig_delay, use_container_width=True)

elif menu == "Manual Data Entry":
    st.title("📝 Manual Shift Data Input Form")
    st.write("Is form ke zariye operators daily furnace production parameters DB mein lock kar sakte hain.")
    st.markdown("---")
    
    with st.form("entry_form", clear_on_submit=True):
        log_date = st.date_input("Operational Logging Date", datetime.now())
        
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            s1_prod = st.number_input("SAF #1 Production (MT)", min_value=0.0, step=0.1)
        with col_p2:
            s2_prod = st.number_input("SAF #2 Production (MT)", min_value=0.0, step=0.1)
            
        st.markdown("##### Breakdown & Delay Hours Log")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            o_del = st.number_input("Operational Delay (Hrs)", min_value=0.0, max_value=24.0, step=0.5)
        with c2:
            m_del = st.number_input("Mechanical Delay (Hrs)", min_value=0.0, max_value=24.0, step=0.5)
        with c3:
            e_del = st.number_input("Electrical (E&I) Delay (Hrs)", min_value=0.0, max_value=24.0, step=0.5)
        with c4:
            mg_del = st.number_input("Management Delay (Hrs)", min_value=0.0, max_value=24.0, step=0.5)
            
        submit_btn = st.form_submit_button("🔐 Lock Data into Database")
        
        if submit_btn:
            insert_or_replace_entry(str(log_date), s1_prod, s2_prod, o_del, m_del, e_del, mg_del)
            st.success(f"✔️ Perfect! {log_date} ka data database mein secure tarike se save ho gaya hai.")

elif menu == "Bulk Data Upload":
    st.title("📤 Bulk Data Upload (Direct MIS Excel Integration)")
    st.write("Apni original 'MIS 26-27.xlsx' file yahan upload kijiye. System 'DATA_entry' sheet se data automatic extract kar lega.")
    st.markdown("---")
    
    uploaded_file = st.file_uploader("Upload Excel Template", type=["xlsx"])
    if uploaded_file is not None:
        try:
            # 1. Direct DATA_entry sheet ko read kiya aur top headers skip kiye
            df_bulk = pd.read_excel(uploaded_file, sheet_name="DATA_entry", skiprows=2)
            
            # 2. Columns ko wese hi map kiya jaise humne pehle kiya tha
            df_bulk.columns.values[0] = "Date"
            df_bulk.columns.values[1] = "SAF1_Prod"
            df_bulk.columns.values[4] = "Oprn_Delay"   
            df_bulk.columns.values[5] = "Mech_Delay"   
            df_bulk.columns.values[6] = "EI_Delay"     
            df_bulk.columns.values[7] = "Mgmt_Delay"   
            df_bulk.columns.values[35] = "SAF2_Prod"  
            
            # 3. Clean and filter out totals/empty rows
            df_bulk = df_bulk[df_bulk["Date"].notna()]
            df_bulk = df_bulk[df_bulk["Date"] != "Total"]
            
            success_count = 0
            
            # 4. Loop chalakar database me safe entry lock ki
            for index, row in df_bulk.iterrows():
                try:
                    formatted_date = pd.to_datetime(row["Date"]).strftime('%Y-%m-%d')
                    s1 = pd.to_numeric(row["SAF1_Prod"], errors='coerce')
                    s2 = pd.to_numeric(row["SAF2_Prod"], errors='coerce')
                    
                    # Agar valid production data hai tabhi insert karein
                    if pd.notna(s1) or pd.notna(s2):
                        insert_or_replace_entry(
                            str(formatted_date), 
                            float(s1) if pd.notna(s1) else 0.0, 
                            float(s2) if pd.notna(s2) else 0.0,
                            float(pd.to_numeric(row["Oprn_Delay"], errors='coerce')) if pd.notna(row["Oprn_Delay"]) else 0.0, 
                            float(pd.to_numeric(row["Mech_Delay"], errors='coerce')) if pd.notna(row["Mech_Delay"]) else 0.0, 
                            float(pd.to_numeric(row["EI_Delay"], errors='coerce')) if pd.notna(row["EI_Delay"]) else 0.0, 
                            float(pd.to_numeric(row["Mgmt_Delay"], errors='coerce')) if pd.notna(row["Mgmt_Delay"]) else 0.0
                        )
                        success_count += 1
                except:
                    continue # Agar koi row corrupt ho toh drop karke aage badein
                    
            if success_count > 0:
                st.success(f"🚀 Perfect! Original Excel se {success_count} din ka data database me successfully process ho gaya hai!")
            else:
                st.error("❌ File me koi valid operational data nahi mila.")
                
        except Exception as e:
            st.error(f"Error processing Excel file: {e}")
    