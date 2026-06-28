# src/ui/admin/_common.py
"""Utilidades compartidas del panel de administración."""
import streamlit as st
import pandas as pd


def es_admin_luis(nombre_usuario) -> bool:
    if not nombre_usuario:
        return False
    return str(nombre_usuario).strip().lower() == 'luis'


def selector_goles(etiqueta: str, clave: str, valor_inicial: int = 0) -> int:
    indice = max(0, min(10, int(valor_inicial or 0)))
    return st.selectbox(
        etiqueta,
        options=list(range(11)),
        index=indice,
        key=clave,
        label_visibility="collapsed",
    )


def refrescar_datos():
    st.cache_data.clear()
    st.rerun()


def formatear_fecha(fecha) -> str:
    if fecha is None or (isinstance(fecha, float) and pd.isna(fecha)):
        return ''
    s = str(fecha).strip()
    if not s:
        return ''
    try:
        return pd.to_datetime(s).strftime('%d/%m/%Y')
    except (ValueError, TypeError):
        return s
