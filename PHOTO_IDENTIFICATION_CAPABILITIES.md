# PHOTO_IDENTIFICATION_CAPABILITIES.md — Capacidades y Diseño del Agente de Identificación por Fotografías

## 1. BASELINE
- **Python**: `3.10.11`
- **Windows**: `Windows 10 Pro build 19045`
- **PostgreSQL**: `18.6`
- **Web App**: `127.0.0.1:8085` (FastAPI / Jinja2 / HTMX)
- **Tests**: `188 passed` (suite sin regresiones)
- **Petition Pipeline**: `PETITION_PIPELINE_READY`

---

## 2. OCR CAPABILITIES (Windows OCR)
- **Engine**: `Windows.Media.Ocr` (`winsdk` 1.0.0b10)
- **Idiomas**: `es-ES` / System default.
- **Capacidad**: Extracción textual pura a partir de imágenes bitmap.
- **Latencia observada**: ~80 ms - 120 ms por imagen en pruebas sintéticas local.
- **Limitaciones**:
  - NO realiza razonamiento semántico ni detecta la categoría visual del objeto.
  - Sensible a fuentes distorsionadas, bajo contraste, inclinaciones severas y artefactos (ej. leyó `WD10EZEk00BNspn` en lugar de `WD10EZEX-00BN5A0`).
  - No entrega directamente un modelo formal de campos clave-valor (`key-value`).

---

## 3. VISION PROVIDERS & OLLAMA INVENTORY
- **Ollama Version**: `0.40.0`
- **Modelos Instalados en Ollama**: `qwen2.5:3b` (1.9 GB)
- **Análisis de Capacidad Multimodal**:
  - `qwen2.5:3b`: Modelo estrictamente **Text-Only**. NO procesa tensores de imagen. Se clasifica únicamente como razonador sintáctico/estructurador sobre el texto plano extraído por OCR.
  - **Modelos VLM (Qwen2.5-VL / LLaVA / MiniCPM-V)**: `NOT_INSTALLED`.
- **Otros Frameworks en Entorno Python**:
  - `PyTorch`: `NOT_INSTALLED`
  - `OpenCV (`cv2`)`: `NOT_INSTALLED`
  - `ONNX Runtime / DirectML`: `NOT_INSTALLED`
  - `Pillow (PIL)`: `INSTALLED` (v12.3.0) — Usado para precarga, hash y decodificación.

---

## 4. DETERMINACIÓN DE CAPACIDAD DE VISIÓN REAL LOCAL
- **Estado de Visión Semántica**: **NO DISPONIBLE LOCALMENTE (`NO_VISION_PROVIDER`)**.
- **Conclusión de Arquitectura**: En R06 y el pipeline actual, la identificación asistida se basará en un pipeline híbrido:
  $$\text{Fotografía} \xrightarrow{\text{Inmutabilidad SHA256}} \text{Windows OCR} \xrightarrow{\text{Texto Plano}} \text{Qwen2.5:3b (Extractor de Campos)} \xrightarrow{\text{Validación Anti-Invención}} \text{Human Review}$$
- No existe procesamiento visual directo (bounding boxes visuales, detección de color de superficie por red neuronal, o clasificación de escena sin texto).

---

## 5. PHOTO COUNT POLICY (`PHOTO_COUNT_POLICY`)
- **Estado Actual**: Recomendación Operacional Recomendada, NO una regla dura de bloqueo estricto en el motor de persistencia.
- **Definición de Política**:
  - **Recomendado Estándar**: 3 fotografías por entidad física (General/Frontal, Etiqueta/Serial, Posterior/Conectores).
  - **Comportamiento por Cantidad**:
    - `0 fotos`: Permitido únicamente en fase preliminar de registro de acta si aún no se adjuntan archivos, pero el estado de identificación queda `IDENTIFICATION_PENDING`.
    - `1 a 2 fotos`: Válido si la etiqueta o serial es completamente visible y legible. Registra advertencia `WARN_LOW_PHOTO_COUNT`.
    - `3 fotos`: Cobertura estándar recomendada.
    - `>3 fotos`: Permitido para objetos complejos con múltiples conectores o daños físicos.
  - **Aplicación por Entidad**:
    - **ESPECIE**: Aplica norma de registro fotográfico.
    - **DSM**: Si es `CONTAINED_STORAGE`, aplica fotos de detalle del DSM específico. Si es `SELF_STORAGE` (donde la ESPECIE es el mismo DSM), se aplica la política de referencia compartida sin duplicación.

