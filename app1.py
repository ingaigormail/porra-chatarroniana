# app.py
import streamlit as st
import pandas as pd
import unicodedata
import flag

# Configuración de la página
st.set_page_config(
    page_title="🏆 Mundial 2026 Chatarronianos",
    page_icon="⚽",
    layout="wide"
)

# Importar módulos
from src.database import Database

# Inicializar la base de datos
db = Database()

# Título
st.title("🏆 Mundial 2026 Chatarronianos")

# =============================================
# IDENTIFICACIÓN DEL USUARIO (con contraseña)
# =============================================
st.sidebar.header("🔑 Identificación")

# Obtener lista de usuarios
usuarios = db.obtener_usuarios()
lista_usuarios = usuarios['nombre'].tolist() if not usuarios.empty else []

# Inicializar sesión
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False
    st.session_state.usuario_actual = None

# Si no está autenticado, mostrar login
if not st.session_state.autenticado:
    with st.sidebar:
        st.markdown("### 🔐 Iniciar sesión")
        
        usuario_seleccionado = st.selectbox(
            "Selecciona tu nombre:",
            options=[""] + lista_usuarios
        )
        
        contraseña = st.text_input(
            "Contraseña:",
            type="password",
            placeholder="Introduce tu contraseña"
        )
        
        if st.button("🔓 Entrar", type="primary", use_container_width=True):
            if usuario_seleccionado and contraseña:
                nombre_normalizado = usuario_seleccionado.lower()
                nombre_normalizado = ''.join(c for c in unicodedata.normalize('NFD', nombre_normalizado) 
                                           if unicodedata.category(c) != 'Mn')
                
                if contraseña.lower() == nombre_normalizado:
                    st.session_state.autenticado = True
                    st.session_state.usuario_actual = usuario_seleccionado
                    st.success(f"✅ Bienvenido, {usuario_seleccionado}!")
                    st.rerun()
                else:
                    st.error("❌ Contraseña incorrecta")
            else:
                st.warning("⚠️ Selecciona un usuario y escribe tu contraseña")
    
    st.stop()

else:
    nombre_usuario = st.session_state.usuario_actual
    st.sidebar.success(f"✅ Conectado como: {nombre_usuario}")
    
    if st.sidebar.button("🚪 Cerrar sesión", use_container_width=True):
        st.session_state.autenticado = False
        st.session_state.usuario_actual = None
        st.rerun()

# =============================================
# CARGAR DATOS CON CACHÉ
# =============================================
@st.cache_data(ttl=60)
def cargar_datos():
    return {
        'equipos': db.obtener_equipos(),
        'partidos': db.obtener_partidos(),
        'clasificacion': db.obtener_clasificacion(),
        'selecciones': db.obtener_selecciones()
    }

datos = cargar_datos()

# =============================================
# PESTAÑAS
# =============================================
tab1, tab2, tab3, tab4 = st.tabs([
    "🏆 Clasificación",
    "👤 Mi Ficha",
    "📅 Calendario",
    "🔧 Admin"
])

