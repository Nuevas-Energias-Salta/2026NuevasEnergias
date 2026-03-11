import pandas as pd
import os

path = r"c:\Users\agusi\OneDrive\Escritorio\AntiGr\Analisis comercial\BBDD"

# Read noCRM
file_nocrm = os.path.join(path, "BBDD noCRM Completa 260226.csv")
df_nocrm = pd.read_csv(file_nocrm, sep=";", engine="python", on_bad_lines="skip", encoding="latin-1")

print("--- noCRM Completa ---")
for col in ['Tipo de cliente', 'Categoria Lead', 'Pipeline', 'Step', 'Status', 'tags']:
    if col in df_nocrm.columns:
        print(f"Unique values in {col}:")
        print(df_nocrm[col].dropna().unique()[:20])

# Read KanbanTrello
file_trello = os.path.join(path, "BBDD KanbanTrello completa 260226.xlsx")
df_trello = pd.read_excel(file_trello)

print("\n--- KanbanTrello ---")
for col in ['List name', 'Labels', 'Producto']:
    if col in df_trello.columns:
        print(f"Unique values in {col}:")
        print(df_trello[col].dropna().unique()[:20])
