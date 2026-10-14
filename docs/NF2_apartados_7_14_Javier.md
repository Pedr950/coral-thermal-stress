# NF2 - Documentación del proyecto

**Proyecto:** Monitorización y predicción del estrés térmico en arrecifes de coral

**Apartados:** 7, 8 y 9

**Responsable:** Javier Badías

## 7. Modelo de datos

### 7.1. Descripción general

Para organizar la información del proyecto se propone un modelo de datos formado por tres tablas relacionadas entre sí.

Estas tablas permitirán guardar las regiones de estudio, sus ubicaciones geográficas y los registros históricos de temperatura y estrés térmico.

El objetivo es mantener los datos organizados para facilitar su análisis y su posterior utilización en los modelos de Machine Learning.

### 7.2. Estructura de las tablas

**Tabla REGIONES**

Contendrá las zonas geográficas que vamos a estudiar, como la Gran Barrera de Coral (Australia) y algunas regiones del Caribe.

| Campo | Tipo | Descripción |
|---|---|---|
| region_id | Entero | Identificador único. Clave primaria (PK) |
| nombre | Texto | Nombre de la región |
| zona_geografica | Texto | País o zona geográfica |

**Tabla UBICACIONES_ANALISIS**

Almacenará los puntos geográficos concretos de los que obtendremos información ambiental.

| Campo | Tipo | Descripción |
|---|---|---|
| ubicacion_id | Entero | Identificador único. Clave primaria (PK) |
| region_id | Entero | Identificador de región. Clave foránea (FK) |
| latitud | Decimal | Coordenada de latitud |
| longitud | Decimal | Coordenada de longitud |

**Tabla REGISTROS_TERMICOS**

Contendrá los datos históricos de temperatura y los principales indicadores de estrés térmico asociados a cada ubicación y fecha.

| Campo | Tipo | Descripción |
|---|---|---|
| registro_id | Entero | Identificador único. Clave primaria (PK) |
| ubicacion_id | Entero | Identificador de ubicación. Clave foránea (FK) |
| fecha | Fecha | Fecha de la observación |
| sst | Decimal | Temperatura superficial del mar, en °C |
| ssta | Decimal | Anomalía de temperatura, en °C |
| hotspot | Decimal | Indicador de exceso térmico, en °C |
| dhw | Decimal | Estrés térmico acumulado, en °C-semanas |

### 7.3. Relaciones entre las tablas

Se establecen las siguientes relaciones:

- REGIONES → UBICACIONES_ANALISIS: relación 1:N. Una región puede contener varias ubicaciones.
- UBICACIONES_ANALISIS → REGISTROS_TERMICOS: relación 1:N. Una ubicación puede tener múltiples registros correspondientes a diferentes fechas.

Las claves primarias permitirán identificar cada elemento y las claves foráneas servirán para relacionar las tablas.

También se controlarán los registros duplicados, teniendo en cuenta la ubicación, fecha y versión de la fuente de datos utilizada.

```mermaid
erDiagram
    REGIONES ||--o{ UBICACIONES_ANALISIS : contiene
    UBICACIONES_ANALISIS ||--o{ REGISTROS_TERMICOS : registra

    REGIONES {
        int region_id PK
        string nombre
        string zona_geografica
    }

    UBICACIONES_ANALISIS {
        int ubicacion_id PK
        int region_id FK
        float latitud
        float longitud
    }

    REGISTROS_TERMICOS {
        int registro_id PK
        int ubicacion_id FK
        date fecha
        float sst
        float ssta
        float hotspot
        float dhw
    }
```


### 7.4. Consideraciones del modelo

Este modelo es provisional y podrá adaptarse cuando se descarguen los datos reales.

Será necesario comprobar sus formatos, unidades, resolución geográfica y temporal, así como la forma de relacionar los datos de distintas fuentes.

En una primera fase se utilizarán los datos necesarios para estudiar unas pocas regiones, evitando una estructura demasiado compleja.

---

## 8. Datos: fuentes, calidad y riesgos

### 8.1. Fuentes de datos

