# app.py
try:
    import truststore
    truststore.inject_into_ssl()
except ImportError:
    pass

import streamlit as st
import pandas as pd
import unicodedata

# Configuración de la página
st.set_page_config(
    page_title="🏆 Mundial 2026 Chatarronianos",
    page_icon="⚽",
    layout="wide"
)

# Importar módulos
from src.database import Database
from src.ui import clasificacion, mi_ficha, calendario
from src.ui.admin import es_admin_luis, mostrar_operaciones, mostrar_extra
from src.ui.mundial_grupos import mostrar as mostrar_mundial

# Inicializar la base de datos
db = Database()

# Título
st.title("🏆 Mundial 2026 Chatarronianos")

# =============================================
# IDENTIFICACIÓN DEL USUARIO (con contraseña)
# =============================================
st.sidebar.header("🔑 Identificación")

# Obtener lista de usuarios
usuarios = db.obtener_usuarios()
lista_usuarios = usuarios['nombre'].tolist() if not usuarios.empty else []

# Inicializar sesión
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False
    st.session_state.usuario_actual = None

# Si no está autenticado, mostrar login
if not st.session_state.autenticado:
    with st.sidebar:
        st.markdown("### 🔐 Iniciar sesión")
        
        usuario_seleccionado = st.selectbox(
            "Selecciona tu nombre:",
            options=[""] + lista_usuarios
        )
        
        contraseña = st.text_input(
            "Contraseña:",
            type="password",
            placeholder="Introduce tu contraseña"
        )
        
        if st.button("🔓 Entrar", type="primary", use_container_width="stretch"):
            if usuario_seleccionado and contraseña:
                nombre_normalizado = usuario_seleccionado.lower()
                nombre_normalizado = ''.join(c for c in unicodedata.normalize('NFD', nombre_normalizado) 
                                           if unicodedata.category(c) != 'Mn')
                
                if contraseña.lower() == nombre_normalizado:
                    st.session_state.autenticado = True
                    st.session_state.usuario_actual = usuario_seleccionado
                    st.success(f"✅ Bienvenido, {usuario_seleccionado}!")
                    st.rerun()
                else:
                    st.error("❌ Contraseña incorrecta")
            else:
                st.warning("⚠️ Selecciona un usuario y escribe tu contraseña")
    
    st.stop()

else:
    nombre_usuario = st.session_state.usuario_actual
    st.sidebar.success(f"✅ Conectado como: {nombre_usuario}")
    
    if st.sidebar.button("🚪 Cerrar sesión", use_container_width="stretch"):
        st.session_state.autenticado = False
        st.session_state.usuario_actual = None
        st.rerun()

# =============================================
# CARGAR DATOS CON CACHÉ
# =============================================
@st.cache_data(ttl=60)
def cargar_datos():
    return {
        'equipos': db.obtener_equipos(),
        'partidos': db.obtener_partidos(),
        'clasificacion': db.obtener_clasificacion(),
        'selecciones': db.obtener_selecciones()
    }


@st.cache_data(ttl=60)
def cargar_extras_clasificacion():
    return {
        'desglose': db.obtener_desglose_puntos(),
        'mvp': db.obtener_mvp(),
        'radar': db.obtener_radar(),
        'votos': db.obtener_equipos_mas_votados(),
        'puntos_equipos': db.obtener_puntos_equipos_reales(),
    }

datos = cargar_datos()

# =============================================
# PESTAÑAS (solo carga la sección activa)
# =============================================
_tab_labels = [
    "👤 Mi Ficha",
    "🏆 Clasificación",
    "🌍 Mundial",
    "📅 Calendario",
]
if es_admin_luis(nombre_usuario):
    _tab_labels.extend(["🔧 Admin", "🎛️ Admin Extra"])

opcion = st.radio(
    "Navegación",
    _tab_labels,
    horizontal=True,
    label_visibility="collapsed",
    key="nav_principal",
)

# =============================================
# CONTENIDO POR SECCIÓN
# =============================================
if opcion == "👤 Mi Ficha":
    mi_ficha.mostrar(
        nombre_usuario,
        usuarios,
        datos['clasificacion'],
        db
    )

elif opcion == "🏆 Clasificación":
    clasificacion.mostrar(
        datos['clasificacion'],
        datos['partidos'],
        db,
        extras=cargar_extras_clasificacion(),
    )

elif opcion == "🌍 Mundial":
    mostrar_mundial(db)

elif opcion == "📅 Calendario":
    calendario.mostrar(datos['partidos'])

elif opcion == "🔧 Admin" and es_admin_luis(nombre_usuario):
    mostrar_operaciones(nombre_usuario, datos['partidos'], db)

elif opcion == "🎛️ Admin Extra" and es_admin_luis(nombre_usuario):
    mostrar_extra(nombre_usuario, datos['partidos'], db)