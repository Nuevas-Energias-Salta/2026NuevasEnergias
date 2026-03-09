import pdfplumber
import os

pdf_dir = "resumenes"
pdf_files = [f for f in os.listdir(pdf_dir) if f.endswith(".pdf")]

for pdf_file in pdf_files:
    print(f"\n{'='*50}")
    print(f"ANALYZING: {pdf_file}")
    print(f"{'='*50}")
    
    path = os.path.join(pdf_dir, pdf_file)
    try:
        with pdfplumber.open(path) as pdf:
            print(f"Total Pages: {len(pdf.pages)}")
            
            # Analyze first 2 pages
            for i, page in enumerate(pdf.pages[:2]):
                print(f"\n--- Page {i+1} ---")
                text = page.extract_text()
                if text:
                    print("TEXT PREVIEW (First 500 chars):")
                    print(text[:500])
                    print("\nTEXT PREVIEW (Lines with money '$'):")
                    lines = text.split('\n')
                    money_lines = [l for l in lines if "$" in l or "USD" in l]
                    for ml in money_lines[:5]:
                        print(f"  {ml}")
                else:
                    print("NO TEXT EXTRACTED (Image based?)")
                
                tables = page.extract_tables()
                if tables:
                    print(f"\nTABLES FOUND: {len(tables)}")
                    print("First table row example:")
                    print(tables[0][0])
                else:
                    print("\nNO TABLES FOUND")

    except Exception as e:
        print(f"ERROR: {e}")
