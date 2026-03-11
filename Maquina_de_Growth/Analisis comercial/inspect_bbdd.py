import pandas as pd
import os

path = r"c:\Users\agusi\OneDrive\Escritorio\AntiGr\Analisis comercial\BBDD"
files = [f for f in os.listdir(path) if f.endswith(('.csv', '.xlsx'))]

print(f"Total files: {len(files)}")

for f in files:
    file_path = os.path.join(path, f)
    try:
        if f.endswith('.csv'):
            # try to read just the first row to get columns and total rows
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as fp:
                lines = fp.readlines()
            print(f"---\n{f}: {len(lines)} rows")
            if len(lines) > 0:
                print(f"Headers: {lines[0].strip()}")
        elif f.endswith('.xlsx'):
            df = pd.read_excel(file_path)
            print(f"---\n{f}: {len(df)} rows")
            print(f"Headers: {list(df.columns)}")
    except Exception as e:
        print(f"Error with {f}: {e}")
