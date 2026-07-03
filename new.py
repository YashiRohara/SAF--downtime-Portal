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

# 3. Session state init — this is our "dynamic file" variable
if "uploaded_excel_name" not in st.session_state:
    st.session_state["uploaded_excel_name"] = None
if "df_summary" not in st.session_state:
    st.session_state["df_summary"] = None
if "df_raw_material" not in st.session_state:
    st.session_state["df_raw_material"] = None
if "df_delay_report" not in st.session_state:
    st.session_state["df_delay_report"] = None
if "df_simn_despatch" not in st.session_state:
    st.session_state["df_simn_despatch"] = None

# 3. Sidebar Navigation
st.sidebar.title("⚙️ SAF-II MIS Portal")
menu = st.sidebar.radio(
    "Navigation",
    [
        "Dashboard Overview",
        "KPI Trends",
        "Raw Material Stock",
        "Delay Reasons",
        "Despatch Trends",
        "Monthly Targets",
        "Consumption & Efficiency",
        "Despatch & Stock Insights",
        "Manual Data Entry",
        "Bulk Data Upload",
    ]
)

if st.session_state["uploaded_excel_name"]:
    st.sidebar.success(f"📂 Active File: {st.session_state['uploaded_excel_name']}")
else:
    st.sidebar.warning("⚠️ No file has been uploaded yet")

# Load Data from Database (fresh every time, since DB is persistent)
conn = sqlite3.connect("saf_production.db")
df_timeline = pd.read_sql_query("SELECT * FROM saf_daily_entries", conn)
conn.close()

# Parse Dates for Plots
df_filtered = pd.DataFrame()
if not df_timeline.empty:
    df_timeline['entry_date'] = pd.to_datetime(df_timeline['entry_date'])
    df_filtered = df_timeline[(df_timeline['saf1_prod'] > 0) & (df_timeline['saf2_prod'] > 0)].copy()
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

    if st.session_state["df_summary"] is None:
        st.warning("⚠️ Please upload your Excel file from the 'Bulk Data Upload' tab first, so the Dashboard can pull data from it.")
    else:
        df_summary = st.session_state["df_summary"]

        # --- Alerts / Attention Needed panel ---
        alerts = []
        try:
            if st.session_state["df_raw_material"] is not None:
                df_rm_alert = st.session_state["df_raw_material"]
                for r in [2, 3, 5, 6]:
                    name = df_rm_alert.iloc[r, 0]
                    cov = pd.to_numeric(df_rm_alert.iloc[r, 6], errors='coerce')
                    if pd.notna(name) and pd.notna(cov) and cov < 10:
                        alerts.append(f"🟥 {name}: only {cov:.1f} days of stock coverage left")
        except Exception:
            pass

        try:
            if not df_filtered.empty:
                recent = df_filtered.sort_values("entry_date").tail(5)
                for _, r in recent.iterrows():
                    total_delay = r["oprn_delay"] + r["mech_delay"] + r["ei_delay"] + r["mgmt_delay"]
                    if total_delay > 5:
                        alerts.append(f"🟧 {r['entry_date'].strftime('%Y-%m-%d')}: {total_delay:.1f} hrs of total delay")
        except Exception:
            pass

        if alerts:
            st.markdown("##### ⚠️ Attention Needed")
            for a in alerts:
                st.markdown(f"- {a}")
            st.markdown("---")

        try:
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

            st.markdown("---")
            st.subheader("📅 Year-to-Date Progress (Total SAF Production)")
            ytd_rows = [
                ("On Date", 3),
                ("Month Cumulative", 4),
                ("Year to Date", 5),
            ]
            ytd_cols = st.columns(3)
            for (label, r), c in zip(ytd_rows, ytd_cols):
                with c:
                    t = pd.to_numeric(df_summary.iloc[r, 7], errors='coerce')
                    a = pd.to_numeric(df_summary.iloc[r, 8], errors='coerce')
                    if pd.notna(t) and pd.notna(a):
                        kpi_card(label, float(a), float(t), "Tons")
        except Exception as e:
            st.error(f"Error occurred while reading data from Summary sheet: {e}")


