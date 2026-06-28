# utils/graficos_clasificacion.py
"""Colores y trazas para gráficos de clasificación."""

import plotly.graph_objects as go

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


def _color_texto_segmento(color_hex):
    """Texto legible sobre el color del segmento."""
    hex_limpio = color_hex.lstrip('#')
    if len(hex_limpio) != 6:
        return 'white'
    r, g, b = (int(hex_limpio[i:i + 2], 16) for i in (0, 2, 4))
    luminancia = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    return '#1a1a1a' if luminancia > 0.62 else 'white'


def _etiquetas_segmento(valores):
    """Número dentro del trozo solo si hay puntos."""
    return [str(int(v)) if int(v) > 0 else '' for v in valores]


def construir_figura_desglose_apilado(df_desglose):
    """Barras apiladas con puntos por categoría y total arriba."""
    fig = go.Figure()
    cols_categorias = [c[0] for c in CATEGORIAS_DESGLOSE]

    for col, etiqueta, color in CATEGORIAS_DESGLOSE:
        if df_desglose[col].sum() == 0:
            continue
        valores = df_desglose[col]
        fig.add_trace(go.Bar(
            name=etiqueta,
            x=df_desglose['nombre'],
            y=valores,
            marker_color=color,
            text=_etiquetas_segmento(valores),
            textposition='inside',
            insidetextanchor='middle',
            textfont=dict(
                size=11,
                color=_color_texto_segmento(color),
            ),
            hovertemplate=(
                '%{x}<br>' + etiqueta + ': %{y} pts<extra></extra>'
            ),
        ))

    if 'total' in df_desglose.columns:
        totales = df_desglose['total']
    else:
        totales = df_desglose[cols_categorias].sum(axis=1)

    fig.add_trace(go.Scatter(
        x=df_desglose['nombre'],
        y=totales,
        mode='text',
        text=[str(int(t)) for t in totales],
        textposition='top center',
        textfont=dict(size=13, color='#222'),
        showlegend=False,
        hoverinfo='skip',
    ))

    max_total = int(totales.max()) if len(totales) else 0
    margen_superior = max(8, int(max_total * 0.12))

    fig.update_layout(
        barmode='stack',
        margin=dict(l=0, r=0, t=30, b=80),
        yaxis_title='Puntos',
        yaxis=dict(range=[0, max_total + margen_superior]),
        xaxis=dict(showticklabels=True, tickangle=-45),
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1,
        ),
        height=max(450, 35 * len(df_desglose)),
    )

    return fig