# =============================================
# PESTAÑA 1: CLASIFICACIÓN
# =============================================
with tab1:
    st.header("🏆 Clasificación General")
    
    df_rank = datos['clasificacion']
    
    if df_rank.empty:
        st.info("Aún no hay datos de clasificación")
    else:
        # PODIO (3 PRIMEROS)
        col1, col2, col3 = st.columns(3)
        
        if len(df_rank) > 0:
            col1.metric("🥇 1º", df_rank.iloc[0]['nombre'], f"{df_rank.iloc[0]['puntos']} pts")
        if len(df_rank) > 1:
            col2.metric("🥈 2º", df_rank.iloc[1]['nombre'], f"{df_rank.iloc[1]['puntos']} pts")
        if len(df_rank) > 2:
            col3.metric("🥉 3º", df_rank.iloc[2]['nombre'], f"{df_rank.iloc[2]['puntos']} pts")
        
        st.write("---")
        
        # POZO (3 ÚLTIMOS)
        st.markdown("#### 🐢 El Pozo (Los 3 últimos clasificados)")
        col_paq1, col_paq2, col_paq3 = st.columns(3)
        
        total_jugadores = len(df_rank)
        
        if total_jugadores > 0:
            paq1 = df_rank.iloc[-1]
            col_paq1.metric("💩 Último", paq1['nombre'], f"{paq1['puntos']} pts")
        if total_jugadores > 1:
            paq2 = df_rank.iloc[-2]
            col_paq2.metric("🐌 Penúltimo", paq2['nombre'], f"{paq2['puntos']} pts")
        if total_jugadores > 2:
            paq3 = df_rank.iloc[-3]
            col_paq3.metric("😅 Antepenúltimo", paq3['nombre'], f"{paq3['puntos']} pts")
        
        st.write("---")
        
        # TABLA COMPLETA CON MOVIMIENTOS
        st.subheader("📋 Clasificación Completa")
        
        df_movimientos = db.obtener_movimientos()
        
        df_tabla = df_rank.copy()
        
        if not df_movimientos.empty:
            df_tabla = df_tabla.merge(
                df_movimientos[['nombre', 'cambio', 'tipo']],
                on='nombre',
                how='left'
            )
            
            def formatear_cambio(row):
                cambio = row.get('cambio', 0)
                tipo = row.get('tipo', 'mantiene')
                if tipo == 'sube':
                    return f"🟢 ↑ +{int(cambio)}"
                elif tipo == 'baja':
                    return f"🔴 ↓ {int(cambio)}"
                else:
                    return "⚪ ="
            
            df_tabla['Cambio'] = df_tabla.apply(formatear_cambio, axis=1)
        else:
            def calcular_cambio_simulado(row):
                pos = row['posicion']
                if pos <= 3:
                    return "🟢 ↑ +1"
                elif pos >= total_jugadores - 2:
                    return "🔴 ↓ -1"
                else:
                    return "⚪ ="
            
            df_tabla['Cambio'] = df_tabla.apply(calcular_cambio_simulado, axis=1)
        
        col_izq, col_centro, col_der = st.columns([1, 2, 1])
        with col_centro:
            st.dataframe(
                df_tabla[['posicion', 'nombre', 'puntos', 'Cambio']],
                hide_index=True,
                use_container_width=True,
                column_config={
                    'posicion': st.column_config.TextColumn('Pos', width='small'),
                    'nombre': st.column_config.TextColumn('Jugador', width='medium'),
                    'puntos': st.column_config.NumberColumn('Puntos', width='small', format='%d'),
                    'Cambio': st.column_config.TextColumn('Cambio', width='small')
                }
            )
        
        st.write("---")
        
        # ESTADO DE PARTIDOS Y FASES
        st.subheader("📅 Estado de Partidos y Fases 🏟️")
        
        partidos = datos['partidos']
        
        if not partidos.empty:
            orden_fases = ['Grupos', 'Dieciseis', 'Octavos', 'Cuartos', 'Semifinal', '3 y 4', 'Final']
            fases_disponibles = partidos['fase'].unique().tolist()
            fases_ordenadas = [f for f in orden_fases if f in fases_disponibles]
            fases_extra = [f for f in fases_disponibles if f not in orden_fases]
            fases_ordenadas.extend(sorted(fases_extra))
            
            for fase in fases_ordenadas:
                df_fase = partidos[partidos['fase'] == fase]
                jugados = len(df_fase[df_fase['estado'] == 'Jugado'])
                pendientes = len(df_fase[df_fase['estado'] == 'Pendiente'])
                
                if 'grupo' in fase.lower():
                    icono = "🌍"
                elif any(x in fase.lower() for x in ['dieciseis', 'octavos']):
                    icono = "⚔️"
                else:
                    icono = "🏆"
                
                with st.container(border=True):
                    st.markdown(f"#### {icono} Fase: {fase}")
                    col_j, col_p = st.columns(2)
                    col_j.metric("Jugados ⚽", jugados)
                    col_p.metric("Pendientes ⏳", pendientes)
        else:
            st.info("No hay datos de partidos")
        
        st.write("---")
        
        # MOVIMIENTOS DE LA SEMANA
        st.subheader("🚀 Movimientos de la Semana")
        
        df_mov = df_rank.copy()
        
        if not df_movimientos.empty:
            df_mov = df_mov.merge(
                df_movimientos[['nombre', 'cambio', 'tipo']],
                on='nombre',
                how='left'
            )
        else:
            movimientos = []
            for i, row in df_mov.iterrows():
                pos = row['posicion']
                if pos <= 3:
                    movimientos.append({'nombre': row['nombre'], 'cambio': 33 - (pos - 1) * 2, 'tipo': 'sube'})
                elif pos >= total_jugadores - 2:
                    movimientos.append({'nombre': row['nombre'], 'cambio': 0, 'tipo': 'baja'})
                else:
                    movimientos.append({'nombre': row['nombre'], 'cambio': 0, 'tipo': 'mantiene'})
            
            df_mov['cambio'] = [m['cambio'] for m in movimientos]
            df_mov['tipo'] = [m['tipo'] for m in movimientos]
        
        col_sube, col_baja = st.columns(2)
        
        with col_sube:
            st.markdown("#### 📈 Los que más han subido")
            top_subida = df_mov[df_mov['tipo'] == 'sube'].sort_values('cambio', ascending=False).head(3)
            if not top_subida.empty:
                for _, row in top_subida.iterrows():
                    st.success(f"🟢 **{row['nombre']}** subió **{int(row['cambio'])} puestos** → {int(row['posicion'])}º")
            else:
                st.info("No hay movimientos de subida")
        
        with col_baja:
            st.markdown("#### 📉 Los que más han bajado")
            top_bajada = df_mov[df_mov['tipo'] == 'baja'].head(3)
            if not top_bajada.empty:
                for _, row in top_bajada.iterrows():
                    st.error(f"🔴 **{row['nombre']}** bajó **{abs(int(row['cambio']))} puestos** → {int(row['posicion'])}º")
            
            mantienen = df_mov[(df_mov['tipo'] == 'mantiene') | (df_mov['cambio'] == 0)].head(3)
            for _, row in mantienen.iterrows():
                st.info(f"⚪ **{row['nombre']}** se mantiene en {int(row['posicion'])}º")
        
        st.write("---")
        
        # MVP Y RADAR CHATARRONIANO CON BANDERAS
        # Diccionario de códigos de países
        codigos_paises = {
            "Espana": "ES", "Argentina": "AR", "Brasil": "BR", "Francia": "FR",
            "Alemania": "DE", "Portugal": "PT", "Inglaterra": "GB", "Reino Unido": "GB",
            "Mexico": "MX", "Canada": "CA", "Estados Unidos": "US", "USA": "US",
            "Paises Bajos": "NL", "Países Bajos": "NL", "Holanda": "NL",
            "Uruguay": "UY", "Colombia": "CO", "Ecuador": "EC",
            "Croacia": "HR", "Marruecos": "MA", "Japon": "JP", "Japón": "JP",
            "Belgica": "BE", "Bélgica": "BE", "Suiza": "CH",
            "Australia": "AU", "Corea del Sur": "KR", "Senegal": "SN",
            "Noruega": "NO", "Panama": "PA", "Paraguay": "PY",
            "Ghana": "GH", "Costa de Marfil": "CI", "Egipto": "EG",
            "Escocia": "GB", "Turquia": "TR", "Turquía": "TR",
            "Suecia": "SE", "Nueva Zelanda": "NZ", "Catar": "QA",
            "Arabia Saudita": "SA", "Irak": "IQ", "Jordania": "JO",
            "Austria": "AT", "Argelia": "DZ", "Tunez": "TN",
            "Sudafrica": "ZA", "Sudáfrica": "ZA", "Republica Checa": "CZ",
            "Cabo Verde": "CV", "Curazao": "CW", "Haiti": "HT",
            "Uzbekistan": "UZ", "Republica del Congo": "CG",
            "Bosnia y Herzegovina": "BA", "Iran": "IR",
            "Peru": "PE", "Chile": "CL", "Italia": "IT",
            "PaisesBajos": "NL"
        }
        
        def con_bandera(pais):
            p_limpio = str(pais).strip()
            if p_limpio == "" or p_limpio.lower() == "nan":
                return "🏳️"
            codigo = codigos_paises.get(p_limpio, None)
            if codigo:
                try:
                    return flag.flag(codigo)
                except:
                    return "⚽"
            return "⚽"
        
        col_mvp, col_radar = st.columns(2)
        
        with col_mvp:
            st.header("🌟 El Equipo MVP")
            st.info("El país que más puntos está sumando en el torneo real.")
            
            mvp_df = db.obtener_mvp()
            
            if not mvp_df.empty:
                max_puntos = mvp_df['puntos'].iloc[0]
                
                if len(mvp_df) == 1:
                    st.success(f"### {con_bandera(mvp_df.iloc[0]['nombre'])} {mvp_df.iloc[0]['nombre']} con {int(max_puntos)} puntos")
                else:
                    st.success(f"### 🏆 {int(max_puntos)} puntos")
                    for _, row in mvp_df.iterrows():
                        st.write(f"• {con_bandera(row['nombre'])} {row['nombre']}")
            else:
                st.warning("Datos del MVP no disponibles.")
        
        with col_radar:
            st.header("🎯 Radar Chatarroniano")
            
            radar_df = db.obtener_radar()
            
            if not radar_df.empty:
                favorito = radar_df.iloc[0]
                st.write(f"❤️ **El Favorito:** {con_bandera(favorito['nombre'])} {favorito['nombre']} (Elegido {favorito['votos']} veces)")
                
                lobos = radar_df[radar_df['votos'] == 1]
                if not lobos.empty:
                    lobos_list = [f"{con_bandera(row['nombre'])} {row['nombre']}" for _, row in lobos.iterrows()]
                    st.write(f"🐺 **Apuestas de 'Lobo Solitario':** {', '.join(lobos_list[:5])} (Solo 1 persona los eligió)")
                else:
                    st.write("🐺 No hay apuestas de 'Lobo Solitario'")
            else:
                st.write("Esperando a que se introduzcan las selecciones de todos...")

