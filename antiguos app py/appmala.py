import streamlit as st
import pandas as pd
import flag
from collections import Counter
import plotly.graph_objects as go
import unicodedata

st.set_page_config(page_title="Mundial 2026 chatarronianos", layout="wide")
st.title("🏆 Mundial 2026 chatarronianos")

# 🔗 CONEXIÓN PÚBLICA
try:
    sheet_id = "1NncO0BuIR8BeYNz8a-VIUODFRx6rdDRwa0xZJQypG44"
    url_base = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet="
    
    df_usuarios = pd.read_csv(url_base + "Participantes ")
    df_calendario = pd.read_csv(url_base + "calendario")
    df_equipos = pd.read_csv(url_base + "equipos")
    
    # Filtro columnas Calendario
    cols_cal = ["Partido", "Grupo", "Equipo 1", "Goles 1", "Equipo 2", "Goles 2", "Estado", "Ganador"]
    df_calendario = df_calendario[[c for c in cols_cal if c in df_calendario.columns]]
        
except Exception as e:
    st.error(f"🚨 Error al conectar: {e}")
    st.stop()

col_nombre = "Nombre "
col_puntos = "Puntos_totales." 
df_usuarios[col_puntos] = pd.to_numeric(df_usuarios[col_puntos], errors='coerce').fillna(0).astype(int)

if "Posicion_anterior" not in df_usuarios.columns: df_usuarios["Posicion_anterior"] = 0
df_usuarios["Posicion_anterior"] = pd.to_numeric(df_usuarios["Posicion_anterior"], errors='coerce').fillna(0).astype(int)

def con_bandera(pais):
    p_limpio = str(pais).strip()
    return f"⚽ {p_limpio}" # Puedes ampliar el diccionario de banderas aquí

st.sidebar.header("🔑 Identificación")
nombre_usuario = st.sidebar.text_input("Introduce tu Nombre:", value="").strip()

if not nombre_usuario:
    st.warning("👋 ¡Bienvenido! Introduce tu nombre.")
elif nombre_usuario not in df_usuarios[col_nombre].values:
    st.error("⚠️ Nombre no encontrado.")
else:
    idx = df_usuarios[df_usuarios[col_nombre] == nombre_usuario].index[0]
    fila_user = df_usuarios.loc[idx]
    tab1, tab2, tab3 = st.tabs(["👑 Dashboard", "🛡️ Mi Ficha", "📅 Calendario"])

    with tab1:
        st.header("👑 El Salón de la Fama")
        df_ranking = df_usuarios[[col_nombre, col_puntos]].sort_values(by=col_puntos, ascending=False).reset_index(drop=True)
        
        # 🌟 MVP MULTIPLE
        st.header("🌟 El Equipo MVP")
        col_pts_eq = [c for c in df_equipos.columns if 'puntos' in str(c).lower()][0]
        col_nom_eq = df_equipos.columns[0]
        max_pts = df_equipos[col_pts_eq].max()
        mvps = df_equipos[df_equipos[col_pts_eq] == max_pts]
        for _, row in mvps.iterrows():
            st.success(f"### {row[col_nom_eq]} con {row[col_pts_eq]} puntos")

    with tab3:
        st.header("📅 Calendario")
        st.dataframe(df_calendario, use_container_width=True)