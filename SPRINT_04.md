# SPRINT_04_OPTIMIZADO.md

# Sprint 04 — Verificación independiente EWF, consolidación de hashes y cierre formal de ADQUISICION

## 1. Objetivo

Cerrar formalmente la fase `ADQUISICION` mediante una verificación independiente del E01 producido por Sprint 03 y validado operativamente en Sprint 03.5.

Este sprint parte de una adquisición real de laboratorio ya ejecutada y aceptada:

```text
Caso: TEST-ACQ-001
Origen: \\.\PhysicalDrive6
Modelo: Generic Flash Disk
Serial reportado por Windows: D
Tamaño físico: 16.106.127.360 bytes
E01: TEST-ACQ-001.E01
Tamaño E01: 6.531.377.213 bytes
Segmentos: 1
Estado actual: ACQUISITION_COMPLETED
```

Hashes del contenido adquirido registrados por `ewfacquire`:

```text
MD5:
bf63eaceec3a4e8cbbc1f9b698f3a70b

SHA-256:
28c376def067274843bab2bb5eac209514c1f8885d91d2b9ecf77b213c3645c0
```

Existe además una validación cruzada independiente con FTK Imager 8.3.0.27 sobre el mismo medio físico:

```text
Fuente FTK:
31.457.280 sectores
512 bytes por sector
= 16.106.127.360 bytes

MD5 FTK:
bf63eaceec3a4e8cbbc1f9b698f3a70b

Resultado:
MATCH con adquisición ewfacquire
```

Esta comparación FTK es evidencia externa de control, pero **NO sustituye la verificación independiente de Sprint 04**.

---

# 2. Resultado esperado

El sprint debe demostrar, usando la herramienta EWF de verificación instalada localmente, que:

1. el E01 puede leerse íntegramente;
2. la verificación EWF finaliza correctamente;
3. el digest calculado sobre los datos del medio coincide con el digest adquirido;
4. cualquier hash almacenado dentro del EWF es coherente con el calculado;
5. los hashes estructurados del caso siguen siendo coherentes;
6. no existe corrupción detectada;
7. el E01 no es modificado por el agente;
8. `case.json` avanza a estado verificado únicamente si todas las comprobaciones críticas pasan.

Si todo es correcto:

```text
acquisition.status = VERIFIED
case.status = ANALYSIS_PENDING
```

---

# 3. Regla previa obligatoria

TRAE debe:

1. leer `G:\AgenteForense\PROMPT_MAESTRO.md`;
2. leer `SPRINT_04_OPTIMIZADO.md`;
3. ejecutar toda la suite;
4. confirmar como baseline mínimo:

```text
77 passed
```

5. inspeccionar:

```text
G:\AgenteForense\ew\ewftools-x64
```

6. identificar la herramienta real de verificación EWF;
7. consultar su ayuda local y versión;
8. no asumir flags no confirmados.

La ayuda local instalada es la fuente de verdad.

---

# 4. No volver a adquirir

Sprint 04 **NO debe volver a acceder al PhysicalDrive para adquirirlo**.

La fuente de verificación será exclusivamente:

```text
G:\AgenteForense\casos\TEST-ACQ-001\ADQUISICION\TEST-ACQ-001.E01
```

No ejecutar nuevamente:

```text
ewfacquire
```

No repetir la adquisición.

No leer `\\.\PhysicalDrive6` para calcular hashes durante este sprint.

---

# 5. Herramienta de verificación

Buscar dentro de:

```text
G:\AgenteForense\ew\ewftools-x64
```

Es esperable encontrar una herramienta equivalente a:

```text
ewfverify.exe
```

pero debe confirmarse realmente.

Ejecutar únicamente operaciones no destructivas para inspección:

```text
<verifier>.exe -h
<verifier>.exe -V
```

o sus equivalentes reales si la ayuda local utiliza otra sintaxis.

Registrar:

- nombre;
- ruta;
- versión;
- formatos aceptados;
- soporte de digest;
- soporte de log;
- comportamiento con segmentos;
- sintaxis de source;
- códigos de salida observables.

---

# 6. Capabilities reales

Crear o completar un modelo:

```text
EwfVerifyCapabilities
```

