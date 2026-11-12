#!/usr/bin/env python3
"""
CoralHeat · Pipeline de datos (descarga + limpieza + procesamiento) de NOAA Coral Reef Watch.

Qué hace:
  1. Descarga series diarias de SST, anomalía, HotSpot, DHW y BAA para unos puntos de arrecife
     (ERDDAP de NOAA CoastWatch, dataset NOAA_DHW, malla de 5 km).
  2. Limpia (fechas, valores de relleno, rangos, duplicados) y calcula columnas extra
     (DHW propio para validar el oficial, marca de estrés severo).
  3. Guarda CSV listos para el dashboard y para la base de datos del modelo de datos de NF2.

Uso:
  python noaa_pipeline.py --demo                                  # datos SIMULADOS, sin internet
  python noaa_pipeline.py --start 2015-01-01 --end 2025-12-31     # datos reales de NOAA
  python noaa_pipeline.py --regiones caribe --start 2020-01-01    # solo una región
"""
import argparse
import io
import json
import time
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import requests

# ----------------------------------------------------------------------------
# Configuración
# ----------------------------------------------------------------------------
ERDDAP_URL = "https://coastwatch.pfeg.noaa.gov/erddap/griddap/NOAA_DHW"   # dataset verificado en la web de NOAA
VARIABLES = {                      # nombre en NOAA -> nombre en nuestro CSV
    "CRW_SST": "sst",              # temperatura superficial del mar (°C)
    "CRW_SSTANOMALY": "ssta",      # anomalía de temperatura (°C)
    "CRW_HOTSPOT": "hotspot",      # exceso sobre el mes más cálido (°C)
    "CRW_DHW": "dhw",              # Degree Heating Weeks (°C-semanas)
    "CRW_BAA": "baa",              # nivel de alerta de blanqueamiento (0-5)
}
DHW_VENTANA_DIAS = 84              # 12 semanas
DHW_UMBRAL_SEVERO = 4.0            # °C-semanas

REGIONES = {
    "gran_barrera": {"region_id": 1, "nombre": "Gran Barrera de Coral", "zona_geografica": "Australia"},
    "caribe":       {"region_id": 2, "nombre": "Caribe",                 "zona_geografica": "Caribe"},
}
# Puntos de muestreo (aprox.). Si algún punto cae en tierra o sale todo vacío, cambia sus coordenadas.
UBICACIONES = [
    {"ubicacion_id": 1, "region": "gran_barrera", "punto": "Lizard Island",    "lat": -14.67, "lon": 145.45},
    {"ubicacion_id": 2, "region": "gran_barrera", "punto": "Davies Reef",      "lat": -18.82, "lon": 147.64},
    {"ubicacion_id": 3, "region": "gran_barrera", "punto": "Heron Island",     "lat": -23.44, "lon": 151.91},
    {"ubicacion_id": 4, "region": "caribe",       "punto": "Florida Keys",     "lat":  24.52, "lon": -81.77},
    {"ubicacion_id": 5, "region": "caribe",       "punto": "Belice (barrera)", "lat":  17.30, "lon": -87.80},
]
# Si algún punto cae en tierra o sale todo vacío, cambia sus coordenadas.

RANGOS = {"sst": (-2, 40), "ssta": (-15, 15), "hotspot": (-10, 15), "dhw": (0, 50), "baa": (0, 5)}


# ----------------------------------------------------------------------------
# 1. Descarga
# ----------------------------------------------------------------------------
def build_url(t0: str, t1: str, lat: float, lon: float) -> str:
    """URL ERDDAP (CSV) para un punto: [tiempo][lat][lon] de todas las variables."""
    dims = f"[({t0}T12:00:00Z):1:({t1}T12:00:00Z)][({lat}):1:({lat})][({lon}):1:({lon})]"
    consulta = ",".join(v + dims for v in VARIABLES)
    return f"{ERDDAP_URL}.csv?{consulta}"


def fetch_text(url: str, reintentos: int = 3) -> str:
    """Descarga el texto CSV con reintentos. Devuelve '' si NOAA responde 'sin resultados' (404)."""
    for intento in range(1, reintentos + 1):
        try:
            r = requests.get(url, timeout=180)
            if r.status_code == 404:
                return ""
            r.raise_for_status()
            return r.text
        except requests.RequestException as e:
            print(f"   ! intento {intento}/{reintentos} fallido: {e}")
            time.sleep(2 * intento)
    raise RuntimeError("No se pudo descargar tras varios reintentos")


