# Sprint 05.1 — Identificación asistida local con Windows OCR + qwen2.5:3b

## 1. Objetivo

Habilitar la primera versión funcional del Agente de Identificación utilizando exclusivamente capacidades locales ya verificadas:

```text
Windows OCR nativo
+
Ollama local
+
qwen2.5:3b
+
validación determinística
+
revisión humana
```

El objetivo NO es implementar visión semántica completa.

El objetivo es:

1. leer texto visible de las 3 fotografías;
2. conservar el OCR bruto como dato observado;
3. permitir que qwen2.5:3b proponga estructura sobre ese texto;
4. rechazar automáticamente cualquier dato que el LLM no pueda sustentar en fuentes autorizadas;
5. presentar la propuesta al operador;
6. permitir corrección humana;
7. renombrar las fotografías de forma segura cuando exista una clasificación suficientemente sustentada o confirmada por el operador;
8. persistir identificación y trazabilidad.

---

## 2. Regla permanente obligatoria

Antes de modificar código, TRAE debe leer completos:

```text
G:\AgenteForense\PROMPT_MAESTRO.md
G:\AgenteForense\REGLA_PERMANENTE_PRE_SPRINT.md
```

Aplicar estrictamente la regla permanente de investigación previa.

Antes de implementar:

1. ejecutar la suite completa;
2. registrar baseline real;
3. revisar Sprint 05 y Sprint 05A;
4. inspeccionar el paquete `identification`;
5. inspeccionar `VisionProvider`;
6. inspeccionar `UnavailableVisionProvider`;
7. inspeccionar `service.py`;
8. inspeccionar persistencia de `identification.json`;
9. inspeccionar actualización de `case.json`;
10. inspeccionar el mecanismo de auditoría;
11. comprobar nuevamente el Windows OCR nativo disponible;
12. comprobar Ollama local;
13. comprobar `qwen2.5:3b`;
14. comprobar que la API/CLI utilizada sea realmente compatible con la versión local;
15. no inventar capacidades visuales inexistentes.

Si cualquier supuesto técnico de este sprint no coincide con el entorno real:

```text
DETENER
DOCUMENTAR
RESOLVER
```

antes de continuar.

---

## 3. Baseline

Baseline esperado:

```text
206 passed, 4 subtests passed
```

Registrar el resultado real.

No aceptar regresiones.

---

## 4. Capacidades locales ya demostradas

### Windows OCR

Entorno verificado:

```text
Windows 10 build 19045
Windows.Media.Ocr.OcrEngine
Language.OCR es-ES disponible
Language.OCR es-MX disponible
MaxImageDimension = 10000
```

Prueba real previa:

```text
Imagen: 900 x 900
Latencia: ~212 ms
Output:
X99
GEFORCE GTX
```

Windows OCR se considera una capacidad REAL disponible para extracción de texto visible.

### Ollama

Versión verificada:

```text
Ollama 0.34.4
```

Modelo local existente:

```text
qwen2.5:3b
```

Manifest:

```text
G:\OllamaModels\manifests\registry.ollama.ai\library\qwen2.5\3b
```

Capacidades reportadas por `ollama show`:

```text
completion
tools
```

NO incluye visión.

Modelo:

```text
architecture: qwen2
parameters: 3.1B
context length: 32768
quantization: Q4_K_M
```

Prueba real:

```text
Tiempo aproximado primera inferencia: 6.3 s
```

El modelo puede estructurar texto OCR pero puede introducir conocimiento no presente en la fuente.

Ejemplo observado:

OCR:

```text
X99
GEFORCE GTX
```

Qwen añadió en explicación una referencia a:

```text
NVIDIA
```

aunque `NVIDIA` no estaba en el OCR.

Conclusión obligatoria:

```text
QWEN NUNCA ES AUTORIDAD DE HECHOS FORENSES
```

---

## 5. Arquitectura obligatoria

Mantener separación:

```text
FOTOGRAFÍA
    ↓
WINDOWS OCR
    ↓
OBSERVED_TEXT
    ↓
QWEN2.5:3B
    ↓
PROPOSED_FIELDS
    ↓
VALIDADOR DETERMINÍSTICO
    ↓
REVISIÓN HUMANA
    ↓
CONFIRMED_FIELDS
```

Nunca:

```text
LLM OUTPUT → CONFIRMED
```

directamente.

---

## 6. Providers

Mantener la interfaz existente `VisionProvider`.

Implementar al menos:

```text
UnavailableVisionProvider
WindowsOcrProvider
```

No declarar `WindowsOcrProvider` como provider de visión semántica.

