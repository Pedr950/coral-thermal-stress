import tempfile
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

import noaa_pipeline as p

CSV_NOAA = """time,latitude,longitude,CRW_SST,CRW_SSTANOMALY,CRW_HOTSPOT,CRW_DHW,CRW_BAA
UTC,degrees_north,degrees_east,degree_C,degree_C,degree_C,degree_C_weeks,1
2020-02-01T12:00:00Z,-14.675,145.425,29.5,1.2,0.8,0.0,1.0
2020-02-02T12:00:00Z,-14.675,145.425,-999.0,1.3,0.9,0.0,1.0
"""


def test_parse_descarta_fila_de_unidades():
    df = p.parse_erddap_csv(CSV_NOAA)
    assert len(df) == 2
    assert {"fecha", "sst", "ssta", "hotspot", "dhw", "baa"} <= set(df.columns)
    assert df["fecha"].iloc[0] == pd.Timestamp("2020-02-01")


def test_limpiar_quita_relleno_y_duplicados():
    df = p.parse_erddap_csv(CSV_NOAA)
    df["ubicacion_id"], df["region"] = 1, "gran_barrera"
    df = pd.concat([df, df.iloc[[0]]], ignore_index=True)       # duplicado
    limpio, info = p.limpiar(df)
    assert info["duplicados_eliminados"] == 1
    assert limpio["sst"].isna().sum() == 1                       # el -999 pasa a NaN


def test_dhw_calculado_constante():
    fechas = pd.date_range("2020-01-01", periods=100, freq="D")
    df = pd.DataFrame({"fecha": fechas, "ubicacion_id": 1, "region": "x", "hotspot": 2.0, "dhw": np.nan})
    out = p.anadir_dhw_calculado(df)
    # 84 días * 2 °C / 7 = 24 °C-semanas
    assert abs(out["dhw_calc"].iloc[83] - 24.0) < 1e-9
    assert np.isnan(out["dhw_calc"].iloc[82])


def test_hotspot_menor_que_1_no_acumula():
    fechas = pd.date_range("2020-01-01", periods=90, freq="D")
    df = pd.DataFrame({"fecha": fechas, "ubicacion_id": 1, "region": "x", "hotspot": 0.9, "dhw": np.nan})
    assert p.anadir_dhw_calculado(df)["dhw_calc"].iloc[-1] == 0


def test_demo_genera_csv_con_columnas_esperadas():
    with tempfile.TemporaryDirectory() as d:
        p.ejecutar(["gran_barrera", "caribe"], date(2022, 1, 1), date(2022, 12, 31), Path(d) / "processed", demo=True)
        df = pd.read_csv(Path(d) / "processed" / "registros_termicos.csv")
        assert {"fecha", "region", "sst", "dhw", "ssta", "hotspot"} <= set(df.columns)
        assert set(df["region"]) == {"gran_barrera", "caribe"}
        assert df.duplicated(["ubicacion_id", "fecha"]).sum() == 0
        assert (df["fuente"] == "SIMULADO").all()


def test_pipeline_real_con_descarga_simulada(monkeypatch=None):
    """Sustituye la descarga por una respuesta falsa de ERDDAP para probar el flujo completo."""
    original = p.fetch_text
    def falso(url, reintentos=3):
        fechas = pd.date_range("2021-01-01", "2021-12-31", freq="D")
        filas = ["time,latitude,longitude,CRW_SST,CRW_SSTANOMALY,CRW_HOTSPOT,CRW_DHW,CRW_BAA",
                 "UTC,degrees_north,degrees_east,degree_C,degree_C,degree_C,degree_C_weeks,1"]
        filas += [f"{f:%Y-%m-%d}T12:00:00Z,-14.675,145.425,28.0,0.5,0.1,0.0,0.0" for f in fechas]
        return "\n".join(filas) + "\n"
    p.fetch_text = falso
    try:
        with tempfile.TemporaryDirectory() as d:
            inf = p.ejecutar(["gran_barrera"], date(2021, 3, 1), date(2021, 6, 30), Path(d) / "processed")
            df = pd.read_csv(Path(d) / "processed" / "registros_termicos.csv")
            assert df["fecha"].min() == "2021-03-01" and df["fecha"].max() == "2021-06-30"
            assert (df["fuente"] == "NOAA_CRW_v3.1").all()
    finally:
        p.fetch_text = original
