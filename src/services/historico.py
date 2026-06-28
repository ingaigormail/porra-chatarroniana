# src/services/historico.py
import pandas as pd


class HistoricoService:
    def __init__(self, client):
        self.client = client

    def guardar_snapshot(self, clasificacion_service):
        df_rank = clasificacion_service.obtener_clasificacion()
        if df_rank.empty:
            return False

        usuarios_response = self.client.table(
            'usuarios').select('id', 'nombre').execute()
        usuarios_dict = {u['nombre']: u['id'] for u in usuarios_response.data}

        for _, row in df_rank.iterrows():
            usuario_id = usuarios_dict.get(row['nombre'])
            if usuario_id:
                self.client.table('historico_puntos').insert({
                    'usuario_id': usuario_id,
                    'puntos': int(row['puntos']),
                    'posicion': int(row['posicion'])
                }).execute()
        return True

    def obtener_ultimo_snapshot(self):
        response = self.client.table('historico_puntos')\
            .select('fecha')\
            .order('fecha', desc=True)\
            .limit(1)\
            .execute()
        if not response.data:
            return pd.DataFrame()

        ultima_fecha = response.data[0]['fecha']
        response = self.client.table('historico_puntos')\
            .select('*, usuarios(nombre)')\
            .eq('fecha', ultima_fecha)\
            .execute()

        data = []
        for item in response.data:
            data.append({
                'nombre': item['usuarios']['nombre'] if item['usuarios'] else 'Desconocido',
                'puntos_anterior': item['puntos'],
                'posicion_anterior': item['posicion']
            })
        return pd.DataFrame(data)

    def obtener_movimientos(self, clasificacion_service, df_actual=None):
        if df_actual is None:
            df_actual = clasificacion_service.obtener_clasificacion()
        if df_actual.empty:
            return pd.DataFrame()

        df_anterior = self.obtener_ultimo_snapshot()
        if df_anterior.empty:
            df_actual['cambio'] = 0
            df_actual['tipo'] = 'mantiene'
            return df_actual

        df_combinado = df_actual.merge(
            df_anterior[['nombre', 'posicion_anterior']],
            on='nombre',
            how='left'
        )
        df_combinado['posicion_anterior'] = df_combinado['posicion_anterior'].fillna(
            df_combinado['posicion'])
        df_combinado['cambio'] = df_combinado['posicion_anterior'] - \
            df_combinado['posicion']
        df_combinado['cambio'] = df_combinado['cambio'].astype(int)

        def get_tipo(row):
            if row['cambio'] > 0:
                return 'sube'
            elif row['cambio'] < 0:
                return 'baja'
            else:
                return 'mantiene'

        df_combinado['tipo'] = df_combinado.apply(get_tipo, axis=1)
        return df_combinado