def parse_erddap_csv(texto: str) -> pd.DataFrame:
    """ERDDAP devuelve una 2ª fila con unidades: se descarta."""
    if not texto.strip():
        return pd.DataFrame()
    df = pd.read_csv(io.StringIO(texto), skiprows=[1])
    df = df.rename(columns={"time": "fecha", "latitude": "lat_celda", "longitude": "lon_celda", **VARIABLES})
    df["fecha"] = pd.to_datetime(df["fecha"], utc=True).dt.tz_localize(None).dt.normalize()
    return df


def descargar_ubicacion(loc: dict, f_ini: date, f_fin: date, cache: Path, forzar=False) -> pd.DataFrame:
    """Descarga año a año (con caché en disco) para no pedir un bloque enorme de golpe."""
    cache.mkdir(parents=True, exist_ok=True)
    partes = []
    for anio in range(f_ini.year, f_fin.year + 1):
        t0 = max(f_ini, date(anio, 1, 1)).isoformat()
        t1 = min(f_fin, date(anio, 12, 31)).isoformat()
        fichero = cache / f"{loc['region']}_{loc['ubicacion_id']}_{t0}_{t1}.csv"   # el rango va en el nombre
        if fichero.exists() and not forzar:
            texto = fichero.read_text()
        else:
            print(f" - {loc['punto']} {anio} ...")
            try:
                texto = fetch_text(build_url(t0, t1, loc["lat"], loc["lon"]))
            except RuntimeError as e:
                print(f"   ! {loc['punto']} {anio}: {e}")
                continue
            fichero.write_text(texto)
            time.sleep(0.5)  # cortesía con el servidor
        df = parse_erddap_csv(texto)
        if not df.empty:
            partes.append(df)
    if not partes:
        return pd.DataFrame()
    df = pd.concat(partes, ignore_index=True)
    for k in ("ubicacion_id", "region"):
        df[k] = loc[k]
    return df


# ----------------------------------------------------------------------------
# 2. Limpieza y procesamiento
# ----------------------------------------------------------------------------
def limpiar(df: pd.DataFrame):
    """Devuelve (df_limpio, informe_de_limpieza)."""
    info = {"filas_entrada": int(len(df))}
    df = df.copy()
    for col in VARIABLES.values():
        if col not in df:
            df[col] = np.nan
        df[col] = pd.to_numeric(df[col], errors="coerce")
        df.loc[df[col] <= -900, col] = np.nan                      # valores de relleno tipo -999
    fuera = 0
    for col, (lo, hi) in RANGOS.items():                            # valores imposibles -> NaN
        mal = df[col].notna() & ((df[col] < lo) | (df[col] > hi))
        fuera += int(mal.sum())
        df.loc[mal, col] = np.nan
    info["valores_fuera_de_rango"] = fuera
    antes = len(df)
    df = df.drop_duplicates(subset=["ubicacion_id", "fecha"], keep="first")
    info["duplicados_eliminados"] = int(antes - len(df))
    df = df.sort_values(["ubicacion_id", "fecha"]).reset_index(drop=True)
    info["filas_salida"] = int(len(df))
    return df, info


def anadir_dhw_calculado(df: pd.DataFrame) -> pd.DataFrame:
    """DHW propio = suma de HotSpot>=1 en 84 días / 7. Sirve para validar el DHW oficial."""
    partes = []
    for _, g in df.groupby("ubicacion_id", sort=False):
        g = g.sort_values("fecha").set_index("fecha")
        completo = g.reindex(pd.date_range(g.index.min(), g.index.max(), freq="D"))
        hs = completo["hotspot"].where(completo["hotspot"] >= 1, 0.0).where(completo["hotspot"].notna())
        g["dhw_calc"] = (hs.rolling(DHW_VENTANA_DIAS, min_periods=DHW_VENTANA_DIAS).sum() / 7).reindex(g.index)
        partes.append(g.reset_index())
    out = pd.concat(partes, ignore_index=True)
    out["dhw_dif"] = out["dhw_calc"] - out["dhw"]
    out["estres_severo"] = np.where(out["dhw"].isna(), pd.NA, (out["dhw"] >= DHW_UMBRAL_SEVERO).astype("Int64"))
    out["estres_severo"] = out["estres_severo"].astype("Int64")
    return out


