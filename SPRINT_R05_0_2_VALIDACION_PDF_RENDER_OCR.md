# SPRINT_R05_0_2 — Validación real de renderizado PDF escaneado → bitmap → Windows OCR

## 1. Objetivo

Resolver la segunda incertidumbre crítica del pipeline de petitorios:

```text
¿Puede el entorno REAL de AGENTE FORENSE
renderizar páginas de un PDF escaneado a imagen
y entregarlas a Windows OCR
sin depender de software cloud ni herramientas no verificadas?
```

R05 verificó:

```text
Windows OCR disponible
es-ES disponible
pypdf seleccionado para PDFs con texto
```

R05.0.1 verificó:

```text
Windows.Media.Ocr
+ winsdk 1.0.0b10
+ Python 3.10.11
+ Windows 10 build 19045
→ RecognizeAsync funcional
```

Pero `pypdf` NO renderiza páginas PDF como imágenes ni realiza OCR.

Por lo tanto, antes de R05.1 debe validarse el camino:

```text
PDF ESCANEADO
→ PdfDocument
→ PdfPage
→ RenderToStreamAsync
→ bitmap/imagen
→ Windows OCR
→ texto
```

Estado esperado:

```text
PDF_RENDER_WINDOWS_OCR_VERIFIED
```

o:

```text
PDF_RENDER_WINDOWS_OCR_UNSUPPORTED
```

---

## 2. Documentación obligatoria

Leer completos:

```text
PROMPT_MAESTRO.md
REGLA_PERMANENTE_PRE_SPRINT.md
SPRINT_R05.md
PETITION_PIPELINE_CAPABILITIES.md
SPRINT_R05_0_1_VALIDACION_WINDOWS_OCR.md
WINDOWS_OCR_RUNTIME_VALIDATION.md
SPRINT_R05_0_2_VALIDACION_PDF_RENDER_OCR.md
```

También revisar reportes R04, R05 y R05.0.1.

---

## 3. Baseline

Esperado:

```text
Python: 3.10.11
Windows: Windows 10 Pro
Build: 19045
winsdk: 1.0.0b10
Pillow: 12.3.0
Windows OCR es-ES: VERIFIED
Tests: 108 passed
```

Ejecutar:

```text
.venv\Scripts\python.exe -m pytest
```

No continuar si existe regresión.

---

## 4. Fuente técnica primaria

Microsoft documenta:

```text
Windows.Data.Pdf.PdfDocument
Windows.Data.Pdf.PdfPage
PdfPage.RenderToStreamAsync
```

`RenderToStreamAsync` produce un stream representando la página PDF renderizada como imagen.

La API aplica a Windows build 19041 y posteriores, por lo que build 19045 está dentro del rango documentado.

Esto NO prueba todavía que funcione mediante `winsdk` en este Python.

La validación local sigue siendo obligatoria.

---

## 5. No instalar un renderer adicional todavía

NO instalar:

```text
PyMuPDF
pdf2image
Poppler
Ghostscript
ImageMagick
```

en este sprint.

Primero validar `Windows.Data.Pdf` mediante el `winsdk` ya instalado.

Si no funciona:

documentar el fallo y detenerse.

No introducir fallback sin investigación específica.

---

## 6. Fixture PDF sintético

Crear un PDF sintético de laboratorio de una o dos páginas que visualmente contenga:

```text
RUC 12345678
NUE 777777
OFICIO 123
SOLICITA DILIGENCIA FORENSE
```

La prueba debe simular un PDF escaneado:

- el contenido visible debe estar contenido como imagen;
- no debe incluir una capa de texto útil;
- pypdf `extract_text()` debería devolver vacío o texto no suficiente;
- ningún dato real.

Puede generarse usando Pillow y herramientas ya disponibles.

No usar `casos/`.

Usar directorio temporal.

---

## 7. Hash del fixture

Calcular y registrar:

```text
SHA-256 del PDF sintético
SHA-256 de imagen fuente si corresponde
```

No modificar el fixture después de calcular el hash.

---

## 8. Validación de pypdf

Si `pypdf` aún no está instalado:

NO instalarlo obligatoriamente en este micro-sprint salvo que sea necesario para comprobar ausencia de capa de texto.

Si se instala:

registrar versión exacta.

Validar:

```text
page.extract_text()
```

y confirmar que el fixture escaneado no depende de texto embebido.

---

## 9. Windows.Data.Pdf

Usar `winsdk` para intentar:

```text
StorageFile / stream
→ PdfDocument.load_from_file_async
  o load_from_stream_async
→ PdfDocument.page_count
→ get_page(0)
→ PdfPage.render_to_stream_async(...)
```

Registrar nombres/métodos exactos expuestos por el binding real.

No inventar equivalencias de API.

---

## 10. Salida renderizada

El resultado debe convertirse a un formato que Windows OCR pueda consumir.

Registrar:

```text
output format real
width
height
byte size
SHA-256
```

No asumir PNG si la API/binding produce otra representación.

Determinarlo por observación.

---

## 11. Render resolution

Registrar el tamaño nativo de la página:

```text
PdfPage.size
```

Si se usan `PdfPageRenderOptions`:

documentar:

```text
destination_width
destination_height
```

No sobreescalar arbitrariamente.

El objetivo es funcionalidad y legibilidad, no optimización todavía.

---

## 12. OCR end-to-end

El criterio crítico no es solo renderizar.

Debe ejecutarse:

```text
PDF escaneado
→ página renderizada
→ SoftwareBitmap / bitmap compatible
→ OcrEngine es-ES
→ RecognizeAsync
→ texto
```

Registrar el texto real observado.

---

## 13. Tokens esperados

Buscar, sin exigir formato exacto:

