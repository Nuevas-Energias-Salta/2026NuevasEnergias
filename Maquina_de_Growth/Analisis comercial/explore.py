import pandas as pd
import sys

try:
    df = pd.read_csv('BBDD noCRM Completa 260226.csv', sep=';', on_bad_lines='skip', low_memory=False)
    print("Columns:")
    for c in df.columns:
        print(f" - {c}")
    print(f"\nTotal rows: {len(df)}")
    print("\nData Types:")
    print(df.dtypes)
    print("\nSample values:")
    print(df.head().to_dict('records'))
except Exception as e:
    print(e, file=sys.stderr)
