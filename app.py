import streamlit as st
import pandas as pd
import gspread
# en teoria lo borro from google.oauth2.service_account import Credentials
import flag
from collections import Counter
import plotly.graph_objects as go
import unicodedata
import os
import datetime

st.set_page_config(page_title="Mundial 2026 chatarronianos", layout="wide")

st.title("🏆 Mundial 2026 chatarronianos")

# 🔗 CONEXIÓN PÚBLICA (SIN CLAVES) con caché para no recargar en cada interacción
@st.cache_data(ttl=300)  # Refresca cada 5 minutos
def cargar_datos():
    sheet_id = "1NncO0BuIR8BeYNz8a-VIUODFRx6rdDRwa0xZJQypG44"
    url_participantes = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet=Participantes"
    url_calendario = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet=calendario"
    url_equipos = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet=equipos"
    url_llaves = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet=llaves"

    df_usuarios = pd.read_csv(url_participantes)
    # Renombrar columna BD (índice 55) si viene como Unnamed por problema de exportación en Google Sheets
    if 'Unnamed: 55' in df_usuarios.columns:
        df_usuarios.rename(columns={'Unnamed: 55': 'Puntos_totales'}, inplace=True)
    df_calendario = pd.read_csv(url_calendario)
    try:
        df_equipos = pd.read_csv(url_equipos)
        df_equipos.columns = [str(c).strip() for c in df_equipos.columns]
    except Exception:
        df_equipos = pd.DataFrame()
    try:
        # header=None → los índices de fila/columna coinciden exactamente con la hoja
        # Fila 1 = iloc[0], Fila 2 = iloc[1], Columna J = índice 9
        df_llaves = pd.read_csv(url_llaves, header=None)
    except Exception:
        df_llaves = pd.DataFrame()
    return df_usuarios, df_calendario, df_equipos, df_llaves

try:
    df_usuarios, df_calendario, df_equipos, df_llaves = cargar_datos()
except Exception as e:
    st.error(f"🚨 Error al conectar con la hoja: {e}")
    st.stop()

col_nombre = "Nombre "

# Buscar dinámicamente la columna de puntos (tolerante a espacios y puntuación)
_col_puntos_candidatos = [c for c in df_usuarios.columns if "puntos_totales" in str(c).lower().replace(" ", "_")]
if _col_puntos_candidatos:
    col_puntos = _col_puntos_candidatos[0]
else:
    # Fallback: mostrar columnas disponibles y detener la app
    st.error(f"🚨 No se encontró la columna 'Puntos_totales' en la hoja Participantes. "
             f"Columnas disponibles: {list(df_usuarios.columns)}")
    st.stop()

df_usuarios[col_puntos] = pd.to_numeric(df_usuarios[col_puntos], errors='coerce').fillna(0).astype(int)

if "Posicion_anterior" not in df_usuarios.columns:
    df_usuarios["Posicion_anterior"] = 0
df_usuarios["Posicion_anterior"] = pd.to_numeric(df_usuarios["Posicion_anterior"], errors='coerce').fillna(0).astype(int)

def limpiar_nombre(texto):
    """Quita tildes y mayúsculas para asegurar que reconoce a Saul y Palpatin"""
    texto = str(texto).strip().lower()
    texto = ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
    return texto

# --- 📅 FECHA DE ÚLTIMA ACTUALIZACIÓN DEL ARCHIVO ---
try:
    _ts = os.path.getmtime(__file__)
    _fecha_mod = datetime.datetime.fromtimestamp(_ts).strftime("%d/%m/%Y %H:%M")
    st.sidebar.caption(f"🕐 Última actualización: **{_fecha_mod}**")
except Exception:
    pass

# --- 🔐 VALIDACIÓN ÚNICA POR NOMBRE ---
st.sidebar.header("🔑 Identificación")
nombre_usuario = st.sidebar.text_input("Introduce tu Nombre para entrar:", value="").strip()

if not nombre_usuario:
    st.warning("👋 ¡Bienvenido! Introduce tu nombre en la barra lateral para ver el súper dashboard y tu ficha.")
elif nombre_usuario not in df_usuarios[col_nombre].values:
    st.error("⚠️ Este nombre no está registrado en la porra. Escríbelo tal y como sale en la lista.")
