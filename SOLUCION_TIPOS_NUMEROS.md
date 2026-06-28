# 📊 SOLUCIÓN ESTRUCTURAL: NORMALIZACIÓN DE TIPOS NUMÉRICOS

## 🔍 ANÁLISIS: RAÍZ DEL PROBLEMA

**El problema exacto:**

1. **Supabase devuelve números como floats:** `goles_local: 2.0` (no 2)
2. **Pandas convierte a float64:** `dtype=float64` en lugar de `int64`
3. **NULLs se vuelven NaN:** Cuando no hay valor, es `NaN` en lugar de `None`
4. **Streamlit requiere tipos consistentes:** Todos los parámetros de `st.number_input()` deben ser del mismo tipo

**Línea problemática en `src/services/partidos.py:12`:**
```python
df = pd.DataFrame(response.data)
# ❌ Sin validación de tipos
# ❌ Números vienen como float64
# ❌ NULLs se convierten en NaN
```

---

## ✅ SOLUCIÓN: TypeNormalizer

**Archivo:** `src/utils/type_normalizer.py` (YA CREADO)

### Características Clave

1. **Detección Dinámica:** Analiza el nombre de la columna
   - Si contiene "gol" → int
   - Si contiene "punto" → int
   - Si contiene "id" → int
   - Extensible sin cambiar código

2. **Conversión Robusta:**
   - `2.0` → `2` (int)
   - `None` → `0`
   - `NaN` → `0`
   - `"3"` → `3`

3. **Métodos Disponibles:**
   - `normalize_df(dataframe)` - Normaliza todo el DF
   - `normalize_val(valor, nombre_columna)` - Normaliza un valor
   - `normalize_row(diccionario)` - Normaliza una fila

---

## 🚀 CÓMO USARLO

### Mejor práctica: Normalizar en el Servicio (BD)

**En `src/services/partidos.py` línea 22:**

```python
from src.utils.type_normalizer import normalize_df

def obtener_partidos(self):
    response = self.client.table('partidos').select('*').execute()
    df = pd.DataFrame(response.data)
    df = normalize_df(df)  # ← AQUÍ!
    # ... resto del código ...
    return df
```

---

## 📋 IMPLEMENTACIÓN NECESARIA

Aplicar `normalize_df()` en:

1. `src/services/partidos.py` - `obtener_partidos()`
2. `src/services/clasificacion.py` - `obtener_clasificacion()`
3. `src/services/quiniela.py` - `obtener_apuestas_usuario()`
4. Otros servicios que retornen DataFrames

---

## ✨ BENEFICIOS

- ✅ Un cambio en un lugar (el servicio)
- ✅ Afecta toda la app automáticamente
- ✅ Si cambias nombre de columna, sigue funcionando
- ✅ Si agregas nueva columna numérica, detecta automáticamente
- ✅ No hay que tocar la UI (Streamlit)
- ✅ Resuelve el problema de raíz, no es un parche

---

**La solución ya está creada. Ahora necesita ser aplicada en los servicios.**
