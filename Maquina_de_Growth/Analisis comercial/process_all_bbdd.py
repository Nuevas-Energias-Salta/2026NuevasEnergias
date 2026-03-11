import pandas as pd
import os
import re
import numpy as np

path = r"c:\Users\agusi\OneDrive\Escritorio\AntiGr\Analisis comercial\BBDD"

all_files = [f for f in os.listdir(path) if f.endswith(('.csv', '.xlsx'))]

all_phones = set()
all_emails = set()

dfs = []

# New Counters for combos
product_counters = {
    'Energia Solar FV': 0,
    'Climatizacion Piletas': 0,
    'Termotanque Solar (ACS)': 0,
    'Biomasa': 0,
    'Calefaccion (Tradicional/Otros)': 0,
    'PRE / Piso Radiante Electrico': 0,
    'Sin Tag de Producto Claro': 0
}

def clean_phone(p):
    if pd.isna(p): return None
    p_str = str(p).strip().replace(' ', '').replace('-', '').replace('+', '')
    if len(p_str) < 6: return None
    return p_str

def clean_email(e):
    if pd.isna(e): return None
    e_str = str(e).strip().lower()
    if '@' not in e_str: return None
    return e_str

for f in all_files:
    file_path = os.path.join(path, f)
    try:
        if f.endswith('.csv'):
            df = pd.read_csv(file_path, sep=None, engine='python', on_bad_lines='skip', encoding='latin-1')
        else:
            df = pd.read_excel(file_path)
            
        # extract phones and emails
        for col in df.columns:
            lcol = str(col).lower()
            if 'tel' in lcol or 'celular' in lcol or 'phone' in lcol:
                for val in df[col].dropna():
                    cp = clean_phone(val)
                    if cp: all_phones.add(cp)
            if 'mail' in lcol or 'correo' in lcol:
                for val in df[col].dropna():
                    ce = clean_email(val)
                    if ce: all_emails.add(ce)
        
        # Standardize basic columns
        df['Source_File'] = f
        
        # We need Tipo de cliente, tags, Status, Step, Categoria Lead, Motivo Perdida, Nombre del lead
        col_map = {}
        for col in df.columns:
            l = str(col).lower()
            if 'tipo de cliente' in l: col_map[col] = 'Tipo de cliente'
            elif l == 'tags' or l == 'labels': col_map[col] = 'tags'
            elif l == 'status' or l == 'estatus': col_map[col] = 'Status'
            elif l == 'step' or 'etapa' in l: col_map[col] = 'Step'
            elif 'categoria' in l: col_map[col] = 'Categoria Lead'
            elif 'motivo' in l: col_map[col] = 'Motivo Perdida'
            elif 'lead' in l or 'name' in l or 'nombre' in l: 
                if 'Nombre del lead' not in col_map.values(): # avoid overwriting
                    col_map[col] = 'Nombre del lead'
                    
        df = df.rename(columns=col_map)
        
        # Ensure required columns exist
        for req in ['Tipo de cliente', 'tags', 'Status', 'Step', 'Categoria Lead', 'Motivo Perdida', 'Nombre del lead', 'Source_File']:
            if req not in df.columns:
                df[req] = ''
                
        # Handle 'List name' for Trello
        if 'List name' in df.columns:
            df['List_name_temp'] = df['List name']
        else:
            df['List_name_temp'] = ''
            
        # Handle 'Description' for Trello 'solar terminados' distinction 
        if 'Description' in df.columns:
            df['Description_temp'] = df['Description']
        else:
            df['Description_temp'] = ''
                
        # Keep only required columns to save memory and avoid mess
        df = df.loc[:,~df.columns.duplicated()].copy()
        
        # Make sure we only take the columns we need, and exactly once
        cols_to_keep = ['Nombre del lead', 'Tipo de cliente', 'tags', 'Status', 'Step', 'Categoria Lead', 'Motivo Perdida', 'Source_File', 'List_name_temp', 'Description_temp']
        df = df[[c for c in cols_to_keep if c in df.columns]]
        for c in cols_to_keep:
            if c not in df.columns:
                df[c] = ''
        df = df[cols_to_keep]
                
        dfs.append(df)
        
    except Exception as e:
        print(f"Error processing {f}: {e}")

master_df = pd.concat(dfs, ignore_index=True)
master_df = master_df.fillna('')

# Categorization Logic
def is_b2c(row):
    tc = str(row['Tipo de cliente']).lower()
    sf = str(row['Source_File']).lower()
    if 'residencial' in tc: return True
    # If empty, check filename for residential hints
    if 'tipal' in sf or 'valle' in sf or 'pradera' in sf or 'casadir' in sf or 'home' in sf or 'piletas' in sf:
        return True
    return False

def is_b2b(row):
    tc = str(row['Tipo de cliente']).lower()
    sf = str(row['Source_File']).lower()
    b2b_keywords = ['agro', 'comercial', 'industria', 'bodega', 'mineria', 'obra publica', 'desarrolladora', 'clinica', 'educacion', 'empresa']
    if any(k in tc for k in b2b_keywords): return True
    # If empty, check filename
    if 'empresa' in sf or 'constructor' in sf or 'turismo' in sf or 'capemisa' in sf or 'gestores' in sf or 'b2b' in sf:
        return True
    return False

