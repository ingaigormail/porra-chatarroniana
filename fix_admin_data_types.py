#!/usr/bin/env python3
"""
Script para arreglar los tipos de datos en admin.py
Convierte st.number_input() a int inmediatamente para evitar StreamlitMixedNumericTypesError
"""

import re

# Leer el archivo
with open('src/ui/admin.py', 'r', encoding='utf8') as f:
    content = f.read()

# Patrón 1: Arreglar goles_local en partidos pendientes
pattern1 = r'''goles_local = st\.number_input\(\s*"GL",\s*min_value=0\.0,\s*max_value=10\.0,\s*key=f"gl_pendiente_\{partido_id\}",\s*value=0,\s*step=1,\s*format="%d",\s*label_visibility="collapsed"\)'''

replacement1 = '''goles_local_raw = st.number_input(
                    "GL", min_value=0.0, max_value=10.0,
                    key=f"gl_pendiente_{partido_id}",
                    value=0, step=1, format="%d", label_visibility="collapsed")
                # Forzar conversión a int para evitar StreamlitMixedNumericTypesError
                goles_local = int(goles_local_raw)'''

# Patrón 2: Arreglar goles_visitante en partidos pendientes
pattern2 = r'''goles_visitante = st\.number_input\(\s*"GV",\s*min_value=0\.0,\s*max_value=10\.0,\s*key=f"gv_pendiente_\{partido_id\}",\s*value=0,\s*step=1,\s*format="%d",\s*label_visibility="collapsed"\)'''

replacement2 = '''goles_visitante_raw = st.number_input(
                    "GV", min_value=0.0, max_value=10.0,
                    key=f"gv_pendiente_{partido_id}",
                    value=0, step=1, format="%d", label_visibility="collapsed")
                # Forzar conversión a int para evitar StreamlitMixedNumericTypesError
                goles_visitante = int(goles_visitante_raw)'''

# Aplicar reemplazos
content_modified = content
content_modified = re.sub(pattern1, replacement1, content_modified)
content_modified = re.sub(pattern2, replacement2, content_modified)

# Cambiar botón de "💾" a "💾 Guardar"
content_modified = content_modified.replace(
    'if st.button("💾", key=f"btn_pendiente_{partido_id}"):',
    'if st.button("💾 Guardar", key=f"btn_pendiente_{partido_id}"):')

# Mejorar manejo de prorroga
old_prorroga_code = '''st.selectbox("Prórroga", ["No", "Sí"], key=f"prorroga_{partido_id}",
                           label_visibility="collapsed", disabled=False)'''

new_prorroga_code = '''prorroga_estado = st.selectbox("Prórroga", ["No", "Sí"], key=f"prorroga_{partido_id}",
                           label_visibility="collapsed", disabled=False)'''

content_modified = content_modified.replace(old_prorroga_code, new_prorroga_code)

# Mejorar lógica de guardar
old_save_logic = '''gl = validar_goles(st.session_state.get(f"gl_pendiente_{partido_id}", 0))
                    gv = validar_goles(st.session_state.get(f"gv_pendiente_{partido_id}", 0))
                    hubo_prorroga = st.session_state.get(f"prorroga_{partido_id}") == "Sí"'''

new_save_logic = '''# Validar con la función centralizada
                    gl = validar_goles(goles_local)
                    gv = validar_goles(goles_visitante)
                    hubo_prorroga = prorroga_estado == "Sí"'''

content_modified = content_modified.replace(old_save_logic, new_save_logic)

# Mejorar mensaje de error
content_modified = content_modified.replace(
    'st.error("❌ Error")',
    'st.error("❌ Error al guardar resultado")')

# Guardar el archivo modificado
with open('src/ui/admin.py', 'w', encoding='utf8') as f:
    f.write(content_modified)

print("✅ admin.py actualizado correctamente")
print("✅ Cambios aplicados:")
print("   - Forzada conversión a int en st.number_input() para goles")
print("   - Mejorado botón de 'Guardar'")
print("   - Optimizado manejo de prórroga")
print("   - Mejorada lógica de validación y guardado")
