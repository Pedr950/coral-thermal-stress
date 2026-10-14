# CoralHeat

**Pipeline Big Data para la monitorización y predicción del estrés térmico en arrecifes de coral**  
*Proyecto de IA y Big Data — Fase 1: Planificación Técnica*

---

## 1. Integrantes

* **Pedro José Boceta Domínguez**
* **Javier Badías**
* **Vanessa Casique Gasco**
* **Paolo Michele Denis**

---

## 2. Resumen ejecutivo

Los arrecifes de coral sufren blanqueamiento y mortalidad masiva cuando las olas de calor marinas elevan la temperatura del agua durante semanas. Aunque existen datos satelitales abiertos desde 1985, su volumen dificulta compararlos entre regiones y anticipar el riesgo. 

**CoralHeat** propone un pipeline Big Data que ingiere series diarias de temperatura superficial del mar, anomalías, HotSpot y *Degree Heating Weeks* (DHW) de **NOAA Coral Reef Watch** para la Gran Barrera de Coral y el Caribe. Los procesa con **Apache Spark** en una arquitectura medallón, detecta episodios de estrés térmico y entrena un modelo de Machine Learning (evaluado con partición temporal y frente a un baseline de persistencia) que predice el estrés severo a cuatro semanas. 

Los resultados se publican mediante una API y un dashboard con mapas y series temporales. El valor está en una alerta temprana comparable entre regiones, reproducible con datos abiertos y sin datos personales, y en una arquitectura escalable a nuevas zonas.

---

## 3. Descripción funcional del sistema

### 3.1. Qué hace la aplicación
CoralHeat es un sistema analítico que automatiza el ciclo completo de los datos de estrés térmico:
1. Descarga datos satelitales abiertos de las regiones seleccionadas.
2. Los limpia y agrega a escala semanal con Spark.
3. Calcula indicadores (anomalía, HotSpot, DHW).
4. Detecta episodios de estrés.
5. Entrena un modelo que estima la probabilidad de estrés severo ($DHW \ge 4 ^\circ\text{C}\text{-semanas}$) en las siguientes 4 semanas.
6. Lo presenta en un dashboard interactivo.

### 3.2. Flujo general de uso
* **Ingesta:** Descarga por región y rango de fechas desde NOAA CRW (Bronze, Parquet).
* **Procesamiento:** Máscara de tierra, tratamiento de nulos y agregación semanal por celda (Silver).
* **Análisis:** Recálculo del DHW propio, validación frente al oficial, detección de episodios, features de lag y estacionalidad (Gold).
* **Predicción:** Baseline + modelo ML; resultados y métricas guardados con su `model_version`.
* **Consulta:** El usuario abre el dashboard, elige región y fecha, y consulta mapas, series y predicciones a través de la API.

### 3.3. Casos principales de usuario

| Usuario | Caso de uso | Resultado |
| :--- | :--- | :--- |
| **Investigador/a** | Compara la evolución del DHW entre el Caribe y la Gran Barrera de Coral (1985-actualidad). | Series temporales superpuestas y estadísticos por década. |
| **Gestor/a de área marina** | Consulta el riesgo previsto para las próximas 4 semanas en su región. | Mapa de probabilidad de estrés severo por celda y fecha de emisión. |
| **Analista de datos** | Contrasta los episodios detectados con blanqueamientos observados. | Tabla de coincidencias y métricas de acierto por región. |
| **Docente / evaluador** | Reproduce el pipeline completo con un comando. | `docker-compose up` ejecuta ingesta + dashboard sobre un subconjunto. |

### 3.4. Qué puede y qué no puede hacer

| El sistema PUEDE | El sistema NO PUEDE |
| :--- | :--- |
| Analizar históricos 1985-actualidad en 2-3 regiones. | Operar como sistema de alerta en tiempo real con garantías operativas. |
| Detectar y catalogar episodios de estrés térmico. | Afirmar causalidad: el estrés térmico es un factor del blanqueamiento, no el único (luz, calidad del agua, especie, etc.). |
| Predecir el estrés severo a 1-4 semanas con métricas honestas frente a un baseline. | Resolver por debajo de ~5 km ni distinguir microhábitats. |
| Mostrar mapas, series y comparaciones entre regiones. | Predecir mortalidad ni recuperación del coral. |
| Ejecutarse de forma reproducible con Docker Compose. | |

