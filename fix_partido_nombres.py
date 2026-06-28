#!/usr/bin/env python3
"""
Llenar los nombres de equipos faltantes en la tabla de partidos
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from supabase import create_client
import re

# Credenciales
with open('.streamlit/secrets.toml') as f:
    content = f.read()
    url = re.search(r'url = "(.*?)"', content).group(1)
    key = re.search(r'key = "(.*?)"', content).group(1)

client = create_client(url, key)

print("=" * 80)
print("🔧 ACTUALIZANDO NOMBRES DE EQUIPOS EN PARTIDOS")
print("=" * 80)

# Obtener todos los equipos
equipos_resp = client.table('equipos').select('*').execute()
equipos = equipos_resp.data

# Crear mapa de ID -> nombre
equipos_dict = {eq['id']: eq.get('nombre', '?') for eq in equipos}

print(f"\n📊 Cargado mapa de {len(equipos_dict)} equipos")

# Obtener todos los partidos
partidos_resp = client.table('partidos').select('*').execute()
partidos = partidos_resp.data

print(f"📋 Total partidos a actualizar: {len(partidos)}")

# Actualizar cada partido
actualizados = 0
errores = 0

for idx, partido in enumerate(partidos, 1):
    try:
        local_id = partido.get('equipo_local_id')
        visit_id = partido.get('equipo_visitante_id')
        
        local_nombre = equipos_dict.get(local_id, '?')
        visit_nombre = equipos_dict.get(visit_id, '?')
        
        # Actualizar en BD
        actualizar_resp = client.table('partidos').update({
            'equipo_local_nombre': local_nombre,
            'equipo_visitante_nombre': visit_nombre
        }).eq('id', partido['id']).execute()
        
        actualizados += 1
        
        if idx % 10 == 0 or idx == len(partidos):
            print(f"   [{idx}/{len(partidos)}] ✅ {local_nombre} vs {visit_nombre}")
    
    except Exception as e:
        errores += 1
        print(f"   ❌ Error en partido {idx}: {str(e)}")

print("\n" + "=" * 80)
print("📊 RESULTADOS")
print("=" * 80)
print(f"\n✅ Partidos actualizados: {actualizados}")
print(f"❌ Errores: {errores}")

if errores == 0:
    print("\n🎉 ¡TODOS los partidos han sido actualizados correctamente!")
else:
    print(f"\n⚠️ {errores} partidos fallaron. Revisa los errores arriba.")

print("\n" + "=" * 80)
