# config.py
import os
import pandas as pd
import psycopg2

# 🔐 PostgreSQL Database Authentication Coordinates
# (Apne local database username aur password ke hisab se isko change kar lena bhai)
DB_HOST = "localhost"
DB_NAME = "saf_production"
DB_USER = "postgres"
DB_PASSWORD = "admin.123"
DB_PORT = "5432"

SECRET_KEY = "jindal_secret_security_token"
EXCEL_FILE_PATH = "MIS 26-27.xlsx"

def get_db_connection():
    """Establishes an atomic transaction connection with PostgreSQL instance."""
    conn = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        port=DB_PORT
    )
    return conn

def init_db():
    """Initializes schema components and default seed metrics into PostgreSQL."""
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Target values tracking matrix table schema
    cur.execute("""
        CREATE TABLE IF NOT EXISTS kpi_targets (
            id SERIAL PRIMARY KEY,
            daily_prod NUMERIC(10,2) DEFAULT 203.00,
            monthly_prod NUMERIC(10,2) DEFAULT 17052.00,
            growth_pct NUMERIC(5,2) DEFAULT 5.00,
            max_sec NUMERIC(5,2) DEFAULT 3.50,
            optimal_sec NUMERIC(5,2) DEFAULT 3.30,
            min_avail NUMERIC(5,2) DEFAULT 95.00,
            util_pct NUMERIC(5,2) DEFAULT 90.00,
            delay_hours NUMERIC(10,2) DEFAULT 120.00,
            dispatch_vol NUMERIC(10,2) DEFAULT 16000.00,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    # Check if a seed row already exists, if not insert default configs
    cur.execute("SELECT COUNT(*) FROM kpi_targets;")
    if cur.fetchone()[0] == 0:
        cur.execute("""
            INSERT INTO kpi_targets (daily_prod, monthly_prod, growth_pct, max_sec, optimal_sec, min_avail, util_pct, delay_hours, dispatch_vol)
            VALUES (203.0, 17052, 5.0, 3.5, 3.3, 95.0, 90.0, 120.0, 16000);
        """)
    
    conn.commit()
    cur.close()
    conn.close()

# Keep your existing Excel Engine perfectly untouched below
def get_excel_data():
    try:
        if not os.path.exists(EXCEL_FILE_PATH):
            return None, None, None, None
        excel_file = pd.ExcelFile(EXCEL_FILE_PATH)
        all_sheets = excel_file.sheet_names
        sheet_dict = {name.strip().lower().replace(" ", ""): name for name in all_sheets}
        
        def load_sheet_safely(target_name, default_fallback):
            for clean_key, original_name in sheet_dict.items():
                if target_name.lower().replace(" ", "") in clean_key:
                    return pd.read_excel(excel_file, sheet_name=original_name)
            if default_fallback in all_sheets:
                return pd.read_excel(excel_file, sheet_name=default_fallback)
            return pd.DataFrame()

        return load_sheet_safely("summary", "Summary"), load_sheet_safely("rawmaterial", "Raw material mail data"), load_sheet_safely("dataentry", "DATA_entry"), load_sheet_safely("delay", "Delay Report")
    except Exception as e:
        print(f"Excel Extraction Core Fault: {e}")
        return None, None, None, None