---

## 6. SELF_STORAGE & CONTAINED_STORAGE POLICIES

### 6.1 SELF_STORAGE (ESPECIE = DSM)
- Cuando un elemento físico es a la vez el contenedor y el medio de almacenamiento (ej. Disco Duro Externo, Pendrive, Laptop con disco no extraíble):
  - El archivo de fotografía se almacena en disco físico **una sola vez** en el directorio de la ESPECIE/DSM.
  - Los registros en base de datos (`forensic.photos`) asocian el mismo `photo_id` o referencia compartida tanto a la ESPECIE como al DSM correspondiente.
  - Se evita estrictamente la duplicación física de bytes en disco.

### 6.2 CONTAINED_STORAGE (ESPECIE con N DSMs)
- Estructura Jerárquica:
  - **ESPECIE (Contenedor)**: Fotos de Gabinete, Bolso, Torre, Consola.
  - **DSM1, DSM2... (Muestras Internas)**: Fotos específicas del componente extraído (Disco 1, Disco 2), fotografiando su serial propio.
- El pipeline permite asociar `entity_type: "ESPECIE" | "DSM"` y `entity_id` a cada `photo_id` para garantizar trazabilidad.

---

## 7. INMUTABILIDAD Y METADATA DE FOTOGRAFÍAS

### 7.1 Protocolo de Inmutabilidad
1. Cálculo de `SHA256_BEFORE` inmediatamente tras la ingesta/staging.
2. Invocación de herramientas (OCR, extracción, Pillow metadata).
3. Cálculo de `SHA256_AFTER`.
4. **Regla de Inmutabilidad**: $\text{SHA256}_{\text{before}} == \text{SHA256}_{\text{after}}$.
5. Prohibido: Recompresión JPEG, rotación física destructiva, edición de EXIF, recortes del original, aplicación de filtros.

### 7.2 Estructura de Metadata por Fotografía
```json
{
  "photo_id": "PHOTO-20261007-001",
  "entity_type": "DSM",
  "entity_id": "DSM-001",
  "original_filename": "IMG_20261007_143011.jpg",
  "relative_path": "casos/NUE123456/ESPECIE_01/DSM_01/photos/IMG_20261007_143011.jpg",
  "size_bytes": 2458112,
  "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "width": 4032,
  "height": 3024,
  "format": "JPEG",
  "captured_at": "2026-10-07T14:30:11Z",
  "classification": "ETIQUETA",
  "ocr_text": "WESTERN DIGITAL MODEL WD10EZEX S/N WCC6Y0123456 1.0TB",
  "analysis_status": "PROCESSED"
}
```

---

## 8. MODELO DE ATRIBUTOS, PROVENANCE Y ESTADOS POR CAMPO

### 8.1 Atributos Extraíbles
`object_type`, `brand`, `model`, `serial`, `capacity`, `color`, `visible_labels`, `part_number`, `imei`, `mac_address`.

### 8.2 Modelo de Provenance
Cada atributo extraído conserva su origen:
```json
{
  "field_name": "serial",
  "value": "WCC6Y0123456",
  "source_photo_id": "PHOTO-20261007-001",
  "source_region": null,
  "source_text": "S/N: WCC6Y0123456",
  "method": "WINDOWS_OCR_PLUS_QWEN2.5_TEXT",
  "status": "EXTRACTED",
  "confidence": null,
  "human_confirmed": false
}
```

