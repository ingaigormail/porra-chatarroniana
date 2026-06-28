# src/ui/admin/operaciones.py
import streamlit as st
import pandas as pd
from utils.validators import validar_goles
from utils.partidos_orden import ordenar_partidos
from src.ui.admin._common import (
    es_admin_luis, selector_goles, refrescar_datos, formatear_fecha,
)


def mostrar_operaciones(nombre_usuario, partidos, db):
    if not es_admin_luis(nombre_usuario):
        st.warning("Solo disponible para Luis.")
        return

    st.header("🔧 Admin — Operación")
    partidos = ordenar_partidos(db.obtener_partidos())
    st.success(f"Bienvenido, {nombre_usuario}")


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
                refrescar_datos()
            elif isinstance(resultado, dict):
                st.error(f"❌ {resultado.get('message', 'Error al generar cruces')}")
            elif resultado:
                st.success("✅ Cruces generados correctamente")
                st.balloons()
                refrescar_datos()
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
                refrescar_datos()
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
                refrescar_datos()
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
            fecha_fmt = formatear_fecha(fecha)
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
                        refrescar_datos()
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
            fecha_fmt = formatear_fecha(fecha)
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
                goles_local_edit = selector_goles(
                    "GL", f"gl_jugado_{orden:04d}", gl_actual)
            with col5:
                goles_visitante_edit = selector_goles(
                    "GV", f"gv_jugado_{orden:04d}", gv_actual)
            with col6:
                if st.button("🧮", key=f"btn_calcular_{orden:04d}", help="Calcular puntos"):
                    with st.spinner("Calculando puntos..."):
                        resultado = db.quiniela.calcular_puntos_partido(partido_id)
                        if resultado['success']:
                            st.success(f"✅ {resultado['message']}")
                            refrescar_datos()
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
                            refrescar_datos()
                        else:
                            st.error("❌ Error al guardar resultado")
                    else:
                        st.info("ℹ️ Sin cambios")

    st.write("---")

    # ==========================================
