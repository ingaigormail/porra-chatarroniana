# src/ui/admin/progresion_panel.py
"""Panel Admin: aplicar bonus de progresión por fase."""
import streamlit as st
from config.puntos_progresion import FASES_PROGRESION
from src.ui.admin._common import refrescar_datos


def mostrar_progresion(db):
    st.subheader("📈 Progresión por fase (bonus selecciones)")
    st.caption(
        "Dieciseisavos: 1º=18, 2º=15, 3º mejor 1-8=12…2. "
        "Octavos +10, Cuartos +15, Semis +20, Final +30.")

    st.markdown("#### 🗑️ Borrar progresión antigua")
    st.warning(
        "Elimina **todos** los bonus de progresión ya aplicados "
        "(para empezar de cero con las nuevas normas).")
    confirm = st.text_input(
        "Escribe BORRAR para confirmar",
        key="prog_confirm_borrar",
        placeholder="BORRAR",
    )
    if st.button(
            "🗑️ Borrar toda la progresión",
            type="primary",
            use_container_width=True,
            key="prog_btn_borrar_todo"):
        if confirm.strip().upper() != 'BORRAR':
            st.error("Debes escribir BORRAR en el campo de arriba.")
        else:
            r = db.eliminar_toda_progresion()
            if r['success']:
                st.success(r['message'])
                refrescar_datos()
            else:
                st.error(r['message'])

    st.markdown("---")
    st.markdown("#### ➕ Aplicar fase completa")

    fase_aplicar = st.selectbox(
        "Fase",
        options=FASES_PROGRESION,
        key="prog_fase_aplicar",
    )

    tabla = db.obtener_tabla_progresion_fase(fase_aplicar)
    if tabla.empty:
        st.info(f"No hay equipos en **{fase_aplicar}** todavía.")
    else:
        show = tabla[['equipo', 'motivo', 'puntos', 'estado', 'usuarios']].copy()
        show.columns = ['Equipo', 'Clasificación', 'Puntos', 'Estado', 'Usuarios']

        edited = st.data_editor(
            show,
            hide_index=True,
            use_container_width=True,
            disabled=['Equipo', 'Clasificación', 'Estado', 'Usuarios'],
            column_config={
                'Puntos': st.column_config.NumberColumn(min_value=0, max_value=100),
            },
            key=f"prog_editor_{fase_aplicar}",
        )

        n_pend = len(tabla[tabla['aplicado'] == False])
        st.caption(f"**{n_pend}** pendiente(s) de aplicar")

        if st.button(
                f"✅ Aplicar pendientes de {fase_aplicar}",
                type="primary",
                use_container_width=True):
            puntos_map = {}
            for i, row in tabla.iterrows():
                puntos_map[int(row['equipo_id'])] = int(edited.iloc[i]['Puntos'])
            with st.spinner("Aplicando..."):
                r = db.aplicar_progresion_fase(fase_aplicar, puntos_map)
            if r['success']:
                st.success(r['message'])
                refrescar_datos()
            else:
                st.error(r['message'])

    st.markdown("---")
    st.markdown("#### 📋 Corregir bonus aplicados")

    filtro = st.selectbox(
        "Ver fase",
        ['Todas'] + FASES_PROGRESION,
        key="prog_filtro_resumen",
    )
    resumen = db.obtener_resumen_progresion(
        None if filtro == 'Todas' else filtro)

    if resumen.empty:
        st.info("No hay bonus aplicados.")
    else:
        fase_prev = None
        for idx, row in resumen.iterrows():
            if row['fase'] != fase_prev:
                st.markdown(f"**🏟️ {row['fase']}**")
                fase_prev = row['fase']
            eid = int(row['equipo_id'])
            fase_row = row['fase']
            c1, c2, c3, c4, c5, c6 = st.columns([2, 0.7, 0.7, 1, 0.6, 0.6])
            with c1:
                st.write(row['equipo'])
            with c2:
                st.write(f"+{int(row['puntos'])}")
            with c3:
                st.write(f"{int(row['usuarios'])} usr")
            with c4:
                nuevo = st.number_input(
                    "pts",
                    0, 100, int(row['puntos']),
                    key=f"pnew_{idx}_{eid}_{fase_row}",
                    label_visibility="collapsed",
                )
            with c5:
                if st.button("💾", key=f"psave_{idx}_{eid}_{fase_row}"):
                    r = db.actualizar_puntos_progresion(eid, fase_row, int(nuevo))
                    if r['success']:
                        st.success("OK")
                        refrescar_datos()
                    else:
                        st.error(r['message'])
            with c6:
                if st.button("🗑️", key=f"pdel_{idx}_{eid}_{fase_row}"):
                    r = db.eliminar_progresion(eid, fase_row)
                    if r['success']:
                        refrescar_datos()

    st.markdown("---")
    st.markdown("#### ➕ Bonus manual (excepcional)")
    equipos_df = db.obtener_equipos()
    if not equipos_df.empty:
        c1, c2, c3 = st.columns(3)
        with c1:
            eq_nom = st.selectbox(
                "Equipo",
                sorted(equipos_df['nombre'].tolist()),
                key="prog_manual_eq",
            )
        with c2:
            fase_m = st.selectbox("Fase", FASES_PROGRESION, key="prog_manual_fase")
        with c3:
            pts_m = st.number_input("Puntos", 1, 100, 5, key="prog_manual_pts")
        eid_m = int(equipos_df[equipos_df['nombre'] == eq_nom]['id'].values[0])
        if st.button("Aplicar"):
            r = db.calcular_progresion(eid_m, fase_m, int(pts_m))
            if r['success']:
                st.success(r['message'])
                refrescar_datos()
            else:
                st.error(r['message'])
