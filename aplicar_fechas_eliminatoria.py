#!/usr/bin/env python3
"""Aplica fechas de config/fechas_eliminatoria.py a Supabase."""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from supabase import create_client

from config.fechas_eliminatoria import FECHAS


def main():
    with open('.streamlit/secrets.toml', encoding='utf-8') as f:
        content = f.read()
    url = re.search(r'url = "(.*?)"', content).group(1)
    key = re.search(r'key = "(.*?)"', content).group(1)
    client = create_client(url, key)

    for pid, fecha in FECHAS.items():
        client.table('partidos').update({'fecha': fecha}).eq('id', pid).execute()

    print(f'Actualizados {len(FECHAS)} partidos (M73-M104)')
    sample = client.table('partidos').select('id,fecha,fase').gte(
        'id', 73).lte('id', 76).order('id').execute().data
    for p in sample:
        print(p)


if __name__ == '__main__':
    main()
