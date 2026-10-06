# PROMPT_MAESTRO.md

# AGENTE FORENSE LOCAL — REGLAS PERMANENTES DEL PROYECTO

## 1. Propósito general

Este proyecto construye un **Agente Forense Local para Windows** capaz de automatizar progresivamente un flujo forense completo, desde la adquisición de una evidencia física hasta la generación del informe pericial final en Word.

El sistema deberá evolucionar por fases, manteniendo siempre:

- integridad de evidencia;
- trazabilidad;
- reproducibilidad;
- seguridad operacional;
- mínima intervención humana;
- separación entre hechos, resultados y conclusiones;
- comportamiento determinista en operaciones críticas;
- auditoría completa;
- reutilización de los formatos históricos reales de la organización.

Este archivo contiene las **reglas permanentes del proyecto**.

TRAE debe leer este archivo completo antes de:

- modificar código;
- crear nuevos módulos;
- cambiar arquitectura;
- iniciar un sprint;
- integrar una nueva herramienta;
- modificar estructura de carpetas;
- alterar flujos existentes.

Las tareas específicas de cada iteración estarán en archivos:

`SPRINT_XX.md`

En caso de conflicto:

1. prevalece `PROMPT_MAESTRO.md`;
2. luego el sprint activo;
3. luego una decisión técnica conservadora;
4. nunca se compromete la integridad de evidencia.

---

# 2. Entorno principal

Sistema operativo objetivo:

`Windows`

Layout físico del entorno:

```text
J:\AgenteForense\
├── AgenteForense\        ← Raíz del proyecto (PROJECT_ROOT)
├── ewftools-x64\         ← Herramientas EWF (EWFTOOLS_ROOT)
└── OllamaModels\         ← Almacén de modelos Ollama (OLLAMA_MODELS_ROOT)
```

Directorio raíz de instalación:

`J:\AgenteForense`

Directorio raíz del proyecto:

`J:\AgenteForense\AgenteForense`

Directorio raíz de casos:

`J:\AgenteForense\AgenteForense\casos`

Herramientas EWF:

`J:\AgenteForense\ewftools-x64`

Ejecutable principal de adquisición:

`J:\AgenteForense\ewftools-x64\ewfacquire.exe`

Ejecutable principal de verificación:

`J:\AgenteForense\ewftools-x64\ewfverify.exe`

Almacén de modelos Ollama:

`J:\AgenteForense\OllamaModels`

No modificar, borrar, reemplazar ni actualizar automáticamente las herramientas ubicadas dentro de:

`J:\AgenteForense\ewftools-x64`

salvo instrucción explícita.

---

# 3. Arquitectura global del sistema

El sistema final estará compuesto por agentes o módulos especializados.

Flujo objetivo:

```text
OPERADOR / PERITO
        │
        ▼
AGENTE DE IDENTIFICACIÓN
        │
        ▼
AGENTE DE ADQUISICIÓN
        │
        ▼
AGENTE AXIOM
        │
        ▼
AGENTE DE RESULTADOS
        │
        ▼
AGENTE DE INFORME
        │
        ▼
INFORME FINAL WORD
```

En una fase posterior se integrará Ollama como capa conversacional y de razonamiento.

Ollama no será autoridad directa sobre operaciones críticas.

---

# 4. Estructura oficial y definitiva de cada caso

Esta estructura debe considerarse un **contrato permanente del sistema**.

Cada caso debe residir en:

```text
<DESTINO>\
└── <NUMERO_CASO>\
    ├── case.json
    │
    ├── IDENTIFICACION\
    │
    ├── ADQUISICION\
    │
    ├── ANALISIS\
    │
    ├── RESULTADOS\
    │
    └── REPORTE\
```

No crear estructuras paralelas fuera de estas carpetas salvo archivos técnicos estrictamente necesarios en la raíz del caso.

No usar como estructura principal carpetas alternativas como:

- evidence
- acquisition
- analysis
- reports
- portable_case

si duplican las carpetas oficiales.

Subcarpetas técnicas sí pueden existir dentro de las carpetas oficiales cuando sea necesario.

---

# 5. Carpeta IDENTIFICACION

Ruta:

`<CASO>\IDENTIFICACION`

Aquí se guardan:

- fotografías generales de la evidencia;
- fotografías de etiquetas;
- fotografías de números de serie;
- fotografías de marca/modelo;
- fotografías de capacidad;
- fotografías de dispositivos o accesorios relacionados;
- fotografías relevantes para la identificación física.

El **Agente de Identificación** deberá analizar estas imágenes.

Objetivos:

- transcribir texto visible;
- identificar marca;
- identificar modelo;
- identificar número de serie;
- identificar capacidad;
- identificar tipo de dispositivo;
- identificar etiquetas de evidencia;
- vincular cada dato con la fotografía que lo sustenta.

Debe diferenciar:

- dato observado;
- lectura incierta;
- dato no disponible.

Nunca inventar información.

Si un número de serie o campo crítico no puede leerse con suficiente confianza:

marcar:

`LECTURA INCIERTA`

y requerir validación humana.

El sistema podrá generar metadata estructurada, por ejemplo:

```json
{
  "evidence_id": "EV01",
  "brand": "Western Digital",
  "model": "WD10SPZX",
  "serial": "WX1234567890",
  "capacity": "1 TB",
  "source_images": [
    "foto_frontal.jpg",
    "foto_serial.jpg"
  ],
  "confidence": "verified"
}
```

Los nombres exactos podrán evolucionar, pero la trazabilidad imagen → dato debe mantenerse.

---

# 6. Carpeta ADQUISICION

Ruta:

`<CASO>\ADQUISICION`

Aquí se guardan:

- imagen E01;
- hashes;
- logs de adquisición;
- metadata de adquisición;
- información de ewfacquire;
- resultados de verificación;
- información del dispositivo físico adquirido.

Objetivo de salida:

```text
ADQUISICION\
├── <CASO>.E01
├── hashes.*
├── acquisition.*
└── logs\
```

La organización interna puede evolucionar sin romper la carpeta principal.

---

# 7. Carpeta ANALISIS

Ruta:

`<CASO>\ANALISIS`

Aquí se guardan:

- caso de Magnet AXIOM;
- resultados de procesamiento;
- planilla XLS/XLSX del proceso;
- exportaciones estructuradas;
- metadata de análisis.

La planilla de proceso será una fuente estructurada crítica para el agente de informe.

Debe contener, cuando corresponda:

- fecha/hora de procesamiento;
- versión de AXIOM;
- fuente procesada;
- configuración;
- artefactos seleccionados;
- todos los resultados relevantes del procesamiento;
- cantidades;
- errores;
- advertencias;
- estado final;
- rutas de salida;
- observaciones;
- cualquier otro dato requerido por los informes históricos.

No depender únicamente de capturas de pantalla para generar el informe.

---

# 8. Carpeta RESULTADOS

Ruta:

`<CASO>\RESULTADOS`

Aquí se guarda:

- Portable Case generado por AXIOM;
- archivo comprimido del Portable Case;
- hash del archivo comprimido;
- tamaño del archivo comprimido;
- metadata de resultados;
- logs de creación/exportación.

Objetivo conceptual:

```text
RESULTADOS\
├── PortableCase\
├── <CASO>_PORTABLE.zip
├── hashes.*
└── metadata.*
```

El Portable Case debe conservarse.

No eliminarlo después de comprimirlo salvo instrucción explícita.

El archivo comprimido debe tener hash calculado y registrado.

---

# 9. Carpeta REPORTE

Ruta:

`<CASO>\REPORTE`

Aquí se genera y almacena:

`<CASO>_INFORME_FINAL.docx`

El informe Word se construirá utilizando:

- datos de IDENTIFICACION;
- datos de ADQUISICION;
- datos de ANALISIS;
- datos de RESULTADOS;
- `case.json`;
- informes históricos reales;
- plantillas o formatos históricos utilizados por la organización.

No inventar una estructura documental nueva si existen formatos históricos válidos.

---

# 10. case.json — índice maestro del caso

Cada caso debe tener:

`<CASO>\case.json`

Este archivo actúa como índice y contrato entre agentes.

Debe contener referencias estructuradas a:

- número de caso;
- estado general;
- evidencias;
- identificación;
- adquisición;
- análisis;
- resultados;
- reporte;
- timestamps;
- rutas;
- hashes;
- versiones de herramientas;
- estados de cada fase.

Ejemplo conceptual:

```json
{
  "case_number": "CASO-2026-001",
  "status": "IN_PROGRESS",
  "identification": {
    "status": "COMPLETED"
  },
  "acquisition": {
    "status": "VERIFIED",
    "e01": "ADQUISICION\\CASO-2026-001.E01"
  },
  "analysis": {
    "status": "COMPLETED",
    "axiom_case": "ANALISIS\\...",
    "process_sheet": "ANALISIS\\proceso.xlsx"
  },
  "results": {
    "status": "COMPLETED",
    "portable_case": "RESULTADOS\\PortableCase",
    "archive": "RESULTADOS\\CASO-2026-001_PORTABLE.zip"
  },
  "report": {
    "status": "PENDING"
  }
}
```

