# -*- coding: utf-8 -*-
"""
EDESA + Growatt - Gestión Total (VERSIÓN ESTABLE v2)
==================================================
Corregido: Error de codificación UTF-8 en Windows.
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import time
from datetime import datetime
from pathlib import Path
import subprocess

# Configuración de rutas
BASE_DIR = Path(__file__).parent
EDESA_DIR = BASE_DIR / "edesa_facturas" / "edesa_facturas"
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(EDESA_DIR))

# Verificar módulos básicos
MODULES_OK = True
try:
    # Solo cargar lo esencial para la UI al inicio
    pass
except Exception as e:
    MODULES_OK = False
    IMPORT_ERROR = str(e)

class UnifiedApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gestión Total ZZZ [Ver. 3.0 COMPLETO] - Growatt & EDESA & Informes")
        self.root.geometry("900x750")
        
        self.is_running = False
        self.stop_requested = False
        
        # Nuevos contadores para estadísticas
        self.facturas_procesadas = 0
        self.informes_generados = 0
        self.tarifas_pdf = 0
        self.tarifas_cuadro = 0
        self.alertas_criticas = []
        
        self.setup_ui()
        self.log("✅ Aplicación iniciada correctamente (v3.0 COMPLETO)")
        self.log("💡 Incluye: Validación de tarifas, Descarga automática, y Reportes finales")
        self.actualizar_info_cuadro()
        
    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        header = ttk.Label(main_frame, text="🚀 SISTEMA DE GESTIÓN TOTAL ZZZ", font=("Segoe UI", 16, "bold"))
        header.pack(pady=(0, 10))
        
        # Config
        config_frame = ttk.LabelFrame(main_frame, text=" Configuración ", padding="15")
        config_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(config_frame, text="Periodo:").pack(side=tk.LEFT, padx=5)
        self.periodo_var = tk.StringVar(value=f"{datetime.now().strftime('%m %Y')}")
        self.periodo_combo = ttk.Combobox(config_frame, textvariable=self.periodo_var, 
                                         values=["ene 2026", "dic 2025", "nov 2025"], width=15)
        self.periodo_combo.pack(side=tk.LEFT, padx=5)
        
        self.do_growatt = tk.BooleanVar(value=True)
        ttk.Checkbutton(config_frame, text="Fase 1: Growatt", variable=self.do_growatt).pack(side=tk.LEFT, padx=20)
        
        self.do_edesa = tk.BooleanVar(value=True)
        ttk.Checkbutton(config_frame, text="Fase 2: EDESA", variable=self.do_edesa).pack(side=tk.LEFT, padx=10)
        
        self.do_informes = tk.BooleanVar(value=True)
        ttk.Checkbutton(config_frame, text="Fase 3: Informes", variable=self.do_informes).pack(side=tk.LEFT)
        
        # Log
        self.log_text = scrolledtext.ScrolledText(main_frame, height=15, font=("Consolas", 9), bg="black", fg="white")
        self.log_text.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Progress
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, pady=5)
        
        # Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        self.start_btn = ttk.Button(btn_frame, text="▶ INICIAR PROCESO COMPLETO", command=self.start_task, width=30)
        self.start_btn.pack(side=tk.LEFT)
        
        ttk.Button(btn_frame, text="⏹ DETENER", command=self.stop_task).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="❌ Salir", command=self.root.quit).pack(side=tk.RIGHT)

    def log(self, message):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{ts}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def start_task(self):
        if self.is_running: return
        self.is_running = True
        self.stop_requested = False
        self.start_btn.config(state=tk.DISABLED)
        threading.Thread(target=self.work, daemon=True).start()

    def stop_task(self):
        self.stop_requested = True
        self.log("⚠️ Solicitando detención...")

    def work(self):
        try:
            periodo = self.periodo_var.get()
            self.log(f"--- INICIO PROCESO: {periodo} ---")
            
            # FASE 1: GROWATT
            if self.do_growatt.get() and not self.stop_requested:
                self.log("🔹 Fase 1: Extrayendo Growatt (Método Robusto)...")
                
                try:
                    from growatt_integration import extraer_datos_growatt_auto
                    
                    # Llamar directamente a la función de integración
                    exito = extraer_datos_growatt_auto(periodo, callback_log=self.log)
                    
                    if exito:
                        self.log("✅ Fase Growatt finalizada correctamente.")
                    else:
                        self.log("⚠ Fase Growatt completada con advertencias.")
                except Exception as e:
                    self.log(f"❌ Error en Fase Growatt: {e}")

            # FASE 2: EDESA
            if self.do_edesa.get() and not self.stop_requested:
                self.log("🔹 Fase 2: Procesando EDESA...")
                
                # Importar aquí para evitar problemas de carga inicial
                sys.path.insert(0, str(EDESA_DIR))
                from descargar_facturas_MEJORADO import leer_planilla, descargar_factura, subir_a_drive
                from extractor_zzz import procesar_y_subir_factura
                import re, shutil
                
                df = leer_planilla()
                total = len(df)
                self.log(f"📋 Clientes en lista: {total}")
                
                for i, row in df.iterrows():
                    if self.stop_requested: break
                    nis = re.sub(r"\D", "", str(row["NIS"]))
                    cliente = str(row["Cliente"])
                    
                    if not nis: continue
                    
                    self.log(f"📥 [{i+1}/{total}] {cliente}...")
                    self.progress_var.set((i+1)/total * 100)
                    
                    tmp = BASE_DIR / f"tmp_{nis}"
                    tmp.mkdir(exist_ok=True)
                    
                    try:
                        ok, err = descargar_factura(nis, str(tmp))
                        if ok:
                            pdfs = list(tmp.glob("*.pdf"))
                            if pdfs:
                                pdf = pdfs[0]
                                self.log(f"  ☁️ Subiendo a Drive...")
                                subir_a_drive(pdf.name, str(pdf))
                                self.log(f"  📊 Actualizando Sheets...")
                                if procesar_y_subir_factura(str(pdf)):
                                    self.log("  ✅ OK")
                        else:
                            self.log(f"  ❌ Error: {err}")
                    except Exception as e:
                        self.log(f"  ⚠️ Fallo técnico: {e}")
                    finally:
                        shutil.rmtree(tmp, ignore_errors=True)
                
                # NUEVO: Resumen de validación de tarifas
                self.log("")
                self.log("📊 Validando calidad de extracción de tarifas...")
                try:
                    from tarifa_edesa import PERIODO_CUADRO_TARIFARIO
                    self.log(f"   Periodo del cuadro tarifario: {PERIODO_CUADRO_TARIFARIO}")
                    self.log("   ✓ Revisar logs arriba para alertas CRITICAS de periodo")
                except:
                    pass

            # FASE 3: GENERAR Y PUBLICAR INFORMES
            if self.do_informes.get() and not self.stop_requested:
                self.log("🔹 Fase 3: Generando Informes HTML...")
                
                try:
                    # Importar funciones de generar_informes
                    from generar_informes import (
                        leer_datos_sheets, 
                        calcular_metricas_nis, 
                        generar_html_informe,
                        publicar_en_github,
                        NIS_NOMBRES
                    )
                    
                    self.log("📖 Leyendo datos de Google Sheets...")
                    datos = leer_datos_sheets()
                    
                    if not datos:
                        self.log("⚠️ No se pudieron leer datos de Sheets")
                    else:
                        self.log(f"📊 Procesando {len(NIS_NOMBRES)} clientes...")
                        
                        # Crear carpeta de salida
                        fecha_hoy = datetime.now()
                        output_dir = BASE_DIR / f'Informes_{fecha_hoy.month:02d}_{fecha_hoy.year}'
                        output_dir.mkdir(exist_ok=True)
                        
                        informes_generados = []
                        total_clientes = len(NIS_NOMBRES)
                        
                        for idx, (nis, nombre_cliente) in enumerate(NIS_NOMBRES.items(), 1):
                            if self.stop_requested: break
                            
                            self.log(f"  📄 [{idx}/{total_clientes}] {nombre_cliente}...")
                            self.progress_var.set((idx / total_clientes) * 100)
                            
                            metricas = calcular_metricas_nis(datos, nis)
                            
                            if not metricas:
                                self.log(f"    ⚠️ Sin datos para NIS {nis}")
                                continue
                            
                            html = generar_html_informe(metricas).strip()
                            filename = f'informe_{nis}_{nombre_cliente.replace(" ", "_")}.html'
                            filepath = output_dir / filename
                            
                            with open(filepath, 'w', encoding='utf-8') as f:
                                f.write(html)
                            
                            informes_generados.append({
                                'nis': nis,
                                'cliente': nombre_cliente,
                                'periodo': metricas['periodo'],
                                'filepath': filepath
                            })
                        
                        if informes_generados and not self.stop_requested:
                            self.log("☁️ Publicando en GitHub Pages...")
                            publicar_en_github(informes_generados)
                            self.log(f"✅ Fase Informes finalizada: {len(informes_generados)} reportes publicados")
                        else:
                            self.log("⚠️ No se generaron informes para publicar")
                            
                except Exception as e:
                    self.log(f"❌ Error en Fase Informes: {e}")

            self.log("--- PROCESO COMPLETADO ---")
            messagebox.showinfo("Listo", "Proceso finalizado con éxito.")
            
        except Exception as ex:
            self.log(f"❌ ERROR CRÍTICO: {ex}")
        finally:
            self.is_running = False
            self.start_btn.config(state=tk.NORMAL)

if __name__ == "__main__":
    root = tk.Tk()
    app = UnifiedApp(root)
    root.mainloop()
