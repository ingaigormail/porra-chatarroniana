#!/usr/bin/env python3
"""Verificar estado de partidos de grupos y qué falta actualizar"""

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
print("📋 ESTADO DE PARTIDOS DE GRUPOS")
print("=" * 80)

# Obtener todos los partidos de grupos
partidos_resp = client.table('partidos').select('*').eq('fase', 'Grupos').order('fecha').execute()
partidos = partidos_resp.data

# Agrupar por fecha
por_fecha = {}
for p in partidos:
    fecha = p.get('fecha', '?')
    if fecha not in por_fecha:
        por_fecha[fecha] = []
    por_fecha[fecha].append(p)

print("\n")
for fecha in sorted(por_fecha.keys()):
    partidos_fecha = por_fecha[fecha]
    jugados = [p for p in partidos_fecha if p.get('estado') == 'Jugado']
    print(f"\n📅 {fecha} - {len(jugados)}/{len(partidos_fecha)} jugados")
    
    for p in partidos_fecha:
        local = p.get('equipo_local_nombre', '?')
        visit = p.get('equipo_visitante_nombre', '?')
        estado = p.get('estado', '?')
        
        if estado == 'Jugado':
            gl = p.get('goles_local', 0)
            gv = p.get('goles_visitante', 0)
            print(f"   ✅ {local} {gl} - {gv} {visit}")
        else:
            print(f"   ⏳ {local} vs {visit}")

print("\n" + "=" * 80)
print("RESUMEN")
print("=" * 80)

jugados = [p for p in partidos if p.get('estado') == 'Jugado']
pendientes = [p for p in partidos if p.get('estado') == 'Pendiente']

print(f"\n✅ Partidos jugados: {len(jugados)}")
print(f"⏳ Partidos pendientes: {len(pendientes)}")

if pendientes:
    print(f"\nÚltimos pendientes:")
    for p in pendientes[:3]:
        fecha = p.get('fecha', '?')
        local = p.get('equipo_local_nombre', '?')
        visit = p.get('equipo_visitante_nombre', '?')
        print(f"   - {fecha}: {local} vs {visit}")

print("\n" + "=" * 80)
