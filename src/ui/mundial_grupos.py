# src/ui/mundial_grupos.py
import streamlit as st
import pandas as pd


def _nombre_equipo(valor) -> str:
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return 'Por definir'
    return str(valor)


def _tarjeta_partido(partido: pd.Series) -> None:
    """Muestra un partido en formato compacto."""
    local = _nombre_equipo(partido.get('equipo_local_nombre'))
    visit = _nombre_equipo(partido.get('equipo_visitante_nombre'))
    pid = int(partido['id'])
    estado = partido.get('estado', 'Pendiente')

    with st.container(border=True):
        st.caption(f"#{pid}")
        if estado == 'Jugado':
            gl = int(partido.get('goles_local') or 0)
            gv = int(partido.get('goles_visitante') or 0)
            st.markdown(f"**{local}** {gl} – {gv} **{visit}**")
            st.caption("✅ Jugado")
        else:
            st.markdown(f"**{local}** vs **{visit}**")
            st.caption("⏳ Pendiente")


def _partidos_por_ids(partidos: pd.DataFrame, ids: list[int]) -> pd.DataFrame:
    df = partidos[partidos['id'].isin(ids)].copy()
    df['_orden'] = df['id'].map({i: n for n, i in enumerate(ids)})
    return df.sort_values('_orden')


def _mostrar_fase_dos_columnas(
        partidos: pd.DataFrame, titulo: str, ids_izq: list[int], ids_der: list[int]) -> None:
    st.markdown(f"#### {titulo}")
    col_izq, col_der = st.columns(2)
    with col_izq:
        for _, p in _partidos_por_ids(partidos, ids_izq).iterrows():
            _tarjeta_partido(p)
    with col_der:
        for _, p in _partidos_por_ids(partidos, ids_der).iterrows():
            _tarjeta_partido(p)


def _mostrar_cuadro_eliminatorio(partidos: pd.DataFrame) -> None:
    elim = partidos[partidos['fase'] != 'Grupos']
    if elim.empty:
        st.info(
            "Fase de grupos completada. Ve a **Admin → Generar Cruces** "
            "para crear los partidos de Dieciseisavos.")
        return

    st.subheader("🏆 Cuadro Eliminatorio")

    # Dieciseisavos: mitad izquierda / derecha del cuadro (M73-80 | M81-88)
    _mostrar_fase_dos_columnas(
        elim,
        "⚔️ Dieciseisavos de final",
        list(range(73, 81)),
        list(range(81, 89)),
    )

    st.write("")

    # Octavos: M89-92 | M93-96
    _mostrar_fase_dos_columnas(
        elim,
        "⚔️ Octavos de final",
        list(range(89, 93)),
        list(range(93, 97)),
    )

    st.write("")

    # Cuartos: M97-98 | M99-100
    _mostrar_fase_dos_columnas(
        elim,
        "⚔️ Cuartos de final",
        [97, 98],
        [99, 100],
    )

    st.write("")

    # Semifinales: M101 | M102
    _mostrar_fase_dos_columnas(
        elim,
        "⚔️ Semifinales",
        [101],
        [102],
    )

    st.write("")

    # 3.er puesto y Final
    st.markdown("#### 🏅 Finales")
    col_bronce, col_final = st.columns(2)
    with col_bronce:
        st.markdown("🥉 **3.º y 4.º puesto**")
        df_bronce = _partidos_por_ids(elim, [103])
        if df_bronce.empty:
            st.info("Partido aún no configurado")
        else:
            _tarjeta_partido(df_bronce.iloc[0])
    with col_final:
        st.markdown("🏆 **Final**")
        df_final = _partidos_por_ids(elim, [104])
        if df_final.empty:
            st.info("Partido aún no configurado")
        else:
            _tarjeta_partido(df_final.iloc[0])


