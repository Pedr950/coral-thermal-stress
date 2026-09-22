# Monitorización y predicción del estrés térmico en arrecifes de coral

## Descripción

Proyecto de **Big Data e Inteligencia Artificial** orientado a la monitorización y predicción del estrés térmico en arrecifes de coral.

El proyecto analizará datos ambientales históricos para estudiar la evolución de la temperatura superficial del mar, las anomalías térmicas y diferentes indicadores relacionados con el estrés térmico de los arrecifes.

El análisis se centrará inicialmente en varias regiones del mundo con presencia de arrecifes de coral, como la **Gran Barrera de Coral (Australia)** y determinadas zonas del **Caribe**. Posteriormente, el sistema podrá ampliarse a otras regiones si el desarrollo del pipeline lo permite.

## Objetivos

Los principales objetivos del proyecto son:

* Analizar la evolución de la temperatura superficial del mar a lo largo del tiempo.
* Identificar anomalías y episodios de estrés térmico.
* Analizar indicadores como **DHW (Degree Heating Weeks)**.
* Comparar la evolución del estrés térmico entre diferentes regiones.
* Procesar grandes volúmenes de datos utilizando tecnologías Big Data.
* Desarrollar modelos de Machine Learning para intentar predecir el estrés térmico de las semanas siguientes.
* Representar los resultados mediante gráficos, dashboards y mapas.
* Construir un pipeline completo desde la adquisición de los datos hasta su análisis y visualización.

## Flujo del proyecto

El proyecto seguirá, de forma general, el siguiente flujo:

**Datos → Limpieza y preparación → Procesamiento Big Data → Análisis → Machine Learning → Predicción → Visualización**

## Regiones de estudio

Inicialmente se trabajará con varias regiones donde existe una importante presencia de arrecifes de coral.

Entre las zonas planteadas se encuentran:

* **Gran Barrera de Coral, Australia**
* **Región del Caribe**

El número de regiones podrá ampliarse posteriormente en función de los resultados obtenidos y de la disponibilidad de tiempo y recursos.

## Fuentes de datos

### NOAA Coral Reef Watch

Se utilizarán datos de **NOAA Coral Reef Watch** relacionados con el estrés térmico de los arrecifes de coral.

Entre los posibles datos a utilizar se encuentran:

* Temperatura superficial del mar.
* Anomalías de temperatura.
* HotSpot.
* DHW (Degree Heating Weeks).
* Alertas de estrés térmico y blanqueamiento.

### Allen Coral Atlas

Se utilizarán datos del **Allen Coral Atlas** para localizar y delimitar las zonas de hábitat de arrecifes de coral y establecer las áreas geográficas de interés para el análisis.

### Otras fuentes

Durante el desarrollo del proyecto podrán incorporarse otras fuentes de datos públicas que permitan contrastar los resultados, especialmente datos relacionados con episodios observados de blanqueamiento de coral.

## Tecnologías

Las tecnologías previstas para el desarrollo del proyecto incluyen:

* **Python**
* **Apache Spark**
* **Machine Learning**
* **GitHub**
* Herramientas de visualización y dashboards

Las tecnologías concretas podrán modificarse o ampliarse durante el desarrollo del proyecto en función de las necesidades del pipeline.

## Procesamiento de datos

El proyecto contempla la utilización de técnicas de procesamiento Big Data para trabajar con los datos ambientales históricos.

Entre las tareas previstas se encuentran:

1. Obtención de los datos.
2. Limpieza y preparación.
3. Transformación de los datos.
4. Integración de diferentes fuentes.
5. Procesamiento mediante herramientas Big Data.
6. Generación de variables e indicadores.
7. Análisis exploratorio.
8. Preparación de los datos para Machine Learning.

## Machine Learning

Se estudiará la posibilidad de desarrollar modelos de **Machine Learning** capaces de predecir el nivel de estrés térmico de los arrecifes en las semanas siguientes.

El modelo se entrenará utilizando datos históricos y variables ambientales disponibles.

La selección del algoritmo y de las variables definitivas se determinará durante la fase de análisis y experimentación.

## Visualización

Los resultados se representarán mediante diferentes tipos de visualizaciones, entre ellas:

* Evolución temporal del estrés térmico.
* Comparación entre regiones.
* Gráficos de temperatura y anomalías.
* Evolución del DHW.
* Mapas geográficos.
* Dashboards interactivos.

## Estructura del proyecto

La estructura del repositorio se irá definiendo a medida que avance el proyecto. Inicialmente se plantea una organización similar a:

```text
coral-thermal-stress/
│
├── data/
│   ├── raw/
│   └── processed/
│
├── notebooks/
│
├── src/
│
├── models/
│
├── dashboards/
│
├── docs/
│
├── requirements.txt
│
└── README.md
```

## Integrantes

* Pedro José Boceta Domínguez
* Vanessa Casique Gasco
* Paolo Michele Denis Magliano
* Javier Badías

## Estado del proyecto

**En desarrollo**

Actualmente se encuentra en fase de planificación y preparación de las fuentes de datos.

## Resultado esperado

El resultado final será un pipeline de Big Data e Inteligencia Artificial capaz de transformar datos ambientales históricos en información útil para:

**monitorizar → analizar → detectar → predecir → visualizar**

la evolución del estrés térmico en diferentes regiones de arrecifes de coral.
