"""
conftest.py - Configuración de pytest y fixtures compartidas
"""

import pytest
import pandas as pd
from unittest.mock import Mock, MagicMock
import sys
from pathlib import Path

# Añadir el directorio raíz al path para importar módulos del proyecto
sys.path.insert(0, str(Path(__file__).parent.parent))


class MockSupabaseResponse:
    """Mock de respuesta de Supabase"""
    def __init__(self, data):
        self.data = data


class MockSupabaseClient:
    """Mock del cliente de Supabase"""
    def __init__(self, mock_data=None):
        self.mock_data = mock_data or {}
    
    def table(self, table_name):
        """Mock del método table()"""
        return MockTableBuilder(self.mock_data.get(table_name, []))


class MockTableBuilder:
    """Builder para queries de tabla"""
    def __init__(self, data):
        self.data = data
        self._filters = []
    
    def select(self, *args):
        """Mock del método select()"""
        return self
    
    def eq(self, column, value):
        """Mock del método eq()"""
        return self
    
    def neq(self, column, value):
        """Mock del método neq()"""
        return self
    
    def execute(self):
        """Mock del método execute()"""
        return MockSupabaseResponse(self.data)


@pytest.fixture
def mock_supabase_client_with_partidos():
    """
    Fixture que proporciona un mock de cliente Supabase con datos de partidos.
    Los goles vienen como FLOAT (simula el problema real de Supabase).
    """
    mock_data = {
        'partidos': [
            {
                'id': 1,
                'equipo_local_id': 101,
                'equipo_visitante_id': 102,
                'goles_local': 2.0,  # ⚠️ Viene como float
                'goles_visitante': 1.0,  # ⚠️ Viene como float
                'estado': 'Jugado',
                'grupo': 'A'
            },
            {
                'id': 2,
                'equipo_local_id': 103,
                'equipo_visitante_id': 104,
                'goles_local': 0.0,  # ⚠️ Viene como float
                'goles_visitante': 3.0,  # ⚠️ Viene como float
                'estado': 'Jugado',
                'grupo': 'A'
            },
            {
                'id': 3,
                'equipo_local_id': 105,
                'equipo_visitante_id': 106,
                'goles_local': None,  # ⚠️ Viene como NULL
                'goles_visitante': None,  # ⚠️ Viene como NULL
                'estado': 'Pendiente',
                'grupo': 'B'
            },
        ],
        'equipos': [
            {'id': 101, 'nombre': 'Argentina'},
            {'id': 102, 'nombre': 'Brasil'},
            {'id': 103, 'nombre': 'Colombia'},
            {'id': 104, 'nombre': 'Uruguay'},
            {'id': 105, 'nombre': 'Paraguay'},
            {'id': 106, 'nombre': 'Perú'},
        ]
    }
    
    client = MockSupabaseClient(mock_data)
    return client


@pytest.fixture
def data_layer(mock_supabase_client_with_partidos):
    """
    Fixture que proporciona una instancia de DataLayer con mock de Supabase.
    """
    from src.data_layer import DataLayer
    return DataLayer(mock_supabase_client_with_partidos)
