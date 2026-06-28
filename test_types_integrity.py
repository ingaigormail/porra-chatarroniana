#!/usr/bin/env python3
"""
TEST DE INTEGRIDAD DE TIPOS
Verifica que goles lleguen como int (no float/NaN).
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np
from src.database import Database
from src.data_layer import DataLayer


def test_integridad_tipos():
    """TEST 1: Verifica goles como int"""
    print("\n" + "="*80)
    print("TEST 1: INTEGRIDAD DE TIPOS - Partidos")
    print("="*80)
    
    db = Database()
    data_layer = DataLayer(db.client)
    df_partidos = data_layer.obtener_partidos()
    
    print(f"📊 Partidos: {len(df_partidos)}")
    
    errores = []
    for idx, row in df_partidos.iterrows():
        pid = row.get('id')
        gl = row.get('goles_local')
        gv = row.get('goles_visitante')
        
        if not isinstance(gl, (int, np.integer)):
            errores.append(f"❌ {pid}: goles_local={gl} tipo={type(gl).__name__}")
        if not isinstance(gv, (int, np.integer)):
            errores.append(f"❌ {pid}: goles_visitante={gv} tipo={type(gv).__name__}")
        if pd.isna(gl) or pd.isna(gv):
            errores.append(f"❌ {pid}: Contiene NaN")
    
    if errores:
        print("\n❌ ERRORES:")
        for e in errores:
            print(e)
        return False
    
    print("✅ Todos los goles son int")
    return True


def test_valores_null():
    """TEST 2: NULL → 0"""
    print("\n" + "="*80)
    print("TEST 2: NULL A CERO")
    print("="*80)
    
    db = Database()
    data_layer = DataLayer(db.client)
    df = data_layer.obtener_partidos()
    
    nulls = df[['goles_local', 'goles_visitante']].isna().sum().sum()
    
    if nulls > 0:
        print(f"❌ {nulls} valores NaN encontrados")
        return False
    
    print("✅ Sin NaN (convertidos a 0)")
    return True


def test_escritura_bd():
    """TEST 3: Escritura correcta"""
    print("\n" + "="*80)
    print("TEST 3: ESCRITURA EN BD")
    print("="*80)
    
    db = Database()
    data_layer = DataLayer(db.client)
    df = data_layer.obtener_partidos()
    
    if df.empty:
        print("⚠️ Sin partidos")
        return True
    
    pid = int(df.iloc[0]['id'])
    print(f"📝 Guardando resultado para partido {pid}...")
    
    resultado = data_layer.guardar_resultado(pid, 3, 2)
    
    if not resultado:
        print("❌ guardar_resultado falló")
        return False
    
    df_check = data_layer.obtener_partidos()
    p = df_check[df_check['id'] == pid].iloc[0]
    
    gl = p['goles_local']
    gv = p['goles_visitante']
    
    print(f"✅ Guardado: {gl}-{gv} (tipos: {type(gl).__name__}, {type(gv).__name__})")
    
    if gl != 3 or gv != 2:
        print("❌ Valores no coinciden")
        return False
    
    if not isinstance(gl, (int, np.integer)):
        print("❌ No es int")
        return False
    
    return True


def main():
    """Ejecuta todos los tests"""
    print("\n🧪 SUITE DE TESTS - INTEGRIDAD DE TIPOS")
    
    tests = [
        ("Integridad", test_integridad_tipos),
        ("NULL→0", test_valores_null),
        ("Escritura BD", test_escritura_bd),
    ]
    
    resultados = []
    for nombre, test_func in tests:
        try:
            resultado = test_func()
            resultados.append((nombre, resultado))
        except Exception as e:
            print(f"\n❌ EXCEPCIÓN: {e}")
            import traceback
            traceback.print_exc()
            resultados.append((nombre, False))
    
    print("\n" + "="*80)
    print("📊 RESUMEN")
    print("="*80)
    
    for nombre, resultado in resultados:
        estado = "✅" if resultado else "❌"
        print(f"{estado} {nombre}")
    
    total = sum(1 for _, r in resultados if r)
    
    if total == len(resultados):
        print(f"\n🎉 ¡{len(resultados)}/{len(resultados)} tests PASARON!")
        return 0
    else:
        print(f"\n❌ {len(resultados)-total} test(s) FALLARON")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