elif menu == "KPI Trends":
    st.title("📈 Operational Performance & Delay Analytics")
    st.markdown("---")

    if df_timeline.empty or df_filtered.empty:
        st.warning("⚠️ The database is currently empty. Please add data entries or upload an Excel file in bulk first!")
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

        st.markdown("---")
        st.subheader("🥧 Total Delay Distribution (Pie Chart)")
        delay_totals = {
            "Operational Delay": df_filtered["oprn_delay"].sum(),
            "Mechanical Delay": df_filtered["mech_delay"].sum(),
            "E&I Delay": df_filtered["ei_delay"].sum(),
            "Management Delay": df_filtered["mgmt_delay"].sum(),
        }
        pie_df = pd.DataFrame({"Delay Type": delay_totals.keys(), "Hours": delay_totals.values()})
        pie_df = pie_df[pie_df["Hours"] > 0]
        if not pie_df.empty:
            fig_pie = px.pie(
                pie_df, names="Delay Type", values="Hours",
                template="plotly_dark", hole=0.4,
                color="Delay Type",
                color_discrete_map={
                    "Operational Delay": "#a855f7",
                    "Mechanical Delay": "#ef4444",
                    "E&I Delay": "#3b82f6",
                    "Management Delay": "#6b7280"
                }
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("No delay data is available for the pie chart.")

elif menu == "Raw Material Stock":
    st.title("🧱 Raw Material Stock & Coverage")
    st.markdown("---")

    if st.session_state["df_raw_material"] is None:
        st.warning("⚠️ Please upload your Excel file from the 'Bulk Data Upload' tab first.")
    else:
        df_rm = st.session_state["df_raw_material"]
        try:
            # Rows 2-6 hold the material-wise stock table in the source sheet
            materials = []
            for r in [2, 3, 5, 6]:
                name = df_rm.iloc[r, 0]
                plant_stock = pd.to_numeric(df_rm.iloc[r, 1], errors='coerce')
                port_stock = pd.to_numeric(df_rm.iloc[r, 2], errors='coerce')
                total_stock = pd.to_numeric(df_rm.iloc[r, 3], errors='coerce')
                coverage_days = pd.to_numeric(df_rm.iloc[r, 6], errors='coerce')
                if pd.notna(name) and pd.notna(total_stock):
                    materials.append({
                        "Material": name,
                        "At Plant (T)": plant_stock if pd.notna(plant_stock) else 0,
                        "At Port (T)": port_stock if pd.notna(port_stock) else 0,
                        "Total (T)": total_stock,
                        "Coverage (Days)": coverage_days if pd.notna(coverage_days) else None
                    })
            mat_df = pd.DataFrame(materials)

            if mat_df.empty:
                st.info("Raw material stock data not found in this file.")
            else:
                st.subheader("Material-wise Stock Table")
                st.dataframe(mat_df, use_container_width=True, hide_index=True)

                st.markdown("---")
                st.subheader("📊 Stock Coverage (Days Remaining)")
                cov_df = mat_df.dropna(subset=["Coverage (Days)"])
                if not cov_df.empty:
                    for _, row in cov_df.iterrows():
                        days = row["Coverage (Days)"]
                        color = "#ef4444" if days < 10 else ("#f59e0b" if days < 20 else "#22c55e")
                        pct = min(max((days / 30) * 100, 0), 100)
                        st.markdown(f"""
                        <div style="margin-bottom: 14px;">
                            <div style="display:flex; justify-content:space-between; color:#cbd5e1; font-size:14px;">
                                <span>{row['Material']}</span><span>{days:.1f} days</span>
                            </div>
                            <div style="background-color:#334155; border-radius:4px; height:10px; width:100%; overflow:hidden;">
                                <div style="background-color:{color}; width:{pct}%; height:100%; border-radius:4px;"></div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("Coverage day data not available for these materials.")

                st.markdown("---")
                st.subheader("🥧 Plant vs Port Stock Split")
                fig_rm = px.bar(
                    mat_df, x="Material", y=["At Plant (T)", "At Port (T)"],
                    barmode="stack", template="plotly_dark",
                    labels={"value": "Stock (Tons)", "variable": "Location"}
                )
                st.plotly_chart(fig_rm, use_container_width=True)
        except Exception as e:
            st.error(f"Error reading raw material data: {e}")

elif menu == "Delay Reasons":
    st.title("🛑 Top Delay Reasons")
    st.markdown("---")

    if st.session_state["df_delay_report"] is None:
        st.warning("⚠️ Please upload your Excel file from the 'Bulk Data Upload' tab first.")
    else:
        df_dr = st.session_state["df_delay_report"]
        try:
            data_rows = df_dr.iloc[4:].copy()
            data_rows = data_rows[pd.to_datetime(data_rows[0], errors='coerce').notna()]

            reasons = []
            for _, row in data_rows.iterrows():
                r1 = row[6]
                h1 = pd.to_numeric(row[5], errors='coerce')
                if isinstance(r1, str) and r1.strip() not in ("", "0") and pd.notna(h1) and h1 > 0:
                    reasons.append({"Reason": r1.strip(), "Hours": h1, "Furnace": "SAF #1"})

                r2 = row[12]
                h2 = pd.to_numeric(row[11], errors='coerce')
                if isinstance(r2, str) and r2.strip() not in ("", "0") and pd.notna(h2) and h2 > 0:
                    reasons.append({"Reason": r2.strip(), "Hours": h2, "Furnace": "SAF #2"})

            if not reasons:
                st.info("No delay reasons found in this file.")
            else:
                reasons_df = pd.DataFrame(reasons)
                top_df = reasons_df.groupby("Reason", as_index=False)["Hours"].sum().sort_values("Hours", ascending=False).head(15)

                st.subheader("Top 15 Delay Reasons (Total Hours Lost)")
                fig_reasons = px.bar(
                    top_df.sort_values("Hours"), x="Hours", y="Reason", orientation="h",
                    template="plotly_dark", color="Hours", color_continuous_scale="Reds"
                )
                fig_reasons.update_layout(height=550)
                st.plotly_chart(fig_reasons, use_container_width=True)

                st.markdown("---")
                st.subheader("Furnace-wise Delay Hours")
                furnace_split = reasons_df.groupby("Furnace", as_index=False)["Hours"].sum()
                fig_furnace = px.pie(
                    furnace_split, names="Furnace", values="Hours",
                    template="plotly_dark", hole=0.4
                )
                st.plotly_chart(fig_furnace, use_container_width=True)

                st.markdown("---")
                st.subheader("Detailed Reason Log")
                st.dataframe(reasons_df.sort_values("Hours", ascending=False), use_container_width=True, hide_index=True)
        except Exception as e:
            st.error(f"Error reading delay report data: {e}")

elif menu == "Despatch Trends":
    st.title("🚚 SiMn Despatch Trends")
    st.markdown("---")

    if st.session_state["df_simn_despatch"] is None:
        st.warning("⚠️ Please upload your Excel file from the 'Bulk Data Upload' tab first.")
    else:
        df_sd = st.session_state["df_simn_despatch"]
        try:
            data_rows = df_sd.iloc[3:].copy()
            data_rows = data_rows[pd.to_datetime(data_rows[0], errors='coerce').notna()]

            despatch_df = pd.DataFrame({
                "Date": pd.to_datetime(data_rows[0]),
                "SMS-2": pd.to_numeric(data_rows[4], errors='coerce').fillna(0),
                "SMS-3": pd.to_numeric(data_rows[8], errors='coerce').fillna(0),
                "Angul": pd.to_numeric(data_rows[12], errors='coerce').fillna(0),
                "Nalwa": pd.to_numeric(data_rows[16], errors='coerce').fillna(0),
            })
            despatch_df = despatch_df.sort_values("Date")
            despatch_df["Total"] = despatch_df[["SMS-2", "SMS-3", "Angul", "Nalwa"]].sum(axis=1)

            st.subheader("Daily Despatch by Location (Tons)")
            fig_despatch = px.line(
                despatch_df, x="Date", y=["SMS-2", "SMS-3", "Angul", "Nalwa", "Total"],
                template="plotly_dark",
                labels={"value": "Despatch (Tons)", "variable": "Location"}
            )
            st.plotly_chart(fig_despatch, use_container_width=True)

            st.markdown("---")
            st.subheader("🥧 Total Despatch Share by Location")
            location_totals = despatch_df[["SMS-2", "SMS-3", "Angul", "Nalwa"]].sum().reset_index()
            location_totals.columns = ["Location", "Total Tons"]
            location_totals = location_totals[location_totals["Total Tons"] > 0]
            if not location_totals.empty:
                fig_loc_pie = px.pie(
                    location_totals, names="Location", values="Total Tons",
                    template="plotly_dark", hole=0.4
                )
                st.plotly_chart(fig_loc_pie, use_container_width=True)
        except Exception as e:
            st.error(f"Error reading despatch data: {e}")

elif menu == "Monthly Targets":
    st.title("🎯 Monthly ABP vs Actual Production")
    st.markdown("---")

    if st.session_state["df_summary"] is None:
        st.warning("⚠️ Please upload your Excel file from the 'Bulk Data Upload' tab first.")
    else:
        df_summary = st.session_state["df_summary"]
        try:
            months = df_summary.iloc[31, 1:13].tolist()
            saf_abp = pd.to_numeric(df_summary.iloc[34, 1:13], errors='coerce').tolist()
            actual_total = pd.to_numeric(df_summary.iloc[38, 1:13], errors='coerce').tolist()
            target_pct = pd.to_numeric(df_summary.iloc[39, 1:13], errors='coerce').tolist()

            monthly_df = pd.DataFrame({
                "Month": months,
                "ABP Target": saf_abp,
                "Actual Production": actual_total,
            })
            monthly_df = monthly_df[monthly_df["ABP Target"].notna()]

            st.subheader("Monthly Target vs Actual Production (Tons)")
            fig_monthly = px.bar(
                monthly_df, x="Month", y=["ABP Target", "Actual Production"],
                barmode="group", template="plotly_dark",
                labels={"value": "Production (Tons)", "variable": "Type"},
                color_discrete_map={"ABP Target": "#64748b", "Actual Production": "#22c55e"}
            )
            st.plotly_chart(fig_monthly, use_container_width=True)

            st.markdown("---")
            st.subheader("Target Achievement % by Month")
            achv_df = pd.DataFrame({"Month": months, "Achieved %": [p * 100 if pd.notna(p) else None for p in target_pct]})
            achv_df = achv_df[achv_df["Achieved %"].notna()]
            if not achv_df.empty:
                fig_achv = px.line(
                    achv_df, x="Month", y="Achieved %", markers=True,
                    template="plotly_dark"
                )
                fig_achv.add_hline(y=100, line_dash="dash", line_color="#94a3b8")
                st.plotly_chart(fig_achv, use_container_width=True)
        except Exception as e:
            st.error(f"Error reading monthly target data: {e}")

elif menu == "Consumption & Efficiency":
    st.title("⚡ Raw Material Consumption & Power Efficiency")
    st.markdown("---")

    if st.session_state["df_summary"] is None:
        st.warning("⚠️ Please upload your Excel file from the 'Bulk Data Upload' tab first.")
    else:
        df_summary = st.session_state["df_summary"]
        try:
            st.subheader("🔥 Specific Consumption Rate: SAF #1 vs SAF #2 (Tons used per Ton produced)")
            rows_map = [
                ("Mn ore (High Gr)", 17), ("Mn ore (Low Gr)", 18),
                ("Nut Coke", 21), ("VT Coal", 22), ("Dryer Coal", 23),
                ("Raw Coal", 24), ("Quartz", 26), ("Paste", 28),
            ]
            cons_data = []
            for name, r in rows_map:
                saf1_sp = pd.to_numeric(df_summary.iloc[r, 2], errors='coerce')
                saf2_sp = pd.to_numeric(df_summary.iloc[r, 4], errors='coerce')
                cons_data.append({"Material": name, "SAF #1 (T/T)": saf1_sp, "SAF #2 (T/T)": saf2_sp})
            cons_df = pd.DataFrame(cons_data)

            fig_cons = px.bar(
                cons_df, x="Material", y=["SAF #1 (T/T)", "SAF #2 (T/T)"],
                barmode="group", template="plotly_dark",
                labels={"value": "Specific Consumption (T/T)", "variable": "Furnace"},
                color_discrete_map={"SAF #1 (T/T)": "#00f2fe", "SAF #2 (T/T)": "#ff9f43"}
            )
            st.plotly_chart(fig_cons, use_container_width=True)

            st.markdown("---")
            st.subheader("⚡ Power Consumption")
            saf1_power = pd.to_numeric(df_summary.iloc[29, 1], errors='coerce')
            saf1_power_sp = pd.to_numeric(df_summary.iloc[29, 2], errors='coerce')
            saf2_power = pd.to_numeric(df_summary.iloc[29, 3], errors='coerce')
            saf2_power_sp = pd.to_numeric(df_summary.iloc[29, 4], errors='coerce')
            total_power = pd.to_numeric(df_summary.iloc[29, 5], errors='coerce')
            total_power_sp = pd.to_numeric(df_summary.iloc[29, 6], errors='coerce')

            pc1, pc2, pc3 = st.columns(3)
            with pc1:
                st.metric("SAF #1 Power Used", f"{saf1_power:,.1f} MWH", f"{saf1_power_sp:.2f} MWH/T")
            with pc2:
                st.metric("SAF #2 Power Used", f"{saf2_power:,.1f} MWH", f"{saf2_power_sp:.2f} MWH/T")
            with pc3:
                st.metric("Total Power Used", f"{total_power:,.1f} MWH", f"{total_power_sp:.2f} MWH/T")

            st.markdown("---")
            st.subheader("📦 Raw Material Quantity Used (SAF #1 vs SAF #2)")
            qty_data = []
            for name, r in rows_map:
                saf1_qty = pd.to_numeric(df_summary.iloc[r, 1], errors='coerce')
                saf2_qty = pd.to_numeric(df_summary.iloc[r, 3], errors='coerce')
                qty_data.append({"Material": name, "SAF #1 (T)": saf1_qty, "SAF #2 (T)": saf2_qty})
            qty_df = pd.DataFrame(qty_data)
            fig_qty = px.bar(
                qty_df, x="Material", y=["SAF #1 (T)", "SAF #2 (T)"],
                barmode="stack", template="plotly_dark",
                labels={"value": "Quantity Used (Tons)", "variable": "Furnace"}
            )
            st.plotly_chart(fig_qty, use_container_width=True)
        except Exception as e:
            st.error(f"Error reading consumption data: {e}")

elif menu == "Despatch & Stock Insights":
    st.title("📦 Despatch History & Product Stock Insights")
    st.markdown("---")

    if st.session_state["df_summary"] is None:
        st.warning("⚠️ Please upload your Excel file from the 'Bulk Data Upload' tab first.")
    else:
        df_summary = st.session_state["df_summary"]
        try:
            st.subheader("📈 Year-on-Year Despatch Comparison")
            yoy_rows = [10, 11, 12, 13]
            yoy_data = []
            for r in yoy_rows:
                year_label = df_summary.iloc[r, 0]
                sms = pd.to_numeric(df_summary.iloc[r, 1], errors='coerce')
                angul_nalwa = pd.to_numeric(df_summary.iloc[r, 2], errors='coerce')
                total = pd.to_numeric(df_summary.iloc[r, 3], errors='coerce')
                yoy_data.append({"Year": year_label, "SMS": sms, "Angul & Nalwa": angul_nalwa, "Total": total})
            yoy_df = pd.DataFrame(yoy_data)

            fig_yoy = px.bar(
                yoy_df, x="Year", y=["SMS", "Angul & Nalwa"],
                barmode="stack", template="plotly_dark",
                labels={"value": "Despatch (Tons)", "variable": "Destination"}
            )
            st.plotly_chart(fig_yoy, use_container_width=True)

            st.markdown("---")
            st.subheader("🥧 SiMn Product Stock by Grade")
            grade_rows = [8, 9, 10]
            grade_data = []
            for r in grade_rows:
                grade = df_summary.iloc[r, 4]
                total = pd.to_numeric(df_summary.iloc[r, 8], errors='coerce')
                if pd.notna(grade) and pd.notna(total):
                    grade_data.append({"Grade": grade, "Stock (T)": total})
            grade_df = pd.DataFrame(grade_data)
            grade_df = grade_df[grade_df["Stock (T)"] > 0]

            colA, colB = st.columns(2)
            with colA:
                if not grade_df.empty:
                    fig_grade = px.pie(
                        grade_df, names="Grade", values="Stock (T)",
                        template="plotly_dark", hole=0.4
                    )
                    st.plotly_chart(fig_grade, use_container_width=True)
                else:
                    st.info("No grade-wise stock data available.")

            with colB:
                st.subheader("Stock by Location")
                loc_data = []
                for r in grade_rows:
                    grade = df_summary.iloc[r, 4]
                    saf = pd.to_numeric(df_summary.iloc[r, 5], errors='coerce')
                    sms = pd.to_numeric(df_summary.iloc[r, 6], errors='coerce')
                    stores = pd.to_numeric(df_summary.iloc[r, 7], errors='coerce')
                    loc_data.append({"Grade": grade, "SAF": saf, "SMS": sms, "Stores": stores})
                loc_df = pd.DataFrame(loc_data)
                fig_loc = px.bar(
                    loc_df, x="Grade", y=["SAF", "SMS", "Stores"],
                    barmode="stack", template="plotly_dark",
                    labels={"value": "Stock (Tons)", "variable": "Location"}
                )
                st.plotly_chart(fig_loc, use_container_width=True)
        except Exception as e:
            st.error(f"Error reading despatch/stock insight data: {e}")

elif menu == "Manual Data Entry":
    st.title("📝 Manual Shift Data Input Form")
    st.write("Using this form, operators can lock daily furnace production parameters into the database.")
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
            st.success(f"✔️ Perfect! Data for {log_date} has been securely saved to the database.")

elif menu == "Bulk Data Upload":
    st.title("📤 Bulk Data Upload (Direct MIS Excel Integration)")
    st.write("Upload your MIS Excel file here. The system will automatically extract daily data from the 'DATA_entry' sheet and KPI targets from the 'Summary' sheet.")
    st.markdown("---")

    uploaded_file = st.file_uploader("Upload Excel Template", type=["xlsx"])
    if uploaded_file is not None:
        try:
            # 1. Store the Summary sheet in session_state (Dashboard will run on this)
            df_summary_new = pd.read_excel(uploaded_file, sheet_name="Summary", header=None)
            st.session_state["df_summary"] = df_summary_new
            st.session_state["uploaded_excel_name"] = uploaded_file.name

            # 1b. Store Raw Material, Delay Report and SiMn Despatch sheets too (used by their own tabs)
            try:
                st.session_state["df_raw_material"] = pd.read_excel(uploaded_file, sheet_name="Raw material mail data", header=None)
            except Exception:
                st.session_state["df_raw_material"] = None
            try:
                st.session_state["df_delay_report"] = pd.read_excel(uploaded_file, sheet_name="Delay Report", header=None)
            except Exception:
                st.session_state["df_delay_report"] = None
            try:
                st.session_state["df_simn_despatch"] = pd.read_excel(uploaded_file, sheet_name="SiMn Despatch", header=None)
            except Exception:
                st.session_state["df_simn_despatch"] = None

            # 2. Read the DATA_entry sheet and skip the top headers
            df_bulk = pd.read_excel(uploaded_file, sheet_name="DATA_entry", skiprows=2)

            # 3. Mapped the columns
            df_bulk.columns.values[0] = "Date"
            df_bulk.columns.values[1] = "SAF1_Prod"
            df_bulk.columns.values[4] = "Oprn_Delay"
            df_bulk.columns.values[5] = "Mech_Delay"
            df_bulk.columns.values[6] = "EI_Delay"
            df_bulk.columns.values[7] = "Mgmt_Delay"
            df_bulk.columns.values[35] = "SAF2_Prod"

            # 4. Clean and filter out totals/empty rows
            df_bulk = df_bulk[df_bulk["Date"].notna()]
            df_bulk = df_bulk[df_bulk["Date"] != "Total"]

            success_count = 0

            # 5. Loop through and safely lock each entry into the database
            for index, row in df_bulk.iterrows():
                try:
                    formatted_date = pd.to_datetime(row["Date"]).strftime('%Y-%m-%d')
                    s1 = pd.to_numeric(row["SAF1_Prod"], errors='coerce')
                    s2 = pd.to_numeric(row["SAF2_Prod"], errors='coerce')

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
                    continue

            if success_count > 0:
                st.success(f"🚀 Perfect! {success_count} days of data from the uploaded file have been successfully processed into the database. Dashboard and KPI Trends are now updated based on this file.")
            else:
                st.error("❌ No valid operational data was found in the file.")

        except Exception as e:
            st.error(f"Error processing Excel file: {e}")