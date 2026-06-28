# importar_datos.py
"""
IMPORTADOR DE DATOS - MUNDIAL 2026
Lee los datos de Google Sheets y los guarda en Supabase
Ejecutar UNA SOLA VEZ para migrar los datos
"""

import pandas as pd
from supabase import create_client
import unicodedata
from datetime import datetime

# =============================================
# CONFIGURACIÓN - CAMBIA ESTOS DATOS
# =============================================

# Tus credenciales de Supabase (cópialas de la página de API)
SUPABASE_URL = "https://drzqnzruoydlidnpyyxy.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRyenFuenJ1b3lkbGlkbnB5eXh5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODIzMDg3NTYsImV4cCI6MjA5Nzg4NDc1Nn0.2UMAe8AbRZon9jW9XRbXjzWfmFX8By7crmy8AtF2L3Q"  # 👈 PON AQUÍ TU CLAVE anon public COMPLETA

# ID de tu Google Sheets (el que usas en tu app)
SHEET_ID = "1NncO0BuIR8BeYNz8a-VIUODFRx6rdDRwa0xZJQypG44"

# =============================================
# FUNCIONES PARA LEER GOOGLE SHEETS
# =============================================

def leer_google_sheets():
    """
    Lee los datos de Google Sheets usando el método público (CSV)
    """
    print("📖 Leyendo datos de Google Sheets...")
    
    # URLs de exportación
    url_equipos = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=equipos"
    url_participantes = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Participantes"
    url_calendario = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=calendario"
    
    # Leer los CSV
    df_equipos = pd.read_csv(url_equipos)
    df_participantes = pd.read_csv(url_participantes)
    df_calendario = pd.read_csv(url_calendario)
    
    print(f"✅ Equipos: {len(df_equipos)} registros")
    print(f"✅ Participantes: {len(df_participantes)} registros")
    print(f"✅ Calendario: {len(df_calendario)} registros")
    
    return df_equipos, df_participantes, df_calendario

def limpiar_texto(texto):
    """Limpia texto para evitar errores"""
    if pd.isna(texto) or texto == "" or texto == "nan":
        return ""
    return str(texto).strip()

def normalizar_nombre(nombre):
    """Quita tildes y espacios para comparar nombres"""
    nombre = limpiar_texto(nombre)
    if not nombre:
        return ""
    # Quitar tildes
    nombre = ''.join(c for c in unicodedata.normalize('NFD', nombre) 
                     if unicodedata.category(c) != 'Mn')
    return nombre.strip().lower()

# =============================================
# FUNCIONES PARA PREPARAR DATOS
# =============================================

def preparar_equipos_sin_stats(df_equipos):
    """Prepara los equipos SIN estadísticas (solo nombre y grupo)"""
    print("\n📦 Preparando equipos (sin estadísticas)...")
    
    col_nombre = df_equipos.columns[0]
    col_grupo = "Grupo" if "Grupo" in df_equipos.columns else None
    
    equipos = []
    for _, row in df_equipos.iterrows():
        nombre = limpiar_texto(row[col_nombre])
        grupo = limpiar_texto(row[col_grupo]) if col_grupo else ""
        
        if nombre:
            equipos.append({
                'nombre': nombre,
                'grupo': grupo,
                'factor_fifa': 0.85,
                'pj': 0, 'ganados': 0, 'empatados': 0, 'perdidos': 0,
                'gf': 0, 'gc': 0, 'dg': 0, 'puntos': 0
            })
    
    print(f"✅ {len(equipos)} equipos preparados")
    return equipos

def preparar_usuarios(df_participantes):
    """Prepara los usuarios para insertar en Supabase"""
    print("\n👤 Preparando usuarios...")
    
    # Buscar columna de nombre
    col_nombre = None
    for col in df_participantes.columns:
        if 'nombre' in str(col).lower():
            col_nombre = col
            break
    
    if not col_nombre:
        raise Exception("No se encontró columna de nombre")
    
    usuarios = []
    for _, row in df_participantes.iterrows():
        nombre = limpiar_texto(row[col_nombre])
        if nombre:
            usuarios.append({'nombre': nombre})
    
    print(f"✅ {len(usuarios)} usuarios preparados")
    return usuarios

