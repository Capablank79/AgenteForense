# SPRINT_05_AGENTE_IDENTIFICACION_FOTOGRAFIAS.md

# Sprint 05 — Agente de Identificación: análisis, clasificación, renombrado y extracción estructurada desde fotografías

## 1. Objetivo
Implementar el Agente de Identificación sobre la jerarquía oficial:

```text
RUC
└── NUE
    └── ESPECIE
        └── DSM
```

El agente trabajará sobre las fotografías depositadas por el operador en las carpetas `FOTOS_PENDIENTES` creadas por Sprint 04.5.

Objetivos:
1. validar el número correcto de fotografías;
2. analizar las fotografías sin modificar los originales;
3. identificar qué representa cada foto;
4. extraer texto visible y atributos físicos;
5. generar datos estructurados de ESPECIE y DSM;
6. comparar datos visuales con datos técnicos existentes;
7. detectar conflictos;
8. renombrar de forma segura las fotografías;
9. preservar trazabilidad completa;
10. dejar metadata preparada para el futuro Agente de Informe.

No generar todavía Word.
No integrar AXIOM.

---

## 2. REGLA PERMANENTE — investigación previa obligatoria

Antes de implementar:
1. leer `PROMPT_MAESTRO.md`;
2. confirmar que contiene la regla permanente de investigación previa;
3. leer reportes Sprint 01–04.5;
4. ejecutar toda la suite actual;
5. registrar baseline real;
6. inspeccionar capacidades locales de visión/OCR;
7. identificar motores instalados realmente;
8. registrar versión de cada motor usable;
9. inspeccionar su interfaz/API/CLI real;
10. ejecutar pruebas no destructivas;
11. documentar limitaciones;
12. NO asumir que Ollama instalado implica capacidad de visión;
13. NO asumir que OCR por sí solo resuelve identificación visual;
14. NO descargar modelos o software automáticamente.

Si no existe un motor local capaz de analizar imágenes:
- implementar toda la arquitectura de identificación;
- dejar provider de visión desacoplado;
- bloquear únicamente la etapa automática de interpretación;
- informar exactamente qué falta;
- no inventar resultados.

---

## 3. Baseline

Antes de cambios:

```text
160 passed
```

o más si la suite creció legítimamente.

No aceptar regresiones.

---

## 4. Alcance

Implementar:
- ingestión de fotografías;
- validación de cantidad;
- clasificación visual;
- extracción de texto visible;
- extracción estructurada;
- nomenclatura fotográfica;
- renombrado seguro;
- metadata;
- comparación foto vs acquisition metadata;
- conflictos;
- revisión humana;
- estados;
- tests.

No implementar:
- AXIOM;
- XLS/XLSX de análisis;
- Portable Case;
- ZIP;
- informe Word final;
- conclusiones;
- lectura de petitorio;
- RAG histórico;
- aprendizaje autónomo.

---

## 5. Regla de tres fotografías

Se mantiene:

```text
EXACTAMENTE 3 FOTOGRAFÍAS POR OBJETO FÍSICO IDENTIFICABLE
```

Estados:

```text
0 fotos  -> PENDING
1-2      -> INCOMPLETE
3        -> READY
>3       -> REVIEW_REQUIRED
```

No borrar fotografías automáticamente.

---

## 6. SELF_STORAGE

Ejemplo:

```text
Pendrive = ESPECIE1 = DSM1
```

Carpeta:

```text
IDENTIFICACION└── NUE_<NUE>    └── NUE_<NUE>_ESPECIE<n>        └── FOTOS_PENDIENTES```

Las 3 fotografías pertenecen físicamente a la especie y al DSM.

No duplicar archivos.

DSM1 usa:

```text
photos_reference = SPECIES_PHOTOS
same_physical_object_as_species = true
```

---

## 7. CONTAINED_STORAGE

Ejemplo:

```text
Notebook = ESPECIE1
SSD      = DSM1
NVMe     = DSM2
```

Estructura:

