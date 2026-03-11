import pandas as pd
import os

file_path = r"c:\Users\agusi\OneDrive\Escritorio\AntiGr\Analisis comercial\BBDD\BBDD NETrello 260226.xlsx"
df = pd.read_excel(file_path)

print("Columns:", df.columns.tolist())

if 'List name' in df.columns:
    print("\nUnique List names in NETrello:")
    print(df['List name'].value_counts())
    
print("\nSample of 'Description' column:")
print(df['Description'].dropna().head(10))

print("\nSample of 'Name' column:")
print(df['Name'].dropna().head(10))
