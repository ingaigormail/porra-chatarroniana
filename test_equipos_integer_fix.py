#!/usr/bin/env python3
"""
Test de validación: Verifica que la función to_int() convierte correctamente
los valores flotantes a enteros.

OBJETIVO: Confirmar que no obtenemos "invalid input syntax for type integer: -2.0"
"""

import sys
sys.path.insert(0, '.')

from utils.validators import to_int

print("="*70)
print("TEST: Validación de la función to_int()")
print("="*70)

# Test cases
test_cases = [
    # (valor_entrada, valor_esperado, descripción)
    (-2.0, -2, "Float negativo"),
    (2.0, 2, "Float positivo"),
    (0.0, 0, "Float cero"),
    ("-2.0", -2, "String negativo con decimal"),
    ("2", 2, "String positivo"),
    (3, 3, "Int"),
    (None, 0, "None"),
    ("abc", 0, "String no numérico"),
    (3.7, 3, "Float con decimales (trunca)"),
    (-3.7, -3, "Float negativo con decimales (trunca)"),
]

all_pass = True

for entrada, esperado, descripcion in test_cases:
    resultado = to_int(entrada)
    estado = "✅ PASS" if resultado == esperado else "❌ FAIL"
    
    if resultado != esperado:
        all_pass = False
    
    print(f"{estado}: {descripcion}")
    print(f"       Entrada: {entrada!r} ({type(entrada).__name__})")
    print(f"       Esperado: {esperado}")
    print(f"       Obtenido: {resultado}")
    print()

print("="*70)
if all_pass:
    print("✅ TODOS LOS TESTS PASARON")
    print("\nLa función to_int() está lista para prevenir:")
    print("  'invalid input syntax for type integer: -2.0'")
else:
    print("❌ ALGUNOS TESTS FALLARON")

print("="*70)

# Test de diccionario (como se envía a Supabase)
print("\nTEST 2: Diccionario completo (como se envía a Supabase)")
print("="*70)

# Simular datos de un equipo con diferencia negativa
datos_simulados = {
    'pj': 5.0,
    'ganados': 2.0,
    'empatados': 1.0,
    'perdidos': 2.0,
    'gf': 8.0,
    'gc': 10.0,  # Perdieron 8-10, dg = -2
    'dg': -2.0,  # ← ESTO CAUSABA EL ERROR
    'puntos': 7.0
}

print("Datos sin limpiar (como vienen de los cálculos):")
print(datos_simulados)
print()

# Aplicar limpieza (como hace el código actualizado)
data_limpiado = {
    'pj': to_int(datos_simulados['pj']),
    'ganados': to_int(datos_simulados['ganados']),
    'empatados': to_int(datos_simulados['empatados']),
    'perdidos': to_int(datos_simulados['perdidos']),
    'gf': to_int(datos_simulados['gf']),
    'gc': to_int(datos_simulados['gc']),
    'dg': to_int(datos_simulados['dg']),
    'puntos': to_int(datos_simulados['puntos'])
}

print("Datos después de aplicar to_int() (listos para Supabase):")
print(data_limpiado)
print()

# Verificar tipos
print("Verificación de tipos:")
todas_int = all(isinstance(v, int) for v in data_limpiado.values())
if todas_int:
    print("✅ Todos los valores son int")
else:
    print("❌ Hay valores que no son int")

# Verificar que dg es -2 (int, no float)
if data_limpiado['dg'] == -2 and isinstance(data_limpiado['dg'], int):
    print("✅ dg = -2 (int) - Evita error de Supabase")
else:
    print(f"❌ dg = {data_limpiado['dg']} ({type(data_limpiado['dg']).__name__})")

print("\n" + "="*70)
print("✅ VALIDACIÓN COMPLETA")
print("="*70)
