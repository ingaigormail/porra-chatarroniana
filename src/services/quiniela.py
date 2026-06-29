# src/services/quiniela.py
import pandas as pd
from utils.validators import to_int  # IMPORTAR FUNCIÓN DE LIMPIEZA

from datetime import datetime


class QuinielaService:
    def __init__(self, client):
        self.client = client

    def guardar_apuesta(
            self,
            usuario_id,
            partido_id,
            tipo,
            eleccion_quiniela=None,
            goles_local=None,
            goles_visitante=None):
        # Validar que el partido esté abierto para apuestas
        partido = self.client.table('partidos').select(
            'apuestas_abiertas').eq('id', partido_id).execute()
        if not partido.data or not partido.data[0].get(
                'apuestas_abiertas', False):
            return {
                'success': False,
                'message': 'Este partido no está abierto para apuestas'}

        existing = self.client.table('quinielas')\
            .select('id')\
            .eq('usuario_id', usuario_id)\
            .eq('partido_id', partido_id)\
            .execute()

        data = {
            'usuario_id': usuario_id,
            'partido_id': partido_id,
            'tipo': tipo,
            'fecha_apuesta': datetime.now().isoformat(),
            'procesado': False,
            'validado': False,
            'puntos_provisionales': 0,
            'puntos_finales': 0
        }

        if tipo == 'quiniela':
            if eleccion_quiniela not in ['1', 'X', '2']:
                return {
                    'success': False,
                    'message': 'Elección de quiniela inválida'}
            data['eleccion_quiniela'] = eleccion_quiniela
            data['goles_local_apostados'] = None
            data['goles_visitante_apostados'] = None
        else:  # porra
            if goles_local is None or goles_visitante is None or goles_local < 0 or goles_visitante < 0:
                return {
                    'success': False,
                    'message': 'Goles inválidos para la porra'}
            data['goles_local_apostados'] = to_int(goles_local)
            data['goles_visitante_apostados'] = to_int(goles_visitante)
            data['eleccion_quiniela'] = None

        if existing.data:
            self.client.table('quinielas').update(data).eq(
                'id', existing.data[0]['id']).execute()
            return {'success': True, 'message': 'Apuesta actualizada'}
        else:
            self.client.table('quinielas').insert(data).execute()
            return {'success': True, 'message': 'Apuesta guardada'}

    def calcular_puntos_partido(self, partido_id):
        partido_resp = self.client.table('partidos').select(
            '*').eq('id', partido_id).execute()
        if not partido_resp.data:
            return {'success': False, 'message': 'Partido no encontrado'}
        partido = partido_resp.data[0]

        if partido['estado'] != 'Jugado':
            return {
                'success': False,
                'message': 'El partido aún no está jugado'}

        goles_local_real = partido['goles_local']
        goles_visitante_real = partido['goles_visitante']

        if goles_local_real > goles_visitante_real:
            ganador_90 = '1'
        elif goles_local_real < goles_visitante_real:
            ganador_90 = '2'
        else:
            ganador_90 = 'X'

        apuestas = self.client.table('quinielas')\
            .select('*')\
            .eq('partido_id', partido_id)\
            .eq('validado', False)\
            .execute()

        if not apuestas.data:
            return {'success': True, 'message': 'No hay apuestas pendientes'}

        for apuesta in apuestas.data:
            puntos = 0
            tipo = apuesta['tipo']

            if tipo == 'quiniela':
                eleccion = apuesta.get('eleccion_quiniela')
                if eleccion == ganador_90:
                    puntos = 3
            else:  # porra
                gl_apost = apuesta.get('goles_local_apostados', 0)
                gv_apost = apuesta.get('goles_visitante_apostados', 0)
                if gl_apost == goles_local_real and gv_apost == goles_visitante_real:
                    puntos = 5
                elif gl_apost == goles_local_real or gv_apost == goles_visitante_real:
                    puntos = 2

            self.client.table('quinielas').update({
                'puntos_provisionales': to_int(puntos),
                'procesado': True
            }).eq('id', apuesta['id']).execute()

        return {
            'success': True,
            'message': f'Puntos provisionales calculados para {
                len(
                    apuestas.data)} apuestas'}

    def obtener_apuestas_partido(self, partido_id):
        response = self.client.table('quinielas')\
            .select('*, usuarios(nombre)')\
            .eq('partido_id', partido_id)\
            .execute()
        data = response.data
        if not data:
            return pd.DataFrame()
        df = pd.DataFrame(data)
        df['usuario_nombre'] = df['usuarios'].apply(
            lambda x: x['nombre'] if x else '')
        df.drop(columns=['usuarios'], inplace=True)
        return df

    @staticmethod
    def texto_apuesta(tipo, eleccion_quiniela=None,
                      goles_local=None, goles_visitante=None):
        if tipo == 'quiniela':
            return f"1/X/2 → {eleccion_quiniela or '?'}"
        gl = 0 if goles_local is None else goles_local
        gv = 0 if goles_visitante is None else goles_visitante
        return f"Marcador → {gl}-{gv}"

    def resumen_apuestas_partido(self, partido_id, nombres_usuarios):
        """Quién apostó, qué eligió y quién falta (como finalistas)."""
        nombres_usuarios = sorted(set(nombres_usuarios))
        apuestas_df = self.obtener_apuestas_partido(partido_id)
        apostaron = []
        con_apuesta = set()

        for _, row in apuestas_df.iterrows():
            nombre = row.get('usuario_nombre') or ''
            if not nombre:
                continue
            con_apuesta.add(nombre)
            apostaron.append({
                'usuario': nombre,
                'tipo': row.get('tipo', ''),
                'apuesta': self.texto_apuesta(
                    row.get('tipo'),
                    row.get('eleccion_quiniela'),
                    row.get('goles_local_apostados'),
                    row.get('goles_visitante_apostados'),
                ),
                'puntos_provisionales': int(row.get('puntos_provisionales') or 0),
                'puntos_finales': int(row.get('puntos_finales') or 0),
                'validado': bool(row.get('validado')),
            })

        apostaron.sort(key=lambda x: x['usuario'].lower())
        faltan = [u for u in nombres_usuarios if u not in con_apuesta]
        return {
            'apostaron': apostaron,
            'faltan': faltan,
            'total_usuarios': len(nombres_usuarios),
            'hechas': len(con_apuesta),
        }

    def validar_apuestas(self, partido_id, puntos_editados=None):
        apuestas = self.client.table('quinielas')\
            .select('id, puntos_provisionales')\
            .eq('partido_id', partido_id)\
            .eq('validado', False)\
            .execute()

        if not apuestas.data:
            return {
                'success': False,
                'message': 'No hay apuestas pendientes de validar'}

        for apuesta in apuestas.data:
            apuesta_id = apuesta['id']
            if puntos_editados and apuesta_id in puntos_editados:
                puntos_final = puntos_editados[apuesta_id]
            else:
                puntos_final = apuesta['puntos_provisionales']

            self.client.table('quinielas').update({
                'puntos_finales': puntos_final,
                'validado': True
            }).eq('id', apuesta_id).execute()

        return {
            'success': True,
            'message': f'Apuestas validadas para el partido {partido_id}'}

    def obtener_apuestas_usuario(self, usuario_id, fase=None):
        query = self.client.table('quinielas')\
            .select('*, partidos(*)')\
            .eq('usuario_id', usuario_id)

        resp = query.execute()
        if not resp.data:
            return pd.DataFrame()

        datos = []
        for item in resp.data:
            partido = item.get('partidos', {})
            datos.append({
                'id': item['id'],
                'usuario_id': item['usuario_id'],
                'partido_id': item['partido_id'],
                'tipo': item.get('tipo'),
                'eleccion_quiniela': item.get('eleccion_quiniela'),
                'goles_local_apostados': item.get('goles_local_apostados'),
                'goles_visitante_apostados': item.get('goles_visitante_apostados'),
                'puntos_provisionales': item.get('puntos_provisionales', 0),
                'puntos_finales': item.get('puntos_finales', 0),
                'validado': item.get('validado', False),
                'fase': partido.get('fase') if partido else None,
                'estado': partido.get('estado') if partido else None,
                'goles_local': partido.get('goles_local') if partido else None,
                'goles_visitante': partido.get('goles_visitante') if partido else None,
                'fecha': partido.get('fecha') if partido else None,
                'equipo_local_id': partido.get('equipo_local_id') if partido else None,
                'equipo_visitante_id': partido.get('equipo_visitante_id') if partido else None,
            })

        df = pd.DataFrame(datos)
        if not df.empty:
            equipos_ids = []
            for _, row in df.iterrows():
                if row.get('equipo_local_id'):
                    equipos_ids.append(row['equipo_local_id'])
                if row.get('equipo_visitante_id'):
                    equipos_ids.append(row['equipo_visitante_id'])
            if equipos_ids:
                equipos_resp = self.client.table('equipos').select(
                    'id', 'nombre').in_('id', equipos_ids).execute()
                equipos_dict = {eq['id']: eq['nombre']
                                for eq in equipos_resp.data}
                df['equipo_local_nombre'] = df['equipo_local_id'].map(
                    equipos_dict)
                df['equipo_visitante_nombre'] = df['equipo_visitante_id'].map(
                    equipos_dict)

        if fase and 'fase' in df.columns:
            df = df[df['fase'] == fase]

        return df

    def apostar_finalistas(self, usuario_id, finalista_1_id, finalista_2_id):
        activo = self.client.table('configuracion').select('valor').eq(
            'clave', 'finalistas_activo').limit(1).execute()
        if not activo.data or activo.data[0].get('valor') != 'true':
            return {
                'success': False,
                'message': 'Las apuestas de finalistas están cerradas',
            }

        # Convertir int64 a int para evitar problemas de serialización JSON
        usuario_id = int(usuario_id)
        finalista_1_id = int(finalista_1_id)
        finalista_2_id = int(finalista_2_id)

        existing = self.client.table('finalistas_apostados')\
            .select('id')\
            .eq('usuario_id', usuario_id)\
            .execute()

        if existing.data:
            self.client.table('finalistas_apostados').update({
                'finalista_1_id': finalista_1_id,
                'finalista_2_id': finalista_2_id,
                'fecha_apuesta': datetime.now().isoformat()
            }).eq('id', existing.data[0]['id']).execute()
            return {'success': True, 'message': 'Finalistas actualizados'}
        else:
            self.client.table('finalistas_apostados').insert({
                'usuario_id': usuario_id,
                'finalista_1_id': finalista_1_id,
                'finalista_2_id': finalista_2_id,
                'fecha_apuesta': datetime.now().isoformat()
            }).execute()
            return {'success': True, 'message': 'Finalistas guardados'}

    def calcular_puntos_finalistas(self, finalista_1_real, finalista_2_real):
        apuestas = self.client.table('finalistas_apostados')\
            .select('*')\
            .execute()

        if not apuestas.data:
            return {
                'success': True,
                'message': 'No hay apuestas de finalistas'}

        contador = 0
        for apuesta in apuestas.data:
            puntos = 0
            aciertos = 0

            if apuesta['finalista_1_id'] in [
                    finalista_1_real, finalista_2_real]:
                aciertos += 1
            if apuesta['finalista_2_id'] in [
                    finalista_1_real, finalista_2_real]:
                aciertos += 1

            if aciertos == 2:
                puntos = 10
            elif aciertos == 1:
                puntos = 4

            self.client.table('finalistas_apostados').update({
                'puntos': to_int(puntos)
            }).eq('id', apuesta['id']).execute()

            contador += 1

        return {
            'success': True,
            'message': f'{contador} apuestas de finalistas procesadas'}

    def obtener_apuestas_usuario_finalistas(self, usuario_id):
        """Obtiene las apuestas de finalistas de un usuario con nombres de equipos"""
        response = self.client.table('finalistas_apostados')\
            .select('*')\
            .eq('usuario_id', usuario_id)\
            .execute()
        
        if not response.data:
            return pd.DataFrame()
        
        datos = []
        equipos_ids = []
        
        # Recolectar IDs de equipos
        for item in response.data:
            if item.get('finalista_1_id'):
                equipos_ids.append(item['finalista_1_id'])
            if item.get('finalista_2_id'):
                equipos_ids.append(item['finalista_2_id'])
        
        # Obtener nombres de equipos
        equipos_dict = {}
        if equipos_ids:
            equipos_resp = self.client.table('equipos')\
                .select('id, nombre')\
                .in_('id', equipos_ids)\
                .execute()
            equipos_dict = {eq['id']: eq['nombre'] for eq in equipos_resp.data}
        
        # Construir dataframe
        for item in response.data:
            datos.append({
                'id': item['id'],
                'usuario_id': item['usuario_id'],
                'finalista_1_id': item['finalista_1_id'],
                'finalista_1_nombre': equipos_dict.get(item['finalista_1_id'], '?'),
                'finalista_2_id': item['finalista_2_id'],
                'finalista_2_nombre': equipos_dict.get(item['finalista_2_id'], '?'),
                'puntos': item.get('puntos', 0),
                'fecha_apuesta': item.get('fecha_apuesta')
            })
        
        return pd.DataFrame(datos)