### 8.3 Estados Posibles de Campo
- `OBSERVED`: Texto detectado en OCR sin estructurar.
- `EXTRACTED`: Atributo estructurado por LLM a partir de OCR.
- `UNCERTAIN`: Atributo parcial o dudoso (ej. serial incompleto).
- `NOT_VISIBLE`: El atributo no aparece en la imagen/OCR.
- `NOT_FOUND`: No se halló valor relevante.
- `CONFLICT`: Múltiples fotos u OCRs entregan valores discrepantes.
- `CONFIRMED`: Confirmado por el operador en Human Review.
- `CORRECTED_BY_HUMAN`: Modificado por el perito operador.
- `REJECTED_UNSUPPORTED`: Rechazado por invención o incoherencia.

### 8.4 Reglas Específicas de Validación
- **Serial**: Prohibido inferir o inventar caracteres no legibles. Si un carácter es borroso $\rightarrow$ State: `UNCERTAIN`.
- **Marca/Modelo**: Prohibida la inferencia comercial no explícita (ej. `GTX` no autoriza `NVIDIA` si `NVIDIA` no aparece en el texto o no es confirmado por humano).
- **Capacidad**: Normalización estructurada (ej. `1.0 TB` $\rightarrow$ `display_value: "1 TB"`, `bytes: 1000204886016`).
- **Color**: Al no existir visión semántica local $\rightarrow$ `NOT_EVALUATED` (requiere `HUMAN_REVIEW`).

---

## 9. MODELO DE CONFLICTOS (`CONFLICT MODEL`)
Tipos de conflicto auditados:
1. `SERIAL_MULTIPLE_VALUES`: Diferentes fotos reportan seriales distintos para la misma entidad.
2. `MODEL_MULTIPLE_VALUES`: Inconsistencia en modelo extraído.
3. `BRAND_CONFLICT`: Inconsistencia de marca.
4. `CAPACITY_CONFLICT`: Inconsistencia de capacidad.
5. `PHOTO_ENTITY_MISMATCH`: La foto adjunta parece pertenecer a otra entidad.
6. `LOW_VISIBILITY`: Texto ilegible o desenfocado.
7. `NO_TEXT`: OCR no detectó ningún texto en la fotografía.
8. `NO_VISION_PROVIDER`: Advertencia de ausencia de analizador VLM para atributos visuales puros (como color o daños).

---

## 10. REVISIÓN HUMANA Y RENOMBRADO SEGURO

### 10.1 Human Review
- La interfaz UI/Web desplegará un panel de inspección con:
  - Imagen inmutable (vista previa).
  - Texto OCR detectado.
  - Atributos propuestos con su estado (`EXTRACTED`, `UNCERTAIN`, `CONFLICT`).
  - Controles para Confirmar, Corregir o Rechazar cada campo.
- Toda acción del operador genera un registro en `forensic.audit_events`.

### 10.2 Renombrado Seguro de Archivos (Diseño Futuro)
- El archivo original **nunca** se sobrescribe ni altera en su contenido.
- Proceso de Renombrado Sugerido (si se habilita en R06.1+):
  1. Propuesta de nombre normalizado determinístico: `{NUE}_{ENTIDAD}_{CLASIFICACION}_{HASH8}.jpg`.
  2. Vista previa en UI (`Preview`).
  3. Verificación de colisiones (`Collision Check`).
  4. Confirmación Explícita Humana (`Human Confirmation`).
  5. Operación de renombrado/movimiento atómico.
  6. Recálculo de HASH posterior (`Hash After`).
  7. Rollback automático si HASH difiere.

---

