# resetear_y_actualizar.py
"""
LIMPIEZA + ACTUALIZACIÓN DE RESULTADOS (SIN RECALCULAR PUNTOS)
- Lee el Excel y actualiza partidos 1-72
- Borra todos los datos de pruebas
- Resetea partidos 73-104
- Los puntos se recalculan desde Admin (botón "Recalcular")
"""

import pandas as pd
from src.database import Database

# =============================================
# CONFIGURACIÓN
# =============================================
SHEET_ID = "1NncO0BuIR8BeYNz8a-VIUODFRx6rdDRwa0xZJQypG44"
URL_CALENDARIO = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=calendario"

def limpiar_texto(texto):
    if pd.isna(texto) or texto == "" or texto == "nan":
        return ""
    return str(texto).strip()

# =============================================
# CONEXIÓN
# =============================================
print("🔌 Conectando a Supabase...")
db = Database()
print("✅ Conectado")

# =============================================
# 1. LEER EXCEL
# =============================================
print("\n📖 Leyendo calendario desde Google Sheets...")
df_calendario = pd.read_csv(URL_CALENDARIO)
print(f"✅ {len(df_calendario)} partidos leídos")

# =============================================
# 2. ACTUALIZAR PARTIDOS 1-72
# =============================================
print("\n⚽ Actualizando fase de grupos (1-72)...")
partidos_actualizados = 0
partidos_sin_cambios = 0

partidos_supabase = db.obtener_partidos()
partidos_grupos = partidos_supabase[partidos_supabase['id'] <= 72]

for _, row in partidos_grupos.iterrows():
    partido_id = row['id']
    excel_row = df_calendario[df_calendario['Partido_ID'] == partido_id]
    if excel_row.empty:
        continue
    
    excel_row = excel_row.iloc[0]
    goles_local = limpiar_texto(excel_row.get('Goles_1', ''))
    goles_visitante = limpiar_texto(excel_row.get('Goles_2', ''))
    
    # Determinar estado y goles
    try:
        if goles_local and goles_local != '' and goles_visitante and goles_visitante != '':
            gl = int(float(goles_local))
            gv = int(float(goles_visitante))
            estado = 'Jugado'
        else:
            gl = 0
            gv = 0
            estado = 'Pendiente'
    except (ValueError, TypeError):
        gl = 0
        gv = 0
        estado = 'Pendiente'
    
    # Actualizar solo si hay cambios
    if (row['goles_local'] != gl or row['goles_visitante'] != gv or row['estado'] != estado):
        db.client.table('partidos').update({
            'goles_local': gl,
            'goles_visitante': gv,
            'estado': estado
        }).eq('id', partido_id).execute()
        partidos_actualizados += 1
        print(f"  ✅ Partido {partido_id}: {gl} - {gv} ({estado})")
    else:
        partidos_sin_cambios += 1

print(f"✅ Actualizados: {partidos_actualizados} | Sin cambios: {partidos_sin_cambios}")

# =============================================
# 3. BORRAR DATOS DE PRUEBAS
# =============================================
print("\n🧹 Eliminando datos de pruebas...")

# 3.1 Quinielas
response = db.client.table('quinielas').select('count', count='exact').execute()
count_quinielas = response.count
db.client.table('quinielas').delete().neq('id', 0).execute()
print(f"  ✅ Quinielas: {count_quinielas} registros")

# 3.2 Finalistas
response = db.client.table('finalistas_apostados').select('count', count='exact').execute()
count_finalistas = response.count
db.client.table('finalistas_apostados').delete().neq('id', 0).execute()
print(f"  ✅ Finalistas: {count_finalistas} registros")

# 3.3 Progresión
response = db.client.table('progresion_equipos').select('count', count='exact').execute()
count_progresion = response.count
db.client.table('progresion_equipos').delete().neq('id', 0).execute()
print(f"  ✅ Progresión: {count_progresion} registros")

# 3.4 Histórico
response = db.client.table('historico_puntos').select('count', count='exact').execute()
count_historico = response.count
db.client.table('historico_puntos').delete().neq('id', 0).execute()
print(f"  ✅ Snapshots: {count_historico} registros")

# 3.5 Auditoría
response = db.client.table('auditoria').select('count', count='exact').execute()
count_auditoria = response.count
db.client.table('auditoria').delete().neq('id', 0).execute()
print(f"  ✅ Auditoría: {count_auditoria} registros")

# =============================================
# 4. RESETEAR PARTIDOS 73-104
# =============================================
print("\n🔄 Resetando eliminatorias (73-104)...")
db.client.table('partidos').update({
    'estado': 'Pendiente',
    'goles_local': None,
    'goles_visitante': None,
    'hubo_prorroga': False,
    'ganador_prorroga': None,
    'tipo_apuesta': 'ninguno',
    'apuestas_abiertas': False,
    'equipo_local_id': None,
    'equipo_visitante_id': None
}).gte('id', 73).lte('id', 104).execute()
print(f"✅ 32 partidos reseteados")

# =============================================
# 5. RESUMEN FINAL
# =============================================
print("\n" + "="*60)
print("🎉 ¡PROCESO COMPLETADO!")
print("="*60)
print(f"""
📋 RESUMEN:
  • Partidos actualizados: {partidos_actualizados}
  • Quinielas eliminadas: {count_quinielas}
  • Finalistas eliminados: {count_finalistas}
  • Progresión eliminada: {count_progresion}
  • Snapshots eliminados: {count_historico}
  • Partidos 73-104 reseteados: 32

✅ BBDD limpia y actualizada.
🚀 Ahora ejecuta 'streamlit run app.py' y usa el botón "Recalcular Puntos de Equipos" en Admin.
""")