El proyecto utilizará principalmente datos ambientales históricos y geográficos procedentes de fuentes públicas.

**NOAA Coral Reef Watch**

Será nuestra fuente principal para analizar la temperatura del mar y los indicadores de estrés térmico.

Las variables previstas son:

- SST: temperatura superficial del mar.
- SSTA: anomalía de temperatura.
- HotSpot: exceso térmico respecto al valor de referencia.
- DHW: indicador de estrés térmico acumulado.
- BAA: niveles de alerta relacionados con el riesgo de blanqueamiento.

NOAA proporciona productos con una resolución espacial aproximada de 5 km y actualizaciones diarias. Los datos están disponibles, entre otros formatos, en NetCDF4.

**Allen Coral Atlas**

Se utilizará para obtener información geográfica sobre la localización y distribución de los arrecifes de coral.

Permitirá seleccionar las zonas que queremos estudiar y relacionarlas con los datos ambientales.

Las capas geográficas podrán descargarse en formatos adecuados para su tratamiento, según el producto seleccionado.

**Otras fuentes**

Si fuera necesario, se estudiará la incorporación de observaciones de blanqueamiento procedentes de fuentes científicas, siempre que tengan datos suficientes y condiciones de uso compatibles.

### 8.2. Licencias y uso de los datos

Los datos de NOAA Coral Reef Watch disponibles en su web son de acceso público y pueden reutilizarse, citando correctamente la fuente.

Los mapas de hábitats y otros datos cartográficos propios de Allen Coral Atlas se distribuyen generalmente bajo licencia Creative Commons CC BY 4.0, que requiere atribución.

No todos los recursos visuales del Atlas tienen necesariamente la misma licencia, por lo que verificaremos las condiciones concretas de cada producto antes de incorporarlo.

### 8.3. Volumen y actualización

El volumen definitivo dependerá de las regiones elegidas, el periodo histórico y las variables descargadas.

Inicialmente se propone trabajar con una muestra limitada de datos de dos regiones, como Australia y el Caribe.

Los productos de NOAA seleccionados tienen una actualización diaria. En el caso de Allen Coral Atlas, se consultará la versión disponible de los mapas y se actualizará cuando corresponda.

No se ha calculado todavía el tamaño exacto de las descargas, ya que será necesario seleccionar los archivos y realizar una primera prueba.

### 8.4. Calidad de los datos

Antes de utilizar los datos se realizará una revisión para comprobar:

- Valores faltantes y posibles duplicados.
- Formatos de fechas y coordenadas.
- Unidades de las variables.
- Valores fuera de los rangos esperados.
- Diferencias de resolución entre fuentes.
- Coherencia entre registros temporales y geográficos.

La limpieza se realizará principalmente con Python y las librerías que se determinen durante el desarrollo.

### 8.5. Riesgos y posibles soluciones

| Riesgo | Posible solución |
|---|---|
| Datos incompletos | Revisar los valores faltantes y utilizar periodos con suficiente información |
| Archivos demasiado grandes | Limitar inicialmente las regiones y fechas |
| Diferencias entre fuentes | Revisar formatos, coordenadas y resoluciones antes de unir los datos |
| Datos insuficientes para predicción | Reducir el alcance y centrarse en indicadores como DHW |
| Problemas de licencia | Comprobar las condiciones y sustituir los recursos si es necesario |

Los datos utilizados serán principalmente reales. Si se necesitan datos simulados para realizar pruebas, se identificarán claramente para no confundirlos con observaciones reales.

---

## 9. Ética, legalidad y accesibilidad

### 9.1. Protección de datos personales

El proyecto se centrará en información ambiental, como temperaturas del mar, fechas, coordenadas geográficas e indicadores de estrés térmico.

En principio, estos datos no contienen información personal de individuos.

Por este motivo, no se prevé utilizar nombres, direcciones, teléfonos ni otros datos que permitan identificar personas.

Si en el futuro se incorporasen usuarios registrados u otra información personal, sería necesario revisar los requisitos aplicables de protección de datos, incluido el Reglamento General de Protección de Datos (RGPD).

