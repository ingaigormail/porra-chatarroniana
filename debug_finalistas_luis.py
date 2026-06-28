# debug_finalistas_luis.py
# Debuggeo del problema con usuario Luis y selección de finalistas

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.database import Database

print("="*70)
print("🔍 DEBUG: Problema con Finalistas en usuario Luis")
print("="*70)

db = Database()

# Obtener usuarios
usuarios = db.obtener_usuarios()
print(f"\n✅ Total usuarios: {len(usuarios)}")
for _, usr in usuarios.iterrows():
    print(f"   • {usr['nombre']} (ID: {usr['id']})")

# Obtener equipos
equipos = db.obtener_equipos()
print(f"\n✅ Total equipos: {len(equipos)}")

# Filtrar equipos vivos (puntos > 0)
equipos_vivos = equipos[equipos['puntos'] > 0]
print(f"✅ Equipos vivos (puntos > 0): {len(equipos_vivos)}")
print(f"❌ Equipos muertos (puntos = 0): {len(equipos[equipos['puntos'] <= 0])}")

print("\n📋 Equipos vivos:")
for _, eq in equipos_vivos.iterrows():
    print(f"   • {eq['nombre']} (ID: {eq['id']}, Puntos: {eq['puntos']})")

# Obtener ID de Luis
luis_id = int(usuarios[usuarios['nombre'] == 'Luis']['id'].values[0])
print(f"\n👤 Usuario Luis - ID: {luis_id}")

# Verificar apuestas actuales de Luis
finalistas_luis = db.client.table('finalistas_apostados')\
    .select('*')\
    .eq('usuario_id', luis_id)\
    .execute()

print(f"\n📊 Apuestas de finalistas de Luis:")
if finalistas_luis.data:
    for apuesta in finalistas_luis.data:
        print(f"   • Finalista 1 ID: {apuesta['finalista_1_id']}")
        print(f"   • Finalista 2 ID: {apuesta['finalista_2_id']}")
        print(f"   • Puntos: {apuesta.get('puntos', 0)}")
else:
    print(f"   ⚠️ No tiene apuestas de finalistas")

# Obtener ID de Bro
bro_id = int(usuarios[usuarios['nombre'] == 'Bro']['id'].values[0])
print(f"\n👤 Usuario Bro - ID: {bro_id}")

# Verificar apuestas actuales de Bro
finalistas_bro = db.client.table('finalistas_apostados')\
    .select('*')\
    .eq('usuario_id', bro_id)\
    .execute()

print(f"\n📊 Apuestas de finalistas de Bro:")
if finalistas_bro.data:
    for apuesta in finalistas_bro.data:
        print(f"   • Finalista 1 ID: {apuesta['finalista_1_id']}")
        print(f"   • Finalista 2 ID: {apuesta['finalista_2_id']}")
        print(f"   • Puntos: {apuesta.get('puntos', 0)}")
else:
    print(f"   ⚠️ No tiene apuestas de finalistas")

# Verificar la lógica del selectbox
print("\n" + "="*70)
print("🔧 ANÁLISIS DE LA LÓGICA DEL SELECTBOX")
print("="*70)

equipos_list = equipos_vivos['nombre'].tolist()
equipos_ids = equipos_vivos['id'].tolist()
equipos_dict = dict(zip(equipos_ids, equipos_list))

print(f"\nEquipos en el diccionario: {len(equipos_dict)}")
print(f"Equipos en la lista: {len(equipos_list)}")

# Simular lo que pasa para Luis
print(f"\n👤 Simulando selectbox para Luis:")
if finalistas_luis.data:
    finalista_1_actual = finalistas_luis.data[0]['finalista_1_id']
    print(f"   Finalista 1 actual: {finalista_1_actual}")
    print(f"   ¿Está en equipos_dict?: {finalista_1_actual in equipos_dict}")
    if finalista_1_actual in equipos_dict:
        nombre_equipo = equipos_dict.get(finalista_1_actual)
        print(f"   Nombre del equipo: {nombre_equipo}")
        print(f"   ¿Está en equipos_list?: {nombre_equipo in equipos_list}")
        if nombre_equipo in equipos_list:
            indice = equipos_list.index(nombre_equipo)
            print(f"   Índice en lista: {indice}")
            print(f"   Índice para selectbox: {indice + 1}")
else:
    print("   No tiene apuestas, índice por defecto: 0")

print("\n" + "="*70)
print("💡 CONCLUSIÓN")
print("="*70)
print("""
El problema podría ser:
1. La lista de equipos_vivos está vacía para Luis
2. Los IDs de apuestas anteriores de Luis no existen en equipos_vivos
3. El selectbox no encuentra el índice correcto

Verifica que:
- Los equipos vivos sean los mismos para ambos usuarios
- Los IDs de los finalistas guardados sean válidos
""")
