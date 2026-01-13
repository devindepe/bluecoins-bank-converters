import os
import sys
import subprocess
from dotenv import load_dotenv, set_key

# Intentar importar tkinter de forma segura
try:
    import tkinter as tk
    from tkinter import filedialog
    HAS_TKINTER = True
except ImportError:
    HAS_TKINTER = False

try:
    from dotenv import load_dotenv, set_key
except ImportError:
    print("\n❌ Error: No se encontró 'python-dotenv'. Ejecuta: pip3 install python-dotenv")
    sys.exit(1)

def select_file(bank_name):
    """Selecciona el archivo usando ventana visual o texto según disponibilidad."""
    if HAS_TKINTER:
        try:
            root = tk.Tk()
            root.withdraw()
            root.attributes("-topmost", True)
            print(f"\n📂 Selecciona el archivo Excel de {bank_name} en la ventana emergente...")
            file_path = filedialog.askopenfilename(
                title=f"Seleccionar extracto de {bank_name}",
                filetypes=[("Archivos Excel", "*.xlsx *.xls"), ("Archivos CSV", "*.csv")]
            )
            if file_path:
                return file_path
        except Exception:
            pass # Si falla tkinter por cualquier razón, vamos al modo texto

    # Fallback: Modo texto manual
    print(f"\n📍 Modo manual (arrastra el archivo aquí o pega la ruta)")
    path = input(f"Introduce la ruta del archivo de {bank_name}: ").strip()
    return path.strip('"').strip("'").strip()

def get_or_set_account_name(bank_name):
    """Gestiona el nombre de la cuenta en el .env."""
    env_key = f"ACCOUNT_NAME_{bank_name.upper()}"
    load_dotenv()
    account_name = os.getenv(env_key)

    if not account_name:
        default_name = f"{bank_name} Cuenta"
        user_input = input(f"\n¿Nombre de cuenta para {bank_name} en Bluecoins? (Enter para '{default_name}'): ").strip()
        account_name = user_input if user_input else default_name
        set_key(".env", env_key, account_name)
    return account_name

def main():
    if not os.path.exists('.env'):
        with open('.env', 'w') as f: f.write("")
    
    supported_banks = {
        "1": ("Ibercaja", "ibercaja.py"),
        "2": ("BBVA", "bbva.py"),
        "3": ("Revolut", "revolut.py")
    }

    print("\n========================================")
    print("  ESPAÑA BANK CONVERTER FOR BLUECOINS   ")
    print("========================================")
    
    for k, v in supported_banks.items(): 
        print(f"{k}. {v[0]}")
    
    res = input("\nSelecciona un banco (número): ").strip()
    if res not in supported_banks:
        print("❌ Selección inválida.")
        return

    bank_name, script_file = supported_banks[res]
    
    get_or_set_account_name(bank_name)
    file_path = select_file(bank_name)
    
    if not file_path or not os.path.exists(file_path):
        print(f"❌ Error: El archivo no existe o no fue seleccionado.")
        return

    if os.path.exists(script_file):
        print(f"\n🚀 Procesando {bank_name}...")
        subprocess.run([sys.executable, script_file, file_path])
    else:
        print(f"❌ Error: El script {script_file} no se encuentra en la carpeta.")

if __name__ == "__main__":
    main()