## 11. DISEÑO DE ESQUEMA `identification.json`

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "PhotoIdentificationResult",
  "type": "object",
  "required": ["entity_id", "entity_type", "photos", "attributes", "conflicts", "human_review", "tool_versions"],
  "properties": {
    "entity_id": { "type": "string" },
    "entity_type": { "enum": ["ESPECIE", "DSM"] },
    "photos": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "photo_id": { "type": "string" },
          "relative_path": { "type": "string" },
          "sha256": { "type": "string" },
          "classification": { "type": "string" },
          "ocr_text": { "type": "string" }
        }
      }
    },
    "attributes": {
      "type": "object",
      "properties": {
        "object_type": { "$ref": "#/definitions/AttributeField" },
        "brand": { "$ref": "#/definitions/AttributeField" },
        "model": { "$ref": "#/definitions/AttributeField" },
        "serial": { "$ref": "#/definitions/AttributeField" },
        "capacity": { "$ref": "#/definitions/AttributeField" },
        "color": { "$ref": "#/definitions/AttributeField" }
      }
    },
    "conflicts": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "code": { "type": "string" },
          "description": { "type": "string" },
          "severity": { "enum": ["WARNING", "BLOCKING"] }
        }
      }
    },
    "human_review": {
      "type": "object",
      "properties": {
        "reviewed": { "type": "boolean" },
        "reviewed_by": { "type": ["string", "null"] },
        "reviewed_at": { "type": ["string", "null"] }
      }
    },
    "tool_versions": {
      "type": "object",
      "properties": {
        "ocr_engine": { "type": "string" },
        "llm_engine": { "type": "string" }
      }
    }
  },
  "definitions": {
    "AttributeField": {
      "type": "object",
      "properties": {
        "value": { "type": ["string", "null"] },
        "status": { "type": "string" },
        "provenance": { "type": "object" }
      }
    }
  }
}
```

---

## 12. IMPACTO EN SITEMA Y COMPONENTES (CASE.JSON, DATABASE, WEB, API, ORQUESTACIÓN)

- **CASE.JSON**: Al confirmar la identificación por fotografías, se actualizan los nodos `especie.marca`, `especie.modelo`, `dsm.serial`, etc., manteniendo la referencia al archivo `identification.json` en la carpeta de la entidad.
- **DATABASE (PostgreSQL)**:
  - Hace uso de las tablas ya preparadas: `forensic.photos`, `forensic.files`, `forensic.hashes`, `forensic.audit_events`.
  - Sin cambios de esquema en R06.
- **WEB FLOW**:
  1. Selección de Caso/NUE/Entidad.
  2. Upload/Staging de Fotografías.
  3. Ejecución de OCR Windows + Extracción Qwen2.5.
  4. Despliegue de Propuestas y Conflictos en Interfaz HTMX.
  5. Confirmación por Perito Operador.
- **CONTRATOS DE API**:
  - `POST /api/identification/photos/stage`
  - `POST /api/identification/entities/{id}/analyze`
  - `GET  /api/identification/entities/{id}`
  - `POST /api/identification/entities/{id}/review`
  - `POST /api/identification/entities/{id}/confirm`
- **ORQUESTADOR / STATE MACHINE**:
  - Transición: `IDENTIFICATION_PENDING` $\rightarrow$ `IDENTIFICATION_COMPLETED` $\rightarrow$ `ACQUISITION_READY`.

---

## 13. DEPENDENCIAS REQUERIDAS PARA R06.1, RIESGOS Y BLOQUEOS

- **Dependencias para R06.1**:
  - Implementación del módulo Python `src/agente_forense/identification/photo_agent.py`.
  - Integración del validador de inmutabilidad y orquestación con `qwen2.5:3b`.
  - Endpoints FastAPI y pantallas Jinja2/HTMX para Human Review de fotos.
- **Riesgos**:
  - Confusión del usuario esperando análisis visual de color/escena cuando solo hay OCR + LLM textual disponible.
  - Imprecisiones de Windows OCR en tipografías no estándar o seriales muy pequeños.
- **Bloqueos**: Ninguno. El desarrollo de R06.1 puede continuar con la pila tecnológica actual (Windows OCR + Ollama Qwen2.5 Text-Only).

---

## 14. ESTADO FINAL DE CAPACIDADES FOTOGRÁFICAS
```text
PHOTO_IDENTIFICATION_CAPABILITIES_VERIFIED
```
