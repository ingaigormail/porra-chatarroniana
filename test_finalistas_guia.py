# test_finalistas_guia.py
# ============================================================
# GUÍA PASO A PASO PARA PROBAR LA FUNCIONALIDAD DE FINALISTAS
# ============================================================

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.database import Database

print("\n" + "="*70)
print("🏆 GUÍA DE PRUEBAS: APOSTAR Y CALCULAR FINALISTAS")
print("="*70)

# Inicializar la base de datos
db = Database()

# ============================================================
# PASO 1: OBTENER DATOS INICIALES
# ============================================================
print("\n📋 PASO 1: Obtener datos iniciales")
print("-" * 70)

# Obtener usuarios
usuarios = db.obtener_usuarios()
print(f"✅ {len(usuarios)} usuarios encontrados:")
for idx, usuario in usuarios.iterrows():
    print(f"   • {usuario['nombre']} (ID: {usuario['id']})")

# Obtener equipos
equipos = db.obtener_equipos()
print(f"\n✅ {len(equipos)} equipos disponibles:")
primeros_5_equipos = equipos.head(10)
for idx, equipo in primeros_5_equipos.iterrows():
    print(f"   • {equipo['nombre']} (ID: {equipo['id']})")

# ============================================================
# PASO 2: SIMULAR APUESTAS DE FINALISTAS
# ============================================================
print("\n\n🎯 PASO 2: Simular apuestas de finalistas")
print("-" * 70)

# Seleccionar usuarios y equipos para las apuestas
if len(usuarios) > 0 and len(equipos) >= 2:
    usuario_1 = usuarios.iloc[0]
    usuario_1_id = int(usuario_1['id'])
    usuario_1_nombre = usuario_1['nombre']
    
    # Seleccionar dos equipos diferentes para apostar
    equipo_1 = equipos.iloc[0]
    equipo_2 = equipos.iloc[1]
    equipo_1_id = int(equipo_1['id'])
    equipo_2_id = int(equipo_2['id'])
    
    print(f"\n🧪 Test 1: Apostar finalistas")
    print(f"   Usuario: {usuario_1_nombre} (ID: {usuario_1_id})")
    print(f"   Finalista 1: {equipo_1['nombre']} (ID: {equipo_1_id})")
    print(f"   Finalista 2: {equipo_2['nombre']} (ID: {equipo_2_id})")
    
    resultado = db.apostar_finalistas(usuario_1_id, equipo_1_id, equipo_2_id)
    print(f"\n   Resultado: {resultado}")
    
    if resultado['success']:
        print(f"   ✅ Apuesta guardada exitosamente!")
    else:
        print(f"   ❌ Error al guardar la apuesta")

# ============================================================
# PASO 3: VERIFICAR APUESTAS GUARDADAS
# ============================================================
print("\n\n🔍 PASO 3: Verificar apuestas guardadas")
print("-" * 70)

try:
    apuestas_guardadas = db.client.table('finalistas_apostados')\
        .select('*, usuarios(nombre), equipos:finalista_1_id(nombre), equipos_2:finalista_2_id(nombre)')\
        .execute()
    
    if apuestas_guardadas.data:
        print(f"\n✅ {len(apuestas_guardadas.data)} apuesta(s) encontrada(s):")
        for idx, apuesta in enumerate(apuestas_guardadas.data, 1):
            usuario_nombre = apuesta['usuarios']['nombre'] if apuesta['usuarios'] else 'Desconocido'
            print(f"\n   Apuesta #{idx}:")
            print(f"   • Usuario: {usuario_nombre}")
            print(f"   • Finalista 1 ID: {apuesta['finalista_1_id']}")
            print(f"   • Finalista 2 ID: {apuesta['finalista_2_id']}")
            print(f"   • Fecha: {apuesta.get('fecha_apuesta', 'N/A')}")
            print(f"   • Puntos: {apuesta.get('puntos', 0)}")
    else:
        print("\n⚠️ No hay apuestas de finalistas registradas aún")
except Exception as e:
    print(f"\n❌ Error al obtener apuestas: {str(e)}")

