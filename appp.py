# appp.py
from flask import Flask, render_template, jsonify, request, flash, redirect, url_for
import config
import pandas as pd
import numpy as np
from functools import wraps

app = Flask(__name__)
app.secret_key = config.SECRET_KEY

# 🚀 Server start hone par DB tables create/verify karein
with app.app_context():
    try:
        config.init_db()
        print("✅ PostgreSQL Database Initialized Successfully!")
    except Exception as e:
        print(f"⚠️ DB Initialization Error: {e}")

# -------------------------------------------------------------
# 🔒 DECORATOR: Check if user is logged in
# -------------------------------------------------------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("🔒 Session expired or login required.")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# -------------------------------------------------------------
# 🔑 LOGIN ROUTE (PostgreSQL Version)
# -------------------------------------------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        selected_role = request.form.get('role')
        username = request.form.get('username')
        password = request.form.get('password')

        try:
            conn = config.get_db_connection()
            cur = conn.cursor()
            
            # PostgreSQL parameterized query
            cur.execute(
                "SELECT id, username, password, role, status FROM users WHERE username = %s;", 
                (username,)
            )
            user = cur.fetchone()
            cur.close()
            conn.close()

            if user:
                user_id, db_user, db_pass, db_role, status = user[0], user[1], user[2], user[3], user[4]
                
                # Check User Status
                if status and str(status).lower() not in ['active', '1', 'true']:
                    flash("⛔ Your account is inactive. Contact Admin.")
                    return redirect(url_for('login'))

                # Password Validation
                if db_pass == password:
                    session['user_id'] = user_id
                    session['username'] = db_user
                    session['role'] = db_role
                    
                    flash(f"Welcome back, {db_user}!")
                    return redirect(url_for('overview'))
                else:
                    flash("❌ Incorrect Password.")
            else:
                flash("❌ User ID not found.")

        except Exception as e:
            flash(f"⚠️ Database Error: {str(e)}")

        return redirect(url_for('login'))

    return render_template('login.html')


# -------------------------------------------------------------
# 🚪 LOGOUT ROUTE
# -------------------------------------------------------------
@app.route('/logout')
def logout():
    session.clear()
    flash("ℹ️ You have logged out successfully.")
    return redirect(url_for('login'))


# Call DB initializing script context upon start
try:
    config.init_db()
    print("🚀 PostgreSQL Target Calibration Table Initialized Successfully!")
except Exception as e:
    print(f"💥 PostgreSQL Initialization Fault Trace: {e}")


