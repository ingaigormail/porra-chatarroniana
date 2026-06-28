#!/usr/bin/env python3
"""Verificar equipos en la BD"""

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
print("⚽ VERIFICAR EQUIPOS Y RELACIONES")
print("=" * 80)

# Obtener equipos
equipos_resp = client.table('equipos').select('*').execute()
equipos = equipos_resp.data

print(f"\n✅ Total equipos: {len(equipos)}")
print(f"\nÚltimos 10 equipos:")
for eq in equipos[-10:]:
    print(f"   - ID: {eq['id']}, Nombre: {eq.get('nombre', '?')}")

# Obtener primer partido para ver qué campos tiene
partidos_resp = client.table('partidos').select('*').limit(1).execute()
if partidos_resp.data:
    p = partidos_resp.data[0]
    print(f"\n📋 Estructura de un partido:")
    print(f"   - id: {p.get('id')}")
    print(f"   - equipo_local_id: {p.get('equipo_local_id')}")
    print(f"   - equipo_local_nombre: {p.get('equipo_local_nombre')}")
    print(f"   - equipo_visitante_id: {p.get('equipo_visitante_id')}")
    print(f"   - equipo_visitante_nombre: {p.get('equipo_visitante_nombre')}")
    print(f"   - goles_local: {p.get('goles_local')}")
    print(f"   - goles_visitante: {p.get('goles_visitante')}")
    print(f"   - estado: {p.get('estado')}")
    print(f"   - fecha: {p.get('fecha')}")

# Verificar si todos los partidos tienen nombres
partidos_resp = client.table('partidos').select('*').eq('fase', 'Grupos').execute()
partidos = partidos_resp.data

sin_nombres = [p for p in partidos if not p.get('equipo_local_nombre') or not p.get('equipo_visitante_nombre')]

print(f"\n⚠️ Partidos sin nombres de equipos: {len(sin_nombres)}/{len(partidos)}")

if sin_nombres:
    print(f"\nPrimer partido sin nombres:")
    p = sin_nombres[0]
    print(f"   - ID: {p['id']}")
    print(f"   - Local ID: {p.get('equipo_local_id')}, Nombre: {p.get('equipo_local_nombre')}")
    print(f"   - Visit ID: {p.get('equipo_visitante_id')}, Nombre: {p.get('equipo_visitante_nombre')}")
    
    # Obtener el equipo para ver si existe
    if p.get('equipo_local_id'):
        eq_local_resp = client.table('equipos').select('*').eq('id', p['equipo_local_id']).execute()
        if eq_local_resp.data:
            print(f"   - Equipo local existe en BD: {eq_local_resp.data[0].get('nombre')}")
        else:
            print(f"   - ❌ Equipo local NO existe en BD")