```text
IDENTIFICACION└── NUE_<NUE>    └── NUE_<NUE>_ESPECIE1        ├── ESPECIE        │   └── FOTOS_PENDIENTES        └── DSM            ├── NUE_<NUE>_ESPECIE1_DSM1            │   └── FOTOS_PENDIENTES            └── NUE_<NUE>_ESPECIE1_DSM2                └── FOTOS_PENDIENTES```

Cada objeto físico tiene sus propias 3 fotos.

---

## 8. Protección de fotografías originales

Antes de analizar, registrar por archivo:

```text
original_filename
size_bytes
last_write_time
sha256
relative_path
```

El análisis NO puede modificar los bytes originales.

Antes de renombrar:
- conservar SHA-256;
- usar rename/move dentro de la misma carpeta;
- verificar SHA-256 después;
- el hash debe permanecer idéntico.

No recomprimir.
No re-guardar JPEG.
No editar EXIF.
No rotar físicamente la imagen.

La orientación visual puede corregirse solo en memoria.

---

## 9. Formatos permitidos

Investigar formatos realmente soportados por el motor elegido.

Como mínimo, si el stack local lo permite:

```text
.jpg
.jpeg
.png
```

Opcional:

```text
.heic
.tif
.tiff
```

No declarar soporte si la librería real no puede abrir el formato.

Archivo no soportado:

```text
UNSUPPORTED_IMAGE_FORMAT
```

---

## 10. Provider de visión desacoplado

Crear interfaz explícita, por ejemplo:

```text
VisionProvider
```

Métodos conceptuales:

```text
inspect_image(path)
extract_visible_text(path)
classify_view(path)
extract_evidence_attributes(paths, context)
```

Implementar provider concreto únicamente para herramientas realmente disponibles.

Ejemplos posibles solo si están instalados y verificados:

```text
OllamaVisionProvider
LocalVLMProvider
OCRProvider
```

No hardcodear un único proveedor en la lógica de negocio.

---

## 11. OCR no equivale a visión

Separar:

```text
OCR
```

de:

```text
VISUAL INTERPRETATION
```

OCR sirve para:
- etiquetas;
- seriales;
- modelo;
- capacidad;
- códigos visibles.

Visión sirve para:
- tipo de objeto;
- color;
- vista general;
- frontal/posterior;
- presencia de etiqueta;
- presencia de puertos/conectores;
- clasificación de foto.

No tratar OCR como suficiente para describir un notebook.

---

## 12. Vocabulario cerrado para tipo de foto

Permitidos inicialmente:

```text
GENERAL
FRONTAL
POSTERIOR
LATERAL
ETIQUETA
SERIAL
CONEXION
DETALLE
```

Si no puede determinar:

```text
NO_CLASIFICADA
```

y requerir revisión humana.

No inventar libremente nuevos sufijos.

---

## 13. Tres nombres únicos por objeto

Dentro de las 3 fotos de un objeto, cada clasificación final debe producir nombre único.

Ejemplo válido:

```text
GENERAL
ETIQUETA
SERIAL
```

Si el motor produce:

```text
GENERAL
GENERAL
ETIQUETA
```

no sobrescribir.

Si no puede resolver la duplicidad de forma sustentada:

```text
PHOTO_CLASSIFICATION_CONFLICT
```

y esperar revisión humana.

---

## 14. Nomenclatura final — ESPECIE

Formato:

```text
NUE_<NUE>_ESPECIE<n>_<TIPO>.ext
```

Ejemplos:

```text
NUE_777777_ESPECIE1_GENERAL.jpg
NUE_777777_ESPECIE1_ETIQUETA.jpg
NUE_777777_ESPECIE1_SERIAL.jpg
```

---

## 15. Nomenclatura final — DSM

Formato:

```text
NUE_<NUE>_ESPECIE<n>_DSM<m>_<TIPO>.ext
```

Ejemplos:

```text
NUE_777777_ESPECIE1_DSM1_GENERAL.jpg
NUE_777777_ESPECIE1_DSM1_ETIQUETA.jpg
NUE_777777_ESPECIE1_DSM1_SERIAL.jpg
```

---

## 16. SELF_STORAGE y nombres

En SELF_STORAGE, evitar duplicados físicos.

Usar nombres de ESPECIE como archivos físicos:

```text
NUE_777777_ESPECIE2_GENERAL.jpg
NUE_777777_ESPECIE2_ETIQUETA.jpg
NUE_777777_ESPECIE2_SERIAL.jpg
```

DSM1 referencia esas mismas rutas.

No crear copias `DSM1_*`.

---

## 17. Renombrado seguro

El renombrado se ejecuta solo después de:

1. analizar las 3 fotos;
2. producir propuesta;
3. verificar ausencia de colisiones;
4. verificar ausencia de conflicto crítico;
5. mostrar al operador;
6. recibir confirmación exacta:

```text
RENOMBRAR
```

No renombrar automáticamente sin confirmación humana en Sprint 05.

---

## 18. Rollback de renombrado

El proceso debe ser transaccional.

Antes:

```text
rename_plan.json
```

Incluye:

```text
source
target
sha256
```

Estrategia:
1. comprobar todos los targets;
2. usar nombres temporales si hace falta;
3. completar renombrado;
4. verificar existencia;
5. verificar hash;
6. persistir metadata.

Si falla a mitad, rollback cuando sea técnicamente seguro.

---

## 19. No sobrescribir

Si target ya existe:

```text
TARGET_FILENAME_EXISTS
```

No sobrescribir.

Revisión humana.

---

## 20. Datos estructurados de ESPECIE

Extraer solo si son observables:

```text
object_type
brand
model
serial
color
visible_labels
other_identifiers
```

No inventar.

---

## 21. Datos estructurados de DSM

Extraer cuando sean observables o técnicos:

```text
storage_type
brand
model
serial
capacity
interface
visible_labels
```

No inventar.

---

## 22. Fuente de cada campo

Cada atributo debe incluir procedencia.

Ejemplo:

```json
{
  "serial": {
    "value": "ABC123",
    "sources": [
      {
        "type": "PHOTO",
        "file": "NUE_..._SERIAL.jpg"
      }
    ],
    "status": "OBSERVED"
  }
}
```

Si además existe acquisition metadata:

```json
{
  "serial": {
    "value": "ABC123",
    "sources": [
      {"type": "PHOTO"},
      {"type": "ACQUISITION"}
    ],
    "status": "CONFIRMED"
  }
}
```

---

## 23. Estados de confianza

No usar porcentajes de confianza si el motor no entrega scores confiables.

Usar:

```text
OBSERVED
CONFIRMED
UNCERTAIN
CONFLICT
NOT_VISIBLE
NOT_AVAILABLE
```

---

## 24. Seriales y campos críticos

Críticos:

```text
serial
model
capacity
NUE label
ESPECIE label
DSM label
```

Si hay duda:

```text
UNCERTAIN
```

No rellenar caracteres faltantes.

No corregir por plausibilidad.

---

## 25. Comparación con adquisición

Para DSM con acquisition metadata, comparar:

```text
photo.model     vs acquisition.model
photo.serial    vs acquisition.serial
photo.capacity  vs acquisition.size/capacity
```

No exigir coincidencia textual exacta de capacidad nominal vs bytes.

Ejemplo:

```text
Foto: 16 GB
Sistema: 16.106.127.360 bytes
```

puede ser:

```text
CAPACITY_COMPATIBLE
```

solo si la regla de conversión está justificada y testeada.

---

## 26. Conflictos

Ejemplo:

```text
PHOTO SERIAL = ABC123
ACQUISITION SERIAL = ABC128
```

Resultado:

```text
IDENTIFICATION_CONFLICT
```

No elegir uno automáticamente.

Revisión humana.

---

## 27. Descripción técnica preliminar

Sprint 05 debe producir datos para la descripción futura.

Puede producir:

```text
description_draft
```

solo si:
- se construye desde campos confirmados;
- queda etiquetado `DRAFT`;
- no se trata como texto final pericial.

El Sprint de Informe usará los formatos históricos.

---

## 28. identification.json

Crear por entidad.

### ESPECIE

```text
IDENTIFICACIONNUE_777777NUE_777777_ESPECIE1identification.json
```

### DSM contained

```text
...\DSMNUE_777777_ESPECIE1_DSM1identification.json
```