def mostrar(db):
    """Muestra la clasificación de todos los grupos del Mundial"""

    st.header("🌍 Clasificación del Mundial 2026")

    # ==========================================
    # TODOS LOS GRUPOS (3 por fila)
    # ==========================================

    grupos = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L']

    for i in range(0, len(grupos), 3):
        cols = st.columns(3)
        for j, grupo in enumerate(grupos[i:i + 3]):
            with cols[j]:
                df_grupo = db.calcular_clasificacion_grupo(grupo)
                if not df_grupo.empty:
                    st.markdown(f"### 📋 Grupo {grupo}")

                    tabla = df_grupo[['posicion',
                                      'nombre',
                                      'pj',
                                      'ganados',
                                      'empatados',
                                      'perdidos',
                                      'gf',
                                      'gc',
                                      'dg',
                                      'puntos']].copy()
                    tabla.columns = ['Pos', 'Equipo', 'PJ',
                                     'G', 'E', 'P', 'GF', 'GC', 'DG', 'Pts']

                    def color_fila(row):
                        if row['Pos'] == 1:
                            return 'background-color: #2ECC71; color: white;'
                        elif row['Pos'] == 2:
                            return 'background-color: #3498DB; color: white;'
                        elif row['Pos'] == 3:
                            return 'background-color: #F39C12; color: white;'
                        else:
                            return 'background-color: #ECF0F1;'

                    styled = tabla.style.apply(
                        lambda row: [color_fila(row) for _ in row], axis=1)

                    st.dataframe(
                        styled,
                        hide_index=True,
                        width='stretch',
                        column_config={
                            'Pos': st.column_config.TextColumn('Pos', width='small'),
                            'Equipo': st.column_config.TextColumn('Equipo', width='medium'),
                            'PJ': st.column_config.NumberColumn('PJ', width='small'),
                            'G': st.column_config.NumberColumn('G', width='small'),
                            'E': st.column_config.NumberColumn('E', width='small'),
                            'P': st.column_config.NumberColumn('P', width='small'),
                            'GF': st.column_config.NumberColumn('GF', width='small'),
                            'GC': st.column_config.NumberColumn('GC', width='small'),
                            'DG': st.column_config.NumberColumn('DG', width='small'),
                            'Pts': st.column_config.NumberColumn('Pts', width='small'),
                        }
                    )
                else:
                    st.info(f"Grupo {grupo}: sin datos")

    st.write("---")

    # ==========================================
    # MEJORES TERCEROS
    # ==========================================
    st.subheader("🏆 Los 8 Mejores Terceros (clasifican a Dieciseisavos)")

    mejores_terceros = db.calcular_mejores_terceros()

    if not mejores_terceros.empty:
        tabla_terceros = mejores_terceros[[
            'posicion_mejores_terceros', 'grupo', 'nombre', 'puntos', 'dg', 'gf', 'clasifica']].copy()
        tabla_terceros.columns = [
            'Pos',
            'Grupo',
            'Equipo',
            'Pts',
            'DG',
            'GF',
            'Clasifica']

        def color_terceros(row):
            if row['Clasifica']:
                return 'background-color: #27AE60; color: white; font-weight: bold;'
            else:
                return 'background-color: #E74C3C; color: white;'

        styled_terceros = tabla_terceros.style.apply(
            lambda row: [color_terceros(row) for _ in row], axis=1)

        st.dataframe(
            styled_terceros,
            hide_index=True,
            width='stretch',
            column_config={
                'Pos': st.column_config.TextColumn('Pos', width='small'),
                'Grupo': st.column_config.TextColumn('Grupo', width='small'),
                'Equipo': st.column_config.TextColumn('Equipo', width='medium'),
                'Pts': st.column_config.NumberColumn('Pts', width='small'),
                'DG': st.column_config.NumberColumn('DG', width='small'),
                'GF': st.column_config.NumberColumn('GF', width='small'),
                'Clasifica': st.column_config.TextColumn('✅', width='small'),
            }
        )

        st.caption("✅ Los 8 primeros (en verde) clasifican a Dieciseisavos")
        st.caption("❌ Los 4 últimos (en rojo) quedan eliminados")
    else:
        st.info("Aún no hay datos suficientes para calcular los mejores terceros")

    st.write("---")

    # ==========================================
    # CUADRO ELIMINATORIO
    # ==========================================
    partidos = db.obtener_partidos()
    grupos_p = partidos[partidos['fase'] == 'Grupos']
    fase_grupos_completa = (
        not grupos_p.empty
        and (grupos_p['estado'] == 'Jugado').all()
    )

    if fase_grupos_completa:
        _mostrar_cuadro_eliminatorio(partidos)
    else:
        pend = len(grupos_p[grupos_p['estado'] != 'Jugado']) if not grupos_p.empty else '?'
        st.info(
            f"📊 Fase de grupos en curso ({pend} partidos pendientes). "
            "Al terminar todos los grupos se podrán generar los cruces de Dieciseisavos.")
