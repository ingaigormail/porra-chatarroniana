#!/usr/bin/env python3
"""
Test del flujo completo:
1. Ingresa resultado de un partido pendiente
2. Verifica que se calcule todo automáticamente
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
print("🧪 TEST FLUJO COMPLETO")
print("=" * 80)

# Obtener un partido pendiente
print("\n1️⃣ Obtener partido pendiente...")
pendientes_resp = client.table('partidos').select('*').eq('estado', 'Pendiente').limit(1).execute()

if not pendientes_resp.data:
    print("❌ No hay partidos pendientes para probar")
    sys.exit(1)

partido = pendientes_resp.data[0]
partido_id = partido['id']
local_id = partido.get('equipo_local_id')
visit_id = partido.get('equipo_visitante_id')

# Obtener nombres de equipos
eq_local_resp = client.table('equipos').select('*').eq('id', local_id).execute()
eq_visit_resp = client.table('equipos').select('*').eq('id', visit_id).execute()

local_nombre = eq_local_resp.data[0]['nombre'] if eq_local_resp.data else f'ID:{local_id}'
visit_nombre = eq_visit_resp.data[0]['nombre'] if eq_visit_resp.data else f'ID:{visit_id}'

print(f"✅ Partido encontrado: {local_nombre} vs {visit_nombre}")
print(f"   ID: {partido_id}")
print(f"   Estado actual: {partido.get('estado')}")

# Obtener puntos actuales de los equipos
eq_local_antes = eq_local_resp.data[0]['puntos'] if eq_local_resp.data else 0
eq_visit_antes = eq_visit_resp.data[0]['puntos'] if eq_visit_resp.data else 0

print(f"\n2️⃣ Puntos ANTES:")
print(f"   {local_nombre}: {eq_local_antes} pts")
print(f"   {visit_nombre}: {eq_visit_antes} pts")

# Simular resultado: local gana 2-1
gl = 2
gv = 1
print(f"\n3️⃣ Simulando resultado: {local_nombre} {gl} - {gv} {visit_nombre}")

# Guardar resultado (sin usar la app, directamente en BD)
try:
    client.table('partidos').update({
        'goles_local': gl,
        'goles_visitante': gv,
        'estado': 'Jugado',
        'hubo_prorroga': False
    }).eq('id', partido_id).execute()
    
    print("✅ Resultado guardado")
    
    # Verificar que cambió a Jugado
    partido_check = client.table('partidos').select('*').eq('id', partido_id).execute()
    if partido_check.data:
        estado_nuevo = partido_check.data[0].get('estado')
        print(f"✅ Partido cambió a: {estado_nuevo}")
    
    # Obtener puntos DESPUÉS
    print(f"\n4️⃣ Verificando puntos DESPUÉS...")
    eq_local_despues_resp = client.table('equipos').select('*').eq('id', local_id).execute()
    eq_visit_despues_resp = client.table('equipos').select('*').eq('id', visit_id).execute()
    
    eq_local_despues = eq_local_despues_resp.data[0]['puntos'] if eq_local_despues_resp.data else 0
    eq_visit_despues = eq_visit_despues_resp.data[0]['puntos'] if eq_visit_despues_resp.data else 0
    
    print(f"   {local_nombre}: {eq_local_antes} → {eq_local_despues} pts")
    print(f"   {visit_nombre}: {eq_visit_antes} → {eq_visit_despues} pts")
    
    # Verificar que se calculó correctamente
    print(f"\n✅ RESULTADO:")
    if eq_local_despues > eq_local_antes:
        print(f"   ✅ {local_nombre} ganó +3 puntos (o lo que corresponda)")
    else:
        print(f"   ⚠️ Puntos de {local_nombre} no cambiaron")
        
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 80)
print("📝 NOTA: En la app real, el flujo es automático cuando el admin")
print("   guarda el resultado en 'Partidos Pendientes'")
print("=" * 80)
