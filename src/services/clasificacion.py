# src/services/clasificacion.py
import pandas as pd


class ClasificacionService:
    def __init__(self, client):
        self.client = client

    def _nombre_usuario(self, item):
        usr = item.get('usuarios') or {}
        return usr.get('nombre') or 'Desconocido'

    def obtener_clasificacion(self):
        resultados = {}

        def sumar(nombre, puntos):
            if not nombre or puntos <= 0:
                return
            resultados[nombre] = resultados.get(nombre, 0) + int(puntos)

        # 1. Puntos de equipos (selecciones)
        response = self.client.table('selecciones')\
            .select('usuario_id, usuarios(nombre), equipos(puntos)')\
            .execute()
        for item in response.data or []:
            puntos_equipo = (item.get('equipos') or {}).get('puntos') or 0
            sumar(self._nombre_usuario(item), puntos_equipo)

        # 2–4. Quinielas, finalistas y progresión (join usuarios, sin N+1)
        quiniela_response = self.client.table('quinielas')\
            .select('puntos_finales, usuarios(nombre)')\
            .execute()
        for item in quiniela_response.data or []:
            sumar(self._nombre_usuario(item), item.get('puntos_finales') or 0)

        finalistas_response = self.client.table('finalistas_apostados')\
            .select('puntos, usuarios(nombre)')\
            .execute()
        for item in finalistas_response.data or []:
            sumar(self._nombre_usuario(item), item.get('puntos') or 0)

        progresion_response = self.client.table('progresion_equipos')\
            .select('puntos, usuarios(nombre)')\
            .execute()
        for item in progresion_response.data or []:
            sumar(self._nombre_usuario(item), item.get('puntos') or 0)

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

    def obtener_desglose_puntos(self):
        """
        Puntos por usuario desglosados (versión simple).
        Columnas: partidos_selecciones, bonus por fase, quiniela, porra, finalistas.
        """
        usuarios_r = self.client.table('usuarios').select('id, nombre').execute()
        uid_a_nombre = {
            u['id']: u['nombre'] for u in (usuarios_r.data or [])
        }

        categorias = [
            'partidos_selecciones',
            'bonus_dieciseisavos',
            'bonus_octavos',
            'bonus_cuartos',
            'bonus_semifinal',
            'bonus_final',
            'quiniela',
            'porra',
            'finalistas',
        ]
        vacio = {c: 0 for c in categorias}
        desglose = {nombre: vacio.copy() for nombre in uid_a_nombre.values()}

        sel_r = self.client.table('selecciones').select(
            'usuario_id, equipos(puntos)').execute()
        for item in sel_r.data or []:
            nombre = uid_a_nombre.get(item['usuario_id'])
            if not nombre:
                continue
            eq = item.get('equipos') or {}
            desglose[nombre]['partidos_selecciones'] += int(eq.get('puntos') or 0)

        fase_a_col = {
            'Dieciseisavos': 'bonus_dieciseisavos',
            'Octavos': 'bonus_octavos',
            'Cuartos': 'bonus_cuartos',
            'Semifinal': 'bonus_semifinal',
            'Final': 'bonus_final',
        }
        prog_r = self.client.table('progresion_equipos').select(
            'usuario_id, fase, puntos').execute()
        for item in prog_r.data or []:
            nombre = uid_a_nombre.get(item['usuario_id'])
            col = fase_a_col.get(item.get('fase'))
            if not nombre or not col:
                continue
            pts = int(item.get('puntos') or 0)
            if pts > 0:
                desglose[nombre][col] += pts

        q_r = self.client.table('quinielas').select(
            'usuario_id, tipo, puntos_finales').execute()
        for item in q_r.data or []:
            nombre = uid_a_nombre.get(item['usuario_id'])
            if not nombre:
                continue
            pts = int(item.get('puntos_finales') or 0)
            if pts <= 0:
                continue
            tipo = item.get('tipo')
            if tipo == 'quiniela':
                desglose[nombre]['quiniela'] += pts
            elif tipo == 'porra':
                desglose[nombre]['porra'] += pts

        fin_r = self.client.table('finalistas_apostados').select(
            'usuario_id, puntos').execute()
        for item in fin_r.data or []:
            nombre = uid_a_nombre.get(item['usuario_id'])
            if not nombre:
                continue
            pts = int(item.get('puntos') or 0)
            if pts > 0:
                desglose[nombre]['finalistas'] += pts

        filas = []
        for nombre, d in desglose.items():
            filas.append({
                'nombre': nombre,
                **{c: int(d.get(c, 0)) for c in categorias},
                'total': int(sum(d.get(c, 0) for c in categorias)),
            })

        if not filas:
            return pd.DataFrame()

        df = pd.DataFrame(filas)
        df = df[df['total'] > 0].sort_values(
            'total', ascending=False).reset_index(drop=True)
        df['posicion'] = df.index + 1
        return df
