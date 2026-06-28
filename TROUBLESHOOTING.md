# 🛠️ Troubleshooting - Limpieza de Tipos de Datos

## Problema 1: Tests No Pasan

**Error**: `ModuleNotFoundError: No module named 'src'`
```bash
cd c:\mundial_app_nueva
python -m pytest tests/test_data_integrity.py -v
```

**Error**: `pytest not installed`
```bash
pip install pytest pytest-mock
```

---

## Problema 2: StreamlitMixedNumericTypesError Persiste

**Paso 1**:
```bash
python validate_admin_changes.py
```

**Paso 2**: Si falla, ejecutar:
```bash
python fix_admin_data_types.py
python fix_admin_jugados.py
```

**Paso 3**: Verificar tipos
```python
from src.data_layer import DataLayer
df = data_layer.obtener_partidos()
print(df['goles_local'].dtype)  # Debe ser int64
```

---

## Problema 3: Botones No Muestran "Guardar"

```bash
python fix_admin_data_types.py
python fix_admin_jugados.py
grep "💾 Guardar" src/ui/admin.py
```

---

## Problema 4: Admin.py Tiene Syntax Error

```bash
python -m py_compile src/ui/admin.py
```

Si falla, restaurar:
```bash
python fix_admin_data_types.py
python fix_admin_jugados.py
```

---

## Problema 5: Tests Fallan con Traceback

```bash
python -m pytest tests/test_data_integrity.py -v --tb=long
```

---

## ✅ Verificación Rápida (5 min)

```bash
# Tests
python -m pytest tests/test_data_integrity.py -v

# Validación
python validate_admin_changes.py

# Sintaxis
python -m py_compile src/ui/admin.py

# Cambios
grep "int(goles_local_raw)" src/ui/admin.py
grep "💾 Guardar" src/ui/admin.py
```

Si todo pasa: ✅ SISTEMA LISTO