Nunca mezclar datos entre casos.

---

# 11. Agente de Identificación

Responsabilidad:

analizar fotografías dentro de:

`IDENTIFICACION`

y producir datos estructurados.

Debe:

1. recorrer imágenes;
2. clasificarlas;
3. extraer texto visible;
4. identificar evidencia;
5. identificar marca/modelo/serial/capacidad;
6. vincular datos con sus fotografías;
7. generar una descripción inicial de la especie/evidencia;
8. marcar lecturas dudosas;
9. guardar metadata;
10. actualizar `case.json`.

No puede inventar seriales ni completar texto ilegible por inferencia.

La descripción obtenida durante IDENTIFICACIÓN debe limitarse a características, etiquetas, inscripciones y datos realmente visibles o sustentados por las fotografías y sus revisiones humanas. La ausencia de marca, modelo, número de serie u otro atributo no autoriza inferirlo ni completarlo. Los datos técnicos reportados posteriormente por el sistema o software de adquisición constituyen una fuente distinta y deben almacenarse separadamente con su propia provenance. La descripción visual y la descripción técnica de adquisición pueden combinarse posteriormente en el informe, pero nunca perder su trazabilidad individual.

Cuando la evidencia fotográfica/OCR no permita resolver de forma sustentada NUE, cantidad de especies, relación SELF_STORAGE/CONTAINED_STORAGE o cantidad de DSM, el agente debe solicitar explícitamente esos datos al operador, registrar la respuesta como fuente humana y bloquear la materialización hasta que toda la estructura obligatoria esté confirmada. Ninguna ausencia de información puede transformarse en un valor estructural por defecto.

---

# 12. Agente de Adquisición

Responsabilidad:

crear una imagen E01 física completa de un dispositivo seleccionado por el operador.

Debe ser determinista.

No depender de decisiones libres de un LLM.

Flujo base:

```text
detectar discos
↓
seleccionar candidato
↓
validar read-only
↓
validar caso
↓
validar destino
↓
revalidar origen
↓
ejecutar ewfacquire
↓
generar E01
↓
registrar hashes
↓
verificar
↓
cerrar adquisición
```

---

# 13. Regla fundamental de adquisición

Un disco solo puede considerarse candidato si Windows reporta:

```text
IsReadOnly = True
IsSystem   = False
IsBoot     = False
```

Regla permanente:

**SIN READ-ONLY = NO HAY ADQUISICIÓN**

No debe existir override manual.

Nunca convertir por software un disco en solo lectura para hacerlo elegible.

No ejecutar automáticamente `Set-Disk` para alterar atributos.

---

# 14. Bloqueador de escritura y Provenance de ReadOnly

El operador conecta físicamente el dispositivo mediante un bloqueador de escritura.

El software debe registrar exactamente la observación del sistema operativo y su provenance técnica.

Ejemplo:

`Windows IsReadOnly: True (Provenance: SYSTEM_DEVICE_ENUMERATION / Windows Storage API)`

Reglas permanentes de Provenance y ReadOnly:

1. **PROVENANCE TÉCNICA:** La propiedad `IsReadOnly` proviene únicamente de la consulta del bus/sistema operativo Windows (`SYSTEM_DEVICE_ENUMERATION` / `Get-Disk` / `Storage API`).
2. **NO INFERIR BLOQUEADOR FÍSICO:** El sistema NO debe inferir ni afirmar automáticamente la existencia, conexión o habilitación de un bloqueador de escritura por hardware (`Hardware Write Blocker`) a partir de `IsReadOnly = True`.
3. **SEPARACIÓN DE DECLARACIONES:** Toda declaración de bloqueador de hardware debe ser ingresada explícitamente como una declaración pericial/humana (`Provenance: HUMAN`) y distinguirse claramente de la observación del sistema operativo.
4. **COMPRESIÓN POR CAPACIDADES REALES:** La selección del nivel y método de compresión EWF debe realizarse dinámicamente mediante la inspección del binario local (`ewfacquire -h`). Se utilizará la máxima compresión demostrada por las capacidades reales alcanzadas (`deflate:best`).

---

# 15. Identificación de discos

Los discos físicos deben representarse como:

`\\.\PhysicalDriveN`

Ejemplo:

`\\.\PhysicalDrive6`

Nunca usar como fuente física:

