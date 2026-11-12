"""Carga, validación y preparación de los CSV del proyecto coral-thermal-stress.

Este módulo no necesita Streamlit: se puede probar por separado con pytest.
"""
from __future__ import annotations

import io
import unicodedata
from pathlib import Path

import pandas as pd

REQUIRED = {"fecha", "region", "ubicacion"}
NUMERIC_DAILY = ("sst", "ssta", "hotspot", "dhw", "dhw_calc", "dhw_dif", "lat_celda", "lon_celda")
NUMERIC_WEEKLY = ("sst_media", "ssta_media", "hotspot_max", "dhw_max", "dias_con_dato")
PLOT_DAILY = {"sst": ("Temperatura superficial (SST)", "°C"),
              "ssta": ("Anomalía térmica (SSTA)", "°C"),
              "hotspot": ("HotSpot", "°C"),
              "dhw": ("Estrés térmico acumulado (DHW)", "°C-semanas")}
PLOT_WEEKLY = {"sst_media": ("SST media semanal", "°C"),
               "ssta_media": ("SSTA media semanal", "°C"),
               "hotspot_max": ("HotSpot máximo semanal", "°C"),
               "dhw_max": ("DHW máximo semanal", "°C-semanas")}
MAX_METRICS = {"dhw", "hotspot", "dhw_max", "hotspot_max"}


def _canonical(name: str) -> str:
    plain = unicodedata.normalize("NFKD", str(name).strip().lower())
    plain = "".join(ch for ch in plain if not unicodedata.combining(ch))
    return plain.replace(" ", "_").replace("-", "_")


