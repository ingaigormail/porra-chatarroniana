# src/services/cruces.py
"""Cuadro eliminatorio FIFA World Cup 2026 (M73-M104)."""
import pandas as pd

from src.services.annex_c_data import ANNEX_C_ROWS, ANNEX_C_WINNERS
from config.mejores_terceros import GRUPOS_TERCERO_CLASIFICAN, RANK_POR_GRUPO_TERCERO

GRUPOS = list('ABCDEFGHIJKL')

# Dieciseisavos (M73-M88)
R32_DEF = [
    (73, ('2', 'A'), ('2', 'B')),
    (74, ('1', 'E'), ('3', 'E')),
    (75, ('1', 'F'), ('2', 'C')),
    (76, ('1', 'C'), ('2', 'F')),
    (77, ('1', 'I'), ('3', 'I')),
    (78, ('2', 'E'), ('2', 'I')),
    (79, ('1', 'A'), ('3', 'A')),
    (80, ('1', 'L'), ('3', 'L')),
    (81, ('1', 'D'), ('3', 'D')),
    (82, ('1', 'G'), ('3', 'G')),
    (83, ('2', 'K'), ('2', 'L')),
    (84, ('1', 'H'), ('2', 'J')),
    (85, ('1', 'B'), ('3', 'B')),
    (86, ('1', 'J'), ('2', 'H')),
    (87, ('1', 'K'), ('3', 'K')),
    (88, ('2', 'D'), ('2', 'G')),
]

# id_partido -> (local_desde_id, visitante_desde_id)
AVANCE_ELIMINATORIA = {
    89: (74, 77), 90: (73, 75), 91: (76, 78), 92: (79, 80),
    93: (83, 84), 94: (81, 82), 95: (86, 88), 96: (85, 87),
    97: (89, 90), 98: (93, 94), 99: (91, 92), 100: (95, 96),
    101: (97, 98), 102: (99, 100),
}

FASE_SIGUIENTE_ELIMINATORIA = {
    'Dieciseisavos': 'Octavos',
    'Octavos': 'Cuartos',
    'Cuartos': 'Semifinal',
    'Semifinal': 'Final',
}

FASES_ELIMINATORIA = [
    (range(73, 89), 'Dieciseisavos'),
    (range(89, 97), 'Octavos'),
    (range(97, 101), 'Cuartos'),
    (range(101, 103), 'Semifinal'),
    (103, '3 y 4'),
    (104, 'Final'),
]


def _fase_partido(partido_id: int) -> str:
    for spec, nombre in FASES_ELIMINATORIA:
        if isinstance(spec, range) and partido_id in spec:
            return nombre
        if spec == partido_id:
            return nombre
    return 'Eliminatoria'


def lookup_terceros_por_combinacion(grupos_terceros: list[str]) -> dict[str, str]:
    """Anexo C: grupos cuyo 3.er clasifica -> asignación a cada 1X."""
    if len(grupos_terceros) != 8:
        raise ValueError(f'Se esperaban 8 grupos terceros, hay {len(grupos_terceros)}')
    clave = ''.join(sorted(grupos_terceros))
    for fila in ANNEX_C_ROWS:
        if ''.join(sorted(fila)) == clave:
            return {ANNEX_C_WINNERS[i]: fila[i] for i in range(8)}
    raise KeyError(f'Combinación Anexo C no encontrada: {clave}')


