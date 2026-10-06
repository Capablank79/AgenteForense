# SPRINT_04_1_RECONCILIACION_VERIFICACION.md

# Sprint 04.1 — Reconciliación de política de verificación

## 1. Objetivo

Corregir la decisión formal tomada en Sprint 04 sin repetir `ewfverify`, sin volver a leer el E01 y sin acceder a ningún PhysicalDrive.

La ejecución real ya capturada sobre:

`G:\AgenteForense\casos\TEST-ACQ-001\ADQUISICION\TEST-ACQ-001.E01`

produjo:

- `ewfverify.exe 20230405`
- exit code `0`
- marcador `ewfverify: SUCCESS`
- sin errores de lectura/integridad
- E01 inmutable
- MEDIA SHA-256 adquisición = verificación
- MD5 adquisición = MD5 EWF/referencia
- ningún hash comparable en mismatch

El estado quedó en `VERIFICATION_FAILED` porque la política anterior exigió un MD5 explícitamente etiquetado como calculado durante verificación. Esa exigencia debe reconciliarse con la semántica real de `ewfverify` y EWF.

## 2. Acción previa obligatoria

Antes de implementar este sprint:

1. leer `PROMPT_MAESTRO.md`;
2. leer `REGLA_PERMANENTE_PRE_SPRINT.md`;
3. incorporar esa regla permanentemente en `PROMPT_MAESTRO.md` si aún no existe;
4. leer este sprint completo;
5. ejecutar toda la suite.

Baseline mínimo esperado:

`129 passed, 4 subtests passed`

o más si la suite creció legítimamente.

## 3. Prohibiciones

NO:

- ejecutar `ewfverify.exe`;
- ejecutar `ewfacquire.exe`;
- abrir ni leer nuevamente el E01;
- recalcular hashes leyendo el E01;
- acceder a `\\.\PhysicalDrive6`;
- integrar AXIOM;
- iniciar Sprint 05;
- alterar PID/timestamps originales;
- borrar el estado histórico `VERIFICATION_FAILED`;
- inventar un MD5 calculado que no aparece explícitamente.

## 4. Fuentes permitidas

Trabajar exclusivamente con artefactos ya persistidos:

- `case.json`
- `ADQUISICION\metadata\acquisition.json`
- `ADQUISICION\metadata\verification.json`
- `ADQUISICION\metadata\acquisition_summary.json`
- `ADQUISICION\hashes\hashes.json`
- `ADQUISICION\logs\ewfverify.log`
- `ADQUISICION\logs\verification_audit.jsonl`
- `ADQUISICION\logs\agent_acquisition.log`
- `ADQUISICION\logs\acquisition_audit.jsonl`

## 5. Semántica técnica

Adoptar explícitamente:

- `ewfverify` verifica media data almacenada en EWF;
- `-d sha256` calcula SHA-256 adicional;
- el MD5 almacenado/referenciado en EWF representa media data, no los bytes del archivo contenedor;
- MEDIA HASH y CONTAINER FILE HASH son dominios distintos.

Nunca mezclar:

`MEDIA_MD5`, `MEDIA_SHA256`, `EWF_STORED_MEDIA_HASH`, `CONTAINER_FILE_HASH`.

## 6. Evidencia del caso

Adquisición:

- MEDIA MD5: `bf63eaceec3a4e8cbbc1f9b698f3a70b`
- MEDIA SHA-256: `28c376def067274843bab2bb5eac209514c1f8885d91d2b9ecf77b213c3645c0`

Verificación real capturada:

- proceso: SUCCESS
- exit code: 0
- errores de lectura: ninguno
- errores de integridad: ninguno
- E01 inmutable: true
- SHA-256 calculado: `28c376def067274843bab2bb5eac209514c1f8885d91d2b9ecf77b213c3645c0`
- SHA-256: MATCH
- MD5 reportado en `Additional hash values`: `bf63eaceec3a4e8cbbc1f9b698f3a70b`
- MD5 adquisición vs referencia EWF: MATCH
- stored SHA-256: N/A