def _standardize(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    new_names = [_canonical(x) for x in out.columns]
    if len(set(new_names)) != len(new_names):
        raise ValueError("Hay columnas repetidas después de normalizar sus nombres.")
    out.columns = new_names
    return out


def read_csv(source: bytes | str | Path) -> pd.DataFrame:
    """Acepta un archivo en disco o bytes de st.file_uploader.

    Detecta comas o punto y coma y soporta UTF-8 y Latin-1.
    """
    if isinstance(source, (str, Path)):
        blob = Path(source).read_bytes()
    else:
        blob = source
    if not blob or not blob.strip():
        raise ValueError("El CSV está vacío.")
    last_error: Exception | None = None
    for encoding in ("utf-8-sig", "latin-1"):
        try:
            return pd.read_csv(io.BytesIO(blob), sep=None, engine="python", encoding=encoding)
        except UnicodeDecodeError as exc:
            last_error = exc
        except pd.errors.EmptyDataError as exc:
            raise ValueError("El CSV no contiene columnas válidas.") from exc
    raise ValueError("No se pudo leer el CSV.") from last_error


def _numbers(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series.astype("string").str.strip().str.replace(",", ".", regex=False), errors="coerce")


def _severe(value: object):
    if pd.isna(value):
        return pd.NA
    normalized = _canonical(str(value))
    if normalized in ("1", "1.0", "true", "si", "yes", "verdadero", "severo"):
        return True
    if normalized in ("0", "0.0", "false", "no", "falso", "normal"):
        return False
    return pd.NA


def prepare_daily(raw: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    df = _standardize(raw)
    if "ubicacion" not in df.columns and "ubicacion_id" in df.columns:
        df["ubicacion"] = "Punto " + df["ubicacion_id"].astype("string").fillna("desconocido")
    missing = sorted(REQUIRED - set(df.columns))
    if missing:
        raise ValueError("Faltan columnas obligatorias: " + ", ".join(missing))

    row_count = len(df)
    df["fecha"] = pd.to_datetime(df["fecha"], format="%Y-%m-%d", errors="coerce")
    invalid_dates = int(df["fecha"].isna().sum())
    # Sin fecha no es posible situar un dato en el gráfico. No se inventa la fecha.
    df = df.dropna(subset=["fecha"]).copy()
    if df.empty:
        raise ValueError("No hay fechas válidas con formato AAAA-MM-DD en el CSV.")

    for col in ("region", "ubicacion"):
        df[col] = df[col].astype("string").str.strip().replace("", pd.NA).fillna("Sin especificar")
    for col in NUMERIC_DAILY:
        if col in df:
            df[col] = _numbers(df[col])
    if "estres_severo" in df:
        df["estres_severo"] = df["estres_severo"].map(_severe).astype("boolean")
    if "fuente" not in df:
        df["fuente"] = "Sin especificar"
    else:
        df["fuente"] = df["fuente"].astype("string").str.strip().replace("", pd.NA).fillna("Sin especificar")
    if "baa" in df:
        df["baa"] = df["baa"].astype("string").str.strip().replace("", pd.NA)

    identifying = [col for col in ("ubicacion_id", "fecha") if col in df]
    if len(identifying) < 2:
        identifying = ["region", "ubicacion", "fecha"]
    duplicate_count = int(df.duplicated(subset=identifying).sum())
    df = df.sort_values(["fecha", "region", "ubicacion"]).reset_index(drop=True)
    stats = {"filas_originales": row_count, "fechas_invalidas": invalid_dates,
             "duplicados": duplicate_count, "clave_duplicados": identifying}
    return df, stats


def prepare_weekly(raw: pd.DataFrame, daily: pd.DataFrame | None = None) -> pd.DataFrame:
    df = _standardize(raw)
    missing = {"semana_inicio", "region"} - set(df)
    if missing:
        raise ValueError("Faltan columnas semanales: " + ", ".join(sorted(missing)))
    df["semana_inicio"] = pd.to_datetime(df["semana_inicio"], format="%Y-%m-%d", errors="coerce")
    df = df.dropna(subset=["semana_inicio"]).copy()
    df["region"] = df["region"].astype("string").str.strip().replace("", pd.NA).fillna("Sin especificar")
    if "ubicacion" not in df and daily is not None and "ubicacion_id" in df and "ubicacion_id" in daily:
        look = daily[["ubicacion_id", "ubicacion"]].drop_duplicates(subset=["ubicacion_id"])
        df = df.merge(look, on="ubicacion_id", how="left")
    if "ubicacion" not in df:
        df["ubicacion"] = "Punto " + df["ubicacion_id"].astype("string") if "ubicacion_id" in df else "Ubicación no indicada"
    df["ubicacion"] = df["ubicacion"].astype("string").fillna("Ubicación no indicada")
    for col in NUMERIC_WEEKLY:
        if col in df:
            df[col] = _numbers(df[col])
    if "estres_severo" in df:
        df["estres_severo"] = df["estres_severo"].map(_severe).astype("boolean")
    return df.sort_values("semana_inicio").reset_index(drop=True)


def filtered(df: pd.DataFrame, region: str, locations: list[str],
             start, end, sources: list[str] | None = None,
             date_col: str = "fecha") -> pd.DataFrame:
    mask = (df[date_col].dt.date >= start) & (df[date_col].dt.date <= end)
    if region != "Todas":
        mask &= df["region"] == region
    if locations:
        mask &= df["ubicacion"].isin(locations)
    if sources is not None and "fuente" in df:
        mask &= df["fuente"].isin(sources)
    return df.loc[mask].copy()


def time_series(df: pd.DataFrame, metric: str, group_col: str = "ubicacion",
                date_col: str = "fecha") -> pd.DataFrame:
    if metric not in df or not df[metric].notna().any():
        return pd.DataFrame(columns=[date_col, group_col, metric])
    operation = "max" if metric in MAX_METRICS else "mean"
    return (df.groupby([date_col, group_col], dropna=False)[metric]
            .agg(operation).reset_index().sort_values(date_col))


def daily_quality(df: pd.DataFrame) -> pd.DataFrame:
    cols = [c for c in ("sst", "ssta", "hotspot", "dhw", "baa", "estres_severo", "lat_celda", "lon_celda") if c in df]
    return pd.DataFrame({"Columna": cols, "Valores vacíos": [int(df[c].isna().sum()) for c in cols],
                         "% vacíos": [round(100 * df[c].isna().mean(), 1) if len(df) else 0 for c in cols]})
