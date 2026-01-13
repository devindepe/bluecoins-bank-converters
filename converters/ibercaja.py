import os
import sys

try:
    import pandas as pd
    from dotenv import load_dotenv
except ImportError:
    print("❌ Error: Missing dependencies. Please run: pip install -r requirements.txt")
    sys.exit(1)

# === LOAD CONFIGURATION ===
# This looks for a .env file in the same directory
load_dotenv()

# We get the account name from .env. If not found, we use a default.
ACCOUNT_NAME = os.getenv("ACCOUNT_NAME_IBERCAJA", "Ibercaja Account")

# === ARGUMENT CHECK (From Dispatcher) ===
# main.py passes the file path as the first argument (sys.argv[1])
if len(sys.argv) < 2:
    print("❌ Error: No file path provided.")
    print("Usage: python ibercaja.py <file_path>")
    sys.exit(1)

input_xlsx = sys.argv[1]

# === VALIDATE FILE EXTENSION ===
# Ensure the user provided a valid Excel file
valid_extensions = ('.xlsx', '.xls')
if not input_xlsx.lower().endswith(valid_extensions):
    print(f"❌ Error: The provided file is not a valid Excel: {input_xlsx}")
    sys.exit(1)

# Validate that the file actually exists
if not os.path.isfile(input_xlsx):
    print(f"❌ Error: The file does not exist at path: {input_xlsx}")
    sys.exit(1)

# === CONFIGURATION ===
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_CSV = os.path.join(SCRIPT_DIR, "ibercaja_bluecoins.csv")

# === READ EXCEL ===
# Read without predefined types to perform manual cleaning
df = pd.read_excel(input_xlsx, header=4)

df.columns = [
    "order",
    "oper_date",
    "value_date",
    "concept",
    "description",
    "reference",
    "amount",
    "balance"
]

# === ROBUST CURRENCY CLEANING ===
def clean_currency(value):
    if pd.isna(value):
        return None
    
    # If it's already a number (int or float), return it as a float
    if isinstance(value, (int, float)):
        return float(value)
    
    # If it's a string, clean it
    s = str(value).strip()
    # Remove Euro symbol and spaces
    s = s.replace('€', '').replace(' ', '')
    # Spanish format: 1.234,56 -> Remove thousands dot, replace decimal comma with dot
    s = s.replace('.', '').replace(',', '.')
    
    try:
        return float(s)
    except ValueError:
        return None

# Apply cleaning to amount and balance
df["amount"] = df["amount"].apply(clean_currency)
df["balance"] = df["balance"].apply(clean_currency)

# Drop rows where amount is not a valid number (headers, footers, etc.)
df = df.dropna(subset=["amount"])

# === BLUECOINS CONVERSION ===
out = pd.DataFrame()

# Type: 'e' for Expense or 'i' for Income
out["(1)Type"] = df["amount"].apply(
    lambda x: "e" if x < 0 else "i"
)

# Date: M/D/YYYY format (e.g., 1/13/2026)
# Use a universal format regardless of OS locale
dt_series = pd.to_datetime(df["oper_date"], dayfirst=True, errors="coerce")
out["(2)Date"] = dt_series.apply(lambda x: f"{x.month}/{x.day}/{x.year}" if pd.notnull(x) else "")

out["(3)Item or Payee"] = (
    df["concept"].astype(str) + " - " + df["description"].astype(str)
)

out["(4)Amount"] = df["amount"].abs()

out["(5)Parent Category"] = ""
out["(6)Category"] = ""
out["(7)Account Type"] = "Bank"
out["(8)Account"] = ACCOUNT_NAME

out["(9)Notes"] = (
    "Ref: " + df["reference"].astype(str) +
    " | Balance: " + df["balance"].astype(str)
)

out["(10) Label"] = ""
out["(11) Status"] = ""
out["(12) Split"] = ""

# === SAVE CSV ===
# Bluecoins requires UTF-8 and comma separator
out.to_csv(OUTPUT_CSV, index=False, encoding="utf-8")

print(f"✅ CSV generated correctly: {OUTPUT_CSV}")