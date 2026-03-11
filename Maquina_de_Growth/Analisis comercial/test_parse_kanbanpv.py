import pandas as pd
import os
import re

file_path = r"c:\Users\agusi\OneDrive\Escritorio\AntiGr\Analisis comercial\BBDD\BBDD KanbanPVTrello 280226.xlsx"
df = pd.read_excel(file_path)

print(f"Total rows in KanbanPVTrello: {len(df)}")
print("\nSample names:")
print(df['Name'].head(10))

# Try extracting the PRE project number: e.g. "61-Pto132-Daniela Romero"
def extract_pre_number(name):
    name_str = str(name).strip()
    # Match starting digits before a dash
    match = re.match(r'^(\d+)\s*-', name_str)
    if match:
        return int(match.group(1))
    return None

df['PRE_Project_Number'] = df['Name'].apply(extract_pre_number)

pre_clients = df[df['PRE_Project_Number'].notnull()]
print(f"\nFound {len(pre_clients)} clients with a PRE project number.")
if len(pre_clients) > 0:
    max_pre = pre_clients['PRE_Project_Number'].max()
    print(f"Maximum PRE project number found: {max_pre}")

print("\n--- Testing Description parsing for Combos ---")
# Example description parsing
def parse_description_products(desc):
    desc = str(desc).lower()
    prods = []
    if 'pileta' in desc or 'colectores' in desc or 'climatiza' in desc: prods.append('Climatizacion Piletas')
    if 'termotanque' in desc or 'termo' in desc or 'hissuma' in desc or 'saiar' in desc or 'heat pipe' in desc or 'acs' in desc: prods.append('Termotanque Solar (ACS)')
    if 'nuke' in desc or 'ñuke' in desc or 'estufa' in desc or 'biomasa' in desc or 'tromen' in desc: prods.append('Biomasa')
    if 'fv' in desc or 'fotovoltaico' in desc or 'paneles' in desc or 'inversor' in desc: prods.append('Energia Solar FV')
    if 'pre' in desc or 'piso radiante' in desc or 'malla' in desc or 'cable calefactor' in desc or 'termostato' in desc: prods.append('PRE / Piso Radiante Electrico')
    return prods

df['Products_from_desc'] = df['Description'].apply(parse_description_products)
combo_clients = df[df['Products_from_desc'].apply(len) > 1]
print(f"Found {len(combo_clients)} clients with multiple products in description.")
for idx, row in combo_clients.head(5).iterrows():
    print(f"Name: {row['Name']}")
    print(f"Detected: {row['Products_from_desc']}")
    print("-")
