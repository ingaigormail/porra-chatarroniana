# src/services/usuarios.py
import pandas as pd


class UsuariosService:
    def __init__(self, client):
        self.client = client

    def obtener_usuarios(self):
        response = self.client.table('usuarios').select('*').execute()
        return pd.DataFrame(response.data)

    def obtener_selecciones(self):
        response = self.client.table('selecciones')\
            .select('*, usuarios(nombre), equipos(nombre, grupo, puntos)')\
            .execute()

        data = response.data
        if not data:
            return pd.DataFrame()

        resultados = []
        for item in data:
            usuario = item.get('usuarios', {})
            equipo = item.get('equipos', {})
            resultados.append({
                'id': item.get('id'),
                'usuario_id': item.get('usuario_id'),
                'equipo_id': item.get('equipo_id'),
                'grupo_seleccion': item.get('grupo_seleccion'),
                'usuario_nombre': usuario.get('nombre') if usuario else None,
                'equipo_nombre': equipo.get('nombre') if equipo else None,
                'equipo_grupo': equipo.get('grupo') if equipo else None,
                'equipo_puntos': equipo.get('puntos') if equipo else 0
            })

        return pd.DataFrame(resultados)
