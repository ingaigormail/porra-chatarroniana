#!/usr/bin/env python3
"""
Script de LIMPIEZA para preparación a producción
Ejecutar con cuidado - REALIZA CAMBIOS EN LA BD
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
print("🔧 LIMPIEZA Y PREPARACIÓN PARA PRODUCCIÓN")
print("=" * 80)

# ============================================================================
# 1. CERRAR TODAS LAS APUESTAS PARA USUARIOS
# ============================================================================
print("\n" + "=" * 80)
print("1️⃣  CERRAR APUESTAS (partidos con apuestas_abiertas=true)")
print("=" * 80)

partidos_resp = client.table('partidos').select('*').execute()
partidos = partidos_resp.data

abiertos = [p for p in partidos if p.get('apuestas_abiertas', False)]

print(f"\nPartidos con apuestas abiertas: {len(abiertos)}")

if abiertos:
    print("\nCerrando...")
    for p in abiertos:
        try:
            client.table('partidos').update({
                'apuestas_abiertas': False
            }).eq('id', p['id']).execute()
            local = p.get('equipo_local_id', '?')
            visit = p.get('equipo_visitante_id', '?')
            print(f"   ✅ Partido {p['id']} cerrado")
        except Exception as e:
            print(f"   ❌ Error en partido {p['id']}: {e}")
    print(f"\n✅ {len(abiertos)} apuestas cerradas")
else:
    print("\n✅ No hay apuestas abiertas - OK")

# ============================================================================
# 2. DESACTIVAR FINALISTAS PARA USUARIOS
# ============================================================================
print("\n" + "=" * 80)
print("2️⃣  DESACTIVAR FINALISTAS (finalistas_activo=false)")
print("=" * 80)

try:
    # Obtener configuración actual
    config_resp = client.table('configuracion').select('*').eq('clave', 'finalistas_activo').execute()
    
    if config_resp.data:
        cfg = config_resp.data[0]
        valor_actual = cfg.get('valor', 'true')
        print(f"\nValor actual: {valor_actual}")
        
        if valor_actual == 'true':
            # Cambiar a false
            client.table('configuracion').update({
                'valor': 'false'
            }).eq('clave', 'finalistas_activo').execute()
            print("✅ Cambiado a 'false' - Finalistas DESACTIVADOS para usuarios")
        else:
            print("✅ Ya estaba en 'false' - Finalistas ya estaban desactivados")
    else:
        print("⚠️ Configuración no encontrada - creando...")
        client.table('configuracion').insert({
            'clave': 'finalistas_activo',
            'valor': 'false'
        }).execute()
        print("✅ Configuración creada - Finalistas DESACTIVADOS")
        
except Exception as e:
    print(f"❌ Error: {e}")

# ============================================================================
# 3. VERIFICAR ESTADO FINAL
# ============================================================================
print("\n" + "=" * 80)
print("3️⃣  VERIFICACIÓN FINAL")
print("=" * 80)

# Verificar apuestas abiertas
partidos_resp = client.table('partidos').select('*').execute()
abiertos_final = len([p for p in partidos_resp.data if p.get('apuestas_abiertas', False)])

# Verificar configuración
config_resp = client.table('configuracion').select('*').eq('clave', 'finalistas_activo').execute()
finalistas_status = config_resp.data[0].get('valor', 'desconocido') if config_resp.data else 'N/A'

print(f"\n✅ Apuestas abiertas: {abiertos_final}")
print(f"✅ Finalistas: {finalistas_status}")

print("\n" + "=" * 80)
print("🎉 LIMPIEZA COMPLETADA")
print("=" * 80)
