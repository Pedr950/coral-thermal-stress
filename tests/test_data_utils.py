from pathlib import Path
import sys

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src" / "dashboard"))
from data_utils import (daily_quality, filtered, prepare_daily, prepare_weekly,
                        read_csv, time_series)


def test_schema_pedro_case_insensitive():
    raw = pd.DataFrame({"Registro_id": [1, 2], "Ubicacion_id": [10, 10],
                        "Region": ["gran_barrera", "gran_barrera"], "Ubicacion": ["A", "A"],
                        "Fecha": ["2021-01-01", "2021-01-02"],
                        "Sst": ["29,2", None], "Ssta": [1.2, None],
                        "Hotspot": [2, 3], "Dhw": [None, 1.0], "Baa": [None, "1"],
                        "Dhw_calc": [None, 0.5], "Dhw_dif": [None, 0.5],
                        "Estres_severo": ["SI", "0"], "Lat_celda": [-18, -18],
                        "Lon_celda": [147, 147], "Fuente": ["simulado", "simulado"]})
    df, stat = prepare_daily(raw)
    assert set(["sst", "dhw", "fuente", "fecha", "region", "ubicacion"]).issubset(df.columns)
    assert df["sst"].iloc[0] == pytest.approx(29.2)
    assert pd.isna(df["sst"].iloc[1])
    assert df["estres_severo"].tolist() == [True, False]
    assert stat["fechas_invalidas"] == 0
    assert len(daily_quality(df)) >= 4


def test_invalid_dates_are_counted_not_plotted():
    raw = pd.DataFrame({"fecha": ["2021-01-01", "no fecha"],
                        "region": ["caribe", "caribe"], "ubicacion": ["C", "C"],
                        "sst": [28, 99]})
    df, stats = prepare_daily(raw)
    assert stats["fechas_invalidas"] == 1
    assert len(df) == 1
    assert df["sst"].max() == 28


def test_missing_required_column_explains_error():
    with pytest.raises(ValueError, match="fecha"):
        prepare_daily(pd.DataFrame({"Region": ["caribe"], "Ubicacion": ["A"]}))


def test_duplicate_warning_and_time_series_nan():
    raw = pd.DataFrame({"fecha": ["2021-01-01", "2021-01-01", "2021-01-02"],
                        "region": ["caribe"] * 3, "ubicacion": ["A"] * 3,
                        "ubicacion_id": [4] * 3, "sst": [29, 30, None]})
    df, stats = prepare_daily(raw)
    assert stats["duplicados"] == 1
    series = time_series(df, "sst")
    assert series["sst"].iloc[0] == pytest.approx(29.5)
    assert pd.isna(series["sst"].iloc[1])


def test_filter_region_and_dates():
    raw = pd.DataFrame({"fecha": ["2021-01-01", "2021-01-02", "2021-01-01"],
                        "region": ["caribe", "caribe", "gran_barrera"],
                        "ubicacion": ["A", "B", "C"], "sst": [28, 29, 30],
                        "fuente": ["real", "real", "simulado"]})
    df, _ = prepare_daily(raw)
    view = filtered(df, "caribe", [], pd.Timestamp("2021-01-01").date(),
                    pd.Timestamp("2021-01-01").date(), ["real"])
    assert len(view) == 1
    assert view["ubicacion"].iloc[0] == "A"


def test_weekly_schema_and_location_join():
    daily = pd.DataFrame({"fecha": ["2021-01-01"], "region": ["caribe"],
                          "ubicacion": ["Arrecife A"], "ubicacion_id": [2], "sst": [28]})
    daily, _ = prepare_daily(daily)
    weekly = pd.DataFrame({"Semana_inicio": ["2021-01-04"], "Ubicacion_id": [2],
                           "Region": ["caribe"], "Sst_media": ["28,5"],
                           "Dhw_max": [2.0], "Dias_con_dato": [6]})
    out = prepare_weekly(weekly, daily)
    assert out["ubicacion"].iloc[0] == "Arrecife A"
    assert out["sst_media"].iloc[0] == pytest.approx(28.5)


def test_semicolon_and_utf8():
    blob = "Fecha;Region;Ubicacion;Sst\n2021-01-01;caribe;A;28,7\n".encode("utf-8")
    daily, _ = prepare_daily(read_csv(blob))
    assert daily["sst"].iloc[0] == pytest.approx(28.7)


def test_no_valid_dates_error():
    with pytest.raises(ValueError, match="fechas válidas"):
        prepare_daily(pd.DataFrame({"Fecha": ["foo"], "Region": ["a"], "Ubicacion": ["b"]}))
