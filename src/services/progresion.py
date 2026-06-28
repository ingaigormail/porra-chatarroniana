# src/services/progresion.py
import pandas as pd
from datetime import datetime


class ProgresionService:
    """Gestiona los puntos de progresión de equipos por avance de fase."""

    def __init__(self, client):
        self.client = client

    # Fases válidas (Dieciseisavos sin valor fijo: puntos manuales)
    FASES_VALIDAS = ['Dieciseisavos', 'Octavos', 'Cuartos', 'Semifinal', 'Final']

    PUNTOS_SUGERIDOS = {
        'Octavos': 10,
        'Cuartos': 15,
        'Semifinal': 20,
        'Final': 30,
    }

    def calcular_y_guardar_progresion(self, equipo_id, fase, puntos=None):
        """
        Guarda bonus de progresión para usuarios que seleccionaron el equipo.

        Args:
            equipo_id: ID del equipo
            fase: Fase alcanzada
            puntos: Puntos a sumar (obligatorio para Dieciseisavos; opcional en otras fases)
        """
        try:
            if fase not in self.FASES_VALIDAS:
                return {
                    'success': False,
                    'message': f'Fase inválida. Válidas: {", ".join(self.FASES_VALIDAS)}',
                    'usuarios_afectados': 0,
                }

            if puntos is None:
                if fase in self.PUNTOS_SUGERIDOS:
                    puntos_fase = self.PUNTOS_SUGERIDOS[fase]
                else:
                    return {
                        'success': False,
                        'message': 'Indica cuántos puntos sumar para Dieciseisavos.',
                        'usuarios_afectados': 0,
                    }
            else:
                puntos_fase = int(puntos)
                if puntos_fase <= 0:
                    return {
                        'success': False,
                        'message': 'Los puntos deben ser mayores que 0.',
                        'usuarios_afectados': 0,
                    }

            # 1. Obtener todos los usuarios que seleccionaron este equipo
            selecciones_response = self.client.table('selecciones')\
                .select('usuario_id')\
                .eq('equipo_id', equipo_id)\
                .execute()

            if not selecciones_response.data:
                return {
                    'success': True,
                    'message': f'No hay usuarios con este equipo',
                    'usuarios_afectados': 0
                }

            usuarios_ids = [sel['usuario_id']
                            for sel in selecciones_response.data]

            # 2. Para cada usuario, verificar que no tenga ya esta progresión
            # y luego guardar
            usuarios_nuevos = 0
            usuarios_duplicados = 0

            for usuario_id in usuarios_ids:
                # Verificar duplicado
                duplicado_check = self.client.table('progresion_equipos')\
                    .select('id')\
                    .eq('usuario_id', usuario_id)\
                    .eq('equipo_id', equipo_id)\
                    .eq('fase', fase)\
                    .execute()

                if duplicado_check.data:
                    # Ya existe, no duplicar
                    usuarios_duplicados += 1
                    continue

                # Insertar nueva progresión
                self.client.table('progresion_equipos').insert({
                    'usuario_id': usuario_id,
                    'equipo_id': equipo_id,
                    'fase': fase,
                    'puntos': puntos_fase,
                    'fecha': datetime.now().isoformat()
                }).execute()

                usuarios_nuevos += 1

            # Mensaje de resultado
            mensaje = f'✅ Bonus aplicado: {usuarios_nuevos} usuario(s) recibió(eron) +{puntos_fase} pts'
            if usuarios_duplicados > 0:
                mensaje += f' ({usuarios_duplicados} usuario(s) ya tenían este bonus)'

            return {
                'success': True,
                'message': mensaje,
                'usuarios_afectados': usuarios_nuevos
            }

        except Exception as e:
            return {
                'success': False,
                'message': f'Error al guardar progresión: {str(e)}'
            }

    def obtener_progresion_usuario(self, usuario_id):
        """
        Obtiene el histórico de progresión de un usuario.

        Args:
            usuario_id (int): ID del usuario

        Returns:
            pd.DataFrame: Con columnas [equipo_nombre, fase, puntos, fecha]
        """
        try:
            response = self.client.table('progresion_equipos')\
                .select('*, equipos(nombre)')\
                .eq('usuario_id', usuario_id)\
                .order('fecha', desc=True)\
                .execute()

            if not response.data:
                return pd.DataFrame()

            data = []
            for item in response.data:
                equipo_nombre = item['equipos']['nombre'] if item['equipos'] else 'Desconocido'
                data.append({
                    'equipo': equipo_nombre,
                    'fase': item['fase'],
                    'puntos': item['puntos'],
                    'fecha': item['fecha']
                })

            return pd.DataFrame(data)

        except Exception as e:
            print(f"Error al obtener progresión de usuario: {e}")
            return pd.DataFrame()

    def obtener_puntos_totales_progresion(self, usuario_id):
        """
        Obtiene la suma total de puntos de progresión de un usuario.

        Args:
            usuario_id (int): ID del usuario

        Returns:
            int: Puntos totales de progresión
        """
        try:
            response = self.client.table('progresion_equipos')\
                .select('puntos')\
                .eq('usuario_id', usuario_id)\
                .execute()

            if not response.data:
                return 0

            return sum([item['puntos'] for item in response.data])

        except Exception as e:
            print(f"Error al obtener puntos de progresión: {e}")
            return 0

    def obtener_usuarios_con_equipo(self, equipo_id):
        """
        Obtiene los usuarios que seleccionaron un equipo específico.

        Args:
            equipo_id (int): ID del equipo

        Returns:
            pd.DataFrame: Con columnas [usuario_id, usuario_nombre]
        """
        try:
            response = self.client.table('selecciones')\
                .select('usuario_id, usuarios(nombre)')\
                .eq('equipo_id', equipo_id)\
                .execute()

            if not response.data:
                return pd.DataFrame()

            data = []
            for item in response.data:
                usuario_nombre = item['usuarios']['nombre'] if item['usuarios'] else 'Desconocido'
                data.append({
                    'usuario_id': item['usuario_id'],
                    'usuario_nombre': usuario_nombre
                })

            return pd.DataFrame(data)

        except Exception as e:
            print(f"Error al obtener usuarios con equipo: {e}")
            return pd.DataFrame()

    def obtener_resumen_aplicado(self, fase=None):
        """
        Resumen de bonus ya otorgados, agrupado por equipo y fase.

        Returns:
            pd.DataFrame: equipo, fase, puntos, usuarios, fecha
        """
        try:
            query = self.client.table('progresion_equipos').select(
                'equipo_id, fase, puntos, usuario_id, fecha, equipos(nombre)'
            )
            if fase:
                query = query.eq('fase', fase)
            response = query.execute()
            if not response.data:
                return pd.DataFrame()

            filas = []
            for item in response.data:
                eq = item.get('equipos') or {}
                filas.append({
                    'equipo_id': item['equipo_id'],
                    'equipo': eq.get('nombre', 'Desconocido'),
                    'fase': item['fase'],
                    'puntos': int(item.get('puntos') or 0),
                    'usuario_id': item['usuario_id'],
                    'fecha': item.get('fecha', ''),
                })

            df = pd.DataFrame(filas)
            resumen = df.groupby(
                ['equipo_id', 'equipo', 'fase', 'puntos'], as_index=False
            ).agg(
                usuarios=('usuario_id', 'nunique'),
                fecha=('fecha', 'max'),
            )
            from utils.partidos_orden import indice_fase
            resumen['_ord'] = resumen['fase'].apply(indice_fase)
            resumen = resumen.sort_values(
                ['_ord', 'equipo']).drop(columns='_ord')
            return resumen.reset_index(drop=True)
        except Exception as e:
            print(f"Error al obtener resumen progresión: {e}")
            return pd.DataFrame()

    def obtener_detalle_equipo_fase(self, equipo_id, fase):
        """Usuarios que recibieron bonus para un equipo en una fase."""
        try:
            response = self.client.table('progresion_equipos').select(
                'id, puntos, fecha, usuarios(nombre)'
            ).eq('equipo_id', equipo_id).eq('fase', fase).execute()
            if not response.data:
                return pd.DataFrame()
            data = []
            for item in response.data:
                usr = item.get('usuarios') or {}
                data.append({
                    'id': item['id'],
                    'usuario': usr.get('nombre', '?'),
                    'puntos': item['puntos'],
                    'fecha': item.get('fecha', ''),
                })
            return pd.DataFrame(data)
        except Exception as e:
            print(f"Error detalle progresión: {e}")
            return pd.DataFrame()

    def eliminar_progresion_equipo_fase(self, equipo_id, fase):
        """Elimina todos los bonus de un equipo en una fase."""
        try:
            prev = self.client.table('progresion_equipos').select('id').eq(
                'equipo_id', equipo_id).eq('fase', fase).execute()
            n = len(prev.data or [])
            if n == 0:
                return {'success': True, 'message': 'No había registros', 'eliminados': 0}
            self.client.table('progresion_equipos').delete().eq(
                'equipo_id', equipo_id).eq('fase', fase).execute()
            return {
                'success': True,
                'message': f'Eliminados {n} registro(s) de progresión',
                'eliminados': n,
            }
        except Exception as e:
            return {'success': False, 'message': str(e), 'eliminados': 0}

    def equipos_en_fase_partidos(self, fase):
        """Equipos que participan en partidos de una fase (local o visitante)."""
        try:
            response = self.client.table('partidos').select(
                'equipo_local_id, equipo_visitante_id'
            ).eq('fase', fase).execute()
            ids = set()
            for p in response.data or []:
                for col in ('equipo_local_id', 'equipo_visitante_id'):
                    eid = p.get(col)
                    if eid:
                        ids.add(int(eid))
            if not ids:
                return pd.DataFrame()
            equipos = self.client.table('equipos').select(
                'id, nombre').in_('id', list(ids)).execute()
            return pd.DataFrame(equipos.data or [])
        except Exception as e:
            print(f"Error equipos en fase: {e}")
            return pd.DataFrame()

    def equipos_sin_bonus_fase(self, fase):
        """Equipos en partidos de la fase que aún no tienen bonus aplicado."""
        en_fase = self.equipos_en_fase_partidos(fase)
        if en_fase.empty:
            return en_fase
        aplicado = self.obtener_resumen_aplicado(fase=fase)
        if aplicado.empty:
            return en_fase.rename(columns={'nombre': 'equipo'})
        con_bonus = set(aplicado['equipo_id'].astype(int))
        sin = en_fase[~en_fase['id'].isin(con_bonus)].copy()
        return sin.rename(columns={'nombre': 'equipo'})
