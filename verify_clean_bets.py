#!/usr/bin/env python3
"""Verificar que no haya apuestas de prueba residuales"""

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
print("🧹 VERIFICAR LIMPIEZA DE APUESTAS")
print("=" * 80)

# Obtener apuestas
quinielas_resp = client.table('quinielas').select('*').execute()
finalistas_resp = client.table('finalistas_apostados').select('*').execute()

quinielas = quinielas_resp.data
finalistas = finalistas_resp.data

print(f"\n✅ Apuestas de quiniela/porra: {len(quinielas)}")
print(f"✅ Apuestas de finalistas: {len(finalistas)}")

if quinielas:
    print(f"\n⚠️ APUESTAS ENCONTRADAS (de prueba?):")
    for q in quinielas[:5]:
        usuario_id = q.get('usuario_id')
        partido_id = q.get('partido_id')
        tipo = q.get('tipo')
        puntos = q.get('puntos_finales')
        print(f"   - Usuario {usuario_id}, Partido {partido_id}, Tipo {tipo}, Puntos {puntos}")
    if len(quinielas) > 5:
        print(f"   ... y {len(quinielas) - 5} más")
else:
    print("\n✅ NO hay apuestas - BD limpia")

if finalistas:
    print(f"\n⚠️ FINALISTAS ENCONTRADOS (de prueba?):")
    for f in finalistas[:5]:
        usuario_id = f.get('usuario_id')
        puntos = f.get('puntos')
        print(f"   - Usuario {usuario_id}, Puntos {puntos}")
else:
    print("\n✅ NO hay finalistas - BD limpia")

# Obtener usuarios y verificar si hay de prueba
usuarios_resp = client.table('usuarios').select('*').execute()
usuarios = usuarios_resp.data

print(f"\n📊 Total usuarios en el sistema:")
for u in usuarios:
    nombre = u.get('nombre')
    es_admin = u.get('es_admin', False)
    admin_str = " [ADMIN]" if es_admin else ""
    print(f"   - {nombre}{admin_str}")

print("\n" + "=" * 80)
