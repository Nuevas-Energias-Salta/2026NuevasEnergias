import sys
from pathlib import Path

def fix_encoding():
    filepath = Path(r"c:\Users\Gonza\Desktop\proyecto zzz\sistema_informes_fv\generar_informes.py")
    
    with open(filepath, 'rb') as f:
        raw_bytes = f.read()
        
    try:
        # Tries to decode it pretending it was saved as utf-8 but mangled as cp1252/iso-8859-1
        # Because we see "Ã³" which is the utf-8 bytes for 'ó' (0xc3 0xb3) read as windows-1252
        text = raw_bytes.decode('utf-8')
        
        # It's actually utf-8 encoded, but the problem is the text *inside* the file
        # was pasted while the editor or python thought it was another encoding.
        # Let's fix the specific replacements we see in the text:
        replacements = {
            "Ã¡": "á",
            "Ã©": "é",
            "Ã­": "í",
            "Ã³": "ó",
            "Ãº": "ú",
            "Ã±": "ñ",
            "Ã\x81": "Á",
            "Ã\x89": "É",
            "Ã\x8d": "Í",
            "Ã\x93": "Ó",
            "Ã\x9a": "Ú",
            "Ã\x91": "Ñ",
            "Ã¼": "ü",
            "Â²": "²",
            "Ã\x82": "Â",
            "Ã¢": "â",
            "Â": "" # Remove residual circumflex from some bad conversions
        }
        
        for bad, good in replacements.items():
            text = text.replace(bad, good)
            
        # Re-save as proper utf-8
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(text)
            
        print("✅ Archivo generar_informes.py corregido y guardado como UTF-8.")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fix_encoding()