### 9.2. Uso legal de las fuentes

Se utilizarán fuentes públicas y se respetarán las condiciones de acceso, reutilización y atribución de cada conjunto de datos.

También se documentará la procedencia de la información para que los resultados sean trazables.

No se utilizarán datos de acceso restringido sin autorización.

### 9.3. Posibles sesgos

Uno de los principales riesgos es que los datos no representen todas las regiones de la misma forma.

Por ejemplo, puede haber diferencias en la cobertura geográfica, resolución o disponibilidad histórica de las mediciones.

Además, un modelo entrenado con datos de una región podría no funcionar igual de bien en otra.

Para reducir estos problemas se propone:

- Revisar la calidad de los datos antes del entrenamiento.
- Comparar los resultados entre regiones.
- Evaluar los modelos con datos no utilizados durante el entrenamiento.
- Explicar las limitaciones de las predicciones.
- Evitar presentar los resultados como certezas absolutas.

### 9.4. Uso responsable de la Inteligencia Artificial

El sistema tendrá una finalidad de análisis y apoyo a la investigación ambiental.

Las predicciones de Machine Learning serán estimaciones basadas en los datos disponibles y no deberán interpretarse como diagnósticos definitivos del estado de los arrecifes.

Los resultados ayudarán a identificar posibles situaciones de estrés térmico, pero las decisiones de conservación corresponderán a especialistas.

### 9.5. Accesibilidad

Si el proyecto incluye un dashboard o interfaz visual, se aplicarán medidas básicas de accesibilidad:

- Textos claros y fáciles de entender.
- Contraste adecuado entre colores.
- Gráficos con títulos, leyendas y unidades.
- Evitar que el color sea la única forma de representar información.
- Navegación sencilla y, cuando sea posible, mediante teclado.

Se tomarán como referencia las recomendaciones básicas de accesibilidad WCAG.

El objetivo es que los resultados puedan consultarse y entenderse de forma sencilla por distintos tipos de usuarios.

## 10. Backlog inicial

El backlog recoge las funcionalidades que queremos construir en fases posteriores. Las siguientes diez historias de usuario se centran en el análisis de las regiones, los indicadores térmicos y la visualización de resultados. Los criterios de aceptación permiten comprobar cuándo se considera terminada cada historia.

| ID | Historia de usuario | Criterios de aceptación |
|---|---|---|
| HU01 | **Consultar regiones.** Como investigador, quiero seleccionar una región para analizar su evolución térmica. | Se muestra una lista de regiones disponibles; al elegir una, solo se consultan sus datos. |
| HU02 | **Consultar un periodo.** Como investigador, quiero seleccionar fechas para estudiar un intervalo concreto. | El usuario indica fecha inicial y final; el sistema muestra datos del intervalo e informa si no existen. |
| HU03 | **Ver temperatura del mar.** Como investigador, quiero visualizar la temperatura superficial del mar (SST). | Se presenta un gráfico con fecha, valores y unidad °C; los datos faltantes se señalan. |
| HU04 | **Detectar anomalías.** Como investigador, quiero consultar las anomalías térmicas (SSTA y HotSpot). | Se muestran las variables disponibles con su explicación y se identifican periodos de valores elevados. |
| HU05 | **Analizar estrés acumulado.** Como investigador, quiero consultar el indicador DHW de una región. | Se muestra su evolución temporal en °C-semanas con la fuente de los datos. |
| HU06 | **Comparar regiones.** Como investigador, quiero comparar dos regiones en el mismo periodo. | El sistema representa ambas series con escala temporal y unidades comparables. |
| HU07 | **Revisar calidad de datos.** Como integrante del equipo, quiero conocer los valores faltantes y los registros duplicados. | El procesamiento genera un resumen de filas, faltantes y duplicados antes del análisis. |
| HU08 | **Consultar información geográfica.** Como investigador, quiero ubicar en un mapa las zonas de estudio. | El mapa identifica las regiones seleccionadas y muestra la fuente geográfica. |
| HU09 | **Consultar una predicción.** Como investigador, quiero visualizar una estimación futura del estrés térmico. | Si existe un modelo validado, se muestra la predicción indicando fecha, variable y limitaciones; si no, se informa que no está disponible. |
| HU10 | **Exportar resultados.** Como investigador, quiero descargar un resumen de los resultados para analizarlos. | El sistema permite exportar una tabla o gráfico con región, periodo, unidades y procedencia de los datos. |

