# -*- coding: utf-8 -*-
"""
Test unitario para la función sanitizar_url
Verifica que nunca retorne strings vacíos o nombres de archivo inválidos
"""

import sys
from pathlib import Path

# Agregar path del proyecto
sys.path.insert(0, str(Path(__file__).parent))

from generar_informes import sanitizar_url


def test_sanitizar_url_empty_input():
    """Probar que entradas vacías retornan string vacío"""
    print("Test 1: Entradas vacias...")
    assert sanitizar_url("") == "", "String vacio debe retornar vacio"
    assert sanitizar_url("   ") == "", "String con espacios debe retornar vacio"
    assert sanitizar_url(None) == "", "None debe retornar vacio"
    print("  [OK] Paso")


def test_sanitizar_url_special_chars_only():
    """Probar que caracteres especiales únicamente retornan string vacío"""
    print("Test 2: Solo caracteres especiales...")
    assert sanitizar_url("@#$%") == "", "Caracteres especiales deben retornar vacío"
    assert sanitizar_url("...") == "", "Solo puntos debe retornar vacío"
    assert sanitizar_url("---") == "", "Solo guiones debe retornar vacío (se eliminan en strip)"
    assert sanitizar_url("   ...   ") == "", "Espacios + puntos debe retornar vacío"
    print("  [OK] Paso")


def test_sanitizar_url_valid_input():
    """Probar conversiones válidas"""
    print("Test 3: Entradas validas...")
    assert sanitizar_url("Dic-2025") == "dic-2025", "Dic-2025 debe convertirse a dic-2025"
    assert sanitizar_url("Cliente ABC") == "cliente-abc", "Espacios deben convertirse a guiones"
    assert sanitizar_url("Año 2026") == "ano-2026", "Ñ debe convertirse a n"
    assert sanitizar_url("José María") == "jose-maria", "Acentos deben eliminarse"
    print("  [OK] Paso")


def test_sanitizar_url_no_extension_only():
    """Probar que nunca retorna solo una extensión (ej: .html)"""
    print("Test 4: Prevenir extensiones solas...")
    # Si el input sanitizado resultaría en algo que empieza con punto, debe retornar vacío
    assert sanitizar_url(".") == "", "Solo punto debe retornar vacío"
    assert sanitizar_url("..") == "", "Puntos múltiples debe retornar vacío"
    # Casos edge que podrían resultar en .algo después de sanitización
    assert not sanitizar_url("@#$").startswith('.'), "No debe empezar con punto"
    print("  [OK] Paso")


def test_sanitizar_url_combined_cases():
    """Probar casos combinados reales"""
    print("Test 5: Casos combinados...")
    
    # Caso real: periodo vacío en Google Sheets
    assert sanitizar_url("") == ""
    
    # Caso real: solo espacios/tabs
    assert sanitizar_url("  \t  ") == ""
    
    # Caso real: caracteres especiales mezclados con texto
    resultado = sanitizar_url("Período: Dic-2025")
    assert resultado != "", "Debe extraer la parte válida"
    assert not resultado.startswith('.'), "No debe empezar con punto"
    
    print("  [OK] Paso")


if __name__ == "__main__":
    print("="*60)
    print("EJECUTANDO TESTS UNITARIOS - sanitizar_url()")
    print("="*60)
    print()
    
    try:
        test_sanitizar_url_empty_input()
        test_sanitizar_url_special_chars_only()
        test_sanitizar_url_valid_input()
        test_sanitizar_url_no_extension_only()
        test_sanitizar_url_combined_cases()
        
        print()
        print("="*60)
        print("[SUCCESS] TODOS LOS TESTS PASARON")
        print("="*60)
        
    except AssertionError as e:
        print()
        print("="*60)
        print(f"[FAIL] TEST FALLO: {e}")
        print("="*60)
        sys.exit(1)
