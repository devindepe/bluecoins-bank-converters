import os
import sys
import subprocess
from dotenv import load_dotenv, set_key

# Try to import tkinter safely
try:
    import tkinter as tk
    from tkinter import filedialog
    HAS_TKINTER = True
except ImportError:
    HAS_TKINTER = False

try:
    from dotenv import load_dotenv, set_key
except ImportError:
    print("\n❌ Error: 'python-dotenv' not found. Run: pip3 install python-dotenv")
    sys.exit(1)

def select_file(bank_name):
    """Selects the file using visual window or text depending on availability."""
    if HAS_TKINTER:
        try:
            root = tk.Tk()
            root.withdraw()
            root.attributes("-topmost", True)
            print(f"\n📂 Select the Excel file from {bank_name} in the pop-up window...")
            file_path = filedialog.askopenfilename(
                title=f"Select statement from {bank_name}",
                filetypes=[("Excel Files", "*.xlsx *.xls"), ("CSV Files", "*.csv")]
            )
            if file_path:
                return file_path
        except Exception:
            pass # If tkinter fails for any reason, go to text mode

    # Fallback: Manual text mode
    print(f"\n📍 Manual mode (drag the file here or paste the path)")
    path = input(f"Enter the path of the {bank_name} file: ").strip()
    return path.strip('"').strip("'").strip()

def get_or_set_account_name(bank_name):
    """Manages the account name in the .env."""
    env_key = f"ACCOUNT_NAME_{bank_name.upper()}"
    load_dotenv()
    account_name = os.getenv(env_key)

    if not account_name:
        default_name = f"{bank_name} Account"
        user_input = input(f"\nAccount name for {bank_name} in Bluecoins? (Enter for '{default_name}'): ").strip()
        account_name = user_input if user_input else default_name
        set_key(".env", env_key, account_name)
    return account_name

def main():
    if not os.path.exists('.env'):
        with open('.env', 'w') as f: f.write("")
    
    supported_banks = {
        "1": ("Ibercaja", "converters/ibercaja.py"),
        "2": ("BBVA", "converters/bbva.py"),
        "3": ("Revolut", "converters/revolut.py")
    }

    print("\n========================================")
    print("  SPAIN BANK CONVERTER FOR BLUECOINS   ")
    print("========================================")
    
    for k, v in supported_banks.items(): 
        print(f"{k}. {v[0]}")
    
    res = input("\nSelect a bank (number): ").strip()
    if res not in supported_banks:
        print("❌ Invalid selection.")
        return

    bank_name, script_file = supported_banks[res]
    
    get_or_set_account_name(bank_name)
    file_path = select_file(bank_name)
    
    if not file_path or not os.path.exists(file_path):
        print(f"❌ Error: The file does not exist or was not selected.")
        return

    if os.path.exists(script_file):
        print(f"\n🚀 Processing {bank_name}...")
        subprocess.run([sys.executable, script_file, file_path])
    else:
        print(f"❌ Error: The script {script_file} is not found in the folder.")

if __name__ == "__main__":
    main()