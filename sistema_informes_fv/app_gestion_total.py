# -*- coding: utf-8 -*-
"""
EDESA + Growatt + Informes - Gestión Total v3.0 COMPLETO
========================================================
Sistema completo de gestión mensual con validación de tarifas
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
import subprocess
import re

# Configuración de rutas
BASE_DIR = Path(__file__).parent
EDESA_DIR = BASE_DIR / "edesa_facturas" / "edesa_facturas"
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(EDESA_DIR))

class UnifiedApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gestión Total ZZZ [Ver. 3.0 COMPLETO] - Growatt & EDESA & Informes")
        self.root.geometry("950x800")
        
        self.is_running = False
        self.stop_requested = False
        
        # Contadores para estadísticas
        self.facturas_procesadas = 0
        self.informes_generados = 0
        self.tarifas_pdf = 0
        self.tarifas_cuadro = 0
        self.emails_enviados = 0
        self.alertas_criticas = []
        
        self.setup_ui()
        self.log("✅ Aplicación iniciada correctamente (v3.0 COMPLETO)")
        self.log("💡 Incluye: Validación de tarifas, Descarga automática, y Reportes finales")
        self.actualizar_info_cuadro()
        
    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        header = ttk.Label(main_frame, text="🚀 SISTEMA DE GESTIÓN TOTAL ZZZ v3.0", font=("Segoe UI", 16, "bold"))
        header.pack(pady=(0, 8))
        
        # FASE 0: PRE-PROCESO - Cuadro Tarifario
        pre_frame = ttk.LabelFrame(main_frame, text=" ⚙️ Fase 0: Verificación de Cuadro Tarifario ", padding="10")
        pre_frame.pack(fill=tk.X, pady=(0, 8))
        
        # Periodo y cuadro
        info_grid = ttk.Frame(pre_frame)
        info_grid.pack(fill=tk.X, pady=3)
        
        ttk.Label(info_grid, text="Periodo a procesar:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.periodo_var = tk.StringVar(value=self.obtener_periodo_anterior())
        periodo_combo = ttk.Combobox(info_grid, textvariable=self.periodo_var, state="readonly", width=12)
        periodo_combo['values'] = self.generar_lista_periodos()
        periodo_combo.grid(row=0, column=1, sticky=tk.W, padx=5)
        periodo_combo.bind('<<ComboboxSelected>>', lambda e: self.actualizar_info_cuadro())
        
        ttk.Label(info_grid, text="Cuadro tarifario:").grid(row=1, column=0, sticky=tk.W, padx=5)
        self.cuadro_periodo_label = ttk.Label(info_grid, text="Cargando...", font=("", 9, "bold"))
        self.cuadro_periodo_label.grid(row=1, column=1, sticky=tk.W, padx=5)
        self.cuadro_status_label = ttk.Label(info_grid, text="")
        self.cuadro_status_label.grid(row=1, column=2, sticky=tk.W, padx=3)
        
        # Botones de cuadro
        btn_cuadro = ttk.Frame(pre_frame)
        btn_cuadro.pack(fill=tk.X, pady=3)
        ttk.Button(btn_cuadro, text="🔄 Actualizar Cuadro", command=self.actualizar_cuadro_tarifario, width=18).pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_cuadro, text="📊 Ver PDF", command=self.ver_cuadro_descargado, width=12).pack(side=tk.LEFT)
        
        # FASES 1-3: CONFIG
        config_frame = ttk.LabelFrame(main_frame, text=" Configuración de Fases ", padding="12")
        config_frame.pack(fill=tk.X, pady=(0, 8))
        
        ttk.Label(config_frame, text="Seleccionar fases a ejecutar:").pack(anchor=tk.W, pady=(0, 5))
        
        phases_frame = ttk.Frame(config_frame)
        phases_frame.pack(fill=tk.X)
        
        self.do_growatt = tk.BooleanVar(value=True)
        ttk.Checkbutton(phases_frame, text="☀️ Fase 1: Growatt", variable=self.do_growatt).pack(side=tk.LEFT, padx=8)
        
        self.do_edesa = tk.BooleanVar(value=True)
        ttk.Checkbutton(phases_frame, text="📄 Fase 2: EDESA", variable=self.do_edesa).pack(side=tk.LEFT, padx=8)
        
        self.do_informes = tk.BooleanVar(value=True)
        ttk.Checkbutton(phases_frame, text="📊 Fase 3: Informes", variable=self.do_informes).pack(side=tk.LEFT, padx=8)
        
        self.do_emails = tk.BooleanVar(value=False)  # Por defecto desactivado para evitar envíos accidentales
        ttk.Checkbutton(phases_frame, text="📧 Fase 4: Emails", variable=self.do_emails).pack(side=tk.LEFT, padx=8)
        
        # Log
        self.log_text = scrolledtext.ScrolledText(main_frame, height=18, font=("Consolas", 9), bg="black", fg="white")
        self.log_text.pack(fill=tk.BOTH, expand=True, pady=8)
        
        # Progress
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, pady=5)
        
        # Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=8)
        
        self.start_btn = ttk.Button(btn_frame, text="▶ INICIAR PROCESO COMPLETO", command=self.start_task, width=30)
        self.start_btn.pack(side=tk.LEFT)
        
        ttk.Button(btn_frame, text="⏹ DETENER", command=self.stop_task).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="❌ Salir", command=self.root.quit).pack(side=tk.RIGHT)

    def log(self, message):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{ts}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def obtener_periodo_anterior(self):
        """Obtiene el periodo del mes anterior en formato 'mes YYYY'."""
        hoy = datetime.now()
        mes_anterior = hoy.replace(day=1) - timedelta(days=1)
        meses = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
        return f"{meses[mes_anterior.month - 1]} {mes_anterior.year}"

    def generar_lista_periodos(self):
        """Genera lista de periodos disponibles (últimos 6 meses)."""
        periodos = []
        meses = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
        hoy = datetime.now()
        
        for i in range(6):
            fecha = hoy.replace(day=1) - timedelta(days=30*i)
            periodos.append(f"{meses[fecha.month - 1]} {fecha.year}")
        
        return periodos

    def actualizar_info_cuadro(self):
        """Actualiza la información del cuadro tarifario en la UI."""
        try:
            from tarifa_edesa import PERIODO_CUADRO_TARIFARIO
            
            self.cuadro_periodo_label.config(text=PERIODO_CUADRO_TARIFARIO)
            
           # Verificar coincidencia
            if self.periodo_var.get() == PERIODO_CUADRO_TARIFARIO:
                self.cuadro_status_label.config(text="✅", foreground="green")
            else:
                self.cuadro_status_label.config(text="⚠️ No coincide", foreground="orange")
        except Exception as e:
            self.cuadro_periodo_label.config(text="Error al cargar")
            self.cuadro_status_label.config(text="❌", foreground="red")

    def actualizar_cuadro_tarifario(self):
        """Ejecuta script de descarga de cuadro tarifario en thread separado."""
        self.log("🔄 Iniciando descarga de cuadro tarifario...")
        self.log("   (Abrirá navegador automáticamente...)")
        
        def run_download():
            try:
                result = subprocess.run(
                    ["python", "descargar_cuadro_tarifario.py"],
                    capture_output=True,
                    text=True,
                    cwd=str(BASE_DIR)
                )
                
                # Mostrar output
                if result.stdout:
                    for line in result.stdout.strip().split('\n'):
                        self.log(f"   {line}")
                
                if result.returncode == 0:
                    self.log("✅ Descarga completada - Revisar downloads_tarifas/")
                    self.log("⚠️ Actualizar tarifa_edesa.py manualmente con los nuevos valores")
                    self.actualizar_info_cuadro()
                else:
                    self.log(f"❌ Error en descarga: {result.stderr}")
            except Exception as e:
                self.log(f"❌ Error ejecutando descarga: {e}")
        
        threading.Thread(target=run_download, daemon=True).start()

    def ver_cuadro_descargado(self):
        """Abre el PDF del cuadro tarifario descargado."""
        download_dir = BASE_DIR / "downloads_tarifas"
        if download_dir.exists():
            pdfs = list(download_dir.glob("*.pdf"))
            if pdfs:
                # Abrir el más reciente
                pdf_mas_reciente = max(pdfs, key=lambda p: p.stat().st_mtime)
                os.startfile(pdf_mas_reciente)
                self.log(f"📄 Abriendo: {pdf_mas_reciente.name}")
            else:
                self.log("⚠️ No hay PDFs descargados en downloads_tarifas/")
        else:
            self.log("⚠️ Carpeta downloads_tarifas/ no existe")

    def start_task(self):
        if self.is_running: return
        self.is_running = True
        self.stop_requested = False
        self.start_btn.config(state=tk.DISABLED)
        
        # Resetear contadores
        self.facturas_procesadas = 0
        self.informes_generados = 0
        self.tarifas_pdf = 0
        self.tarifas_cuadro = 0
        self.emails_enviados = 0
        self.alertas_criticas = []
        
        threading.Thread(target=self.work, daemon=True).start()

    def stop_task(self):
        self.stop_requested = True
        self.log("⚠️ Solicitando detención...")

    def work(self):
        try:
            periodo = self.periodo_var.get()
            self.log("="*60)
            self.log(f"INICIO PROCESO MENSUAL: {periodo}")
            self.log("="*60)
            
            # FASE 1: GROWATT
            if self.do_growatt.get() and not self.stop_requested:
                self.log("")
                self.log("🔹 Fase 1: Extrayendo Growatt (M\u00E9todo Robusto)...")
                
                try:
                    from growatt_integration import extraer_datos_growatt_auto
                    
                    exito = extraer_datos_growatt_auto(periodo, callback_log=self.log)
                    
                    if exito:
                        self.log("✅ Fase Growatt finalizada correctamente.")
                    else:
                        self.log("⚠️ Fase Growatt completada con advertencias.")
                except Exception as e:
                    self.log(f"❌ Error en Fase Growatt: {e}")

            # FASE 2: EDESA (CON TRACKING)
            if self.do_edesa.get() and not self.stop_requested:
                self.log("")
                self.log("🔹 Fase 2: Procesando EDESA...")
                
                sys.path.insert(0, str(EDESA_DIR))
                from descargar_facturas_MEJORADO import leer_planilla, descargar_factura, subir_a_drive
                from extractor_zzz import procesar_y_subir_factura
                import shutil
                
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
                                
                                # NUEVO: Capturar resultado para tracking
                                resultado = procesar_y_subir_factura(str(pdf))
                                if resultado:
                                    self.facturas_procesadas += 1
                                    self.log("  ✅ OK")
                        else:
                            self.log(f"  ❌ Error: {err}")
                    except Exception as e:
                        self.log(f"  ⚠️ Fallo técnico: {e}")
                    finally:
                        shutil.rmtree(tmp, ignore_errors=True)
                
                # Resumen de tarifas
                self.log("")
                self.log("📊 Validando calidad de extracción de tarifas...")
                try:
                    from tarifa_edesa import PERIODO_CUADRO_TARIFARIO
                    self.log(f"   Periodo del cuadro tarifario: {PERIODO_CUADRO_TARIFARIO}")
                    self.log(f"   Facturas procesadas: {self.facturas_procesadas}")
                    self.log("   ✓ Revisar logs arriba para alertas CRITICAS de periodo")
                except:
                    pass

            # FASE 3: INFORMES
            if self.do_informes.get() and not self.stop_requested:
                self.log("")
                self.log("🔹 Fase 3: Generando Informes HTML...")
                
                try:
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
                                'filepath': filepath,
                                'metricas': {
                                    'consumo_total': metricas['consumo_total'],
                                    'generacion': metricas['generacion_fv'],
                                    'ahorro_estimado': metricas['ahorro_mes']
                                }
                            })
                            self.informes_generados += 1
                        
                        if informes_generados and not self.stop_requested:
                            self.log("☁️ Publicando en GitHub Pages...")
                            publicar_en_github(informes_generados)
                            self.log(f"✅ Fase Informes finalizada: {len(informes_generados)} reportes publicados")
                        else:
                            self.log("⚠️ No se generaron informes para publicar")
                            
                except Exception as e:
                    self.log(f"❌ Error en Fase Informes: {e}")
                    import traceback
                    traceback.print_exc()

            # FASE 4: ENVÍO DE EMAILS
            if self.do_emails.get() and not self.stop_requested:
                self.log("")
                self.log("🔹 Fase 4: Enviando Emails a Clientes...")
                
                try:
                    from email_sender import enviar_emails_batch
                    
                    self.log("🔍 Obteniendo destinatarios desde Master_Clientes...")
                    
                    # Verificar que tenemos informes generados
                    if 'informes_generados' in locals() and informes_generados:
                        # Confirmar con el usuario antes de enviar
                        if messagebox.askyesno(
                            "Confirmar Envío de Emails",
                            f"¿Enviar {len(informes_generados)} emails a los clientes?\n\n"
                            f"Esto enviará los informes del periodo {periodo}.\n"
                            f"Asegúrate de haber configurado correctamente el archivo .env"
                        ):
                            self.log("📤 Iniciando envío de emails...")
                            
                            # Pasamos None en emails_clientes para que email_sender los cargue de Sheets
                            resultado = enviar_emails_batch(
                                informes=informes_generados,
                                emails_clientes=None,
                                callback_log=self.log
                            )
                            
                            self.emails_enviados = resultado['exitosos']
                            
                            self.log("")
                            self.log(f"✅ Emails enviados: {resultado['exitosos']}")
                            self.log(f"❌ Emails fallidos: {resultado['fallidos']}")
                            
                            # Mostrar detalles de fallidos
                            if resultado['fallidos'] > 0:
                                self.log("")
                                self.log("⚠️ Detalles de envíos fallidos:")
                                for detalle in resultado['detalles']:
                                    if not detalle['exito']:
                                        self.log(f"   - {detalle['cliente']}: {detalle.get('error', detalle.get('mensaje'))}")
                        else:
                            self.log("⏸️ Envío de emails cancelado por el usuario")
                    else:
                        self.log("⚠️ No hay informes generados para enviar por email")
                        self.log("   Activar Fase 3: Informes primero")
                        
                except ImportError:
                    self.log("❌ Error: Instalar dependencias con: pip install python-dotenv")
                except Exception as e:
                    self.log(f"❌ Error en Fase Emails: {e}")
                    import traceback
                    traceback.print_exc()

            # FASE 5: VALIDACIÓN FINAL Y RESUMEN
            if not self.stop_requested:
                self.log("")
                self.log("="*60)
                self.log("✅ FASE 4: VALIDACIÓN FINAL Y RESUMEN")
                self.log("="*60)
                
                self.log(f"\n📊 Estadísticas del proceso:")
                self.log(f"   Facturas procesadas: {self.facturas_procesadas}")
                self.log(f"   Informes generados: {self.informes_generados}")
                self.log(f"   Emails enviados: {self.emails_enviados}")
                
                self.log("\n🌐 Próximos pasos:")
                if self.emails_enviados > 0:
                    self.log("   1. ✅ Emails enviados a clientes")
                    self.log("   2. Verificar que los clientes recibieron los emails")
                    self.log("   3. Revisar si hay alertas CRÍTICAS arriba")
                else:
                    self.log("   1. Verificar informes en GitHub Pages")
                    self.log("   2. Revisar si hay alertas CRÍTICAS arriba")
                    self.log("   3. Activar Fase 4 para enviar emails automáticamente")
                
                self.log("")
                self.log("="*60)
                self.log("🎉 PROCESO MENSUAL COMPLETADO")
                self.log("="*60)
            
            messagebox.showinfo("Proceso Completo", 
                               f"✅ Proceso finalizado con éxito\n\n"
                               f"Facturas: {self.facturas_procesadas}\n"
                               f"Informes: {self.informes_generados}\n"
                               f"Emails: {self.emails_enviados}")
            
        except Exception as ex:
            self.log(f"❌ ERROR CRÍTICO: {ex}")
            import traceback
            traceback.print_exc()
        finally:
            self.is_running = False
            self.start_btn.config(state=tk.NORMAL)
            self.progress_var.set(0)

if __name__ == "__main__":
    root = tk.Tk()
    app = UnifiedApp(root)
    root.mainloop()