- `E:\`
- `F:\`
- partición;
- volumen lógico;
- carpeta.

Obtener como mínimo:

- Number
- FriendlyName
- SerialNumber
- Size
- BusType
- IsReadOnly
- IsSystem
- IsBoot
- OperationalStatus
- HealthStatus

---

# 16. Protección del sistema

Nunca permitir como evidencia:

```text
IsSystem = True
```

o:

```text
IsBoot = True
```

No puede existir excepción manual.

---

# 17. No modificar evidencia

Está prohibido ejecutar automáticamente sobre el origen:

- formateo;
- inicialización;
- CHKDSK;
- reparación;
- montaje automático deliberado;
- modificación de particiones;
- cambio de atributos;
- DiskPart destructivo;
- escritura de firmas;
- conversión MBR/GPT;
- cambio de filesystem;
- limpieza;
- comandos que escriban en el medio.

El agente observa y lee.

---

# 18. Adquisición E01

Cuando se implemente o ejecute adquisición:

- origen: `\\.\PhysicalDriveN`;
- adquisición física completa;
- desde inicio físico;
- hasta fin del dispositivo;
- incluir particiones;
- incluir espacio no asignado;
- incluir estructuras fuera de particiones;
- formato E01/EWF;
- máxima compresión soportada;
- objetivo de un único archivo `.E01`;
- sin segmentación intencional;
- verificación posterior obligatoria.

---

# 20. Semántica Canónica de Tamaños en Adquisición

Se prohíbe utilizar la etiqueta o concepto genérico "Tamaño" para datos de distinta naturaleza técnica. El sistema debe distinguir e informar cuatro magnitudes independientes:

1. **`physical_device_size_bytes`**: Tamaño físico total del dispositivo `\\.\PhysicalDriveN` obtenido mediante enumeración técnica del sistema operativo Windows (`SYSTEM_DEVICE_ENUMERATION` / `Get-Disk`). Es la cantidad total de bytes que serán adquiridos físicamente.
2. **`source_volume_free_space_bytes`**: Espacio libre del volumen/filesystem ubicado dentro del medio fuente (si aplica y se consulta). Es estrictamente informativo. **El espacio libre del volumen fuente NO determina ni modifica el tamaño de la adquisición física completa.**
3. **`destination_free_space_bytes`**: Espacio libre real disponible en el filesystem destino donde se almacenará el archivo `.E01`. Se utiliza exclusivamente para la evaluación de capacidad del destino (`RAW_SIZE_CAPACITY_OK` / `LOW_FREE_SPACE_WARNING`).
4. **`ewf_segment_size_bytes`**: Tamaño máximo de segmento pasado a `ewfacquire` mediante el parámetro `-S`. Se deriva desde `physical_device_size_bytes` y las capacidades del binario para garantizar el objetivo de un único archivo `.E01` (sin segmentación intencional). No representa espacio libre ni garantiza el tamaño final del archivo comprimido.

---

# 21. Regla Permanente — Enumeración Fresca Previa a Cada Adquisición

Toda adquisición física constituye una nueva operación crítica.

Antes de CADA adquisición física real debe realizarse una enumeración fresca del hardware presente en el sistema operativo.

No se pueden reutilizar como autoridad operacional los datos provenientes de una enumeración anterior.

El número `PhysicalDriveN` es una referencia operativa temporal, NO una identidad persistente del dispositivo.

Flujo obligatorio previo a cada adquisición:
1. Enumerar discos físicos en el sistema en tiempo real.
2. Mostrar candidatos y discos bloqueados al operador.
3. Requerir selección humana explícita del dispositivo `PhysicalDrive`.
4. Capturar snapshot de identidad técnica (`Number`, `FriendlyName`, `SerialNumber`, `Size`, `BusType`, `IsReadOnly`, `IsSystem`, `IsBoot`).
5. Validar reglas de seguridad: `IsReadOnly=True`, `IsSystem=False`, `IsBoot=False`.
6. Validar filesystem y capacidad libre en destino (`destination_free_space_bytes`).
7. Calcular `ewf_segment_size_bytes` y construir el plan/argv de `ewfacquire`.
8. Mostrar el resumen previa de adquisición con la semántica canónica de tamaños.
9. **Doble Revalidación (Pre-ejecución):** Inmediatamente antes de invocar `ewfacquire.exe`, volver a enumerar el hardware, reidentificar el dispositivo seleccionado y verificar que mantiene `IsReadOnly=True`, `IsSystem=False`, `IsBoot=False`, tamaño idéntico y número de serie/identidad coincidente. Si hay cualquier discrepancia o sustitución de hardware, ABORTAR inmediatamente (Fail-Closed).
10. Solicitar confirmación humana interactiva explícita (`ADQUIRIR` / `CANCELAR`).

Sin confirmación interactiva `ADQUIRIR`, está prohibido iniciar la ejecución del binario `ewfacquire.exe`.

1. ejecutar `ewfacquire.exe -h`;
2. inspeccionar opciones reales;
3. modelar capabilities;
4. usar solo flags soportados;
5. registrar versión.

No inventar parámetros.

---

# 22. Regla Permanente — Reutilización de Estructura Materializada y Canónica del Caso

1. **Jerarquía Canónica Schema v2:** La ruta de adquisición física oficial para un dispositivo en un caso debe seguir estrictamente la estructura materializada:
   `<case_root>/ADQUISICION/NUE_<nue>/NUE_<nue>_ESPECIE<n>/NUE_<nue>_ESPECIE<n>_DSM<m>/`
2. **Identificadores Canónicos Persistidos:** Los IDs de Especie (`species_label`) y DSM (`label`) deben ser completos (ej. `NUE_7746368_ESPECIE1` y `NUE_7746368_ESPECIE1_DSM1`). Está estrictamente prohibido truncar o abreviar dichos identificadores a formas reducidas como `ESPECIE1` o `DSM1`.
3. **Reutilización de la Fuente de Verdad:** `planner.py` y el workflow de adquisición deben basar sus rutas en el `case_root` oficial persistido en `case.json` (ej. `J:\AgenteForense\AgenteForense\casos\RUC_24027199-0`). Está prohibido recalcular un caso base alternativo (como `J:\AgenteForense\AgenteForense\casos\...`) a partir de la entrada del usuario cuando el caso ya ha sido creado y materializado.
4. **Política Fail-Closed:** Ante cualquier divergencia entre las rutas o identificadores solicitados y la estructura física materializada existente en el disco (o si el directorio oficial de adquisición para el DSM no existe previa a la planificación, o si no pertenece al `case_root` oficial), el sistema debe ABORTAR inmediatamente la operación con un error estructural (`AcquisitionPreparationError`).
5. **Persistencia y Recarga Verificadas:** Una estructura confirmada solo se considera materializada después de persistir atómicamente `case.json`, descartar el contexto en memoria, recargarlo desde disco y verificar la coherencia entre JSON, filesystem, fotografías, hashes y metadata. La continuidad operacional debe usar exclusivamente el contexto recargado.
6. **Crear y Abrir son Operaciones Distintas:** El entrypoint debe ofrecer explícitamente `NUEVO CASO` y `ABRIR CASO EXISTENTE` como rutas separadas. `NUEVO CASO` sólo crea casos inexistentes y nunca sobrescribe un RUC ya materializado. `ABRIR CASO EXISTENTE` carga el `case.json` persistido, valida y reutiliza su `case_root`, no solicita un destino nuevo, no recrea estructura ni reinicializa metadata, y reanuda exclusivamente desde los estados persistidos. Si un RUC ya existe, debe abrirse, no recrearse.
7. **Reapertura sin Reinicialización:** Todo caso existente debe cargarse desde su `case_root` persistido. Está prohibido reinicializarlo, reconstruirlo desde conversación o informes no autoritativos, o sustituir sus campos estructurales por valores predeterminados vacíos.
8. **Protección contra Escrituras Desactualizadas:** Un `CaseContext` vacío o desactualizado no puede sobrescribir una revisión más reciente de `case.json`. Toda divergencia de revisión, un Schema v2 sin campos estructurales obligatorios o una discordancia JSON/filesystem debe rechazarse de forma Fail-Closed y requerir reconciliación explícita.
9. **Auditoría Estructural Previa a Adquisición:** La confirmación `CREAR`, la creación de directorios y la materialización de fotografías deben quedar en una auditoría durable atribuible al caso antes de seleccionar un DSM o enumerar dispositivos físicos.

---

# 20. Compresión

Usar la máxima compresión soportada por la versión local.

Si existe:

`best`

utilizarla.

Si la versión utiliza otra nomenclatura:

usar el máximo real soportado.

Registrar:

- método;
- nivel.

---

# 21. E01 único

Objetivo:

```text
<CASO>.E01
```

No:

```text
<CASO>.E01
<CASO>.E02
<CASO>.E03
```

Calcular tamaño de segmento dinámicamente según:

- tamaño exacto del origen;
- formato EWF;
- límites reales de ewfacquire;
- filesystem destino.

No segmentar silenciosamente como fallback.

Si no puede garantizarse un único E01:

abortar o requerir decisión explícita de diseño.

---

# 22. Filesystem destino

Verificar antes de adquisición:

- tipo de filesystem;
- espacio libre;
- capacidad para almacenar un archivo grande;
- que destino no esté en el mismo disco físico que origen.

Nunca formatear automáticamente el destino.

---

# 23. Agente AXIOM

Responsabilidad inicial:

automatizar procesamiento completo de la E01 en Magnet AXIOM.

La primera versión NO debe interpretar de forma autónoma relevancia probatoria.

Debe:

1. leer `case.json`;
2. tomar el mismo número de caso;
3. localizar la E01;
4. crear o abrir el caso AXIOM;
5. agregar la E01;
6. seleccionar todos los artefactos requeridos;
7. procesar;
8. esperar finalización;
9. registrar errores/advertencias;
10. guardar el caso en `ANALISIS`;
11. generar una planilla XLS/XLSX con el proceso;
12. actualizar `case.json`.

---

# 24. Automatización AXIOM

Antes de automatizar GUI:

priorizar:

1. API oficial;
2. CLI oficial;
3. mecanismo de automatización soportado;
4. Magnet AUTOMATE si está disponible y se decide utilizar;
5. automatización GUI controlada como último recurso.

No depender únicamente de coordenadas de pantalla.

No construir automatización frágil si existe interfaz oficial.

---

# 25. Planilla del proceso AXIOM

La planilla en:

`ANALISIS`

será una fuente principal del reporte.

Debe registrar los datos que el informe histórico requiera.

Como mínimo, considerar:

- número de caso;
- E01 procesada;
- hash de E01;
- versión AXIOM;
- fecha inicio;
- fecha fin;
- artefactos procesados;
- cantidades por categoría;
- errores;
- advertencias;
- resultados;
- observaciones;
- ruta del caso AXIOM;
- estado.

El formato exacto podrá ajustarse según los informes históricos reales.

---

# 26. Agente de Resultados

Responsabilidad:

1. generar Portable Case;
2. almacenarlo en `RESULTADOS`;
3. comprimirlo;
4. calcular hash del comprimido;
5. registrar tamaño;
6. registrar herramienta/método de compresión;
7. actualizar `case.json`.

No borrar el Portable Case original.

---

# 27. Agente de Informe

Responsabilidad:

generar el Word final dentro de:

`REPORTE`

No inventar un formato nuevo.

Debe aprender y reutilizar los **informes históricos reales**.

Los históricos sirven para aprender:

- estructura;
- títulos;
- subtítulos;
- estilo;
- redacción;
- disposición;
- tablas;
- numeración;
- ubicación de fotos;
- pies de figura;
- formato de hashes;
- presentación de resultados;
- forma de conclusiones.

Los históricos NO sirven como fuente de hechos del caso actual.

Nunca copiar hechos, nombres, fechas, hashes o resultados de casos antiguos al nuevo caso.

---

# 28. Uso de informes históricos

El agente debe analizar documentos históricos para identificar patrones.

Debe aprender:

- dónde van las fotografías;
- cómo se describe la evidencia;
- cómo se presenta marca/modelo/serial;
- cómo se documenta adquisición;
- cómo se muestran hashes;
- cómo se presentan resultados;
- cómo se construyen tablas;
- cómo se redactan conclusiones.

El caso nuevo debe alimentarse solo con datos de su propia carpeta.

---

# 29. Generación del Word

El agente de informe toma:

```text
IDENTIFICACION
+
ADQUISICION
+
ANALISIS
+
RESULTADOS
+
case.json
+
formatos históricos
```

y genera:

`REPORTE\<CASO>_INFORME_FINAL.docx`

Debe:

- insertar fotografías;
- mantener orden histórico;
- insertar identificación;
- redactar descripción de la especie;
- documentar adquisición;
- insertar nombre y hash de la E01;
- generar tablas de resultados;
- incorporar datos de AXIOM;
- documentar Portable Case;
- documentar hash del comprimido;
- redactar conclusiones basadas únicamente en datos disponibles.

---

# 30. Fotografías en el informe

El agente debe insertar imágenes según el patrón histórico.

Cada fotografía debe mantener trazabilidad con:

- archivo fuente;
- evidencia;
- descripción;
- ubicación dentro de IDENTIFICACION.

No alterar la imagen original.

Si se requiere una copia redimensionada para Word:

crear copia derivada sin modificar el original.

---

# 31. Descripción de la especie/evidencia

La descripción puede ser redactada automáticamente utilizando:

- fotografía;
- marca;
- modelo;
- serial;
- capacidad;
- tipo de medio;
- etiqueta de evidencia.

Debe distinguir dato observado de inferencia.

No completar campos inexistentes.

---

# 32. Resultados y tablas

Las tablas deben generarse con datos estructurados reales.

Fuentes preferentes:

1. planilla de `ANALISIS`;
2. metadata;
3. exportaciones de AXIOM;
4. `case.json`.

No contar manualmente si existe un valor oficial exportado.

No inventar categorías.

---

# 33. Conclusiones

Las conclusiones deben basarse exclusivamente en:

- evidencia observada;
- datos de adquisición;
- resultados AXIOM;
- resultados estructurados;
- hallazgos validados;
- información disponible en el caso.

No realizar acusaciones ni afirmaciones no sustentadas.

Separar:

- hecho;
- interpretación;
- conclusión.

---

# 34. Ollama

Ollama será integrado posteriormente.

Uso previsto:

- interfaz conversacional;
- redacción;
- clasificación;
- razonamiento;
- generación de texto;
- apoyo al análisis;
- interpretación de información estructurada.

No tendrá:

- shell libre;
- acceso irrestricto;
- capacidad de saltarse validaciones;
- autoridad para seleccionar automáticamente un disco físico crítico;
- autoridad para modificar evidencia.

---

# 35. Aprendizaje del agente

El aprendizaje inicial NO debe depender de fine-tuning.

Preferir:

- workflows;
- reglas;
- plantillas;
- ejemplos históricos;
- feedback humano;
- RAG;
- memoria estructurada;
- metadata.

El agente debe aprender procedimientos, no hechos de otros casos.

---

# 36. Workflows

Los procedimientos repetidos deben representarse de forma estructurada.

Ejemplos futuros:

```text
ANALISIS_PC_GENERAL
FUGA_DE_INFORMACION
MALWARE
USB
NAVEGACION_WEB
CORREO
DOCUMENTOS
```

No improvisar workflows críticos si ya existe uno validado.

---

# 37. Feedback humano

Cuando se habilite aprendizaje operativo:

el perito podrá indicar:

```text
RELEVANTE
NO RELEVANTE
REVISAR
```

Estas decisiones deben conservarse junto con:

- artefacto;
- contexto;
- regla;
- razón;
- workflow.

No reentrenar automáticamente pesos del modelo con cada caso.

---

# 38. Auditoría

Toda operación importante debe ser registrable.

Como mínimo:

- fecha/hora;
- número de caso;
- agente/módulo;
- herramienta;
- versión;
- acción;
- origen;
- destino;
- resultado;
- exit code;
- error;
- operador;
- confirmación humana cuando aplique.

---

# 39. Metadata y trazabilidad

Toda información debe poder rastrearse a su fuente.

Ejemplos:

```text
serial -> foto_serial_01.jpg
hash E01 -> ewfacquire/ewfverify
cantidad artefactos -> proceso.xlsx
Portable hash -> archivo ZIP
conclusión -> datos estructurados del caso
```

---

# 40. Estados del caso

Usar estados explícitos.

Ejemplo global:

```text
NEW
IDENTIFICATION_PENDING
IDENTIFICATION_COMPLETED
ACQUISITION_READY
ACQUIRING
ACQUISITION_COMPLETED
ACQUISITION_VERIFIED
ANALYSIS_PENDING
PROCESSING_AXIOM
ANALYSIS_COMPLETED
RESULTS_PENDING
PORTABLE_CREATED
REPORT_PENDING
REPORT_GENERATED
COMPLETED
FAILED
ABORTED
```

No es obligatorio usar exactamente estos nombres, pero sí una máquina de estados clara.

---

# 41. Privilegios

Si una operación requiere administrador:

- detectarlo;
- informar;
- registrar;
- detener si no se cumplen permisos.

No elevar privilegios silenciosamente.

---

# 42. Calidad del código

Priorizar:

- modularidad;
- claridad;
- type hints;
- modelos explícitos;
- tests;
- manejo de errores;
- logs;
- separación de responsabilidades;
- pocas dependencias;
- seguridad.

Evitar archivos monolíticos.

---

# 43. Manejo de errores

No mostrar únicamente tracebacks al operador.

Mostrar:

- qué falló;
- dónde;
- estado final;
- si el flujo se abortó.

Guardar detalles técnicos en logs.

Nunca continuar silenciosamente después de una validación crítica fallida.

---

# 44. Desarrollo por sprints

Cada sprint debe:

1. leer `PROMPT_MAESTRO.md`;
2. leer el sprint activo;
3. ejecutar tests previos;
4. inspeccionar estado real;
5. implementar unidad mínima;
6. probar;
7. corregir;
8. volver a probar;
9. revisar seguridad;
10. documentar.

No adelantar grandes funcionalidades fuera de alcance.

---

# 45. Regla de regresión

Ningún sprint se considera completo si rompe tests de sprints anteriores.

Todas las suites previas deben seguir pasando.

---

# 46. Operaciones reales

Durante desarrollo:

- mocks primero;
- tests primero;
- inspección primero.

Antes de operaciones reales sobre evidencia:

- mostrar resumen;
- requerir confirmación explícita;
- registrar confirmación.

---

# 47. No borrar artefactos parciales

Si una adquisición, procesamiento o exportación falla:

- conservar archivos parciales;
- no borrar silenciosamente;
- registrar estado;
- permitir análisis posterior.

---

# 48. Separación entre datos y presentación

Los datos técnicos deben almacenarse estructurados.

El Word es una salida de presentación.

Nunca usar el Word como única fuente de verdad.

La fuente de verdad debe estar en:

- `case.json`;
- metadata;
- XLS/XLSX;
- logs;
- hashes;
- resultados AXIOM.

---

# 49. Principio de no invención

Si falta un dato:

no inventar.

Si una fotografía no permite leer un serial:

marcarlo.

Si AXIOM no produjo un resultado:

no declararlo.

Si no existe hash:

no fabricarlo.

Si una conclusión no está sustentada:

no incluirla.

---

# 50. Principio final

Ante cualquier duda, elegir la opción que:

1. preserve la evidencia;
2. reduzca error humano;
3. deje trazabilidad;
4. sea reproducible;
5. sea verificable;
6. utilice datos reales;
7. respete la estructura oficial del caso;
8. no invente información;
9. mantenga compatibilidad con informes históricos;
10. facilite la automatización futura sin comprometer rigor forense.

La seguridad y trazabilidad forense tienen prioridad sobre comodidad y velocidad.

---

# 51. Investigación previa obligatoria antes de crear sprints

## Regla principal

**NO crear, aprobar ni ejecutar un sprint técnico sin investigar previamente todo lo necesario para que sus requisitos sean compatibles con la herramienta, versión, formato, entorno y comportamiento real involucrados.**

No construir criterios críticos sobre supuestos verificables.

## Antes de redactar cualquier sprint

Revisar, según corresponda:

1. estado actual del repositorio;
2. `PROMPT_MAESTRO.md`;
3. sprints anteriores y reportes finales;
4. suite de tests actual;
5. herramientas realmente instaladas;
6. versión exacta;
7. ayuda local;
8. documentación técnica primaria;
9. código fuente oficial si es necesario;
10. semántica real de flags;
11. semántica real de outputs;
12. hashes, estados y exit codes;
13. diferencias entre versiones;
14. casos límite;
15. criterios reales de éxito/fallo;
16. datos observados vs almacenados vs calculados vs inferidos;
17. información que la herramienta realmente puede producir;
18. riesgos forenses y de seguridad;
19. dependencias con fases futuras;
20. pruebas automatizadas y reales requeridas.

## Jerarquía de fuentes

Para comportamiento de herramientas:

1. binario local y ayuda local;
2. salida real capturada;
3. documentación oficial/primaria;
4. código fuente oficial;
5. documentación secundaria como apoyo.

Si hay discrepancia, no asumir: documentar y resolver antes de cerrar el sprint.

## Criterios de aceptación

Todo criterio crítico debe tener justificación técnica.

No exigir:

- campos inexistentes;
- etiquetas que una versión no utiliza;
- algoritmos no soportados;
- redundancias sin valor técnico;
- operaciones incompatibles con la semántica real de la herramienta.

Fail-closed significa:

**rechazar ante evidencia insuficiente, contradictoria o insegura.**

No significa:

**inventar requisitos imposibles o innecesarios.**

## Regla de detención

Si falta información material:

**NO crear todavía el sprint. Investigar primero.**

## Checklist obligatorio antes de entregar un sprint

Responder:

- ¿Conozco la versión real?
- ¿Conozco la semántica real de sus opciones?
- ¿Conozco el output real o esperado?
- ¿Los criterios de aceptación pueden cumplirse?
- ¿Los criterios de fallo representan fallos reales?
- ¿Hay alguna exigencia inventada o redundante?
- ¿Revisé los resultados previos?
- ¿Se preserva la evidencia?
- ¿Se evita trabajo forense innecesario/repetido?
- ¿Los tests cubren la semántica real?
- ¿Existe auditabilidad suficiente?

Si una respuesta material es `NO`, el sprint no está listo.

## Corrección de errores conceptuales

Si un sprint descubre que una política anterior estaba mal definida:

1. conservar el error en auditoría;
2. no ocultarlo;
3. corregir la política;
4. evitar repetir operaciones forenses si los artefactos existentes permiten reconciliar;
5. agregar tests que eviten recurrencia.

Esta regla aplica permanentemente a todos los sprints futuros del proyecto AGENTE FORENSE.
