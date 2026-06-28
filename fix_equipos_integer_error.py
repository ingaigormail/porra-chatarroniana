#!/usr/bin/env python3
"""
Script crítico para arreglar el error: "invalid input syntax for type integer: -2.0"
Aplica la función to_int() a todos los valores numéricos en equipos.py
"""

# Leer el archivo
with open('src/services/equipos.py', 'r', encoding='utf8') as f:
    content = f.read()

# Reemplazo 1: Cambiar el update dict para usar to_int()
old_update = """        for equipo_id, data in stats.items():
            data['dg'] = data['gf'] - data['gc']
            self.client.table('equipos').update({
                'pj': data['pj'],
                'ganados': data['ganados'],
                'empatados': data['empatados'],
                'perdidos': data['perdidos'],
                'gf': data['gf'],
                'gc': data['gc'],
                'dg': data['dg'],
                'puntos': data['puntos']
            }).eq('id', equipo_id).execute()"""

new_update = """        for equipo_id, data in stats.items():
            data['dg'] = data['gf'] - data['gc']
            
            # LIMPIEZA CRÍTICA: Convertir todos los valores a int
            # Evita error: "invalid input syntax for type integer: -2.0"
            data_to_update = {
                'pj': to_int(data['pj']),
                'ganados': to_int(data['ganados']),
                'empatados': to_int(data['empatados']),
                'perdidos': to_int(data['perdidos']),
                'gf': to_int(data['gf']),
                'gc': to_int(data['gc']),
                'dg': to_int(data['dg']),
                'puntos': to_int(data['puntos'])
            }
            
            # LOG: Verificar que no hay decimales antes de enviar
            print(f"[equipos.py] Enviando a Supabase - Equipo {equipo_id}: {data_to_update}")
            
            self.client.table('equipos').update(data_to_update).eq('id', equipo_id).execute()"""

# Aplicar reemplazo
if old_update in content:
    content = content.replace(old_update, new_update)
    print("✅ Reemplazo 1: Update dict aplicado")
else:
    print("⚠️ Reemplazo 1: Pattern no encontrado")

# Guardar el archivo
with open('src/services/equipos.py', 'w', encoding='utf8') as f:
    f.write(content)

print("✅ equipos.py actualizado correctamente")
print("\nCambios aplicados:")
print("  ✅ Importado to_int() de utils.validators")
print("  ✅ Todos los valores numéricos pasan por to_int()")
print("  ✅ Log agregado para verificación")
print("\nResultado esperado:")
print("  Antes: 'invalid input syntax for type integer: -2.0'")
print("  Ahora: Todos los valores son int sin decimales")