# =============================================
# PESTAÑA 2: MI FICHA
# =============================================
with tab2:
    st.header(f"👤 Ficha de {nombre_usuario}")
    
    usuario_id = usuarios[usuarios['nombre'] == nombre_usuario]['id'].values[0]
    
    selecciones = datos['selecciones']
    mis_selecciones = selecciones[selecciones['usuario_id'] == usuario_id]
    
    if mis_selecciones.empty:
        st.info("No tienes equipos seleccionados")
    else:
        df_rank = datos['clasificacion']
        mis_puntos = df_rank[df_rank['nombre'] == nombre_usuario]['puntos'].values[0] if not df_rank.empty else 0
        
        st.metric("⭐ Tus Puntos", f"{mis_puntos} pts")
        
        st.write("---")
        st.subheader("📌 Tus Equipos")
        
        for grupo in ['G1', 'G2', 'G3', 'G4', 'GA']:
            equipos_grupo = mis_selecciones[mis_selecciones['grupo_seleccion'] == grupo]
            if not equipos_grupo.empty:
                with st.expander(f"📂 Grupo {grupo}"):
                    for _, row in equipos_grupo.iterrows():
                        equipo = row['equipos']
                        st.write(f"⚽ {equipo['nombre']} - {equipo['puntos']} pts")