> **Nota científica relevante:** El DHW se deriva de la temperatura superficial del mar (SST), por lo que predecir el DHW equivale en gran parte a predecir la temperatura. Por ello el modelo incorpora estacionalidad, lags y anomalías, y se evalúa siempre contra un baseline de persistencia: un modelo solo es útil si lo supera.

---

## 4. Alcance definitivo (IN / OUT)

| Categoría | Elementos |
| :--- | :--- |
| **INCLUYE (Mínimo obligatorio)** | • Dos regiones: Gran Barrera de Coral y Caribe.<br>• Ingesta automatizada y reproducible de NOAA CRW (SST, anomalía, HotSpot, DHW).<br>• Procesamiento con PySpark y arquitectura medallón (Bronze/Silver/Gold) en Parquet.<br>• Cálculo de anomalías y de un DHW propio validado contra el oficial.<br>• Detección de episodios de estrés térmico.<br>• Un modelo de ML con baseline de persistencia y partición temporal.<br>• Capa Gold cargada en PostgreSQL/PostGIS.<br>• API REST de consulta (FastAPI).<br>• Dashboard con mapa de DHW, series temporales y comparación de regiones.<br>• Despliegue local con Docker Compose, pruebas básicas y documentación. |
| **INCLUYE (Opcional)** | • Tercera región (Mar Rojo o Triángulo de Coral).<br>• Filtrado de celdas por hábitat del Allen Coral Atlas.<br>• Validación con observaciones de blanqueamiento (Global Coral Bleaching Database).<br>• Comparación de varios modelos (XGBoost, Random Forest, Spark MLlib).<br>• Regresión de DHW máximo a 1-4 semanas.<br>• Simulación de ingesta en streaming con Kafka (etiquetada como simulada).<br>• CI con GitHub Actions. |
| **NO INCLUYE** | • Datos *in situ* de boyas ni imágenes satelitales en bruto.<br>• Predicción de mortalidad o recuperación del coral.<br>• Alertas en tiempo real operativas ni notificaciones a usuarios.<br>• Autenticación y gestión de usuarios.<br>• Despliegue en producción en la nube.<br>• Cobertura global desde el inicio (solo se escala si el pipeline funciona y hay tiempo). |

---

## 5. Arquitectura del sistema (alto nivel)

```
[FUENTES]                  [INGESTA]               [PROCESAMIENTO (Spark)]             [SERVICIO / ML]                  [PRESENTACIÓN]
NOAA Coral Reef Watch  ──> Ingesta             ──> BRONZE (Parquet crudo)        ──> PostgreSQL + PostGIS        <──> Backend API REST (FastAPI)
Allen Coral Atlas          (Python, xarray,        SILVER (Nulos, semanal)            (Tablas analíticas)                 │
Obs. Blanqueamiento         ERDDAP/HTTP)           GOLD (Features, DHW propio)   ──> Servicio ML (Modelos, Metrics) └──> Frontend Dashboard (Streamlit)
```

### Componentes del Sistema

| Componente | Función | Entrada | Salida |
| :--- | :--- | :--- | :--- |
| **Pipeline de datos (ingesta)** | Descarga de NOAA CRW por región y rango de fechas (ERDDAP/HTTP), lectura de NetCDF con xarray y escritura en Bronze. Reintentos, logs y caché local. | NetCDF | Parquet crudo |
| **Procesamiento Spark (Silver)** | Máscara de tierra, tratamiento de nulos, tipado, agregación semanal por celda; particionado por región/año. | Bronze | Silver |
| **Procesamiento Spark (Gold)** | Features (lags, medias móviles, estacionalidad), recálculo del DHW, detección de episodios, etiqueta de predicción. | Silver | Gold |
| **Base de datos** | PostgreSQL + PostGIS como capa de consulta: celdas georreferenciadas, observaciones, episodios, predicciones y ejecuciones de modelo. | Gold | Tablas SQL |
| **Servicio ML** | Entrenamiento con partición temporal, baseline de persistencia, modelo (XGBoost/MLlib), evaluación y registro de métricas en `model_run`. | Gold | Predicciones + métricas |
| **Backend (API)** | FastAPI con endpoints de regiones, observaciones, episodios y predicciones. Valida parámetros y desacopla el dashboard de la BD. | SQL | JSON |
| **Frontend / Dashboards** | Streamlit con Plotly y Folium: mapa de DHW por fecha, series, comparación entre regiones, predicción a 4 semanas y avisos de limitaciones. | JSON | Visualizaciones |
| **Otros servicios** | Airflow/Prefect (orquestación), Docker Compose (entorno), Git/GitHub y pytest. | - | - |

