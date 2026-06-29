# src/ui/mi_ficha.py
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import time


def _selector_goles(etiqueta: str, clave: str, valor_inicial: int = 0) -> int:
    indice = max(0, min(10, int(valor_inicial or 0)))
    return st.selectbox(
        etiqueta,
        options=list(range(11)),
        index=indice,
        key=clave,
        label_visibility="collapsed",
    )


def mostrar(nombre_usuario, usuarios, df_rank, db):
    """Muestra la pestaña de Mi Ficha con quiniela, porra y finalistas."""

    st.header(f"👤 Ficha de {nombre_usuario}")

    # Obtener ID del usuario
    usuario_id = int(usuarios[usuarios['nombre'] ==
                     nombre_usuario]['id'].values[0])

    # ==========================================
    # PUNTOS TOTALES CON EVOLUCIÓN
    # ==========================================
    mis_puntos = df_rank[df_rank['nombre'] ==
                         nombre_usuario]['puntos'].values[0] if not df_rank.empty else 0

    # Obtener movimientos/evolución
    movimientos = db.obtener_movimientos()
    puntos_anterior = mis_puntos
    if not movimientos.empty:
        movimientos_usuario = movimientos[movimientos['nombre']
                                          == nombre_usuario]
        if not movimientos_usuario.empty:
            puntos_anterior = movimientos_usuario['puntos'].values[0]

    diferencia = mis_puntos - puntos_anterior

    col_pts1, col_pts2, col_pts3 = st.columns(3)
    with col_pts1:
        st.metric("⭐ Puntos Totales", f"{mis_puntos} pts")
    with col_pts2:
        if diferencia != 0:
            st.metric(
                "📊 Fase Anterior",
                f"{puntos_anterior} pts",
                delta=f"{
                    diferencia:+d} pts")
        else:
            st.metric("📊 Fase Anterior", f"{puntos_anterior} pts")
    with col_pts3:
        if not df_rank.empty:
            posicion = df_rank[df_rank['nombre'] ==
                               nombre_usuario]['posicion'].values[0]
            st.metric("🏅 Posición", f"#{posicion}")

    st.write("---")

    # ==========================================
    # TUS EQUIPOS SELECCIONADOS (CON EMOJIS - EN 3-4 COLUMNAS)
    # ==========================================
    st.subheader("📌 Tus Equipos")

    # Obtener selecciones
    selecciones_df = db.obtener_selecciones()
    mis_selecciones = selecciones_df[selecciones_df['usuario_id'].astype(
        int) == usuario_id]

    if mis_selecciones.empty:
        st.info("No tienes equipos seleccionados")
    else:
        # Mostrar equipos en 3-4 columnas
        equipos_lista = []
        for _, row in mis_selecciones.iterrows():
            nombre = row.get('equipo_nombre', 'Desconocido')
            puntos = row.get('equipo_puntos', 0)

            # Emoji según puntos
            if puntos >= 6:
                emoji = "🌟"
            elif puntos >= 3:
                emoji = "⚡"
            else:
                emoji = "⚽"

            equipos_lista.append({
                'nombre': nombre,
                'puntos': puntos,
                'emoji': emoji
            })

        # Mostrar en columnas (3-4 columnas según cantidad)
        num_equipos = len(equipos_lista)
        num_columnas = 4 if num_equipos >= 4 else 3 if num_equipos >= 3 else num_equipos

        cols = st.columns(num_columnas)
        for idx, equipo in enumerate(equipos_lista):
            with cols[idx % num_columnas]:
                st.info(
                    f"{equipo['emoji']} **{equipo['nombre']}**\n\n{equipo['puntos']} pts")

    st.write("---")

    # ==========================================
    # QUINIELA / PORRA - APOSTAR PARTIDOS
    # ==========================================
    st.subheader("🎯 Quiniela / Porra - Eliminatorias")
    st.caption(
        "Apuesta en los partidos de eliminación directa que el administrador haya habilitado.")

    # Obtener partidos abiertos y apuestas del usuario
    partidos_abiertos = db.obtener_partidos_abiertos_apuestas()
    apuestas_usuario = db.obtener_apuestas_usuario(usuario_id)

    if partidos_abiertos.empty:
        st.info("⏳ No hay partidos disponibles para apostar")
    else:
        for _, partido in partidos_abiertos.iterrows():
            partido_id = partido['id']
            local = partido.get('equipo_local_nombre', '?')
            visitante = partido.get('equipo_visitante_nombre', '?')
            fase = partido.get('fase', '')
            estado = partido.get('estado', 'Pendiente')
            fecha = partido.get('fecha', '')
            tipo_apuesta = partido.get('tipo_apuesta', 'ninguno')

            # Verificar si el usuario ya apostó en este partido
            ya_aposto = False
            apuesta = pd.DataFrame()
            if not apuestas_usuario.empty and 'partido_id' in apuestas_usuario.columns:
                apuesta = apuestas_usuario[apuestas_usuario['partido_id']
                                           == partido_id]
                ya_aposto = not apuesta.empty

            # Calcular si la apuesta está cerrada (1 hora antes del partido)
            apuesta_cerrada = False
            if fecha:
                try:
                    fecha_partido = datetime.strptime(str(fecha), '%Y-%m-%d')
                    ahora = datetime.now()
                    hora_partido = 15
                    if hora_partido >= 1 and hora_partido <= 8:
                        limite = fecha_partido - timedelta(days=1)
                        limite = limite.replace(hour=0, minute=0)
                    else:
                        limite = fecha_partido - timedelta(hours=1)
                    if ahora > limite:
                        apuesta_cerrada = True
                except BaseException:
                    apuesta_cerrada = False

            with st.container(border=True):
                col1, col2, col3 = st.columns([2, 2, 1])
                with col1:
                    st.write(f"🏟️ **{fase}** - {local} vs {visitante}")
                    if fecha:
                        st.caption(f"📅 {fecha}")
                    st.caption(f"🎯 Tipo: {tipo_apuesta.capitalize()}")

                with col2:
                    if estado == 'Jugado':
                        goles_local_real = partido.get('goles_local', 0)
                        goles_visitante_real = partido.get(
                            'goles_visitante', 0)
                        st.write(
                            f"✅ Resultado: **{goles_local_real} - {goles_visitante_real}**")
                        if ya_aposto:
                            puntos_finales = apuesta['puntos_finales'].values[0] if 'puntos_finales' in apuesta else 0
                            if puntos_finales > 0:
                                st.success(f"🏅 Puntos: {puntos_finales}")
                            else:
                                st.info("❌ No acertaste")
                    else:
                        if apuesta_cerrada:
                            st.warning("⏳ Apuestas cerradas para este partido")
                            if ya_aposto:
                                if tipo_apuesta == 'quiniela':
                                    elec = apuesta['eleccion_quiniela'].values[0] if 'eleccion_quiniela' in apuesta else '-'
                                    st.write(f"Tu elección: **{elec}**")
                                else:
                                    gl = apuesta['goles_local_apostados'].values[0] if 'goles_local_apostados' in apuesta else 0
                                    gv = apuesta['goles_visitante_apostados'].values[0] if 'goles_visitante_apostados' in apuesta else 0
                                    st.write(f"Tu apuesta: **{gl} - {gv}**")
                        else:
                            if ya_aposto:
                                if tipo_apuesta == 'quiniela':
                                    elec_actual = apuesta['eleccion_quiniela'].values[0] if 'eleccion_quiniela' in apuesta else '1'
                                    st.write(
                                        f"Tu elección actual: **{elec_actual}**")
                                else:
                                    gl_actual = apuesta['goles_local_apostados'].values[
                                        0] if 'goles_local_apostados' in apuesta else 0
                                    gv_actual = apuesta['goles_visitante_apostados'].values[
                                        0] if 'goles_visitante_apostados' in apuesta else 0
                                    st.write(
                                        f"Tu apuesta actual: **{gl_actual} - {gv_actual}**")

                            if tipo_apuesta == 'quiniela':
                                eleccion = st.radio(
                                    "Elige 1, X o 2",
                                    options=['1', 'X', '2'],
                                    key=f"quiniela_{partido_id}",
                                    horizontal=True,
                                    label_visibility="collapsed"
                                )
                                goles_local_apost = None
                                goles_visitante_apost = None
                            else:
                                col_a, col_b = st.columns(2)
                                with col_a:
                                    goles_local_apost = _selector_goles(
                                        f"Goles {local[:10]}",
                                        f"gl_porra_{partido_id}",
                                        0,
                                    )
                                with col_b:
                                    goles_visitante_apost = _selector_goles(
                                        f"Goles {visitante[:10]}",
                                        f"gv_porra_{partido_id}",
                                        0,
                                    )
                                eleccion = None

                            if st.button(
                                "📩 Guardar apuesta",
                                    key=f"btn_apuesta_{partido_id}"):
                                if tipo_apuesta == 'quiniela' and eleccion:
                                    resultado = db.apostar_partido(
                                        usuario_id, partido_id, tipo_apuesta, eleccion_quiniela=eleccion)
                                elif tipo_apuesta == 'porra' and goles_local_apost is not None and goles_visitante_apost is not None:
                                    resultado = db.apostar_partido(
                                        usuario_id,
                                        partido_id,
                                        tipo_apuesta,
                                        goles_local=goles_local_apost,
                                        goles_visitante=goles_visitante_apost)
                                else:
                                    resultado = {
                                        'success': False, 'message': 'Datos incompletos'}
                                if resultado['success']:
                                    st.success(f"✅ {resultado['message']}")
                                    st.rerun()
                                else:
                                    st.error(f"❌ {resultado['message']}")

                with col3:
                    if estado == 'Jugado':
                        st.caption("✅ Jugado")
                    elif apuesta_cerrada:
                        st.caption("🔒 Cerrado")
                    else:
                        st.caption("⏳ Abierto")

    st.write("---")

    # ==========================================
    # APOSTAR FINALISTAS (SOLO SI ADMIN ACTIVA)
    # ==========================================
    st.subheader("🏆 Apuesta de Finalistas")

    finalistas_activo = db.obtener_configuracion('finalistas_activo') == 'true'

    if not finalistas_activo:
        st.info(
            "🔒 Las apuestas de finalistas están cerradas. "
            "Ya no puedes cambiar tu elección.")
    else:
        st.caption("Elige los 2 equipos que crees que llegarán a la Final")

        equipos = db.obtener_equipos()
        equipos_vivos = equipos[equipos['puntos'] > 0]

        if equipos_vivos.empty:
            st.info("⏳ Aún no hay equipos disponibles para apostar finalistas")
        else:
            finalistas_response = db.client.table('finalistas_apostados')\
                .select('*')\
                .eq('usuario_id', usuario_id)\
                .execute()

            finalista_1_actual = None
            finalista_2_actual = None
            if finalistas_response.data:
                finalista_1_actual = finalistas_response.data[0]['finalista_1_id']
                finalista_2_actual = finalistas_response.data[0]['finalista_2_id']

            equipos_list = equipos_vivos['nombre'].tolist()
            equipos_ids = equipos_vivos['id'].tolist()
            equipos_dict = dict(zip(equipos_ids, equipos_list))

            # Inicializar session_state con apuestas previas si no existen
            if 'finalista_1_temp' not in st.session_state:
                if finalista_1_actual is not None and equipos_dict.get(finalista_1_actual, "") in equipos_list:
                    st.session_state.finalista_1_temp = equipos_dict.get(finalista_1_actual, "")
                else:
                    st.session_state.finalista_1_temp = ""
            
            if 'finalista_2_temp' not in st.session_state:
                if finalista_2_actual is not None and equipos_dict.get(finalista_2_actual, "") in equipos_list:
                    st.session_state.finalista_2_temp = equipos_dict.get(finalista_2_actual, "")
                else:
                    st.session_state.finalista_2_temp = ""
            
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                finalista_1 = st.selectbox(
                    "🏆 Finalista 1",
                    options=[""] + equipos_list,
                    key=f"selectbox_finalista_1",
                    index=0 if st.session_state.finalista_1_temp == "" else ([""] + equipos_list).index(st.session_state.finalista_1_temp) if st.session_state.finalista_1_temp in ([""] + equipos_list) else 0
                )
                st.session_state.finalista_1_temp = finalista_1
            with col_f2:
                finalista_2 = st.selectbox(
                    "🏆 Finalista 2",
                    options=[""] + equipos_list,
                    key=f"selectbox_finalista_2",
                    index=0 if st.session_state.finalista_2_temp == "" else ([""] + equipos_list).index(st.session_state.finalista_2_temp) if st.session_state.finalista_2_temp in ([""] + equipos_list) else 0
                )
                st.session_state.finalista_2_temp = finalista_2

            # Mostrar mensaje de confirmación si ambos están seleccionados
            if finalista_1 and finalista_2:
                st.success(f"✅ Has seleccionado: **{finalista_1}** vs **{finalista_2}**")
            elif finalista_1 or finalista_2:
                st.info("⏳ Selecciona ambos equipos para completar tu apuesta")

            if st.button("📩 Guardar Finalistas", type="primary"):
                if finalista_1 and finalista_2:
                    if finalista_1 == finalista_2:
                        st.error(
                            "❌ Los dos finalistas deben ser equipos diferentes")
                    else:
                        f1_id = equipos_vivos[equipos_vivos['nombre']
                                              == finalista_1]['id'].values[0]
                        f2_id = equipos_vivos[equipos_vivos['nombre']
                                              == finalista_2]['id'].values[0]

                        resultado = db.apostar_finalistas(
                            usuario_id, f1_id, f2_id)
                        if resultado['success']:
                            st.success(f"✅ {resultado['message']}")
                            st.rerun()
                        else:
                            st.error(f"❌ {resultado['message']}")
                else:
                    st.warning("⚠️ Selecciona ambos finalistas")

    st.write("---")

    # ==========================================
    # HISTÓRICO DE APUESTAS
    # ==========================================
    st.subheader("📜 Histórico de tus apuestas")

    apuestas = db.obtener_apuestas_usuario(usuario_id)
    apuestas_finalistas = db.quiniela.obtener_apuestas_usuario_finalistas(usuario_id)

    if apuestas.empty and apuestas_finalistas.empty:
        st.info("No has realizado ninguna apuesta aún")
    else:
        # Mostrar apuestas de quiniela/porra
        if not apuestas.empty:
            st.subheader("🎯 Quiniela y Porra")
        for _, apuesta in apuestas.iterrows():
            partido_id_apuesta = apuesta.get('partido_id')
            if partido_id_apuesta:
                partido_data = partidos_abiertos[partidos_abiertos['id'] ==
                                                 partido_id_apuesta] if not partidos_abiertos.empty else pd.DataFrame()
                if partido_data.empty:
                    partidos_all = db.obtener_partidos()
                    partido_data = partidos_all[partidos_all['id']
                                                == partido_id_apuesta]

                if not partido_data.empty:
                    partido = partido_data.iloc[0]
                    local = partido.get('equipo_local_nombre', '?')
                    visitante = partido.get('equipo_visitante_nombre', '?')
                    fase = partido.get('fase', '')
                    estado = partido.get('estado', 'Pendiente')

                    gl_apost = apuesta.get('goles_local_apostados', 0)
                    gv_apost = apuesta.get('goles_visitante_apostados', 0)
                    puntos_finales = apuesta.get('puntos_finales', 0)
                    eleccion = apuesta.get('eleccion_quiniela', '-')
                    tipo = apuesta.get('tipo', '')

                    with st.container(border=True):
                        col_a, col_b = st.columns([2, 1])
                        with col_a:
                            st.write(f"🏟️ **{fase}** - {local} vs {visitante}")
                            if tipo == 'quiniela':
                                st.write(f"Tu elección: **{eleccion}**")
                            else:
                                st.write(
                                    f"Tu apuesta: **{gl_apost} - {gv_apost}**")
                        with col_b:
                            if estado == 'Jugado':
                                st.write(f"🏅 **{puntos_finales} pts**")
                            else:
                                st.write("⏳ Pendiente")
        
        # Mostrar apuestas de finalistas
        if not apuestas_finalistas.empty:
            st.subheader("🏆 Tus Apuestas de Finalistas")
            for _, apuesta_fin in apuestas_finalistas.iterrows():
                finalista_1 = apuesta_fin.get('finalista_1_nombre', '?')
                finalista_2 = apuesta_fin.get('finalista_2_nombre', '?')
                puntos_fin = apuesta_fin.get('puntos', 0)
                
                # Determinar estado basado en puntos
                if puntos_fin == 0 and apuesta_fin.get('id'):
                    estado_fin = "❌ No acertó"
                elif puntos_fin == 4:
                    estado_fin = "🥈 Acertó 1"
                elif puntos_fin == 10:
                    estado_fin = "🥇 Acertó ambos"
                else:
                    estado_fin = "⏳ Pendiente"
                
                with st.container(border=True):
                    col_a, col_b = st.columns([2, 1])
                    with col_a:
                        st.write(f"🏆 **{finalista_1}** vs **{finalista_2}**")
                        st.caption("Tu apuesta de finalistas")
                    with col_b:
                        st.write(estado_fin)
                        if puntos_fin > 0:
                            st.write(f"🏅 **{puntos_fin} pts**")
