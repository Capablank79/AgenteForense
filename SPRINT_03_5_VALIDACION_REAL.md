# SPRINT_03_5_VALIDACION_REAL.md

# Sprint 03.5 — Validación real controlada de adquisición

## 1. Objetivo
Validar en condiciones reales que Sprint 03 funciona contra Windows real, un dispositivo físico de laboratorio, un bloqueador de escritura físico, `ewfacquire.exe` real y un destino real.

Este sprint NO agrega funcionalidades nuevas salvo correcciones mínimas necesarias para que la prueba de aceptación funcione.

Debe responder: **¿La adquisición real funciona de extremo a extremo de manera segura, trazable y reproducible?**

## 2. Alcance
Validar únicamente:

```text
SELECCIÓN DEL DISCO
↓
VALIDACIÓN READ-ONLY
↓
CREACIÓN DEL CASO
↓
PREPARACIÓN DE ADQUISICIÓN
↓
CONFIRMACIÓN HUMANA
↓
EJECUCIÓN REAL DE ewfacquire
↓
GENERACIÓN DE E01
↓
LOGS / HASHES / METADATA
↓
case.json
↓
ACQUISITION_COMPLETED
```

No ejecutar todavía:
- `ewfverify`;
- AXIOM;
- análisis de fotografías;
- XLS/XLSX;
- Portable Case;
- reporte Word;
- Ollama.

## 3. Medio de prueba obligatorio
Utilizar únicamente un dispositivo de laboratorio. No usar evidencia real.

Preferir un USB, SSD o disco de laboratorio de tamaño moderado.

El dispositivo debe identificarse inequívocamente por:
- marca;
- modelo;
- serial;
- tamaño.

## 4. Preparación del medio de laboratorio
Antes de conectarlo al bloqueador, preparar el medio con archivos conocidos.

Ejemplo:

```text
LAB_TEST\
├── prueba.txt
├── documento.pdf
├── imagen.jpg
└── carpeta\
    └── archivo_interno.txt
```

No es necesario validar contenido en este sprint. El objetivo es dejar datos reconocibles para futuras pruebas AXIOM.

## 5. Condición crítica: bloqueador físico
Conectar el medio de laboratorio mediante el bloqueador de escritura físico.

El sistema debe reportar:

```text
IsReadOnly = True
IsSystem   = False
IsBoot     = False
```

Si `IsReadOnly = False`, DETENER.

No usar software para convertir el disco en read-only.

## 6. Identificación del disco
Antes de adquirir, mostrar:
- Disk Number
- PhysicalDrive
- FriendlyName
- SerialNumber
- Size
- BusType
- IsReadOnly
- IsSystem
- IsBoot
- OperationalStatus
- HealthStatus

El operador debe confirmar visualmente que corresponde al dispositivo de laboratorio.

## 7. Caso de prueba
Crear un caso dedicado, preferentemente:

`TEST-ACQ-001`

o equivalente válido.

No reutilizar un caso existente.

## 8. Destino
Elegir un destino distinto al disco fuente.

Debe:
- ser escribible;
- tener filesystem compatible;
- tener espacio suficiente;
- no residir en el mismo PhysicalDrive;
- soportar un único E01.

## 9. Estructura esperada
Después de crear el caso:

```text
TEST-ACQ-001\
├── case.json
├── IDENTIFICACION\
├── ADQUISICION\
├── ANALISIS\
├── RESULTADOS\
└── REPORTE\
```

Antes de adquirir, verificar que no existe:

`TEST-ACQ-001.E01`

## 10. Preparación de adquisición
Ejecutar el flujo normal de Sprint 03 hasta:

`LISTO PARA ADQUISICIÓN REAL`

Antes de escribir `ADQUIRIR`, revisar que coincidan:
- caso;
- PhysicalDrive;
- modelo;
- serial;
- tamaño;
- `IsReadOnly=True`;
- destino;
- formato;
- compresión;
- objetivo de E01 único;
- archivo esperado.

## 11. Registro previo obligatorio
Registrar:

```text
Número de caso:
PhysicalDrive:
Marca/modelo:
Serial:
Tamaño:
ReadOnly:
Destino:
Filesystem:
Espacio libre:
Formato:
Compresión:
Segment size:
ewfacquire version:
```

No inventar datos.

## 12. Confirmación
Escribir únicamente:

