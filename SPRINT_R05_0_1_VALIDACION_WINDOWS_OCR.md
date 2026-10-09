# SPRINT_R05_0_1 — Validación real de Windows OCR desde Python

## 1. Objetivo

Resolver una única incertidumbre crítica descubierta al auditar R05:

```text
¿Puede el proceso REAL de AGENTE FORENSE,
ejecutándose como Python 3.10.11 de escritorio no empaquetado,
invocar Windows.Media.Ocr de forma funcional, reproducible y soportable?
```

R05 verificó que:

```text
Windows.Media.Ocr existe
es-ES y es-MX están instalados
winsdk es candidato
```

Pero eso NO prueba todavía que el runtime Python actual pueda realizar OCR end-to-end.

Microsoft documenta actualmente que `Windows.Media.Ocr` para desktop apps está soportado con package identity/MSIX. `winsdk` es un binding comunitario/beta.

Por ello, NO iniciar R05.1 hasta ejecutar esta validación real.

Estado esperado:

```text
WINDOWS_OCR_PYTHON_VERIFIED
```

o:

```text
WINDOWS_OCR_PYTHON_UNSUPPORTED
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
```

Revisar además los reportes R04 y R05.

---

## 3. Baseline

Esperado:

```text
Python: 3.10.11
Tests: 108 passed
Windows OCR languages:
es-ES
es-MX
```

Ejecutar:

```text
.venv\Scripts\python.exe -m pytest
```

No aceptar regresiones.

---

## 4. Verificación de entorno

Registrar:

```text
Windows edition
Windows build
Python architecture
Python executable
venv
package identity presente: SI/NO
MSIX: SI/NO
```

No asumir package identity.

---

## 5. Documentación primaria

Registrar referencia oficial actual de Microsoft para:

```text
Windows.Media.Ocr
OcrEngine
AvailableRecognizerLanguages
RecognizeAsync
desktop package identity
```

Documentar explícitamente la diferencia entre:

```text
API disponible
vs
API invocable desde nuestro proceso Python actual
```

---

## 6. winsdk

Verificar PyPI/metadata real.

Versión candidata observada:

```text
winsdk 1.0.0b10
```

Confirmar antes de instalar:

- wheel CPython 3.10 x64 disponible;
- estado pre-release/beta;
- fecha;
- licencia;
- origen.

No usar una versión distinta sin documentarla.

---

## 7. Instalación controlada

Se permite instalar dentro de `.venv` únicamente:

```text
winsdk
Pillow
```

si son necesarios para la prueba.

Registrar versiones reales instaladas.

No modificar Python global.

No instalar OCR cloud.

No instalar Tesseract todavía.

---

## 8. Fixture sintético

Crear en directorio temporal una imagen PNG sintética con texto claramente legible, por ejemplo:

```text
RUC 12345678
NUE 777777
OFICIO 123
SOLICITA DILIGENCIA FORENSE
```

El fixture:

- no contiene datos reales;
- no va a `casos/`;
- puede generarse con Pillow;
- debe tener hash SHA-256 registrado.

---

## 9. Prueba Windows OCR real

Intentar desde:

```text
.venv\Scripts\python.exe
```

un flujo real equivalente a:

```text
PNG
→ decode a SoftwareBitmap
→ OcrEngine es-ES
→ RecognizeAsync
→ texto reconocido
```

No basta con:

```text
import winsdk
listar idiomas
crear OcrEngine
```

La aceptación requiere `RecognizeAsync` real sobre la imagen sintética.

---

## 10. Resultado mínimo exigido

Registrar:

```text
engine creation
recognizer language
input dimensions
MaxImageDimension
RecognizeAsync success/failure
returned lines
returned words
returned text
exception type/message si falla
latency
```

No ocultar excepciones.

---

## 11. Package Identity

Comprobar específicamente si el éxito depende de:

```text
MSIX/package identity
```

Si falla por ausencia de identidad, documentarlo como:

```text
WINDOWS_OCR_PACKAGE_IDENTITY_REQUIRED
```

No intentar modificar el producto para empaquetarlo en este sprint.

---

## 12. Repetibilidad

Si funciona, repetir mínimo 3 veces con el mismo fixture.

