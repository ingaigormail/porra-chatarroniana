# src/ui/admin/operaciones.py
import streamlit as st
import pandas as pd
from utils.validators import validar_goles
from utils.partidos_orden import ordenar_partidos
from src.ui.admin._common import (
    es_admin_luis, selector_goles, refrescar_datos, formatear_fecha,
)


def _es_eliminatoria(fase):
    return fase and str(fase) != 'Grupos'


def _opciones_ganador_empate(local, visitante, actual=None):
    opciones = ['—', str(local), str(visitante)]
    idx = 0
    if actual == 'local':
        idx = 1
    elif actual == 'visitante':
        idx = 2
    return opciones, idx


def _ganador_prorroga_desde_ui(fase, gl, gv, prorroga_si, ganador_elegido, local, visitante):
    """En eliminatoria con empate, indica quién pasa (prórroga/penaltis)."""
    if not _es_eliminatoria(fase):
        return False, None
    hubo_prorroga = prorroga_si == 'Sí'
    if gl != gv:
        return hubo_prorroga, None
    if ganador_elegido == str(local):
        return True, 'local'
    if ganador_elegido == str(visitante):
        return True, 'visitante'
    return hubo_prorroga, None


def _validar_ganador_eliminatoria(fase, gl, gv, ganador_prorroga):
    if _es_eliminatoria(fase) and gl == gv and not ganador_prorroga:
        return (
            'Empate en eliminatoria: indica quién pasó de ronda '
            '(ganador en prórroga o penaltis).'
        )
    return None


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
    st.caption(
        "Introduce el marcador final. En eliminatoria con empate, marca "
        "**Prórroga = Sí** y elige **quién pasó** (penaltis).")
    pendientes = ordenar_partidos(
        partidos[partidos['estado'] == 'Pendiente'].copy()
    ).reset_index(drop=True)
    if pendientes.empty:
        st.info("✅ No hay partidos pendientes")
    else:
        col1, col2, col3, col4, col5, col6, col7, col8 = st.columns(
            [0.6, 1, 2, 0.6, 0.6, 0.7, 1.1, 0.8])
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
            st.caption("🏆 Si empate")
        with col8:
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
                col1, col2, col3, col4, col5, col6, col7, col8 = st.columns(
                    [0.6, 1, 2, 0.6, 0.6, 0.7, 1.1, 0.8])
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
                    if _es_eliminatoria(fase):
                        ganador_empate = st.selectbox(
                            "Ganador",
                            options=['—', local_str, visitante_str],
                            label_visibility="collapsed",
                        )
                    else:
                        ganador_empate = '—'
                        st.write("—")
                with col8:
                    guardar = st.form_submit_button("💾 Guardar")

                if guardar:
                    gl = validar_goles(goles_local)
                    gv = validar_goles(goles_visitante)
                    hubo_prorroga, ganador_prorroga = _ganador_prorroga_desde_ui(
                        fase, gl, gv, prorroga_estado, ganador_empate,
                        local_str, visitante_str)
                    err = _validar_ganador_eliminatoria(
                        fase, gl, gv, ganador_prorroga)
                    if err:
                        st.error(f"❌ {err}")
                    elif db.guardar_resultado(
                            partido_id, gl, gv, nombre_usuario,
                            hubo_prorroga=hubo_prorroga,
                            ganador_prorroga=ganador_prorroga):
                        extra = ''
                        if ganador_prorroga == 'local':
                            extra = f' — pasa {local_str}'
                        elif ganador_prorroga == 'visitante':
                            extra = f' — pasa {visitante_str}'
                        st.success(f"✅ Resultado guardado: {gl}-{gv}{extra}")
                        refrescar_datos()
                    else:
                        st.error("❌ Error al guardar resultado")

    st.write("---")

    # ==========================================
    # PARTIDOS JUGADOS - EDITAR RESULTADO
    # ==========================================
    st.subheader("📊 Partidos Jugados - Editar Resultado")
    st.caption(
        "Modifica marcador, prórroga y ganador si hubo empate en eliminatoria. "
        "Al guardar se recalculan puntos y el cuadro de cruces.")
    partidos_jugados_edit = ordenar_partidos(
        partidos[partidos['estado'] == 'Jugado'].copy()
    ).reset_index(drop=True)
    if partidos_jugados_edit.empty:
        st.info("✅ No hay partidos jugados")
    else:
        col1, col2, col3, col4, col5, col6, col7, col8, col9, col10 = st.columns(
            [0.6, 1, 2, 0.5, 0.5, 0.6, 1.0, 0.5, 0.5, 0.5])
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
            st.caption("⚙️ Prór.")
        with col7:
            st.caption("🏆 Si empate")
        with col8:
            st.caption("🧮")
        with col9:
            st.caption("💾")
        with col10:
            st.caption("↩️")
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
            hubo_prorroga_actual = bool(partido.get('hubo_prorroga', False))
            ganador_actual = partido.get('ganador_prorroga')
            local_str = str(local) if local else '?'
            visitante_str = str(visitante) if visitante else '?'
            opciones_gan, idx_gan = _opciones_ganador_empate(
                local_str, visitante_str, ganador_actual)

            col1, col2, col3, col4, col5, col6, col7, col8, col9, col10 = st.columns(
                [0.6, 1, 2, 0.5, 0.5, 0.6, 1.0, 0.5, 0.5, 0.5])
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
                if _es_eliminatoria(fase):
                    prorroga_edit = st.selectbox(
                        "Prórroga",
                        ["No", "Sí"],
                        index=1 if hubo_prorroga_actual else 0,
                        key=f"prorroga_jugado_{orden:04d}",
                        label_visibility="collapsed",
                    )
                else:
                    prorroga_edit = "No"
                    st.write("—")
            with col7:
                if _es_eliminatoria(fase):
                    ganador_edit = st.selectbox(
                        "Ganador",
                        options=opciones_gan,
                        index=idx_gan,
                        key=f"ganador_jugado_{orden:04d}",
                        label_visibility="collapsed",
                    )
                else:
                    ganador_edit = '—'
                    st.write("—")
            with col8:
                if st.button("🧮", key=f"btn_calcular_{orden:04d}", help="Calcular puntos"):
                    with st.spinner("Calculando puntos..."):
                        resultado = db.quiniela.calcular_puntos_partido(partido_id)
                        if resultado['success']:
                            st.success(f"✅ {resultado['message']}")
                            refrescar_datos()
                        else:
                            st.warning(f"⚠️ {resultado['message']}")
            with col9:
                if st.button("💾", key=f"btn_guardar_jugado_{orden:04d}", help="Guardar"):
                    gl = validar_goles(goles_local_edit)
                    gv = validar_goles(goles_visitante_edit)
                    hubo_prorroga, ganador_prorroga = _ganador_prorroga_desde_ui(
                        fase, gl, gv, prorroga_edit, ganador_edit,
                        local_str, visitante_str)
                    err = _validar_ganador_eliminatoria(
                        fase, gl, gv, ganador_prorroga)
                    if err:
                        st.error(f"❌ {err}")
                    elif db.guardar_resultado(
                            partido_id, gl, gv, nombre_usuario,
                            hubo_prorroga=hubo_prorroga,
                            ganador_prorroga=ganador_prorroga):
                        st.success(f"✅ {gl}-{gv} guardado")
                        refrescar_datos()
                    else:
                        st.error("❌ Error al guardar resultado")
            with col10:
                if st.button(
                        "↩️",
                        key=f"btn_revertir_{orden:04d}",
                        help="Revertir: vuelve a Pendiente y deshace cuadro/apuestas"):
                    r = db.revertir_resultado(partido_id, nombre_usuario)
                    if r.get('success'):
                        st.success(r['message'])
                        refrescar_datos()
                        st.rerun()
                    else:
                        st.error(r.get('message', 'Error al revertir'))

    st.write("---")

    # ==========================================
