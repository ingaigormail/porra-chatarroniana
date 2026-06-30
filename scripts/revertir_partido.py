"""Revertir resultado de un partido (uso puntual / admin)."""
import sys
import tomllib
from pathlib import Path

try:
    import truststore
    truststore.inject_into_ssl()
except ImportError:
    pass

from supabase import create_client

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.services.partidos import PartidosService  # noqa: E402


def _fmt_partido(client, pid):
    p = client.table('partidos').select(
        'id,estado,goles_local,goles_visitante,hubo_prorroga,ganador_prorroga,'
        'equipo_local_id,equipo_visitante_id,fase'
    ).eq('id', pid).execute().data[0]
    eq = client.table('equipos').select('id,nombre').execute().data
    names = {e['id']: e['nombre'] for e in eq}
    loc = names.get(p.get('equipo_local_id'), '?')
    vis = names.get(p.get('equipo_visitante_id'), '?')
    return (
        f"#{pid}: {loc} vs {vis} | {p['estado']} {p['goles_local']}-{p['goles_visitante']} "
        f"prorr={p.get('hubo_prorroga')} gan={p.get('ganador_prorroga')}"
    )


def main():
    partido_id = int(sys.argv[1]) if len(sys.argv) > 1 else 77
    secrets = tomllib.load(open(ROOT / '.streamlit' / 'secrets.toml', 'rb'))
    client = create_client(secrets['supabase']['url'], secrets['supabase']['key'])

    print('ANTES 77:', _fmt_partido(client, 77))
    print('ANTES 89:', _fmt_partido(client, 89))

    svc = PartidosService(client)
    r = svc.revertir_resultado(partido_id, 'script_admin')
    print('REVERTIR:', r)

    print('DESPUES 77:', _fmt_partido(client, 77))
    print('DESPUES 89:', _fmt_partido(client, 89))

    q = client.table('quinielas').select(
        'id,puntos_provisionales,puntos_finales,validado'
    ).eq('partido_id', partido_id).execute().data
    print(f'Apuestas M{partido_id}: {len(q)} filas')


if __name__ == '__main__':
    main()