No modificar estos hechos.

## 7. Política correcta de decisión

Una verificación puede terminar en `VERIFIED` si simultáneamente:

1. el proceso termina con éxito;
2. la herramienta reporta éxito;
3. no hay errores de lectura;
4. no hay errores CRC/checksum/integridad;
5. el E01 permanece inmutable;
6. al menos un digest criptográfico calculado durante la verificación coincide con el digest de adquisición;
7. hashes almacenados/referenciados comparables son coherentes;
8. no existe ningún hash comparable en mismatch;
9. metadata y logs son coherentes.

No exigir dos digests calculados simultáneamente si la versión/herramienta no los expone de esa manera.

## 8. Aplicación a TEST-ACQ-001

Si los artefactos persistidos confirman el resumen anterior, la decisión reconciliada debe ser:

- `verification.status = VERIFIED`
- `acquisition.status = VERIFIED`
- `case.status = ANALYSIS_PENDING`
- `analysis.status = PENDING`

Si los artefactos contradicen el resumen, no promover el caso.

## 9. Conservar historial

No reescribir la historia.

Registrar:

- `previous_status = VERIFICATION_FAILED`
- `new_status = VERIFIED`
- razón de reconciliación;
- timestamp nuevo solo para la reconciliación;
- `verification_execution_repeated = false`
- `e01_re_read = false`
- `physical_drive_accessed = false`

Conservar PID original:

`20808`

Conservar timestamps originales de verificación.

## 10. Parser y clasificación MD5

No es obligatorio reclasificar:

`Additional hash values: MD5: ...`

como `verification_calculated_media_md5`.

Puede permanecer como:

`ewf_stored_or_reference_media_md5`

si esa es la clasificación soportada por salida/documentación.

Lo que cambia es la política: su ausencia como MD5 calculado no invalida por sí sola una verificación que ya tiene un SHA-256 calculado coincidente.

## 11. Modelo de evaluación

Separar:

- `process_success`
- `integrity_success`
- `calculated_media_hash_match`
- `stored_media_hash_consistency`
- `e01_immutable`
- `policy_decision`

No reducir el resultado a la existencia de un campo MD5.

## 12. verification.json

Preservar contenido existente y agregar:

- `policy_version`
- `previous_decision`
- `reconciled_decision`
- `decision_evidence`
- `policy_reconciliation`
- `verification_execution_repeated: false`
- `e01_re_read: false`

## 13. hashes.json

No cambiar valores.

Ajustar solo semántica/estado si corresponde.

Ejemplo conceptual:

- MD5 acquisition = valor real
- MD5 EWF/reference = mismo valor
- MD5 status = `CONSISTENT`
- SHA-256 acquisition = valor real
- SHA-256 verification-calculated = mismo valor
- SHA-256 status = `MATCH`

No crear un MD5 calculado inexistente.

## 14. acquisition.json

Preservar íntegramente:

- adquisición original;
- comando;
- PID;
- exit code;
- timestamps;
- stdout/stderr;
- hashes originales.

Agregar referencia a reconciliación de política.

## 15. acquisition_summary.json

Actualizar:

- verification_process_result = SUCCESS
- verification_policy_result = VERIFIED
- media_sha256_match = true
- md5_reference_consistent = true
- integrity_errors = none
- verification_repeated = false
- final_acquisition_status = VERIFIED

Solo si los artefactos reales lo respaldan.

## 16. case.json

Actualizar atómicamente.

Resultado esperado:

- `case.status = ANALYSIS_PENDING`
- `acquisition.status = VERIFIED`
- `analysis.status = PENDING`

No eliminar historial previo.

## 17. Auditoría

Agregar un evento nuevo, no modificar eventos históricos.

Evento sugerido:

`verification_policy_reconciled`

Registrar:

- timestamp;
- previous status;
- new status;
- reason;
- fuentes usadas;
- verifier not re-run;
- E01 not re-read;
- no PhysicalDrive access.

## 18. Fail-closed corregido

Fail-closed significa rechazar ante evidencia:

- insuficiente;
- contradictoria;
- insegura;
- corrupta;
- con mismatch.

No significa exigir información redundante que la herramienta/version no expone con una etiqueta específica.

## 19. Tests nuevos obligatorios

Agregar pruebas para:

1. SHA-256 calculated MATCH + MD5 reference MATCH -> VERIFIED;
2. SHA-256 calculated MATCH + MD5 calculated absent -> VERIFIED;
3. SHA-256 mismatch -> FAILED;
4. MD5 reference mismatch -> FAILED;
5. process failure -> FAILED;
6. integrity error -> FAILED;
7. E01 modified -> FAILED;
8. no calculated media hash available -> FAILED/INDETERMINATE;
9. original PID preserved;
10. original verification timestamps preserved;
11. verifier not executed;
12. E01 not opened/read;
13. PhysicalDrive not accessed;
14. previous failure remains auditable;
15. transition to ANALYSIS_PENDING;
16. hash values unchanged;
17. atomic persistence;
18. reconciliation idempotent.

## 20. Idempotencia

Una segunda ejecución de la reconciliación no debe:

- duplicar estados;
- alterar hashes;
- crear timestamps falsos de verificación;
- ejecutar herramientas;
- releer el E01.

## 21. Criterios de aceptación

Completo si:

- baseline pasa;
- regla permanente fue agregada al PROMPT_MAESTRO;
- ninguna herramienta forense fue ejecutada;
- E01 no fue leído;
- PhysicalDrive no fue accedido;
- política corregida;
- SHA-256 MATCH reconocido correctamente;
- MD5 reference correctamente clasificado;
- no se inventó MD5 calculado;
- historial de fallo conservado;
- metadata actualizada;
- audit trail agregado;
- `acquisition.status = VERIFIED`;
- `case.status = ANALYSIS_PENDING`;
- todos los tests pasan.

## 22. Reporte final de TRAE

Entregar:

```text
SPRINT 04.1: COMPLETADO / INCOMPLETO

BASELINE:
...

REGLA PERMANENTE PRE-SPRINT:
AGREGADA / NO AGREGADA

HERRAMIENTAS FORENSES EJECUTADAS:
NINGUNA

E01 LEÍDO:
NO

PHYSICALDRIVE ACCEDIDO:
NO

POLÍTICA ANTERIOR:
...

POLÍTICA NUEVA:
...

MEDIA SHA256:
Acquisition:
Verification:
Result:

MD5:
Acquisition:
EWF reference:
Result:

ESTADO PREVIO:
VERIFICATION_FAILED

ESTADO RECONCILIADO:
...

ARCHIVOS MODIFICADOS:
...

AUDITORÍA:
...

TESTS NUEVOS:
...

TESTS FINALES:
...

ESTADO FINAL DE ADQUISICION:
...

ESTADO DEL CASO:
...

RESULTADO:
ACCEPTED / REJECTED
```

No iniciar Sprint 05.

## 23. Instrucción final

TRAE:

1. lee `PROMPT_MAESTRO.md`;
2. lee `REGLA_PERMANENTE_PRE_SPRINT.md`;
3. agrega esa regla al `PROMPT_MAESTRO.md` si falta;
4. lee este sprint;
5. ejecuta baseline;
6. no ejecutes herramientas forenses;
7. no abras ni leas el E01;
8. no accedas a PhysicalDrive;
9. reconcilia solo desde artefactos persistidos;
10. conserva todo el historial;
11. implementa la política corregida;
12. agrega tests;
13. deja toda la suite en verde;
14. actualiza estados solo si la evidencia persistida sustenta VERIFIED;
15. entrega reporte final;
16. no inicies Sprint 05.

Comienza ahora.