# 📊 HELPER ENGINES FOR REPORTS & DASHBOARDS
def get_daily_performance_summary(report_date):
    """
    Fetches real production, MTD totals, and FY Month-wise ABP vs Actual performance from PostgreSQL.
    """
    conn = config.get_db_connection()
    cur = conn.cursor()
    
    # 1. On Date Metrics
    cur.execute("""
        SELECT steel_yield, power_ingested, saf1_steel_yield, saf2_steel_yield
        FROM saf_production_data 
        WHERE log_date = %s;
    """, (report_date,))
    row = cur.fetchone()
    
    # 2. Target values from kpi_targets
    cur.execute("SELECT daily_prod FROM kpi_targets WHERE id = 1;")
    t_row = cur.fetchone()
    target_prod = float(t_row[0]) if t_row else 203.0
    
    # 3. Month-to-Date (MTD) Cumulative
    cur.execute("""
        SELECT SUM(steel_yield)
        FROM saf_production_data 
        WHERE DATE_TRUNC('month', log_date) = DATE_TRUNC('month', %s::date);
    """, (report_date,))
    mtd_row = cur.fetchone()
    
    # 4. Month-wise Aggregations for Financial Year (April to March)
    cur.execute("""
        SELECT 
            TO_CHAR(log_date, 'Mon') as mon_name,
            SUM(COALESCE(saf1_steel_yield, steel_yield / 2.0)) as saf1_total,
            SUM(COALESCE(saf2_steel_yield, steel_yield / 2.0)) as saf2_total,
            SUM(steel_yield) as plant_total,
            SUM(power_ingested) as power_total
        FROM saf_production_data
        GROUP BY TO_CHAR(log_date, 'Mon'), DATE_TRUNC('month', log_date)
        ORDER BY DATE_TRUNC('month', log_date);
    """)
    monthly_db_rows = cur.fetchall()
    
    cur.close()
    conn.close()
    
    # Monthly Financial Mapping (Apr - Mar)
    months_order = ['Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar']
    abp_targets = {'Apr': 6014, 'May': 4893, 'Jun': 6014, 'Jul': 6229, 'Aug': 6229, 'Sep': 6014, 'Oct': 6229, 'Nov': 6014, 'Dec': 6229, 'Jan': 6229, 'Feb': 5585, 'Mar': 6229}
    
    monthly_matrix = {m: {'saf1': 0.0, 'saf2': 0.0, 'total': 0.0, 'pct': '0.0%', 'sec': '-'} for m in months_order}
    
    fy_saf1_sum = 0.0
    fy_saf2_sum = 0.0
    fy_total_sum = 0.0
    fy_power_sum = 0.0

    for r in monthly_db_rows:
        m_code = r[0] # e.g., 'Apr', 'May'
        if m_code in monthly_matrix:
            s1_val = float(r[1] or 0.0)
            s2_val = float(r[2] or 0.0)
            tot_val = float(r[3] or 0.0)
            power_val = float(r[4] or 0.0)
            
            target_val = abp_targets.get(m_code, 6000)
            achieved_pct = round((tot_val / target_val) * 100, 1) if target_val > 0 else 0.0
            sec_rate = round(power_val / tot_val, 3) if tot_val > 0 else '-'
            
            monthly_matrix[m_code] = {
                'saf1': round(s1_val, 1),
                'saf2': round(s2_val, 1),
                'total': round(tot_val, 1),
                'pct': f"{achieved_pct}%",
                'sec': sec_rate
            }
            
            fy_saf1_sum += s1_val
            fy_saf2_sum += s2_val
            fy_total_sum += tot_val
            fy_power_sum += power_val

    fy_target_sum = sum(abp_targets.values())
    fy_pct = round((fy_total_sum / fy_target_sum) * 100, 1) if fy_target_sum > 0 else 0.0
    fy_sec = round(fy_power_sum / fy_total_sum, 3) if fy_total_sum > 0 else '-'

    actual_total = float(row[0]) if row and row[0] else 0.0
    power_date = float(row[1]) if row and row[1] else 0.0
    saf1_act = float(row[2]) if row and row[2] else actual_total / 2
    saf2_act = float(row[3]) if row and row[3] else actual_total / 2
    
    mtd_actual_prod = float(mtd_row[0]) if mtd_row and mtd_row[0] else actual_total
    
    pct_on_date = round((actual_total / target_prod) * 100) if target_prod > 0 else 0
    mtd_target = target_prod * 15
    pct_mtd = round((mtd_actual_prod / mtd_target) * 100) if mtd_target > 0 else 0

    return {
        "on_date": {
            "target": target_prod, "actual": actual_total, "pct": f"{pct_on_date}%", "power": power_date,
            "saf1": {"target": target_prod / 2, "actual": saf1_act, "pct": f"{pct_on_date}%"},
            "saf2": {"target": target_prod / 2, "actual": saf2_act, "pct": f"{pct_on_date}%"}
        },
        "month_cum": {
            "target": mtd_target, "actual": mtd_actual_prod, "pct": f"{pct_mtd}%",
            "saf1": {"target": mtd_target / 2, "actual": mtd_actual_prod / 2, "pct": f"{pct_mtd}%"},
            "saf2": {"target": mtd_target / 2, "actual": mtd_actual_prod / 2, "pct": f"{pct_mtd}%"}
        },
        "monthly_matrix": monthly_matrix,
        "abp_targets": abp_targets,
        "fy_totals": {
            "target": fy_target_sum,
            "saf1": round(fy_saf1_sum, 1),
            "saf2": round(fy_saf2_sum, 1),
            "total": round(fy_total_sum, 1),
            "pct": f"{fy_pct}%",
            "sec": fy_sec
        }
    }