def is_cliente(row):
    tg = str(row['tags']).lower()
    st = str(row['Status']).lower()
    if 'cliente' in tg or st == 'won': return True
    return False

# Assign T1, T2, T3, T4
categories = []
for idx, row in master_df.iterrows():
    b2c = is_b2c(row)
    b2b = is_b2b(row)
    cliente = is_cliente(row)
    
    # default to B2C if unknown and not B2B
    if not b2c and not b2b:
        b2c = True 
        
    if b2c and not cliente: cat = 'T1'
    elif b2c and cliente: cat = 'T2'
    elif b2b and not cliente: cat = 'T3'
    elif b2b and cliente: cat = 'T4'
    else: cat = 'Uncategorized' # Should not happen
    
    categories.append(cat)

master_df['Category'] = categories

# Inside T1: Architects / Constructors
def is_architect(row):
    text = str(row['tags']).lower() + str(row['Tipo de cliente']).lower() + str(row['Nombre del lead']).lower() + str(row['Source_File']).lower()
    if 'arquitect' in text or 'construct' in text or 'desarrolladora' in text or 'estudio' in text:
        return True
    return False

master_df['Is_Architect_Constructor'] = master_df.apply(is_architect, axis=1)

# Inside T2: Products
def extract_products(row):
    tg = str(row['tags']).lower()
    ln = str(row['List_name_temp']).lower()
    sf = str(row['Source_File']).lower()
    desc = str(row['Description_temp']).lower()
    name = str(row['Nombre del lead']).lower()
    
    prods = set()
    
    # 1. Analyze Tags first
    if 'fv' in tg or 'fotovoltaico' in tg or ('solar' in tg and 'termotanque' not in tg and 'pileta' not in tg): 
        prods.add('Energia Solar FV')
    if 'pileta' in tg or 'climat' in tg: 
        prods.add('Climatizacion Piletas')
    if 'acs' in tg or 'agua caliente' in tg or 'termotanque' in tg: 
        prods.add('Termotanque Solar (ACS)')
    if 'biomasa' in tg: 
        prods.add('Biomasa')
    if 'calefacc' in tg and 'electrica' not in tg and 'eléctrica' not in tg and 'piso radiante' not in tg and 'pre' not in tg: 
        prods.add('Calefaccion (Tradicional/Otros)')
    if 'pre' in tg or 'piso radiante' in tg or 'calefaccion electrica' in tg or 'calefacción eléctrica' in tg:
        prods.add('PRE / Piso Radiante Electrico')
        
    # 2. Extract specific PRE numbering from Name (e.g. 61-Pto132-Name)
    if re.match(r'^\s*\d+\s*-', name):
        prods.add('PRE / Piso Radiante Electrico')
        
    # 3. Deep Analyze Descriptions & Names across Trello boards
    if 'trello' in sf:
        full_text = name + " " + desc
        if 'pileta' in full_text or 'colectores' in full_text or 'climatiza' in full_text: 
            prods.add('Climatizacion Piletas')
        if 'termotanque' in full_text or 'termo' in full_text or 'hissuma' in full_text or 'saiar' in full_text or 'heat pipe' in full_text or 'acs' in full_text: 
            prods.add('Termotanque Solar (ACS)')
        if 'nuke' in full_text or 'ñuke' in full_text or 'estufa' in full_text or 'biomasa' in full_text or 'tromen' in full_text: 
            prods.add('Biomasa')
        if 'fv' in full_text or 'fotovoltaico' in full_text or 'paneles' in full_text or 'inversor' in full_text: 
            prods.add('Energia Solar FV')
        if 'pre' in full_text or 'piso radiante' in full_text or 'malla' in full_text or 'cable calefactor' in full_text or 'termostato' in full_text: 
            prods.add('PRE / Piso Radiante Electrico')

    # 4. Analyze specific list names logic (NETrello / Kanban)
    if 'netrello' in sf:
        if ('pre' in ln and ('piso' in ln or 'terminados' in ln)) or 'piso radiante' in ln or 'radiante' in ln:
            prods.add('PRE / Piso Radiante Electrico')
        if 'nuke' in ln or 'ñuke' in ln:
            prods.add('Biomasa')
            
    # Remove contradictory tags if needed
    if 'PRE / Piso Radiante Electrico' in prods and 'Climatizacion Piletas' in prods:
        # We allow combos now! If they bought both, both stay
        pass

    result_list = sorted(list(prods))
    
    # Update global counters
    if len(result_list) == 0:
        product_counters['Sin Tag de Producto Claro'] += 1
    else:
        for p in result_list:
            if p in product_counters:
                product_counters[p] += 1
                
    return ", ".join(result_list) if result_list else 'Sin Tag de Producto Claro'

master_df['Products'] = master_df.apply(extract_products, axis=1)

