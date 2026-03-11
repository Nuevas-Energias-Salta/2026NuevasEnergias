import pandas as pd
import os
import re

file_path = r"c:\Users\agusi\OneDrive\Escritorio\AntiGr\Analisis comercial\BBDD\BBDD KanbanPVTrello 280226.xlsx"
df = pd.read_excel(file_path)

print(f"Total rows in KanbanPVTrello: {len(df)}")
print("Columns:", df.columns.tolist())

print("\nSample of Name column (checking for PRE numbers like 61-Pto132-Name):")

# Regex to find names starting with a number and a dash
mask = df['Name'].str.match(r'^\s*\d+\s*-', na=False)
matches = df[mask]

print(f"Found {len(matches)} rows where Name starts with a number.")
print(matches['Name'].head(15))

print("\nSample of Description column:")
for idx, row in df.dropna(subset=['Description']).head(15).iterrows():
    print(f"Name: {row['Name']}")
    desc = str(row['Description']).replace('\n', ' ')[:150]
    print(f"Desc: {desc}...")
    print("-")
