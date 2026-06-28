#!/usr/bin/env python3
"""Verificar que los puntos de equipos sean correctos"""

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
print("✅ VERIFICAR PUNTOS DE EQUIPOS")
print("=" * 80)

# Obtener partidos jugados
print("\n📋 Obteniendo partidos...")
partidos_resp = client.table('partidos').select('*').eq('estado', 'Jugado').execute()
partidos = partidos_resp.data

# Obtener equipos
print("⚽ Obteniendo equipos...")
equipos_resp = client.table('equipos').select('*').order('puntos', desc=True).execute()
equipos = equipos_resp.data

print(f"\n✅ {len(partidos)} partidos jugados")
print(f"✅ {len(equipos)} equipos")

# Mostrar TOP 15
print(f"\n📊 TOP 15 EQUIPOS ACTUALES:")
print(f"{'Pos':<4} {'Equipo':<25} {'Puntos':>8}")
print("-" * 40)
for idx, eq in enumerate(equipos[:15], 1):
    nombre = eq.get('nombre', '?')
    puntos = eq.get('puntos', 0)
    print(f"{idx:<4} {nombre:<25} {puntos:>8}")

# Verificar equipos con puntos 0
print(f"\n⚠️ EQUIPOS SIN PUNTOS (0 pts):")
sin_puntos = [e for e in equipos if e.get('puntos', 0) == 0]
print(f"   Total: {len(sin_puntos)}")
for eq in sin_puntos[:5]:
    print(f"   - {eq.get('nombre', '?')}")
if len(sin_puntos) > 5:
    print(f"   ... y {len(sin_puntos) - 5} más")

# Verificar total de puntos
total_puntos = sum(e.get('puntos', 0) for e in equipos)
print(f"\n💡 Total puntos en sistema: {total_puntos}")
print(f"   Partidos x 3 puntos por equipo: {len(partidos) * 3}")
print(f"   (Debería ser similar o menor si hay empates)")

print("\n" + "=" * 80)