def get_monthly_delay_breakdown(report_date):
    """
    Fetches daily delay logs (Oprn, Mech, E&I, Mgmt) for the entire month of the selected report date.
    """
    conn = config.get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT log_date, 
               saf1_oprn_delay, saf1_mech_delay, saf1_ei_delay, saf1_mgmt_delay, saf1_delay_reason,
               saf2_oprn_delay, saf2_mech_delay, saf2_ei_delay, saf2_mgmt_delay, saf2_delay_reason,
               delay_hours
        FROM saf_production_data 
        WHERE DATE_TRUNC('month', log_date) = DATE_TRUNC('month', %s::date)
        ORDER BY log_date ASC;
    """, (report_date,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    
    delay_records = []
    for r in rows:
        base_delay = float(r[11]) if r[11] else 0.0
        
        s1_oprn = float(r[1]) if r[1] else 0.0
        s1_mech = float(r[2]) if r[2] else 0.0
        s1_ei = float(r[3]) if r[3] else (base_delay / 2 if base_delay > 0 else 0.0)
        s1_mgmt = float(r[4]) if r[4] else 0.0
        s1_total = s1_oprn + s1_mech + s1_ei + s1_mgmt
        
        s2_oprn = float(r[6]) if r[6] else 0.0
        s2_mech = float(r[7]) if r[7] else 0.0
        s2_ei = float(r[8]) if r[8] else (base_delay / 2 if base_delay > 0 else 0.0)
        s2_mgmt = float(r[9]) if r[9] else 0.0
        s2_total = s2_oprn + s2_mech + s2_ei + s2_mgmt
        
        delay_records.append({
            "date": r[0].strftime('%Y-%m-%d'),
            "s1": {"oprn": s1_oprn, "mech": s1_mech, "ei": s1_ei, "mgmt": s1_mgmt, "total": s1_total, "reason": r[5] or "-"},
            "s2": {"oprn": s2_oprn, "mech": s2_mech, "ei": s2_ei, "mgmt": s2_mgmt, "total": s2_total, "reason": r[10] or "-"}
        })
        
    return delay_records


def fetch_database_metrics():
    try:
        conn = config.get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT log_date, power_ingested, steel_yield, delay_hours, data_source 
            FROM saf_production_data 
            ORDER BY log_date ASC;
        """)
        rows = cur.fetchall()
        cur.close()
        conn.close()
        
        time_series = []
        for r in rows:
            yield_val = float(r[2]) if r[2] and float(r[2]) > 0 else 1.0
            sec_rate = round(float(r[1]) / yield_val, 2) if r[1] else 0.0
            
            time_series.append({
                "Date": r[0].strftime('%Y-%m-%d'),
                "Production_MT": float(r[2]) if r[2] else 0.0,
                "Delay_Hours": float(r[3]) if r[3] else 0.0,
                "SEC_Rate": sec_rate,
                "Source": r[4]
            })
        return time_series
    except Exception as e:
        print(f"⚠️ Failover Reading DB Analytics: {e}")
        return []

@app.route('/')
@app.route('/overview')
@login_required
def overview():
    try:
        conn = config.get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT daily_prod, max_sec, monthly_prod, min_avail FROM kpi_targets ORDER BY id DESC LIMIT 1;")
        target_row = cur.fetchone()
        cur.close()
        conn.close()
        
        targets = {
            "daily_prod": target_row[0],
            "max_sec": target_row[1],
            "monthly_prod": target_row[2],
            "min_avail": target_row[3]
        } if target_row else {"daily_prod": 203.0, "max_sec": 3.50, "monthly_prod": 17052, "min_avail": 95.0}
    except Exception:
        targets = {"daily_prod": 203.0, "max_sec": 3.50, "monthly_prod": 17052, "min_avail": 95.0}
        
    return render_template('overview.html', targets=targets)