`ADQUIRIR`

cuando toda la información sea correcta.

Si existe advertencia de espacio, registrar cualquier segunda confirmación.

## 13. Ejecución real
Permitir a `ewfacquire` completar la adquisición.

Durante ejecución, confirmar:
- PID visible/registrado;
- stdout/stderr capturados;
- logs actualizados;
- ausencia de errores críticos;
- origen no cambia;
- no se selecciona otro disco.

## 14. No intervenir manualmente
Durante la adquisición no:
- desconectar origen;
- desconectar destino;
- cerrar consola;
- matar proceso;
- modificar carpetas;
- renombrar archivos;
- montar/desmontar manualmente el origen.

## 15. Resultado esperado de archivos
Después de terminar:

```text
ADQUISICION\
├── TEST-ACQ-001.E01
├── logs\
├── hashes\
└── metadata\
```

No deben existir `.E02`, `.E03`, etc.

Si aparecen, marcar:

`UNEXPECTED_SEGMENTATION`

y considerar fallido el requisito de E01 único.

## 16. Validación del E01
Confirmar que el `.E01`:
- existe;
- tamaño > 0;
- fecha/hora coherente;
- está en `ADQUISICION`;
- no está fuera del caso.

Registrar tamaño exacto.

## 17. Validación de logs
Confirmar:

```text
ADQUISICION\logs\agent_acquisition.log
ADQUISICION\logs\acquisition_audit.jsonl
```

y log nativo si corresponde.

Revisar que contengan:
- inicio;
- caso;
- origen;
- destino;
- herramienta;
- PID;
- timestamps;
- exit code;
- estado final.

## 18. Validación de metadata
Confirmar:

`ADQUISICION\metadata\acquisition.json`

Debe ser JSON válido y contener como mínimo:
- case_number;
- source;
- serial;
- source_size;
- destination;
- ewfacquire version;
- format;
- compression;
- segment size;
- timestamps;
- exit code;
- generated files;
- segment count;
- status.

## 19. Validación de hashes
Confirmar:

`ADQUISICION\hashes\hashes.json`

Si `ewfacquire` entregó hashes, deben estar realmente registrados.

No exigir un hash que la herramienta no haya emitido.

No fabricar valores.

## 20. Validación de case.json
Abrir `case.json`.

Debe seguir siendo JSON válido.

Después de adquisición exitosa:

`acquisition.status = ACQUISITION_COMPLETED`

No debe indicar todavía `VERIFIED`.

## 21. Exit code
Registrar exit code real.

La adquisición solo puede considerarse completada si:
- el proceso finaliza según comportamiento esperado;
- existe E01 válido;
- no existen errores críticos;
- metadata/logs son coherentes.

## 22. Validación de identidad
Comparar antes y después:
- PhysicalDrive
- SerialNumber
- Size
- FriendlyName
- BusType
- IsReadOnly
- IsSystem
- IsBoot

Debe mantenerse la identidad.

Si cambia, la prueba falla.

## 23. Validación de seguridad
Confirmar explícitamente:
- no se ejecutó `Set-Disk`;
- no se ejecutó DiskPart;
- no se ejecutó CHKDSK;
- no se formateó origen;
- no se inicializó origen;
- no se escribió en origen;
- no se usó `shell=True`;
- no se adquirió una letra de unidad;
- la fuente fue `\\.\PhysicalDriveN`.

## 24. Prueba de rechazo obligatoria
Además de la adquisición exitosa, ejecutar al menos una prueba negativa sin adquirir.

Ejemplo recomendado: medio sin read-only o mock seguro.

Confirmar que `IsReadOnly = False` impide llegar a `ADQUIRIR`.

## 25. Segunda prueba negativa
Intentar configurar como destino el mismo disco físico del origen en un entorno de prueba seguro.

El sistema debe bloquear antes de adquisición.

## 26. Tercera prueba negativa
Crear previamente un archivo:

`ADQUISICION\TEST-ACQ-XXX.E01`

en un caso de prueba independiente.

El sistema debe bloquear sobrescritura.

No eliminar automáticamente el archivo.

## 27. No repetir adquisición innecesariamente
Una adquisición real exitosa es suficiente para aceptación inicial.

Las pruebas negativas deben realizarse sin una adquisición física adicional cuando sea posible.

## 28. Evidencia de aceptación
Crear:

`ADQUISICION\metadata\acceptance_test.json`

Debe contener:
- test_case;
- date;
- operator;
- source_identity;
- destination;
- read_only_check;
- ewfacquire_version;
- command_summary;
- start_time;
- end_time;
- exit_code;
- e01_path;
- e01_size;
- segment_count;
- hashes_detected;
- case_json_status;
- negative_tests;
- final_result.

No almacenar secretos.

## 29. Resultado final
Solo:

`ACCEPTED`
`ACCEPTED_WITH_OBSERVATIONS`
`REJECTED`

Usar `ACCEPTED` si todos los criterios críticos pasan.

Usar `ACCEPTED_WITH_OBSERVATIONS` solo para observaciones no críticas.

Usar `REJECTED` si falla cualquier criterio crítico.

## 30. Criterios críticos
La prueba debe ser `REJECTED` si ocurre cualquiera:
- origen no read-only;
- origen system/boot;
- disco incorrecto;
- destino en mismo disco físico;
- comando inseguro;
- adquisición lógica en vez de física;
- E01 inexistente;
- E01 vacío;
- exit code incompatible con éxito;
- segmentación inesperada;
- `case.json` incoherente;
- metadata corrupta;
- error crítico no manejado;
- sobrescritura de evidencia previa;
- pérdida de trazabilidad.

## 31. Correcciones permitidas
Si la prueba detecta un defecto, TRAE puede hacer una corrección mínima.

Después debe:
1. documentarla;
2. ejecutar toda la suite;
3. repetir únicamente la parte necesaria;
4. no introducir features nuevas.

## 32. Tests automatizados
Después de cualquier corrección, todos los tests deben pasar.

Esperado como mínimo:

`76 passed`

o más si se agregan pruebas de regresión.

## 33. No ejecutar Sprint 04 todavía
Aunque la adquisición resulte exitosa, no iniciar automáticamente Sprint 04.

Primero entregar reporte de aceptación.

## 34. Reporte final de TRAE
Al terminar:

```text
SPRINT 03.5: COMPLETADO / INCOMPLETO

PRUEBA REAL EJECUTADA:
SI / NO

CASO DE PRUEBA:
...

ORIGEN:
PhysicalDrive:
Modelo:
Serial:
Tamaño:
ReadOnly:

DESTINO:
...

EWFACQUIRE:
Ruta:
Versión:

ADQUISICIÓN:
Inicio:
Fin:
Exit code:

E01:
Ruta:
Tamaño:
Segmentos:

HASHES DETECTADOS:
...

LOGS:
...

METADATA:
...

case.json:
...

PRUEBAS NEGATIVAS:
1. ReadOnly false:
2. Mismo disco destino:
3. E01 preexistente:

CORRECCIONES REALIZADAS:
...

TESTS AUTOMATIZADOS:
...

VALIDACIONES DE SEGURIDAD:
...

OBSERVACIONES:
...

RESULTADO FINAL:
ACCEPTED / ACCEPTED_WITH_OBSERVATIONS / REJECTED

ESTADO:
LISTO / NO LISTO PARA SPRINT 04
```

## 35. Instrucción operativa importante
TRAE no debe escoger por sí solo qué PhysicalDrive adquirir.

Debe mostrar candidatos y esperar selección humana.

TRAE no debe escribir `ADQUIRIR` automáticamente.

La confirmación debe ser ingresada manualmente por el operador.

## 36. Instrucción de inicio
TRAE:

1. lee `PROMPT_MAESTRO.md`;
2. lee `SPRINT_03_5_VALIDACION_REAL.md`;
3. ejecuta los tests existentes;
4. prepara una prueba real exclusivamente con medio de laboratorio;
5. muestra discos;
6. espera selección humana;
7. valida `IsReadOnly=True`;
8. crea un caso de prueba nuevo;
9. valida destino;
10. muestra el resumen de adquisición;
11. espera que el operador escriba `ADQUIRIR`;
12. ejecuta una única adquisición real controlada;
13. inspecciona todos los artefactos generados;
14. ejecuta pruebas negativas sin adquisición real adicional cuando sea posible;
15. corrige únicamente defectos necesarios;
16. vuelve a ejecutar tests;
17. genera `acceptance_test.json`;
18. entrega el reporte final;
19. NO ejecutes Sprint 04.

Comienza ahora.
