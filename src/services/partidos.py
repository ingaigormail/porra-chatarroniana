# src/services/partidos.py
import pandas as pd
from utils.validators import validar_goles  # <-- Import correcto (desde raíz)


class PartidosService:
    def __init__(self, client):
        self.client = client

    def obtener_partidos(self):
        response = self.client.table('partidos').select('*').execute()
        df = pd.DataFrame(response.data)
        if df.empty:
            return df
        equipos_response = self.client.table(
            'equipos').select('id', 'nombre').execute()
        equipos_df = pd.DataFrame(equipos_response.data)
        equipos_dict = dict(zip(equipos_df['id'], equipos_df['nombre']))
        df['equipo_local_nombre'] = df['equipo_local_id'].map(equipos_dict)
        df['equipo_visitante_nombre'] = df['equipo_visitante_id'].map(
            equipos_dict)
        from utils.partidos_orden import ordenar_partidos
        return ordenar_partidos(df)

    def actualizar_fechas(self, fechas: dict) -> int:
        """Actualiza campo fecha por id de partido. fechas = {id: 'YYYY-MM-DD'}."""
        actualizados = 0
        for partido_id, fecha in fechas.items():
            if not fecha:
                continue
            self.client.table('partidos').update({
                'fecha': str(fecha)[:10],
            }).eq('id', int(partido_id)).execute()
            actualizados += 1
        return actualizados

    def guardar_resultado(
            self,
            partido_id,
            goles_local,
            goles_visitante,
            admin,
            hubo_prorroga=False,
            ganador_prorroga=None):
        try:
            # --- USANDO EL VALIDADOR CENTRALIZADO ---
            gl = validar_goles(goles_local)
            gv = validar_goles(goles_visitante)
            # --- FIN VALIDADOR ---

            self.client.table('partidos').update({
                'goles_local': gl,
                'goles_visitante': gv,
                'estado': 'Jugado',
                'hubo_prorroga': hubo_prorroga,
                'ganador_prorroga': ganador_prorroga
            }).eq('id', partido_id).execute()

            self.client.table('auditoria').insert({
                'admin': admin,
                'accion': 'Resultado_partido',
                'detalle': f"Partido {partido_id}: {gl}-{gv} (prórroga: {hubo_prorroga})"
            }).execute()

            partidos_df = self.obtener_partidos()
            from src.services.equipos import EquiposService
            equipos_service = EquiposService(self.client)
            equipos_service._recalcular_puntos_equipos(partidos_df)

            from src.services.quiniela import QuinielaService
            quiniela_service = QuinielaService(self.client)
            quiniela_service.calcular_puntos_partido(partido_id)

            from src.services.cruces import CrucesService
            cruces_svc = CrucesService(self.client)
            cruces_svc.avanzar_ganador(int(partido_id))

            # Auto-generar dieciseisavos al cerrar la fase de grupos
            partido_row = self.client.table('partidos').select('fase').eq(
                'id', partido_id).execute().data
            if partido_row and partido_row[0].get('fase') == 'Grupos':
                pend = self.client.table('partidos').select('id').eq(
                    'fase', 'Grupos').neq('estado', 'Jugado').execute().data
                if not pend:
                    from src.services.grupos import GruposService
                    cruces_svc.actualizar_cruces(GruposService(self.client))

            return True
        except Exception as e:
            print(f"Error en guardar_resultado: {e}")
            return False

    def obtener_partidos_abiertos_apuestas(self):
        response = self.client.table('partidos')\
            .select('*')\
            .eq('apuestas_abiertas', True)\
            .neq('tipo_apuesta', 'ninguno')\
            .execute()
        df = pd.DataFrame(response.data)
        if df.empty:
            return df
        equipos_response = self.client.table(
            'equipos').select('id', 'nombre').execute()
        equipos_dict = {eq['id']: eq['nombre'] for eq in equipos_response.data}
        df['equipo_local_nombre'] = df['equipo_local_id'].map(equipos_dict)
        df['equipo_visitante_nombre'] = df['equipo_visitante_id'].map(
            equipos_dict)
        from utils.partidos_orden import ordenar_partidos
        return ordenar_partidos(df)
            self,
            partido_id,
            tipo_apuesta,
            apuestas_abiertas):
        try:
            self.client.table('partidos').update({
                'tipo_apuesta': tipo_apuesta,
                'apuestas_abiertas': apuestas_abiertas
            }).eq('id', partido_id).execute()
            return {
                'success': True,
                'message': 'Estado de apuesta actualizado'}
        except Exception as e:
            return {'success': False, 'message': str(e)}
