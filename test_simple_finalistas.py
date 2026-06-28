#!/usr/bin/env python3
"""Test simple sin Streamlit para validar la función"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Importar sin Streamlit
from supabase import create_client
import pandas as pd

# Configurar manualmente las credenciales
try:
    with open('.streamlit/secrets.toml', 'r') as f:
        import re
        content = f.read()
        url = re.search(r'url = "(.*?)"', content).group(1)
        key = re.search(r'key = "(.*?)"', content).group(1)
except:
    print("❌ No se encontró .streamlit/secrets.toml")
    sys.exit(1)

print("=" * 70)
print("🧪 TEST SIMPLE: obtener_apuestas_usuario_finalistas()")
print("=" * 70)

try:
    # Conectar a Supabase
    print("\n📡 Conectando a Supabase...")
    client = create_client(url, key)
    print("✅ Conexión exitosa")
    
    # Obtener usuarios
    print("\n👥 Obteniendo usuarios...")
    usuarios_resp = client.table('usuarios').select('id, nombre').execute()
    usuarios = usuarios_resp.data
    
    if not usuarios:
        print("❌ No hay usuarios")
        sys.exit(1)
    
    print(f"✅ {len(usuarios)} usuarios encontrados")
    
    # Seleccionar primer usuario
    usuario_id = usuarios[0]['id']
    usuario_nombre = usuarios[0]['nombre']
    print(f"   Usuario: {usuario_nombre} (ID: {usuario_id})")
    
    # Obtener finalistas apostados por este usuario
    print(f"\n🔍 Obteniendo apuestas de finalistas para {usuario_nombre}...")
    finalistas_resp = client.table('finalistas_apostados')\
        .select('*')\
        .eq('usuario_id', usuario_id)\
        .execute()
    
    finalistas_data = finalistas_resp.data
    print(f"✅ {len(finalistas_data)} apuestas encontradas")
    
    if not finalistas_data:
        print("   ℹ️ Este usuario no tiene apuestas de finalistas")
    else:
        # Obtener IDs de equipos
        equipos_ids = []
        for item in finalistas_data:
            if item.get('finalista_1_id'):
                equipos_ids.append(item['finalista_1_id'])
            if item.get('finalista_2_id'):
                equipos_ids.append(item['finalista_2_id'])
        
        # Obtener nombres de equipos
        print(f"\n📋 Obteniendo nombres de {len(set(equipos_ids))} equipos...")
        equipos_resp = client.table('equipos')\
            .select('id, nombre')\
            .in_('id', list(set(equipos_ids)))\
            .execute()
        
        equipos_dict = {eq['id']: eq['nombre'] for eq in equipos_resp.data}
        print(f"✅ {len(equipos_dict)} equipos cargados")
        
        # Mostrar apuestas
        print(f"\n📊 Apuestas de finalistas:")
        for idx, item in enumerate(finalistas_data, 1):
            f1_nombre = equipos_dict.get(item['finalista_1_id'], '?')
            f2_nombre = equipos_dict.get(item['finalista_2_id'], '?')
            puntos = item.get('puntos', 0)
            
            print(f"\n   Apuesta #{idx}:")
            print(f"      {f1_nombre} vs {f2_nombre}")
            print(f"      Puntos: {puntos}")
    
    print("\n" + "=" * 70)
    print("✅ TEST COMPLETADO EXITOSAMENTE")
    print("=" * 70)
    
except Exception as e:
    print(f"\n❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
