import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os, json, re, threading
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except:
    GEMINI_AVAILABLE = False
try:
    from pdf2image import convert_from_path
    import pytesseract
    from PIL import Image, ImageEnhance, ImageFilter
    PDF2IMAGE_AVAILABLE = True
except:
    PDF2IMAGE_AVAILABLE = False
class InterpretadorGemini:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model = None
        self.banco_detectado = "desconocido"
        self.movimientos = []
        if self.api_key and GEMINI_AVAILABLE:
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel('gemini-2.0-flash')
            except: pass
    
    def detectar_banco(self, texto):
        texto_upper = texto.upper()
        bancos = {"macro": ["MACRO"], "galicia": ["GALICIA"], "bbva": ["BBVA"], "santander": ["SANTANDER"]}
        for banco, kws in bancos.items():
            if any(k in texto_upper for k in kws): return banco
        return "desconocido"
    
    def extraer_texto_pdf(self, pdf_path):
        if not PDF2IMAGE_AVAILABLE: return ""
        try:
            poppler = r"C:\Users\Gonza\Downloads\poppler-25.12.0\Library\bin"
            tesseract = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
            pytesseract.pytesseract.tesseract_cmd = tesseract
            images = convert_from_path(pdf_path, dpi=300, poppler_path=poppler)
            texto = ""
            for i, img in enumerate(images, 1):
                gray = img.convert('L')
                enhanced = ImageEnhance.Contrast(gray).enhance(2.0)
                txt = pytesseract.image_to_string(enhanced, config='--oem 3 --psm 6 -l spa+eng')
                texto += f"---PAG{i}---\n{txt}\n"
            return texto
        except: return ""
    
    def generar_prompt_mejorado(self, banco: str) -> str:
        return f"""Eres experto en transcribir resúmenes de tarjetas de crédito de bancos argentinos.

BANCO: {banco.upper()}

Tu tarea es extraer TODOS los movimientos del resumen en formato de tabla.

REGLAS ESTRICTAS:
1. Lee el PDF y extrae TODOS los consumos, pagos, cuotas e impuestos
2. Presenta en formato tabla Markdown
3. Columnas: Fecha | Comercio | Nro Cupón | Cuota | Importe ($) | Importe (US$)
4. Si hay múltiples titulares, crea tabla separada para cada uno con totales
5. Sección de Pagos: saldo anterior, pagos realizados
6. Sección de Impuestos: comisiones, IVA, intereses
7. Ignora: avisos legales, publicidades, tasas, límites

FORMATO DE SALIDA:
### Consumos [Nombre Titular]
| Fecha | Comercio | Nro. Cupón | Cuota | Importe ($) | Importe (US$) |
|---|---|---|---|---|---|
| ... | ... | ... | ... | ... | ... |
| **Total** | | | | **SUMA** | **SUMA** |

### Pagos
| Fecha | Concepto | Importe ($) | Importe (US$) |
|---|---|---|---|
| ... | ... | ... | ... |

### Impuestos y Comisiones
| Fecha | Concepto | Importe ($) |
|---|---|---|
| ... | ... | ... |

Responde SOLO con las tablas, sin texto adicional."""

    def interpretar(self, texto, callback=None):
        self.banco_detectado = self.detectar_banco(texto)
        
        prompt = self.generar_prompt_mejorado(self.banco_detectado)
        
        if not self.model:
            return self._local(texto)
        
        try:
            full_prompt = f"{prompt}\n\n--- TEXTO EXTRAIDO DEL PDF ---\n{texto[:15000]}\n---"
            resp = self.model.generate_content(full_prompt)
            
            # Intentar parsear la respuesta como JSON también
            match = re.search(r'\[[\s\S]*\]', resp.text)
            if match:
                self.movimientos = json.loads(match.group(0))
                return self.movimientos
            
            # Si no hay JSON, parsear las tablas Markdown
            self.movimientos = self._parsear_markdown(resp.text)
            return self.movimientos
            
        except Exception as e:
            print(f"Error Gemini: {e}")
            return self._local(texto)
    
    def _parsear_markdown(self, texto_markdown: str) -> list:
        """Parsea las tablas markdown devueltas por Gemini"""
        movimientos = []
        lines = texto_markdown.split('\n')
        
        # Estados: consumos, pagos, impuestos
        seccion_actual = "consumos"
        
        for line in lines:
            line = line.strip()
            
            # Detectar sección
            if "### Pagos" in line or "PAGOS" in line.upper():
                seccion_actual = "pagos"
                continue
            elif "### Impuestos" in line or "IMPUESTOS" in line.upper():
                seccion_actual = "impuestos"
                continue
            elif "### Consumos" in line:
                seccion_actual = "consumos"
                continue
            
            # Saltar encabezados de tabla
            if line.startswith('|') and '---' in line:
                continue
            
            # Parsear filas de tabla
            if line.startswith('|') and not line.startswith('| :'):
                parts = [p.strip() for p in line.split('|')[1:-1]]
                
                if len(parts) >= 4:
                    fecha = parts[0] if parts[0] else ""
                    comercio = parts[1] if len(parts) > 1 else ""
                    cupon = parts[2] if len(parts) > 2 else ""
                    cuota = parts[3] if len(parts) > 3 else ""
                    
                    monto_ars = 0
                    monto_usd = 0
                    
                    if len(parts) > 4 and parts[4]:
                        try:
                            monto_ars = float(parts[4].replace('.', '').replace(',', '.').replace('$', '').replace('*', ''))
                        except:
                            pass
                    
                    if len(parts) > 5 and parts[5]:
                        try:
                            monto_usd = float(parts[5].replace('.', '').replace(',', '.').replace('US$', '').replace('*', ''))
                        except:
                            pass
                    
                    # Ignorar filas de totales
                    if 'total' in comercio.lower() or 'total' in fecha.lower():
                        continue
                    
                    if monto_ars > 0 or monto_usd > 0:
                        tipo = "pago" if seccion_actual == "pagos" else "impuesto" if seccion_actual == "impuestos" else "compra"
                        
                        movimientos.append({
                            "fecha": fecha,
                            "descripcion": comercio,
                            "cupon": cupon,
                            "cuotas": cuota if cuota and '/' in cuota else "",
                            "monto_ars": monto_ars,
                            "monto_usd": monto_usd,
                            "tipo": tipo,
                            "seccion": seccion_actual
                        })
        
        return movimientos
    
    def _local(self, texto):
        movs = []
        seccion = "consumos"
        for line in texto.split('\n'):
            line = line.strip()
            if len(line) < 10: continue
            
            if "PAGOS" in line.upper() and len(line) < 20:
                seccion = "pagos"
                continue
            if "IMPUESTO" in line.upper() or "COMISION" in line.upper():
                seccion = "impuestos"
                continue
            if "CONSUMOS" in line.upper():
                seccion = "consumos"
                continue
                
            skip = ['RESUMEN', 'TOTAL', 'SALDO', 'IVA', 'SUBTOTAL', 'VISA', 'MASTERCARD']
            if any(t in line.upper() for t in skip): continue
            
            m = re.search(r'(\d{1,5}[.,]\d{2})', line)
            if not m: continue
            try: 
                monto = float(m.group(1).replace(',','.'))
            except: continue
            
            fecha = re.search(r'(\d{1,2}[/\-]\d{1,2})', line)
            tipo = "pago" if seccion == "pagos" else "impuesto" if seccion == "impuestos" else "compra"
            
            # Buscar cuotas
            cuotas_match = re.search(r'(\d+)\s*/\s*(\d+)', line)
            cuotas = f"{cuotas_match.group(1)}/{cuotas_match.group(2)}" if cuotas_match else ""
            
            # Buscar cupón
            cupon_match = re.search(r'\b(\d{6})\b', line)
            cupon = cupon_match.group(1) if cupon_match else ""
            
            desc = line
            if fecha: desc = desc.replace(fecha.group(0), '')
            desc = re.sub(r'\d{1,5}[.,]\d{2}\s*$', '', desc).strip()
            desc = re.sub(r'^[MERPAGO\*|MP\*|\*]+', '', desc).strip()
            
            if monto > 0 and len(desc) > 3:
                movs.append({
                    "fecha": fecha.group(1) if fecha else "",
                    "descripcion": desc[:80],
                    "cupon": cupon,
                    "cuotas": cuotas,
                    "monto_ars": monto,
                    "monto_usd": 0,
                    "tipo": tipo,
                    "seccion": seccion,
                    "categoria": "otros"
                })
        
        self.movimientos = movs
        return movs
    
    def exportar(self, path):
        with open(path, 'w', encoding='utf-8') as f:
            json.dump({"banco":self.banco_detectado, "fecha":datetime.now().isoformat(), "movimientos":self.movimientos}, f, indent=2)
class GUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Interpretador Gemini")
        self.geometry("900x600")
        self.int = InterpretadorGemini()
        self._ui()
    
    def _ui(self):
        main = ttk.Frame(self, padding=10)
        main.pack(fill=tk.BOTH, expand=True)
        ttk.Label(main, text="INTERPRETADOR DE RESUMENES - GEMINI", font=("Arial",12,"bold")).pack(pady=10)
        
        btns = ttk.Frame(main)
        btns.pack(pady=5)
        ttk.Button(btns, text="PDF", command=self.sel).pack(side=tk.LEFT, padx=5)
        self.btnProc = ttk.Button(btns, text="Procesar", command=self.proc, state=tk.DISABLED)
        self.btnProc.pack(side=tk.LEFT, padx=5)
        self.btnExp = ttk.Button(btns, text="Exportar", command=self.exp, state=tk.DISABLED)
        self.btnExp.pack(side=tk.LEFT, padx=5)
        
        self.info = ttk.Label(main, text="Banco: --- | Mov: 0 | Total: $0")
        self.info.pack()
        
        cols = ("f","d","c","cuota","monto","seccion")
        self.tree = ttk.Treeview(main, columns=cols, show="headings")
        self.tree.heading("f", text="Fecha")
        self.tree.heading("d", text="Comercio")
        self.tree.heading("c", text="Cupón")
        self.tree.heading("cuota", text="Cuota")
        self.tree.heading("monto", text="Importe")
        self.tree.heading("seccion", text="Sección")
        
        self.tree.column("f", width=70)
        self.tree.column("d", width=250)
        self.tree.column("c", width=70)
        self.tree.column("cuota", width=60)
        self.tree.column("monto", width=100)
        self.tree.column("seccion", width=80)
        
        scroll = ttk.Scrollbar(main, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scroll.set)
        self.tree.pack(fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.status = ttk.Label(main, text="Listo")
        self.status.pack()
    
    def sel(self):
        p = filedialog.askopenfilename(filetypes=[("PDF","*.pdf")])
        if p:
            self.pdf = p
            self.btnProc.config(state=tk.NORMAL)
            self.status.config(text=f"Listo: {os.path.basename(p)}")
    
    def proc(self):
        self.btnProc.config(state=tk.DISABLED)
        self.status.config(text="Procesando...")
        def go():
            txt = self.int.extraer_texto_pdf(self.pdf)
            movs = self.int.interpretar(txt)
            self.after(0, lambda: self._show(movs))
        threading.Thread(target=go, daemon=True).start()
    
    def _show(self, movs):
        for i in self.tree.get_children(): self.tree.delete(i)
        
        total = 0
        for m in movs:
            monto = m.get('monto_ars', 0) or 0
            total += monto
            self.tree.insert("", tk.END, values=(
                m.get("fecha",""), 
                m.get("descripcion","")[:45], 
                m.get("cupon",""),
                m.get("cuotas",""),
                f"${monto:,.0f}",
                m.get("seccion", m.get("tipo",""))
            ))
        
        self.info.config(text=f"Banco: {self.int.banco_detectado} | Mov: {len(movs)} | Total: ${total:,.0f}")
        self.btnExp.config(state=tk.NORMAL)
        self.status.config(text=f"✓ {len(movs)} movimientos extraídos")
    
    def exp(self):
        p = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON","*.json")])
        if p: self.int.exportar(p); messagebox.showinfo("OK","Guardado")
if __name__ == "__main__": GUI().mainloop()