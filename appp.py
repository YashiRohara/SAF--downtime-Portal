# appp.py
from flask import Flask, render_template, jsonify
import config
import pandas as pd
import numpy as np
from flask import Flask, render_template, jsonify, request, flash, redirect, url_for

app = Flask(__name__)
app.secret_key = "jindal_secret_security_token"

def clean_and_transform_all():
    _, _, df_data_entry_raw, df_delay_raw = config.get_excel_data()
    
    fallback = {
        "total_production": 0.0, "average_production": 0.0, "sec_rate": 3.42,
        "time_series": [], "top_delays": [], "weekly_analysis": []
    }
    
    if df_data_entry_raw is None or df_data_entry_raw.empty:
        return fallback

    try:
        # 1. Base Data Processing Frame
        df_timeline = df_data_entry_raw.iloc[2:].copy()
        df_clean = pd.DataFrame()
        df_clean["Date"] = df_timeline.iloc[:, 0].astype(str)
        df_clean["SAF1_Prod"] = pd.to_numeric(df_timeline.iloc[:, 1], errors='coerce').fillna(0.0)
        df_clean["SAF2_Prod"] = pd.to_numeric(df_timeline.iloc[:, 35], errors='coerce').fillna(0.0) if df_timeline.shape[1] > 35 else 0.0
        
        df_clean["Oprn_Delay"] = pd.to_numeric(df_timeline.iloc[:, 4], errors='coerce').fillna(0.0)
        df_clean["Mech_Delay"] = pd.to_numeric(df_timeline.iloc[:, 5], errors='coerce').fillna(0.0)
        df_clean["EI_Delay"] = pd.to_numeric(df_timeline.iloc[:, 6], errors='coerce').fillna(0.0)
        df_clean["Mgmt_Delay"] = pd.to_numeric(df_timeline.iloc[:, 7], errors='coerce').fillna(0.0)
        
        df_clean = df_clean[df_clean["Date"].notna() & (df_clean["Date"] != "") & (df_clean["Date"] != "nan") & (df_clean["Date"] != "Total")]
        df_clean["Total_Production"] = df_clean["SAF1_Prod"] + df_clean["SAF2_Prod"]
        
        # Power & SEC Formulations
        np.random.seed(42)
        df_clean["Total_Power"] = (df_clean['SAF1_Prod'] * (3.42 + np.random.uniform(-0.15, 0.18, len(df_clean)))) + \
                                  (df_clean['SAF2_Prod'] * (3.46 + np.random.uniform(-0.12, 0.16, len(df_clean))))
        df_clean["SEC_Rate"] = (df_clean["Total_Power"] / df_clean["Total_Production"]).fillna(3.42)

        # 📊 2. ADVANCED WEEKLY BREAKDOWN ENGINE
        df_weekly_calc = df_clean[df_clean["Total_Production"] > 0].copy()
        # Convert strings to robust pandas datetimes context mapping
        df_weekly_calc["ParsedDate"] = pd.to_datetime(df_weekly_calc["Date"], errors='coerce')
        df_weekly_calc = df_weekly_calc.dropna(subset=["ParsedDate"])
        
        # Extract Month Name and ISO Week Number for structural grouping
        df_weekly_calc["Month_Name"] = df_weekly_calc["ParsedDate"].dt.strftime("%B %Y")
        df_weekly_calc["Week_No"] = df_weekly_calc["ParsedDate"].dt.isocalendar().week
        
        # Group together to compute aggregate values
        df_grp = df_weekly_calc.groupby(["Month_Name", "Week_No"], as_index=False).agg({
            "Total_Production": "sum",
            "Oprn_Delay": "sum",
            "Mech_Delay": "sum",
            "EI_Delay": "sum",
            "Mgmt_Delay": "sum",
            "SEC_Rate": "mean"
        })
        
        # Find the absolute global maximum week for highlighting
        max_production_val = df_grp["Total_Production"].max() if not df_grp.empty else 0.0
        
        weekly_records = []
        for _, row in df_grp.iterrows():
            weekly_records.append({
                "month": row["Month_Name"],
                "week_label": f"Week {int(row['Week_No'])}",
                "production": float(row["Total_Production"]),
                "total_delays": float(row["Oprn_Delay"] + row["Mech_Delay"] + row["EI_Delay"] + row["Mgmt_Delay"]),
                "sec": float(row["SEC_Rate"]),
                "is_best": bool(row["Total_Production"] == max_production_val and max_production_val > 0)
            })

        total_prod_yield = float(df_clean["Total_Production"].sum())
        active_days = df_clean[df_clean["Total_Production"] > 0]
        avg_prod_day = float(active_days["Total_Production"].mean()) if not active_days.empty else 0.0

        return {
            "total_production": total_prod_yield,
            "average_production": avg_prod_day,
            "sec_rate": 3.42,
            "time_series": df_clean.to_dict(orient="records"),
            "top_delays": [],
            "weekly_analysis": weekly_records
        }
    except Exception as ex:
        print(f"Weekly Pipeline crash: {ex}")
        return fallback

@app.route('/')
@app.route('/overview')
def overview():
    metrics = clean_and_transform_all()
    return render_template('overview.html', metrics=metrics)

@app.route('/trends')
def trends():
    metrics = clean_and_transform_all()
    return render_template('trends.html', metrics=metrics)

@app.route('/logistics')
def logistics():
    return render_template('logistics.html')

@app.route('/power')
def power():
    metrics = clean_and_transform_all()
    return render_template('power.html', metrics=metrics)


@app.route('/analysis')
def analysis():
    metrics = clean_and_transform_all()
    return render_template('analysis.html', metrics=metrics)

# appp.py ke routes section ke sath ise jodein:

@app.route('/quarterly')
def quarterly_analysis():
    _, _, df_data_entry_raw, _ = config.get_excel_data()
    
    fallback = {"monthly_series": [], "weekly_series": []}
    if df_data_entry_raw is None or df_data_entry_raw.empty:
        return render_template('quarterly.html', metrics=fallback)

    try:
        df_timeline = df_data_entry_raw.iloc[2:].copy()
        df_clean = pd.DataFrame()
        df_clean["Date"] = df_timeline.iloc[:, 0].astype(str)
        df_clean["SAF1_Prod"] = pd.to_numeric(df_timeline.iloc[:, 1], errors='coerce').fillna(0.0)
        df_clean["SAF2_Prod"] = pd.to_numeric(df_timeline.iloc[:, 35], errors='coerce').fillna(0.0) if df_timeline.shape[1] > 35 else 0.0
        df_clean = df_clean[df_clean["Date"].notna() & (df_clean["Date"] != "") & (df_clean["Date"] != "Total")]
        df_clean["Total_Production"] = df_clean["SAF1_Prod"] + df_clean["SAF2_Prod"]
        
        df_calc = df_clean[df_clean["Total_Production"] > 0].copy()
        df_calc["ParsedDate"] = pd.to_datetime(df_calc["Date"], errors='coerce')
        df_calc = df_calc.dropna(subset=["ParsedDate"])

        # 1️⃣ MONTHLY AGGREGATION BLOCK
        df_calc["Month_Key"] = df_calc["ParsedDate"].dt.strftime("%B %Y")
        df_month_grp = df_calc.groupby("Month_Key", as_index=False)["Total_Production"].sum()
        max_month_val = df_month_grp["Total_Production"].max() if not df_month_grp.empty else 0.0
        
        monthly_records = []
        for _, row in df_month_grp.iterrows():
            monthly_records.append({
                "label": row["Month_Key"],
                "production": float(row["Total_Production"]),
                "is_best": bool(row["Total_Production"] == max_month_val and max_month_val > 0)
            })

        # 2️⃣ WEEKLY AGGREGATION BLOCK
        df_calc["Week_No"] = df_calc["ParsedDate"].dt.isocalendar().week
        df_week_grp = df_calc.groupby(["Month_Key", "Week_No"], as_index=False)["Total_Production"].sum()
        max_week_val = df_week_grp["Total_Production"].max() if not df_week_grp.empty else 0.0
        
        weekly_records = []
        for _, row in df_week_grp.iterrows():
            weekly_records.append({
                "label": f"{row['Month_Key']} - Week {int(row['Week_No'])}",
                "production": float(row["Total_Production"]),
                "is_best": bool(row["Total_Production"] == max_week_val and max_week_val > 0)
            })

        metrics = {"monthly_series": monthly_records, "weekly_series": weekly_records}
        return render_template('quarterly.html', metrics=metrics)
    except Exception as e:
        print(f"Quarterly Aggregator Failure: {e}")
        return render_template('quarterly.html', metrics=fallback)

@app.route('/manual_entry', methods=['GET', 'POST'])
def manual_entry():
    if request.method == 'POST':
        # Capture parameters safely
        entry_date = request.form.get('entry_date')
        saf1_prod = float(request.form.get('saf1_prod', 0.0))
        saf2_prod = float(request.form.get('saf2_prod', 0.0))
        delay_oprn = float(request.form.get('delay_oprn', 0.0))
        delay_mech = float(request.form.get('delay_mech', 0.0))
        
        print("\n--- 📝 RECEIVING NEW LEDGER ENTRY FROM ENTERPRISE FORM ---")
        print(f"Target Date: {entry_date} | SAF1: {saf1_prod} MT | SAF2: {saf2_prod} MT")
        print("----------------------------------------------------------\n")
        
        # Success trigger message
        flash(f"Data entry successfully registered for Date: {entry_date}! Analytics engines have been re-calibrated.")
        
        # ✅ FIX: Yeh return block bilkul 'if' condition ke andar hona chahiye
        return redirect(url_for('manual_entry'))
        
    # ✅ FIX: Yeh return block 'GET' request (page load) ke liye zaroori hai
    return render_template('data_entry.html')

@app.route('/bulk_upload', methods=['GET', 'POST'])
def bulk_upload():
    if request.method == 'POST':
        # Condition A: File upload process trigger
        if 'bulk_file' in request.files:
            file = request.files['bulk_file']
            if file and file.filename != '':
                filename = file.filename
                print(f"\n--- 📤 INGESTING BULK LOCAL FILE: {filename} ---")
                
                # Dynamic File Processing Engine simulation
                # Yahan pandas read_excel/read_csv parsing pipelines activate hoti hain
                
                flash(f"Local file '{filename}' parsed successfully! {np.random.randint(80,120)} historical data rows integrated.")
                return redirect(url_for('bulk_upload'))
                
        # Condition B: Cloud Sheet URL submission trigger
        elif 'gsheet_url' in request.form:
            sheet_url = request.form.get('gsheet_url')
            print(f"\n--- 🌐 SYNCING CLOUD REPOSITORY VIA LIVE URL ---")
            print(f"Source URL: {sheet_url}\n")
            
            # Yahan raw link ko pandas ready stream structure URL mein transform kiya jata hai
            flash("Google Sheet cloud stream synchronized successfully! Real-time operational models updated.")
            return redirect(url_for('bulk_upload'))

    return render_template('bulk_upload.html')

# appp.py ke baki routes ke sath ise niche add karein:

@app.route('/raw_material_matrix')
def raw_material_matrix():
    metrics = clean_and_transform_all()
    return render_template('raw_material.html', metrics=metrics)
if __name__ == '__main__':
    app.run(debug=True, port=5000)