Como mínimo, considerar:

```text
executable
version
supported_digests
supports_log
supports_verbose
supports_segment_set
supports_stored_hash_validation
success_markers
failure_markers
```

No modelar una capability no comprobada.

---

# 7. Distinción obligatoria de hashes

Este sprint debe diferenciar estrictamente dos conceptos.

## 7.1 MEDIA / ACQUIRED-DATA HASH

Hash calculado sobre los datos forenses reconstruidos del medio adquirido.

Ejemplo:

```text
MD5 del contenido adquirido:
bf63eaceec3a4e8cbbc1f9b698f3a70b
```

Este es el hash comparable entre:

- `ewfacquire`;
- `ewfverify`;
- FTK Imager;
- otras herramientas que calculen digest sobre el mismo stream de datos.

## 7.2 CONTAINER FILE HASH

Hash calculado sobre los bytes físicos del archivo:

```text
TEST-ACQ-001.E01
```

Este hash NO debe confundirse con el hash del medio adquirido.

Dos E01 creados por herramientas distintas pueden contener los mismos datos forenses y tener:

- tamaños distintos;
- metadata distinta;
- bytes de contenedor distintos;
- hash de archivo E01 distinto.

Por lo tanto:

**NO comparar el SHA-256 del archivo `.E01` con el SHA-256 del contenido adquirido.**

Si se calcula un hash del contenedor, usar un nombre explícito:

```text
container_file_sha256
```

Nunca:

```text
sha256
```

sin indicar su dominio.

---

# 8. Evidencia previa conocida del caso

Para `TEST-ACQ-001`, la metadata ya capturada contiene:

```text
MEDIA_MD5 =
bf63eaceec3a4e8cbbc1f9b698f3a70b

MEDIA_SHA256 =
28c376def067274843bab2bb5eac209514c1f8885d91d2b9ecf77b213c3645c0
```

Estas son las referencias de adquisición.

No hardcodear estos valores globalmente en el software.

Solo pertenecen a este caso de laboratorio.

Los tests unitarios deben usar valores mock independientes.

---

# 9. Validación cruzada FTK

Registrar, si corresponde, como evidencia externa de aceptación:

```text
tool: FTK Imager
version: 8.3.0.27
source_size_bytes: 16106127360
sector_count: 31457280
bytes_per_sector: 512
media_md5: bf63eaceec3a4e8cbbc1f9b698f3a70b
result: MATCH
```

FTK produjo un E01 distinto de:

```text
6.528.503.131 bytes
```

mientras el agente produjo:

```text
6.531.377.213 bytes
```

Esta diferencia de contenedor **no es un error** si el hash del contenido adquirido coincide.

La validación FTK debe quedar separada conceptualmente de `ewfverify`.

No usar FTK como requisito técnico para que Sprint 04 funcione.

---

# 10. Precondiciones del caso real

Antes de ejecutar verificación:

confirmar:

```text
case.json existe
case.status == ACQUISITION_COMPLETED
acquisition.status == ACQUISITION_COMPLETED
```

Confirmar:

```text
TEST-ACQ-001.E01 existe
size == 6.531.377.213 bytes
size > 0
```

Confirmar:

```text
segment_count == 1
```

Confirmar ausencia de:

```text
TEST-ACQ-001.E02
TEST-ACQ-001.E03
...
```

Si la metadata actual difiere de los archivos reales:

ABORTAR.

No corregir silenciosamente.

---

# 11. Protección del E01

La verificación debe ser de solo lectura.

El agente no debe:

- truncar;
- renombrar;
- reescribir;
- reparar;
- modificar metadata interna;
- convertir;
- recomprimir;
- concatenar;
- mover automáticamente el E01.

Registrar antes de verificar:

```text
path
size_bytes
creation_time
last_write_time
```

Opcionalmente registrar:

```text
container_file_sha256
```

si se decide utilizarlo como control adicional de inmutabilidad.

No confundirlo con `MEDIA_SHA256`.

---

# 12. Timestamps del filesystem

Una lectura puede alterar `last access time` dependiendo de la configuración del filesystem.

Por ello:

- no considerar un cambio de `LastAccessTime` como corrupción;
- no restaurar timestamps automáticamente;
- no escribir en el E01 para restaurarlos;
- usar principalmente tamaño, `LastWriteTime` y hash del contenedor si se requiere comprobar inmutabilidad.

---

# 13. Segmentos

Para el caso real esperado:

```text
segment_count = 1
```

Si se detectan segmentos adicionales:

registrar:

```text
UNEXPECTED_SEGMENTATION
```

No borrar.

No concatenar.

No considerar la adquisición formalmente cerrada sin revisar la causa.

Los tests deben cubrir también conjuntos EWF segmentados aunque el objetivo operacional actual sea E01 único.

---

# 14. Command builder

Implementar o adaptar:

```text
build_ewfverify_command(context, capabilities)
```

Debe devolver:

- executable;
- argument list;
- log target si aplica.

Prohibido:

```text
shell=True
```

Prohibido aceptar argumentos arbitrarios del operador.

No construir comandos mediante concatenación de strings de shell.

---

# 15. Digests solicitados

Usar las opciones realmente soportadas por la versión local.

Objetivo:

- verificar MD5 almacenado/calculado;
- calcular MD5 del contenido;
- calcular SHA-256 del contenido si el verifier local lo soporta.

Si el EWF solo almacena internamente MD5 pero permite calcular SHA-256 adicional:

aceptar esa semántica.

Debe quedar explícito:

```text
MD5 stored in EWF
MD5 calculated over media data
SHA256 calculated over media data
```

No afirmar que SHA-256 está almacenado dentro del EWF salvo que la herramienta realmente lo reporte.

---

# 16. Parser de salida

El parser debe soportar los formatos reales observados por la versión instalada.

Debe reconocer conceptualmente campos como:

```text
hash stored in file
hash calculated over data
verification success
verification failure
read errors
checksum errors
```

No depender exclusivamente de una sola línea literal si la herramienta imprime variaciones de espacios o mayúsculas.

No declarar éxito únicamente por encontrar la palabra `SUCCESS` si existen indicadores críticos de error.

---

# 17. Condición de verificación exitosa

Solo declarar:

```text
VERIFICATION_COMPLETED
```

si simultáneamente:

1. el proceso terminó con código compatible con éxito;
2. la herramienta reporta verificación satisfactoria;
3. no existe error de integridad;
4. no existe error de lectura crítico;
5. MD5 calculado por verificación coincide con el MD5 de adquisición;
6. si existe MD5 almacenado en EWF, coincide con el MD5 calculado;
7. si se calcula SHA-256, coincide con el SHA-256 de adquisición;
8. los artefactos de metadata pudieron persistirse correctamente.

---

# 18. Matriz de comparación de hashes

Generar una estructura conceptual:

```text
Algorithm: MD5

acquisition_calculated:
bf63...

verification_calculated:
bf63...

ewf_stored:
bf63...

ftk_external_reference:
bf63...

result:
MATCH
```

Para SHA-256:

```text
Algorithm: SHA256

acquisition_calculated:
28c...

verification_calculated:
28c...

ewf_stored:
ONLY IF ACTUALLY PRESENT

result:
MATCH
```

Nunca inventar un `ewf_stored` inexistente.

---

# 19. HASH_MISMATCH

Si cualquier hash comparable difiere:

```text
HASH_MISMATCH
```

y:

```text
VERIFICATION_FAILED
```

No avanzar a AXIOM.

Registrar:

- algoritmo;
- valor esperado;
- valor observado;
- fuente de cada valor.

No sobrescribir el hash previo.

---

# 20. Hash faltante

Si SHA-256 no puede calcularse porque la versión instalada no lo soporta:

no inventarlo.

Registrar:

```text
NOT_SUPPORTED_BY_VERIFIER
```

Si MD5 de adquisición existe pero el verifier no puede validar ninguna forma de digest:

no considerar suficiente una verificación ambigua.

---

# 21. Ejecución

Usar:

```text
subprocess.Popen
```

o mecanismo equivalente controlado.

Capturar:

- PID;
- stdout;
- stderr;
- exit code;
- started_at;
- finished_at.

No ocultar salida crítica.

---

# 22. Logs

Crear o actualizar dentro de:

```text
ADQUISICION\logs\
```

Objetivo:

```text
ewfverify.log
verification_audit.jsonl
```

El audit debe registrar como mínimo:

```text
verification_prepared
verification_started
verification_pid
verification_completed
hash_comparison
state_transition
```

---

# 23. verification.json

Crear:

```text
ADQUISICION\metadata\verification.json
```

Debe contener:

```text
case_number
e01_path
e01_size_bytes
segment_count
tool
tool_version
command_args
started_at
finished_at
pid
exit_code
stdout_summary
stderr_summary
stored_hashes
calculated_media_hashes
acquisition_media_hashes
hash_comparisons
integrity_errors
result
```

No almacenar resultados ficticios.

---

# 24. hashes.json

Actualizar conservando evidencia anterior.

Estructura recomendada:

```json
{
  "media_hashes": {
    "md5": {
      "acquisition": "...",
      "verification": "...",
      "ewf_stored": "...",
      "external_ftk": "...",
      "status": "MATCH"
    },
    "sha256": {
      "acquisition": "...",
      "verification": "...",
      "status": "MATCH"
    }
  },
  "container_hashes": {
    "sha256": {
      "value": "...",
      "scope": "E01_FILE_BYTES",
      "status": "RECORDED"
    }
  }
}
```

`container_hashes` es opcional.

No mezclar namespaces.

---

# 25. acquisition.json

No reescribir desde cero.

Agregar una sección:

```text
verification
```

y conservar íntegramente:

- configuración de adquisición;
- argumentos;
- PID;
- exit code;
- stdout;
- stderr;
- hashes originales;
- timestamps;
- archivos generados.

---

# 26. acquisition_summary.json

Generar o completar:

```text
ADQUISICION\metadata\acquisition_summary.json
```

Debe servir posteriormente al Agente de Informe.

Incluir:

```text
case_number
source_physical_drive
source_model
source_serial
source_size_bytes
source_sector_count if known
source_bytes_per_sector if known
e01_path
e01_size_bytes
segment_count
format
compression
media_md5
media_sha256
acquisition_tool
acquisition_tool_version
verification_tool
verification_tool_version
verification_result
verification_started_at
verification_finished_at
cross_validation_ftk if recorded
final_acquisition_status
```

---

# 27. case.json

Usar escritura atómica ya implementada.

Antes de verificar:

```text
case.status = VERIFYING
acquisition.status = VERIFYING
```

si la máquina de estados existente lo permite.

Si todo termina correctamente:

```text
acquisition.status = VERIFIED
case.status = ANALYSIS_PENDING
analysis.status = PENDING
```

Si falla:

```text
acquisition.status = VERIFICATION_FAILED
case.status = VERIFICATION_FAILED
```

No avanzar a AXIOM automáticamente.

---

# 28. Estado ACQUISITION_CLOSED

Evitar duplicidad semántica innecesaria.

Si el modelo actual usa:

```text
VERIFIED
```

como estado terminal de adquisición, preferir:

```text
acquisition.status = VERIFIED
```

y no agregar `ACQUISITION_CLOSED` salvo que exista una necesidad clara.

El cierre formal queda implícito en:

```text
VERIFIED
```

---

# 29. Verificación real obligatoria del caso de laboratorio

Después de completar implementación y tests:

TRAE debe pedir autorización para verificar el E01 real:

```text
TEST-ACQ-001.E01
```

Esta operación es de lectura sobre el archivo E01 y no es una nueva adquisición.

Mostrar antes:

```text
Caso:
E01:
Tamaño:
Segmentos:
MD5 adquisición:
SHA-256 adquisición:
Herramienta de verificación:
Versión:
```

Confirmación manual sugerida:

```text
VERIFICAR
```

TRAE no debe ingresarla por el operador.

---

# 30. No requerir PhysicalDrive para verificar

La verificación del E01 no debe depender de que:

```text
\\.\PhysicalDrive6
```

siga conectado.

Si el software exige el disco físico para esta fase, existe un error de diseño.

Sprint 04 verifica el contenedor adquirido.

---

# 31. Resultado esperado para TEST-ACQ-001

El resultado ideal es:

```text
MEDIA MD5 adquisición:
bf63eaceec3a4e8cbbc1f9b698f3a70b

MEDIA MD5 verificación:
bf63eaceec3a4e8cbbc1f9b698f3a70b

MATCH
```

y, si la herramienta soporta SHA-256:

```text
MEDIA SHA256 adquisición:
28c376def067274843bab2bb5eac209514c1f8885d91d2b9ecf77b213c3645c0

MEDIA SHA256 verificación:
28c376def067274843bab2bb5eac209514c1f8885d91d2b9ecf77b213c3645c0

MATCH
```

No forzar estos resultados.

Si no coinciden:

la prueba debe fallar.

---

# 32. FTK como control independiente

La verificación interna del agente no depende de FTK.

Sin embargo, al finalizar, puede registrarse:

```text
CROSS_VALIDATION:
FTK 8.3.0.27
MD5 media: MATCH
Source size: MATCH
Sector count: 31.457.280
Bytes per sector: 512
```

Esto debe quedar claramente etiquetado como:

```text
INDEPENDENT_EXTERNAL_VALIDATION
```

---

# 33. Interrupción

Si el operador interrumpe:

- terminar proceso controladamente;
- no modificar E01;
- conservar logs;
- persistir estado;
- no marcar VERIFIED.

Usar:

```text
ABORTED
```

o estado equivalente ya definido.

---

# 34. Errores de integridad

Ante:

- CRC error;
- checksum error;
- corrupt chunk;
- read failure;
- malformed EWF;
- stored/calculated hash mismatch;

registrar:

```text
VERIFICATION_FAILED
```

No intentar reparar automáticamente.

No usar modos que sustituyan silenciosamente sectores corruptos para declarar éxito.

---

# 35. Prohibición de reparación

Sprint 04 no debe:

- reparar E01;
- rellenar sectores dañados para ocultar errores;
- reescribir checksums;
- regenerar segmentos;
- exportar un E01 nuevo;
- reemplazar el original.

Solo verificar y documentar.

---

# 36. Tests automatizados obligatorios

Mantener como baseline:

```text
77 tests
```

Agregar tests para al menos:

1. verifier inexistente;
2. ayuda válida;
3. versión;
4. capabilities;
5. command builder;
6. `shell=False`;
7. E01 inexistente;
8. E01 tamaño 0;
9. E01 único;
10. segmentos inesperados;
11. success realista;
12. exit code de error;
13. error textual aunque exit code sea 0;
14. MD5 acquisition vs calculated MATCH;
15. MD5 mismatch;
16. stored MD5 vs calculated MATCH;
17. stored MD5 mismatch;
18. SHA-256 acquisition vs calculated MATCH;
19. SHA-256 mismatch;
20. SHA-256 no soportado;
21. diferenciación media hash/container hash;
22. parser con espacios/casing;
23. `verification.json`;
24. `hashes.json` sin pérdida;
25. `acquisition.json` sin pérdida;
26. `acquisition_summary.json`;
27. case -> VERIFIED;
28. case -> VERIFICATION_FAILED;
29. interrupción;
30. persistencia atómica;
31. no acceso a PhysicalDrive;
32. no modificación del E01.

No usar el E01 real dentro de tests unitarios.

---

# 37. Prueba de inmutabilidad

En tests:

simular snapshot de:

```text
size
last_write_time
optional container hash
```

antes y después.

Debe comprobarse que el agente no escribe en el E01.

No exigir igualdad de `last access time`.

---

# 38. Test del parser con salida real

Cuando se ejecute la verificación real de laboratorio:

capturar stdout/stderr.

Después agregar al menos un test de regresión basado en el formato real observado por:

```text
ewfverify 20230405
```

o la versión realmente detectada.

No hardcodear rutas locales en el parser.

---

# 39. No implementar todavía

Fuera de alcance:

- AXIOM;
- procesamiento de artefactos;
- planilla XLS/XLSX de análisis;
- Portable Case;
- ZIP de resultados;
- identificación por fotografías;
- OCR;
- Word;
- Ollama.

---

# 40. Criterios de aceptación del Sprint 04

Sprint 04 queda `COMPLETADO` si:

