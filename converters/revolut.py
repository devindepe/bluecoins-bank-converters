import os
import sys
from datetime import datetime

try:
    import pandas as pd
    from dotenv import load_dotenv
except ImportError:
    print("❌ Error: Missing dependencies. Please run: pip install -r requirements.txt")
    sys.exit(1)

# === LOAD CONFIGURATION ===
load_dotenv()

ACCOUNT_NAME = os.getenv("ACCOUNT_NAME_REVOLUT", "Revolut Account")
ACCOUNT_TYPE = os.getenv("ACCOUNT_TYPE_REVOLUT", "Bank")
OUTPUT_NAME_BASE = os.getenv("OUTPUT_NAME_REVOLUT", "revolut_bluecoins")

# === ARGUMENT CHECK ===
if len(sys.argv) < 3:
    print("❌ Error: Missing arguments.")
    print("Usage: python revolut.py <input_file> <output_folder>")
    sys.exit(1)

input_csv = sys.argv[1]
output_dir = sys.argv[2]

# === VALIDATE FILE EXTENSION ===
valid_extensions = ('.csv',)
if not input_csv.lower().endswith(valid_extensions):
    print(f"❌ Error: The provided file is not a valid CSV: {input_csv}")
    sys.exit(1)

if not os.path.isfile(input_csv):
    print(f"❌ Error: The file does not exist at path: {input_csv}")
    sys.exit(1)

# === CONFIGURATION ===
current_date = datetime.now().strftime("%Y-%m-%d")
output_filename = f"{OUTPUT_NAME_BASE.replace('.csv', '')}_{current_date}.csv"
OUTPUT_CSV = os.path.join(output_dir, output_filename)

# === READ CSV ===
# Revolut CSV uses comma separator and has a header row
df = pd.read_csv(input_csv, encoding='utf-8')

# Clean column names (remove extra spaces)
df.columns = [str(col).strip() for col in df.columns]

# Expected columns from Revolut:
# Tipo, Producto, Fecha de inicio, Fecha de finalización, Descripción, Importe, Comisión, Divisa, State, Saldo
expected_cols = {
    'tipo': ['Tipo', 'Type'],
    'producto': ['Producto', 'Product'],
    'fecha_inicio': ['Fecha de inicio', 'Started Date'],
    'fecha_fin': ['Fecha de finalización', 'Completed Date'],
    'descripcion': ['Descripción', 'Description'],
    'importe': ['Importe', 'Amount'],
    'comision': ['Comisión', 'Fee'],
    'divisa': ['Divisa', 'Currency'],
    'estado': ['State', 'Status'],
    'saldo': ['Saldo', 'Balance']
}

# Map columns (support both Spanish and English)
col_mapping = {}
for key, possible_names in expected_cols.items():
    for possible_name in possible_names:
        if possible_name in df.columns:
            col_mapping[key] = possible_name
            break

# Verify we have the essential columns
if 'fecha_inicio' not in col_mapping or 'importe' not in col_mapping:
    print("❌ Error: Could not find essential columns (Fecha de inicio/Started Date, Importe/Amount)")
    print("Available columns:", list(df.columns))
    sys.exit(1)

# === ROBUST CURRENCY CLEANING ===
def clean_currency(value):
    if pd.isna(value):
        return None
    
    if isinstance(value, (int, float)):
        return float(value)
    
    s = str(value).strip()
    # Revolut uses dot for decimals (1234.56 format)
    # Remove currency symbols and spaces
    s = s.replace('€', '').replace('EUR', '').replace(' ', '')
    
    try:
        return float(s)
    except ValueError:
        return None

# Apply cleaning to amount, fee and balance
df[col_mapping['importe']] = df[col_mapping['importe']].apply(clean_currency)

if 'comision' in col_mapping:
    df[col_mapping['comision']] = df[col_mapping['comision']].apply(clean_currency)

if 'saldo' in col_mapping:
    df[col_mapping['saldo']] = df[col_mapping['saldo']].apply(clean_currency)

# Drop rows where amount is not a valid number
df = df.dropna(subset=[col_mapping['importe']])

# === BLUECOINS CONVERSION ===
out = pd.DataFrame()

# Type: 'e' for Expense or 'i' for Income
out["(1)Type"] = df[col_mapping['importe']].apply(
    lambda x: "e" if x < 0 else "i"
)

# Date: M/D/YYYY format (e.g., 1/13/2026)
# Revolut dates come as "2026-01-14 11:54:37" or "2026-01-14"
dt_series = pd.to_datetime(df[col_mapping['fecha_inicio']], errors="coerce")
out["(2)Date"] = dt_series.apply(lambda x: f"{x.month}/{x.day}/{x.year}" if pd.notnull(x) else "")

# Item or Payee: Combine Type and Description
if 'tipo' in col_mapping and 'descripcion' in col_mapping:
    out["(3)Item or Payee"] = (
        df[col_mapping['tipo']].astype(str) + " - " + 
        df[col_mapping['descripcion']].astype(str)
    )
elif 'descripcion' in col_mapping:
    out["(3)Item or Payee"] = df[col_mapping['descripcion']].astype(str)
else:
    out["(3)Item or Payee"] = "Transaction"

# Amount: Always positive (type indicates income/expense)
out["(4)Amount"] = df[col_mapping['importe']].abs()

out["(5)Parent Category"] = ""
out["(6)Category"] = ""
out["(7)Account Type"] = ACCOUNT_TYPE
out["(8)Account"] = ACCOUNT_NAME

# Notes: Include useful information
notes_parts = []

if 'producto' in col_mapping:
    notes_parts.append("Producto: " + df[col_mapping['producto']].astype(str))

if 'comision' in col_mapping:
    # Only add fee if it's not zero or NaN
    fee_col = df[col_mapping['comision']].apply(
        lambda x: f"Comisión: {x}" if pd.notnull(x) and x != 0 else ""
    )
    notes_parts.append(fee_col)

if 'saldo' in col_mapping:
    notes_parts.append("Saldo: " + df[col_mapping['saldo']].astype(str))

if 'estado' in col_mapping:
    notes_parts.append("Estado: " + df[col_mapping['estado']].astype(str))

if notes_parts:
    out["(9)Notes"] = notes_parts[0]
    for i, part in enumerate(notes_parts[1:], 1):
        if isinstance(part, pd.Series):
            # For Series, concatenate with | separator where part is not empty
            out["(9)Notes"] = out["(9)Notes"] + part.apply(lambda x: f" | {x}" if x else "")
        else:
            out["(9)Notes"] = out["(9)Notes"] + " | " + part
else:
    out["(9)Notes"] = ""

out["(10) Label"] = ""
out["(11) Status"] = ""
out["(12) Split"] = ""

# === SAVE CSV ===
try:
    out.to_csv(OUTPUT_CSV, index=False, encoding="utf-8")
    print(f"✅ CSV generated correctly: {OUTPUT_CSV}")
    print(f"📊 Total transactions: {len(out)}")
except Exception as e:
    print(f"❌ Error saving CSV: {e}")