# src/ui/clasificacion.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils.banderas import con_bandera
from utils.graficos_clasificacion import (
    CATEGORIAS_DESGLOSE,
    color_barra_usuario,
)


def mostrar(df_rank, partidos, db):
    """Muestra la pestaña de Clasificación"""

    st.header("🏆 Clasificación General")

    if df_rank.empty:
        st.info("Aún no hay datos de clasificación")
        return

    # ==========================================
    # PODIO (3 PRIMEROS)
    # ==========================================
    col1, col2, col3 = st.columns(3)

    if len(df_rank) > 0:
        col1.metric(
            "🥇 1º", df_rank.iloc[0]['nombre'], f"{
                df_rank.iloc[0]['puntos']} pts")
    if len(df_rank) > 1:
        col2.metric(
            "🥈 2º", df_rank.iloc[1]['nombre'], f"{
                df_rank.iloc[1]['puntos']} pts")
    if len(df_rank) > 2:
        col3.metric(
            "🥉 3º", df_rank.iloc[2]['nombre'], f"{
                df_rank.iloc[2]['puntos']} pts")

    st.write("---")

    # ==========================================
    # POZO (3 ÚLTIMOS)
    # ==========================================
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
        col_paq3.metric(
            "😅 Antepenúltimo", paq3['nombre'], f"{
                paq3['puntos']} pts")

    st.write("---")

    # ==========================================
    # TABLA COMPLETA + GRÁFICO DE BARRAS
    # ==========================================
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

    # ==========================================
    # DOS COLUMNAS: TABLA + GRÁFICO
    # ==========================================
    col_izq, col_der = st.columns([1, 1.5])

    with col_izq:
        st.dataframe(
            df_tabla[['posicion', 'nombre', 'puntos', 'Cambio']],
            hide_index=True,
            width='stretch',
            column_config={
                'posicion': st.column_config.TextColumn('Pos', width='small'),
                'nombre': st.column_config.TextColumn('Jugador', width='medium'),
                'puntos': st.column_config.NumberColumn('Puntos', width='small', format='%d'),
                'Cambio': st.column_config.TextColumn('Cambio', width='small')
            }
        )

    with col_der:
        st.markdown("#### 📊 Clasificación en barras")

        df_grafico = db.obtener_datos_grafico_clasificacion()

        if not df_grafico.empty:
            colores = [
                color_barra_usuario(row['nombre'], idx)
                for idx, (_, row) in enumerate(df_grafico.iterrows())
            ]

            fig = go.Figure()

            for idx, (_, row) in enumerate(df_grafico.iterrows()):
                color_config = colores[idx]
                if isinstance(
                        color_config,
                        dict) and 'pattern' in color_config:
                    fig.add_trace(go.Bar(
                        x=[row['nombre']],
                        y=[row['puntos']],
                        text=[row['puntos']],
                        textposition='auto',
                        marker=color_config,
                        name=row['nombre'],
                        showlegend=False
                    ))
                else:
                    fig.add_trace(go.Bar(
                        x=[row['nombre']],
                        y=[row['puntos']],
                        text=[row['puntos']],
                        textposition='auto',
                        marker=dict(color=color_config),
                        name=row['nombre'],
                        showlegend=False
                    ))

            fig.update_layout(
                margin=dict(l=0, r=0, t=10, b=80),
                yaxis_title="Puntos",
                xaxis=dict(showticklabels=True, tickangle=-45),
                showlegend=False,
                height=400,
                barmode='group'
            )

            st.plotly_chart(
                fig, width='stretch', theme=None, config={
                    "displayModeBar": False})
            st.caption(
                "🔴🟡 Las barras de JC y Saul tienen rayas rojas y amarillas (bandera estelada)")
        else:
            st.info("No hay datos para mostrar")

    st.markdown("#### 📊 Desglose de puntos por jugador")

    df_desglose = db.obtener_desglose_puntos()
    if df_desglose.empty:
        st.info("No hay datos para el desglose.")
    else:
        fig_desglose = go.Figure()
        for col, etiqueta, color in CATEGORIAS_DESGLOSE:
            if df_desglose[col].sum() == 0:
                continue
            fig_desglose.add_trace(go.Bar(
                name=etiqueta,
                x=df_desglose['nombre'],
                y=df_desglose[col],
                marker_color=color,
                hovertemplate=(
                    '%{x}<br>' + etiqueta + ': %{y} pts<extra></extra>'
                ),
            ))

        fig_desglose.update_layout(
            barmode='stack',
            margin=dict(l=0, r=0, t=30, b=80),
            yaxis_title="Puntos",
            xaxis=dict(showticklabels=True, tickangle=-45),
            legend=dict(
                orientation='h',
                yanchor='bottom',
                y=1.02,
                xanchor='right',
                x=1,
            ),
            height=max(450, 35 * len(df_desglose)),
        )

        st.plotly_chart(
            fig_desglose,
            width='stretch',
            theme=None,
            config={"displayModeBar": False},
        )
        st.caption(
            "Grupos y partidos = puntos de tus selecciones en el torneo real. "
            "Los bonus de fase se suman al pasar cada ronda.")

    st.write("---")

    # ==========================================
    # ESTADO DE PARTIDOS Y FASES
    # ==========================================
    st.subheader("📅 Estado de Partidos y Fases 🏟️")

    if not partidos.empty:
        orden_fases = [
            'Grupos',
            'Dieciseis',
            'Octavos',
            'Cuartos',
            'Semifinal',
            '3 y 4',
            'Final']
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

    # ==========================================
    # MOVIMIENTOS DE LA SEMANA
    # ==========================================
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
                movimientos.append(
                    {'nombre': row['nombre'], 'cambio': 33 - (pos - 1) * 2, 'tipo': 'sube'})
            elif pos >= total_jugadores - 2:
                movimientos.append(
                    {'nombre': row['nombre'], 'cambio': 0, 'tipo': 'baja'})
            else:
                movimientos.append(
                    {'nombre': row['nombre'], 'cambio': 0, 'tipo': 'mantiene'})

        df_mov['cambio'] = [m['cambio'] for m in movimientos]
        df_mov['tipo'] = [m['tipo'] for m in movimientos]

    col_sube, col_baja = st.columns(2)

    with col_sube:
        st.markdown("#### 📈 Los que más han subido")
        top_subida = df_mov[df_mov['tipo'] == 'sube'].sort_values(
            'cambio', ascending=False).head(3)
        if not top_subida.empty:
            for _, row in top_subida.iterrows():
                st.success(
                    f"🟢 **{row['nombre']}** subió **{int(row['cambio'])} puestos** → {int(row['posicion'])}º")
        else:
            st.info("No hay movimientos de subida")

    with col_baja:
        st.markdown("#### 📉 Los que más han bajado")
        top_bajada = df_mov[df_mov['tipo'] == 'baja'].head(3)
        if not top_bajada.empty:
            for _, row in top_bajada.iterrows():
                st.error(
                    f"🔴 **{row['nombre']}** bajó **{abs(int(row['cambio']))} puestos** → {int(row['posicion'])}º")

        mantienen = df_mov[(df_mov['tipo'] == 'mantiene') |
                           (df_mov['cambio'] == 0)].head(3)
        for _, row in mantienen.iterrows():
            st.info(
                f"⚪ **{row['nombre']}** se mantiene en {int(row['posicion'])}º")

    st.write("---")

    # ==========================================
    # MVP Y RADAR
    # ==========================================
    col_mvp, col_radar = st.columns(2)

    with col_mvp:
        st.header("🌟 El Equipo MVP")
        st.info("El país que más puntos está sumando en el torneo real.")

        mvp_df = db.obtener_mvp()

        if not mvp_df.empty:
            max_puntos = mvp_df['puntos'].iloc[0]

            if len(mvp_df) == 1:
                st.success(
                    f"### ⚽ {
                        mvp_df.iloc[0]['nombre']} con {
                        int(max_puntos)} puntos")
            else:
                st.success(f"### 🏆 {int(max_puntos)} puntos")
                for _, row in mvp_df.iterrows():
                    st.write(f"• ⚽ {row['nombre']}")
        else:
            st.warning("Datos del MVP no disponibles.")

    with col_radar:
        st.header("🎯 Radar Chatarroniano")

        radar_df = db.obtener_radar()

        if not radar_df.empty:
            favorito = radar_df.iloc[0]
            st.write(
                f"❤️ **El Favorito:** ⚽ {favorito['nombre']} (Elegido {favorito['votos']} veces)")

            lobos = radar_df[radar_df['votos'] == 1]
            if not lobos.empty:
                lobos_list = [
                    f"⚽ {
                        row['nombre']}" for _,
                    row in lobos.iterrows()]
                st.write(
                    f"🐺 **Apuestas de 'Lobo Solitario':** {', '.join(lobos_list[:5])} (Solo 1 persona los eligió)")
            else:
                st.write("🐺 No hay apuestas de 'Lobo Solitario'")
        else:
            st.write("Esperando a que se introduzcan las selecciones de todos...")

    st.write("---")

    # ==========================================
    # GRÁFICO: EQUIPOS MÁS APOSTADOS
    # ==========================================
    st.subheader("📊 Equipos más apostados por los chatarronianos")

    df_votos = db.obtener_equipos_mas_votados()

    if not df_votos.empty:
        colores = ['#19D3F3', '#00CC96'] * (len(df_votos) // 2 + 1)
        colores = colores[:len(df_votos)]

        fig = go.Figure(go.Bar(
            x=df_votos['Equipo'],
            y=df_votos['Votos'],
            text=df_votos['Votos'],
            textposition='auto',
            marker_color=colores
        ))

        fig.update_layout(
            margin=dict(l=0, r=0, t=30, b=80),
            yaxis_title="Nº de jugadores que lo eligieron",
            xaxis=dict(showticklabels=True, tickangle=-45),
            showlegend=False,
            height=400
        )

        st.plotly_chart(
            fig, width='stretch', theme=None, config={
                "displayModeBar": False})
    else:
        st.info("Esperando a que se introduzcan las selecciones de todos...")

    st.write("---")

    # ==========================================
    # GRÁFICO: PUNTOS POR EQUIPO EN EL TORNEO REAL
    # ==========================================
    st.subheader("🏅 Puntos por Equipo en el Torneo Real")

    df_puntos = db.obtener_puntos_equipos_reales()

    if not df_puntos.empty:
        colores = ['#2ECC71', '#F1C40F'] * (len(df_puntos) // 2 + 1)
        colores = colores[:len(df_puntos)]

        fig = go.Figure(go.Bar(
            x=df_puntos['nombre'],
            y=df_puntos['puntos'],
            text=df_puntos['puntos'],
            textposition='auto',
            marker_color=colores
        ))

        fig.update_layout(
            margin=dict(l=0, r=0, t=30, b=80),
            yaxis_title="Puntos en el torneo",
            xaxis=dict(showticklabels=True, tickangle=-45),
            showlegend=False,
            height=400
        )

        st.plotly_chart(
            fig, width='stretch', theme=None, config={
                "displayModeBar": False})
    else:
        st.info("No hay datos de puntos disponibles")