> **Decisión de diseño:** Se guarda el dato masivo en Parquet (barato y escalable para Spark) y solo se carga en PostgreSQL lo agregado y consultable, para que el dashboard responda con rapidez sin recorrer el histórico completo.

---

## 6. Tecnologías seleccionadas

| Tecnología | Uso | Por qué se ha elegido | Alternativa descartada |
| :--- | :--- | :--- | :--- |
| **Python 3.11** | Lenguaje principal | Ecosistema científico (xarray, pandas, scikit-learn) y soporte nativo de PySpark. | R (peor integración con el stack Big Data) |
| **SQL** | Consultas y modelo relacional | Estándar para la capa analítica y espacial. | - |
| **Apache Spark (PySpark)** | Procesamiento masivo | Procesa cientos de millones de filas con particionado y es la referencia del ecosistema Big Data. | Dask (menor peso en el ecosistema); pandas (no escala) |
| **xarray + netCDF4** | Lectura de NetCDF | Manejo natural de cubos multidimensionales (tiempo, lat, lon). | GDAL directo (más verboso) |
| **Parquet** | Formato de almacenamiento | Columnar, comprimido y particionable; mucho más rápido y pequeño que CSV. | CSV, JSON |
| **PostgreSQL + PostGIS** | Capa de consulta | Datos tabulares y espaciales con relaciones claras; consultas geográficas nativas. | MongoDB (sin ventaja en datos tabulares) |
| **scikit-learn / XGBoost** | Modelos ML | Buen rendimiento en datos tabulares con series; fácil de interpretar y validar. | Redes LSTM (más coste; se valorarán solo si sobra tiempo) |
| **FastAPI** | Backend | Rápido, tipado, con documentación OpenAPI automática. | Flask, Django |
| **Streamlit + Plotly + Folium** | Dashboard | Desarrollo ágil con mapas y gráficos interactivos. | Grafana / Superset (menos flexibles para mapas ML) |
| **Airflow o Prefect** | Orquestación | Dependencias entre tareas, reintentos y planificación. | Cron (sin trazabilidad) |
| **Docker Compose** | Entorno reproducible | Un comando levanta todos los servicios. | Instalación manual |
| **Git/GitHub, pytest** | Control de versiones y tests | Estándar de colaboración y de pruebas en Python. | - |

---

## 7. Modelo de datos

### 7.1. Descripción general
El modelo de datos se compone de tres tablas relacionales principales que organizan la información geográfica y los registros históricos de temperatura y estrés térmico, facilitando el análisis y la alimentación de los modelos de Machine Learning.

### 7.2. Estructura de las tablas

#### Tabla `REGIONES`
Contendrá las zonas geográficas de estudio (e.g., Gran Barrera de Coral, Caribe).

| Campo | Tipo | Descripción |
| :--- | :--- | :--- |
| `region_id` | Entero | Identificador único. Clave primaria (PK) |
| `nombre` | Texto | Nombre de la región |
| `zona_geografica` | Texto | País o zona geográfica |

#### Tabla `UBICACIONES_ANALISIS`
Almacenará los puntos geográficos concretos (celdas/coordenadas).

| Campo | Tipo | Descripción |
| :--- | :--- | :--- |
| `ubicacion_id` | Entero | Identificador único. Clave primaria (PK) |
| `region_id` | Entero | Identificador de región. Clave foránea (FK) |
| `latitud` | Decimal | Coordenada de latitud |
| `longitud` | Decimal | Coordenada de longitud |

