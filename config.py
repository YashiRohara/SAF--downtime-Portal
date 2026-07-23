import os
import pandas as pd
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "saf_production")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "admin.123")
DB_PORT = os.getenv("DB_PORT", "5432")

SECRET_KEY = os.getenv("SECRET_KEY", "jindal_secret_security_token")
EXCEL_FILE_PATH = "MIS 26-27.xlsx"

def get_db_connection():
    conn = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        port=DB_PORT
    )
    return conn

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    
    # 🔑 1. USERS TABLE FOR ROLE-BASED LOGIN (ADDED FIX)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            role VARCHAR(20) DEFAULT 'Viewer',
            status VARCHAR(20) DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # 2. KPI TARGETS TABLE
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

    # 3. PRODUCTION DATA TABLE
    cur.execute("""
        CREATE TABLE IF NOT EXISTS saf_production_data (
            id SERIAL PRIMARY KEY,
            data_source VARCHAR(50) DEFAULT 'MANUAL_ENTRY', 
            log_date DATE UNIQUE NOT NULL,    
            power_ingested NUMERIC(10,2) DEFAULT 0.0,    
            steel_yield NUMERIC(10,2) DEFAULT 0.0,       
            delay_hours NUMERIC(5,2) DEFAULT 0.0,        
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # 4. INITIAL SEEDS (Default Admin & Users Insert agar Empty ho)
    cur.execute("SELECT COUNT(*) FROM users;")
    if cur.fetchone()[0] == 0:
        cur.execute("""
            INSERT INTO users (username, password, role, status) VALUES
            ('EMP001', 'admin123', 'Admin', 'active'),
            ('EMP002', 'operator123', 'Operator', 'active'),
            ('EMP003', 'viewer123', 'Viewer', 'active');
        """)

    cur.execute("SELECT COUNT(*) FROM kpi_targets;")
    if cur.fetchone()[0] == 0:
        cur.execute("""
            INSERT INTO kpi_targets (daily_prod, monthly_prod, growth_pct, max_sec, optimal_sec, min_avail, util_pct, delay_hours, dispatch_vol)
            VALUES (203.0, 17052, 5.0, 3.5, 3.3, 95.0, 90.0, 120.0, 16000);
        """)

    # 5. GOOGLE SHEET CONFIG TABLE
    cur.execute("""
        CREATE TABLE IF NOT EXISTS gsheet_config (
            id SERIAL PRIMARY KEY,
            url TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    # 6. ALTER COLUMNS IF NEEDED
    cur.execute("""
        ALTER TABLE saf_production_data 
        ADD COLUMN IF NOT EXISTS saf1_oprn_delay NUMERIC(5,2) DEFAULT 0.0,
        ADD COLUMN IF NOT EXISTS saf1_mech_delay NUMERIC(5,2) DEFAULT 0.0,
        ADD COLUMN IF NOT EXISTS saf1_ei_delay NUMERIC(5,2) DEFAULT 0.0,
        ADD COLUMN IF NOT EXISTS saf1_mgmt_delay NUMERIC(5,2) DEFAULT 0.0,
        ADD COLUMN IF NOT EXISTS saf1_delay_reason TEXT,
        ADD COLUMN IF NOT EXISTS saf2_oprn_delay NUMERIC(5,2) DEFAULT 0.0,
        ADD COLUMN IF NOT EXISTS saf2_mech_delay NUMERIC(5,2) DEFAULT 0.0,
        ADD COLUMN IF NOT EXISTS saf2_ei_delay NUMERIC(5,2) DEFAULT 0.0,
        ADD COLUMN IF NOT EXISTS saf2_mgmt_delay NUMERIC(5,2) DEFAULT 0.0,
        ADD COLUMN IF NOT EXISTS saf2_delay_reason TEXT,
        ADD COLUMN IF NOT EXISTS saf1_steel_yield NUMERIC(10,2) DEFAULT 0.0,
        ADD COLUMN IF NOT EXISTS saf2_steel_yield NUMERIC(10,2) DEFAULT 0.0,
        ADD COLUMN IF NOT EXISTS mn_ore_high NUMERIC(10,2) DEFAULT 0.0,
        ADD COLUMN IF NOT EXISTS mn_ore_low NUMERIC(10,2) DEFAULT 0.0,
        ADD COLUMN IF NOT EXISTS nut_coke NUMERIC(10,2) DEFAULT 0.0,
        ADD COLUMN IF NOT EXISTS raw_coal NUMERIC(10,2) DEFAULT 0.0;
    """)
    
    conn.commit()
    cur.close()
    conn.close()

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