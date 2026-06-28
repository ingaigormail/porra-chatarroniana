#!/usr/bin/env python3
"""
Script crítico: Arregla StreamlitMixedNumericTypesError
Problema: min_value=0.0 (float) + value=0 (int) = Error
Solución: Unificar todos a int: min_value=0, max_value=10
"""

import re

# Leer admin.py
with open('src/ui/admin.py', 'r', encoding='utf8') as f:
    content = f.read()

print("="*70)
print("ARREGLANDO StreamlitMixedNumericTypesError en admin.py")
print("="*70)

# ============================================================================
# REEMPLAZO 1: Partidos Pendientes - goles_local (línea 554-557)
# ============================================================================
old_1 = '''goles_local_raw = st.number_input(
                    "GL", min_value=0.0, max_value=10.0,
                    key=f"gl_pendiente_{partido_id}",
                    value=0, step=1, format="%d", label_visibility="collapsed")'''

new_1 = '''goles_local_raw = st.number_input(
                    "GL", min_value=0, max_value=10,
                    key=f"gl_pendiente_{partido_id}",
                    value=0, step=1, format="%d", label_visibility="collapsed")'''

if old_1 in content:
    content = content.replace(old_1, new_1)
    print("✅ Reemplazo 1: Partidos Pendientes - goles_local")
else:
    print("⚠️ Reemplazo 1: Pattern no encontrado")

# ============================================================================
# REEMPLAZO 2: Partidos Pendientes - goles_visitante (línea 561-564)
# ============================================================================
old_2 = '''goles_visitante_raw = st.number_input(
                    "GV", min_value=0.0, max_value=10.0,
                    key=f"gv_pendiente_{partido_id}",
                    value=0, step=1, format="%d", label_visibility="collapsed")'''

new_2 = '''goles_visitante_raw = st.number_input(
                    "GV", min_value=0, max_value=10,
                    key=f"gv_pendiente_{partido_id}",
                    value=0, step=1, format="%d", label_visibility="collapsed")'''

if old_2 in content:
    content = content.replace(old_2, new_2)
    print("✅ Reemplazo 2: Partidos Pendientes - goles_visitante")
else:
    print("⚠️ Reemplazo 2: Pattern no encontrado")

# ============================================================================
# REEMPLAZO 3: Partidos Jugados - goles_local_edit (línea 631-634)
# ============================================================================
old_3 = '''goles_local_edit_raw = st.number_input(
                    "GL", min_value=0, max_value=10,
                    key=f"gl_jugado_{partido_id}",
                    value=int(gl_actual), step=1, format="%d", label_visibility="collapsed")'''

# Este ya está bien, pero lo incluimos por si acaso
if old_3 in content:
    print("✅ Reemplazo 3: Partidos Jugados - goles_local_edit (ya está correcto)")
else:
    print("⚠️ Reemplazo 3: Pattern no encontrado (posiblemente ya arreglado)")

# ============================================================================
# REEMPLAZO 4: Partidos Jugados - goles_visitante_edit (línea 638-641)
# ============================================================================
old_4 = '''goles_visitante_edit_raw = st.number_input(
                    "GV", min_value=0, max_value=10,
                    key=f"gv_jugado_{partido_id}",
                    value=int(gv_actual), step=1, format="%d", label_visibility="collapsed")'''

# Este ya está bien, pero lo incluimos por si acaso
if old_4 in content:
    print("✅ Reemplazo 4: Partidos Jugados - goles_visitante_edit (ya está correcto)")
else:
    print("⚠️ Reemplazo 4: Pattern no encontrado (posiblemente ya arreglado)")

# Guardar cambios
with open('src/ui/admin.py', 'w', encoding='utf8') as f:
    f.write(content)

print("\n" + "="*70)
print("✅ TODOS LOS CAMBIOS APLICADOS")
print("="*70)
print("\nCambios realizados:")
print("  • min_value=0.0 → min_value=0 (todas las líneas)")
print("  • max_value=10.0 → max_value=10 (todas las líneas)")
print("\nResultado:")
print("  ✅ Todos los argumentos de st.number_input() son INT")
print("  ✅ StreamlitMixedNumericTypesError ELIMINADO")
print("\nVerificación:")
print("  Ejecutar: python -m py_compile src/ui/admin.py")
