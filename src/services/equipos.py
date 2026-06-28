# src/services/equipos.py
from utils.validators import to_int  # IMPORTAR FUNCIÓN DE LIMPIEZA

import pandas as pd


class EquiposService:
    def __init__(self, client):
        self.client = client

    def obtener_equipos(self):
        response = self.client.table('equipos').select('*').execute()
        return pd.DataFrame(response.data)

    def obtener_mvp(self):
        response = self.client.table('equipos').select(
            'nombre', 'puntos').execute()
        df = pd.DataFrame(response.data)
        if df.empty:
            return df
        df = df.sort_values('puntos', ascending=False).reset_index(drop=True)
        max_puntos = df['puntos'].max() if not df.empty else 0
        return df[df['puntos'] == max_puntos]

    def obtener_radar(self):
        response = self.client.table('selecciones')\
            .select('equipos(nombre)')\
            .execute()
        if not response.data:
            return pd.DataFrame()
        votos = {}
        for item in response.data:
            nombre = item['equipos']['nombre'] if item['equipos'] else None
            if nombre:
                votos[nombre] = votos.get(nombre, 0) + 1
        df = pd.DataFrame([
            {'nombre': nombre, 'votos': votos}
            for nombre, votos in votos.items()
        ])
        if df.empty:
            return df
        return df.sort_values('votos', ascending=False).reset_index(drop=True)

    def obtener_equipos_mas_votados(self):
        response = self.client.table('selecciones')\
            .select('equipos(nombre)')\
            .execute()
        if not response.data:
            return pd.DataFrame()
        votos = {}
        for item in response.data:
            nombre = item['equipos']['nombre'] if item['equipos'] else None
            if nombre:
                votos[nombre] = votos.get(nombre, 0) + 1
        df = pd.DataFrame([
            {'Equipo': nombre, 'Votos': votos}
            for nombre, votos in sorted(votos.items(), key=lambda x: x[1], reverse=True)
        ])
        return df

    def obtener_puntos_equipos_reales(self):
        response = self.client.table('equipos')\
            .select('nombre', 'puntos')\
            .order('puntos', desc=True)\
            .execute()
        df = pd.DataFrame(response.data)
        if not df.empty:
            df['puntos'] = pd.to_numeric(
                df['puntos'], errors='coerce').fillna(0)
            df = df[df['puntos'] > 0]
            df = df.sort_values(
                'puntos',
                ascending=False).reset_index(
                drop=True)
        return df

    def _recalcular_puntos_equipos(self, partidos_df):
        """
        Recalcula los puntos de todos los equipos a partir de los partidos jugados,
        teniendo en cuenta la prórroga según la normativa.
        """
        equipos_response = self.client.table('equipos').select('id').execute()
        df_equipos = pd.DataFrame(equipos_response.data)

        stats = {}
        for _, eq in df_equipos.iterrows():
            stats[eq['id']] = {
                'pj': 0, 'ganados': 0, 'empatados': 0, 'perdidos': 0,
                'gf': 0, 'gc': 0, 'dg': 0, 'puntos': 0
            }

        # Procesar TODOS los partidos jugados (incluye eliminatorias)
        df_jugados = partidos_df[partidos_df['estado'] == 'Jugado']

        for _, partido in df_jugados.iterrows():
            local_id = partido['equipo_local_id']
            visitante_id = partido['equipo_visitante_id']
            gl = partido['goles_local']
            gv = partido['goles_visitante']
            hubo_prorroga = partido.get('hubo_prorroga', False)
            ganador_prorroga = partido.get('ganador_prorroga')

            # Si no hay equipo asignado (ej: cruces aún no generados), saltar
            if local_id is None or visitante_id is None:
                continue

            stats[local_id]['pj'] += 1
            stats[visitante_id]['pj'] += 1

            stats[local_id]['gf'] += gl
            stats[local_id]['gc'] += gv
            stats[visitante_id]['gf'] += gv
            stats[visitante_id]['gc'] += gl

            if hubo_prorroga and ganador_prorroga:
                if ganador_prorroga == 'local':
                    stats[local_id]['ganados'] += 1
                    stats[visitante_id]['perdidos'] += 1
                    stats[local_id]['puntos'] += 3
                elif ganador_prorroga == 'visitante':
                    stats[visitante_id]['ganados'] += 1
                    stats[local_id]['perdidos'] += 1
                    stats[visitante_id]['puntos'] += 3
            else:
                if gl > gv:
                    stats[local_id]['ganados'] += 1
                    stats[visitante_id]['perdidos'] += 1
                    stats[local_id]['puntos'] += 3
                elif gv > gl:
                    stats[visitante_id]['ganados'] += 1
                    stats[local_id]['perdidos'] += 1
                    stats[visitante_id]['puntos'] += 3
                else:
                    stats[local_id]['empatados'] += 1
                    stats[visitante_id]['empatados'] += 1
                    stats[local_id]['puntos'] += 1
                    stats[visitante_id]['puntos'] += 1

        for equipo_id, data in stats.items():
            data['dg'] = data['gf'] - data['gc']
            
            # LIMPIEZA CRÍTICA: Convertir todos los valores a int
            # Evita error: "invalid input syntax for type integer: -2.0"
            data_to_update = {
                'pj': to_int(data['pj']),
                'ganados': to_int(data['ganados']),
                'empatados': to_int(data['empatados']),
                'perdidos': to_int(data['perdidos']),
                'gf': to_int(data['gf']),
                'gc': to_int(data['gc']),
                'dg': to_int(data['dg']),
                'puntos': to_int(data['puntos'])
            }
            
            # LOG: Verificar que no hay decimales antes de enviar
            print(f"[equipos.py] Enviando a Supabase - Equipo {equipo_id}: {data_to_update}")
            
            self.client.table('equipos').update(data_to_update).eq('id', equipo_id).execute()