def preparar_selecciones(df_participantes, equipos_map):
    """Prepara las selecciones de cada usuario"""
    print("\n📝 Preparando selecciones...")
    
    # Buscar columnas de equipos (las que empiezan por G)
    cols_equipos = []
    for col in df_participantes.columns:
        col_str = str(col).strip()
        if col_str.startswith('G') and 'pts_' not in col_str.lower():
            cols_equipos.append(col_str)
    
    # Buscar columna de nombre
    col_nombre = None
    for col in df_participantes.columns:
        if 'nombre' in str(col).lower():
            col_nombre = col
            break
    
    selecciones = []
    for _, row in df_participantes.iterrows():
        nombre = limpiar_texto(row[col_nombre])
        if not nombre:
            continue
        
        for col_eq in cols_equipos:
            equipo = limpiar_texto(row[col_eq])
            if equipo:
                # Buscar el ID del equipo por su nombre normalizado
                equipo_id = None
                for eq_nombre, eq_id in equipos_map.items():
                    if normalizar_nombre(eq_nombre) == normalizar_nombre(equipo):
                        equipo_id = eq_id
                        break
                
                if equipo_id:
                    selecciones.append({
                        'usuario_nombre': nombre,
                        'equipo_id': equipo_id,
                        'grupo_seleccion': col_eq.replace('_Equipo', '').replace('_', '')
                    })
    
    print(f"✅ {len(selecciones)} selecciones preparadas")
    return selecciones

def preparar_partidos(df_calendario, equipos_map):
    """Prepara los partidos para insertar"""
    print("\n⚽ Preparando partidos...")
    
    # Mostrar columnas para diagnóstico
    print("📋 Columnas del calendario:", list(df_calendario.columns))
    
    partidos = []
    partido_id = 1
    
    for _, row in df_calendario.iterrows():
        equipo1 = limpiar_texto(row.get('Equipo_1', ''))
        equipo2 = limpiar_texto(row.get('Equipo_2', ''))
        fase = limpiar_texto(row.get('Fase ', ''))
        
        # Conversión de fecha
        fecha = row.get('Fecha', '')
        fecha_formateada = None
        if fecha and fecha != '':
            try:
                fecha_obj = datetime.strptime(str(fecha), '%d/%m/%Y')
                fecha_formateada = fecha_obj.strftime('%Y-%m-%d')
            except:
                try:
                    fecha_obj = datetime.strptime(str(fecha), '%Y-%m-%d')
                    fecha_formateada = fecha_obj.strftime('%Y-%m-%d')
                except:
                    fecha_formateada = None
        
        if equipo1 and equipo2:
            # Buscar IDs por nombre normalizado
            equipo1_id = None
            equipo2_id = None
            
            for eq_nombre, eq_id in equipos_map.items():
                if normalizar_nombre(eq_nombre) == normalizar_nombre(equipo1):
                    equipo1_id = eq_id
                if normalizar_nombre(eq_nombre) == normalizar_nombre(equipo2):
                    equipo2_id = eq_id
            
            if equipo1_id and equipo2_id:
                # Obtener goles
                goles1 = row.get('Goles_1', 0)
                goles2 = row.get('Goles_2', 0)
                
                # LEER EL ESTADO DEL EXCEL
                estado_excel = ''
                for col in df_calendario.columns:
                    col_clean = str(col).strip().lower()
                    if 'estado' in col_clean:
                        estado_excel = limpiar_texto(row[col])
                        break
                
                # Si no encuentra "estado", usar los goles como respaldo
                if estado_excel == '':
                    if pd.notna(goles1) and goles1 != '' and goles1 != 0:
                        estado_excel = 'Jugado'
                    else:
                        estado_excel = 'Pendiente'
                
                # Aplicar el estado
                if estado_excel == 'Jugado':
                    estado = 'Jugado'
                    goles_local = int(goles1) if pd.notna(goles1) and goles1 != '' else 0
                    goles_visitante = int(goles2) if pd.notna(goles2) and goles2 != '' else 0
                else:
                    estado = 'Pendiente'
                    goles_local = 0
                    goles_visitante = 0
                
                partidos.append({
                    'id': partido_id,
                    'fase': fase if fase else 'Grupos',
                    'fecha': fecha_formateada,
                    'equipo_local_id': equipo1_id,
                    'goles_local': goles_local,
                    'equipo_visitante_id': equipo2_id,
                    'goles_visitante': goles_visitante,
                    'estado': estado
                })
                partido_id += 1
    
    print(f"✅ {len(partidos)} partidos preparados")
    return partidos

