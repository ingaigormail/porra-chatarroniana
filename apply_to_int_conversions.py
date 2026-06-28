#!/usr/bin/env python3
"""
Script para aplicar la conversión to_int() a todos los lugares críticos en quiniela.py
"""
import re

# Leer el archivo
with open('src/services/quiniela.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Reemplazo 1: puntos_provisionales en calcular_puntos_partido
content = re.sub(
    r"'puntos_provisionales': puntos,",
    "'puntos_provisionales': to_int(puntos),",
    content
)

# Reemplazo 2: puntos en calcular_puntos_finalistas
content = re.sub(
    r"'puntos': puntos\n\s+\}\).eq\('id', apuesta\['id'\]\).execute\(\)",
    "'puntos': to_int(puntos)\n            }).eq('id', apuesta['id']).execute()",
    content
)

# Escribir el archivo actualizado
with open('src/services/quiniela.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Conversiones to_int() aplicadas correctamente a quiniela.py")
