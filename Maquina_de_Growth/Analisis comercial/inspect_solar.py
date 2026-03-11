import pandas as pd
import os

file_path = r"c:\Users\agusi\OneDrive\Escritorio\AntiGr\Analisis comercial\BBDD\BBDD NETrello 260226.xlsx"
df = pd.read_excel(file_path)

solar_df = df[df['List name'] == 'solar terminados'].copy()

print(f"Total rows in 'solar terminados': {len(solar_df)}")
print("\n--- Name and Description Sample ---")
for idx, row in solar_df.dropna(subset=['Description']).head(20).iterrows():
    print(f"Name: {row['Name']}")
    # Replace newlines with spaces for printing
    desc = str(row['Description']).replace('\n', ' ')
    print(f"Desc: {desc}")
    print("-")
