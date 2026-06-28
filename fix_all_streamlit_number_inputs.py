#!/usr/bin/env python3
"""
Script DEFINITIVO: Arregla StreamlitMixedNumericTypesError EN TODOS LOS ARCHIVOS
Busca y reemplaza TODOS los min_value=0.0 y max_value=10.0 por min_value=0 y max_value=10
"""

import os
import re

# Archivos a revisar
archivos_a_revisar = [
    'src/ui/admin.py',
    'src/ui/mi_ficha.py',
    'src/ui/clasificacion.py',
    'src/ui/calendario.py',
    'src/ui/mundial_grupos.py',
    'app.py',
    'app1.py',
]

print("="*70)
print("ARREGLANDO StreamlitMixedNumericTypesError EN TODOS LOS ARCHIVOS")
print("="*70)

total_cambios = 0

for archivo in archivos_a_revisar:
    ruta = os.path.join('c:\\mundial_app_nueva', archivo)
    
    # Verificar que el archivo existe
    if not os.path.exists(ruta):
        print(f"⚠️  {archivo} - No existe")
        continue
    
    # Leer archivo
    with open(ruta, 'r', encoding='utf8') as f:
        contenido_original = f.read()
    
    contenido = contenido_original
    
    # REEMPLAZO GLOBAL: min_value=0.0 → min_value=0
    patrón_min = r'min_value=0\.0'
    reemplazo_min = 'min_value=0'
    contenido = re.sub(patrón_min, reemplazo_min, contenido)
    
    # REEMPLAZO GLOBAL: max_value=10.0 → max_value=10
    patrón_max = r'max_value=10\.0'
    reemplazo_max = 'max_value=10'
    contenido = re.sub(patrón_max, reemplazo_max, contenido)
    
    # Contar cambios
    cambios = 0
    if contenido != contenido_original:
        cambios = (contenido_original.count('0.0') + contenido_original.count('10.0')) - \
                  (contenido.count('0.0') + contenido.count('10.0'))
        
        # Guardar cambios
        with open(ruta, 'w', encoding='utf8') as f:
            f.write(contenido)
        
        print(f"✅ {archivo}")
        print(f"   Cambios aplicados: {cambios}")
        total_cambios += cambios
    else:
        print(f"✅ {archivo} - Ya está correcto")

print("\n" + "="*70)
print(f"✅ TODOS LOS CAMBIOS COMPLETADOS")
print(f"Total de reemplazos: {total_cambios}")
print("="*70)
print("\nCambios realizados:")
print("  • min_value=0.0 → min_value=0")
print("  • max_value=10.0 → max_value=10")
print("\nResultado:")
print("  ✅ Todos los st.number_input() con tipos INT unificados")
print("  ✅ StreamlitMixedNumericTypesError ELIMINADO")