**Prioridad inicial:** HU01, HU02, HU03, HU05 y HU07. La predicción (HU09) queda condicionada a disponer de datos suficientes y alcanzar resultados razonables en la evaluación del modelo.

## 11. Plan de trabajo

La planificación propuesta abarca unas 13 semanas de trabajo, ajustables al calendario real del curso. El orden tiene en cuenta las dependencias: antes de entrenar modelos hay que obtener y preparar los datos, y antes de visualizar predicciones hay que comprobar que el modelo funciona.

| Semanas | Fase | Actividades principales | Hito o resultado | Responsable previsto |
|---|---|---|---|---|
| 1–2 | Datos y alcance | Confirmar regiones, fuentes, formatos y licencias; descargar una muestra. | Muestra disponible y fuentes documentadas. | Javier (datos); Pedro (seguimiento) |
| 3–4 | Limpieza y modelo | Preparar fechas, coordenadas y variables; comprobar calidad; adaptar modelo de datos. | Dataset limpio inicial + diccionario de variables. | Javier; apoyo por asignar |
| 5–6 | Integración y análisis | Relacionar información ambiental y geográfica; gráficos exploratorios. | Análisis exploratorio y comparación inicial de regiones. | Por acordar en equipo |
| 7–9 | Machine Learning | Definir variable objetivo, separar datos en orden temporal, entrenar modelo base y evaluar. | Modelo de referencia con métricas registradas. | Por acordar en equipo |
| 10–11 | Visualización | Crear dashboard con gráficos, comparación regional y resultado del modelo si funciona. | Prototipo navegable con visualizaciones. | Por acordar en equipo |
| 12–13 | Pruebas y entrega | Verificar ejecución, limitaciones, documentación y versión final. | Proyecto reproducible y documentación final. | Equipo completo |

**Dependencias principales:** descarga de datos → limpieza y modelo de datos → integración y análisis → evaluación de modelos → dashboard → documentación y pruebas.

**Reparto de tareas en NF2 (14/10/2026):** Pedro está preparando los apartados 1–6 y Javier los apartados 7–14, pendiente de revisar solapamientos del apartado 7. Las responsabilidades de Vanessa y Paolo para el desarrollo posterior deben confirmarse con el equipo antes de considerarlas asignadas.

**Seguimiento:** se propone utilizar Discord para comunicación, GitHub Issues para tareas concretas y reuniones breves cuando haya decisiones o bloqueos. Se registrarán responsables y fecha objetivo de cada tarea.

## 12. Estrategia de desarrollo

**Flujo de Git:** `main` mantendrá los cambios revisados. Cada integrante trabajará en una rama propia o de funcionalidad (por ejemplo, `javier-nf2` o `feature/limpieza-noaa`). Para integrar el trabajo se abrirá una *Pull Request* que otra persona revisará antes de fusionarla. No se debería trabajar directamente sobre `main`.

**Organización:** las tareas se describirán en GitHub Issues, incluyendo objetivo, responsable y criterios para considerarlas finalizadas. Los cambios se harán en commits pequeños, con mensajes descriptivos.

**Validación básica:**

- **Datos:** comprobar formatos de fechas, columnas necesarias, coordenadas válidas, duplicados y valores faltantes.
- **Procesamiento:** ejecutar los scripts con una muestra pequeña y comprobar que producen los resultados previstos.
- **Machine Learning:** separar entrenamiento y prueba respetando el orden temporal; comparar el modelo con una referencia sencilla y registrar métricas como MAE o RMSE si se predice un valor numérico.
- **Visualización:** comprobar que filtros, etiquetas, unidades y gráficos corresponden al conjunto de datos seleccionado.
- **Reproducibilidad:** anotar versiones de librerías, fuentes y pasos para ejecutar el proyecto desde cero.