#### Tabla `REGISTROS_TERMICOS`
Contendrá los datos históricos e indicadores de estrés térmico asociados a cada ubicación y fecha.

| Campo | Tipo | Descripción |
| :--- | :--- | :--- |
| `registro_id` | Entero | Identificador único. Clave primaria (PK) |
| `ubicacion_id` | Entero | Identificador de ubicación. Clave foránea (FK) |
| `fecha` | Fecha | Fecha de la observación |
| `sst` | Decimal | Temperatura superficial del mar ($^\circ\text{C}$) |
| `ssta` | Decimal | Anomalía de temperatura ($^\circ\text{C}$) |
| `hotspot` | Decimal | Indicador de exceso térmico ($^\circ\text{C}$) |
| `dhw` | Decimal | Estrés térmico acumulado ($^\circ\text{C}\text{-semanas}$) |

### 7.3. Relaciones entre las tablas
* **`REGIONES` $\rightarrow$ `UBICACIONES_ANALISIS`:** Relación 1:N.
* **`UBICACIONES_ANALISIS` $\rightarrow$ `REGISTROS_TERMICOS`:** Relación 1:N.

Se controlarán registros duplicados considerando ubicación, fecha y versión de la fuente.

---

## 8. Datos: fuentes, calidad y riesgos

### 8.1. Fuentes de datos
* **NOAA Coral Reef Watch (CRW):** Fuente principal (SST, SSTA, HotSpot, DHW, BAA). Resolución de ~5 km, actualización diaria, formato NetCDF4.
* **Allen Coral Atlas:** Distribución y mapas de hábitat de arrecifes de coral.
* **Global Coral Bleaching Database (Opcional):** Observaciones reales de blanqueamiento para validación.

### 8.2. Licencias y uso de datos
* **NOAA CRW:** Acceso público con atribución.
* **Allen Coral Atlas:** Generalmente Creative Commons CC BY 4.0.

### 8.3. Calidad y Riesgos

| Riesgo | Impacto | Probabilidad | Plan de mitigación | Área afectada |
| :--- | :--- | :--- | :--- | :--- |
| **No disponer de datos suficientes o comparables** | Media | Alta | Usar solo 1-2 regiones y acotar periodos; registrar los faltantes. | Datos |
| **Formatos o resoluciones diferentes entre fuentes** | Alta | Media | Validar coordenadas, fechas y resolución antes de cruzar fuentes; integrar solo a escala compatible. | Integración |
| **Datos muy grandes para el equipo** | Media | Media | Procesar subconjuntos por zona y fecha; ampliar solo si el entorno lo permite. | Procesamiento |
| **Predicciones con resultados poco fiables** | Alta | Media | Crear modelo base y evaluar con separación temporal; si falla, priorizar análisis y predicción de DHW con alcance reducido. | ML |
| **Falta de tiempo o contribuciones descoordinadas** | Alta | Alta | Asignar responsables, abrir issues, revisar avances y priorizar funcionalidades mínimas. | Equipo |
| **Fallos de repositorio, ejecución o dependencias** | Alta | Media | Usar PR, README, `.gitignore`, instrucciones de entorno y pruebas antes de fusionar. | Desarrollo |

---

## 9. Ética, legalidad y accesibilidad

* **Protección de datos personales:** Proyecto exclusivo sobre variables ambientales. No contiene ni maneja datos personales.
* **Uso legal:** Uso de fuentes públicas con atribución y trazabilidad.
* **Sesgos y transparencia:**
  * Evaluación por separado entre regiones.
  * Uso de validación temporal.
  * Claridad en que las predicciones son herramientas de apoyo, no certezas absolutas ni diagnósticos definitivos.
* **Accesibilidad (WCAG):** Contraste adecuado de colores, información no dependiente solo del color, textos claros y gráficos legibles.

---

## 10. Backlog inicial

