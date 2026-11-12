"""Dashboard Streamlit del proyecto de estrés térmico en arrecifes de coral.

Ejecutar desde la raíz del repo: python -m streamlit run src/dashboard/app.py
"""
from __future__ import annotations

from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st

from data_utils import (PLOT_DAILY, PLOT_WEEKLY, daily_quality, filtered,
                        prepare_daily, prepare_weekly, read_csv, time_series)

ROOT = Path(__file__).resolve().parents[2]
MAIN_CSV = ROOT / "data" / "processed" / "registros_termicos.csv"
WEEK_CSV = ROOT / "data" / "processed" / "registros_semanales.csv"
DEMO_CSV = ROOT / "data" / "examples" / "registros_termicos_demo.csv"

st.set_page_config(page_title="Coral Thermal Stress | NF3", page_icon="🌊", layout="wide")
st.title("🌊 Estrés térmico en arrecifes de coral")
st.caption("NF3 · Dashboard de análisis ambiental · Grupo 3")

with st.sidebar:
    st.header("Datos")
    upload = st.file_uploader("Cargar registros_termicos.csv", type="csv", help="Archivo CSV diario recibido de Pedro")
    demo = st.checkbox("Usar datos simulados de ejemplo", value=False,
                       help="Solo para probar la aplicación antes de recibir el CSV real")
    upload_week = st.file_uploader("CSV semanal (opcional)", type="csv", key="weekly")

if upload is not None:
    source = upload.getvalue()
    origin = "CSV cargado por el usuario"
elif MAIN_CSV.exists():
    source = MAIN_CSV
    origin = str(MAIN_CSV.relative_to(ROOT))
elif demo and DEMO_CSV.exists():
    source = DEMO_CSV
    origin = "Archivo de demostración SIMULADO"
else:
    st.info("La aplicación está lista para recibir los datos. Carga **registros_termicos.csv** desde la barra lateral, "
            "cópialo a `data/processed/` o activa el ejemplo simulado para probarla.")
    st.stop()

try:
    raw_daily = read_csv(source)
    df, quality_initial = prepare_daily(raw_daily)
except (ValueError, OSError, pd.errors.ParserError) as exc:
    st.error(f"No se ha podido cargar el CSV diario: {exc}")
    st.stop()

st.success(f"Archivo cargado: {origin} · {len(df):,} registros con fecha válida")
if demo and upload is None and not MAIN_CSV.exists():
    st.warning("**MODO DEMOSTRACIÓN.** Los datos son totalmente simulados y no deben presentarse como mediciones de NOAA.")
if df["fuente"].astype("string").str.contains("simul", case=False, na=False).any():
    st.warning("El CSV contiene filas marcadas como **simuladas** en la columna `fuente`. "
               "No deben presentarse como observaciones reales.")
if quality_initial["fechas_invalidas"]:
    st.warning(f"Se excluyeron {quality_initial['fechas_invalidas']} filas con fecha inválida.")
if quality_initial["duplicados"]:
    st.warning(f"Se detectaron {quality_initial['duplicados']} posibles registros duplicados. No se han eliminado automáticamente.")

with st.sidebar:
    st.divider()
    st.header("Filtros")
    regions = sorted(df["region"].dropna().astype(str).unique().tolist())
    region = st.selectbox("Región", ["Todas"] + regions)
    available = df if region == "Todas" else df[df["region"] == region]
    locations = st.multiselect("Ubicaciones (vacío = todas)", sorted(available["ubicacion"].dropna().astype(str).unique()))
    start_date = df["fecha"].min().date()
    end_date = df["fecha"].max().date()
    period = st.date_input("Fechas", value=(start_date, end_date), min_value=start_date,
                           max_value=end_date, format="DD/MM/YYYY")
    available_sources = sorted(df["fuente"].dropna().astype(str).unique().tolist())
    selected_sources = st.multiselect("Fuentes", available_sources, default=available_sources)
    st.caption("Los NaN no se sustituyen por cero ni se interpolan.")