def agregar_semanal(df: pd.DataFrame) -> pd.DataFrame:
    g = df.set_index("fecha").groupby(["ubicacion_id", "region", pd.Grouper(freq="W-MON", label="left", closed="left")])
    sem = g.agg(sst_media=("sst", "mean"), ssta_media=("ssta", "mean"), hotspot_max=("hotspot", "max"),
                dhw_max=("dhw", "max"), baa_max=("baa", "max"), estres_severo=("estres_severo", "max"),
                dias_con_dato=("sst", "count")).reset_index().rename(columns={"fecha": "semana_inicio"})
    return sem


def informe_calidad(df: pd.DataFrame, f_ini: date, f_fin: date, limpieza: dict) -> dict:
    inf = {"limpieza": limpieza, "ubicaciones": {}}
    dias_esperados = (f_fin - f_ini).days + 1
    for uid, g in df.groupby("ubicacion_id"):
        d = {
            "region": g["region"].iloc[0], "filas": int(len(g)), "dias_esperados": dias_esperados,
            "fecha_min": str(g["fecha"].min().date()), "fecha_max": str(g["fecha"].max().date()),
            "faltantes": {c: int(g[c].isna().sum()) for c in VARIABLES.values()},
            "todo_vacio": bool(g[list(VARIABLES.values())].isna().all().all()),
        }
        comp = g["dhw_dif"].dropna()
        if len(comp):
            d["dhw_calc_vs_oficial"] = {"mae": round(float(comp.abs().mean()), 3), "max_abs": round(float(comp.abs().max()), 3)}
        d["dias_estres_severo"] = int(g["estres_severo"].fillna(0).sum())
        inf["ubicaciones"][int(uid)] = d
    return inf