Debe publicar capacidades explícitas, por ejemplo:

```text
ocr = true
image_classification = false
visual_attribute_inference = false
local_only = true
```

Qwen debe integrarse como capa textual separada, por ejemplo:

```text
TextReasoningProvider
OllamaTextReasoningProvider
```

o equivalente coherente con la arquitectura real.

No mezclar OCR y LLM en un único componente opaco.

---

## 7. Descubrimiento seguro de Ollama

El agente NO debe modificar automáticamente:

```text
OLLAMA_MODELS
```

No debe mover modelos.

No debe copiar blobs.

No debe ejecutar `ollama pull`.

Debe comprobar:

```text
Ollama API local disponible
qwen2.5:3b visible
modelo ejecutable
```

Si el modelo no está disponible:

```text
LLM_PROVIDER_UNAVAILABLE
```

y continuar, cuando sea posible, solo con OCR + revisión humana.

---

## 8. Windows OCR Provider

Implementar un provider local que:

1. reciba ruta a imagen;
2. compruebe formato soportado;
3. lea la imagen sin modificarla;
4. extraiga texto mediante Windows OCR;
5. devuelva:
   - texto bruto;
   - líneas;
   - idioma usado;
   - timestamp;
   - provider;
   - versión/entorno disponible;
   - errores;
6. no reescriba la imagen;
7. no altere EXIF;
8. no modifique timestamps intencionalmente;
9. no use red.

---

## 9. Texto observado

Guardar por fotografía:

```text
raw_ocr_text
ocr_lines
ocr_language
ocr_status
source_photo
source_photo_sha256
```

Ejemplo:

```json
{
  "raw_ocr_text": "KINGSTON\n64GB\nS/N ABC123",
  "ocr_lines": [
    "KINGSTON",
    "64GB",
    "S/N ABC123"
  ],
  "status": "OBSERVED"
}
```

El OCR es una lectura automatizada observada.

No equivale a confirmación humana.

---

## 10. Estados de datos

Usar como mínimo:

```text
OBSERVED
PROPOSED
CONFIRMED
UNCERTAIN
CONFLICT
NOT_VISIBLE
NOT_AVAILABLE
REJECTED_UNSUPPORTED
```

---

## 11. Qwen2.5:3b — alcance permitido

Qwen puede:

- estructurar texto OCR;
- identificar candidatos a marca, modelo, serial, capacidad e identificadores;
- normalizar presentación;
- proponer tipo textual de campo;
- sugerir clasificación fotográfica si existe evidencia textual suficiente;
- generar un borrador de descripción claramente marcado como DRAFT.

Qwen NO puede:

- inventar marca;
- inferir fabricante por conocimiento general;
- completar seriales;
- completar caracteres ausentes;
- convertir conocimiento del modelo en observación forense;
- confirmar un campo por sí solo;
- declarar que ve elementos que no fueron obtenidos del OCR o de otra fuente autorizada.

---

## 12. Prompt de Qwen

Diseñar un prompt estricto.

Debe exigir:

```text
SOLO JSON
SIN EXPLICACIÓN
SIN TEXTO FUERA DEL JSON
```

y reglas como:

```text
No agregues marcas, modelos, seriales, capacidades o identificadores que no aparezcan literalmente en las fuentes suministradas.

Si no existe evidencia suficiente:
null / UNCERTAIN / NOT_VISIBLE

No uses conocimiento general para completar datos.
```

El sistema NO debe confiar en que el prompt sea suficiente.

Toda salida debe pasar después por validación determinística.

---

## 13. JSON estricto

La respuesta esperada debe seguir schema cerrado.

Ejemplo conceptual:

```json
{
  "brand_candidate": {
    "value": "KINGSTON",
    "support": ["KINGSTON"]
  },
  "model_candidate": {
    "value": null,
    "support": []
  },
  "serial_candidate": {
    "value": "ABC123",
    "support": ["S/N ABC123"]
  },
  "capacity_candidate": {
    "value": "64GB",
    "support": ["64GB"]
  }
}
```

Rechazar salida no parseable.

No extraer valores libremente desde explicaciones en lenguaje natural.

---

## 14. Validación determinística anti-invención

Por cada valor propuesto por Qwen, el código debe verificar sustento en fuentes autorizadas.

Fuentes autorizadas iniciales:

```text
OCR de las 3 fotografías
acquisition metadata existente
corrección humana
```

Si Qwen devuelve un valor sin soporte:

```text
LLM_UNSUPPORTED_VALUE
status = REJECTED_UNSUPPORTED
```