```text
RUC
12345678
NUE
777777
OFICIO
123
SOLICITA
DILIGENCIA
FORENSE
```

Aceptar uniones OCR como:

```text
NUE777777
```

si el contenido semántico sigue siendo observable.

---

## 14. Multi-page

Si el fixture tiene dos páginas:

verificar:

```text
page_count
orden 0..N-1
texto por página
provenance page_number
```

No concatenar sin conservar el origen por página.

---

## 15. Repetibilidad

Ejecutar el pipeline completo mínimo 3 veces.

Registrar:

```text
render latency
OCR latency
total latency
recognized text
errors
```

No exigir latencia idéntica.

---

## 16. Recursos

Registrar aproximadamente:

```text
tamaño PDF
tamaño render
duración
```

No realizar benchmark exhaustivo.

---

## 17. Manejo de errores

Probar al menos:

```text
archivo no PDF
PDF corrupto sintético
PDF vacío o sin páginas si es técnicamente generable
```

El sistema debe fallar de manera controlada.

No traceback sin manejar como resultado aceptable.

---

## 18. PDF protegido

No implementar soporte de PDF cifrado en este sprint.

Solo documentar cómo responde la API si se observa.

Debe quedar para política futura.

---

## 19. No modificar original

El PDF fixture no debe modificarse durante:

```text
load
render
OCR
```

Verificar SHA-256 antes y después.

Debe coincidir.

---

## 20. Resultado

Usar exactamente uno:

```text
PDF_RENDER_WINDOWS_OCR_VERIFIED
```

si:

- PdfDocument carga;
- página renderiza;
- salida puede alimentar Windows OCR;
- RecognizeAsync devuelve texto útil;
- flujo es repetible;
- PDF original conserva hash.

o:

```text
PDF_RENDER_WINDOWS_OCR_UNSUPPORTED
```

si cualquier eslabón material no funciona en el entorno actual.

---

## 21. Si falla

NO instalar automáticamente otro renderer.

Documentar:

```text
failure stage
exception
binding limitation
recommended next investigation
```

La siguiente investigación podrá evaluar:

```text
PyMuPDF
```

como renderer local.

No implementar workaround silencioso.

---

## 22. No realizar

Prohibido:

- petitorio real;
- PostgreSQL modifications;
- `casos/`;
- cloud;
- Ollama/Qwen;
- PhysicalDrive;
- EWF;
- AXIOM;
- OpenClaw;
- MSIX packaging;
- cambios firewall;
- adquisición;
- evidencia real.

---

## 23. Tests

Antes:

```text
108 passed
```

Después:

```text
108 passed
```

o más si existen nuevos tests legítimos.

---

## 24. Entregable

Crear:

```text
PDF_RENDER_OCR_RUNTIME_VALIDATION.md
```

Debe contener:

```text
ENVIRONMENT
WINDOWS BUILD
PYTHON
WINSDK
PDF FIXTURE
PDF SHA256
TEXT LAYER CHECK
PDFDOCUMENT LOAD
PAGE COUNT
RENDER API
RENDER OUTPUT
RENDER DIMENSIONS
RENDER SHA256
OCR ENGINE
OCR TEXT
PAGE PROVENANCE
LATENCY
REPEATABILITY
ORIGINAL HASH AFTER
ERROR TESTS
CONCLUSION
RECOMMENDATION
```

---

## 25. Reporte final obligatorio

```text
SPRINT R05.0.2:
COMPLETADO / BLOCKED

BASELINE:
...

TESTS BEFORE:
...

WINDOWS:
...

BUILD:
...

PYTHON:
...

WINSDK:
...

PYPDF:
INSTALLED / NOT_INSTALLED
VERSION:
...

PDF FIXTURE:
...

PDF SHA256 BEFORE:
...

PDF TEXT LAYER:
PRESENT / ABSENT / INSUFFICIENT

PDFDOCUMENT LOAD:
SUCCESS / FAIL

PAGE COUNT:
...

RENDERTOSTREAMASYNC:
SUCCESS / FAIL

RENDER OUTPUT TYPE:
...

RENDER SIZE:
...

RENDER SHA256:
...

WINDOWS OCR:
...

OCR LANGUAGE:
...

RUN 1:
...

RUN 2:
...

RUN 3:
...

RECOGNIZED TEXT:
...

EXPECTED TOKENS:
...

MATCHED TOKENS:
...

PAGE PROVENANCE:
...

PDF SHA256 AFTER:
...

ORIGINAL UNCHANGED:
SI / NO

ERROR TESTS:
...

FILES CREATED:
...

FILES MODIFIED:
...

POSTGRESQL MODIFIED:
NO

CASOS/ MODIFIED:
NO

REAL PETITION READ:
NO

CLOUD:
NO

OLLAMA:
NO

PHYSICALDRIVE:
NO

EWF:
NO

AXIOM:
NO

TESTS FINAL:
...

STATUS:
PDF_RENDER_WINDOWS_OCR_VERIFIED / PDF_RENDER_WINDOWS_OCR_UNSUPPORTED

RECOMMENDATION:
...
```

---

## 26. Instrucción final

TRAE:

1. lee documentación vigente;
2. ejecuta baseline;
3. crea PDF escaneado sintético;
4. calcula hash;
5. valida ausencia/insuficiencia de capa de texto;
6. carga PDF mediante Windows.Data.Pdf;
7. renderiza página mediante RenderToStreamAsync;
8. entrega el render a Windows OCR es-ES;
9. ejecuta RecognizeAsync real;
10. repite el flujo tres veces;
11. verifica hash original;
12. documenta errores controlados;
13. ejecuta tests finales;
14. entrega reporte;
15. detente;
16. NO inicies R05.1.

Comienza ahora.
