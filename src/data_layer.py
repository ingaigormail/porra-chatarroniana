"""
CAPA DE DATOS CON TIPADO ESTRICTO - Elimina StreamlitMixedNumericTypesError
Tipado estricto AL MOMENTO DE RECIBIR datos de Supabase.
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict


class DataLayer:
    """Capa de datos que garantiza tipado correcto de campos numéricos."""
    
    # Campos que DEBEN ser int (con su default si NULL)
    CAMPOS_INT = {
        'goles_local': 0,
        'goles_visitante': 0,
        'puntos': 0,
        'puntos_finales': 0,
        'puntos_provisionales': 0,
        'id': None,
        'usuario_id': None,
        'partido_id': None,
        'equipo_id': None,
        'equipo_local_id': None,
        'equipo_visitante_id': None,
        'posicion': 0,
    }
    
    def __init__(self, client):
        self.client = client
    
    def _tipificar_dataframe(self, df: pd.DataFrame, campos_especificos: Optional[Dict] = None) -> pd.DataFrame:
        """Tipifica DataFrame: NaN→0, float→int"""
        if df.empty:
            return df
        
        df = df.copy()
        campos = campos_especificos or self.CAMPOS_INT
        
        for campo, default_value in campos.items():
            if campo not in df.columns:
                continue
            
            try:
                if default_value is not None:
                    df[campo] = df[campo].fillna(default_value)
                df[campo] = df[campo].astype(int)
            except (ValueError, TypeError):
                pass
        
        return df
    
    def obtener_partidos(self) -> pd.DataFrame:
        """Obtiene partidos CON tipado estricto (int para goles)"""
        response = self.client.table('partidos').select('*').execute()
        df = pd.DataFrame(response.data)
        
        if df.empty:
            return df
        
        campos_partidos = {
            'goles_local': 0,
            'goles_visitante': 0,
            'id': None,
            'equipo_local_id': None,
            'equipo_visitante_id': None,
        }
        
        df = self._tipificar_dataframe(df, campos_partidos)
        
        # Obtener nombres
        equipos_response = self.client.table('equipos').select('id', 'nombre').execute()
        if equipos_response.data:
            equipos_df = pd.DataFrame(equipos_response.data)
            equipos_dict = dict(zip(equipos_df['id'], equipos_df['nombre']))
            df['equipo_local_nombre'] = df['equipo_local_id'].map(equipos_dict)
            df['equipo_visitante_nombre'] = df['equipo_visitante_id'].map(equipos_dict)
        
        return df
    
    def obtener_quinielas(self) -> pd.DataFrame:
        """Obtiene quinielas CON tipado estricto"""
        response = self.client.table('quinielas').select('*').execute()
        df = pd.DataFrame(response.data)
        
        if df.empty:
            return df
        
        campos = {
            'id': None,
            'usuario_id': None,
            'partido_id': None,
            'puntos_provisionales': 0,
            'puntos_finales': 0,
        }
        
        return self._tipificar_dataframe(df, campos)
    
    def obtener_clasificacion(self) -> pd.DataFrame:
        """Obtiene clasificación CON tipado estricto"""
        response = self.client.table('usuarios_clasificacion').select('*').execute()
        df = pd.DataFrame(response.data)
        
        if df.empty:
            return df
        
        campos = {
            'posicion': 0,
            'puntos': 0,
            'usuario_id': None,
        }
        
        return self._tipificar_dataframe(df, campos)
    
    def guardar_resultado(self, partido_id: int, goles_local: int, goles_visitante: int) -> bool:
        """Guarda resultado ASEGURANDO que son int"""
        try:
            goles_local = int(goles_local)
            goles_visitante = int(goles_visitante)
            
            self.client.table('partidos').update({
                'goles_local': goles_local,
                'goles_visitante': goles_visitante,
                'estado': 'Jugado',
            }).eq('id', partido_id).execute()
            
            print(f"✅ ESCRITURA EN BD: Partido {partido_id} → {goles_local}-{goles_visitante} (tipos: {type(goles_local).__name__}, {type(goles_visitante).__name__})")
            return True
        except Exception as e:
            print(f"❌ Error: {e}")
            return False


_instance: Optional[DataLayer] = None

def get_data_layer(client=None) -> DataLayer:
    """Obtiene instancia global de DataLayer"""
    global _instance
    if _instance is None:
        if client is None:
            raise ValueError("Se requiere cliente Supabase")
        _instance = DataLayer(client)
    return _instance
