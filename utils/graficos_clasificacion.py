# utils/graficos_clasificacion.py
"""Colores y trazas para gráficos de clasificación."""

PALETA_USUARIOS = [
    '#636EFA',
    '#EF553B',
    '#00CC96',
    '#AB63FA',
    '#FFA15A',
    '#19D3F3',
    '#FF6692',
    '#B6E880',
    '#FF97FF',
    '#FECB52',
    '#FF6B35',
    '#6C5CE7',
]

CATEGORIAS_DESGLOSE = [
    ('partidos_selecciones', 'Grupos y partidos', '#2ECC71'),
    ('bonus_dieciseisavos', 'Bonus 16avos', '#5DADE2'),
    ('bonus_octavos', 'Bonus octavos', '#3498DB'),
    ('bonus_cuartos', 'Bonus cuartos', '#2874A6'),
    ('bonus_semifinal', 'Bonus semifinal', '#8E44AD'),
    ('bonus_final', 'Bonus final', '#F1C40F'),
    ('quiniela', 'Quiniela', '#E67E22'),
    ('porra', 'Porra', '#9B59B6'),
    ('finalistas', 'Finalistas', '#E74C3C'),
]


def es_usuario_especial(nombre):
    return str(nombre).strip().lower() in ['jc', 'saul']


def color_barra_usuario(nombre, indice):
    """Color/patrón de barra individual (gráfico de totales)."""
    if es_usuario_especial(nombre):
        return {
            'color': 'rgba(255,0,0,0.0)',
            'pattern': {
                'shape': '|',
                'fgcolor': '#CC0000',
                'bgcolor': '#FFCE00',
                'size': 10,
                'solidity': 0.5,
            },
        }
    return PALETA_USUARIOS[indice % len(PALETA_USUARIOS)]
