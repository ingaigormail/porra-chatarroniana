# src/database.py
import streamlit as st
from supabase import create_client

# Importar servicios
from src.services.usuarios import UsuariosService
from src.services.equipos import EquiposService
from src.services.partidos import PartidosService
from src.services.clasificacion import ClasificacionService
from src.services.grupos import GruposService
from src.services.cruces import CrucesService
from src.services.historico import HistoricoService
from src.services.quiniela import QuinielaService
from src.services.configuracion import ConfiguracionService
from src.services.progresion import ProgresionService  # <-- NUEVO


class Database:
    def __init__(self):
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
        self.client = create_client(url, key)

        # Inicializar servicios
        self.usuarios = UsuariosService(self.client)
        self.equipos = EquiposService(self.client)
        self.partidos = PartidosService(self.client)
        self.clasificacion = ClasificacionService(self.client)
        self.grupos = GruposService(self.client)
        self.cruces = CrucesService(self.client)
        self.historico = HistoricoService(self.client)
        self.quiniela = QuinielaService(self.client)
        self.configuracion = ConfiguracionService(self.client)
        self.progresion = ProgresionService(self.client)  # <-- NUEVO

    # =============================================
    # MÉTODOS DE CONVENIENCIA
    # =============================================

    def obtener_usuarios(self):
        return self.usuarios.obtener_usuarios()

    def obtener_equipos(self):
        return self.equipos.obtener_equipos()

    def obtener_selecciones(self):
        return self.usuarios.obtener_selecciones()

    def obtener_partidos(self):
        return self.partidos.obtener_partidos()

    def actualizar_fechas_partidos(self, fechas):
        return self.partidos.actualizar_fechas(fechas)

    def obtener_clasificacion(self):
        return self.clasificacion.obtener_clasificacion()

    def obtener_mvp(self):
        return self.equipos.obtener_mvp()

    def obtener_radar(self):
        return self.equipos.obtener_radar()

    def obtener_equipos_mas_votados(self):
        return self.equipos.obtener_equipos_mas_votados()

    def obtener_puntos_equipos_reales(self):
        return self.equipos.obtener_puntos_equipos_reales()

    def obtener_datos_grafico_clasificacion(self):
        return self.clasificacion.obtener_datos_grafico_clasificacion()

    def guardar_snapshot(self):
        return self.historico.guardar_snapshot(self.clasificacion)

    def obtener_ultimo_snapshot(self):
        return self.historico.obtener_ultimo_snapshot()

    def obtener_movimientos(self):
        return self.historico.obtener_movimientos(self.clasificacion)

    def guardar_resultado(
            self,
            partido_id,
            goles_local,
            goles_visitante,
            admin,
            hubo_prorroga=False,
            ganador_prorroga=None):
        """
        Guarda el resultado de un partido, incluyendo prórroga.
        """
        resultado = self.partidos.guardar_resultado(
            partido_id,
            goles_local,
            goles_visitante,
            admin,
            hubo_prorroga,
            ganador_prorroga)
        if resultado:
            # Guardar snapshot automático (opcional)
            self.guardar_snapshot()
        return resultado

    def calcular_clasificacion_grupo(self, grupo):
        return self.grupos.calcular_clasificacion_grupo(grupo)

    def calcular_mejores_terceros(self):
        return self.cruces.calcular_mejores_terceros(self.grupos)

    def generar_cruces_dieciseisavos(self):
        return self.cruces.generar_cruces_dieciseisavos(self.grupos)

    def actualizar_cruces(self):
        return self.cruces.actualizar_cruces(self.grupos)

    # =============================================
    # QUINIELA
    # =============================================

    def apostar_partido(
            self,
            usuario_id,
            partido_id,
            tipo,
            eleccion_quiniela=None,
            goles_local=None,
            goles_visitante=None):
        return self.quiniela.guardar_apuesta(
            usuario_id,
            partido_id,
            tipo,
            eleccion_quiniela,
            goles_local,
            goles_visitante)

    def calcular_puntos_quiniela(self, partido_id):
        return self.quiniela.calcular_puntos_quiniela(partido_id)

    def obtener_apuestas_usuario(self, usuario_id, fase=None):
        return self.quiniela.obtener_apuestas_usuario(usuario_id, fase)

    def apostar_finalistas(self, usuario_id, finalista_1_id, finalista_2_id):
        return self.quiniela.apostar_finalistas(
            usuario_id, finalista_1_id, finalista_2_id)

    def calcular_puntos_finalistas(self, finalista_1_real, finalista_2_real):
        return self.quiniela.calcular_puntos_finalistas(
            finalista_1_real, finalista_2_real)

    # =============================================
    # GESTIÓN DE APUESTAS (ADMIN)
    # =============================================

    def obtener_partidos_abiertos_apuestas(self):
        return self.partidos.obtener_partidos_abiertos_apuestas()

    def actualizar_estado_apuesta(
            self,
            partido_id,
            tipo_apuesta,
            apuestas_abiertas):
        return self.partidos.actualizar_estado_apuesta(
            partido_id, tipo_apuesta, apuestas_abiertas)

    # =============================================
    # CONFIGURACIÓN (FINALISTAS, ETC.)
    # =============================================

    def obtener_configuracion(self, clave):
        return self.configuracion.obtener_valor(clave)

    def actualizar_configuracion(self, clave, valor):
        return self.configuracion.actualizar_valor(clave, valor)

    # =============================================
    # PROGRESIÓN (BONUS POR FASE)
    # =============================================

    def calcular_progresion(self, equipo_id, fase, puntos=None):
        return self.progresion.calcular_y_guardar_progresion(equipo_id, fase, puntos)

    def obtener_progresion_usuario(self, usuario_id):
        return self.progresion.obtener_progresion_usuario(usuario_id)

    def obtener_puntos_totales_progresion(self, usuario_id):
        return self.progresion.obtener_puntos_totales_progresion(usuario_id)
