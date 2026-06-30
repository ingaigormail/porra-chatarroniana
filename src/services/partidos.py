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

    def revertir_resultado(self, partido_id, admin):
        """Vuelve un partido a Pendiente y deshace cuadro, apuestas y puntos."""
        try:
            partido_id = int(partido_id)
            resp = self.client.table('partidos').select('*').eq(
                'id', partido_id).execute()
            if not resp.data:
                return {'success': False, 'message': 'Partido no encontrado'}
            partido = resp.data[0]
            if partido.get('estado') != 'Jugado':
                return {
                    'success': False,
                    'message': 'El partido ya está pendiente',
                }

            from src.services.cruces import CrucesService, FASE_SIGUIENTE_ELIMINATORIA
            cruces_svc = CrucesService(self.client)
            rev = cruces_svc.revertir_avance_ganador(partido_id)
            ganador_id = rev.get('ganador_id')

            fase = partido.get('fase', '')
            fase_sig = FASE_SIGUIENTE_ELIMINATORIA.get(fase)
            prog_msg = ''
            if ganador_id and fase_sig:
                from src.services.progresion import ProgresionService
                prog = ProgresionService(self.client)
                r_prog = prog.eliminar_progresion_equipo_fase(
                    ganador_id, fase_sig)
                if r_prog.get('eliminados', 0) > 0:
                    prog_msg = (
                        f" Progresión {fase_sig} del ganador revertida "
                        f"({r_prog['eliminados']} registro(s)).")

            self.client.table('partidos').update({
                'goles_local': 0,
                'goles_visitante': 0,
                'estado': 'Pendiente',
                'hubo_prorroga': False,
                'ganador_prorroga': None,
            }).eq('id', partido_id).execute()

            from src.services.quiniela import QuinielaService
            quiniela_svc = QuinielaService(self.client)
            q_rev = quiniela_svc.resetear_puntos_partido(partido_id)

            partidos_df = self.obtener_partidos()
            from src.services.equipos import EquiposService
            EquiposService(self.client)._recalcular_puntos_equipos(partidos_df)

            self.client.table('auditoria').insert({
                'admin': admin,
                'accion': 'Revertir_resultado',
                'detalle': (
                    f"Partido {partido_id} revertido a Pendiente. "
                    f"Cuadro: {rev.get('slots', 0)} hueco(s). "
                    f"Apuestas: {q_rev.get('apuestas', 0)}.{prog_msg}"
                ),
            }).execute()

            return {
                'success': True,
                'message': (
                    f'Partido #{partido_id} vuelve a Pendiente. '
                    f'Apuestas reseteadas ({q_rev.get("apuestas", 0)}).'
                    f'{prog_msg}'
                ),
                'slots': rev.get('slots', 0),
                'apuestas': q_rev.get('apuestas', 0),
            }
        except Exception as e:
            return {'success': False, 'message': str(e)}

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

    def actualizar_estado_apuesta(
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

    def cerrar_apuestas_por_tipo(self, tipo_apuesta, fase=None):
        """Cierra partidos abiertos de quiniela o porra (opcionalmente solo una fase)."""
        try:
            if tipo_apuesta not in ('quiniela', 'porra'):
                return {
                    'success': False,
                    'message': 'Tipo inválido',
                    'cerrados': 0,
                }
            query = self.client.table('partidos').update({
                'apuestas_abiertas': False,
            }).eq('tipo_apuesta', tipo_apuesta).eq('apuestas_abiertas', True)
            if fase:
                query = query.eq('fase', fase)
            resp = query.execute()
            n = len(resp.data or [])
            donde = f' en {fase}' if fase else ''
            return {
                'success': True,
                'message': f'Cerrada la {tipo_apuesta}{donde}: {n} partido(s)',
                'cerrados': n,
            }
        except Exception as e:
            return {'success': False, 'message': str(e), 'cerrados': 0}
