# src/services/grupos.py
import pandas as pd


class GruposService:
    def __init__(self, client):
        self.client = client

    def calcular_clasificacion_grupo(self, grupo):
        """Calcula la clasificación de un grupo con criterios FIFA 2026"""
        # Obtener equipos del grupo
        equipos_response = self.client.table('equipos')\
            .select('id', 'nombre', 'puntos', 'gf', 'gc', 'dg', 'factor_fifa')\
            .eq('grupo', grupo)\
            .execute()
        equipos = equipos_response.data
        if not equipos:
            return pd.DataFrame()

        equipos_ids = [e['id'] for e in equipos]

        # Obtener partidos del grupo
        partidos_response = self.client.table('partidos')\
            .select('*')\
            .eq('fase', 'Grupos')\
            .execute()
        partidos = partidos_response.data

        # Filtrar partidos de este grupo
        partidos_grupo = []
        for p in partidos:
            if p['equipo_local_id'] in equipos_ids and p['equipo_visitante_id'] in equipos_ids:
                partidos_grupo.append(p)

        # Calcular estadísticas básicas
        stats = {}
        for equipo in equipos:
            stats[equipo['id']] = {
                'id': equipo['id'],
                'nombre': equipo['nombre'],
                'pj': 0, 'ganados': 0, 'empatados': 0, 'perdidos': 0,
                'gf': 0, 'gc': 0, 'dg': 0, 'puntos': 0,
                'factor_fifa': equipo.get('factor_fifa', 0.85)
            }

        # Procesar partidos jugados
        for p in partidos_grupo:
            if p['estado'] != 'Jugado':
                continue
            local_id = p['equipo_local_id']
            visitante_id = p['equipo_visitante_id']
            gl = p['goles_local']
            gv = p['goles_visitante']

            stats[local_id]['pj'] += 1
            stats[visitante_id]['pj'] += 1
            stats[local_id]['gf'] += gl
            stats[local_id]['gc'] += gv
            stats[visitante_id]['gf'] += gv
            stats[visitante_id]['gc'] += gl

            if gl > gv:
                stats[local_id]['ganados'] += 1
                stats[local_id]['puntos'] += 3
                stats[visitante_id]['perdidos'] += 1
            elif gv > gl:
                stats[visitante_id]['ganados'] += 1
                stats[visitante_id]['puntos'] += 3
                stats[local_id]['perdidos'] += 1
            else:
                stats[local_id]['empatados'] += 1
                stats[visitante_id]['empatados'] += 1
                stats[local_id]['puntos'] += 1
                stats[visitante_id]['puntos'] += 1

        for equipo_id in stats:
            stats[equipo_id]['dg'] = stats[equipo_id]['gf'] - \
                stats[equipo_id]['gc']

        # Función head-to-head
        def calcular_head_to_head(equipo1_id, equipo2_id, partidos_grupo):
            puntos = 0
            gf = 0
            gc = 0
            for p in partidos_grupo:
                if p['estado'] != 'Jugado':
                    continue
                if (p['equipo_local_id'] == equipo1_id and p['equipo_visitante_id'] == equipo2_id) or (
                        p['equipo_local_id'] == equipo2_id and p['equipo_visitante_id'] == equipo1_id):
                    if p['equipo_local_id'] == equipo1_id:
                        gl = p['goles_local']
                        gv = p['goles_visitante']
                    else:
                        gl = p['goles_visitante']
                        gv = p['goles_local']
                    gf += gl
                    gc += gv
                    if gl > gv:
                        puntos += 3
                    elif gl == gv:
                        puntos += 1
            return {'puntos': puntos, 'dg': gf - gc, 'gf': gf}

        # Ordenar con head-to-head
        equipos_stats = list(stats.values())
        equipos_ordenados = sorted(equipos_stats, key=lambda x: -x['puntos'])

        i = 0
        while i < len(equipos_ordenados):
            j = i
            while j < len(
                    equipos_ordenados) and equipos_ordenados[j]['puntos'] == equipos_ordenados[i]['puntos']:
                j += 1
            if j - i > 1:
                empatados = equipos_ordenados[i:j]
                h2h_results = {}
                for equipo in empatados:
                    h2h = {'puntos': 0, 'dg': 0, 'gf': 0}
                    for otro in empatados:
                        if equipo['id'] != otro['id']:
                            resultado = calcular_head_to_head(
                                equipo['id'], otro['id'], partidos_grupo)
                            h2h['puntos'] += resultado['puntos']
                            h2h['dg'] += resultado['dg']
                            h2h['gf'] += resultado['gf']
                    h2h_results[equipo['id']] = h2h
                empatados_ordenados = sorted(
                    empatados,
                    key=lambda x: (
                        -h2h_results[x['id']]['puntos'],
                        -h2h_results[x['id']]['dg'],
                        -h2h_results[x['id']]['gf'],
                        -x['dg'],
                        -x['gf'],
                        -x.get('factor_fifa', 0.85)
                    )
                )
                equipos_ordenados[i:j] = empatados_ordenados
            i = j

        for i, equipo in enumerate(equipos_ordenados):
            equipo['posicion'] = i + 1

        return pd.DataFrame(equipos_ordenados)