- [ ] baseline de 77 tests pasa;
- [ ] verifier real detectado;
- [ ] ayuda real inspeccionada;
- [ ] versión real registrada;
- [ ] capabilities reales modeladas;
- [ ] command builder cerrado;
- [ ] `shell=True` ausente;
- [ ] E01 real no es modificado;
- [ ] PhysicalDrive no es requerido;
- [ ] verificación real de TEST-ACQ-001 se ejecutó con autorización humana;
- [ ] MD5 media calculado coincide con adquisición;
- [ ] stored MD5 coincide si existe;
- [ ] SHA-256 coincide si el verifier lo calcula;
- [ ] media hashes y container hashes están separados;
- [ ] logs persistidos;
- [ ] verification.json válido;
- [ ] hashes.json consolidado;
- [ ] acquisition.json preservado;
- [ ] acquisition_summary.json generado;
- [ ] case.json actualizado atómicamente;
- [ ] acquisition.status == VERIFIED;
- [ ] case.status == ANALYSIS_PENDING;
- [ ] validación FTK queda registrada solo como referencia independiente;
- [ ] todos los tests finales pasan.

---

# 41. Resultado de fallo

Sprint 04 debe quedar `REJECTED` o `INCOMPLETO` si:

- el verifier no puede abrir E01;
- reporta corrupción;
- media MD5 difiere;
- stored MD5 difiere;
- SHA-256 calculado difiere de adquisición;
- E01 cambia por acción del agente;
- metadata se corrompe;
- el sistema marca VERIFIED pese a error;
- el agente necesita acceder al disco físico original;
- se pierde trazabilidad.

---

# 42. Reporte final de TRAE

Entregar exactamente una sección de cierre similar a:

```text
SPRINT 04: COMPLETADO / INCOMPLETO

TESTS INICIALES:
...

VERIFIER DETECTADO:
...

VERSIÓN:
...

CAPABILITIES:
...

CASO REAL VERIFICADO:
TEST-ACQ-001

E01:
Ruta:
Tamaño:
Segmentos:

VERIFICACIÓN:
Inicio:
Fin:
PID:
Exit code:
Resultado:

MEDIA HASHES:
MD5 adquisición:
MD5 calculado:
MD5 stored:
Resultado MD5:

SHA256 adquisición:
SHA256 calculado:
Resultado SHA256:

CONTAINER HASHES:
...

VALIDACIÓN FTK INDEPENDIENTE:
...

ARCHIVOS CREADOS:
...

ARCHIVOS MODIFICADOS:
...

LOGS:
...

METADATA:
...

case.json:
...

TESTS FINALES:
...

VALIDACIONES DE SEGURIDAD:
...

OBSERVACIONES:
...

ESTADO FINAL DE ADQUISICION:
VERIFIED / VERIFICATION_FAILED

ESTADO DEL CASO:
ANALYSIS_PENDING / VERIFICATION_FAILED

RESULTADO FINAL:
ACCEPTED / ACCEPTED_WITH_OBSERVATIONS / REJECTED

SIGUIENTE SPRINT:
Sprint 05 — Agente de Identificación
```

No iniciar Sprint 05 automáticamente.

---

# 43. Instrucción final para TRAE

TRAE:

1. lee `PROMPT_MAESTRO.md`;
2. lee `SPRINT_04_OPTIMIZADO.md`;
3. ejecuta los 77 tests existentes;
4. inspecciona herramientas EWF reales;
5. identifica verifier;
6. lee ayuda y versión;
7. modela capabilities;
8. implementa/adapta parser;
9. diferencia MEDIA HASH y CONTAINER HASH;
10. implementa comando seguro;
11. implementa runner;
12. implementa logs y metadata;
13. agrega tests;
14. deja toda la suite en verde;
15. solicita confirmación manual `VERIFICAR` para el E01 real de `TEST-ACQ-001`;
16. ejecuta una única verificación real;
17. captura salida real;
18. compara hashes;
19. agrega regresión del parser si fue necesaria;
20. actualiza `case.json`;
21. no accedas al PhysicalDrive;
22. no ejecutes AXIOM;
23. entrega reporte final;
24. no inicies Sprint 05.

Comienza ahora.
