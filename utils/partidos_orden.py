# utils/partidos_orden.py
"""Ordenación de partidos por fase del Mundial."""
import pandas as pd

# Orden oficial: Grupos → Dieciseisavos → Octavos → Cuartos → Semifinal → 3 y 4 → Final
ORDEN_FASES = [
    'Grupos',
    'Dieciseisavos',
    'Octavos',
    'Cuartos',
    'Semifinal',
    '3 y 4',
    'Final',
]


def indice_fase(fase) -> int:
    if fase is None or (isinstance(fase, float) and pd.isna(fase)):
        return 999
    f = str(fase).strip().lower()
    if f == 'grupos':
        return 0
    if 'diecis' in f:
        return 1
    if 'octav' in f:
        return 2
    if 'cuart' in f:
        return 3
    if 'semi' in f:
        return 4
    if '3 y 4' in f or '3y4' in f.replace(' ', ''):
        return 5
    if 'final' in f:
        return 6
    return 900


def ordenar_partidos(df: pd.DataFrame) -> pd.DataFrame:
    """Ordena por fase (Mundial) y dentro de cada fase por fecha e id."""
    if df.empty:
        return df
    out = df.copy()
    out['_idx_fase'] = out['fase'].apply(indice_fase)
    if 'fecha' in out.columns:
        out['_fecha_ord'] = pd.to_datetime(out['fecha'], errors='coerce')
        out = out.sort_values(
            ['_idx_fase', '_fecha_ord', 'id'],
            ascending=[True, True, True],
            na_position='last',
        )
    else:
        out = out.sort_values(['_idx_fase', 'id'], ascending=[True, True])
    return out.drop(columns=[c for c in ('_idx_fase', '_fecha_ord') if c in out.columns])
