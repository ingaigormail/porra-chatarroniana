# src/services/clasificacion.py
import pandas as pd


class ClasificacionService:
    def __init__(self, client):
        self.client = client

    def obtener_clasificacion(self):
        resultados = {}

        # 1. Puntos de equipos (selecciones)
        response = self.client.table('selecciones')\
            .select('usuario_id, usuarios(nombre), equipos(puntos)')\
            .execute()
        for item in response.data:
            usuario_nombre = item['usuarios']['nombre'] if item['usuarios'] else 'Desconocido'
            puntos_equipo = item['equipos']['puntos'] if item['equipos'] else 0
            if usuario_nombre not in resultados:
                resultados[usuario_nombre] = 0
            resultados[usuario_nombre] += puntos_equipo

        # 2. Puntos de quinielas (apuestas validadas)
        quiniela_response = self.client.table('quinielas')\
            .select('usuario_id, puntos_finales')\
            .execute()
        for item in quiniela_response.data:
            usuario_id = item['usuario_id']
            puntos = item.get('puntos_finales', 0)
            if puntos > 0:
                user_resp = self.client.table('usuarios').select(
                    'nombre').eq('id', usuario_id).execute()
                if user_resp.data:
                    nombre = user_resp.data[0]['nombre']
                    if nombre not in resultados:
                        resultados[nombre] = 0
                    resultados[nombre] += puntos

        # 3. Puntos de finalistas
        finalistas_response = self.client.table('finalistas_apostados')\
            .select('usuario_id, puntos')\
            .execute()
        for item in finalistas_response.data:
            user_resp = self.client.table('usuarios').select(
                'nombre').eq('id', item['usuario_id']).execute()
            if user_resp.data:
                nombre = user_resp.data[0]['nombre']
                puntos = item.get('puntos', 0)
                if nombre not in resultados:
                    resultados[nombre] = 0
                resultados[nombre] += puntos

        # 4. Puntos de progresión (bonus por avance de fase)
        progresion_response = self.client.table('progresion_equipos')\
            .select('usuario_id, puntos')\
            .execute()
        for item in progresion_response.data:
            usuario_id = item['usuario_id']
            puntos = item.get('puntos', 0)
            if puntos > 0:
                user_resp = self.client.table('usuarios').select(
                    'nombre').eq('id', usuario_id).execute()
                if user_resp.data:
                    nombre = user_resp.data[0]['nombre']
                    if nombre not in resultados:
                        resultados[nombre] = 0
                    resultados[nombre] += puntos

        df = pd.DataFrame([
            {'nombre': nombre, 'puntos': puntos}
            for nombre, puntos in resultados.items()
        ])
        if df.empty:
            return df
        df = df.sort_values('puntos', ascending=False).reset_index(drop=True)
        df['posicion'] = df.index + 1
        return df

    def obtener_datos_grafico_clasificacion(self):
        df = self.obtener_clasificacion()
        if df.empty:
            return df

        def get_color(nombre):
            nombre_limpio = str(nombre).strip().lower()
            if nombre_limpio in ['jc', 'saul']:
                return 'especial'
            return 'normal'
        df['tipo_barra'] = df['nombre'].apply(get_color)
        return df
