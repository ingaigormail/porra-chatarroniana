# config/mejores_terceros.py
"""Ranking oficial de los 8 mejores terceros — Mundial 2026."""

# Orden del 1 al 8 (posición entre terceros clasificados)
MEJORES_TERCEROS_OFICIAL = [
    {'grupo': 'K', 'equipo': 'Republica del Congo', 'posicion': 1},
    {'grupo': 'F', 'equipo': 'Suecia', 'posicion': 2},
    {'grupo': 'L', 'equipo': 'Ghana', 'posicion': 3},
    {'grupo': 'E', 'equipo': 'Ecuador', 'posicion': 4},
    {'grupo': 'B', 'equipo': 'Bosnia y Herzegovina', 'posicion': 5},
    {'grupo': 'J', 'equipo': 'Argelia', 'posicion': 6},
    {'grupo': 'D', 'equipo': 'Paraguay', 'posicion': 7},
    {'grupo': 'I', 'equipo': 'Senegal', 'posicion': 8},
]

RANK_POR_GRUPO_TERCERO = {
    item['grupo']: item['posicion'] for item in MEJORES_TERCEROS_OFICIAL
}

GRUPOS_TERCERO_CLASIFICAN = set(RANK_POR_GRUPO_TERCERO.keys())
