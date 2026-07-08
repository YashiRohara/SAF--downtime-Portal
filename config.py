# config.py
import os
import pandas as pd

# 🔐 Flask Core Parameters Baseline Keys
SECRET_KEY = "jindal_secret_security_token"
DB_NAME = "saf_production.db"

EXCEL_FILE_PATH = "MIS 26-27.xlsx"

def get_excel_data():
    try:
        if not os.path.exists(EXCEL_FILE_PATH):
            print(f"🚨 Target File '{EXCEL_FILE_PATH}' not found. Falling back to empty structures.")
            return None, None, None, None
        
        excel_file = pd.ExcelFile(EXCEL_FILE_PATH)
        
        # 🔍 SMART MATCH ENGINE: Saare tabs ke asli naam nikalne ke liye
        all_sheets = excel_file.sheet_names
        sheet_dict = {name.strip().lower().replace(" ", ""): name for name in all_sheets}
        
        def load_sheet_safely(target_name, default_fallback):
            for clean_key, original_name in sheet_dict.items():
                if target_name.lower().replace(" ", "") in clean_key:
                    return pd.read_excel(excel_file, sheet_name=original_name)
            # Safe Fallback
            if default_fallback in all_sheets:
                return pd.read_excel(excel_file, sheet_name=default_fallback)
            return pd.DataFrame() # Khali DataFrame agar sheet hi missing ho

        df_summary = load_sheet_safely("summary", "Summary")
        df_raw_material = load_sheet_safely("rawmaterial", "Raw material mail data")
        df_data_entry = load_sheet_safely("dataentry", "DATA_entry")
        df_delay = load_sheet_safely("delay", "Delay Report")
        
        return df_summary, df_raw_material, df_data_entry, df_delay
    except Exception as e:
        print(f"Excel Extraction Core Fault: {e}")
        return None, None, None, None