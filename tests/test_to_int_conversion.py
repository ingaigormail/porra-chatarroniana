"""
test_to_int_conversion.py
Tests comprensivos para la función to_int() que evita el error:
'invalid input syntax for type integer: "-2.0"'
"""

import pytest
import sys
from pathlib import Path

# Añadir el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.validators import to_int


class TestToIntConversion:
    """Tests para la función to_int()"""

    def test_conversion_int_to_int(self):
        """Convierte int correctamente"""
        assert to_int(5) == 5
        assert to_int(0) == 0
        assert to_int(-2) == -2
        assert to_int(999999) == 999999

    def test_conversion_float_to_int(self):
        """Convierte float a int correctamente"""
        assert to_int(5.7) == 5
        assert to_int(5.3) == 5
        assert to_int(0.0) == 0
        assert to_int(2.9) == 2
        assert to_int(-2.5) == -2
        assert to_int(-2.0) == -2  # CRÍTICO: El error reportado

    def test_conversion_string_to_int(self):
        """Convierte string a int correctamente"""
        assert to_int("5") == 5
        assert to_int("0") == 0
        assert to_int("-2") == -2
        assert to_int("2.5") == 2
        assert to_int("-2.0") == -2  # CRÍTICO: Simula el error de Supabase
        assert to_int("999") == 999

    def test_conversion_none_to_zero(self):
        """None se convierte a 0"""
        assert to_int(None) == 0

    def test_conversion_invalid_string_to_zero(self):
        """String inválido se convierte a 0"""
        assert to_int("abc") == 0
        assert to_int("") == 0
        assert to_int("12.34.56") == 0

    def test_conversion_bool_to_int(self):
        """Bool se convierte correctamente"""
        assert to_int(True) == 1
        assert to_int(False) == 0

    def test_conversion_preserves_negative_values(self):
        """Preserva valores negativos correctamente"""
        assert to_int(-5) == -5
        assert to_int(-5.9) == -5
        assert to_int("-10") == -10
        assert to_int("-10.5") == -10

    def test_all_values_are_int_type(self):
        """Todos los valores retornados son tipo int"""
        test_values = [5, 5.7, "5", None, True, "-2.0"]
        for value in test_values:
            result = to_int(value)
            assert isinstance(result, int), f"to_int({value}) retornó {type(result).__name__}, no int"

    def test_conversion_large_numbers(self):
        """Convierte números grandes correctamente"""
        assert to_int(999999999999) == 999999999999
        assert to_int(999999999999.9) == 999999999999
        assert to_int("999999999999") == 999999999999

    def test_zero_values(self):
        """Todos los ceros se convierten a 0"""
        assert to_int(0) == 0
        assert to_int(0.0) == 0
        assert to_int("0") == 0
        assert to_int(-0.0) == 0