Debe contener:

```text
entity_label
entity_type
storage_relation
photos
photo_hashes
photo_classifications
extracted_text
attributes
source_mapping
conflicts
human_review
status
provider
provider_version
processed_at
```

---

## 29. case.json

Actualizar schema v2 sin perder datos.

Por ESPECIE:

```text
identification.status
photos
attributes
conflicts
```

Por DSM:

```text
identification.status
photos/photo_reference
attributes
conflicts
```

Persistencia atómica obligatoria.

---

## 30. Estados de identificación

Permitidos:

```text
PENDING_PHOTOS
INCOMPLETE_PHOTOS
READY_FOR_ANALYSIS
ANALYZING
REVIEW_REQUIRED
IDENTIFIED
CONFLICT
FAILED
```

SELF_STORAGE debe mantener coherencia entre ESPECIE y DSM.

---

## 31. Revisión humana

Antes de confirmar identificación, mostrar resumen.

Requerir confirmación exacta:

```text
CONFIRMAR_IDENTIFICACION
```

Si no:

```text
REVIEW_REQUIRED
```

---

## 32. Correcciones humanas

Permitir corregir:
- clasificación;
- marca;
- modelo;
- serial;
- color;
- tipo;
- capacidad;
- interfaz.

Guardar:

```text
original_machine_value
human_value
timestamp
field
reason optional
```

No borrar lo observado originalmente por el motor.

---

## 33. Auditoría

Registrar eventos:

```text
photo_ingested
photo_hashed
photo_analyzed
photo_classified
text_extracted
attribute_detected
conflict_detected
rename_proposed
rename_confirmed
photo_renamed
identification_reviewed
human_correction
identification_confirmed
```

---

## 34. Privacidad y ejecución local

No enviar fotografías a servicios externos por defecto.

Si un provider requiere cloud/red externa:

ABORTAR esa integración en Sprint 05.

Procesamiento objetivo: local.

---

## 35. Criterio para motor local de visión

Solo usar un motor si:

1. está instalado localmente;
2. procesa imágenes realmente;
3. versión identificable;
4. interfaz automatizable;
5. no requiere subida externa;
6. ejecución reproducible;
7. puede aislarse detrás de `VisionProvider`.

Si no:

```text
VISION_PROVIDER_UNAVAILABLE
```

No inventar análisis.

---

## 36. Tests obligatorios

Mantener los 160 tests existentes.

Agregar al menos:

1. 0 fotos -> PENDING;
2. 1 -> INCOMPLETE;
3. 2 -> INCOMPLETE;
4. 3 -> READY;
5. 4 -> REVIEW_REQUIRED;
6. hash original preservado;
7. foto no modificada;
8. formato no soportado;
9. provider no disponible;
10. clasificación válida;
11. NO_CLASIFICADA;
12. nombres ESPECIE;
13. nombres DSM;
14. SELF_STORAGE no duplica;
15. collision target;
16. rename exige `RENOMBRAR`;
17. cancel rename conserva originales;
18. renombrado transaccional;
19. rollback;
20. serial extraído;
21. serial UNCERTAIN;
22. no inventar caracteres;
23. acquisition serial MATCH;
24. acquisition serial CONFLICT;
25. capacity compatible;
26. conflicto crítico -> REVIEW_REQUIRED;
27. identification.json;
28. case.json atomic update;
29. human correction audit;
30. `CONFIRMAR_IDENTIFICACION`;
31. provider externo bloqueado;
32. schema v1 intacto;
33. no ewfacquire;
34. no ewfverify;
35. no PhysicalDrive.

---

## 37. Prueba funcional real con fotografías

Solo después de implementar y pasar tests:

usar caso schema v2 de laboratorio.

Preferir un pendrive:

```text
SELF_STORAGE
ESPECIE1 = DSM1
```

El operador:

1. crea caso jerárquico;
2. copia 3 fotos reales a `FOTOS_PENDIENTES`;
3. inicia análisis;
4. revisa propuesta;
5. confirma `RENOMBRAR`;
6. revisa identificación;
7. confirma `CONFIRMAR_IDENTIFICACION`.

