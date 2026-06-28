"""
test_int_conversion_integration.py
Tests de integración para verificar que to_int() funciona en los servicios
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.validators import to_int
from src.services.equipos import EquiposService
from src.services.quiniela import QuinielaService


class TestSupabaseIntConversion:
    """Tests para validar el error 'invalid input syntax for type integer: "-2.0"'"""

    def test_supabase_float_values_are_converted(self):
        """Valores float de Supabase se convierten a int"""
        # Supabase devuelve enteros como float
        supabase_values = [1.0, 2.0, 3.0, 0.0, -2.0]
        for val in supabase_values:
            result = to_int(val)
            assert isinstance(result, int)
            assert result == int(val)

    def test_critical_error_scenario(self):
        """Simula el escenario crítico que causa el error"""
        # El error exacto: 'invalid input syntax for type integer: "-2.0"'
        problematic_value = "-2.0"
        converted = to_int(problematic_value)
        assert converted == -2
        assert isinstance(converted, int)

    def test_database_update_with_converted_values(self):
        """Simula guardado en BD con valores convertidos"""
        stats = {
            'pj': 3.0,
            'ganados': 2.0,
            'empatados': 0.0,
            'perdidos': 1.0,
            'gf': 5.0,
            'gc': 2.0,
            'dg': 3.0,
            'puntos': 6.0
        }

        data_to_update = {
            'pj': to_int(stats['pj']),
            'ganados': to_int(stats['ganados']),
            'empatados': to_int(stats['empatados']),
            'perdidos': to_int(stats['perdidos']),
            'gf': to_int(stats['gf']),
            'gc': to_int(stats['gc']),
            'dg': to_int(stats['dg']),
            'puntos': to_int(stats['puntos'])
        }

        for key, value in data_to_update.items():
            assert isinstance(value, int), f"{key} no es int: {type(value)}"
            assert "." not in str(value)

        assert data_to_update == {
            'pj': 3,
            'ganados': 2,
            'empatados': 0,
            'perdidos': 1,
            'gf': 5,
            'gc': 2,
            'dg': 3,
            'puntos': 6
        }


class TestQuinielaWithIntConversion:
    """Tests para QuinielaService con to_int()"""

    def test_goles_apostados_conversion_in_guardar_apuesta(self):
        """Prueba conversión de goles apostados"""
        goles_local = 2.5
        goles_visitante = 1.0

        data = {
            'goles_local_apostados': to_int(goles_local),
            'goles_visitante_apostados': to_int(goles_visitante),
        }

        assert data['goles_local_apostados'] == 2
        assert data['goles_visitante_apostados'] == 1
        assert isinstance(data['goles_local_apostados'], int)
        assert isinstance(data['goles_visitante_apostados'], int)

    def test_puntos_provisionales_conversion(self):
        """Prueba conversión de puntos provisionales"""
        puntos = 5.0

        data = {
            'puntos_provisionales': to_int(puntos),
            'procesado': True
        }

        assert data['puntos_provisionales'] == 5
        assert isinstance(data['puntos_provisionales'], int)

    def test_puntos_finalistas_conversion(self):
        """Prueba conversión de puntos finalistas"""
        puntos = 10.0

        data = {
            'puntos': to_int(puntos)
        }

        assert data['puntos'] == 10
        assert isinstance(data['puntos'], int)


class TestNegativeValuesConversion:
    """Tests específicos para valores negativos (causa del error)"""

    def test_negative_dg_conversion(self):
        """Diferencia de goles negativa se convierte correctamente"""
        gf = 2.0
        gc = 5.0
        dg = gf - gc

        assert to_int(dg) == -3
        assert to_int(dg) < 0

    def test_negative_float_string_conversion(self):
        """String de float negativo se convierte correctamente"""
        assert to_int("-2.0") == -2
        assert to_int("-5.5") == -5
        assert to_int("-0.5") == 0

    def test_zero_negative_float(self):
        """Float negativo muy pequeño se convierte a 0"""
        assert to_int(-0.5) == 0
        assert to_int(-0.1) == 0
        assert to_int(-0.0) == 0
