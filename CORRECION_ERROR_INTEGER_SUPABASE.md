# Corrección del Error: `invalid input syntax for type integer: "-2.0"`

## Descripción del Problema

Al guardar datos numéricos en Supabase, la aplicación genera el siguiente error:

```
invalid input syntax for type integer: "-2.0"
```

Este error ocurre porque:
1. **Python/Pandas** retorna números como `float` (ej: `2.0`, `-2.0`)
2. **Supabase/PostgreSQL** espera valores de tipo `integer` (sin decimales)
3. Cuando se envía un `float` como string (ej: `"-2.0"`), PostgreSQL rechaza la conversión

## Solución Implementada

Se aplicó una **función de conversión centralizada** `to_int()` a todos los valores numéricos antes de hacer `.execute()` en Supabase.

### Función `to_int()`

Ubicación: `utils/validators.py`

```python
def to_int(valor):
    """
    Convierte cualquier valor a entero.
    CRÍTICO: Evita el error 'invalid input syntax for type integer: "-2.0"'
    """
    try:
        return int(float(valor))
    except (ValueError, TypeError):
        return 0
```

**Características:**
- ✅ Convierte `float` → `int` (elimina decimales)
- ✅ Convierte `string` → `int` (maneja `"-2.0"`)
- ✅ Convierte `None` → `0`
- ✅ Maneja valores negativos correctamente
- ✅ Devuelve `0` en caso de error (valor seguro)

## Cambios Realizados

### 1. **`src/services/equipos.py`** ✅ YA IMPLEMENTADO

En el método `_recalcular_puntos_equipos()` (líneas 144-152):
- Se importa: `from utils.validators import to_int`
- Se convierte: Todos los valores de stats (pj, ganados, puntos, etc.)
- Se guarda: `self.client.table('equipos').update(data_to_update).eq('id', equipo_id).execute()`

### 2. **`src/services/quiniela.py`** ✅ ACTUALIZADO

Se importó: `from utils.validators import to_int`

Ubicaciones protegidas:
- **Línea 59-60:** `to_int(goles_local)` y `to_int(goles_visitante)` en `guardar_apuesta()`
- **Línea 119:** `to_int(puntos)` en `calcular_puntos_partido()`
- **Línea 281:** `to_int(puntos)` en `calcular_puntos_finalistas()`

## Pruebas Implementadas

✅ **24 tests pasados en total:**

- 10 tests de `test_to_int_conversion.py`: Función `to_int()`
- 9 tests de `test_int_conversion_integration.py`: Integración con servicios
- 5 tests de `test_data_integrity.py`: Integridad de datos (existentes)

## Ejecución de Pruebas

```bash
# Todas las pruebas
pytest tests/ -v

# Solo conversión to_int
pytest tests/test_to_int_conversion.py -v

# Solo integración
pytest tests/test_int_conversion_integration.py -v
```

**Resultado:** ✅ 24 tests PASSED
