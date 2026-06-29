# src/services/progresion.py
import pandas as pd
from datetime import datetime

from config.puntos_progresion import (
    FASES_PROGRESION,
    PUNTOS_1_GRUPO,
    PUNTOS_1_GRUPO_INVICTO,
    PUNTOS_2_GRUPO,
    PUNTOS_MEJOR_TERCERO,
    PUNTOS_FASE_FIJA,
)
from src.services.cruces import GRUPOS, CrucesService
from src.services.grupos import GruposService


class ProgresionService:
    """Gestiona los puntos de progresión de equipos por avance de fase."""

    FASES_VALIDAS = FASES_PROGRESION
    PUNTOS_SUGERIDOS = PUNTOS_FASE_FIJA

    def __init__(self, client):
        self.client = client

    def _grupos_service(self):
        return GruposService(self.client)

    def _mapa_clasificacion_dieciseisavos(self):
        """equipo_id -> {motivo, puntos} según grupos y ranking de terceros."""
        gs = self._grupos_service()
        mapa = {}
        for grupo in GRUPOS:
            df = gs.calcular_clasificacion_grupo(grupo)
            if df.empty:
                continue
            for _, row in df.iterrows():
                pos = int(row['posicion'])
                eid = int(row['id'])
                if pos == 1:
                    perdidos = int(row.get('perdidos', 0) or 0)
                    pj = int(row.get('pj', 0) or 0)
                    invicto = pj > 0 and perdidos == 0
                    puntos = PUNTOS_1_GRUPO + (
                        PUNTOS_1_GRUPO_INVICTO if invicto else 0)
                    motivo = f'1º Grupo {grupo}'
                    if invicto:
                        motivo += ' (invicto)'
                    mapa[eid] = {
                        'motivo': motivo,
                        'puntos': puntos,
                    }
                elif pos == 2:
                    mapa[eid] = {
                        'motivo': f'2º Grupo {grupo}',
                        'puntos': PUNTOS_2_GRUPO,
                    }

        cruces = CrucesService(self.client)
        mejores = cruces.calcular_mejores_terceros(gs)
        if not mejores.empty:
            for _, row in mejores.iterrows():
                if not row.get('clasifica'):
                    continue
                eid = int(row['id'])
                rank = int(row['posicion_mejores_terceros'])
                mapa[eid] = {
                    'motivo': f'{rank}º mejor 3º (Grupo {row["grupo"]})',
                    'puntos': PUNTOS_MEJOR_TERCERO.get(rank, 0),
                }
        return mapa

    def _clave_aplicado_sin_usuarios(self, equipo_id, fase):
        return f'progresion_aplicada_{fase}_{equipo_id}'

    def _marcar_aplicado_sin_usuarios(self, equipo_id, fase, puntos):
        """Marca equipo/fase como aplicado aunque nadie lo tenga en selecciones."""
        self.client.table('configuracion').upsert({
            'clave': self._clave_aplicado_sin_usuarios(equipo_id, fase),
            'valor': str(int(puntos)),
        }).execute()

    def _equipo_ya_aplicado(self, equipo_id, fase):
        r = self.client.table('progresion_equipos').select('id').eq(
            'equipo_id', equipo_id).eq('fase', fase).limit(1).execute()
        if r.data:
            return True
        cfg = self.client.table('configuracion').select('clave').eq(
            'clave', self._clave_aplicado_sin_usuarios(equipo_id, fase)
        ).limit(1).execute()
        return bool(cfg.data)

    def _contar_usuarios_equipo(self, equipo_id):
        r = self.client.table('selecciones').select(
            'usuario_id').eq('equipo_id', equipo_id).execute()
        return len(r.data or [])

    def obtener_tabla_aplicar_fase(self, fase):
        """
        Tabla para aplicar bonus de una fase.
        Columnas: equipo_id, equipo, motivo, puntos, aplicado, estado, usuarios
        """
        en_fase = self.equipos_en_fase_partidos(fase)
        if en_fase.empty:
            return pd.DataFrame()

        mapa_r16 = self._mapa_clasificacion_dieciseisavos() if fase == 'Dieciseisavos' else {}

        filas = []
        for _, eq in en_fase.iterrows():
            eid = int(eq['id'])
            nombre = eq['nombre']
            if fase == 'Dieciseisavos':
                info = mapa_r16.get(eid, {'motivo': '— (revisar grupos)', 'puntos': 0})
                motivo = info['motivo']
                puntos = int(info['puntos'])
            else:
                motivo = f'Pasa a {fase}'
                puntos = int(PUNTOS_FASE_FIJA.get(fase, 0))

            aplicado = self._equipo_ya_aplicado(eid, fase)
            usuarios = self._contar_usuarios_equipo(eid)
            if aplicado:
                estado = '✅ Aplicado'
            elif puntos > 0 and usuarios == 0:
                estado = '⏳ Pendiente (sin apostadores)'
            else:
                estado = '⏳ Pendiente'
            filas.append({
                'equipo_id': eid,
                'equipo': nombre,
                'motivo': motivo,
                'puntos': puntos,
                'aplicado': aplicado,
                'estado': estado,
                'usuarios': usuarios,
            })

        return pd.DataFrame(filas).sort_values('equipo').reset_index(drop=True)

    def aplicar_progresion_fase(self, fase, puntos_por_equipo=None):
        """Aplica bonus a todos los equipos pendientes de la fase."""
        puntos_por_equipo = puntos_por_equipo or {}
        tabla = self.obtener_tabla_aplicar_fase(fase)
        if tabla.empty:
            return {'success': False, 'message': 'No hay equipos en esta fase', 'equipos': 0}

        total_usuarios = 0
        equipos_ok = 0
        errores = []

        for _, row in tabla.iterrows():
            if row['aplicado']:
                continue
            eid = int(row['equipo_id'])
            pts = int(puntos_por_equipo.get(eid, row['puntos']))
            if pts <= 0:
                errores.append(f"{row['equipo']}: 0 puntos")
                continue
            r = self.calcular_y_guardar_progresion(eid, fase, pts)
            if r['success']:
                total_usuarios += r.get('usuarios_afectados', 0)
                equipos_ok += 1
            else:
                errores.append(f"{row['equipo']}: {r['message']}")

        msg = f'Aplicado en {equipos_ok} equipo(s), {total_usuarios} usuario(s) bonificados.'
        if errores:
            msg += ' Avisos: ' + '; '.join(errores[:3])
        return {'success': True, 'message': msg, 'equipos': equipos_ok}

    def corregir_bonus_dieciseisavos(self):
        """Ajusta bonus Dieciseisavos ya aplicados según mapa actual (mejores 3º, etc.)."""
        mapa = self._mapa_clasificacion_dieciseisavos()
        en_fase = self.equipos_en_fase_partidos('Dieciseisavos')
        actualizados = 0
        eliminados = 0
        detalle = []

        for _, eq in en_fase.iterrows():
            eid = int(eq['id'])
            nombre = eq['nombre']
            if not self._equipo_ya_aplicado(eid, 'Dieciseisavos'):
                continue
            pts_ok = int(mapa.get(eid, {}).get('puntos', 0))
            if pts_ok <= 0:
                r = self.eliminar_progresion_equipo_fase(eid, 'Dieciseisavos')
                if r.get('success'):
                    eliminados += 1
                    detalle.append(f'{nombre}: quitado')
            else:
                r = self.actualizar_puntos_equipo_fase(
                    eid, 'Dieciseisavos', pts_ok)
                if r.get('success'):
                    actualizados += 1
                    detalle.append(
                        f"{nombre}: {pts_ok} ({mapa[eid]['motivo']})")
                elif self._equipo_ya_aplicado(eid, 'Dieciseisavos'):
                    self._marcar_aplicado_sin_usuarios(
                        eid, 'Dieciseisavos', pts_ok)
                    actualizados += 1
                    detalle.append(f'{nombre}: marcador {pts_ok}')

        msg = (
            f'Corregidos {actualizados} equipo(s), '
            f'eliminados {eliminados} sin bonus de dieciseisavos.'
        )
        if detalle:
            msg += ' ' + '; '.join(detalle[:6])
            if len(detalle) > 6:
                msg += f' (+{len(detalle) - 6} más)'
        return {
            'success': True,
            'message': msg,
            'actualizados': actualizados,
            'eliminados': eliminados,
        }

    def eliminar_toda_progresion(self):
        try:
            prev = self.client.table('progresion_equipos').select('id').execute()
            n = len(prev.data or [])
            if n == 0:
                return {'success': True, 'message': 'No había registros', 'eliminados': 0}
            self.client.table('progresion_equipos').delete().neq('id', 0).execute()
            cfg = self.client.table('configuracion').select('clave').like(
                'clave', 'progresion_aplicada_%').execute()
            for item in cfg.data or []:
                self.client.table('configuracion').delete().eq(
                    'clave', item['clave']).execute()
            return {
                'success': True,
                'message': f'Eliminados {n} registros de progresión',
                'eliminados': n,
            }
        except Exception as e:
            return {'success': False, 'message': str(e), 'eliminados': 0}

    def actualizar_puntos_equipo_fase(self, equipo_id, fase, nuevos_puntos):
        """Cambia los puntos ya otorgados a todos los usuarios (equipo+fase)."""
        try:
            nuevos_puntos = int(nuevos_puntos)
            if nuevos_puntos < 0:
                return {'success': False, 'message': 'Puntos inválidos'}
            r = self.client.table('progresion_equipos').update({
                'puntos': nuevos_puntos,
            }).eq('equipo_id', equipo_id).eq('fase', fase).execute()
            n = len(r.data or [])
            if n == 0:
                return {'success': False, 'message': 'No había bonus aplicado para este equipo/fase'}
            return {'success': True, 'message': f'Actualizados {n} registro(s) a +{nuevos_puntos} pts'}
        except Exception as e:
            return {'success': False, 'message': str(e)}

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
                if fase == 'Dieciseisavos':
                    mapa = self._mapa_clasificacion_dieciseisavos()
                    info = mapa.get(int(equipo_id))
                    if not info or info['puntos'] <= 0:
                        return {
                            'success': False,
                            'message': 'No se pudo calcular puntos de dieciseisavos para este equipo.',
                            'usuarios_afectados': 0,
                        }
                    puntos_fase = info['puntos']
                elif fase in PUNTOS_FASE_FIJA:
                    puntos_fase = PUNTOS_FASE_FIJA[fase]
                else:
                    return {
                        'success': False,
                        'message': 'Indica cuántos puntos sumar.',
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
                self._marcar_aplicado_sin_usuarios(
                    equipo_id, fase, puntos_fase)
                return {
                    'success': True,
                    'message': (
                        f'Nadie eligió este equipo; marcado como aplicado '
                        f'(+{puntos_fase} pts)'
                    ),
                    'usuarios_afectados': 0,
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
            self.client.table('configuracion').delete().eq(
                'clave', self._clave_aplicado_sin_usuarios(equipo_id, fase)
            ).execute()
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