else:
    idx = df_usuarios[df_usuarios[col_nombre] == nombre_usuario].index[0]
    fila_user = df_usuarios.loc[idx]
    st.sidebar.success(f"✅ Conectado: {fila_user[col_nombre]}")

    codigos_paises = {
        "Espana": "ES", "Argentina": "AR", "Brasil": "BR", "Francia": "FR", 
        "Alemania": "DE", "Portugal": "PT", "Inglaterra": "GB",
        "Mexico": "MX", "Canada": "CA", "Estados Unidos": "US", "Paises Bajos": "NL",
        "Uruguay": "UY", "Colombia": "CO", "Ecuador": "EC", "Peru": "PE", "Chile": "CL",
        "Italia": "IT", "Belgica": "BE", "Croacia": "HR", "Marruecos": "MA", "Japon": "JP"
    }

    def con_bandera(pais):
        p_limpio = str(pais).strip()
        if p_limpio == "" or p_limpio.lower() == "nan": return "🏳️ -"
        codigo = codigos_paises.get(p_limpio, None)
        if codigo:
            try: return f"{flag.flag(codigo)} {p_limpio}"
            except: return f"⚽ {p_limpio}"
        return f"⚽ {p_limpio}"

    tab1, tab2, tab3, tab4 = st.tabs(["👑 Dashboard General", "🛡️ Mi Ficha Privada", "📅 Calendario y Resultados", "🔮 Pronóstico"])

    # ==========================================
    # PESTAÑA 1: EL SÚPER DASHBOARD
    # ==========================================
    with tab1:
        st.header("👑 El Salón de la Fama")
        df_ranking = df_usuarios[[col_nombre, col_puntos, "Posicion_anterior"]].sort_values(by=col_puntos, ascending=False).reset_index(drop=True)
        df_ranking["Posicion_actual"] = df_ranking.index + 1
        total_jugadores = len(df_ranking)
        
        st.write("¿Quién lidera la clasificación y a cuántos puntos están los perseguidores?")
        col_podio1, col_podio2, col_podio3 = st.columns(3)
        
        if total_jugadores > 0: 
            lider_pts = df_ranking.loc[0, col_puntos]
            col_podio1.metric(label="🥇 LÍDER INDISCUTIBLE", value=f"{df_ranking.loc[0, col_nombre]}", delta=f"{lider_pts} pts", delta_color="off")
        
        if total_jugadores > 1: 
            pts_2 = df_ranking.loc[1, col_puntos]
            distancia_2 = pts_2 - lider_pts
            col_podio2.metric(label="🥈 2º Puesto", value=f"{df_ranking.loc[1, col_nombre]} ({pts_2} pts)", delta=f"A {abs(distancia_2)} pts del líder", delta_color="inverse" if distancia_2 < 0 else "off")
            
        if total_jugadores > 2: 
            pts_3 = df_ranking.loc[2, col_puntos]
            distancia_3 = pts_3 - lider_pts
            col_podio3.metric(label="🥉 3º Puesto", value=f"{df_ranking.loc[2, col_nombre]} ({pts_3} pts)", delta=f"A {abs(distancia_3)} pts del líder", delta_color="inverse" if distancia_3 < 0 else "off")
        
        st.write("---")
        
        # 🔻 ZONA DE LOS 3 ÚLTIMOS 🔻
        st.markdown("#### 🐢 El Pozo (Los 3 últimos clasificados)")
        col_paq1, col_paq2, col_paq3 = st.columns(3)
        
        if total_jugadores > 0: 
            paq1 = df_ranking.iloc[-1]
            col_paq1.metric(label="🛑 Último Puesto", value=paq1[col_nombre], delta=f"{paq1[col_puntos]} pts", delta_color="inverse")
        if total_jugadores > 1: 
            paq2 = df_ranking.iloc[-2]
            col_paq2.metric(label="⚠️ Penúltimo", value=paq2[col_nombre], delta=f"{paq2[col_puntos]} pts", delta_color="inverse")
        if total_jugadores > 2: 
            paq3 = df_ranking.iloc[-3]
            col_paq3.metric(label="🐌 Antepenúltimo", value=paq3[col_nombre], delta=f"{paq3[col_puntos]} pts", delta_color="inverse")

        st.write("---")

        # ==========================================
        # 📋 TABLA COMPLETA DE CLASIFICACIÓN
        # ==========================================
        st.subheader("📋 Clasificación Completa")

        def calcular_cambio(row):
            pos_actual = int(row["Posicion_actual"])
            pos_ant = int(row["Posicion_anterior"])
            if pos_ant == 0:
                return "⚪ ="
            diff = pos_ant - pos_actual
            if diff > 0:
                return f"🟢 ↑ +{diff}"
            elif diff < 0:
                return f"🔴 ↓ {diff}"
            else:
                return "⚪ ="

        df_tabla = df_ranking.copy()
        df_tabla["Cambio"] = df_tabla.apply(calcular_cambio, axis=1)
        df_tabla["Pos"] = df_tabla["Posicion_actual"].apply(lambda x: f"{x}º")
        df_tabla_display = df_tabla[["Pos", col_nombre, col_puntos, "Cambio"]].rename(columns={
            col_nombre: "Jugador",
            col_puntos: "Puntos"
        })
        # Tabla centrada y con tamaño ajustado
        col_izq, col_centro, col_der = st.columns([1, 2, 1])
        with col_centro:
            st.dataframe(
                df_tabla_display,
                width='stretch',
                hide_index=True,
                column_config={
                    "Pos": st.column_config.TextColumn("Pos", width="small"),
                    "Jugador": st.column_config.TextColumn("Jugador", width="medium"),
                    "Puntos": st.column_config.NumberColumn("Puntos", width="small"),
                    "Cambio": st.column_config.TextColumn("Cambio", width="small"),
                }
            )

        st.write("---")

        # ==========================================
        # 📅 ESTADO DE PARTIDOS Y FASES
        # ==========================================
        st.subheader("📅 Estado de Partidos y Fases 🏟️")

        # ── Verificación temporal de columnas (visible solo para Luis) ──
        if nombre_usuario.strip().lower() == "luis":
            with st.expander("🔎 Verificar columnas calendario (admin)"):
                st.write("Columnas disponibles en calendario:", list(df_calendario.columns))

        def _icono_fase(fase):
            f = str(fase).lower()
            if 'grupo' in f:
                return "🌍"
            elif any(x in f for x in ['octavo', 'dieciseis', '16', '32', 'treintaidos']):
                return "⚔️"
            elif any(x in f for x in ['cuarto', 'semi', 'final', 'tercero']):
                return "🏆"
            return "🏟️"

        if 'Fase ' in df_calendario.columns and 'Estado' in df_calendario.columns:
            _orden_fases_manual = ['Grupos', 'Dieciseis', 'Octavos', 'Cuartos', 'Semifinal', '3 y 4', 'Final']
            _fases_disponibles = set(df_calendario['Fase '].dropna().unique())
            _fases_extra = sorted([f for f in _fases_disponibles if f not in _orden_fases_manual])
            fases_orden = [f for f in _orden_fases_manual if f in _fases_disponibles] + _fases_extra
            for _fase in fases_orden:
                df_fase_cal = df_calendario[df_calendario['Fase '] == _fase]
                _jugados = int((df_fase_cal['Estado'] == 'Jugado').sum())
                _pendientes = int((df_fase_cal['Estado'] == 'Pendiente').sum())
                with st.container(border=True):
                    st.markdown(f"#### {_icono_fase(_fase)} Fase: {_fase}")
                    _cj, _cp = st.columns(2)
                    _cj.metric("Jugados ⚽", _jugados)
                    _cp.metric("Pendientes ⏳", _pendientes)
        else:
            st.warning(f"⚠️ No se encuentran las columnas 'Fase ' o 'Estado'. Columnas: {list(df_calendario.columns)}")

        st.write("---")

        # ==========================================
        # 🚀 QUIÉN HA SUBIDO / BAJADO MÁS
        # ==========================================
        df_movimiento = df_ranking[df_ranking["Posicion_anterior"] > 0].copy()
        df_movimiento["Cambio_num"] = df_movimiento["Posicion_anterior"] - df_movimiento["Posicion_actual"]

        if not df_movimiento.empty:
            st.subheader("🚀 Movimientos de la Semana")
            col_sube, col_baja = st.columns(2)

            with col_sube:
                st.markdown("#### 📈 Los que más han subido")
                top_subida = df_movimiento.sort_values("Cambio_num", ascending=False).head(3)
                for _, row in top_subida.iterrows():
                    if row["Cambio_num"] > 0:
                        st.success(f"🟢 **{row[col_nombre]}** subió **{int(row['Cambio_num'])} puestos** → {int(row['Posicion_actual'])}º")
                    else:
                        st.info(f"⚪ **{row[col_nombre]}** se mantiene en {int(row['Posicion_actual'])}º")

            with col_baja:
                st.markdown("#### 📉 Los que más han bajado")
                top_bajada = df_movimiento.sort_values("Cambio_num", ascending=True).head(3)
                for _, row in top_bajada.iterrows():
                    if row["Cambio_num"] < 0:
                        st.error(f"🔴 **{row[col_nombre]}** bajó **{abs(int(row['Cambio_num']))} puestos** → {int(row['Posicion_actual'])}º")
                    else:
                        st.info(f"⚪ **{row[col_nombre]}** se mantiene en {int(row['Posicion_actual'])}º")

            st.write("---")

        col_stats1, col_stats2 = st.columns(2)
        
        with col_stats1:
            st.header("🌟 El Equipo MVP")
            st.info("El país que más puntos está sumando en el torneo real.")
            if not df_equipos.empty:
                try:
                    col_pts_eq = [c for c in df_equipos.columns if 'punto' in str(c).lower()][0]
                    col_nom_eq = df_equipos.columns[0] 
                    df_eq_sort = df_equipos.copy()
                    df_eq_sort[col_pts_eq] = pd.to_numeric(df_eq_sort[col_pts_eq], errors='coerce').fillna(0)
                    df_eq_sort = df_eq_sort.sort_values(by=col_pts_eq, ascending=False).reset_index(drop=True)
                    pts_mejor = df_eq_sort.loc[0, col_pts_eq]
                    # Todos los equipos empatados en el máximo de puntos
                    mejores = df_eq_sort[df_eq_sort[col_pts_eq] == pts_mejor][col_nom_eq].tolist()
                    if len(mejores) == 1:
                        st.success(f"### {con_bandera(mejores[0])} con {int(pts_mejor)} puntos")
                    else:
                        st.success(f"### 🏆 {int(pts_mejor)} puntos")
                        for eq_mvp in mejores:
                            st.write(f"• {con_bandera(eq_mvp)}")
                except Exception as e:
                    st.warning(f"Datos del MVP calculándose... ({e})")
            else:
                st.warning("Datos del MVP no disponibles.")

        with col_stats2:
            st.header("🎯 Radar Chatarroniano")
            cols_equipos = [c for c in df_usuarios.columns if 'equipo' in str(c).lower() and 'pts_' not in str(c).lower()]
            todos_los_votos = df_usuarios[cols_equipos].values.flatten()

            # Normalizar nombre: sin tildes, sin espacios extra, minúsculas → clave de agrupación
            def _canon_eq(x):
                s = str(x).strip()
                s = ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
                s = ' '.join(s.split())  # elimina espacios múltiples/no rompibles
                return s.lower()

            # Mapa: forma_canónica -> nombre original representativo (primera aparición)
            _mapa_repr = {}
            for _v in todos_los_votos:
                _orig = str(_v).strip()
                if _orig == "" or _orig.lower() == "nan":
                    continue
                _k = _canon_eq(_orig)
                if _k and _k != "nan" and _k not in _mapa_repr:
                    _mapa_repr[_k] = _orig

            # votos_limpios: lista unificada por forma canónica
            votos_limpios = [_mapa_repr[_canon_eq(x)]
                             for x in todos_los_votos
                             if str(x).strip() != "" and str(x).strip().lower() != "nan"
                             and _canon_eq(x) in _mapa_repr]

            if votos_limpios:
                conteo = Counter(votos_limpios)
                favorito = conteo.most_common(1)[0]
                lobos = [pais for pais, votos in conteo.items() if votos == 1]
                
                st.write(f"❤️ **El Favorito:** {con_bandera(favorito[0])} (Elegido {favorito[1]} veces)")
                
                if lobos:
                    st.write(f"🐺 **Apuestas de 'Lobo Solitario':** {', '.join([con_bandera(l) for l in lobos[:3]])} (Solo 1 persona los eligió)")
            else:
                st.write("Esperando a que se introduzcan las selecciones de todos...")

        st.write("---")

        # ==========================================
        # 📊 GRÁFICO: EQUIPOS MÁS APOSTADOS
        # ==========================================
        # 🔬 DIAGNÓSTICO (solo visible para el admin Luis)
        if nombre_usuario.strip().lower() == "luis":
            with st.expander("🔬 Diagnóstico raw de votos (admin)"):
                st.caption("Valores exactos que llegan desde el Google Sheet para cada columna de equipo:")
                cols_equipos_diag = [c for c in df_usuarios.columns if 'equipo' in str(c).lower() and 'pts_' not in str(c).lower()]
                diag_rows = []
                for _, r in df_usuarios.iterrows():
                    for c in cols_equipos_diag:
                        val = str(r[c]).strip()
                        if val and val.lower() != "nan":
                            diag_rows.append({"Jugador": r[col_nombre], "Columna": c, "Valor_raw": val, "Canon": _canon_eq(val)})
                if diag_rows:
                    df_diag = pd.DataFrame(diag_rows)
                    st.write("**Conteo por forma canónica:**")
                    st.dataframe(df_diag.groupby("Canon")["Jugador"].apply(list).reset_index().rename(columns={"Jugador": "Personas"}), hide_index=True)
                    st.write("**Tabla completa raw:**")
                    st.dataframe(df_diag, hide_index=True)

        if votos_limpios:
            st.subheader("📊 Equipos más apostados por los chatarronianos")
            conteo_todos = Counter(votos_limpios)
            paises_ord = sorted(conteo_todos.items(), key=lambda x: x[1], reverse=True)
            nombres_eq = [con_bandera(p[0]) for p in paises_ord]
            votos_eq = [p[1] for p in paises_ord]

            fig_votos = go.Figure(go.Bar(
                x=nombres_eq,
                y=votos_eq,
                text=votos_eq,
                textposition='auto',
                marker_color='#FFA15A'
            ))
            fig_votos.update_layout(
                margin=dict(l=0, r=0, t=30, b=80),
                yaxis_title="Nº de jugadores que lo eligieron",
                xaxis=dict(showticklabels=True, tickangle=-45),
                showlegend=False
            )
            st.plotly_chart(fig_votos, width='stretch', theme=None, config={"displayModeBar": False})

            st.write("---")

        # ==========================================
        # 🏅 PUNTOS POR EQUIPO EN EL TORNEO REAL
        # ==========================================
        if not df_equipos.empty:
            try:
                col_pts_eq2 = [c for c in df_equipos.columns if 'punto' in str(c).lower()][0]
                col_nom_eq2 = df_equipos.columns[0]
                df_eq_graf = df_equipos[[col_nom_eq2, col_pts_eq2]].copy()
                df_eq_graf[col_pts_eq2] = pd.to_numeric(df_eq_graf[col_pts_eq2], errors='coerce').fillna(0)
                df_eq_graf = df_eq_graf.sort_values(by=col_pts_eq2, ascending=False).reset_index(drop=True)

                st.subheader("🏅 Puntos por Equipo en el Torneo Real")

                # Colores alternos: verde y azul claro
                colores_equipos = ['#00CC96' if i % 2 == 0 else '#19D3F3' for i in range(len(df_eq_graf))]

                num_equipos = len(df_eq_graf)
                ancho_grafico = max(800, num_equipos * 60)  # Mínimo 800px, 60px por equipo

                fig_equipos = go.Figure(go.Bar(
                    x=df_eq_graf[col_nom_eq2].tolist(),
                    y=df_eq_graf[col_pts_eq2].tolist(),
                    text=df_eq_graf[col_pts_eq2].tolist(),
                    textposition='auto',
                    marker_color=colores_equipos
                ))
                fig_equipos.update_layout(
                    width=ancho_grafico,
                    margin=dict(l=0, r=0, t=30, b=100),
                    yaxis_title="Puntos en el torneo",
                    xaxis=dict(showticklabels=True, tickangle=-45),
                    showlegend=False
                )
                st.plotly_chart(fig_equipos, width='content', theme=None, config={"displayModeBar": False})
                st.write("---")
            except Exception:
                pass

        st.subheader("📈 Análisis de Clasificación y Evolución")
        
        col_graf1, col_graf2 = st.columns(2)
        
        with col_graf1:
            st.markdown("#### 🏆 Clasificación Actual")
            nombres = df_ranking[col_nombre].tolist()
            puntos = df_ranking[col_puntos].tolist()
            
            colores_base = ['#636EFA', '#EF553B', '#00CC96', '#AB63FA', '#FFA15A', '#19D3F3', '#FF6692', '#B6E880', '#FF97FF', '#FECB52']
            
            # Construimos las trazas: una por cada barra para poder mezclar colores especiales
            traces = []
            for i, (n, p) in enumerate(zip(nombres, puntos)):
                n_limpio = limpiar_nombre(n)
                if n_limpio in ('saul', 'jc'):
                    # Dos trazas superpuestas: fondo rojo + rayas amarillas
                    traces.append(go.Bar(
                        x=[n], y=[p],
                        text=[p], textposition='auto',
                        marker=dict(color='#CC0000'),
                        showlegend=False, name=n
                    ))
                    traces.append(go.Bar(
                        x=[n], y=[p],
                        marker=dict(
                            color='rgba(0,0,0,0)',
                            pattern=dict(shape='|', fgcolor='#FFCE00', size=8, solidity=0.5)
                        ),
                        showlegend=False, name=n + "_rayas"
                    ))
                else:
                    traces.append(go.Bar(
                        x=[n], y=[p],
                        text=[p], textposition='auto',
                        marker=dict(color=colores_base[i % len(colores_base)]),
                        showlegend=False, name=n
                    ))

            fig1 = go.Figure(data=traces)
            fig1.update_layout(barmode='overlay')
            
            fig1.update_layout(
                margin=dict(l=0, r=0, t=30, b=50), 
                yaxis_title="Puntos Totales", 
                xaxis=dict(showticklabels=True, tickangle=-45),
                showlegend=False
            )
            st.plotly_chart(fig1, width='stretch', theme=None, config={"displayModeBar": False})

        with col_graf2:
            st.markdown("#### ⏪ Posiciones de la Semana Pasada")
            df_prev = df_usuarios[df_usuarios["Posicion_anterior"] > 0].sort_values(by="Posicion_anterior")
            
            if not df_prev.empty:
                nombres_prev = df_prev[col_nombre].tolist()
                posiciones = df_prev["Posicion_anterior"].tolist()
                
                max_pos = len(df_prev)
                alturas_visuales = [(max_pos - p + 1) for p in posiciones]
                
                fig2 = go.Figure(data=[go.Bar(
                    x=nombres_prev,
                    y=alturas_visuales,
                    text=[f"{p}º" for p in posiciones], 
                    textposition='auto',
                    marker_color='#8C92AC' 
                )])
                
                fig2.update_layout(
                    margin=dict(l=0, r=0, t=30, b=50), 
                    yaxis=dict(showticklabels=False), 
                    xaxis=dict(showticklabels=True, tickangle=-45),
                    showlegend=False
                )
                st.plotly_chart(fig2, width='stretch', theme=None, config={"displayModeBar": False})
            else:
                st.info("Aún no hay datos de la jornada pasada en tu columna 'Posicion_anterior'.")

    # ==========================================
    # PESTAÑA 2: CUARTEL GENERAL DEL USUARIO
    # ==========================================
    with tab2:
        st.header(f"🛡️ Cuartel General de {fila_user[col_nombre]}")
        
        df_ranking_temp = df_usuarios.sort_values(by=col_puntos, ascending=False).reset_index(drop=True)
        posicion_actual = df_ranking_temp[df_ranking_temp[col_nombre] == nombre_usuario].index[0] + 1
        posicion_anterior = int(fila_user["Posicion_anterior"]) if fila_user["Posicion_anterior"] != 0 else posicion_actual
        diferencia_posicion = posicion_anterior - posicion_actual

        col_res1, col_res2 = st.columns(2)
        col_res1.metric(label="🏆 Tu Posición Actual", value=f"{posicion_actual}º", delta=f"{diferencia_posicion} puestos respecto a la semana pasada", delta_color="normal")
        col_res2.metric(label="⭐ Puntos Totales", value=f"{fila_user[col_puntos]} pts")
        
        st.write("---")
        st.subheader("📌 Desglose de Puntos por Equipo")
        
        pares_equipos = [
            ("G1_Equipo1", "Pts_G1_Equipo1"), ("G1_Equipo2", "Pts_G1_Equipo2"), ("G1_Equipo3", "Pts_G1_Equip03"),
            ("G2_Equipo1", "Pts_G2_Equipo1"), ("G2_Equipo2", "Pts_G2_Equipo2"), ("G2_Equipo3", "Pts_G2_Equipo3"), ("G2_Equipo4", "Pts_G2_Equipo4"), ("G2_Equipo5", "Pts_G2_Equipo5"),
            ("G3_Equipo1", "Pts_G3_Equipo1"), ("G3_Equipo2", "Pts_G3_Equipo2"), ("G3_Equipo3", "Pts_G3_Equipo3"), ("G3_Equipo4", "Pts_G3_Equipo4"), ("G3_Equipo5", "Pts_G3_Equipo5"),
            ("G4_Equipo1", "Pts_G4_Equipo1"), ("G4_Equipo2", "Pts_G4_Equipo2"), ("G4_Equipo3", "Pts_G4_Equipo3"), ("G4_Equipo4", "Pts_G4_Equipo4"), ("G4_Equipo5", "Pts_G4_Equipo5"),
            ("GA_Equipo1", "Pts_GA_Equipo")
        ]
        
        nombres_grafico = []
        puntos_grafico = []

        st.markdown("### 🟨 Grupo 1")
        c1, c2, c3 = st.columns(3)
        c1.metric(label=con_bandera(fila_user.get("G1_Equipo1", "")), value=f"{fila_user.get('Pts_G1_Equipo1', 0)} pts")
        c2.metric(label=con_bandera(fila_user.get("G1_Equipo2", "")), value=f"{fila_user.get('Pts_G1_Equipo2', 0)} pts")
        c3.metric(label=con_bandera(fila_user.get("G1_Equipo3", "")), value=f"{fila_user.get('Pts_G1_Equip03', 0)} pts")
        
        st.markdown("### 🟩 Grupo 2")
        c4, c5, c6, c7, c8 = st.columns(5)
        c4.metric(label=con_bandera(fila_user.get("G2_Equipo1", "")), value=f"{fila_user.get('Pts_G2_Equipo1', 0)} pts")
        c5.metric(label=con_bandera(fila_user.get("G2_Equipo2", "")), value=f"{fila_user.get('Pts_G2_Equipo2', 0)} pts")
        c6.metric(label=con_bandera(fila_user.get("G2_Equipo3", "")), value=f"{fila_user.get('Pts_G2_Equipo3', 0)} pts")
        c7.metric(label=con_bandera(fila_user.get("G2_Equipo4", "")), value=f"{fila_user.get('Pts_G2_Equipo4', 0)} pts")
        c8.metric(label=con_bandera(fila_user.get("G2_Equipo5", "")), value=f"{fila_user.get('Pts_G2_Equipo5', 0)} pts")

        st.markdown("### 🟦 Grupo 3")
        c9, c10, c11, c12, c13 = st.columns(5)
        c9.metric(label=con_bandera(fila_user.get("G3_Equipo1", "")), value=f"{fila_user.get('Pts_G3_Equipo1', 0)} pts")
        c10.metric(label=con_bandera(fila_user.get("G3_Equipo2", "")), value=f"{fila_user.get('Pts_G3_Equipo2', 0)} pts")
        c11.metric(label=con_bandera(fila_user.get("G3_Equipo3", "")), value=f"{fila_user.get('Pts_G3_Equipo3', 0)} pts")
        c12.metric(label=con_bandera(fila_user.get("G3_Equipo4", "")), value=f"{fila_user.get('Pts_G3_Equipo4', 0)} pts")
        c13.metric(label=con_bandera(fila_user.get("G3_Equipo5", "")), value=f"{fila_user.get('Pts_G3_Equipo5', 0)} pts")

        st.markdown("### 🟧 Grupo 4")
        c14, c15, c16, c17, c18 = st.columns(5)
        c14.metric(label=con_bandera(fila_user.get("G4_Equipo1", "")), value=f"{fila_user.get('Pts_G4_Equipo1', 0)} pts")
        c15.metric(label=con_bandera(fila_user.get("G4_Equipo2", "")), value=f"{fila_user.get('Pts_G4_Equipo2', 0)} pts")
        c16.metric(label=con_bandera(fila_user.get("G4_Equipo3", "")), value=f"{fila_user.get('Pts_G4_Equipo3', 0)} pts")
        c17.metric(label=con_bandera(fila_user.get("G4_Equipo4", "")), value=f"{fila_user.get('Pts_G4_Equipo4', 0)} pts")
        c18.metric(label=con_bandera(fila_user.get("G4_Equipo5", "")), value=f"{fila_user.get('Pts_G4_Equipo5', 0)} pts")

        st.markdown("### 🅰️ Grupo A")
        st.metric(label=con_bandera(fila_user.get("GA_Equipo1", "")), value=f"{fila_user.get('Pts_GA_Equipo', 0)} pts")

        st.write("---")
        
        st.subheader("📈 ¿Qué equipo te está dando más puntos?")
        
        for col_eq, col_pt in pares_equipos:
            eq_name = str(fila_user.get(col_eq, "")).strip()
            if eq_name and eq_name.lower() != "nan":
                nombres_grafico.append(con_bandera(eq_name))
                puntos_grafico.append(int(fila_user.get(col_pt, 0)))
                
        if nombres_grafico:
            df_mis_equipos = pd.DataFrame({"Equipo": nombres_grafico, "Puntos": puntos_grafico})
            df_mis_equipos = df_mis_equipos.sort_values(by="Puntos", ascending=True)
            
            fig_rendimiento = go.Figure(go.Bar(
                x=df_mis_equipos["Puntos"],
                y=df_mis_equipos["Equipo"],
                orientation='h',
                text=df_mis_equipos["Puntos"],
                textposition='auto',
                marker_color='#19D3F3' 
            ))
            fig_rendimiento.update_layout(margin=dict(l=0, r=0, t=10, b=0), xaxis_title="Puntos Aportados", height=max(300, len(nombres_grafico)*30))
            st.plotly_chart(fig_rendimiento, width='stretch', theme=None, config={"displayModeBar": False})

        st.write("---")
        st.subheader("📅 Partidos de mis Equipos por Fase")

        if 'Fase ' in df_calendario.columns and 'Estado' in df_calendario.columns and 'Equipo_1' in df_calendario.columns:
            # Detectar columna de fecha (auto-detección)
            _col_fecha_u = next((c for c in df_calendario.columns if 'fecha' in str(c).lower() or ('date' in str(c).lower() and 'update' not in str(c).lower())), None)

            # Equipos del usuario: columnas que empiezan por G y no son de puntos
            cols_g_user = [c for c in df_usuarios.columns if str(c).startswith('G') and 'pts_' not in str(c).lower()]
            equipos_user = [str(fila_user.get(c, "")).strip() for c in cols_g_user]
            equipos_user = [e for e in equipos_user if e and e.lower() != "nan"]

            if equipos_user:
                df_mis_partidos = df_calendario[
                    df_calendario['Equipo_1'].isin(equipos_user) |
                    df_calendario['Equipo_2'].isin(equipos_user)
                ].copy()

                if not df_mis_partidos.empty:
                    # Orden manual de fases
                    _orden_fases_u2 = ['Grupos', 'Dieciseis', 'Octavos', 'Cuartos', 'Semifinal', '3 y 4', 'Final']
                    _fases_disp_u2 = set(df_mis_partidos['Fase '].dropna().unique())
                    _fases_extra_u2 = sorted([f for f in _fases_disp_u2 if f not in _orden_fases_u2])
                    fases_user = [f for f in _orden_fases_u2 if f in _fases_disp_u2] + _fases_extra_u2

                    for _fase_u in fases_user:
                        df_f_u = df_mis_partidos[df_mis_partidos['Fase '] == _fase_u]
                        if df_f_u.empty:
                            continue
                        _jug_u = int((df_f_u['Estado'] == 'Jugado').sum())
                        _pend_u = int((df_f_u['Estado'] == 'Pendiente').sum())

                        with st.container(border=True):
                            st.markdown(f"#### 👤 Fase: {_fase_u} {_icono_fase(_fase_u)}")
                            _cu1, _cu2 = st.columns(2)
                            _cu1.metric("Jugados ⚽", _jug_u)
                            _cu2.metric("Pendientes ⏳", _pend_u)

                            # ── Partidos JUGADOS ──
                            _df_jug_u = df_f_u[df_f_u['Estado'] == 'Jugado']
                            if not _df_jug_u.empty:
                                st.markdown("**⚽ Jugados:**")
                                for _, _rp in _df_jug_u.iterrows():
                                    _e1 = str(_rp.get('Equipo_1', '')).strip()
                                    _e2 = str(_rp.get('Equipo_2', '')).strip()
                                    _g1 = _rp.get('Goles_1', '')
                                    _g2 = _rp.get('Goles_2', '')
                                    # Negrita al equipo del usuario
                                    _e1f = f"**{_e1}**" if _e1 in equipos_user else _e1
                                    _e2f = f"**{_e2}**" if _e2 in equipos_user else _e2
                                    _fstr = ""
                                    if _col_fecha_u:
                                        try:
                                            _fraw = str(_rp[_col_fecha_u]).strip()
                                            if _fraw and _fraw.lower() != 'nan':
                                                _fstr = f" · 📅 {pd.to_datetime(_fraw, dayfirst=True).strftime('%d/%m/%Y')}"
                                        except Exception:
                                            _fstr = f" · 📅 {_fraw}"
                                    st.markdown(f"&nbsp;&nbsp;⚽ {_e1f} **{_g1}** - **{_g2}** {_e2f}{_fstr}")

                            # ── Partidos PENDIENTES ──
                            _df_pend_u = df_f_u[df_f_u['Estado'] == 'Pendiente']
                            if not _df_pend_u.empty:
                                st.markdown("**⏳ Pendientes:**")
                                for _, _rp in _df_pend_u.iterrows():
                                    _e1 = str(_rp.get('Equipo_1', '')).strip()
                                    _e2 = str(_rp.get('Equipo_2', '')).strip()
                                    _e1f = f"**{_e1}**" if _e1 in equipos_user else _e1
                                    _e2f = f"**{_e2}**" if _e2 in equipos_user else _e2
                                    _fstr = ""
                                    if _col_fecha_u:
                                        try:
                                            _fraw = str(_rp[_col_fecha_u]).strip()
                                            if _fraw and _fraw.lower() != 'nan':
                                                _fstr = f" · 📅 {pd.to_datetime(_fraw, dayfirst=True).strftime('%d/%m/%Y')}"
                                        except Exception:
                                            _fstr = f" · 📅 {_fraw}"
                                    st.markdown(f"&nbsp;&nbsp;⏳ {_e1f} vs {_e2f}{_fstr}")
                else:
                    st.info("No se encontraron partidos de tus equipos en el calendario.")
            else:
                st.info("No tienes equipos asignados para buscar en el calendario.")
        else:
            st.warning(f"⚠️ Columnas necesarias no encontradas en el calendario: {list(df_calendario.columns)}")

        st.caption("🔒 Tus apuestas están bloqueadas y son gestionadas por la administración del torneo.")

    # ==========================================
    # PESTAÑA 3: CALENDARIO
    # ==========================================
    with tab3:
        st.header("📅 Estado de los Partidos del Mundial")
        columnas_calendario = ["Grupo", "Equipo_1", "Goles_1", "Equipo_2", "Goles_2", "Estado", "Ganador"]
        cols_disponibles = [c for c in columnas_calendario if c in df_calendario.columns]
        st.dataframe(df_calendario[cols_disponibles], width='stretch')

    # ==========================================
    # PESTAÑA 4: PRONÓSTICO DINÁMICO
    # Usa columna AE Puntos_por_Ganar = (F*4) + I - J
    # Multiplicador Lobo Solitario leído de Llaves J2
    # ==========================================
    def mostrar_pronostico_dinamico(df_usuarios, df_equipos, df_llaves):
        st.header("🔮 Comparativa: Real vs. Pronóstico")

        # Leer multiplicador de Lobo Solitario desde la hoja llaves, celda J2
        # La hoja se carga con header=None → índices exactos del sheet:
        # Fila 1 = iloc[0], Fila 2 = iloc[1]
        # Columna J = índice 9 (A=0, B=1, C=2, D=3, E=4, F=5, G=6, H=7, I=8, J=9)
        multiplicador_lobo = 1.5
        if not df_llaves.empty:
            try:
                val = df_llaves.iloc[1, 9]   # Fila 2, Columna J → celda J2
                multiplicador_lobo = float(val)
            except Exception:
                multiplicador_lobo = 1.5

        col_info1, col_info2 = st.columns(2)
        col_info1.info(f"🐺 Multiplicador 'Lobo Solitario': **x{multiplicador_lobo}**")
        col_info2.caption("Fórmula: Puntos_por_Ganar = (Partidos ganados × 4) + Goles a favor − Goles en contra")

        # Verificar que la columna existe
        if df_equipos.empty or 'Puntos_por_Ganar' not in df_equipos.columns:
            st.warning("⚠️ No se encontró la columna 'Puntos_por_Ganar' en la hoja equipos.")
            st.write("Columnas disponibles:", list(df_equipos.columns) if not df_equipos.empty else "Sin datos")
            return

        # Columnas de equipos seleccionados por participantes (case-insensitive)
        cols_equipos = [c for c in df_usuarios.columns if 'equipo' in str(c).lower() and 'pts_' not in str(c).lower()]

        # Función de normalización (igual que en el Radar Chatarroniano)
        def _canon_eq_p4(x):
            s = str(x).strip()
            s = ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
            s = ' '.join(s.split())
            return s.lower()

        # Conteo de votos por equipo con normalización (para detectar lobos solitarios)
        todos_los_votos = df_usuarios[cols_equipos].values.flatten()
        # Mapa canónico → nombre representativo
        _mapa_p4 = {}
        for _v in todos_los_votos:
            _orig = str(_v).strip()
            if _orig == "" or _orig.lower() == "nan":
                continue
            _k = _canon_eq_p4(_orig)
            if _k and _k != "nan" and _k not in _mapa_p4:
                _mapa_p4[_k] = _orig

        votos_normalizados = [_mapa_p4[_canon_eq_p4(x)]
                              for x in todos_los_votos
                              if str(x).strip() != "" and str(x).strip().lower() != "nan"
                              and _canon_eq_p4(x) in _mapa_p4]
        conteo_votos = pd.Series(votos_normalizados).value_counts()

        # Detectar lobos solitarios (elegidos por 1 sola persona)
        lobos_solitarios = set(conteo_votos[conteo_votos == 1].index)

        nombres_list, puntos_reales_list, puntos_proy_list, bonus_list, equipos_detalle_list = [], [], [], [], []

        for _, row in df_usuarios.iterrows():
            nombre = row[col_nombre]
            pts_real = float(row[col_puntos])
            proy = pts_real
            bonus_total = 0.0
            detalle_equipos = []

            for col in cols_equipos:
                eq = str(row[col]).strip()
                if not eq or eq.lower() == 'nan':
                    continue
                match = df_equipos[df_equipos.iloc[:, 0].astype(str).str.strip() == eq]
                if not match.empty:
                    pts_eq = pd.to_numeric(match['Puntos_por_Ganar'].values[0], errors='coerce')
                    if pd.isna(pts_eq):
                        pts_eq = 0.0
                    pts_eq = float(pts_eq)
                    es_lobo = eq in lobos_solitarios
                    if es_lobo:
                        pts_con_bonus = pts_eq * multiplicador_lobo
                        bonus_total += pts_con_bonus - pts_eq
                        detalle_equipos.append(f"🐺{eq}({pts_con_bonus:.1f})")
                    else:
                        pts_con_bonus = pts_eq
                        detalle_equipos.append(f"{eq}({pts_eq:.1f})")
                    proy += pts_con_bonus

            nombres_list.append(nombre)
            puntos_reales_list.append(pts_real)
            puntos_proy_list.append(round(proy, 1))
            bonus_list.append(round(bonus_total, 1))
            equipos_detalle_list.append(", ".join(detalle_equipos) if detalle_equipos else "—")

        # Construir DataFrame de resultados ordenado por proyección
        df_pron = pd.DataFrame({
            "Jugador": nombres_list,
            "Pts Reales": [int(p) for p in puntos_reales_list],
            "Pts Proyectados": puntos_proy_list,
            "Bonus Lobo 🐺": bonus_list,
            "Equipos (pts)": equipos_detalle_list
        }).sort_values(by="Pts Proyectados", ascending=False).reset_index(drop=True)

        def icono_pos(i, total):
            if i == 0: return "🥇"
            if i == 1: return "🥈"
            if i == 2: return "🥉"
            if i >= total - 3: return "💩"
            return "😐"

        df_pron["🏅"] = [icono_pos(i, len(df_pron)) for i in range(len(df_pron))]
        df_pron.index = df_pron.index + 1

        # Tabla ranking proyectado
        st.subheader("📋 Ranking Proyectado")
        st.dataframe(
            df_pron[["🏅", "Jugador", "Pts Reales", "Pts Proyectados", "Bonus Lobo 🐺"]],
            width='stretch',
            hide_index=False,
        )

        st.write("---")

        # Gráfico agrupado: Reales vs Proyectados
        st.subheader("📊 Puntos Reales vs Proyectados")
        fig = go.Figure()
        fig.add_trace(go.Bar(
            name='Puntos Reales',
            x=df_pron["Jugador"].tolist(),
            y=df_pron["Pts Reales"].tolist(),
            marker_color='#636EFA',
            text=df_pron["Pts Reales"].tolist(),
            textposition='auto'
        ))
        fig.add_trace(go.Bar(
            name='Pronóstico (con bonus 🐺)',
            x=df_pron["Jugador"].tolist(),
            y=df_pron["Pts Proyectados"].tolist(),
            marker_color='#FFA15A',
            text=df_pron["Pts Proyectados"].tolist(),
            textposition='auto'
        ))
        fig.update_layout(
            barmode='group',
            margin=dict(l=0, r=0, t=30, b=80),
            xaxis=dict(tickangle=-45),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig, width='stretch', theme=None, config={"displayModeBar": False})

        # Equipos Lobo Solitario (elegidos solo por 1 persona)
        if lobos_solitarios:
            st.write("---")
            st.subheader("🐺 Equipos 'Lobo Solitario' (elegidos por 1 sola persona)")
            st.info(f"Estos equipos aplican el multiplicador **x{multiplicador_lobo}** a los Puntos_por_Ganar")
            lobos_info = []
            for eq in sorted(lobos_solitarios):
                match = df_equipos[df_equipos.iloc[:, 0].astype(str).str.strip() == eq]
                if not match.empty:
                    pts = pd.to_numeric(match['Puntos_por_Ganar'].values[0], errors='coerce')
                    pts = float(pts) if not pd.isna(pts) else 0.0
                    quien = df_usuarios[df_usuarios[cols_equipos].apply(
                        lambda r: eq in r.astype(str).str.strip().values, axis=1
                    )][col_nombre].values
                    lobos_info.append({
                        "Equipo": eq,
                        "Puntos_por_Ganar": pts,
                        "Con bonus": round(pts * multiplicador_lobo, 1),
                        "Elegido por": quien[0] if len(quien) > 0 else "—"
                    })
            if lobos_info:
                st.dataframe(pd.DataFrame(lobos_info), width='stretch', hide_index=True)

    with tab4:
        mostrar_pronostico_dinamico(df_usuarios, df_equipos, df_llaves)
