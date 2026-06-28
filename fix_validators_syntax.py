#!/usr/bin/env python3
"""Arregla la sintaxis de validators.py"""

content = """# src/utils/validators.py

def validar_goles(valor):
    \"\"\"
    Convierte un valor a entero positivo.
    Si el valor es None, negativo, o no convertible, devuelve 0.
    \"\"\"
    try:
        v = float(valor)
        if v < 0:
            return 0
        return int(v)
    except (ValueError, TypeError):
        return 0


def to_int(valor):
    \"\"\"
    Convierte cualquier valor a entero.
    CRÍTICO: Evita el error 'invalid input syntax for type integer: \"-2.0\"'
    
    Maneja floats, strings, None, negativos, etc.
    Siempre devuelve un int válido para Supabase.
    
    Args:
        valor: Cualquier valor (float, string, int, None, etc.)
    
    Returns:
        int: Valor convertido a entero (si falla, devuelve 0)
    \"\"\"
    try:
        # Convertir a float primero (maneja strings como \"-2.0\")
        # Luego a int para eliminar decimales
        return int(float(valor))
    except (ValueError, TypeError):
        # Si algo falla, devolver 0 (valor seguro para BD)
        return 0
"""

with open('utils/validators.py', 'w', encoding='utf8') as f:
    f.write(content)

print("✅ validators.py arreglado")