Debe producir ejecución estable.

No exigir texto byte-a-byte idéntico si el API no garantiza eso, pero sí extracción funcional del contenido esperado.

---

## 13. Español

Probar explícitamente:

```text
es-ES
```

Si está disponible.

Registrar resultado de:

```text
IsLanguageSupported
TryCreateFromLanguage
RecognizerLanguage
```

---

## 14. Calidad mínima

No evaluar todavía precisión forense profunda.

Solo confirmar que reconoce de forma útil varios tokens esperados del fixture:

```text
RUC
NUE
777777
OFICIO
```

Si algunos caracteres difieren, registrar.

---

## 15. Fallback si Windows OCR falla

Si el runtime actual no puede usar `Windows.Media.Ocr`:

NO implementar hacks.

No empaquetar MSIX todavía.

No declarar Windows OCR como motor primario.

Resultado:

```text
WINDOWS_OCR_PYTHON_UNSUPPORTED
```

y recomendar para investigación siguiente:

```text
Tesseract 5.x + spa
```

u otra alternativa local verificable.

---

## 16. No usar Ollama

No ejecutar Qwen/Ollama en esta validación.

Esta prueba es exclusivamente OCR.

---

## 17. No realizar

Prohibido:

- PostgreSQL modifications;
- casos/;
- petitorios reales;
- evidencia real;
- PhysicalDrive;
- EWF;
- AXIOM;
- OpenClaw;
- cloud;
- MSIX packaging productivo;
- cambios de firewall.

---

## 18. Tests

Después de la prueba:

```text
.venv\Scripts\python.exe -m pytest
```

Esperado:

```text
108 passed
```

o más si se agregan tests legítimos.

---

## 19. Entregable

Crear:

```text
WINDOWS_OCR_RUNTIME_VALIDATION.md
```

Debe contener:

```text
ENVIRONMENT
WINDOWS BUILD
PYTHON
PACKAGE IDENTITY
WINSDK VERSION
PILLOW VERSION
OCR LANGUAGES
FIXTURE
SHA256
OCR CALL PATH
RESULT
TEXT OBSERVED
LATENCY
REPEATABILITY
ERRORS
MICROSOFT SUPPORT NOTE
CONCLUSION
RECOMMENDATION
```

---

## 20. Criterio de aceptación

Usar exactamente uno:

```text
WINDOWS_OCR_PYTHON_VERIFIED
```

si `RecognizeAsync` funciona realmente desde el venv actual y es repetible.

o:

```text
WINDOWS_OCR_PYTHON_UNSUPPORTED
```

si la API está presente pero el proceso Python actual no puede usarla de forma funcional/soportable.

No usar un estado ambiguo.

---

## 21. Reporte final obligatorio

```text
SPRINT R05.0.1:
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

PACKAGE IDENTITY:
SI / NO

WINSDK:
...

PILLOW:
...

OCR LANGUAGES:
...

ES-ES SUPPORTED:
SI / NO

FIXTURE:
...

FIXTURE SHA256:
...

OCR ENGINE CREATED:
SI / NO

RECOGNIZEASYNC EXECUTED:
SI / NO

RECOGNIZED TEXT:
...

EXPECTED TOKENS:
...

MATCHED TOKENS:
...

RUN 1:
...

RUN 2:
...

RUN 3:
...

ERRORS:
...

MSIX REQUIRED IN PRACTICE:
SI / NO / NO DETERMINADO

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
WINDOWS_OCR_PYTHON_VERIFIED / WINDOWS_OCR_PYTHON_UNSUPPORTED

RECOMMENDATION:
...
```

---

## 22. Instrucción final

TRAE:

1. lee Prompt Maestro y regla permanente;
2. ejecuta baseline;
3. verifica package identity;
4. verifica metadata real de winsdk;
5. instala winsdk/Pillow solo en `.venv` si corresponde;
6. crea fixture sintético;
7. ejecuta OCR real end-to-end;
8. repite tres veces;
9. documenta éxito o fallo sin reinterpretar;
10. ejecuta suite final;
11. entrega reporte;
12. detente;
13. NO inicies R05.1.

Comienza ahora.