Ejemplo:

OCR:

```text
GEFORCE GTX
```

Qwen:

```text
brand = NVIDIA
```

Resultado:

```text
REJECTED_UNSUPPORTED
```

No guardar `NVIDIA` como hecho.

---

## 15. Normalización permitida

La validación puede aceptar transformaciones determinísticas seguras:

- trim;
- diferencias de mayúsculas/minúsculas;
- espacios repetidos;
- normalización simple de separadores;
- `64 GB` ↔ `64GB` cuando la regla sea explícita y testeada.

No permitir:

- sustitución semántica;
- completar abreviaturas por conocimiento;
- inferir fabricante;
- expandir nombre comercial;
- completar serial.

---

## 16. Comparación con metadata de adquisición

Si existe metadata DSM, comparar:

```text
OCR/propuesta.model vs acquisition.model
OCR/propuesta.serial vs acquisition.serial
OCR/propuesta.capacity vs acquisition.size_bytes
```

No fabricar `model` a partir de `friendly_name`.

Estados:

```text
MATCH
COMPATIBLE
CONFLICT
NOT_COMPARABLE
```

Capacidad nominal vs bytes solo con regla matemática explícita y testeada.

---

## 17. Clasificación de fotografías

Windows OCR NO puede clasificar visualmente una foto.

Qwen2.5:3b tampoco ve la imagen.

Por tanto, solo permitir clasificación automática si existe soporte textual inequívoco.

Ejemplos:

Texto contiene claramente:

```text
S/N
Serial Number
Número de serie
```

puede proponer:

```text
SERIAL
```

Texto contiene etiqueta de producto con varios campos:

puede proponer:

```text
ETIQUETA
```

Si no existe fundamento textual:

```text
NO_CLASIFICADA
```

El operador selecciona:

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

No inventar clasificación visual.

---

## 18. Renombrado

Mantener el mecanismo transaccional de Sprint 05.

Solo después de:

1. análisis;
2. propuesta;
3. revisión humana;
4. clasificación final de cada una de las 3 fotos;
5. ausencia de colisiones;
6. confirmación exacta:

```text
RENOMBRAR
```

renombrar.

Preservar SHA-256.

---

## 19. Identificación humana final

Mostrar:

```text
Entidad:
...

Foto 1:
nombre original
OCR
clasificación propuesta/final

Foto 2:
...

Foto 3:
...

Marca:
...

Modelo:
...

Serial:
...

Capacidad:
...

Conflictos:
...

Valores rechazados por falta de soporte:
...
```

Requerir:

```text
CONFIRMAR_IDENTIFICACION
```

antes de marcar:

```text
IDENTIFIED
```

---

## 20. Caso SELF_STORAGE

Para el pendrive de prueba:

```text
ESPECIE1 = DSM1
```

Usar solo las 3 fotos físicas de ESPECIE.

No duplicar archivos.

Los datos identificatorios pueden alimentar lógicamente ESPECIE y DSM según corresponda, conservando:

```text
photos_reference = SPECIES_PHOTOS
```

---

## 21. Prueba real con las 3 JPG existentes en G:\

El operador informa que existen 3 fotografías JPG del pendrive en:

```text
G:\
```

La prueba real debe ser NO DESTRUCTIVA.

### Descubrimiento

Enumerar únicamente:

```powershell
Get-ChildItem G:\ -File -Filter *.jpg
Get-ChildItem G:\ -File -Filter *.jpeg
```

NO hacer búsqueda recursiva inicialmente.

### Regla

Si se encuentran exactamente 3 JPG/JPEG candidatas, mostrar:

```text
nombre
ruta
tamaño
last write
SHA-256
```

y pedir confirmación humana:

```text
USAR_ESTAS_3_FOTOS
```

Si hay menos de 3:

```text
TEST_PHOTOS_INCOMPLETE
```

Si hay más de 3:

mostrar lista y requerir selección humana exacta de 3.

No elegir automáticamente.

---

## 22. Preservación de originales en G:\

Las fotografías originales en:

```text
G:\
```

NO se renombran.
NO se mueven.
NO se borran.
NO se editan.

Antes de usarlas:

calcular SHA-256 de cada original.

Crear un caso de laboratorio Schema v2 o usar uno temporal seguro.

Copiar las 3 imágenes a:

```text
IDENTIFICACION\
NUE_<NUE>\
NUE_<NUE>_ESPECIE1\
FOTOS_PENDIENTES\
```

Después de copiar:

calcular SHA-256 de cada copia.

Debe cumplirse:

```text
SHA256_ORIGINAL == SHA256_COPIA
```

Si no:

```text
PHOTO_COPY_HASH_MISMATCH
```

y abortar la prueba.

El agente solo podrá renombrar las COPIAS de laboratorio después de confirmación.

Nunca los originales en G:\.

---

## 23. Caso de laboratorio

Usar un RUC y NUE inequívocamente identificados como laboratorio.

No reutilizar:

```text
TEST-ACQ-001
```

No alterar casos anteriores.

El caso debe ser Schema v2.

Configuración:

```text
1 NUE
1 ESPECIE
SELF_STORAGE
DSM1 automático
```

---

## 24. Ejecución de prueba real

Después de copiar y verificar hashes:

1. validar exactamente 3 fotos;
2. ejecutar Windows OCR sobre cada copia;
3. persistir OCR bruto;
4. consolidar texto;
5. enviar únicamente el texto y metadata autorizada a qwen2.5:3b;
6. exigir JSON;
7. validar cada propuesta;
8. rechazar valores no sustentados;
9. mostrar propuesta al operador;
10. permitir corrección;
11. clasificar fotos automáticamente solo donde exista soporte textual;
12. pedir clasificación humana de las restantes;
13. mostrar plan de renombrado;
14. requerir `RENOMBRAR`;
15. verificar hashes post-rename;
16. mostrar identificación final;
17. requerir `CONFIRMAR_IDENTIFICACION`;
18. persistir `identification.json`;
19. actualizar `case.json`;
20. auditar todo.

---

## 25. Datos que intentar obtener del pendrive

Cuando estén visibles:

```text
object_type
brand
model
serial
capacity
visible_labels
```

No exigir que todos existan.

Si no están impresos o no son legibles:

```text
NOT_VISIBLE
```

No fallar la identificación solo por ausencia.

---

## 26. Rendimiento

Registrar por foto:

```text
OCR latency
```

Registrar por llamada Qwen:

```text
LLM latency
```

Registrar:

```text
total identification time
```

No establecer límites rígidos antes de medir.

---

## 27. Privacidad

Todo procesamiento debe ser local.

Permitir únicamente:

```text
Windows OCR local
Ollama en 127.0.0.1
```

No enviar fotos o OCR a Internet.

No usar APIs cloud.

---

## 28. Fallos

Windows OCR no disponible:

```text
OCR_PROVIDER_UNAVAILABLE
```

Ollama no disponible:

```text
LLM_PROVIDER_UNAVAILABLE
```

Qwen no visible:

```text
MODEL_UNAVAILABLE
```

JSON inválido:

```text
LLM_INVALID_OUTPUT
```

Valor no sustentado:

```text
LLM_UNSUPPORTED_VALUE
```

El flujo debe poder continuar con revisión humana cuando sea técnicamente seguro.

---

## 29. Auditoría

Registrar:

```text
test_photo_discovered
test_photo_selected
test_photo_hashed
test_photo_copied
copy_hash_verified
ocr_started
ocr_completed
llm_started
llm_completed
llm_value_rejected
photo_classification_proposed
photo_classification_confirmed
rename_plan_created
rename_confirmed
photo_renamed
hash_verified_after_rename
human_correction
identification_confirmed
```

---

## 30. Tests obligatorios

Mantener los 206 tests existentes.

Agregar tests para:

1. WindowsOcrProvider disponible;
2. WindowsOcrProvider no disponible;
3. OCR JPG;
4. OCR PNG;
5. OCR sin texto;
6. OCR no modifica bytes;
7. OCR metadata persistida;
8. qwen disponible;
9. qwen no disponible;
10. qwen model missing;
11. JSON válido;
12. JSON inválido;
13. valor soportado por OCR aceptado;
14. valor no soportado rechazado;
15. `NVIDIA` rechazado cuando OCR solo tiene `GEFORCE GTX`;
16. case-insensitive match seguro;
17. whitespace normalization;
18. capacidad normalizada;
19. serial incompleto no completado;
20. no inferir marca;
21. no inferir modelo;
22. classification SERIAL desde patrón explícito;
23. classification ETIQUETA solo con regla definida;
24. foto sin soporte textual -> NO_CLASIFICADA;
25. clasificación humana;
26. SELF_STORAGE no duplica fotos;
27. originales G:\ nunca renombrados;
28. originales G:\ nunca modificados;
29. copia conserva SHA-256;
30. hash mismatch aborta;
31. >3 fotos requiere selección;
32. <3 fotos bloquea prueba real;
33. exactamente 3 permite prueba;
34. rename solo sobre copias;
35. rename conserva SHA-256;
36. identification.json;
37. case.json atomic update;
38. human confirmation;
39. audit trail;
40. no cloud;
41. no ewfacquire;
42. no ewfverify;
43. no PhysicalDrive;
44. Schema v1 intacto;
45. TEST-ACQ-001 intacto;
46. Sprint 05A sin regresión.

