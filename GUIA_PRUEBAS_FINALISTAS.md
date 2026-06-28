# 🏆 GUÍA COMPLETA: PRUEBAS DE FINALISTAS

## 📊 Resumen de la Prueba Ejecutada

✅ **La prueba se ejecutó exitosamente el 26/6/2026 a las 12:32**

Resultado de la ejecución:
- **11 usuarios** en el sistema
- **48 equipos** disponibles
- **1 apuesta** de finalista creada y validada
- **Puntos calculados correctamente**

---

## 🚀 CÓMO FUNCIONAN LOS FINALISTAS

### 1️⃣ **Estructura de la Funcionalidad**

La funcionalidad de **apostar finalistas** tiene 3 componentes:

| Componente | Ubicación | Función |
|-----------|-----------|---------|
| **QuinielaService** | `src/services/quiniela.py` | Guarda apuestas y calcula puntos |
| **Admin Panel** | `src/ui/admin.py` | Interfaz para gestionar finalistas |
| **Database** | `src/database.py` | Conecta con Supabase |

---

## 📋 PASO 1: Entender el Sistema de Puntos

### Cálculo de Puntos de Finalistas

```
┌─────────────────────────────────────────────┐
│         RESULTADO FINAL (REAL)              │
│     Equipo A  🏆  vs  🏆  Equipo B          │
└─────────────────────────────────────────────┘

Tu apuesta: Equipo X vs Equipo Y

┌─────────────────────────────────────────────┐
│  ✅ AMBOS ACERTADOS (X=A y Y=B)             │
│  ➡️  PUNTOS: 10 puntos 🥇                   │
├─────────────────────────────────────────────┤
│  ✅ UNO ACERTADO (X=A o Y=B)                │
│  ➡️  PUNTOS: 4 puntos 🥈                    │
├─────────────────────────────────────────────┤
│  ❌ NINGUNO ACERTADO                        │
│  ➡️  PUNTOS: 0 puntos                       │
└─────────────────────────────────────────────┘
```

---

## 🧪 PASO 2: Ejecutar el Script de Pruebas

### Comando para ejecutar las pruebas:

```bash
python test_finalistas_guia.py
```

### Qué hace el script:

1. ✅ **PASO 1**: Obtiene usuarios y equipos de la BD
2. ✅ **PASO 2**: Simula una apuesta de finalistas
3. ✅ **PASO 3**: Verifica que la apuesta se guardó
4. ✅ **PASO 4**: Calcula puntos (simula que Corea del Sur y Canada son los finalistas)
5. ✅ **PASO 5**: Muestra los puntos asignados a cada usuario

### Resultado esperado:

```
Usuario              Puntos     Estado
---------------------------------------------
Bro                  10         🥇 Acertó ambos
```

---

## 🎯 PASO 3: Usar el Admin Panel en la Aplicación

### 3.1 Activar la Funcionalidad de Finalistas

1. Abre la aplicación Streamlit
2. Inicia sesión con usuario **admin** (contraseña: `admin`)
3. Ve a la pestaña **"🔧 Admin"**
4. Busca la sección: **"🏆 Gestión de Apuesta de Finalistas"**
5. Marca la casilla: ✅ **"Activar apuesta de finalistas"**
6. Haz clic en **"Guardar estado finalistas"**

### 3.2 Permitir que Usuarios Apuesten

En la sección **"🏆 Calcular Finalistas"** (arriba):

1. Selecciona **Finalista 1**: (ej. Brasil)
2. Selecciona **Finalista 2**: (ej. Argentina)
3. Verás dos tablas:
   - ✅ **"Usuarios que YA apostaron"** - muestra sus apuestas
   - ⚠️ **"Usuarios que AÚN NO han apostado"** - avísalos

---

## 🔄 PASO 4: Flujo Completo de Prueba

### Escenario: Probar que todo funciona

**4.1 - Crear una apuesta (como usuario)**
```
1. Inicia sesión como "Bro"
2. Ve a "👤 Mi Ficha" o donde esté la opción de apostar finalistas
3. Selecciona dos equipos y haz clic en "Apostar"
```

**4.2 - Verificar en base de datos**
```python
# En una terminal Python o script:
python test_finalistas_guia.py
# Veras tu apuesta en PASO 3
```

**4.3 - Calcular los puntos reales**
```
1. Admin -> "🔧 Admin" tab
2. "🏆 Calcular Finalistas"
3. Selecciona los 2 equipos ganadores REALES
4. Revisa quién apostó qué
5. Haz clic en "✅ Calcular y Aplicar Puntos de Finalistas"
```