| ID | Historia de usuario | Criterios de aceptación | Prioridad |
| :--- | :--- | :--- | :--- |
| **HU01** | **Consultar regiones:** Seleccionar una región para analizar su evolución. | Se muestra lista disponible; al elegir una, solo se consultan sus datos. | **Alta** |
| **HU02** | **Consultar un periodo:** Seleccionar fechas para estudiar un intervalo. | Indica fecha inicial/final; muestra datos del intervalo e informa si no existen. | **Alta** |
| **HU03** | **Ver temperatura del mar:** Visualizar la SST. | Gráfico con fecha, valores y unidad ($^\circ\text{C}$); señala datos faltantes. | **Alta** |
| **HU04** | **Detectar anomalías:** Consultar SSTA y HotSpot. | Muestra variables explicadas e identifica periodos elevados. | Media |
| **HU05** | **Analizar estrés acumulado:** Consultar indicador DHW. | Muestra evolución temporal en $^\circ\text{C}\text{-semanas}$ con la fuente. | **Alta** |
| **HU06** | **Comparar regiones:** Comparar dos regiones en el mismo periodo. | Representa ambas series con escala y unidades comparables. | Media |
| **HU07** | **Revisar calidad de datos:** Conocer faltantes y duplicados. | Genera resumen de filas, faltantes y duplicados antes del análisis. | **Alta** |
| **HU08** | **Consultar información geográfica:** Ubicar zonas en mapa. | El mapa identifica las regiones seleccionadas y muestra la fuente. | Media |
| **HU09** | **Consultar una predicción:** Visualizar estimación futura de estrés. | Si hay modelo validado, muestra predicción con limitaciones; si no, informa. | Condicionada |
| **HU10** | **Exportar resultados:** Descargar resumen de datos. | Permite exportar tabla o gráfico con región, periodo, unidades y fuentes. | Media |

---

## 11. Plan de trabajo (13 semanas)

| Semanas | Fase | Actividades principales | Hito / Resultado |
| :---: | :--- | :--- | :--- |
| **1-2** | Datos y alcance | Confirmar regiones, fuentes, formatos y licencias; descargar muestra. | Muestra disponible y fuentes documentadas. |
| **3-4** | Limpieza y modelo | Preparar fechas, coordenadas y variables; comprobar calidad; adaptar modelo. | Dataset limpio inicial + diccionario de variables. |
| **5-6** | Integración y análisis | Relacionar información ambiental y geográfica; gráficos exploratorios. | Análisis exploratorio y comparación inicial de regiones. |
| **7-9** | Machine Learning | Definir variable objetivo, separar datos temporalmente, entrenar y evaluar. | Modelo de referencia con métricas registradas. |
| **10-11** | Visualización | Crear dashboard con gráficos, comparación regional y predicción. | Prototipo navegable con visualizaciones. |
| **12-13** | Pruebas y entrega | Verificar ejecución, limitaciones, documentación y versión final. | Proyecto reproducible y documentación final. |

---

## 12. Estrategia de desarrollo

* **Flujo de Git:** Trabajo mediante ramas (`feature/*` o `nombre-nf2`) e integración en `main` exclusivamente mediante *Pull Requests* (PR) revisadas.
* **Gestión de tareas:** Organización vía **GitHub Issues** con objetivos, asignados y criterios de aceptación. Commits atómicos y claros.
* **Validaciones:**
  * **Datos:** Verificación de esquemas, nulos y duplicados.
  * **Procesamiento:** Pruebas de integración de pipeline sobre muestras.
  * **ML:** Evaluación con split temporal estricto y comparación obligatoria vs baseline de persistencia.

---

## 13. Repositorio del proyecto

**URL del repositorio:** [https://github.com/Pedr950/coral-thermal-stress](https://github.com/Pedr950/coral-thermal-stress)

### Estructura del proyecto

```text
coral-thermal-stress/
├── README.md
├── .gitignore
├── docs/
│   ├── NF2_Documentacion_y_Diseno_Tecnico.pdf
│   ├── arquitectura.png
│   └── NF2_apartados_7_14_Javier.md
├── data/
├── environment/
└── src/
```

---

## Fuentes consultadas

* [NOAA Coral Reef Watch](https://coralreefwatch.noaa.gov/product/5km/index.php)
* [NOAA - Condiciones de uso y atribución](https://coralreefwatch.noaa.gov/satellite/docs/recommendations_crw_citation.php)
* [Allen Coral Atlas](https://allencoralatlas.org/)
* [Allen Coral Atlas - Recursos y descargas](https://allencoralatlas.org/resource)