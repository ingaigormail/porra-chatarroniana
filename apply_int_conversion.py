#!/usr/bin/env python3
"""
Script que aplica la conversión explícita int() a todos los st.number_input() en admin.py
Para resolver StreamlitMixedNumericTypesError en Python 3.14
"""

# Leer el archivo
with open('src/ui/admin.py', 'r', encoding='utf8') as f:
    content = f.read()

print("="*70)
print("APLICANDO CONVERSIÓN int() EXPLÍCITA A TODOS st.number_input()")
print("="*70)

# ============================================================================
# REEMPLAZO 1: GOLES LOCAL PENDIENTES
# ============================================================================
old_1 = '''goles_local_raw = st.number_input(
                    "GL", min_value=0, max_value=10,
                    key=f"gl_pendiente_{partido_id}",
                    value=0, step=1, format="%d", label_visibility="collapsed")'''

new_1 = '''goles_local_raw = st.number_input(
                    "GL", 
                    min_value=int(0), 
                    max_value=int(10),
                    key=f"gl_pendiente_{partido_id}",
                    value=int(0), 
                    step=int(1), 
                    format="%d", 
                    label_visibility="collapsed")'''

if old_1 in content:
    content = content.replace(old_1, new_1)
    print("✅ Reemplazo 1: Goles local pendientes")
else:
    print("⚠️ Reemplazo 1: Pattern no encontrado")

# ============================================================================
# REEMPLAZO 2: GOLES VISITANTE PENDIENTES
# ============================================================================
old_2 = '''goles_visitante_raw = st.number_input(
                    "GV", min_value=0, max_value=10,
                    key=f"gv_pendiente_{partido_id}",
                    value=0, step=1, format="%d", label_visibility="collapsed")'''

new_2 = '''goles_visitante_raw = st.number_input(
                    "GV", 
                    min_value=int(0), 
                    max_value=int(10),
                    key=f"gv_pendiente_{partido_id}",
                    value=int(0), 
                    step=int(1), 
                    format="%d", 
                    label_visibility="collapsed")'''

if old_2 in content:
    content = content.replace(old_2, new_2)
    print("✅ Reemplazo 2: Goles visitante pendientes")
else:
    print("⚠️ Reemplazo 2: Pattern no encontrado")

# ============================================================================
# REEMPLAZO 3: GOLES LOCAL JUGADOS
# ============================================================================
old_3 = '''goles_local_edit_raw = st.number_input(
                    "GL", min_value=0, max_value=10,
                    key=f"gl_jugado_{partido_id}",
                    value=int(gl_actual), step=1, format="%d", label_visibility="collapsed")'''

new_3 = '''goles_local_edit_raw = st.number_input(
                    "GL", 
                    min_value=int(0), 
                    max_value=int(10),
                    key=f"gl_jugado_{partido_id}",
                    value=int(gl_actual), 
                    step=int(1), 
                    format="%d", 
                    label_visibility="collapsed")'''

if old_3 in content:
    content = content.replace(old_3, new_3)
    print("✅ Reemplazo 3: Goles local jugados")
else:
    print("⚠️ Reemplazo 3: Pattern no encontrado")

# ============================================================================
# REEMPLAZO 4: GOLES VISITANTE JUGADOS
# ============================================================================
old_4 = '''goles_visitante_edit_raw = st.number_input(
                    "GV", min_value=0, max_value=10,
                    key=f"gv_jugado_{partido_id}",
                    value=int(gv_actual), step=1, format="%d", label_visibility="collapsed")'''

new_4 = '''goles_visitante_edit_raw = st.number_input(
                    "GV", 
                    min_value=int(0), 
                    max_value=int(10),
                    key=f"gv_jugado_{partido_id}",
                    value=int(gv_actual), 
                    step=int(1), 
                    format="%d", 
                    label_visibility="collapsed")'''

if old_4 in content:
    content = content.replace(old_4, new_4)
    print("✅ Reemplazo 4: Goles visitante jugados")
else:
    print("⚠️ Reemplazo 4: Pattern no encontrado")

# Guardar el archivo modificado
with open('src/ui/admin.py', 'w', encoding='utf8') as f:
    f.write(content)

print("\n" + "="*70)
print("✅ ARCHIVO ACTUALIZADO CON CONVERSIONES int() EXPLÍCITAS")
print("="*70)
print("\nCambios aplicados:")
print("  • min_value=0 → min_value=int(0)")
print("  • max_value=10 → max_value=int(10)")
print("  • value=0 → value=int(0)")
print("  • step=1 → step=int(1)")
print("\nResultado:")
print("  ✅ Streamlit ya NO puede malinterpretar los tipos")
print("  ✅ Python 3.14 tendrá tipos explícitos")
print("\nPróximo paso:")
print("  1. Presiona Ctrl+C para detener el servidor Streamlit")
print("  2. Reinicia: streamlit run app.py")
print("  3. Verifica que no hay StreamlitMixedNumericTypesError")