# =============================================
# PESTAÑA 3: CALENDARIO
# =============================================
with tab3:
    st.header("📅 Calendario de Partidos")
    
    partidos = datos['partidos']
    
    if partidos.empty:
        st.info("No hay partidos cargados")
    else:
        fases = partidos['fase'].unique().tolist()
        fase_seleccionada = st.selectbox("Selecciona una fase:", ["Todas"] + fases)
        
        if fase_seleccionada != "Todas":
            partidos_filtrados = partidos[partidos['fase'] == fase_seleccionada]
        else:
            partidos_filtrados = partidos
        
        for _, partido in partidos_filtrados.iterrows():
            estado_icon = "✅" if partido['estado'] == 'Jugado' else "⏳"
            
            local = partido.get('equipo_local_nombre', '?')
            visitante = partido.get('equipo_visitante_nombre', '?')
            
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"{estado_icon} {local} vs {visitante}")
            with col2:
                if partido['estado'] == 'Jugado':
                    st.write(f"{partido['goles_local']} - {partido['goles_visitante']}")
                else:
                    st.write("⏳ Pendiente")

# =============================================
# PESTAÑA 4: ADMIN
# =============================================
with tab4:
    st.header("🔧 Panel de Administración")
    
    admin_list = ['luis', 'Luis', 'admin', 'Admin']
    if nombre_usuario not in admin_list:
        st.warning("⛔ Esta sección solo está disponible para administradores")
        st.stop()
    
    st.success(f"✅ Bienvenido, {nombre_usuario}")
    
    # BOTÓN PARA GUARDAR SNAPSHOT
    st.subheader("📸 Guardar Snapshot del día")
    
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("📸 Guardar Snapshot Ahora", type="primary"):
            with st.spinner("Guardando snapshot..."):
                if db.guardar_snapshot():
                    st.success("✅ Snapshot guardado correctamente")
                    st.balloons()
                    st.rerun()
                else:
                    st.error("❌ Error al guardar snapshot")
    
    with col_btn2:
        df_anterior = db.obtener_ultimo_snapshot()
        if not df_anterior.empty:
            st.info(f"📅 Último snapshot: {len(df_anterior)} posiciones guardadas")
        else:
            st.warning("⚠️ No hay snapshots guardados aún")
    
    st.write("---")
    
    # PARTIDOS PENDIENTES
    st.subheader("📝 Partidos Pendientes")
    
    partidos = datos['partidos']
    pendientes = partidos[partidos['estado'] == 'Pendiente']
    
    if pendientes.empty:
        st.info("✅ No hay partidos pendientes")
    else:
        for _, partido in pendientes.iterrows():
            local = partido.get('equipo_local_nombre', '?')
            visitante = partido.get('equipo_visitante_nombre', '?')
            
            with st.container(border=True):
                col1, col2, col3, col4 = st.columns([2, 0.8, 0.8, 1])
                
                with col1:
                    st.write(f"⚽ {local} vs {visitante}")
                
                with col2:
                    st.number_input(
                        f"Goles {local[:10]}",
                        min_value=0,
                        max_value=10,
                        key=f"gl_{partido['id']}",
                        value=0,
                        step=1,
                        label_visibility="collapsed"
                    )
                    st.caption(local[:10])
                
                with col3:
                    st.number_input(
                        f"Goles {visitante[:10]}",
                        min_value=0,
                        max_value=10,
                        key=f"gv_{partido['id']}",
                        value=0,
                        step=1,
                        label_visibility="collapsed"
                    )
                    st.caption(visitante[:10])
                
                with col4:
                    if st.button(f"✅ Guardar", key=f"btn_{partido['id']}", type="primary"):
                        with st.spinner("Guardando..."):
                            # Recoger los valores de los inputs
                            gl = st.session_state.get(f"gl_{partido['id']}", 0)
                            gv = st.session_state.get(f"gv_{partido['id']}", 0)
                            if db.guardar_resultado(partido['id'], gl, gv, nombre_usuario):
                                st.success(f"✅ {local} {gl} - {gv} {visitante}")
                                st.rerun()
                            else:
                                st.error("❌ Error al guardar")