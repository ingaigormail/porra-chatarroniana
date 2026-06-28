# src/ui/admin/extra.py
import streamlit as st
import pandas as pd
import time
from utils.partidos_orden import ordenar_partidos
from src.ui.admin._common import es_admin_luis, refrescar_datos, formatear_fecha


from src.ui.admin.progresion_panel import mostrar_progresion


def mostrar_extra(nombre_usuario, partidos, db):
    if not es_admin_luis(nombre_usuario):
        st.warning("Solo disponible para Luis.")
        return

    st.header("🎛️ Admin Extra — Apuestas y Puntos")
    partidos = ordenar_partidos(db.obtener_partidos())

    mostrar_progresion(db)

    st.write("---")

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
            fecha_fmt = formatear_fecha(fecha)
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
                        refrescar_datos()
                    else:
                        st.error(resultado['message'])
