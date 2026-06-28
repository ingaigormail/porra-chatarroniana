#!/usr/bin/env python3
"""Corregir tipos en admin.py - convertir floats de vuelta a ints"""

with open('src/ui/admin.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Cambiar min_value=0.0, max_value=10.0 a min_value=0, max_value=10
content = content.replace(
    'min_value=0.0, max_value=10.0,\n                    key=f"gl_jugado',
    'min_value=0, max_value=10,\n                    key=f"gl_jugado'
)

content = content.replace(
    'min_value=0.0, max_value=10.0,\n                    key=f"gv_jugado',
    'min_value=0, max_value=10,\n                    key=f"gv_jugado'
)

# Cambiar step=1.0 a step=1
content = content.replace(
    'value=int(gl_actual), step=1.0, format="%d"',
    'value=int(gl_actual), step=1, format="%d"'
)

content = content.replace(
    'value=int(gv_actual), step=1.0, format="%d"',
    'value=int(gv_actual), step=1, format="%d"'
)

with open('src/ui/admin.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Tipos corregidos en admin.py")
print("   Todos los parámetros de st.number_input son ahora ints consistentes")
