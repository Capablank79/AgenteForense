# SPRINT_03.md

# Sprint 03 — Integración controlada de ewfacquire y adquisición E01

## 1. Objetivo

Integrar `ewfacquire.exe` al Agente Forense Local para Windows utilizando la arquitectura definitiva del proyecto.

Este sprint parte desde un `CaseContext` válido, persistido en `case.json` y en estado `READY`, producido por Sprint 02.5.

Debe dejar implementada y testeada la adquisición forense física E01, pero NO ejecutar automáticamente una adquisición real durante el desarrollo.

La adquisición real requerirá confirmación humana explícita.

## 2. Regla previa obligatoria

Antes de comenzar:

1. leer completamente `G:\AgenteForense\PROMPT_MAESTRO.md`;
2. leer este `SPRINT_03.md`;
3. ejecutar toda la suite existente;
4. confirmar que Sprint 01, 02 y 02.5 siguen pasando;
5. inspeccionar el binario local real `G:\AgenteForense\ew\ewftools-x64\ewfacquire.exe`.

La versión local instalada es la fuente de verdad. No asumir argumentos por memoria ni documentación externa si no coinciden con el binario local.

## 3. Estructura oficial de salida

Toda la adquisición debe quedar dentro de:

`<CASO>\ADQUISICION`

Estructura objetivo:

```text
<CASO>\
├── case.json
├── IDENTIFICACION\
├── ADQUISICION\
│   ├── <CASO>.E01
│   ├── logs\
│   ├── hashes\
│   └── metadata\
├── ANALISIS\
├── RESULTADOS\
└── REPORTE\
```

No crear carpetas principales antiguas ni guardar E01 fuera de `ADQUISICION`.

## 4. Inspección obligatoria de ewfacquire

Antes de implementar el command builder, ejecutar de forma no destructiva:

```text
G:\AgenteForense\ew\ewftools-x64\ewfacquire.exe -h
```

y consultar versión si el binario dispone de esa opción.

Registrar:

- versión;
- formatos EWF soportados;
- compresión disponible;
- hashes soportados;
- tamaño de segmento;
- parámetros de case number;
- evidence number;
- description;
- examiner;
- notes;
- log;
- target;
- source;
- modo físico si existe explícitamente.

Modelar estas capacidades. No inventar flags.

## 5. Modelo de capacidades

Crear un modelo explícito, por ejemplo `EwfAcquireCapabilities`, que represente únicamente capacidades comprobadas:

```text
version
supported_formats
supported_compression_levels
supported_hashes
supports_case_number
supports_evidence_number
supports_description
supports_examiner
supports_notes
supports_log
supports_segment_size
supports_physical_mode
```

## 6. Ejecutable

Ruta:

`G:\AgenteForense\ew\ewftools-x64\ewfacquire.exe`

Validar que existe, es archivo, es invocable y responde a `-h`. Si falla, estado `FAILED`. No descargar reemplazos.

## 7. Origen

El origen debe provenir únicamente del snapshot validado en `CaseContext` y `case.json`.

Formato:

`\\.\PhysicalDriveN`

Nunca usar letra de unidad, partición, volumen lógico, carpeta o archivo.

## 8. Revalidación final del origen

Inmediatamente antes de iniciar adquisición, reconsultar Windows y comparar:

- disk_number;
- physical_drive;
- serial_number;
- size_bytes;
- friendly_name;
- bus_type;
- is_read_only;
- is_system;
- is_boot.

Abortar si `IsReadOnly != True`, `IsSystem == True`, `IsBoot == True`, cambia serial, cambia tamaño o desaparece el disco. No seleccionar otro disco automáticamente.

## 9. Revalidación del destino

Antes de ejecutar, revalidar:

- `ADQUISICION` existe;
- destino escribible;
- filesystem;
- espacio libre;
- disco físico del destino;
- origen y destino siguen siendo discos distintos.

Si el destino pertenece al mismo PhysicalDrive, ABORTAR.

## 10. E01 previo

Antes de iniciar, buscar:

`ADQUISICION\<CASO>.E01`

Si existe, ABORTAR. No sobrescribir, eliminar ni renombrar automáticamente.

## 11. Adquisición física completa

Debe corresponder al dispositivo físico completo e incluir sector inicial, tabla de particiones, particiones, espacio no asignado, estructuras fuera de particiones y todos los sectores hasta el final.

No realizar adquisición lógica ni de una sola partición.

## 12. Formato EWF

Objetivo: `E01`.

Preferir un formato moderno soportado por la versión local. `encase6` es solo referencia conceptual: usarlo únicamente si aparece realmente soportado. No cambiar a RAW/DD.

## 13. Compresión

Usar la compresión máxima soportada. Si el binario local soporta `best`, utilizarla. Registrar `compression_method` y `compression_level`.

## 14. Un único E01

Requisito operativo: intentar generar exactamente `<CASO>.E01`, sin segmentación intencional.