if len(period) != 2:
    st.info("Selecciona una fecha inicial y otra final para continuar.")
    st.stop()
start, end = period
view = filtered(df, region, locations, start, end, selected_sources)
if view.empty:
    st.warning("No hay registros para los filtros seleccionados. Cambia la región, las fechas o la fuente.")
    st.stop()

summary_cols = st.columns(5)
summary_cols[0].metric("Registros", f"{len(view):,}")
summary_cols[1].metric("Regiones", view["region"].nunique())
summary_cols[2].metric("Ubicaciones", view["ubicacion"].nunique())
summary_cols[3].metric("SST media (°C)", f"{view['sst'].mean():.2f}" if "sst" in view and view["sst"].notna().any() else "Sin datos")
summary_cols[4].metric("DHW máximo", f"{view['dhw'].max():.2f}" if "dhw" in view and view["dhw"].notna().any() else "Sin datos")

tabs = st.tabs(["Resumen", "Evolución", "Comparar regiones", "Calidad", "Semanal", "Datos y exportación"])


def graph(frame: pd.DataFrame, metric: str, label: str, unit: str,
          by: str = "ubicacion", date_col: str = "fecha", chart_key: str = "grafico"):
    series = time_series(frame, metric, group_col=by, date_col=date_col)
    if series.empty or not series[metric].notna().any():
        st.info(f"No hay valores disponibles de {metric.upper()} con estos filtros.")
        return
    fig = px.line(series, x=date_col, y=metric, color=by, markers=False,
                  labels={date_col: "Fecha", metric: f"{label} ({unit})", by: "Región" if by == "region" else "Ubicación"})
    fig.update_traces(connectgaps=False)
    fig.update_layout(legend_title_text="Región" if by == "region" else "Ubicación", hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True, key=f"plot_{chart_key}")
    if frame[metric].isna().any():
        st.caption(f"Aviso: {frame[metric].isna().sum()} valores faltantes de {metric.upper()}; no se dibujan como cero.")

with tabs[0]:
    st.subheader("Vista general")
    st.write("Datos cargados entre", view["fecha"].min().date(), "y", view["fecha"].max().date())
    if "sst" in view:
        graph(view, "sst", *PLOT_DAILY["sst"], chart_key="resumen")
    if "estres_severo" in view:
        known = view["estres_severo"].notna()
        st.write("Registros marcados con estrés severo:",
                 f"**{int(view.loc[known, 'estres_severo'].sum())}** de **{int(known.sum())}** con indicador conocido")
        st.caption("La categoría proviene del CSV; la aplicación no calcula una nueva alerta.")
    st.write("**Procedencia indicada en el archivo**")
    st.dataframe(view["fuente"].value_counts(dropna=False).rename_axis("Fuente").reset_index(name="Registros"),
                 use_container_width=True, hide_index=True)
    if {"lat_celda", "lon_celda"}.issubset(view.columns):
        coords = (view[["ubicacion", "lat_celda", "lon_celda"]]
                  .dropna().drop_duplicates(subset=["ubicacion", "lat_celda", "lon_celda"]))
        coords = coords[coords["lat_celda"].between(-90, 90) & coords["lon_celda"].between(-180, 180)]
        if not coords.empty:
            st.write("**Ubicaciones de análisis**")
            st.map(coords.rename(columns={"lat_celda": "lat", "lon_celda": "lon"}), latitude="lat", longitude="lon")
            st.caption("Coordenadas indicadas por el CSV; no verificadas externamente.")

with tabs[1]:
    st.subheader("Evolución temporal")
    options = [k for k in PLOT_DAILY if k in view]
    if options:
        metric = st.selectbox("Indicador", options, format_func=lambda x: PLOT_DAILY[x][0])
        graph(view, metric, *PLOT_DAILY[metric], chart_key="evolucion")
    else:
        st.info("El CSV no contiene indicadores numéricos para representar.")
    if "baa" in view:
        st.subheader("Distribución BAA")
        baa_counts = view["baa"].fillna("Sin datos").value_counts().rename_axis("BAA").reset_index(name="Registros")
        st.plotly_chart(px.bar(baa_counts, x="BAA", y="Registros"), use_container_width=True)
        st.caption("Se muestran las categorías o valores tal como vienen en el archivo.")