@app.route('/raw_material_matrix')
@login_required
def raw_material_matrix():
    metrics = {"time_series": fetch_database_metrics()}
    return render_template('raw_material.html', metrics=metrics)


@app.route('/power')
@login_required
def power():
    metrics = {"time_series": fetch_database_metrics()}
    return render_template('power.html', metrics=metrics)


@app.route('/target_settings', methods=['GET', 'POST'])
@login_required
def target_settings():
    conn = config.get_db_connection()
    cur = conn.cursor()
    
    if request.method == 'POST':
        daily_prod = request.form.get('target_daily_prod')
        monthly_prod = request.form.get('target_monthly_prod')
        growth_pct = request.form.get('target_growth_pct')
        max_sec = request.form.get('target_max_sec')
        optimal_sec = request.form.get('target_optimal_sec')
        min_avail = request.form.get('target_avail_pct')
        util_pct = request.form.get('target_util_pct')
        delay_hours = request.form.get('target_delay_hours')
        dispatch_vol = request.form.get('target_dispatch_vol')
        
        cur.execute("""
            UPDATE kpi_targets 
            SET daily_prod=%s, monthly_prod=%s, growth_pct=%s, max_sec=%s, 
                optimal_sec=%s, min_avail=%s, util_pct=%s, delay_hours=%s, dispatch_vol=%s, last_updated=CURRENT_TIMESTAMP
            WHERE id = 1;
        """, (daily_prod, monthly_prod, growth_pct, max_sec, optimal_sec, min_avail, util_pct, delay_hours, dispatch_vol))
        
        conn.commit()
        flash("🎯 Operational benchmarks successfully saved and distributed across DB pipelines.")
        cur.close()
        conn.close()
        return redirect(url_for('target_settings'))

    cur.execute("SELECT daily_prod, monthly_prod, growth_pct, max_sec, optimal_sec, min_avail, util_pct, delay_hours, dispatch_vol FROM kpi_targets WHERE id = 1;")
    row = cur.fetchone()
    cur.close()
    conn.close()
    
    t_data = {}
    if row:
        keys = ['daily_prod', 'monthly_prod', 'growth_pct', 'max_sec', 'optimal_sec', 'min_avail', 'util_pct', 'delay_hours', 'dispatch_vol']
        t_data = dict(zip(keys, [float(val) for val in row]))
        
    return render_template('target.html', t=t_data)


@app.route('/trends')
@login_required
def trends():
    db_series = fetch_database_metrics()
    
    df = pd.DataFrame(db_series)
    weekly_analysis = []
    
    if not df.empty:
        df['Date'] = pd.to_datetime(df['Date'])
        df['Week_Label'] = df['Date'].dt.strftime('Week %U')
        grp = df.groupby('Week_Label')['Production_MT'].agg(['mean', 'max', 'min']).reset_index()
        
        max_avg = grp['mean'].max() if not grp.empty else 0
        for _, row in grp.iterrows():
            weekly_analysis.append({
                "Week": row['Week_Label'],
                "Avg": round(row['mean'], 1),
                "Max": round(row['max'], 1),
                "Min": round(row['min'], 1),
                "IsBest": row['mean'] == max_avg and max_avg > 0
            })
    else:
        weekly_analysis = [{"Week": "No Database Data Available", "Avg": 0, "Max": 0, "Min": 0, "IsBest": False}]

    metrics = {
        "time_series": db_series,
        "weekly_analysis": weekly_analysis
    }
    return render_template('trends.html', metrics=metrics)


