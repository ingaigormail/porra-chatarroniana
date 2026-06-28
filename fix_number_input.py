#!/usr/bin/env python3
"""Corregir todos los st.number_input con tipos mixtos"""

import re

# Leer admin.py
with open('src/ui/admin.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Patrón a buscar y reemplazar
# Buscar: min_value=0, max_value=10, (para número inputs)
# Reemplazar con: min_value=0.0, max_value=10.0,

# Para las líneas 627-628 (goles_local_edit)
content = content.replace(
    '                    "GL", min_value=0, max_value=10,',
    '                    "GL", min_value=0.0, max_value=10.0,'
)

# Para las líneas 632-633 (goles_visitante_edit) 
content = content.replace(
    '                    "GV", min_value=0, max_value=10,',
    '                    "GV", min_value=0.0, max_value=10.0,'
)

# Escribir de vuelta
with open('src/ui/admin.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Corregidos todos los st.number_input")
print("   - min_value=0 → min_value=0.0")
print("   - max_value=10 → max_value=10.0")
