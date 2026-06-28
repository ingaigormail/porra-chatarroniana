#!/usr/bin/env python3
"""
Script de validación: Verifica que los cambios en admin.py se aplicaron correctamente
"""

import re

def validate_admin_file():
    """Valida que los cambios de tipos de datos estén presentes"""
    
    with open('src/ui/admin.py', 'r', encoding='utf8') as f:
        content = f.read()
    
    checks = {
        'int(goles_local_raw)': 'Conversión inmediata de goles_local en partidos pendientes',
        'int(goles_visitante_raw)': 'Conversión inmediata de goles_visitante en partidos pendientes',
        'int(goles_local_edit_raw)': 'Conversión inmediata de goles_local en partidos jugados',
        'int(goles_visitante_edit_raw)': 'Conversión inmediata de goles_visitante en partidos jugados',
        '"💾 Guardar"': 'Botón mejorado con texto "Guardar"',
        'prorroga_estado = st.selectbox': 'Variable prorroga_estado declarada',
        'Error al guardar resultado': 'Mensaje de error mejorado',
    }
    
    print("\n" + "="*70)
    print("VALIDACIÓN: CAMBIOS EN admin.py")
    print("="*70 + "\n")
    
    all_passed = True
    for check_str, description in checks.items():
        if check_str in content:
            print(f"✅ PASS: {description}")
            print(f"   Búsqueda: '{check_str}'")
        else:
            print(f"❌ FAIL: {description}")
            print(f"   Búsqueda: '{check_str}'")
            all_passed = False
        print()
    
    # Verificar que NO hay valores old_style
    old_patterns = [
        ('st.number_input.*value=0.*step=1.*format="%d".*label_visibility="collapsed"\\)', 'st.number_input sin conversión'),
        ('if st.button\\("💾",', 'Botón sin mejorar'),
    ]
    
    print("\nVERIFICACIONES NEGATIVAS (debe NO encontrarse):\n")
    
    for pattern, description in old_patterns:
        if re.search(pattern, content):
            print(f"⚠️  ADVERTENCIA: Posible {description}")
            print(f"   Patrón: {pattern}")
        else:
            print(f"✅ OK: No se encontró {description}")
        print()
    
    # Contar líneas modificadas
    pendientes_section = content[content.find('# PARTIDOS PENDIENTES'):content.find('# PARTIDOS JUGADOS')]
    if 'Forzar conversión a int' in pendientes_section:
        print(f"✅ Sección 'Partidos Pendientes' contiene comentarios de conversión")
    
    jugados_section = content[content.find('# PARTIDOS JUGADOS - EDITAR'):content.find('# REVISAR Y VALIDAR')]
    if 'Forzar conversión a int' in jugados_section:
        print(f"✅ Sección 'Partidos Jugados' contiene comentarios de conversión")
    
    print("\n" + "="*70)
    if all_passed:
        print("✅ TODAS LAS VALIDACIONES PASARON CORRECTAMENTE")
    else:
        print("❌ ALGUNAS VALIDACIONES FALLARON")
    print("="*70 + "\n")
    
    return all_passed

if __name__ == '__main__':
    success = validate_admin_file()
    exit(0 if success else 1)
