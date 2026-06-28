#!/usr/bin/env python3
"""
Fix quiniela.py - Corregir las comillas removidas accidentalmente
"""

with open('src/services/quiniela.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Reemplazar las líneas sin comillas
content = content.replace(
    "data[ goles_local_apostados]",
    "data['goles_local_apostados']"
)
content = content.replace(
    "data[ goles_visitante_apostados]",
    "data['goles_visitante_apostados']"
)

with open('src/services/quiniela.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Quiniela.py corregida")
