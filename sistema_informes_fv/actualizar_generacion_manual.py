# -*- coding: utf-8 -*-
"""
Script para actualizar manualmente los valores de generación conocidos
"""

import pandas as pd
from pathlib import Path

def actualizar_generacion_manual():
    """Actualiza los valores de generación que conocemos son incorrectos."""
    
    csv_path = Path("growatt_generacion_mensual_202601.csv")
    
    if not csv_path.exists():
        print(f"ERROR: No se encontró {csv_path}")
        return
    
    # Leer CSV
    df = pd.read_csv(csv_path)
    
    print("Actualizando valores de generación conocidos...\n")
    
    # Valores a actualizar (según información del usuario)
    actualizaciones = {
        "distribuidora maestro": 808.8,  # Usuario confirmó este valor
        "Claudia tolaba": 1931.65,  # Usuario confirmó - imagen Growatt
        # Agregar más según vayamos confirmando
    }
    
    for planta_nombre, nueva_generacion in actualizaciones.items():
        # Buscar la planta
        mask = df['Plant Name'].str.lower() == planta_nombre.lower()
        
        if mask.any():
            valor_anterior = df.loc[mask, 'Generacion_Mensual_kWh'].values[0]
            df.loc[mask, 'Generacion_Mensual_kWh'] = nueva_generacion
            
            print(f"OK {planta_nombre}")
            print(f"  Anterior: {valor_anterior} kWh")
            print(f"  Nuevo: {nueva_generacion} kWh")
            print()
        else:
            print(f"ERROR No se encontro: {planta_nombre}")
            print()
    
    # Guardar CSV actualizado
    backup_path = csv_path.with_suffix('.csv.backup')
    if backup_path.exists():
        backup_path.unlink()  # Eliminar backup anterior
    csv_path.rename(backup_path)
    print(f"Backup creado: {backup_path}")
    
    df.to_csv(csv_path, index=False)
    print(f"CSV actualizado: {csv_path}")
    
    # Mostrar resumen
    print("\n" + "=" * 80)
    print("RESUMEN DE GENERACION ACTUALIZADA")
    print("=" * 80)
    
    total_gen = df['Generacion_Mensual_kWh'].sum()
    plantas_activas = len(df[df['Generacion_Mensual_kWh'] > 0])
    
    print(f"Total plantas: {len(df)}")
    print(f"Plantas con generación: {plantas_activas}")
    print(f"Generación total: {total_gen:,.2f} kWh")
    print()


if __name__ == "__main__":
    actualizar_generacion_manual()
