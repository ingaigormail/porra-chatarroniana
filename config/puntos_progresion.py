# config/puntos_progresion.py
"""Puntos de progresión por pasar de fase (bonus a usuarios con esa selección)."""

# Dieciseisavos — según cómo clasificó en grupos
PUNTOS_1_GRUPO = 18
PUNTOS_2_GRUPO = 15

# Ranking entre los 8 mejores terceros (1 = mejor)
PUNTOS_MEJOR_TERCERO = {
    1: 12,
    2: 10,
    3: 8,
    4: 6,
    5: 5,
    6: 4,
    7: 3,
    8: 2,
}

# Octavos en adelante — fijo por pasar de ronda
PUNTOS_FASE_FIJA = {
    'Octavos': 10,
    'Cuartos': 15,
    'Semifinal': 20,
    'Final': 30,
}

FASES_PROGRESION = [
    'Dieciseisavos', 'Octavos', 'Cuartos', 'Semifinal', 'Final',
]