Antes de ejecutar:

1. obtener `source_size_bytes`;
2. detectar soporte real de `-S` o equivalente;
3. determinar máximo permitido;
4. calcular tamaño de segmento mayor al origen;
5. comprobar que filesystem destino soporta el archivo;
6. comprobar que la herramienta soporta ese tamaño.

Si no puede garantizarse técnicamente un único E01, ABORTAR y registrar `SINGLE_E01_NOT_GUARANTEED`. No segmentar automáticamente.

## 15. Filesystem destino

Aplicar política conservadora. FAT32 debe bloquearse si el archivo potencial puede exceder su límite. NTFS es apto si dispone de espacio suficiente. ReFS/exFAT se evalúan según capacidades reales ya implementadas. No formatear ni convertir filesystem.

## 16. Espacio libre

Comparar `source_size_bytes` con `destination_free_bytes`.

Si espacio libre >= tamaño RAW, marcar `RAW_SIZE_CAPACITY_OK`.

Si espacio libre < tamaño RAW, no asumir que la compresión resolverá el problema. Mostrar advertencia crítica y exigir segunda confirmación explícita antes de una adquisición real. Registrar `LOW_FREE_SPACE_WARNING`.

## 17. Nombre de salida

Base: `<case_number>`.

Ruta base:

`<CASO>\ADQUISICION\<case_number>`

La extensión final debe seguir la sintaxis real esperada por `ewfacquire`. Confirmarlo con `-h`.

## 18. Metadata EWF

Mapear campos disponibles desde `CaseContext`. Usar cuando la herramienta lo soporte:

- case number;
- description;
- evidence number;
- examiner;
- notes.

No inventar valores.

## 19. Construcción del comando

Crear una función cerrada y testeable, por ejemplo:

`build_ewfacquire_command(context, capabilities)`

Debe devolver ejecutable, lista de argumentos y ruta de trabajo si aplica.

Usar `subprocess` con lista de argumentos. No usar `shell=True`.

## 20. Seguridad del command builder

Los argumentos solo pueden provenir de `CaseContext`, `case.json`, configuración interna y capabilities detectadas. No aceptar flags libres del operador, fragmentos de shell ni parámetros arbitrarios.

## 21. Estados

Extender `AppState` con:

```text
PREPARING_ACQUISITION
WAITING_FINAL_CONFIRMATION
ACQUIRING
ACQUISITION_COMPLETED
ACQUISITION_FAILED
ABORTED
```

No usar todavía `VERIFIED`.

## 22. Persistencia en case.json

Actualizar `case.json` durante la adquisición.

Antes de ejecutar: `acquisition.status = READY`.

Al iniciar: `acquisition.status = ACQUIRING`.

Al finalizar correctamente: `acquisition.status = ACQUISITION_COMPLETED`.

Si falla: `acquisition.status = ACQUISITION_FAILED`.

No marcar `VERIFIED`. Usar escritura atómica existente.

## 23. Confirmación humana final

Antes de una adquisición real mostrar un resumen completo del caso, origen, modelo, serial, tamaño, ReadOnly, destino, formato, compresión, segmentación y archivo esperado.

Exigir entrada exacta:

`ADQUIRIR`

Cualquier otro texto: ABORTAR.

## 24. Segunda confirmación por espacio

Si `destination_free_bytes < source_size_bytes`, exigir además:

`CONTINUAR_CON_RIESGO`

Registrar esta decisión.

## 25. Ejecución

Usar `subprocess.Popen` o equivalente controlado. Capturar:

- PID;
- stdout;
- stderr;
- exit code;
- started_at;
- finished_at.

Mostrar progreso cuando sea posible y no ocultar errores.

## 26. Logs

Crear bajo:

`ADQUISICION\logs\`

Como mínimo `agent_acquisition.log` y cualquier log nativo soportado por `ewfacquire`.

Registrar inicio, estados, revalidaciones, comando, PID, timestamps, exit code, errores y archivos generados.

## 27. Metadata

Crear bajo:

`ADQUISICION\metadata\`

Por ejemplo `acquisition.json` con:

- case_number;
- source;
- destination;
- ewfacquire path;
- versión;
- capabilities;
- format;
- compression;
- segment size;
- timestamps;
- exit code;
- generated files;
- generated segment count;
- acquisition status.

## 28. Hashes

Si `ewfacquire` soporta hashes, habilitar los requeridos. Preferir MD5 si es nativo/obligatorio y SHA-256 adicional si está soportado.

Guardar resultados estructurados bajo `ADQUISICION\hashes\`.

## 29. Interrupción

Si el operador pulsa Ctrl+C:

- capturar `KeyboardInterrupt`;
- terminar el proceso de forma controlada;
- registrar `ABORTED`;
- conservar archivos parciales;
- actualizar `case.json`.

## 30. Inspección post-ejecución

Después de exit code 0, examinar `ADQUISICION` y confirmar:

- existe E01;
- tamaño > 0;
- número de segmentos;
- extensiones.

Si existe un solo `.E01`, registrar `generated_segment_count = 1`.

Si existen `.E02`, `.E03`, etc., registrar `UNEXPECTED_SEGMENTATION`. No borrar ni concatenar.

## 31. Resultado del Sprint 03

Si exit code == 0 y existe E01, estado `ACQUISITION_COMPLETED`.

Esto significa adquisición finalizada pero todavía no verificada. Sprint 04 ejecutará verificación EWF independiente.

## 32. Prueba real durante desarrollo

TRAE NO debe iniciar adquisición física automáticamente.

Durante desarrollo puede consultar ayuda, versión, construir comando, ejecutar mocks, probar parser, logs, metadata y máquina de estados.

Al final debe detenerse en:

`LISTO PARA PRUEBA DE ADQUISICIÓN REAL`

## 33. Tests obligatorios

Mantener todos los tests previos y agregar cobertura para:

- ewfacquire inexistente;
- `-h` válido;
- parseo de capabilities;
- formato soportado;
- compresión máxima;
- hash soportado;
- cálculo de segment size;
- límite insuficiente;
- FAT32 incompatible;
- E01 previo existente;
- revalidación origen falla;
- revalidación destino falla;
- command builder;
- `shell=False`;
- confirmación distinta de `ADQUIRIR`;
- confirmación por espacio insuficiente;
- exit code 0;
- exit code no cero;
- interrupción;
- E01 único;
- múltiples segmentos;
- metadata;
- hashes;
- logs;
- actualización atómica de `case.json`.

No usar un PhysicalDrive real en tests.

## 34. Fuera de alcance

No implementar todavía:

- `ewfverify`;
- cierre definitivo de hashes;
- AXIOM;
- identificación fotográfica;
- OCR;
- XLS/XLSX;
- Portable Case;
- ZIP;
- informe Word;
- Ollama.

## 35. Definición de terminado

Sprint 03 es COMPLETO cuando:

- [ ] toda la suite anterior pasa;
- [ ] ewfacquire local es detectado;
- [ ] ayuda local es inspeccionada;
- [ ] versión registrada;
- [ ] capabilities modeladas;
- [ ] formato E01 seleccionado;
- [ ] compresión máxima seleccionada;
- [ ] tamaño de segmento calculado;
- [ ] un solo E01 es objetivo obligatorio;
- [ ] E01 previo bloquea;
- [ ] origen se revalida;
- [ ] destino se revalida;
- [ ] command builder es seguro;
- [ ] `shell=True` no se usa;
- [ ] confirmación `ADQUIRIR` existe;
- [ ] ejecución controlada está implementada;
- [ ] PID/stdout/stderr/exit code se capturan;
- [ ] interrupción está controlada;
- [ ] logs se escriben bajo ADQUISICION;
- [ ] metadata se escribe bajo ADQUISICION;
- [ ] hashes se registran bajo ADQUISICION;
- [ ] `case.json` se actualiza;
- [ ] segmentación inesperada se detecta;
- [ ] no se ejecutó adquisición real automáticamente;
- [ ] todos los tests pasan.

## 36. Reporte final de TRAE

Al terminar responder:

```text
SPRINT 03: COMPLETADO / INCOMPLETO

TESTS INICIALES:
...

EWFACQUIRE DETECTADO:
...

VERSIÓN:
...

CAPABILITIES DETECTADAS:
...

ARCHIVOS CREADOS:
...

ARCHIVOS MODIFICADOS:
...

COMANDO GENERADO:
...

ESTRUCTURA ADQUISICION:
...

PRUEBAS:
...

RESULTADOS:
...

VALIDACIONES DE SEGURIDAD:
...

RIESGOS / LIMITACIONES:
...

ESTADO:
LISTO / NO LISTO PARA PRUEBA DE ADQUISICIÓN REAL

SIGUIENTE SPRINT:
Sprint 04 — Verificación EWF, hashes finales y cierre de ADQUISICION.
```

No iniciar Sprint 04.

## 37. Instrucción de inicio

TRAE:

1. lee `PROMPT_MAESTRO.md`;
2. lee `SPRINT_03.md`;
3. ejecuta los 67 tests existentes;
4. inspecciona `ewfacquire.exe -h`;
5. inspecciona versión;
6. modela capabilities;
7. adapta `planner.py`, `runner.py` y `workflow.py` existentes;
8. implementa command builder seguro;
9. implementa persistencia en `case.json`;
10. implementa logs, hashes y metadata bajo `ADQUISICION`;
11. agrega tests;
12. corrige hasta que toda la suite pase;
13. NO ejecutes adquisición física real;
14. termina en `LISTO PARA PRUEBA DE ADQUISICIÓN REAL`.

Comienza ahora.