Si alguna prueba falla, el cambio se corregirá antes de incorporarlo a `main`.

## 13. Riesgos técnicos actualizados

Se priorizan los riesgos mediante una estimación cualitativa de impacto y probabilidad. Estas valoraciones son iniciales y se revisarán al trabajar con datos reales.

| Riesgo | Impacto | Probabilidad | Plan de mitigación | Área afectada |
|---|---|---|---|---|
| No disponer de datos suficientes o comparables | Media | Alta | Usar solo 1–2 regiones y acotar periodos; registrar los faltantes. | Datos |
| Formatos o resoluciones diferentes entre NOAA y Allen Coral Atlas | Alta | Media | Validar coordenadas, fechas y resolución antes de cruzar fuentes; integrar solo a escala compatible. | Integración |
| Datos muy grandes para el equipo | Media | Media | Procesar subconjuntos por zona y fecha; ampliar solo si el entorno lo permite. | Procesamiento |
| Predicciones con resultados poco fiables | Alta | Media | Crear modelo base y evaluar con separación temporal; si falla, priorizar análisis y predicción de DHW con alcance reducido. | ML |
| Falta de tiempo o contribuciones descoordinadas | Alta | Alta | Asignar responsables, abrir issues, revisar avances y priorizar funcionalidades mínimas. | Equipo |
| Fallos de repositorio, ejecución o dependencias | Alta | Media | Usar PR, README, .gitignore, instrucciones de entorno y pruebas antes de fusionar. | Desarrollo |

**Plan alternativo general:** si el modelo de predicción no alcanza resultados útiles, se mantendrá un sistema funcional de análisis histórico, comparación regional y visualización de los indicadores SST, SSTA, HotSpot y DHW. Se explicará expresamente esta limitación.

## 14. Repositorio del proyecto

El equipo dispone de un repositorio común: **https://github.com/Pedr950/coral-thermal-stress**. En el momento de esta propuesta, el repositorio ya contiene `README.md` y documentación inicial de Javier en la rama `javier-nf2`; falta confirmar o completar la estructura base que exige NF2.

**Estructura propuesta:**

```text
coral-thermal-stress/
├── README.md
├── .gitignore
├── docs/
│   ├── NF2_Documentacion_y_Diseno_Tecnico.pdf
│   ├── arquitectura.png
│   └── NF2_apartados_7_14_Javier.md
├── src/
├── data/
└── environment/
```

Las carpetas de trabajo podrán contener inicialmente un archivo `.gitkeep`, ya que Git no guarda directorios vacíos. No se subirán datasets pesados ni credenciales al repositorio.

El `README.md` final deberá explicar: objetivo del proyecto; integrantes y roles confirmados; arquitectura resumida; tecnologías previstas; enlaces a la documentación; e instrucciones básicas de puesta en marcha, aunque todavía no exista código funcional.

**Acciones pendientes para completar este apartado:** comprobar que `docs/` contiene el PDF de NF2 y el diagrama de arquitectura, crear las carpetas y `.gitignore` que falten, y actualizar `README.md` con la información exigida. La existencia de este plan no sustituye la creación de esos archivos en GitHub.


---

## Fuentes consultadas

- NOAA Coral Reef Watch: https://coralreefwatch.noaa.gov/product/5km/index.php
- NOAA - Condiciones de uso y atribución: https://coralreefwatch.noaa.gov/satellite/docs/recommendations_crw_citation.php
- Allen Coral Atlas: https://allencoralatlas.org/
- Allen Coral Atlas - Recursos, licencias y descargas: https://allencoralatlas.org/resources/

**Nota:** Esta documentación corresponde al diseño inicial de la segunda fase. El modelo de datos, los formatos y las estimaciones deberán revisarse cuando el equipo comience a trabajar con los datasets reales.