@app.route('/logistics')
def logistics(): return render_template('logistics.html')

@app.route('/analysis')
@login_required
def analysis():
    try:
        metrics = {"time_series": fetch_database_metrics()}
        return render_template('analysis.html', metrics=metrics)
    except Exception as e:
        print(f"💥 Analysis Route Render Core Error: {e}")
        return f"Template Error: {e}"


@app.route('/quarterly')
@login_required
def quarterly():
    db_series = fetch_database_metrics()
    
    if not db_series:
        metrics = {
            "monthly_series": [
                {"label": "April Production", "production": 0.0, "is_best": False},
                {"label": "May Production", "production": 0.0, "is_best": False},
                {"label": "June Production", "production": 0.0, "is_best": False}
            ],
            "weekly_series": [{"label": f"Week {i}", "production": 0.0, "is_best": False} for i in range(1, 9)]
        }
        return render_template('quarterly.html', metrics=metrics)
        
    df = pd.DataFrame(db_series)
    
    if 'log_date' in df.columns:
        df = df.rename(columns={'log_date': 'Date'})
    if 'steel_yield' in df.columns:
        df = df.rename(columns={'steel_yield': 'Production_MT'})
        
    weekly_series = []
    monthly_series = []
    
    if not df.empty and 'Date' in df.columns and 'Production_MT' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'])
        
        df['Wk_Num'] = df['Date'].dt.isocalendar().week
        min_wk = df['Wk_Num'].min()
        df['Wk_Key'] = df['Wk_Num'].apply(lambda x: f"Week {x - min_wk + 1}")
        
        wk_grp = df.groupby('Wk_Key')['Production_MT'].sum().reset_index()
        max_wk = wk_grp['Production_MT'].max() if not wk_grp.empty else 0
        
        for _, r in wk_grp.iterrows():
            weekly_series.append({
                "label": str(r['Wk_Key']), 
                "production": float(r['Production_MT']), 
                "is_best": bool(r['Production_MT'] == max_wk)
            })
            
        df['Mon_Key'] = df['Date'].dt.strftime('%B Production')
        mon_grp = df.groupby('Mon_Key')['Production_MT'].sum().reset_index()
        max_mon = mon_grp['Production_MT'].max() if not mon_grp.empty else 0
        
        for _, r in mon_grp.iterrows():
            monthly_series.append({
                "label": str(r['Mon_Key']), 
                "production": float(r['Production_MT']), 
                "is_best": bool(r['Production_MT'] == max_mon)
            })
    
    if len(weekly_series) < 4:
        existing_labels = [w['label'] for w in weekly_series]
        for i in range(1, 5):
            lbl = f"Week {i}"
            if lbl not in existing_labels:
                weekly_series.append({"label": lbl, "production": 0.0, "is_best": False})
                
    if len(monthly_series) < 2:
        existing_months = [m['label'] for m in monthly_series]
        for m_lbl in ["April Production", "May Production", "June Production"]:
            if m_lbl not in existing_months:
                monthly_series.append({"label": m_lbl, "production": 0.0, "is_best": False})

    weekly_series = sorted(weekly_series, key=lambda x: x['label'])

    metrics = {
        "monthly_series": monthly_series,
        "weekly_series": weekly_series
    }
    return render_template('quarterly.html', metrics=metrics)