No ejecutar adquisición en esta prueba salvo sprint separado.

---

## 38. Qué intentar identificar en el pendrive

```text
object_type = pendrive / USB storage
brand si visible
model si visible
serial si visible
capacity si visible
visible labels
```

Comparar con datos técnicos solo si existe acquisition metadata asociada.

No asumir serial impreso.

---

## 39. Ausencia no es error

Si serial no es visible:

```text
serial = NOT_VISIBLE
```

No:

```text
FAILED
```

La identificación puede ser válida con campos no visibles.

---

## 40. Petitorio

No implementar todavía.

Pero `identification.json` y `case.json` deben permitir futura fuente:

```text
PETITORIO
```

sin cambiar schema principal.

---

## 41. Informe futuro

El futuro Agente de Informe debe consumir:

```text
entity_label
attributes
confirmed fields
photo paths
photo classifications
photo hashes
description data
```

No volver a ejecutar visión al crear el Word.

---

## 42. Definición de terminado

Sprint 05 queda COMPLETO si:

- regla permanente aplicada;
- baseline pasa;
- capacidades reales de visión investigadas;
- provider desacoplado;
- no cloud;
- regla 3 fotos;
- fotos hasheadas;
- clasificación implementada si hay provider real;
- lectura visible implementada si hay provider real;
- datos estructurados;
- conflictos;
- renombrado seguro;
- hash foto idéntico;
- SELF_STORAGE sin duplicación;
- identification.json;
- case.json actualizado;
- revisión humana;
- auditoría;
- schema v1 intacto;
- sin adquisición real;
- sin verificación real;
- todos los tests pasan.

Si no existe motor local usable:

```text
IMPLEMENTATION_COMPLETE_VISION_BLOCKED
```

solo si toda la arquitectura restante está implementada y se documenta qué capability falta.

No declarar identificación automática funcional si no fue probada.

---

## 43. Reporte final de TRAE

```text
SPRINT 05: COMPLETADO / INCOMPLETO / IMPLEMENTATION_COMPLETE_VISION_BLOCKED

BASELINE:
...

INVESTIGACIÓN PREVIA:
...

VISION PROVIDERS DETECTADOS:
...

PROVIDER SELECCIONADO:
...

VERSIÓN:
...

OCR:
...

PROCESAMIENTO LOCAL:
SI / NO

ARCHIVOS CREADOS:
...

ARCHIVOS MODIFICADOS:
...

VALIDACIÓN 3 FOTOS:
...

CLASIFICACIÓN:
...

EXTRACCIÓN:
...

RENOMBRADO:
...

SELF_STORAGE:
...

CONTAINED_STORAGE:
...

CONFLICTOS:
...

METADATA:
...

AUDITORÍA:
...

PRUEBA REAL CON FOTOS:
...

TESTS NUEVOS:
...

TESTS FINALES:
...

OPERACIONES FORENSES:
NINGUNA

RIESGOS / LIMITACIONES:
...

ESTADO:
LISTO / NO LISTO PARA SIGUIENTE SPRINT
```

No iniciar el siguiente sprint.

---

## 44. Instrucción final para TRAE

1. lee `PROMPT_MAESTRO.md`;
2. aplica la regla permanente;
3. lee este Sprint 05 completo;
4. ejecuta baseline;
5. inspecciona capacidades reales de visión/OCR;
6. no asumas que Ollama soporta imágenes;
7. no descargues automáticamente modelos;
8. implementa provider desacoplado;
9. implementa validación y hashing;
10. implementa análisis solo con provider local real;
11. implementa extracción estructurada;
12. implementa conflictos;
13. implementa renombrado transaccional;
14. implementa revisión humana;
15. preserva SELF_STORAGE;
16. actualiza metadata y case.json;
17. agrega tests;
18. deja suite en verde;
19. prueba con fotos de laboratorio solo si existe provider funcional;
20. no ejecutes ewfacquire;
21. no ejecutes ewfverify;
22. no accedas a PhysicalDrive;
23. no integres AXIOM;
24. no generes Word;
25. entrega reporte final;
26. no inicies el siguiente sprint.

Comienza ahora.