# ============================================================
# PASO 4: SIMULAR CÁLCULO DE PUNTOS DE FINALISTAS
# ============================================================
print("\n\n🏆 PASO 4: Calcular puntos de finalistas")
print("-" * 70)

# Para este test, seleccionamos dos equipos como "ganadores reales"
if len(equipos) >= 2:
    finalista_1_real = equipos.iloc[0]
    finalista_2_real = equipos.iloc[1]
    
    finalista_1_real_id = int(finalista_1_real['id'])
    finalista_2_real_id = int(finalista_2_real['id'])
    
    print(f"\n📊 Finalistas reales (simulados):")
    print(f"   Finalista 1: {finalista_1_real['nombre']} (ID: {finalista_1_real_id})")
    print(f"   Finalista 2: {finalista_2_real['nombre']} (ID: {finalista_2_real_id})")
    
    print(f"\n🧪 Calculando puntos...")
    resultado_calc = db.calcular_puntos_finalistas(
        finalista_1_real_id, 
        finalista_2_real_id
    )
    
    print(f"\n   Resultado: {resultado_calc}")
    
    if resultado_calc['success']:
        print(f"   ✅ Puntos calculados exitosamente!")
        print(f"   Mensaje: {resultado_calc['message']}")
    else:
        print(f"   ❌ Error al calcular puntos")

# ============================================================
# PASO 5: VERIFICAR PUNTOS ASIGNADOS
# ============================================================
print("\n\n✅ PASO 5: Verificar puntos asignados a usuarios")
print("-" * 70)

try:
    apuestas_finales = db.client.table('finalistas_apostados')\
        .select('*, usuarios(nombre)')\
        .execute()
    
    if apuestas_finales.data:
        print(f"\n🏆 Resumen de puntos de finalistas:")
        print(f"\n{'Usuario':<20} {'Puntos':<10} {'Estado':<15}")
        print("-" * 45)
        
        for apuesta in apuestas_finales.data:
            usuario_nombre = apuesta['usuarios']['nombre'] if apuesta['usuarios'] else 'Desconocido'
            puntos = apuesta.get('puntos', 0)
            
            if puntos == 10:
                estado = "🥇 Acertó ambos"
            elif puntos == 4:
                estado = "🥈 Acertó uno"
            elif puntos == 0:
                estado = "❌ No acertó"
            else:
                estado = "❓ Pendiente"
            
            print(f"{usuario_nombre:<20} {str(puntos):<10} {estado:<15}")
    else:
        print("\n⚠️ No hay apuestas para verificar")
except Exception as e:
    print(f"\n❌ Error: {str(e)}")

# ============================================================
# PASO 6: RESUMEN Y PRÓXIMOS PASOS
# ============================================================
print("\n\n" + "="*70)
print("📝 RESUMEN DE LA PRUEBA")
print("="*70)

print("""
✅ PASOS COMPLETADOS:
   1. ✓ Se obtuvieron usuarios y equipos de la BD
   2. ✓ Se simuló una apuesta de finalistas
   3. ✓ Se verificaron las apuestas guardadas
   4. ✓ Se calcularon los puntos de finalistas
   5. ✓ Se verificaron los puntos asignados

📌 PRÓXIMOS PASOS EN EL ADMIN PANEL:
   1. Ve a la pestaña "🔧 Admin" en la app
   2. Busca la sección "🏆 Gestión de Apuesta de Finalistas"
   3. Activa la casilla "Activar apuesta de finalistas"
   4. Ve a "🏆 Calcular Finalistas"
   5. Selecciona los 2 equipos finalistas
   6. Revisa quién apostó y quién no
   7. Haz clic en "✅ Calcular y Aplicar Puntos de Finalistas"

⚙️ VARIABLES CLAVE:
   • 10 puntos: Si acertaste AMBOS finalistas
   • 4 puntos: Si acertaste UNO de los dos
   • 0 puntos: Si no acertaste ninguno

""")

print("="*70)
print("✅ PRUEBA COMPLETADA\n")
