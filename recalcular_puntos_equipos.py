#!/usr/bin/env python3
"""
Recalcular puntos de todos los equipos basados en partidos jugados
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.database import Database
import pandas as pd

print("=" * 80)
print("📊 RECALCULAR PUNTOS DE EQUIPOS")
print("=" * 80)

try:
    # Inicializar BD
    print("\n📡 Conectando a base de datos...")
    db = Database()
    print("✅ Conexión exitosa")
    
    # Obtener partidos
    print("\n📋 Obteniendo partidos...")
    partidos = db.obtener_partidos()
    
    # Filtrar jugados
    jugados = partidos[partidos['estado'] == 'Jugado']
    print(f"✅ {len(jugados)} partidos jugados encontrados")
    
    # Obtener equipos
    print("\n⚽ Obteniendo equipos...")
    equipos = db.obtener_equipos()
    print(f"✅ {len(equipos)} equipos")
    
    # Recalcular puntos
    print("\n🔄 Recalculando puntos de equipos...")
    from src.services.equipos import EquiposService
    equipos_service = EquiposService(db.client)
    equipos_service._recalcular_puntos_equipos(jugados)
    
    print("✅ Puntos recalculados")
    
    # Mostrar top 10 equipos
    print("\n📊 Top 10 equipos por puntos:")
    top_equipos = equipos.nlargest(10, 'puntos')[['nombre', 'puntos']].reset_index(drop=True)
    for idx, row in top_equipos.iterrows():
        print(f"   {idx+1}. {row['nombre']}: {row['puntos']} pts")
    
    print("\n" + "=" * 80)
    print("✅ RECALCULACIÓN COMPLETADA")
    print("=" * 80)
    
except Exception as e:
    print(f"\n❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()
