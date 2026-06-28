"""
Normalizador de Tipos para DataFrames de Supabase
================================================================================
Problema: Supabase devuelve números como floats (2.0, 1.0) o NULL/NaN
Solución: Convertir automáticamente campos numéricos a int basado en:
  1. Nombre de columna (patrón matching)
  2. Tipo de datos detectado
  3. Valores presentes en la columna

POLÍTICA GLOBAL:
- Cualquier campo que contenga "gol", "punto", "puntos" → int
- Si tiene NaN, convertir a 0
- Si viene como float (2.0), convertir a int (2)
- Independiente del nombre exacto de la columna
================================================================================
"""

import pandas as pd
import numpy as np


class TypeNormalizer:
    """Normaliza tipos de datos de DataFrames de Supabase"""
    
    # Patrones de columnas que SIEMPRE deben ser int
    NUMERIC_INTEGER_PATTERNS = [
        'gol',        # goles_local, goles_visitante, goles_apostados, etc.
        'punto',      # puntos, puntos_finales, puntos_provisionales, etc.
        'id',         # id, usuario_id, partido_id, equipo_id, etc.
        'posicion',   # posicion en ranking
        'numero',     # numero, numero_camiseta, etc.
        'cantidad',   # cantidad de usuarios, etc.
        'ronda',      # ronda del torneo
    ]
    
    # Patrones que pueden ser float
    NUMERIC_FLOAT_PATTERNS = [
        'promedio',
        'porcentaje',
        'probabilidad',
        'rating',
    ]
    
    @staticmethod
    def should_be_integer(column_name):
        """
        Determina si una columna debería ser int basado en su nombre
        
        Args:
            column_name (str): Nombre de la columna
            
        Returns:
            bool: True si debería ser int
        """
        col_lower = column_name.lower()
        
        # Revisar patrones que DEBEN ser int
        for pattern in TypeNormalizer.NUMERIC_INTEGER_PATTERNS:
            if pattern in col_lower:
                return True
        
        # Si matchea float pattern, NO es int
        for pattern in TypeNormalizer.NUMERIC_FLOAT_PATTERNS:
            if pattern in col_lower:
                return False
        
        return False
    
    @staticmethod
    def normalize_dataframe(df):
        """
        Normaliza tipos de datos en un DataFrame
        
        Estrategia:
        1. Detecta columnas numéricas por nombre
        2. Convierte NaN a 0
        3. Convierte float a int
        
        Args:
            df (pd.DataFrame): DataFrame de Supabase
            
        Returns:
            pd.DataFrame: DataFrame con tipos normalizados
        """
        if df.empty:
            return df
        
        df = df.copy()  # No modificar el original
        
        for col in df.columns:
            if TypeNormalizer.should_be_integer(col):
                try:
                    # Convertir NaN a 0
                    df[col] = df[col].fillna(0)
                    
                    # Convertir a int (float → int)
                    df[col] = df[col].astype(int)
                    
                except (ValueError, TypeError) as e:
                    # Si no se puede convertir, dejar como está
                    pass
        
        return df
    
    @staticmethod
    def normalize_value(value, column_name):
        """
        Normaliza un valor individual basado en el nombre de la columna
        
        Útil cuando necesitas un solo valor antes de pasarlo a Streamlit
        
        Args:
            value: Valor a normalizar
            column_name (str): Nombre de la columna
            
        Returns:
            int o valor original: Valor normalizado
        """
        if not TypeNormalizer.should_be_integer(column_name):
            return value
        
        # Si es None/NaN, retornar 0
        if value is None or (isinstance(value, float) and np.isnan(value)):
            return 0
        
        # Si es float, convertir a int
        if isinstance(value, float):
            return int(value)
        
        # Si ya es int, retornar como está
        if isinstance(value, int):
            return value
        
        # Intentar convertir
        try:
            return int(value)
        except:
            return value
    
    @staticmethod
    def normalize_row_values(row_dict):
        """
        Normaliza todos los valores en un diccionario (fila del DataFrame)
        
        Args:
            row_dict (dict): Diccionario con {columna: valor}
            
        Returns:
            dict: Diccionario con valores normalizados
        """
        normalized = {}
        for key, value in row_dict.items():
            normalized[key] = TypeNormalizer.normalize_value(value, key)
        
        return normalized


# ============================================================================
# FUNCIONES DE CONVENIENCIA PARA USO EN TODA LA APP
# ============================================================================

def normalize_df(df):
    """Alias corto para normalizar DataFrame"""
    return TypeNormalizer.normalize_dataframe(df)


def normalize_val(value, column_name):
    """Alias corto para normalizar valor individual"""
    return TypeNormalizer.normalize_value(value, column_name)


def normalize_row(row_dict):
    """Alias corto para normalizar fila (diccionario)"""
    return TypeNormalizer.normalize_row_values(row_dict)
