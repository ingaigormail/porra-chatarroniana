# src/services/configuracion.py
import pandas as pd


class ConfiguracionService:
    def __init__(self, client):
        self.client = client

    def obtener_valor(self, clave):
        response = self.client.table('configuracion')\
            .select('valor')\
            .eq('clave', clave)\
            .execute()
        if response.data:
            return response.data[0]['valor']
        return None

    def actualizar_valor(self, clave, valor):
        try:
            self.client.table('configuracion').upsert({
                'clave': clave,
                'valor': str(valor)
            }).execute()
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}
