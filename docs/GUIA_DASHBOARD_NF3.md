# NF3 · Dashboard de estrés térmico (Grupo 3)

## Resumen
Aplicación local con **Streamlit + Pandas + Plotly** para explorar los registros térmicos de arrecifes de coral. Está preparada para el CSV diario de Pedro (`registros_termicos.csv`) con datos desde 2021 y, de manera opcional, su agregado (`registros_semanales.csv`). No descarga datos de NOAA por sí misma ni entrena un modelo de predicción: esas tareas no se deben declarar realizadas en NF3 sin implementarlas y probarlas.

## Archivos que añadimos al repositorio

```text
coral-thermal-stress/
├── requirements.txt
├── data/
│   ├── processed/
│   │   ├── .gitkeep
│   │   ├── registros_termicos.csv        # añadir cuando lo entregue Pedro (según licencia/tamaño)
│   │   └── registros_semanales.csv       # opcional
│   └── examples/
│       └── registros_termicos_demo.csv   # SIMULADO, solo para las pruebas
├── src/
│   └── dashboard/
│       ├── app.py
│       └── data_utils.py
├── tests/
│   └── test_data_utils.py
└── docs/
    └── GUIA_DASHBOARD_NF3.md
```

Se conserva el README principal del grupo, la estructura existente y los demás archivos.

## 1. Instalación y ejecución local (Windows)

**Opción rápida:** hacer doble clic en `INICIAR_DASHBOARD_WINDOWS.bat` desde la raíz del repositorio. La primera vez necesita Internet para instalar dependencias.

**Opción manual:**

1. Abrir una terminal en la carpeta raíz del repositorio.
2. Tener **Python 3.10 o superior** instalado.
3. Crear y activar un entorno virtual:

   ```powershell
   py -m venv .venv
   .venv\Scripts\activate
   ```

4. Instalar las dependencias:

   ```powershell
   python -m pip install -r requirements.txt
   ```

5. Ejecutar la aplicación:

   ```powershell
   python -m streamlit run src/dashboard/app.py
   ```

6. Abrir la dirección local que muestra Streamlit (normalmente `http://localhost:8501`).

En Linux/macOS, activar el entorno con `source .venv/bin/activate` y utilizar `python3` si procede.

## 2. Introducir los datos de Pedro

**Opción A (más rápida):** abrir el dashboard y pulsar **Cargar registros_termicos.csv** en la barra lateral.

**Opción B:** copiar el CSV diario a `data/processed/registros_termicos.csv` (se carga automáticamente cuando se abre el programa). El CSV semanal puede ir en `data/processed/registros_semanales.csv` o cargarse en el widget de la barra lateral.

Los archivos `regiones.csv` y `ubicaciones.csv` son complementarios y, de momento, **no hacen falta**: el CSV principal ya incluye `region` y `ubicacion`. Si se necesita enriquecer las ubicaciones, se ampliará el pipeline.

### Columnas acordadas con Pedro

`Registro_id, Ubicacion_id, Region, Ubicacion, Fecha, Sst, Ssta, Hotspot, Dhw, Baa, Dhw_calc, Dhw_dif, Estres_severo, Lat_celda, Lon_celda, Fuente`

Se convierten a minúsculas para trabajarlas con Pandas. **Formato de `Fecha`: AAAA-MM-DD.** Las columnas básicas son `fecha`, `region` y `ubicacion`; para visualizar gráficos se utilizan `sst`, `ssta`, `hotspot` y `dhw` cuando estén disponibles. No se fuerza a cero ningún `NaN`.

CSV semanal (opcional): `semana_inicio, sst_media, ssta_media, hotspot_max, dhw_max, baa_max, estres_severo, ubicacion_id, region, dias_con_dato`. Si trae `ubicacion_id`, se asocia al nombre de la ubicación mediante el archivo diario.

## 3. Qué permite hacer

- Seleccionar **región**, **ubicaciones**, **fechas** y **fuente**.
- Consultar métricas de SST, DHW y cantidad de registros.
- Ver la evolución de SST, SSTA, HotSpot o DHW sin inventar valores faltantes.
- Comparar regiones sobre una serie temporal.
- Ver los valores del campo BAA como categorías y revisar la marca `estres_severo`.
- Revisar indicadores de calidad (vacíos, duplicados y fechas inválidas).
- Visualizar ubicaciones en un mapa si el CSV incluye coordenadas válidas.
- Consultar datos semanales (si se adjunta `registros_semanales.csv`).
- Exportar los registros filtrados a un CSV.

**Atención:** las etiquetas `fuente` y `estres_severo` provienen del CSV. No se atribuye origen real a registros simulados ni se calcula una nueva predicción.

## 4. Pruebas

Desde la raíz:

```powershell
python -m pytest -q
```

Incluye pruebas unitarias del formato de Pedro, conversión de fechas y decimales, filtrado, datos incompletos, detección de duplicados y carga semanal. En la entrega se debe mostrar una captura de los resultados **obtenidos realmente en el ordenador utilizado** y otra captura de la aplicación abierta con datos.

Para probar antes de recibir el CSV, activar **Usar datos simulados de ejemplo**: los datos de `data/examples/` son completamente inventados y solo sirven para verificar la interfaz.

## 5. Limitaciones y tareas de integración

- Se asume que los encabezados acordados no cambian; se toleran mayúsculas y acentos simples.
- La presencia de `NaN` es normal. El dashboard no interpola valores, ni trata como cero las semanas iniciales sin `dhw_calc`.
- Los gráficos por región muestran medias (SST/SSTA) o máximos (DHW/HotSpot) diarios. No deben confundirse con productos oficiales agregados de NOAA.
- Las alertas de estrés severo son **etiquetas ya calculadas** por Pedro; no son una inferencia independiente de esta aplicación.
- Aún no hay modelo de Machine Learning validado ni backend/API independiente: Streamlit usa el módulo de procesamiento de Pandas.
- Si Pedro actualiza las columnas, validar el esquema y volver a ejecutar las pruebas.
- Antes de la entrega: probar con **CSV real**, capturar la interfaz y los tests, incluir el **commit o tag exacto**, comprobar licencias de los datos y actualizar el README principal con el comando de ejecución.

## 6. Evidencias recomendadas para NF3

1. Pantalla inicial con el CSV cargado y el resumen.
2. Gráfico de evolución de SST y DHW.
3. Comparativa de las dos regiones (si existen en el fichero).
4. Pestaña de calidad y campo `fuente` para distinguir real/simulado.
5. Terminal con `python -m pytest -q` ejecutado correctamente.
6. Referencia al commit/tag definitivo de GitHub y al manual de ejecución.
