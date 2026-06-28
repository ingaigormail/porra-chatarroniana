#!/usr/bin/env python3
"""Arreglar conversión de tipos de Supabase en admin.py"""

with open('src/ui/admin.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Arreglar líneas 612-613: convertir a int ANTES de st.number_input
old = """            gl_actual = partido.get('goles_local', 0)
            gv_actual = partido.get('goles_visitante', 0)"""

new = """            gl_actual = int(partido.get('goles_local', 0) or 0)
            gv_actual = int(partido.get('goles_visitante', 0) or 0)"""

content = content.replace(old, new)

with open('src/ui/admin.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Tipos de Supabase corregidos en admin.py")
print("   gl_actual y gv_actual ahora se convierten a int ANTES de st.number_input")