---

## 31. Operaciones prohibidas

NO:

- ejecutar ewfacquire;
- ejecutar ewfverify;
- acceder a PhysicalDrive;
- modificar evidencia física;
- renombrar originales en G:\;
- mover originales;
- borrar originales;
- descargar modelos;
- ejecutar ollama pull;
- cambiar permanentemente OLLAMA_MODELS;
- usar cloud;
- integrar AXIOM;
- generar Word;
- iniciar siguiente sprint.

---

## 32. Criterio de cierre

Sprint 05.1 queda COMPLETO si:

- baseline íntegro;
- Windows OCR provider funcional;
- qwen2.5:3b integrado como razonador textual;
- Qwen no puede confirmar hechos directamente;
- validación anti-invención funciona;
- valores no sustentados se rechazan;
- 3 fotos reales pueden procesarse desde copias verificadas;
- originales permanecen intactos;
- OCR bruto queda persistido;
- clasificación automática se limita a evidencia textual;
- clasificación humana cubre el resto;
- renombrado seguro funciona;
- identification.json se genera;
- case.json se actualiza;
- auditoría completa;
- toda la suite pasa;
- ninguna operación forense real de adquisición se ejecutó.

---

## 33. Reporte final de TRAE

Entregar:

```text
SPRINT 05.1:
COMPLETADO / INCOMPLETO

BASELINE:
...

INVESTIGACIÓN PREVIA:
...

WINDOWS OCR:
...

OLLAMA:
...

QWEN2.5:3B:
...

CAPACIDADES REALES:
...

ARCHIVOS MODIFICADOS:
...

ARCHIVOS CREADOS:
...

TEST PHOTOS EN G:\:
...

FOTOS ENCONTRADAS:
...

FOTOS SELECCIONADAS:
...

HASHES ORIGINALES:
...

HASHES COPIAS:
...

HASH MATCH:
...

CASO LAB:
...

OCR FOTO 1:
...

OCR FOTO 2:
...

OCR FOTO 3:
...

OCR LATENCIAS:
...

QWEN INPUT:
...

QWEN OUTPUT:
...

QWEN LATENCIA:
...

VALORES ACEPTADOS:
...

VALORES RECHAZADOS:
...

CONFLICTOS:
...

CLASIFICACIÓN FOTOS:
...

INTERVENCIÓN HUMANA:
...

RENOMBRADO:
...

HASH POST-RENAME:
...

IDENTIFICATION.JSON:
...

CASE.JSON:
...

AUDITORÍA:
...

TESTS NUEVOS:
...

TESTS FINALES:
...

ORIGINALES G:\ MODIFICADOS:
NO

EWFACQUIRE:
NO

EWFVERIFY:
NO

PHYSICALDRIVE:
NO

CLOUD:
NO

RIESGOS / LIMITACIONES:
...

ESTADO:
LISTO / NO LISTO PARA SIGUIENTE SPRINT
```

No iniciar siguiente sprint.

---

## 34. Instrucción final

TRAE:

1. lee PROMPT_MAESTRO;
2. lee REGLA_PERMANENTE_PRE_SPRINT;
3. revisa Sprint 05 y 05A;
4. ejecuta baseline;
5. inspecciona providers actuales;
6. confirma Windows OCR real;
7. confirma Ollama real;
8. confirma qwen2.5:3b;
9. no cambies configuración permanente de Ollama;
10. implementa WindowsOcrProvider;
11. implementa capa textual Qwen desacoplada;
12. implementa JSON estricto;
13. implementa validación anti-invención;
14. implementa fallback humano;
15. preserva renombrado transaccional;
16. descubre las JPG de G:\ no recursivamente;
17. si no son exactamente 3, pide selección;
18. hashea originales;
19. copia a caso lab;
20. verifica hash;
21. procesa únicamente las copias;
22. nunca renombres originales G:\;
23. ejecuta prueba real con las 3 fotos;
24. registra outputs y latencias;
25. agrega tests;
26. deja toda la suite verde;
27. entrega reporte final completo;
28. no ejecutes adquisición;
29. no accedas a PhysicalDrive;
30. no uses cloud;
31. NO inicies el siguiente sprint.

COMIENZA AHORA.
