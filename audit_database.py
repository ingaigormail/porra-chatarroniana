#!/usr/bin/env python3
"""
Script de auditoría de la base de datos para preparación a producción
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from supabase import create_client
import pandas as pd
from datetime import datetime

# Configurar credenciales
try:
    with open('.streamlit/secrets.toml', 'r') as f:
        import re
        content = f.read()
        url = re.search(r'url = "(.*?)"', content).group(1)
        key = re.search(r'key = "(.*?)"', content).group(1)
except Exception as e:
    print(f"❌ Error al leer credenciales: {e}")
    sys.exit(1)

client = create_client(url, key)

print("=" * 80)
print("🔍 AUDITORÍA DE BASE DE DATOS - PREPARACIÓN PARA PRODUCCIÓN")
print("=" * 80)

# ============================================================================
# 1. REVISAR USUARIOS
# ============================================================================
print("\n" + "=" * 80)
print("1️⃣  USUARIOS")
print("=" * 80)

usuarios_resp = client.table('usuarios').select('*').execute()
usuarios_data = usuarios_resp.data

print(f"\n✅ Total de usuarios: {len(usuarios_data)}")
print("\nUsuarios en la BD:")
for user in usuarios_data:
    print(f"   - {user['nombre']} (ID: {user['id']}, Admin: {user.get('es_admin', False)})")

# ============================================================================
# 2. REVISAR PARTIDOS DE GRUPOS
# ============================================================================
print("\n" + "=" * 80)
print("2️⃣  PARTIDOS DE GRUPOS")
print("=" * 80)

partidos_resp = client.table('partidos').select('*').eq('fase', 'Grupos').execute()
partidos_data = partidos_resp.data

print(f"\n✅ Total partidos de grupos: {len(partidos_data)}")

# Contar por estado
estados = {}
for p in partidos_data:
    estado = p.get('estado', 'Desconocido')
    estados[estado] = estados.get(estado, 0) + 1

print("\nPartidos por estado:")
for estado, count in sorted(estados.items()):
    print(f"   - {estado}: {count}")

# Mostrar últimos partidos jugados
jugados = [p for p in partidos_data if p.get('estado') == 'Jugado']
if jugados:
    print(f"\n✅ Últimos 5 partidos jugados:")
    for p in jugados[-5:]:
        local = p.get('equipo_local_nombre', '?')
        visit = p.get('equipo_visitante_nombre', '?')
        gl = p.get('goles_local', 0)
        gv = p.get('goles_visitante', 0)
        print(f"   - {local} {gl} - {gv} {visit}")

# ============================================================================
# 3. REVISAR APUESTAS
# ============================================================================
print("\n" + "=" * 80)
print("3️⃣  APUESTAS - QUINIELAS Y PORRAS")
print("=" * 80)

quinielas_resp = client.table('quinielas').select('*').execute()
quinielas_data = quinielas_resp.data

print(f"\n✅ Total apuestas: {len(quinielas_data)}")

# Contar por tipo
tipos = {}
for q in quinielas_data:
    tipo = q.get('tipo', 'desconocido')
    tipos[tipo] = tipos.get(tipo, 0) + 1

print("\nApuestas por tipo:")
for tipo, count in sorted(tipos.items()):
    print(f"   - {tipo}: {count}")

# Contar validadas
validadas = len([q for q in quinielas_data if q.get('validado', False)])
print(f"\nApuestas validadas: {validadas}")
print(f"Apuestas sin validar: {len(quinielas_data) - validadas}")

# ============================================================================
# 4. REVISAR FINALISTAS
# ============================================================================
print("\n" + "=" * 80)
print("4️⃣  APUESTAS DE FINALISTAS")
print("=" * 80)

finalistas_resp = client.table('finalistas_apostados').select('*').execute()
finalistas_data = finalistas_resp.data

print(f"\n✅ Total apuestas de finalistas: {len(finalistas_data)}")

# ============================================================================
# 5. REVISAR CONFIGURACIÓN
# ============================================================================
print("\n" + "=" * 80)
print("5️⃣  CONFIGURACIÓN - APUESTAS ACTIVAS")
print("=" * 80)

config_resp = client.table('configuracion').select('*').execute()
config_data = config_resp.data

for cfg in config_data:
    clave = cfg.get('clave', '?')
    valor = cfg.get('valor', '?')
    print(f"   - {clave}: {valor}")

# Verificar si hay partidos con apuestas abiertas
partidos_abiertos = [p for p in partidos_data if p.get('apuestas_abiertas', False)]
print(f"\n⚠️ Partidos con apuestas abiertas: {len(partidos_abiertos)}")
if partidos_abiertos:
    print("   Estos partidos deberían estar CERRADOS antes de producción:")
    for p in partidos_abiertos[:5]:
        local = p.get('equipo_local_nombre', '?')
        visit = p.get('equipo_visitante_nombre', '?')
        tipo = p.get('tipo_apuesta', 'ninguno')
        print(f"      - {local} vs {visit} (tipo: {tipo})")

# ============================================================================
# 6. CLASIFICACIÓN
# ============================================================================
print("\n" + "=" * 80)
print("6️⃣  CLASIFICACIÓN ACTUAL")
print("=" * 80)

clasif_resp = client.table('usuarios_clasificacion').select('*').order('posicion').limit(10).execute()
clasif_data = clasif_resp.data

if clasif_data:
    print("\n✅ Top usuarios por puntos:")
    for user in clasif_data[:5]:
        nombre = user.get('nombre', '?')
        puntos = user.get('puntos', 0)
        print(f"   - {nombre}: {puntos} pts")
else:
    print("\n⚠️ Clasificación vacía")

print("\n" + "=" * 80)
print("✅ AUDITORÍA COMPLETADA")
print("=" * 80)

