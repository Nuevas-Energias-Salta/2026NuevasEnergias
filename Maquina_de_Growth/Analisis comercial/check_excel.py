import pandas as pd
import sys

try:
    df1 = pd.read_excel('T1-Nocrm.xlsx', nrows=5)
    print("T1-Nocrm.xlsx columns:")
    print(df1.columns.tolist())
except Exception as e:
    print("Error T1:", e)

try:
    df2 = pd.read_excel('T2-Nocrm.xlsx', nrows=5)
    print("\nT2-Nocrm.xlsx columns:")
    print(df2.columns.tolist())
except Exception as e:
    print("Error T2:", e)