with tabs[2]:
    st.subheader("Comparar regiones")
    if view["region"].nunique() < 2:
        st.info("Selecciona 'Todas' en Región y conserva datos de ambas regiones para compararlas.")
    else:
        options = [k for k in PLOT_DAILY if k in view]
        if options:
            metric_compare = st.selectbox("Indicador de comparación", options,
                                          format_func=lambda x: PLOT_DAILY[x][0])
            graph(view, metric_compare, *PLOT_DAILY[metric_compare], by="region", chart_key="comparar")
            st.caption("SST y SSTA se agregan mediante la media por región y día; "
                       "DHW y HotSpot mediante el máximo. No representan predicciones.")

with tabs[3]:
    st.subheader("Revisión de calidad")
    a, b, c = st.columns(3)
    a.metric("Filas originales", quality_initial["filas_originales"])
    b.metric("Fechas inválidas excluidas", quality_initial["fechas_invalidas"])
    c.metric("Posibles duplicados", quality_initial["duplicados"])
    st.write("**Valores faltantes en los registros filtrados**")
    st.dataframe(daily_quality(view), hide_index=True, use_container_width=True)
    st.caption("Los faltantes pueden ser normales (por ejemplo, al inicio de DHW_calc). "
               "No se han sustituido por cero ni se han estimado.")
    st.write("**Columnas del CSV**")
    st.code(", ".join(df.columns))

with tabs[4]:
    st.subheader("Resumen semanal")
    if upload_week is not None:
        weekly_input = upload_week.getvalue()
        weekly_origin = "CSV semanal cargado"
    elif WEEK_CSV.exists():
        weekly_input = WEEK_CSV
        weekly_origin = "data/processed/registros_semanales.csv"
    else:
        weekly_input = None
        weekly_origin = None
    if weekly_input is None:
        st.info("Este apartado es opcional. Carga `registros_semanales.csv` en la barra lateral "
                "o cópialo a `data/processed/` cuando Pedro lo comparta.")
    else:
        try:
            weekly_df = prepare_weekly(read_csv(weekly_input), df)
            weekly_view = filtered(weekly_df, region, locations, start, end, date_col="semana_inicio")
            st.caption(f"Fuente: {weekly_origin}. Semana filtrada según la fecha de inicio.")
            if weekly_view.empty:
                st.info("No hay datos semanales para los filtros elegidos.")
            else:
                weekly_metrics = [k for k in PLOT_WEEKLY if k in weekly_view]
                if weekly_metrics:
                    wmetric = st.selectbox("Indicador semanal", weekly_metrics,
                                           format_func=lambda x: PLOT_WEEKLY[x][0])
                    graph(weekly_view, wmetric, *PLOT_WEEKLY[wmetric], date_col="semana_inicio", chart_key="semanal")
                st.dataframe(weekly_view, hide_index=True, use_container_width=True)
        except (ValueError, OSError, pd.errors.ParserError) as exc:
            st.warning(f"No se ha podido mostrar el CSV semanal: {exc}")

with tabs[5]:
    st.subheader("Tabla de registros filtrados")
    st.dataframe(view, hide_index=True, use_container_width=True)
    exported = view.to_csv(index=False, date_format="%Y-%m-%d").encode("utf-8-sig")
    st.download_button("Descargar CSV filtrado", data=exported,
                       file_name="registros_termicos_filtrados.csv", mime="text/csv")

st.divider()
st.caption("NF3: aplicación de exploración y visualización. No incluye todavía un modelo predictivo validado "
           "ni una API independiente. La columna `fuente` describe la procedencia declarada por el dataset.")
