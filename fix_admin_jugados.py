#!/usr/bin/env python3
"""
Script para arreglar los tipos de datos en la sección de Partidos Jugados en admin.py
Convierte st.number_input() a int inmediatamente
"""

import re

# Leer el archivo
with open('src/ui/admin.py', 'r', encoding='utf8') as f:
    content = f.read()

# Arreglar goles_local en partidos jugados
pattern1 = r'''goles_local_edit = st\.number_input\(\s*"GL",\s*min_value=0,\s*max_value=10,\s*key=f"gl_jugado_\{partido_id\}",\s*value=int\(gl_actual\),\s*step=1,\s*format="%d",\s*label_visibility="collapsed"\)'''

replacement1 = '''goles_local_edit_raw = st.number_input(
                    "GL", min_value=0, max_value=10,
                    key=f"gl_jugado_{partido_id}",
                    value=int(gl_actual), step=1, format="%d", label_visibility="collapsed")
                # Forzar conversión a int
                goles_local_edit = int(goles_local_edit_raw)'''

# Arreglar goles_visitante en partidos jugados
pattern2 = r'''goles_visitante_edit = st\.number_input\(\s*"GV",\s*min_value=0,\s*max_value=10,\s*key=f"gv_jugado_\{partido_id\}",\s*value=int\(gv_actual\),\s*step=1,\s*format="%d",\s*label_visibility="collapsed"\)'''

replacement2 = '''goles_visitante_edit_raw = st.number_input(
                    "GV", min_value=0, max_value=10,
                    key=f"gv_jugado_{partido_id}",
                    value=int(gv_actual), step=1, format="%d", label_visibility="collapsed")
                # Forzar conversión a int
                goles_visitante_edit = int(goles_visitante_edit_raw)'''

# Aplicar reemplazos
content_modified = content
content_modified = re.sub(pattern1, replacement1, content_modified)
content_modified = re.sub(pattern2, replacement2, content_modified)

# Cambiar botón de "💾" a "💾 Guardar" en jugados
content_modified = content_modified.replace(
    'if st.button("💾", key=f"btn_guardar_jugado_{partido_id}"):',
    'if st.button("💾 Guardar", key=f"btn_guardar_jugado_{partido_id}"):')

# Guardar el archivo modificado
with open('src/ui/admin.py', 'w', encoding='utf8') as f:
    f.write(content_modified)

print("✅ admin.py - sección 'Partidos Jugados' actualizada")
print("✅ Cambios aplicados:")
print("   - Forzada conversión a int en st.number_input() para goles jugados")
print("   - Mejorado botón 'Guardar' en jugados")
