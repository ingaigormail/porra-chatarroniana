# src/ui/calendario.py
import streamlit as st
import pandas as pd
from datetime import datetime
from utils.partidos_orden import ordenar_partidos


def mostrar(partidos):
    """Muestra la pestaña de Calendario"""

    st.header("📅 Calendario de Partidos")

    if partidos.empty:
        st.info("No hay partidos cargados")
        return

    # Mostrar contadores
    total = len(partidos)
    jugados = len(partidos[partidos['estado'] == 'Jugado'])
    pendientes = len(partidos[partidos['estado'] == 'Pendiente'])

    col1, col2, col3 = st.columns(3)
    col1.metric("Total", total)
    col2.metric("Jugados ⚽", jugados)
    col3.metric("Pendientes ⏳", pendientes)

    st.write("---")

    # ==========================================
    # PARTIDOS JUGADOS (ordenados por fecha)
    # ==========================================
    st.subheader("✅ Partidos Jugados")

    df_jugados = partidos[partidos['estado'] == 'Jugado'].copy()

    if not df_jugados.empty:
        df_jugados = ordenar_partidos(df_jugados)

        for _, partido in df_jugados.iterrows():
            local = partido.get('equipo_local_nombre', '?')
            visitante = partido.get('equipo_visitante_nombre', '?')
            goles_local = partido.get('goles_local', 0)
            goles_visitante = partido.get('goles_visitante', 0)
            fase = partido.get('fase', '')

            # Formatear fecha
            fecha = partido.get('fecha', '')
            fecha_str = ""
            if fecha and fecha != '':
                try:
                    fecha_obj = datetime.strptime(str(fecha), '%Y-%m-%d')
                    fecha_str = fecha_obj.strftime('%d/%m/%Y')
                except BaseException:
                    fecha_str = str(fecha)

            with st.container(border=True):
                col_a, col_b, col_c, col_d = st.columns([1.2, 2.5, 1.5, 1.5])
                with col_a:
                    st.write(f"📅 **{fecha_str}**")
                with col_b:
                    st.write(f"⚽ {local} vs {visitante}")
                with col_c:
                    st.write(f"**{goles_local} - {goles_visitante}**")
                with col_d:
                    st.write(f"🏟️ {fase}")
    else:
        st.info("No hay partidos jugados")

    st.write("---")

    # ==========================================
    # PARTIDOS PENDIENTES (ordenados por fecha)
    # ==========================================
    st.subheader("⏳ Partidos Pendientes")

    df_pendientes = partidos[partidos['estado'] == 'Pendiente'].copy()

    if not df_pendientes.empty:
        df_pendientes = ordenar_partidos(df_pendientes)

        for _, partido in df_pendientes.iterrows():
            local = partido.get('equipo_local_nombre', '?')
            visitante = partido.get('equipo_visitante_nombre', '?')
            fase = partido.get('fase', '')

            # Formatear fecha
            fecha = partido.get('fecha', '')
            fecha_str = ""
            if fecha and fecha != '':
                try:
                    fecha_obj = datetime.strptime(str(fecha), '%Y-%m-%d')
                    fecha_str = fecha_obj.strftime('%d/%m/%Y')
                except BaseException:
                    fecha_str = str(fecha)

            with st.container(border=True):
                col_a, col_b, col_c, col_d = st.columns([1.2, 2.5, 1.5, 1.5])
                with col_a:
                    st.write(f"📅 **{fecha_str}**")
                with col_b:
                    st.write(f"⏳ {local} vs {visitante}")
                with col_c:
                    st.write("⏳ Pendiente")
                with col_d:
                    st.write(f"🏟️ {fase}")
    else:
        st.info("✅ No hay partidos pendientes")
