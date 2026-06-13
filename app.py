import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import flag
from collections import Counter
import plotly.graph_objects as go
import unicodedata

st.set_page_config(page_title="Mundial 2026 chatarronianos", layout="wide")

st.title("🏆 Mundial 2026 chatarronianos")

# 🔗 CONEXIÓN CON GOOGLE SHEETS
try:
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    credenciales = Credentials.from_service_account_file("creds.json", scopes=scope)
    cliente = gspread.authorize(credenciales)
    
    id_excel = "1NncO0BuIR8BeYNz8a-VIUODFRx6rdDRwa0xZJQypG44"
    doc = cliente.open_by_key(id_excel)
    
    hoja_user = doc.worksheet("Participantes ")
    df_usuarios = pd.DataFrame(hoja_user.get_all_records())
    df_calendario = pd.DataFrame(doc.worksheet("calendario").get_all_records())
    
    try:
        df_equipos = pd.DataFrame(doc.worksheet("equipos").get_all_records())
    except:
        df_equipos = pd.DataFrame()
    
except Exception as e:
    st.error(f"🚨 Error de conexión con Google Sheets: {e}")
    st.stop()

col_nombre = "Nombre "
col_puntos = "Puntos_totales." 

df_usuarios[col_puntos] = pd.to_numeric(df_usuarios[col_puntos], errors='coerce').fillna(0).astype(int)

if "Posicion_anterior" not in df_usuarios.columns:
    df_usuarios["Posicion_anterior"] = 0
df_usuarios["Posicion_anterior"] = pd.to_numeric(df_usuarios["Posicion_anterior"], errors='coerce').fillna(0).astype(int)

def limpiar_nombre(texto):
    """Quita tildes y mayúsculas para asegurar que reconoce a Saul y Palpatin"""
    texto = str(texto).strip().lower()
    texto = ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
    return texto

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

    tab1, tab2, tab3 = st.tabs(["👑 Dashboard General", "🛡️ Mi Ficha Privada", "📅 Calendario y Resultados"])

    # ==========================================
    # PESTAÑA 1: EL SÚPER DASHBOARD
    # ==========================================
    with tab1:
        st.header("👑 El Salón de la Fama")
        df_ranking = df_usuarios[[col_nombre, col_puntos]].sort_values(by=col_puntos, ascending=False).reset_index(drop=True)
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
        
        col_stats1, col_stats2 = st.columns(2)
        
        with col_stats1:
            st.header("🌟 El Equipo MVP")
            st.info("El país que más puntos está sumando en el torneo real.")
            if not df_equipos.empty:
                try:
                    col_pts_eq = [c for c in df_equipos.columns if 'punto' in str(c).lower()][0]
                    col_nom_eq = df_equipos.columns[0] 
                    df_eq_sort = df_equipos.sort_values(by=col_pts_eq, ascending=False).reset_index(drop=True)
                    mejor_equipo = df_eq_sort.loc[0, col_nom_eq]
                    pts_mejor = df_eq_sort.loc[0, col_pts_eq]
                    st.success(f"### {con_bandera(mejor_equipo)} con {pts_mejor} puntos")
                except:
                    st.warning("Datos del MVP calculándose...")
            else:
                st.warning("Datos del MVP no disponibles.")

        with col_stats2:
            st.header("🎯 Radar Chatarroniano")
            cols_equipos = [c for c in df_usuarios.columns if 'Equipo' in c and 'Pts_' not in c]
            todos_los_votos = df_usuarios[cols_equipos].values.flatten()
            votos_limpios = [str(x).strip() for x in todos_los_votos if str(x).strip() != "" and str(x).lower() != "nan"]
            
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
        st.subheader("📈 Análisis de Clasificación y Evolución")
        
        col_graf1, col_graf2 = st.columns(2)
        
        with col_graf1:
            st.markdown("#### 🏆 Clasificación Actual")
            nombres = df_ranking[col_nombre].tolist()
            puntos = df_ranking[col_puntos].tolist()
            
            colores_base = ['#636EFA', '#EF553B', '#00CC96', '#AB63FA', '#FFA15A', '#19D3F3', '#FF6692', '#B6E880', '#FF97FF', '#FECB52']
            colores_barras = []
            patrones = []
            colores_patron = []
            
            for i, n in enumerate(nombres):
                n_limpio = limpiar_nombre(n) 
                
                if n_limpio == 'saul' or n_limpio == 'palpatin':
                    colores_barras.append('#FFCE00') # Fondo amarillo
                    patrones.append('|')             # 🔴🟡 Rayas VERTICALES ('|')
                    colores_patron.append('#CC0000') # Color rojo para las rayas
                else:
                    colores_barras.append(colores_base[i % len(colores_base)])
                    patrones.append('')              
                    colores_patron.append('#FFFFFF') 
                    
            fig1 = go.Figure(data=[go.Bar(
                x=nombres,
                y=puntos,
                text=puntos,
                textposition='auto',
                marker=dict(
                    color=colores_barras,
                    pattern=dict(shape=patrones, fgcolor=colores_patron)
                )
            )])
            
            # Forzamos a que salgan los nombres debajo inclinados y dejamos margen
            fig1.update_layout(
                margin=dict(l=0, r=0, t=30, b=50), 
                yaxis_title="Puntos Totales", 
                xaxis=dict(showticklabels=True, tickangle=-45), # ¡NOMBRES DEBAJO DE LAS BARRAS!
                showlegend=False
            )
            st.plotly_chart(fig1, use_container_width=True, theme=None)

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
                    xaxis=dict(showticklabels=True, tickangle=-45), # NOMBRES DEBAJO AQUÍ TAMBIÉN
                    showlegend=False
                )
                st.plotly_chart(fig2, use_container_width=True, theme=None)
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
            st.plotly_chart(fig_rendimiento, use_container_width=True, theme=None)

        st.caption("🔒 Tus apuestas están bloqueadas y son gestionadas por la administración del torneo.")

    # ==========================================
    # PESTAÑA 3: CALENDARIO
    # ==========================================
    with tab3:
        st.header("📅 Estado de los Partidos del Mundial")
        st.dataframe(df_calendario, use_container_width=True)