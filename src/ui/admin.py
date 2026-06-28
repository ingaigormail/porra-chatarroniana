# src/ui/admin.py
import streamlit as st
import pandas as pd
import time
from utils.validators import validar_goles
from utils.partidos_orden import ordenar_partidos


def _selector_goles(etiqueta: str, clave: str, valor_inicial: int = 0) -> int:
    """Selector 0-10: evita StreamlitMixedNumericTypesError de number_input."""
    indice = max(0, min(10, int(valor_inicial or 0)))
    return st.selectbox(
        etiqueta,
        options=list(range(11)),
        index=indice,
        key=clave,
        label_visibility="collapsed",
    )


def _refrescar_datos():
    """Invalida caché de app.py y recarga la interfaz con datos frescos."""
    st.cache_data.clear()
    st.rerun()


def _formatear_fecha(fecha) -> str:
    """Convierte fecha ISO a DD/MM/YYYY para mostrar en Admin."""
    if fecha is None or (isinstance(fecha, float) and pd.isna(fecha)):
        return ''
    s = str(fecha).strip()
    if not s:
        return ''
    try:
        return pd.to_datetime(s).strftime('%d/%m/%Y')
    except (ValueError, TypeError):
        return s


def mostrar(nombre_usuario, partidos, db):
    st.header("🔧 Panel de Administración")

    admin_list = ['luis', 'Luis', 'admin', 'Admin']
    if nombre_usuario not in admin_list:
        st.warning("⛔ Esta sección solo está disponible para administradores")
        return

    partidos = ordenar_partidos(db.obtener_partidos())

    st.success(f"✅ Bienvenido, {nombre_usuario}")

    # ==========================================
    # SNAPSHOT
    # ==========================================
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
            st.info(
                f"📅 Último snapshot: {
                    len(df_anterior)} posiciones guardadas")
        else:
            st.warning("⚠️ No hay snapshots guardados aún")

    st.write("---")

    # ==========================================
    # GENERAR CRUCES
    # ==========================================
    st.subheader("🔄 Generar Cruces Automáticos")
    if st.button(
        "🔄 Calcular y Generar Cruces de Dieciseisavos",
            type="primary"):
        with st.spinner("Calculando clasificaciones y generando cruces..."):
            resultado = db.actualizar_cruces()
            if isinstance(resultado, dict) and resultado.get('success'):
                st.success(f"✅ {resultado['message']}")
                st.balloons()
                _refrescar_datos()
            elif isinstance(resultado, dict):
                st.error(f"❌ {resultado.get('message', 'Error al generar cruces')}")
            elif resultado:
                st.success("✅ Cruces generados correctamente")
                st.balloons()
                _refrescar_datos()
            else:
                st.error(
                    "❌ Error al generar cruces (puede que falten partidos o equipos)")

    st.write("---")

    # ==========================================
    # FECHAS ELIMINATORIA
    # ==========================================
    st.subheader("📅 Fechas de Eliminatoria")
    st.caption(
        "Asigna fechas por número de partido (M73–M104). "
        "Edita `config/fechas_eliminatoria.py` o pega líneas id,fecha abajo.")

    try:
        from config.fechas_eliminatoria import FECHAS as fechas_config
    except ImportError:
        fechas_config = {}

    col_f1, col_f2 = st.columns(2)
    with col_f1:
        if fechas_config:
            st.write(f"**Config:** {len(fechas_config)} fechas en archivo")
            if st.button("📅 Aplicar fechas del archivo config", type="primary"):
                n = db.actualizar_fechas_partidos(fechas_config)
                st.success(f"✅ {n} fechas actualizadas")
                _refrescar_datos()
        else:
            st.info(
                "Rellena `config/fechas_eliminatoria.py` con tus fechas "
                "(id: 'YYYY-MM-DD') y pulsa aplicar.")

    with col_f2:
        texto_fechas = st.text_area(
            "Pegar CSV (id,fecha)",
            placeholder="73,2026-06-28\n74,2026-06-28\n89,2026-07-04",
            height=120,
            key="fechas_csv_paste",
        )
        if st.button("📅 Aplicar fechas pegadas"):
            fechas_parsed = {}
            for linea in texto_fechas.strip().splitlines():
                partes = [p.strip() for p in linea.replace(';', ',').split(',')]
                if len(partes) >= 2 and partes[0].isdigit():
                    fechas_parsed[int(partes[0])] = partes[1]
            if fechas_parsed:
                n = db.actualizar_fechas_partidos(fechas_parsed)
                st.success(f"✅ {n} fechas actualizadas")
                _refrescar_datos()
            else:
                st.warning("No se encontraron líneas válidas (formato: id,fecha)")

    st.write("---")

    # ==========================================
    # RECALCULAR PUNTOS DE EQUIPOS
    # ==========================================
    st.subheader("🔄 Recalcular Puntos de Equipos")
    st.caption(
        "Recalcula todos los puntos reales de los equipos basándose en los partidos jugados.")
    col_rec1, col_rec2 = st.columns(2)
    with col_rec1:
        if st.button("🔄 Recalcular Ahora", type="primary"):
            with st.spinner("Recalculando puntos de todos los equipos..."):
                partidos_df = db.obtener_partidos()
                from src.services.equipos import EquiposService
                equipos_service = EquiposService(db.client)
                equipos_service._recalcular_puntos_equipos(partidos_df)
                st.success("✅ Puntos de equipos recalculados correctamente")
                st.rerun()
    with col_rec2:
        st.info("⚠️ Esto sobreescribirá los puntos actuales de los equipos con el cálculo basado en los partidos jugados.")

    st.write("---")

    # ==========================================
    # RECALCULAR CLASIFICACIÓN GENERAL
    # ==========================================
    st.subheader("📊 Recalcular Clasificación General")
    st.caption(
        "Fuerza el recálculo de la clasificación de usuarios (útil si los puntos no se actualizan).")
    if st.button("🔄 Recalcular Clasificación", type="primary"):
        with st.spinner("Recalculando clasificación..."):
            df_rank = db.obtener_clasificacion()
            st.success(f"✅ Clasificación recalculada: {len(df_rank)} usuarios")
            st.rerun()

    st.write("---")

    # ==========================================
    # FORZAR SNAPSHOT
    # ==========================================
    st.subheader("📸 Forzar Snapshot (Movimientos)")
    st.caption(
        "Guarda un snapshot manual para que los movimientos (subidas/bajadas) se actualicen.")
    if st.button("📸 Forzar Snapshot", type="primary"):
        with st.spinner("Guardando snapshot..."):
            if db.guardar_snapshot():
                st.success("✅ Snapshot forzado correctamente")
                st.rerun()
            else:
                st.error("❌ Error al guardar snapshot")

    st.write("---")

    # ==========================================
    # PROGRESIÓN DE EQUIPOS (BONUS POR FASE)
    # ==========================================
    st.subheader("📈 Progresión de Equipos (Bonus por Fase)")
    st.caption(
        "Bonus manual por avance de fase. Octavos (+10), Cuartos (+15), "
        "Semifinal (+20), Final (+30). Dieciseisavos: tú eliges los puntos.")

    equipos_df = db.obtener_equipos()
    if equipos_df.empty:
        st.warning("⚠️ No hay equipos disponibles")
    else:
        equipos_ordenados = sorted(equipos_df['nombre'].tolist())

        puntos_sugeridos = {
            'Dieciseisavos': 5,
            'Octavos': 10,
            'Cuartos': 15,
            'Semifinal': 20,
            'Final': 30,
        }

        col_eq, col_fase, col_pts = st.columns([2, 2, 1])

        with col_eq:
            equipo_seleccionado = st.selectbox(
                "Selecciona un equipo:",
                options=equipos_ordenados,
                key="progresion_equipo"
            )

        with col_fase:
            fase_seleccionada = st.selectbox(
                "Selecciona la fase:",
                options=['Dieciseisavos', 'Octavos', 'Cuartos', 'Semifinal', 'Final'],
                key="progresion_fase"
            )

        with col_pts:
            puntos_a_sumar = st.number_input(
                "Puntos (+)",
                min_value=1,
                max_value=100,
                value=puntos_sugeridos[fase_seleccionada],
                step=1,
                key=f"progresion_puntos_{fase_seleccionada}",
                help="Editable: cambia el valor antes de aplicar",
            )

        equipo_id = int(
            equipos_df[equipos_df['nombre'] == equipo_seleccionado]['id'].values[0])

        usuarios_con_equipo = db.progresion.obtener_usuarios_con_equipo(
            equipo_id)

        st.info(
            f"💡 Se otorgarán **+{int(puntos_a_sumar)} pts** ({fase_seleccionada}) "
            f"a todos los usuarios con **{equipo_seleccionado}**")

        if usuarios_con_equipo.empty:
            st.warning(f"⚠️ No hay usuarios con **{equipo_seleccionado}**")
        else:
            # Obtener clasificación actual para mostrar puntos
            df_clasificacion = db.obtener_clasificacion()

            # Mostrar tabla de usuarios que recibirán el bonus
            st.write(f"**👥 Usuarios que recibirán el bonus:**")

            usuarios_tabla = []
            for _, usuario in usuarios_con_equipo.iterrows():
                nombre_usuario = usuario['usuario_nombre']
                pts_actuales = 0
                if not df_clasificacion.empty:
                    pts_row = df_clasificacion[df_clasificacion['nombre']
                                               == nombre_usuario]
                    if not pts_row.empty:
                        pts_actuales = int(pts_row.iloc[0]['puntos'])

                usuarios_tabla.append({
                    'Usuario': nombre_usuario,
                    'Puntos Actuales': pts_actuales,
                    'Bonus': f"+{int(puntos_a_sumar)}"
                })

            df_usuarios_tabla = pd.DataFrame(usuarios_tabla)
            st.dataframe(
                df_usuarios_tabla, hide_index=True, use_container_width=True, column_config={
                    'Usuario': st.column_config.TextColumn(
                        'Usuario', width='medium'), 'Puntos Actuales': st.column_config.NumberColumn(
                        'Puntos Actuales', width='small'), 'Bonus': st.column_config.TextColumn(
                        'Bonus a Recibir', width='small')})

            if st.button(
                "✅ Aplicar Bonus a Usuarios",
                type="primary",
                    use_container_width=True):
                try:
                    with st.spinner("Aplicando bonus de progresión..."):
                        # Llamar al servicio con equipo_id convertido a int
                        resultado = db.calcular_progresion(
                            equipo_id, fase_seleccionada, int(puntos_a_sumar))

                        if resultado['success']:
                            if resultado['usuarios_afectados'] > 0:
                                st.success(f"✅ {resultado['message']}")
                                st.balloons()
                                # Limpiar caché para forzar recálculo de
                                # clasificación
                                st.cache_data.clear()
                                st.rerun()
                            else:
                                st.warning(resultado['message'])
                        else:
                            st.error(f"❌ {resultado['message']}")
                except Exception as e:
                    st.error(f"❌ Error inesperado: {str(e)}")
                    import traceback
                    st.error(traceback.format_exc())

    st.write("---")

    # ==========================================
    # GESTIÓN DE APUESTAS
    # ==========================================
    st.subheader("🎯 Gestión de Apuestas (Quiniela/Porra)")
    st.caption(
        "Activa los partidos de eliminatoria en los que los usuarios podrán apostar")
    partidos_elim = ordenar_partidos(
        partidos[partidos['fase'] != 'Grupos'].copy()
    ).reset_index(drop=True)
    if partidos_elim.empty:
        st.info("No hay partidos de eliminatoria disponibles aún")
    else:
        col1, col2, col3, col4, col5, col6 = st.columns(
            [0.8, 1.2, 2.5, 1.5, 1, 1.2])
        with col1:
            st.caption("🆔 **Nº**")
        with col2:
            st.caption("📅 **Fecha**")
        with col3:
            st.caption("🏟️ **Partido**")
        with col4:
            st.caption("🎯 **Tipo**")
        with col5:
            st.caption("🔓 **Abierto**")
        with col6:
            st.caption("💾 **Acción**")
        st.divider()
        fase_prev = None
        fecha_prev = None
        for orden, (_, partido) in enumerate(partidos_elim.iterrows()):
            fase_row = partido.get('fase', '')
            if fase_row != fase_prev:
                st.markdown(f"**🏟️ {fase_row}**")
                fase_prev = fase_row
                fecha_prev = None

            fecha = partido.get('fecha', '')
            fecha_fmt = _formatear_fecha(fecha)
            if fecha_fmt and fecha_fmt != fecha_prev:
                st.caption(f"📅 {fecha_fmt}")
                fecha_prev = fecha_fmt

            partido_id = partido['id']
            local = partido.get('equipo_local_nombre', '?')
            visitante = partido.get('equipo_visitante_nombre', '?')
            fase = partido.get('fase', '')
            tipo_actual = partido.get('tipo_apuesta', 'ninguno')
            abierto_actual = partido.get('apuestas_abiertas', False)
            with st.container(border=True):
                col1, col2, col3, col4, col5, col6 = st.columns(
                    [0.8, 1.2, 2.5, 1.5, 1, 1.2])
                with col1:
                    st.write(f"#{partido_id}")
                with col2:
                    st.write(f"📅 {fecha_fmt or '—'}")
                with col3:
                    st.write(f"🏟️ **{fase}** - {local} vs {visitante}")
                with col4:
                    tipo_seleccionado = st.selectbox(
                        "Tipo",
                        options=[
                            'ninguno',
                            'quiniela',
                            'porra'],
                        index=[
                            'ninguno',
                            'quiniela',
                            'porra'].index(tipo_actual),
                        key=f"tipo_apuesta_{orden:04d}",
                        label_visibility="collapsed")
                with col5:
                    abierto = st.checkbox(
                        "Abierto",
                        value=abierto_actual,
                        key=f"abierto_apuesta_{orden:04d}"
                    )
                with col6:
                    if st.button("💾 Guardar",
                                 key=f"btn_apuesta_gestion_{orden:04d}"):
                        resultado = db.actualizar_estado_apuesta(
                            partido_id, tipo_seleccionado, abierto)
                        if resultado['success']:
                            st.success("✅ Guardado")
                            st.rerun()
                        else:
                            st.error(f"❌ {resultado['message']}")

    st.write("---")

    # ==========================================
    # GESTIÓN DE FINALISTAS
    # ==========================================
    st.subheader("🏆 Gestión de Apuesta de Finalistas")
    st.caption(
        "Activa o desactiva la posibilidad de que los usuarios apuesten los finalistas")
    estado_actual = db.obtener_configuracion('finalistas_activo')
    estado_bool = estado_actual == 'true'
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        nuevo_estado = st.checkbox(
            "Activar apuesta de finalistas",
            value=estado_bool)
    with col_f2:
        if nuevo_estado != estado_bool:
            if st.button("Guardar estado finalistas", type="primary"):
                db.actualizar_configuracion(
                    'finalistas_activo', str(nuevo_estado).lower())
                st.success("✅ Estado actualizado")
                st.rerun()

    st.write("---")

    # ==========================================
    # CALCULAR FINALISTAS
    # ==========================================
    st.subheader("🏆 Calcular Finalistas")
    st.caption(
        "Define los 2 equipos finalistas reales y calcula los puntos para los usuarios que apostaron")

    # Obtener todos los usuarios para saber quién apostó y quién no
    todos_usuarios = db.obtener_usuarios()

    equipos_df = db.obtener_equipos()
    if equipos_df.empty:
        st.warning("⚠️ No hay equipos disponibles")
    else:
        equipos_ordenados = sorted(equipos_df['nombre'].tolist())

        col_f1, col_f2 = st.columns(2)
        with col_f1:
            # Usar session_state para evitar conflictos de claves
            if 'admin_finalista_1' not in st.session_state:
                st.session_state.admin_finalista_1 = equipos_ordenados[0] if equipos_ordenados else ""
            finalista_1_nombre = st.selectbox(
                "Selecciona Finalista 1:",
                options=equipos_ordenados,
                index=equipos_ordenados.index(
                    st.session_state.admin_finalista_1) if st.session_state.admin_finalista_1 in equipos_ordenados else 0,
                key=f"admin_finalista_1_{
                    int(
                        time.time() *
                        1000)}")
            st.session_state.admin_finalista_1 = finalista_1_nombre

        with col_f2:
            # Usar session_state para evitar conflictos de claves
            if 'admin_finalista_2' not in st.session_state:
                st.session_state.admin_finalista_2 = equipos_ordenados[1] if len(
                    equipos_ordenados) > 1 else (equipos_ordenados[0] if equipos_ordenados else "")
            finalista_2_nombre = st.selectbox(
                "Selecciona Finalista 2:",
                options=equipos_ordenados,
                index=equipos_ordenados.index(
                    st.session_state.admin_finalista_2) if st.session_state.admin_finalista_2 in equipos_ordenados else 0,
                key=f"admin_finalista_2_{
                    int(
                        time.time() *
                        1000)}")
            st.session_state.admin_finalista_2 = finalista_2_nombre

        if finalista_1_nombre == finalista_2_nombre:
            st.error("❌ Los dos finalistas deben ser equipos diferentes")
        else:
            # Obtener IDs de los equipos
            finalista_1_id = int(
                equipos_df[equipos_df['nombre'] == finalista_1_nombre]['id'].values[0])
            finalista_2_id = int(
                equipos_df[equipos_df['nombre'] == finalista_2_nombre]['id'].values[0])

            st.info(
                f"🏆 Finalistas Reales: **{finalista_1_nombre}** vs **{finalista_2_nombre}**")

            # Obtener todas las apuestas de finalistas
            try:
                apuestas_finalistas = db.client.table('finalistas_apostados')\
                    .select('*, usuarios(nombre)')\
                    .execute()

                # Obtener clasificación actual
                df_clasificacion = db.obtener_clasificacion()

                # Separar usuarios que apostaron vs no apostaron
                usuarios_apostaron = {}
                usuarios_no_apostaron = []

                if apuestas_finalistas.data:
                    for apuesta in apuestas_finalistas.data:
                        usuario_nombre = apuesta['usuarios']['nombre'] if apuesta['usuarios'] else 'Desconocido'

                        # Obtener nombres de equipos apostados
                        eq1_apostado = equipos_df[equipos_df['id'] ==
                                                  apuesta['finalista_1_id']]['nombre'].values
                        eq2_apostado = equipos_df[equipos_df['id'] ==
                                                  apuesta['finalista_2_id']]['nombre'].values
                        eq1_apostado = eq1_apostado[0] if len(
                            eq1_apostado) > 0 else f"ID:{apuesta['finalista_1_id']}"
                        eq2_apostado = eq2_apostado[0] if len(
                            eq2_apostado) > 0 else f"ID:{apuesta['finalista_2_id']}"

                        pts_actuales = 0
                        if not df_clasificacion.empty:
                            pts_row = df_clasificacion[df_clasificacion['nombre']
                                                       == usuario_nombre]
                            if not pts_row.empty:
                                pts_actuales = int(pts_row.iloc[0]['puntos'])

                        # Calcular puntos estimados
                        puntos_estimados = 0
                        aciertos = 0
                        if apuesta['finalista_1_id'] in [
                                finalista_1_id, finalista_2_id]:
                            aciertos += 1
                        if apuesta['finalista_2_id'] in [
                                finalista_1_id, finalista_2_id]:
                            aciertos += 1

                        if aciertos == 2:
                            puntos_estimados = 10
                        elif aciertos == 1:
                            puntos_estimados = 4

                        puntos_finales = apuesta.get('puntos', 0)

                        usuarios_apostaron[usuario_nombre] = {
                            'Puntos Actuales': pts_actuales,
                            'Apuesta': f"{eq1_apostado} vs {eq2_apostado}",
                            'Puntos a Recibir': f"+{puntos_estimados}",
                            'Puntos Finales': puntos_finales
                        }

                # Encontrar usuarios que NO apostaron
                usuarios_apostaron_set = set(usuarios_apostaron.keys())
                for _, usuario_row in todos_usuarios.iterrows():
                    usuario_nombre = usuario_row.get('nombre')
                    if usuario_nombre not in usuarios_apostaron_set:
                        usuarios_no_apostaron.append(usuario_nombre)

                # Mostrar sección de usuarios que SÍ apostaron
                if usuarios_apostaron:
                    st.write("### ✅ Usuarios que YA apostaron:")
                    usuarios_tabla = []
                    for usuario_nombre, datos in usuarios_apostaron.items():
                        usuarios_tabla.append({
                            'Usuario': usuario_nombre,
                            'Apuesta': datos['Apuesta'],
                            'Puntos Actuales': datos['Puntos Actuales'],
                            'Puntos a Recibir': datos['Puntos a Recibir'],
                            'Puntos Finales': datos['Puntos Finales']
                        })

                    df_usuarios_tabla = pd.DataFrame(usuarios_tabla)
                    st.dataframe(
                        df_usuarios_tabla, hide_index=True, use_container_width=True, column_config={
                            'Usuario': st.column_config.TextColumn(
                                'Usuario', width='medium'), 'Apuesta': st.column_config.TextColumn(
                                'Su Apuesta', width='large'), 'Puntos Actuales': st.column_config.NumberColumn(
                                'Pts Actuales', width='small'), 'Puntos a Recibir': st.column_config.TextColumn(
                                'Pts Recibir', width='small'), 'Puntos Finales': st.column_config.NumberColumn(
                                'Pts Finales', width='small')})

                # Mostrar sección de usuarios que NO apostaron
                if usuarios_no_apostaron:
                    st.write("### ⚠️ Usuarios que AÚN NO han apostado:")
                    st.warning(
                        f"Los siguientes usuarios deben ser avisados para que apuesten los finalistas:")
                    for usuario in sorted(usuarios_no_apostaron):
                        st.caption(f"• {usuario}")
                else:
                    st.success("✅ Todos los usuarios han apostado finalistas")

                # Botón para calcular
                if usuarios_apostaron:
                    st.write("---")
                    if st.button(
                        "✅ Calcular y Aplicar Puntos de Finalistas",
                        type="primary",
                            use_container_width=True):
                        with st.spinner("Calculando puntos de finalistas..."):
                            resultado = db.calcular_puntos_finalistas(
                                finalista_1_id, finalista_2_id)

                            if resultado['success']:
                                st.success(f"✅ {resultado['message']}")
                                st.balloons()
                                # Limpiar caché para forzar recálculo
                                st.cache_data.clear()
                                st.rerun()
                            else:
                                st.error(f"❌ {resultado['message']}")
                else:
                    st.info("ℹ️ No hay usuarios que hayan apostado finalistas aún")

            except Exception as e:
                st.error(
                    f"❌ Error al obtener apuestas de finalistas: {
                        str(e)}")

    st.write("---")

    # ==========================================
    # PARTIDOS PENDIENTES (COMPACTO)
    # ==========================================
    st.subheader("📝 Partidos Pendientes")
    st.caption("Introduce resultados. Prórroga y guardar en cada fila.")
    pendientes = ordenar_partidos(
        partidos[partidos['estado'] == 'Pendiente'].copy()
    ).reset_index(drop=True)
    if pendientes.empty:
        st.info("✅ No hay partidos pendientes")
    else:
        col1, col2, col3, col4, col5, col6, col7 = st.columns(
            [0.6, 1, 2, 0.6, 0.6, 0.8, 0.8])
        with col1:
            st.caption("🆔 ID")
        with col2:
            st.caption("📅 Fecha")
        with col3:
            st.caption("🏟️ Partido")
        with col4:
            st.caption("⚽ Local")
        with col5:
            st.caption("⚽ Visit")
        with col6:
            st.caption("⚙️ Prórroga")
        with col7:
            st.caption("💾 Guardar")
        st.divider()

        fase_prev = None
        fecha_prev = None
        for orden, (_, partido) in enumerate(pendientes.iterrows()):
            fase_row = partido.get('fase', '')
            if fase_row != fase_prev:
                st.markdown(f"**🏟️ {fase_row}**")
                fase_prev = fase_row
                fecha_prev = None

            fecha = partido.get('fecha', '')
            fecha_fmt = _formatear_fecha(fecha)
            if fecha_fmt and fecha_fmt != fecha_prev:
                st.caption(f"📅 {fecha_fmt}")
                fecha_prev = fecha_fmt

            partido_id = int(partido['id'])
            local = partido.get('equipo_local_nombre', '?')
            visitante = partido.get('equipo_visitante_nombre', '?')
            fase = partido.get('fase', '')
            local_str = str(local) if local else '?'
            visitante_str = str(visitante) if visitante else '?'

            # Clave con índice de fila: Streamlit ordena widgets por key (100 < 89 alfabéticamente)
            with st.form(key=f"form_pend_{orden:04d}", border=False):
                col1, col2, col3, col4, col5, col6, col7 = st.columns(
                    [0.6, 1, 2, 0.6, 0.6, 0.8, 0.8])
                with col1:
                    st.write(f"#{partido_id}")
                with col2:
                    st.write(fecha_fmt or '—')
                with col3:
                    st.write(f"{fase} - {local_str} vs {visitante_str}")
                with col4:
                    goles_local = st.selectbox(
                        "GL",
                        options=list(range(11)),
                        index=0,
                        label_visibility="collapsed",
                    )
                with col5:
                    goles_visitante = st.selectbox(
                        "GV",
                        options=list(range(11)),
                        index=0,
                        label_visibility="collapsed",
                    )
                with col6:
                    prorroga_estado = st.selectbox(
                        "Prórroga", ["No", "Sí"], label_visibility="collapsed")
                with col7:
                    guardar = st.form_submit_button("💾 Guardar")

                if guardar:
                    gl = validar_goles(goles_local)
                    gv = validar_goles(goles_visitante)
                    hubo_prorroga = prorroga_estado == "Sí"
                    if db.guardar_resultado(
                            partido_id, gl, gv, nombre_usuario,
                            hubo_prorroga=hubo_prorroga):
                        st.success(f"✅ Resultado guardado: {gl}-{gv}")
                        _refrescar_datos()
                    else:
                        st.error("❌ Error al guardar resultado")

    st.write("---")

    # ==========================================
    # PARTIDOS JUGADOS - EDITAR RESULTADO
    # ==========================================
    st.subheader("📊 Partidos Jugados - Editar Resultado")
    st.caption("Modifica el resultado de partidos jugados y recalcula puntos automáticamente.")
    partidos_jugados_edit = ordenar_partidos(
        partidos[partidos['estado'] == 'Jugado'].copy()
    ).reset_index(drop=True)
    if partidos_jugados_edit.empty:
        st.info("✅ No hay partidos jugados")
    else:
        col1, col2, col3, col4, col5, col6, col7 = st.columns(
            [0.6, 1, 2, 0.6, 0.6, 0.6, 0.8])
        with col1:
            st.caption("🆔 ID")
        with col2:
            st.caption("📅 Fecha")
        with col3:
            st.caption("🏟️ Partido")
        with col4:
            st.caption("⚽ Local")
        with col5:
            st.caption("⚽ Visit")
        with col6:
            st.caption("🧮 Calcular")
        with col7:
            st.caption("💾 Guardar")
        st.divider()
        
        fase_prev = None
        fecha_prev = None
        for orden, (_, partido) in enumerate(partidos_jugados_edit.iterrows()):
            fase_row = partido.get('fase', '')
            if fase_row != fase_prev:
                st.markdown(f"**🏟️ {fase_row}**")
                fase_prev = fase_row
                fecha_prev = None

            fecha = partido.get('fecha', '')
            fecha_fmt = _formatear_fecha(fecha)
            if fecha_fmt and fecha_fmt != fecha_prev:
                st.caption(f"📅 {fecha_fmt}")
                fecha_prev = fecha_fmt

            partido_id = partido['id']
            local = partido.get('equipo_local_nombre', '?')
            visitante = partido.get('equipo_visitante_nombre', '?')
            fase = partido.get('fase', '')
            gl_actual = int(partido.get('goles_local', 0) or 0)
            gv_actual = int(partido.get('goles_visitante', 0) or 0)
            local_str = str(local) if local else '?'
            visitante_str = str(visitante) if visitante else '?'

            col1, col2, col3, col4, col5, col6, col7 = st.columns(
                [0.6, 1, 2, 0.6, 0.6, 0.6, 0.8])
            with col1:
                st.write(f"#{partido_id}")
            with col2:
                st.write(fecha_fmt or '—')
            with col3:
                st.write(f"{fase} - {local_str} vs {visitante_str}")
            with col4:
                goles_local_edit = _selector_goles(
                    "GL", f"gl_jugado_{orden:04d}", gl_actual)
            with col5:
                goles_visitante_edit = _selector_goles(
                    "GV", f"gv_jugado_{orden:04d}", gv_actual)
            with col6:
                if st.button("🧮", key=f"btn_calcular_{orden:04d}", help="Calcular puntos"):
                    with st.spinner("Calculando puntos..."):
                        resultado = db.quiniela.calcular_puntos_partido(partido_id)
                        if resultado['success']:
                            st.success(f"✅ {resultado['message']}")
                            _refrescar_datos()
                        else:
                            st.warning(f"⚠️ {resultado['message']}")
            with col7:
                if st.button("💾 Guardar", key=f"btn_guardar_jugado_{orden:04d}"):
                    if goles_local_edit != gl_actual or goles_visitante_edit != gv_actual:
                        if db.guardar_resultado(
                            partido_id, goles_local_edit, goles_visitante_edit,
                            nombre_usuario):
                            st.success(
                                f"✅ {goles_local_edit}-{goles_visitante_edit}")
                            _refrescar_datos()
                        else:
                            st.error("❌ Error al guardar resultado")
                    else:
                        st.info("ℹ️ Sin cambios")

    st.write("---")

    # ==========================================
    # REVISAR Y VALIDAR APUESTAS
    # ==========================================
    st.subheader("✅ Revisar y Validar Apuestas")
    st.caption(
        "Una vez calculados los puntos provisionales, revisa y aplica los puntos definitivos.")
    partidos_jugados = db.obtener_partidos()
    partidos_jugados = partidos_jugados[partidos_jugados['estado'] == 'Jugado']
    if partidos_jugados.empty:
        st.info("No hay partidos jugados con apuestas pendientes de validar.")
    else:
        opciones_partidos = {}
        for _, row in partidos_jugados.iterrows():
            local_nom = row.get('equipo_local_nombre', '?')
            visit_nom = row.get('equipo_visitante_nombre', '?')
            fase = row.get('fase', '')
            opciones_partidos[f"{row['id']} - {local_nom} vs {visit_nom} ({fase})"] = row['id']
        partido_seleccionado = st.selectbox(
            "Selecciona un partido jugado para revisar apuestas",
            options=[""] + list(opciones_partidos.keys()),
            key="admin_revisar"
        )
        if partido_seleccionado:
            partido_id = opciones_partidos[partido_seleccionado]
            apuestas_df = db.quiniela.obtener_apuestas_partido(partido_id)
            if apuestas_df.empty:
                st.info("No hay apuestas para este partido.")
            else:
                partido_info = partidos_jugados[partidos_jugados['id']
                                                == partido_id].iloc[0]
                st.write(
                    f"**Resultado real:** {
                        partido_info['equipo_local_nombre']} " f"{
                        partido_info['goles_local']} - {
                        partido_info['goles_visitante']} " f"{
                        partido_info['equipo_visitante_nombre']}")
                st.dataframe(
                    apuestas_df[['usuario_nombre', 'tipo', 'eleccion_quiniela', 'goles_local_apostados',
                                 'goles_visitante_apostados', 'puntos_provisionales']],
                    hide_index=True,
                    column_config={
                        'usuario_nombre': 'Usuario',
                        'tipo': 'Tipo',
                        'eleccion_quiniela': '1/X/2',
                        'goles_local_apostados': 'Goles Local',
                        'goles_visitante_apostados': 'Goles Visitante',
                        'puntos_provisionales': 'Pts. Prov.'
                    }
                )
                st.write("**Edición manual de puntos (opcional):**")
                puntos_editados = {}
                for _, row in apuestas_df.iterrows():
                    puntos_editados[row['id']] = st.selectbox(
                        f"Puntos para {row['usuario_nombre']}",
                        options=list(range(101)),
                        index=max(0, min(100, int(row['puntos_provisionales'] or 0))),
                        key=f"edit_{row['id']}",
                    )
                if st.button("✅ Validar y Aplicar Puntos", type="primary"):
                    resultado = db.quiniela.validar_apuestas(
                        partido_id, puntos_editados)
                    if resultado['success']:
                        st.success(resultado['message'])
                        df_rank = db.obtener_clasificacion()
                        for nombre in ['Luis', 'luis']:
                            if nombre in df_rank['nombre'].values:
                                puntos_luis = df_rank[df_rank['nombre']
                                                      == nombre]['puntos'].values[0]
                                st.info(
                                    f"📊 Puntos totales de {nombre}: **{puntos_luis} pts**")
                                break
                        _refrescar_datos()
                    else:
                        st.error(resultado['message'])
