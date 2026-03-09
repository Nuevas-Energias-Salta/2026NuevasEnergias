import sys
import os
from pathlib import Path
import time

# --- Setup Paths ---
BASE_DIR = Path(__file__).parent.absolute()
EDESA_DIR = BASE_DIR / "edesa_facturas" / "edesa_facturas"
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(EDESA_DIR))

try:
    from extractor_zzz import extraer_datos_factura
    from growatt_extractor_auto import GrowattExtractor
except ImportError as e:
    print(f"Error importing modules: {e}")
    sys.exit(1)

def test_edesa_extraction():
    print("\n--- TEST 1: EDESA PDF Extraction (Safe Mode) ---")
    
    # Find a sample PDF
    knowledge_dir = BASE_DIR / "Facturas-conocimiento"
    pdfs = list(knowledge_dir.glob("*.pdf"))
    
    if not pdfs:
        print("No sample PDFs found in Facturas-conocimiento.")
        return
    
    sample_pdf = pdfs[0]
    print(f"Testing with file: {sample_pdf.name}")
    
    try:
        # Extract data BUT NOT upload
        data = extraer_datos_factura(sample_pdf)
        
        print("\n[SUCCESS] Data Extracted:")
        print(f"  - Client: {data.get('cliente')}")
        print(f"  - NIS: {data.get('nis')}")
        print(f"  - Period: {data.get('fecha')}")
        print(f"  - Total Consumption: {data.get('consumo_total')} kWh")
        print(f"  - Category: {data.get('categoria')}")
        print(f"  [SAFE] Data was NOT uploaded to Google Sheets.")
        
    except Exception as e:
        print(f"\n[FAILURE] Error extracting PDF: {e}")

def test_growatt_connection():
    print("\n--- TEST 2: Growatt Connection (Safe Mode) ---")
    print("Initializing Growatt Extractor (Headless)...")
    
    extractor = None
    try:
        extractor = GrowattExtractor(headless=True)
        
        # Test Login
        print("Attempting to login...")
        if extractor.login():
            print("[SUCCESS] Login successful!")
            
            # Test Plant Search (Non-intrusive)
            test_plant = "Fabrica Forja"
            print(f"Attempting to find plant: '{test_plant}'...")
            if extractor.buscar_planta(test_plant):
                 print(f"[SUCCESS] Plant '{test_plant}' found!")
                 
                 # Test Date Injection
                 from datetime import datetime
                 test_date = datetime(2025, 12, 1) # Dec 2025
                 print(f"Testing export for date: {test_date.strftime('%Y-%m')}...")
                 
                 # Call the export function with the date
                 gen = extractor.exportar_y_procesar_excel(test_plant, target_date=test_date)
                 
                 print(f"Extraction Result: {gen} kWh")
            else:
                 print(f"[WARNING] Could not find test plant '{test_plant}'.")
        else:
            print("[FAILURE] Login failed.")
            
    except Exception as e:
        print(f"[FAILURE] Error during Growatt test: {e}")
    finally:
        if extractor:
            print("Closing browser...")
            try:
                extractor.driver.quit()
            except:
                pass

if __name__ == "__main__":
    print("=== STARTING PROJECT TEST SAFE MODE ===")
    test_edesa_extraction()
    test_growatt_connection()
    print("\n=== TEST COMPLETED ===")
