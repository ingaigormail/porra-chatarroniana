#!/usr/bin/env python3
"""
Recalcular puntos de equipos CORRECTAMENTE basados en partidos jugados
Formula:
- Ganador: 3 puntos
- Empate: 1 punto cada uno
- Perdedor: 0 puntos
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
print("📊 RECALCULAR PUNTOS DE EQUIPOS (CORRECTO)")
print("=" * 80)

# Paso 1: Obtener todos los partidos jugados de CUALQUIER fase
print("\n📋 Obteniendo todos los partidos jugados...")
partidos_resp = client.table('partidos').select('*').eq('estado', 'Jugado').execute()
partidos_jugados = partidos_resp.data

print(f"✅ {len(partidos_jugados)} partidos jugados encontrados")

# Paso 2: Calcular puntos por equipo
print("\n🔢 Calculando puntos por equipo...")
puntos_por_equipo = {}

for p in partidos_jugados:
    local_id = p.get('equipo_local_id')
    visit_id = p.get('equipo_visitante_id')
    goles_local = p.get('goles_local', 0)
    goles_visitante = p.get('goles_visitante', 0)
    
    # Inicializar si no existe
    if local_id not in puntos_por_equipo:
        puntos_por_equipo[local_id] = 0
    if visit_id not in puntos_por_equipo:
        puntos_por_equipo[visit_id] = 0
    
    # Aplicar lógica de puntos
    if goles_local > goles_visitante:
        # Ganó local
        puntos_por_equipo[local_id] += 3
        # Perdió visitante (0 puntos)
    elif goles_visitante > goles_local:
        # Ganó visitante
        puntos_por_equipo[visit_id] += 3
        # Perdió local (0 puntos)
    else:
        # Empate
        puntos_por_equipo[local_id] += 1
        puntos_por_equipo[visit_id] += 1

print(f"✅ Puntos calculados para {len(puntos_por_equipo)} equipos")

# Paso 3: Obtener todos los equipos
print("\n⚽ Obteniendo lista de equipos...")
equipos_resp = client.table('equipos').select('*').execute()
equipos = equipos_resp.data
print(f"✅ {len(equipos)} equipos en BD")

# Paso 4: Actualizar puntos en BD
print("\n🔄 Actualizando puntos en BD...")
actualizados = 0
errores = 0

for equipo in equipos:
    equipo_id = equipo['id']
    puntos_nuevos = puntos_por_equipo.get(equipo_id, 0)
    puntos_actuales = equipo.get('puntos', 0)
    
    try:
        # Actualizar en BD
        client.table('equipos').update({
            'puntos': puntos_nuevos
        }).eq('id', equipo_id).execute()
        
        # Log si cambió
        if puntos_nuevos != puntos_actuales:
            nombre = equipo.get('nombre', f'ID:{equipo_id}')
            print(f"   ✅ {nombre}: {puntos_actuales} → {puntos_nuevos} pts")
        
        actualizados += 1
        
    except Exception as e:
        errores += 1
        print(f"   ❌ Error en equipo {equipo_id}: {e}")

print(f"\n✅ {actualizados} equipos actualizados")
if errores > 0:
    print(f"❌ {errores} errores")

# Paso 5: Mostrar top 10
print("\n📊 TOP 10 EQUIPOS POR PUNTOS:")
equipos_ordenados = sorted(equipos, key=lambda x: x.get('puntos', 0), reverse=True)
for idx, eq in enumerate(equipos_ordenados[:10], 1):
    nombre = eq.get('nombre', '?')
    puntos = eq.get('puntos', 0)
    print(f"   {idx:2d}. {nombre:25s} {puntos:3d} pts")

print("\n" + "=" * 80)
print("✅ RECALCULACIÓN COMPLETADA")
print("=" * 80)