**4.4 - Verificar puntos asignados**
```
1. Ve a "🏆 Clasificación"
2. Verás los puntos actualizados para cada usuario
```

---

## 🔧 PASO 5: Métodos Clave del Sistema

### En `src/services/quiniela.py`:

```python
# 1. Guardar una apuesta de finalistas
def apostar_finalistas(self, usuario_id, finalista_1_id, finalista_2_id):
    # Guarda o actualiza la apuesta de un usuario
    
# 2. Calcular los puntos
def calcular_puntos_finalistas(self, finalista_1_real, finalista_2_real):
    # Recorre todas las apuestas y asigna puntos
    # finalista_1_real = ID del equipo ganador 1
    # finalista_2_real = ID del equipo ganador 2
```

### En `src/database.py`:

```python
# Desde app o admin, llamarás así:
db.apostar_finalistas(usuario_id, equipo_1_id, equipo_2_id)
db.calcular_puntos_finalistas(equipo_1_id, equipo_2_id)
```

---

## ✅ VERIFICACIÓN MANUAL

### Para verificar que todo está guardado correctamente:

#### A través de SQL (Supabase):

```sql
-- Ver todas las apuestas de finalistas
SELECT id, usuario_id, finalista_1_id, finalista_2_id, puntos 
FROM finalistas_apostados;

-- Ver apuestas de un usuario específico
SELECT * FROM finalistas_apostados 
WHERE usuario_id = 1;
```

#### A través del Script Python:

```python
from src.database import Database
db = Database()

# Ver todas las apuestas
apuestas = db.client.table('finalistas_apostados').select('*').execute()
print(apuestas.data)
```

---

## 🐛 Solución de Problemas

### ❌ Error: "No se puede conectar a Supabase"

**Solución:**
1. Verifica que tengas el archivo `.streamlit/secrets.toml`
2. Asegúrate de que tiene las claves correctas de Supabase
3. Reinicia la aplicación

### ❌ Error: "No hay apuestas encontradas"

**Solución:**
1. Primero crea una apuesta (PASO 2)
2. Luego calcula los puntos (PASO 4)
3. Ejecuta `python test_finalistas_guia.py` nuevamente

### ❌ Los puntos no se actualizan en la clasificación

**Solución:**
1. Ve a Admin -> "📊 Recalcular Clasificación General"
2. Haz clic en "🔄 Recalcular Clasificación"
3. Limpia el caché: `st.cache_data.clear()`

---

## 📌 Checklist de Prueba Completa

```
PREPARACIÓN:
☐ Tienes archivo .streamlit/secrets.toml
☐ Tienes conexión a Supabase

PRUEBAS BÁSICAS:
☐ Ejecutaste: python test_finalistas_guia.py
☐ El script mostró 11 usuarios
☐ El script mostró 48 equipos
☐ Se guardó una apuesta
☐ Se calcularon los puntos (10 puntos)

PRUEBAS EN APP:
☐ Iniciaste sesión en la app
☐ Viste la pestaña "🔧 Admin"
☐ Activaste "Gestión de Apuesta de Finalistas"
☐ Seleccionaste 2 finalistas en "Calcular Finalistas"
☐ Viste la tabla de usuarios que apostaron
☐ Hiciste clic en "Calcular y Aplicar Puntos"
☐ Verificaste puntos en "Clasificación"

TODO FUNCIONA: ✅
```

---

## 🎓 Resumen Rápido

### Para usuarios normales:
1. Espera a que el admin active los finalistas
2. Ve a donde esté la opción de apostar finalistas
3. Selecciona 2 equipos
4. Espera a que se juegue la final
5. Gana puntos si acertaste

### Para el admin:
1. Ejecuta: `python test_finalistas_guia.py` (para verificar el sistema)
2. Ve a Admin Panel
3. Activa "Gestión de Apuesta de Finalistas"
4. Deja que los usuarios apuesten
5. Cuando sepas los finalistas reales, ve a "Calcular Finalistas"
6. Selecciona los 2 equipos ganadores
7. Haz clic en "Calcular y Aplicar Puntos"
8. Los puntos se asignan automáticamente

---

## 📞 Próximos Pasos

Si encuentras problemas:
1. Revisa el archivo `test_finalistas_guia.py` para entender la lógica
2. Consulta `src/services/quiniela.py` líneas 224-286
3. Consulta `src/ui/admin.py` líneas 300-505

Si todo funciona correctamente:
✅ **La funcionalidad de finalistas está lista para usar**

---

**Última actualización:** 26/6/2026 - 12:32 GMT+2