class CrucesService:
    def __init__(self, client):
        self.client = client

    def calcular_mejores_terceros(self, grupos_service):
        terceros = []
        for grupo in GRUPOS:
            df_grupo = grupos_service.calcular_clasificacion_grupo(grupo)
            if not df_grupo.empty and len(df_grupo) >= 3:
                tercero = df_grupo.iloc[2].to_dict()
                tercero['grupo'] = grupo
                terceros.append(tercero)

        if not terceros:
            return pd.DataFrame()

        if GRUPOS_TERCERO_CLASIFICAN:
            for t in terceros:
                grupo = t['grupo']
                if grupo in GRUPOS_TERCERO_CLASIFICAN:
                    t['posicion_mejores_terceros'] = RANK_POR_GRUPO_TERCERO[grupo]
                    t['clasifica'] = True
                else:
                    t['posicion_mejores_terceros'] = None
                    t['clasifica'] = False
            terceros_ordenados = sorted(
                terceros,
                key=lambda x: (
                    x['posicion_mejores_terceros'] is None,
                    x['posicion_mejores_terceros'] or 99,
                ),
            )
            return pd.DataFrame(terceros_ordenados)

        terceros_ordenados = sorted(
            terceros,
            key=lambda x: (
                -x['puntos'], -x['dg'], -x['gf'],
                -x.get('factor_fifa', 0.85),
            ),
        )
        for i, t in enumerate(terceros_ordenados):
            t['posicion_mejores_terceros'] = i + 1
            t['clasifica'] = i < 8
        return pd.DataFrame(terceros_ordenados)

    def _equipos_por_posicion(self, grupos_service):
        equipos = {}
        for grupo in GRUPOS:
            df = grupos_service.calcular_clasificacion_grupo(grupo)
            if df.empty:
                continue
            for _, row in df.iterrows():
                equipos[f"{grupo}{int(row['posicion'])}"] = int(row['id'])

        mejores = self.calcular_mejores_terceros(grupos_service)
        if mejores.empty:
            return equipos, mejores, {}

        clasificados = mejores[mejores['clasifica']]
        terceros_map = {}
        for _, row in clasificados.iterrows():
            g = row['grupo']
            equipos[f'{g}3'] = int(row['id'])
            terceros_map[g] = int(row['id'])

        grupos_3 = sorted(clasificados['grupo'].tolist())
        try:
            annex = lookup_terceros_por_combinacion(grupos_3)
        except KeyError:
            annex = {}
        return equipos, mejores, annex

    def _resolver_boca(self, ref, equipos, annex):
        """ref = ('1','A'), ('2','B') o ('3','E') — E = ganador cuyo slot de 3.er usa Anexo C."""
        tipo, grupo = ref
        if tipo in ('1', '2'):
            return equipos.get(f'{grupo}{tipo}')
        if tipo == '3':
            if annex and grupo in annex:
                g_tercero = annex[grupo]
                return equipos.get(f'{g_tercero}3')
            return equipos.get(f'{grupo}3')
        return None

    def generar_cruces_dieciseisavos(self, grupos_service):
        equipos, mejores, annex = self._equipos_por_posicion(grupos_service)
        if mejores.empty or len(annex) != 8:
            return []

        partidos = []
        for pid, local_ref, visit_ref in R32_DEF:
            local_id = self._resolver_boca(local_ref, equipos, annex)
            visit_id = self._resolver_boca(visit_ref, equipos, annex)
            if local_id and visit_id:
                partidos.append({
                    'id': pid,
                    'local_id': local_id,
                    'visitante_id': visit_id,
                })
        return partidos

    def asegurar_partidos_eliminatoria(self):
        """Crea M73-M104 en BD si no existen."""
        existentes = {
            p['id'] for p in
            self.client.table('partidos').select('id').gte('id', 73).lte('id', 104).execute().data
        }
        creados = 0
        for pid in range(73, 105):
            if pid in existentes:
                continue
            self.client.table('partidos').insert({
                'id': pid,
                'fase': _fase_partido(pid),
                'fecha': None,
                'equipo_local_id': None,
                'equipo_visitante_id': None,
                'goles_local': 0,
                'goles_visitante': 0,
                'estado': 'Pendiente',
                'tipo_apuesta': 'ninguno',
                'apuestas_abiertas': False,
                'hubo_prorroga': False,
            }).execute()
            creados += 1
        return creados

    def actualizar_cruces(self, grupos_service):
        """Genera dieciseisavos con Anexo C y persiste en BD."""
        creados = self.asegurar_partidos_eliminatoria()
        cruces = self.generar_cruces_dieciseisavos(grupos_service)

        if len(cruces) < 16:
            return {
                'success': False,
                'message': (
                    f'Solo se pudieron armar {len(cruces)}/16 cruces. '
                    'Comprueba que todos los grupos tienen resultados completos.'
                ),
                'creados': creados,
                'cruces': len(cruces),
            }

        for cruce in cruces:
            self.client.table('partidos').update({
                'equipo_local_id': cruce['local_id'],
                'equipo_visitante_id': cruce['visitante_id'],
                'fase': 'Dieciseisavos',
                'estado': 'Pendiente',
            }).eq('id', cruce['id']).execute()

        return {
            'success': True,
            'message': f'16 cruces de Dieciseisavos generados ({creados} partidos nuevos creados)',
            'creados': creados,
            'cruces': 16,
        }

    def _ganador_partido(self, partido: dict) -> int | None:
        if partido.get('estado') != 'Jugado':
            return None
        gl = int(partido.get('goles_local') or 0)
        gv = int(partido.get('goles_visitante') or 0)
        gp = partido.get('ganador_prorroga')
        if gl == gv and gp in ('local', 'visitante'):
            if gp == 'local':
                return partido['equipo_local_id']
            return partido['equipo_visitante_id']
        if partido.get('hubo_prorroga') and gp in ('local', 'visitante'):
            if gp == 'local':
                return partido['equipo_local_id']
            return partido['equipo_visitante_id']
        if gl > gv:
            return partido['equipo_local_id']
        if gv > gl:
            return partido['equipo_visitante_id']
        return None

    def _perdedor_partido(self, partido: dict) -> int | None:
        ganador = self._ganador_partido(partido)
        if ganador is None:
            return None
        if ganador == partido['equipo_local_id']:
            return partido['equipo_visitante_id']
        return partido['equipo_local_id']

    def avanzar_ganador(self, partido_id: int):
        """Tras guardar un resultado, rellena el siguiente cruce en el cuadro."""
        resp = self.client.table('partidos').select('*').eq('id', partido_id).execute()
        if not resp.data:
            return
        origen = resp.data[0]
        ganador = self._ganador_partido(origen)
        if not ganador:
            return

        if partido_id in (101, 102):
            self._colocar_en_siguiente(104, partido_id, ganador, es_local=(partido_id == 101))
            perdedor = self._perdedor_partido(origen)
            if perdedor:
                self._colocar_en_siguiente(103, partido_id, perdedor, es_local=(partido_id == 101))
            return

        for siguiente_id, (id_a, id_b) in AVANCE_ELIMINATORIA.items():
            if partido_id == id_a:
                self._colocar_en_siguiente(siguiente_id, partido_id, ganador, es_local=True)
                return
            if partido_id == id_b:
                self._colocar_en_siguiente(siguiente_id, partido_id, ganador, es_local=False)
                return

    def _colocar_en_siguiente(
            self, siguiente_id: int, origen_id: int, equipo_id: int, *, es_local: bool):
        dest = self.client.table('partidos').select('*').eq('id', siguiente_id).execute()
        if not dest.data:
            self.asegurar_partidos_eliminatoria()
            dest = self.client.table('partidos').select('*').eq('id', siguiente_id).execute()
        if not dest.data:
            return

        campo = 'equipo_local_id' if es_local else 'equipo_visitante_id'
        actual = dest.data[0].get(campo)
        if actual == equipo_id:
            return

        self.client.table('partidos').update({
            campo: equipo_id,
            'fase': _fase_partido(siguiente_id),
        }).eq('id', siguiente_id).execute()

    def _limpiar_slot_siguiente(
            self, siguiente_id: int, equipo_id: int, *, es_local: bool) -> bool:
        dest = self.client.table('partidos').select('*').eq(
            'id', siguiente_id).execute()
        if not dest.data:
            return False
        campo = 'equipo_local_id' if es_local else 'equipo_visitante_id'
        if dest.data[0].get(campo) != equipo_id:
            return False
        self.client.table('partidos').update({
            campo: None,
        }).eq('id', siguiente_id).execute()
        return True

    def revertir_avance_ganador(self, partido_id: int, ganador_id=None):
        """Quita del cruce siguiente el equipo que avanzó desde este partido."""
        if ganador_id is None:
            resp = self.client.table('partidos').select('*').eq(
                'id', partido_id).execute()
            if not resp.data:
                return {'success': False, 'message': 'Partido no encontrado', 'slots': 0}
            ganador_id = self._ganador_partido(resp.data[0])
        if not ganador_id:
            return {
                'success': True,
                'message': 'Sin ganador que revertir en el cuadro',
                'slots': 0,
                'ganador_id': None,
            }

        slots = 0
        if partido_id in (101, 102):
            if self._limpiar_slot_siguiente(
                    104, ganador_id, es_local=(partido_id == 101)):
                slots += 1
            perdedor = None
            resp = self.client.table('partidos').select('*').eq(
                'id', partido_id).execute()
            if resp.data:
                perdedor = self._perdedor_partido(resp.data[0])
            if perdedor and self._limpiar_slot_siguiente(
                    103, perdedor, es_local=(partido_id == 101)):
                slots += 1
        else:
            for siguiente_id, (id_a, id_b) in AVANCE_ELIMINATORIA.items():
                if partido_id == id_a:
                    if self._limpiar_slot_siguiente(
                            siguiente_id, ganador_id, es_local=True):
                        slots += 1
                if partido_id == id_b:
                    if self._limpiar_slot_siguiente(
                            siguiente_id, ganador_id, es_local=False):
                        slots += 1

        return {
            'success': True,
            'message': f'Quitado del cuadro en {slots} hueco(s)',
            'slots': slots,
            'ganador_id': ganador_id,
        }