# =============================================
# FUNCIONES PARA CALCULAR ESTADÍSTICAS
# =============================================

def calcular_estadisticas_equipos(partidos, equipos_map):
    """
    Calcula PJ, Ganados, Empatados, Perdidos, GF, GC, DG, Puntos
    a partir de los partidos jugados
    """
    print("\n📊 Calculando estadísticas de equipos...")
    
    # Inicializar estadísticas para todos los equipos
    stats = {}
    for equipo_id in equipos_map.values():
        stats[equipo_id] = {
            'pj': 0, 'ganados': 0, 'empatados': 0, 'perdidos': 0,
            'gf': 0, 'gc': 0, 'dg': 0, 'puntos': 0
        }
    
    # Procesar solo partidos jugados
    for partido in partidos:
        if partido['estado'] != 'Jugado':
            continue
        
        local_id = partido['equipo_local_id']
        visitante_id = partido['equipo_visitante_id']
        gl = partido['goles_local']
        gv = partido['goles_visitante']
        
        # Actualizar partidos jugados
        stats[local_id]['pj'] += 1
        stats[visitante_id]['pj'] += 1
        
        # Actualizar goles
        stats[local_id]['gf'] += gl
        stats[local_id]['gc'] += gv
        stats[visitante_id]['gf'] += gv
        stats[visitante_id]['gc'] += gl
        
        # Actualizar resultados
        if gl > gv:
            stats[local_id]['ganados'] += 1
            stats[visitante_id]['perdidos'] += 1
            stats[local_id]['puntos'] += 3
        elif gv > gl:
            stats[visitante_id]['ganados'] += 1
            stats[local_id]['perdidos'] += 1
            stats[visitante_id]['puntos'] += 3
        else:
            stats[local_id]['empatados'] += 1
            stats[visitante_id]['empatados'] += 1
            stats[local_id]['puntos'] += 1
            stats[visitante_id]['puntos'] += 1
    
    # Calcular diferencia de goles
    for equipo_id in stats:
        stats[equipo_id]['dg'] = stats[equipo_id]['gf'] - stats[equipo_id]['gc']
    
    print(f"✅ Estadísticas calculadas para {len(stats)} equipos")
    return stats

# =============================================
# FUNCIONES PARA INSERTAR EN SUPABASE
# =============================================

def insertar_equipos(supabase, equipos):
    """Inserta equipos en Supabase y devuelve mapa nombre -> id"""
    print("\n📤 Insertando equipos en Supabase...")
    
    mapa = {}
    for equipo in equipos:
        # Verificar si ya existe
        existing = supabase.table('equipos')\
            .select('id')\
            .eq('nombre', equipo['nombre'])\
            .execute()
        
        if existing.data:
            mapa[equipo['nombre']] = existing.data[0]['id']
            print(f"  ⏭️ {equipo['nombre']} ya existe")
        else:
            result = supabase.table('equipos').insert(equipo).execute()
            if result.data:
                mapa[equipo['nombre']] = result.data[0]['id']
                print(f"  ✅ Insertado: {equipo['nombre']}")
    
    return mapa

def actualizar_estadisticas_equipos(supabase, estadisticas):
    """Actualiza las estadísticas de los equipos en Supabase"""
    print("\n📤 Actualizando estadísticas de equipos...")
    
    for equipo_id, stats in estadisticas.items():
        supabase.table('equipos').update({
            'pj': stats['pj'],
            'ganados': stats['ganados'],
            'empatados': stats['empatados'],
            'perdidos': stats['perdidos'],
            'gf': stats['gf'],
            'gc': stats['gc'],
            'dg': stats['dg'],
            'puntos': stats['puntos']
        }).eq('id', equipo_id).execute()
    
    print(f"✅ Estadísticas actualizadas para {len(estadisticas)} equipos")

def insertar_usuarios(supabase, usuarios):
    """Inserta usuarios en Supabase y devuelve mapa nombre -> id"""
    print("\n👤 Insertando usuarios en Supabase...")
    
    mapa = {}
    for usuario in usuarios:
        # Verificar si ya existe
        existing = supabase.table('usuarios')\
            .select('id')\
            .eq('nombre', usuario['nombre'])\
            .execute()
        
        if existing.data:
            mapa[usuario['nombre']] = existing.data[0]['id']
            print(f"  ⏭️ {usuario['nombre']} ya existe")
        else:
            result = supabase.table('usuarios').insert(usuario).execute()
            if result.data:
                mapa[usuario['nombre']] = result.data[0]['id']
                print(f"  ✅ Insertado: {usuario['nombre']}")
    
    return mapa

