"""
test_data_integrity.py
Tests para verificar que los datos de goles se cargan como int desde Supabase.
"""

import pytest
import pandas as pd
import numpy as np


class TestPartidosDataIntegrity:
    """Tests de integridad de datos de partidos"""

    def test_obtener_partidos_goles_son_int(self, data_layer):
        """TEST CRÍTICO: goles_local y goles_visitante deben ser INT"""
        df = data_layer.obtener_partidos()

        assert not df.empty
        assert "goles_local" in df.columns
        assert "goles_visitante" in df.columns

        # Dtype debe ser int64, no float
        assert df["goles_local"].dtype in [np.int64, int]
        assert df["goles_visitante"].dtype in [np.int64, int]

    def test_goles_no_contienen_nan(self, data_layer):
        """TEST: NO hay NaN en goles"""
        df = data_layer.obtener_partidos()

        assert not df["goles_local"].isna().any()
        assert not df["goles_visitante"].isna().any()

    def test_goles_valores_nulos_convertidos_a_cero(self, data_layer):
        """TEST: NULL de Supabase se convierte a 0"""
        df = data_layer.obtener_partidos()

        # Partido 3 tenía NULL en Supabase
        partido = df[df["id"] == 3]
        assert not partido.empty

        goles_local = partido["goles_local"].values[0]
        goles_visitante = partido["goles_visitante"].values[0]

        assert goles_local == 0
        assert goles_visitante == 0

    def test_compatibilidad_streamlit(self, data_layer):
        """TEST: DataFrame compatible con Streamlit (sin tipos mixtos)"""
        df = data_layer.obtener_partidos()

        goles_local_dtype = df["goles_local"].dtype
        goles_visitante_dtype = df["goles_visitante"].dtype

        # No debe haber dtype=object (indicaría mezcla de tipos)
        assert goles_local_dtype != "object"
        assert goles_visitante_dtype != "object"

    def test_sin_streamlit_mixed_numeric_types_error(self, data_layer):
        """TEST: No hay tipos mixtos (causa StreamlitMixedNumericTypesError)"""
        df = data_layer.obtener_partidos()

        for col in ["goles_local", "goles_visitante"]:
            unique_types = set(type(x).__name__ for x in df[col] if pd.notna(x))

            # Solo UN tipo de dato
            assert len(unique_types) <= 1

            # Debe ser 'int', no 'float'
            if unique_types:
                assert "int" in unique_types