# Inside T3: Active vs Inactive
def t3_status(row):
    if row['Category'] != 'T3': return ''
    st = str(row['Status']).lower()
    if st in ['todo', 'standby']: return 'Activo en Funnel'
    elif st in ['lost', 'cancelled']: return 'Inactivo'
    else: return 'Desconocido / Sin Estado'

master_df['T3_Status'] = master_df.apply(t3_status, axis=1)

# Inside T3 Inactive: Former Leads vs Cold Prospects
def t3_inactive_type(row):
    if row['T3_Status'] != 'Inactivo': return ''
    step = str(row['Step']).lower()
    cat_lead = str(row['Categoria Lead']).lower()
    
    advanced_steps = ['presupuesto', 'negociaci', 'propuesta', 'incubadora', 'vendido']
    hot_lead = ['caliente', 'tibio']
    
    if any(a in step for a in advanced_steps) or any(h in cat_lead for h in hot_lead):
        return 'Lead Anterior (Avanzado)'
    else:
        return 'Prospecto en Frio'

master_df['T3_Inactive_Type'] = master_df.apply(t3_inactive_type, axis=1)

# Split into 4 dataframes
df_t1 = master_df[master_df['Category'] == 'T1'].copy()
df_t2 = master_df[master_df['Category'] == 'T2'].copy()
df_t3 = master_df[master_df['Category'] == 'T3'].copy()
df_t4 = master_df[master_df['Category'] == 'T4'].copy()

# Save to excel
output_dir = r"c:\Users\agusi\OneDrive\Escritorio\AntiGr\Analisis comercial\Salida_BBDD"
os.makedirs(output_dir, exist_ok=True)

df_t1.to_excel(os.path.join(output_dir, "T1_B2C_NoCliente.xlsx"), index=False)
df_t2.to_excel(os.path.join(output_dir, "T2_B2C_Cliente.xlsx"), index=False)
df_t3.to_excel(os.path.join(output_dir, "T3_B2B_NoCliente.xlsx"), index=False)
df_t4.to_excel(os.path.join(output_dir, "T4_B2B_Cliente.xlsx"), index=False)

# Save the requested 2042 PRE clients
df_pre = master_df[master_df['Products'].str.contains('PRE / Piso Radiante Electrico')]
df_pre.to_excel(os.path.join(output_dir, "PRE_Piso_Radiante_Electrico.xlsx"), index=False)

# Write report
with open(os.path.join(output_dir, "reporte_analisis.txt"), "w", encoding="utf-8") as f:
    f.write("RESUMEN DE ANALISIS DE BASES DE DATOS\n")
    f.write("="*40 + "\n\n")
    
    f.write(f"Total Numeros de Celular / Telefono unicos: {len(all_phones)}\n")
    f.write(f"Total Correos Electronicos (Mails) unicos: {len(all_emails)}\n")
    f.write(f"Total Registros procesados (con posibles duplicados de nombres): {len(master_df)}\n\n")
    
    f.write("DISTRIBUCION POR CATEGORIA (T1 - T4):\n")
    f.write(f"- T1 (B2C No Cliente): {len(df_t1)}\n")
    f.write(f"- T2 (B2C Cliente): {len(df_t2)}\n")
    f.write(f"- T3 (B2B No Cliente): {len(df_t3)}\n")
    f.write(f"- T4 (B2B Cliente): {len(df_t4)}\n\n")
    
    f.write("DETALLE T1 (Arquitectos o Constructores):\n")
    arch_count = df_t1['Is_Architect_Constructor'].sum()
    f.write(f"- Arquitectos/Constructores dentro de T1: {arch_count}\n")
    f.write(f"- B2C Normal: {len(df_t1) - arch_count}\n\n")
    
    f.write("DETALLE T2 (Separacion por Productos - Contando Combos individualmente):\n")
    for prod, count in sorted(product_counters.items(), key=lambda x: x[1], reverse=True):
        f.write(f"- {prod}: {count}\n")
    
    f.write("\nDETALLE T2 (Agrupaciones Originales y Combos encontrados):\n")
    prod_counts = master_df[master_df['Category'] == 'T2']['Products'].value_counts()
    for prod, count in prod_counts.items():
        f.write(f"- {prod}: {count}\n")
    f.write("\n")
    
    f.write("DETALLE T3 (Status y Leads):\n")
    t3_status = df_t3['T3_Status'].value_counts()
    for st, count in t3_status.items():
        f.write(f"- {st}: {count}\n")
        
    f.write("\nDe los T3 Inactivos:\n")
    t3_inact = df_t3[df_t3['T3_Status'] == 'Inactivo']
    inact_counts = t3_inact['T3_Inactive_Type'].value_counts()
    for act_type, count in inact_counts.items():
        f.write(f"- {act_type}: {count}\n")
        
    f.write("\n========================================\n")
    f.write("OTROS DATOS DE INTERES (Insights):\n")
    motivos = master_df['Motivo Perdida'].replace('', np.nan).dropna().value_counts().head(5)
    f.write(f"Top 5 Motivos de Perdida generales:\n")
    for m, c in motivos.items():
        f.write(f"- {m}: {c}\n")
    
print("Proceso completado.")