def insertar_selecciones(supabase, selecciones, usuarios_map, equipos_map):
    """Inserta las selecciones de los usuarios"""
    print("\n📝 Insertando selecciones...")
    
    contador = 0
    for seleccion in selecciones:
        usuario_id = usuarios_map.get(seleccion['usuario_nombre'])
        equipo_id = seleccion['equipo_id']
        
        if usuario_id and equipo_id:
            # Verificar si ya existe
            existing = supabase.table('selecciones')\
                .select('id')\
                .eq('usuario_id', usuario_id)\
                .eq('equipo_id', equipo_id)\
                .execute()
            
            if not existing.data:
                supabase.table('selecciones').insert({
                    'usuario_id': usuario_id,
                    'equipo_id': equipo_id,
                    'grupo_seleccion': seleccion['grupo_seleccion']
                }).execute()
                contador += 1
    
    print(f"✅ {contador} selecciones insertadas")

def insertar_partidos(supabase, partidos):
    """Inserta o actualiza los partidos"""
    print("\n⚽ Insertando/Actualizando partidos...")
    
    contador = 0
    for partido in partidos:
        # Verificar si ya existe
        existing = supabase.table('partidos')\
            .select('id')\
            .eq('id', partido['id'])\
            .execute()
        
        if existing.data:
            # ACTUALIZAR
            supabase.table('partidos').update({
                'fase': partido['fase'],
                'fecha': partido['fecha'],
                'equipo_local_id': partido['equipo_local_id'],
                'goles_local': partido['goles_local'],
                'equipo_visitante_id': partido['equipo_visitante_id'],
                'goles_visitante': partido['goles_visitante'],
                'estado': partido['estado']
            }).eq('id', partido['id']).execute()
            contador += 1
        else:
            # INSERTAR
            supabase.table('partidos').insert(partido).execute()
            contador += 1
    
    print(f"✅ {contador} partidos procesados")

# =============================================
# FUNCIÓN PRINCIPAL
# =============================================

def main():
    print("="*60)
    print("🚀 IMPORTADOR DE DATOS - MUNDIAL 2026")
    print("="*60)
    
    # 1. Conectar a Supabase
    print("\n🔌 Conectando a Supabase...")
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("✅ Conectado")
    
    # 2. Leer datos de Google Sheets
    df_equipos, df_participantes, df_calendario = leer_google_sheets()
    
    # 3. Preparar equipos (sin estadísticas aún, solo nombre y grupo)
    equipos = preparar_equipos_sin_stats(df_equipos)
    
    # 4. Insertar equipos y obtener IDs
    equipos_map = insertar_equipos(supabase, equipos)
    
    # 5. Preparar partidos (usando los IDs de equipos)
    partidos = preparar_partidos(df_calendario, equipos_map)
    
    # 6. CALCULAR estadísticas a partir de los partidos
    estadisticas = calcular_estadisticas_equipos(partidos, equipos_map)
    
    # 7. ACTUALIZAR equipos con las estadísticas calculadas
    actualizar_estadisticas_equipos(supabase, estadisticas)
    
    # 8. Insertar usuarios
    usuarios = preparar_usuarios(df_participantes)
    usuarios_map = insertar_usuarios(supabase, usuarios)
    
    # 9. Insertar selecciones
    selecciones = preparar_selecciones(df_participantes, equipos_map)
    insertar_selecciones(supabase, selecciones, usuarios_map, equipos_map)
    
    # 10. Insertar partidos
    insertar_partidos(supabase, partidos)
    
    print("\n" + "="*60)
    print("🎉 ¡IMPORTACIÓN COMPLETADA!")
    print("="*60)
    print("\n📊 Resumen:")
    print(f"  • Equipos: {len(equipos)}")
    print(f"  • Usuarios: {len(usuarios)}")
    print(f"  • Selecciones: {len(selecciones)}")
    print(f"  • Partidos: {len(partidos)}")
    print("\n✅ Ve a Table Editor en Supabase para verificar los datos.")

if __name__ == "__main__":
    main()