# 📖 GUÍA DE USO - ADMIN MUNDIAL 2026

## ✅ FLUJO COMPLETO AUTOMATIZADO

Cuando ingresas un resultado de un partido, el sistema **HACE TODO AUTOMÁTICAMENTE**:

```
1. Tú ingresas goles en Admin
   ↓
2. Presionas "Guardar"
   ↓
3. Partido cambia a "Jugado" automáticamente
   ↓
4. Python recalcula:
   - Puntos de equipos ✅
   - Puntos de usuarios (selecciones) ✅
   - Clasificación general ✅
   - Gráficos ✅
   ↓
5. Usuarios ven cambios en tiempo real
```

---

## 📋 PASO A PASO - INGRESAR RESULTADOS

### 1️⃣ Abre la App
```
URL: Tu app de Streamlit
```

### 2️⃣ Inicia Sesión como Admin
```
Usuario: luis (o tu usuario admin)
Contraseña: tu contraseña
```

### 3️⃣ Ve a la Pestaña "🔧 Admin"
```
Arriba de la pantalla
```

### 4️⃣ Busca "📝 Partidos Pendientes"
```
Sección donde están todos los partidos sin jugar
```

### 5️⃣ Ingresa el Resultado
```
Para cada partido pendiente:
- Columna "GL" (Goles Local): ingresa número (0-10)
- Columna "GV" (Goles Visitante): ingresa número (0-10)
- Si hay prórroga: selecciona "Sí" en columna "Prórroga"
- Click botón "💾" (guardar en esa fila)
```

### 6️⃣ Confirma que Guardó
```
Verás: ✅ Mensaje de éxito
       "✅ 2-1" o el resultado que ingresaste
```

### 7️⃣ ¡LISTO!
```
El sistema hace TODO automáticamente:
- Partido pasa a "Jugado" ✅
- Puntos de equipos se actualizan ✅
- Puntos de usuarios se calculan ✅
- Clasificación se actualiza ✅
- Usuarios ven cambios ✅
```

---

## 📊 QUÉ CAMBIA DESPUÉS DE GUARDAR

Cuando guardas un resultado, automáticamente se actualiza:

### 1. **Puntos de Equipos**
```
Si gana:     +3 puntos
Si empata:   +1 punto cada uno
Si pierde:   0 puntos
```

### 2. **Puntos de Usuarios (por selecciones)**
```
Si su equipo ganó:   +3 puntos
Si su equipo empató: +1 punto
Si su equipo perdió: 0 puntos
```

### 3. **Clasificación General**
```
Se suma todo automáticamente:
- Puntos por selecciones
- Puntos por apuestas (si activas)
- Puntos por finalistas (si activas)
```

### 4. **Gráficos**
```
Se actualizan automáticamente:
- Gráfico de puntos por usuario
- Gráfico de progresión
```

---

## 🎯 ACTIVAR APUESTAS (Opcional)

Cuando quieras que los usuarios comiencen a apostar:

### 1. Ve a "🎯 Gestión de Apuestas"
```
En Admin Panel
```

### 2. Selecciona un Partido
```
De la lista de partidos de eliminatoria
```

### 3. Elige Tipo
```
- "quiniela": Usuarios apuestan 1/X/2
- "porra": Usuarios apuestan resultado exacto (goles)
- "ninguno": Sin apuestas (desactivado)
```

### 4. Marca "Abierto"
```
Checkbox para habilitar apuestas
```

### 5. Click "💾 Guardar"
```
¡Listo! Usuarios verán la opción de apostar
```

---

## ⚠️ NOTAS IMPORTANTES

### ✅ TODO ES AUTOMÁTICO
```
Cuando guardas un resultado, Python hace TODOS los cálculos.
NO necesitas hacer clic en "Calcular" ni "Validar".
```

### ✅ SIN APUESTAS POR DEFECTO
```
Las apuestas están DESACTIVADAS para usuarios.
Actívalas desde Admin cuando quieras.
```

### ✅ USUARIOS NO VEN RESULTADOS PENDIENTES
```
Si ingresas un resultado incorrecto, puedes editarlo.
Ve a "📊 Partidos Jugados - Editar Resultado"
Cambias el resultado y Python recalcula todo.
```

### ✅ TODO EN TIEMPO REAL
```
Cuando los usuarios recargan la página, ven los cambios.
Si entran en la app mientras guardas, verán la actualización.
```

---

## 🧪 EJEMPLO PRÁCTICO

### Escenario:
```
- Partido: México vs Suiza (pendiente)
- México tenía 9 puntos
- Suiza tenía 7 puntos
- Usuario "Luis" eligió a México
```

### Tú haces:
```
1. Admin → Partidos Pendientes
2. Ingresa: México 2 - 1 Suiza
3. Click "💾"
```

### Sistema automáticamente:
```
1. México: 9 → 12 puntos (+3 ganó) ✅
2. Suiza: 7 → 7 puntos (0 perdió) ✅
3. Luis: suma +3 por México ✅
4. Clasificación de Luis se actualiza ✅
5. Gráficos se actualizan ✅
```

### Luis ve en su teléfono:
```
- Puntos aumentaron
- Clasificación actualizó
- Vio que México ganó
```

---

## 🔗 RESUMEN

```
ACCIONES TÚ (Admin):
1. Ir a Partidos Pendientes
2. Ingresar goles
3. Guardar

ACCIONES SISTEMA (Automático):
1. Marcar como Jugado
2. Calcular puntos equipos
3. Calcular puntos usuarios
4. Actualizar clasificación
5. Actualizar gráficos

RESULTADO:
Usuarios ven todo actualizado en tiempo real
```

---

**¿Preguntas? El sistema está listo. ¡Adelante!** 🚀