@app.route('/manual_entry', methods=['GET', 'POST'])
@login_required
def manual_entry():
    if session.get('role') == 'Viewer':
            flash("⛔ Access Restricted: Viewers cannot perform Manual Entry.")
            return redirect(url_for('overview'))
    
    if request.method == 'POST':
        try:
            log_date = request.form.get('log_date') or request.form.get('date') or request.form.get('target_date')
            
            if not log_date or log_date.strip() == '':
                flash("❌ Operation Blocked: Please select a valid Date from the calendar before submitting!")
                return redirect(url_for('manual_entry'))
                
            power = float(request.form.get('power_ingested', 0) or 0)
            yield_mt = float(request.form.get('steel_yield', 0) or 0)
            delays = float(request.form.get('delay_hours', 0) or 0)
            
            conn = config.get_db_connection()
            cur = conn.cursor()
            
            cur.execute("""
                INSERT INTO saf_production_data (data_source, log_date, power_ingested, steel_yield, delay_hours)
                VALUES ('MANUAL_ENTRY', %s, %s, %s, %s)
                ON CONFLICT (log_date) DO UPDATE 
                SET data_source='MANUAL_ENTRY', power_ingested=EXCLUDED.power_ingested, 
                    steel_yield=EXCLUDED.steel_yield, delay_hours=EXCLUDED.delay_hours;
            """, (log_date, power, yield_mt, delays))
            
            conn.commit()
            cur.close()
            conn.close()
            flash("🎯 Manual furnace log logged permanently into PostgreSQL.")
        except Exception as e:
            flash(f"❌ Manual Entry Failed: {e}")
        return redirect(url_for('manual_entry'))

        
    return render_template('data_entry.html')


