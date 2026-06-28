#!/usr/bin/env python3
"""Recalcular puntos de equipos - versión simple"""

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
print("📊 RECALCULAR PUNTOS DE EQUIPOS")
print("=" * 80)

# Obtener partidos jugados
print("\n📋 Obteniendo partidos jugados...")
partidos_resp = client.table('partidos').select('*').eq('estado', 'Jugado').execute()
partidos_jugados = partidos_resp.data

print(f"✅ {len(partidos_jugados)} partidos jugados")

# Calcular puntos por equipo
puntos_equipo = {}

for p in partidos_jugados:
    local_id = p.get('equipo_local_id')
    visit_id = p.get('equipo_visitante_id')
    gl = p.get('goles_local', 0)
    gv = p.get('goles_visitante', 0)
    
    # Inicializar si no existen
    if local_id not in puntos_equipo:
        puntos_equipo[local_id] = 0
    if visit_id not in puntos_equipo:
        puntos_equipo[visit_id] = 0
    
    # Sumar puntos según resultado
    if gl > gv:
        puntos_equipo[local_id] += 3  # Ganó local
    elif gv > gl:
        puntos_equipo[visit_id] += 3  # Ganó visitante
    else:
        puntos_equipo[local_id] += 1  # Empate
        puntos_equipo[visit_id] += 1

print(f"\n📊 Puntos calculados para {len(puntos_equipo)} equipos")

# Actualizar en BD
print("\n🔄 Actualizando puntos en BD...")
actualizados = 0
for equipo_id, puntos in puntos_equipo.items():
    try:
        client.table('equipos').update({
            'puntos': puntos
        }).eq('id', equipo_id).execute()
        actualizados += 1
    except Exception as e:
        print(f"   ❌ Error actualizando equipo {equipo_id}: {e}")

print(f"✅ {actualizados} equipos actualizados")

# Mostrar top 10
print("\n📊 Top 10 equipos por puntos:")
equipos_resp = client.table('equipos').select('*').order('puntos', ascending=False).limit(10).execute()
for idx, eq in enumerate(equipos_resp.data, 1):
    nombre = eq.get('nombre', '?')
    puntos = eq.get('puntos', 0)
    print(f"   {idx}. {nombre}: {puntos} pts")

print("\n" + "=" * 80)
print("✅ RECALCULACIÓN COMPLETADA")
print("=" * 80)
