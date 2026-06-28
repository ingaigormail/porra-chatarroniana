# test_grupo.py
import sys
import os

# Añadir la ruta del proyecto al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.database import Database

# Configurar secrets para prueba (si es necesario)
# Si estás en local, asegúrate de tener .streamlit/secrets.toml

print("="*50)
print("📊 CLASIFICACIÓN GRUPO A (FIFA 2026)")
print("="*50)

db = Database()

# Probar Grupo A
df = db.calcular_clasificacion_grupo('A')

if not df.empty:
    print(df[['posicion', 'nombre', 'puntos', 'pj', 'ganados', 'empatados', 'perdidos', 'gf', 'gc', 'dg']].to_string(index=False))
else:
    print("❌ No hay datos para el Grupo A")

# Verificar el orden esperado según resultados reales
print("\n" + "="*50)
print("🔍 VERIFICACIÓN MANUAL")
print("="*50)
print("Resultados reales del Grupo A:")
print("  • México: 3 victorias (9 puntos) → 1º")
print("  • Sudáfrica: 1 victoria, 1 empate, 1 derrota (4 puntos) → 2º")
print("  • Corea del Sur: 1 victoria, 0 empates, 2 derrotas (3 puntos) → 3º")
print("  • República Checa: 0 victorias, 1 empate, 2 derrotas (1 punto) → 4º")
print("\n✅ El orden debería ser: México → Sudáfrica → Corea del Sur → República Checa")