@app.route('/bulk_upload', methods=['GET', 'POST'])
def bulk_upload():
    if session.get('role') == 'Viewer':
        flash("⛔ Access Restricted: Viewers cannot access Bulk Upload.")
        return redirect(url_for('overview'))

    conn = config.get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS gsheet_config (
            id SERIAL PRIMARY KEY,
            url TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    
    if request.method == 'POST':
        if 'gsheet_url' in request.form and request.form.get('gsheet_url').strip() != '':
            url = request.form.get('gsheet_url').strip()
            try:
                cur.execute("DELETE FROM gsheet_config;")
                cur.execute("INSERT INTO gsheet_config (url) VALUES (%s);", (url,))
                conn.commit()
                flash("🎯 Success: Official Google Sheet URL saved permanently!")
            except Exception as e:
                conn.rollback()
                flash(f"❌ Error saving URL: {e}")
                
        elif 'bulk_file' in request.files:
            file = request.files['bulk_file']
            if file and file.filename != '':
                try:
                    df = pd.read_csv(file) if file.filename.endswith('.csv') else pd.read_excel(file)
                    df.columns = df.columns.str.strip().str.lower()
                    inserted_rows = 0
                    
                    d_col = next((c for c in df.columns if 'date' in c), df.columns[0])
                    y_col = next((c for c in df.columns if 'total prod' in str(c) or 'prod' in str(c)), df.columns[1])
                    
                    for _, row in df.iterrows():
                        log_date_raw = str(row[d_col]).strip()
                        if not log_date_raw or log_date_raw.lower() in ['nan', 'none', '']: continue
                        log_date = pd.to_datetime(log_date_raw).strftime('%Y-%m-%d')
                        yield_mt = float(row[y_col]) if pd.notna(row[y_col]) else 0.0
                        
                        cur.execute("""
                            INSERT INTO saf_production_data (data_source, log_date, steel_yield, power_ingested, delay_hours)
                            VALUES ('BULK_UPLOAD', %s, %s, 0.0, 0.0)
                            ON CONFLICT (log_date) DO UPDATE SET steel_yield=EXCLUDED.steel_yield;
                        """, (log_date, yield_mt))
                        inserted_rows += 1
                    conn.commit()
                    flash(f"📁 Local file processed! Imported {inserted_rows} rows.")
                except Exception as e:
                    flash(f"❌ Local File Error: {e}")

    cur.execute("SELECT url FROM gsheet_config ORDER BY id DESC LIMIT 1;")
    saved_url_row = cur.fetchone()
    saved_url = saved_url_row[0] if saved_url_row else None
    
    cur.close()
    conn.close()
    
    return render_template('bulk_upload.html', saved_url=saved_url)


@app.route('/sync_now', methods=['POST'])
def sync_now():
    conn = config.get_db_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT url FROM gsheet_config ORDER BY id DESC LIMIT 1;")
    url_row = cur.fetchone()
    
    if not url_row:
        flash("❌ Sync Blocked: No Google Sheet URL configured yet!")
        cur.close()
        conn.close()
        return redirect(url_for('bulk_upload'))
        
    url = url_row[0]
    try:
        if "/edit" in url:
            base_url = url.split("/edit")[0]
            gid_part = "0"
            if "gid=" in url:
                gid_part = url.split("gid=")[1].split("&")[0]
            csv_export_url = f"{base_url}/export?format=csv&gid={gid_part}"
        else:
            csv_export_url = url

        df_sheet_data = pd.read_csv(csv_export_url, header=1)
        df_sheet_data.columns = df_sheet_data.columns.str.strip().str.lower()
        
        date_col = next((c for c in df_sheet_data.columns if 'date' in str(c)), df_sheet_data.columns[0])
        yield_col = next((c for c in df_sheet_data.columns if 'total prod' in str(c) or 'prod (t)' in str(c)), None)
        power_col = next((c for c in df_sheet_data.columns if 'power' in str(c) or 'mwh' in str(c)), None)
        delay_col = next((c for c in df_sheet_data.columns if 'delay' in str(c) or 'downtime' in str(c)), None)

        if not yield_col:
            yield_col = df_sheet_data.columns[1]

        inserted_rows = 0
        for _, row in df_sheet_data.iterrows():
            log_date_raw = str(row[date_col]).strip()
            if not log_date_raw or log_date_raw.lower() in ['nan', 'none', '', 'total', 'avg', 'unnamed:']:
                continue
                
            try:
                log_date = pd.to_datetime(log_date_raw, errors='coerce').strftime('%Y-%m-%d')
                if log_date == 'NaT' or not log_date: continue
            except:
                continue

            def parse_numeric(val):
                if pd.isna(val): return 0.0
                try: return float(str(val).replace(',', '').strip())
                except: return 0.0

            yield_mt = parse_numeric(row[yield_col])
            power = parse_numeric(row[power_col]) if power_col else 0.0
            delays = parse_numeric(row[delay_col]) if delay_col else 0.0
            
            if yield_mt == 0.0 and power == 0.0:
                continue

            cur.execute("""
                INSERT INTO saf_production_data (data_source, log_date, power_ingested, steel_yield, delay_hours)
                VALUES ('GOOGLE_SHEET', %s, %s, %s, %s)
                ON CONFLICT (log_date) DO UPDATE 
                SET data_source='GOOGLE_SHEET', power_ingested=EXCLUDED.power_ingested, 
                    steel_yield=EXCLUDED.steel_yield, delay_hours=EXCLUDED.delay_hours;
            """, (log_date, power, yield_mt, delays))
            inserted_rows += 1
        
        conn.commit()
        flash(f"🚀 Success: Database dynamically refreshed with {inserted_rows} live entries!")
    except Exception as e:
        flash(f"❌ Dynamic Sync Fault: {e}")
    finally:
        cur.close()
        conn.close()
        
    return redirect(url_for('bulk_upload'))


@app.route('/reports')
def view_reports():
    report_date = request.args.get('report_date')
    if not report_date:
        report_date = date.today().strftime('%Y-%m-%d')
    
    active_report = request.args.get('report_type', 'daily')
    
    perf = get_daily_performance_summary(report_date)
    delays = get_monthly_delay_breakdown(report_date)
    
    return render_template(
        'reports.html', 
        selected_date=report_date, 
        active_report=active_report, 
        perf=perf, 
        delays=delays
    )


if __name__ == '__main__':
    # 🌐 Configured for Jindal Steel Local Network / Server Deployment
    app.run(host='0.0.0.0', port=8989, debug=True)
'''if __name__ == '__main__':
    app.run(debug=True, port=5000)'''
    