# ----------------------------------------------------------------------------
# 3. Datos simulados (solo para desarrollar el dashboard sin internet)
# ----------------------------------------------------------------------------
def generar_demo(locs, f_ini: date, f_fin: date, seed=42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    fechas = pd.date_range(f_ini - timedelta(days=DHW_VENTANA_DIAS), f_fin, freq="D")
    doy = fechas.dayofyear.values
    años = (fechas - fechas[0]).days.values / 365.25
    partes = []
    for loc in locs:
        lat = loc["lat"]
        media = 28.0 - abs(lat) * 0.15
        amp = 2.6 if abs(lat) > 20 else 1.5
        pico = 45 if lat < 0 else 235
        estacional = amp * np.cos(2 * np.pi * (doy - pico) / 365.25)
        ruido = np.zeros(len(fechas))
        for i in range(1, len(fechas)):
            ruido[i] = 0.9 * ruido[i - 1] + rng.normal(0, 0.12)
        ola = np.zeros(len(fechas))
        for anio in sorted(set(fechas.year)):
            if rng.random() < 0.35:                                   # ola de calor ese verano
                centro = pd.Timestamp(anio, 2, 15) if lat < 0 else pd.Timestamp(anio, 8, 25)
                dias = (fechas - centro).days.values
                ola += rng.uniform(1.2, 2.6) * np.exp(-0.5 * (dias / 18.0) ** 2)
        sst = media + estacional + 0.025 * años + ruido + ola
        mmm = media + amp                                             # mes más cálido de referencia
        df = pd.DataFrame({"fecha": fechas, "lat_celda": lat, "lon_celda": loc["lon"], "sst": sst.round(2),
                           "ssta": (sst - (media + estacional)).round(2),
                           "hotspot": np.clip(sst - mmm, 0, None).round(2)})
        df["ubicacion_id"], df["region"] = loc["ubicacion_id"], loc["region"]
        partes.append(df)
    df = pd.concat(partes, ignore_index=True)
    df["dhw"] = np.nan
    df = anadir_dhw_calculado(df)
    df["dhw"] = df["dhw_calc"].round(2)
    df["baa"] = np.select([df["dhw"] >= 8, df["dhw"] >= 4, df["hotspot"] >= 1, df["hotspot"] > 0], [4, 3, 2, 1], 0).astype(float)
    df = df.drop(columns=["dhw_calc", "dhw_dif", "estres_severo"])
    # pequeñas imperfecciones para que la limpieza tenga algo que hacer
    idx = rng.choice(len(df), size=max(3, len(df) // 200), replace=False)
    df.loc[idx, "sst"] = np.nan
    df = pd.concat([df, df.sample(3, random_state=1)], ignore_index=True)
    return df


# ----------------------------------------------------------------------------
# 4. Orquestación
# ----------------------------------------------------------------------------
def ejecutar(regiones, f_ini: date, f_fin: date, out: Path, demo=False, forzar=False) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    locs = [u for u in UBICACIONES if u["region"] in regiones]
    f_desc = f_ini - timedelta(days=DHW_VENTANA_DIAS)      # margen previo para poder calcular el DHW propio
    if demo:
        bruto = generar_demo(locs, f_ini, f_fin)
        fuente = "SIMULADO"
    else:
        partes = [descargar_ubicacion(l, f_desc, f_fin, out.parent / "raw", forzar) for l in locs]
        partes = [p for p in partes if not p.empty]
        if not partes:
            raise SystemExit("No se obtuvo ningún dato. Revisa la conexión o las coordenadas.")
        bruto = pd.concat(partes, ignore_index=True)
        fuente = "NOAA_CRW_v3.1"
    limpio, info_limpieza = limpiar(bruto)
    proc = anadir_dhw_calculado(limpio)
    proc = proc[(proc["fecha"] >= pd.Timestamp(f_ini)) & (proc["fecha"] <= pd.Timestamp(f_fin))].reset_index(drop=True)  # quita el margen previo
    proc["fuente"] = fuente
    proc.insert(0, "registro_id", np.arange(1, len(proc) + 1))
    nombres = {u["ubicacion_id"]: u["punto"] for u in locs}
    proc.insert(3, "ubicacion", proc["ubicacion_id"].map(nombres))
    columnas = ["registro_id", "ubicacion_id", "region", "ubicacion", "fecha", "sst", "ssta", "hotspot", "dhw", "baa",
                "dhw_calc", "dhw_dif", "estres_severo", "lat_celda", "lon_celda", "fuente"]
    proc = proc[columnas]
    proc.to_csv(out / "registros_termicos.csv", index=False, date_format="%Y-%m-%d")
    agregar_semanal(proc).to_csv(out / "registros_semanales.csv", index=False, date_format="%Y-%m-%d")
    # tablas auxiliares con los mismos nombres que el modelo de datos de NF2
    pd.DataFrame([{"region_id": v["region_id"], "nombre": v["nombre"], "zona_geografica": v["zona_geografica"]}
                  for k, v in REGIONES.items() if k in regiones]).to_csv(out / "regiones.csv", index=False)
    celdas = proc.groupby("ubicacion_id")[["lat_celda", "lon_celda"]].first()
    pd.DataFrame([{"ubicacion_id": l["ubicacion_id"], "region_id": REGIONES[l["region"]]["region_id"], "nombre": l["punto"],
                   "latitud": float(celdas.loc[l["ubicacion_id"], "lat_celda"]) if l["ubicacion_id"] in celdas.index else l["lat"],
                   "longitud": float(celdas.loc[l["ubicacion_id"], "lon_celda"]) if l["ubicacion_id"] in celdas.index else l["lon"]}
                  for l in locs]).to_csv(out / "ubicaciones.csv", index=False)
    inf = informe_calidad(proc, f_ini, f_fin, info_limpieza)
    inf["fuente"] = fuente
    (out / "informe_calidad.json").write_text(json.dumps(inf, indent=2, ensure_ascii=False))
    print(f"\nListo: {len(proc)} filas -> {out/'registros_termicos.csv'}  (fuente: {fuente})")
    return inf


def main():
    ap = argparse.ArgumentParser(description="Pipeline de datos NOAA CRW para CoralHeat")
    ap.add_argument("--start", default="2015-01-01")
    ap.add_argument("--end", default=(date.today() - timedelta(days=10)).isoformat(), help="por defecto, hoy-10 días")
    ap.add_argument("--regiones", nargs="+", default=list(REGIONES), choices=list(REGIONES))
    ap.add_argument("--out", default="data/processed")
    ap.add_argument("--demo", action="store_true", help="genera datos SIMULADOS sin internet")
    ap.add_argument("--forzar", action="store_true", help="ignora la caché y vuelve a descargar")
    a = ap.parse_args()
    ejecutar(a.regiones, date.fromisoformat(a.start), date.fromisoformat(a.end), Path(a.out), a.demo, a.forzar)


if __name__ == "__main__":
    main()
