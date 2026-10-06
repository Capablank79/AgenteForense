# SPRINT_02_5.md

# Sprint 02.5 — Migración a la estructura definitiva del caso

## 1. Objetivo

Alinear la implementación existente de Sprint 01 y Sprint 02 con la nueva estructura oficial definida en `PROMPT_MAESTRO.md`, sin rehacer lógica ya funcional.

Este sprint es una **migración de arquitectura**, no una reimplementación.

Debe conservar:

- detección de discos;
- selección segura;
- validación `IsReadOnly=True`;
- bloqueo `IsSystem=True`;
- bloqueo `IsBoot=True`;
- validación de número de caso;
- validación de destino;
- comprobación de origen y destino en discos físicos distintos;
- revalidación de identidad;
- `CaseContext`;
- `AppState`;
- manejo de errores;
- tests existentes que sigan siendo aplicables.

Debe modificar únicamente lo necesario para adoptar la estructura definitiva:

```text
<CASO>\
├── case.json
├── IDENTIFICACION\
├── ADQUISICION\
├── ANALISIS\
├── RESULTADOS\
└── REPORTE\
```

No ejecutar `ewfacquire`.

No integrar Ollama.

---

## 2. Regla previa obligatoria

Antes de comenzar:

1. leer completamente `G:\AgenteForense\PROMPT_MAESTRO.md`;
2. leer este `SPRINT_02_5.md`;
3. ejecutar toda la suite existente;
4. registrar el número de tests y resultado;
5. inspeccionar la estructura actual del código;
6. no reescribir módulos que ya funcionan sin necesidad.

---

## 3. Principio de migración

No destruir trabajo válido.

No sustituir módulos completos por versiones nuevas si basta con adaptar:

- rutas;
- modelos;
- constructores;
- tests;
- serialización;
- nombres de campos.

La meta es:

**mínimo cambio necesario + cero regresiones**.

---

## 4. Estructura oficial del caso

Reemplazar cualquier estructura previa como:

```text
<CASO>\
├── evidence\
├── logs\
├── metadata\
├── hashes\
└── reports\
```

por:

```text
<CASO>\
├── case.json
├── IDENTIFICACION\
├── ADQUISICION\
├── ANALISIS\
├── RESULTADOS\
└── REPORTE\
```

Esta estructura es definitiva.

No crear carpetas principales paralelas.

---

## 5. Subcarpetas técnicas permitidas

Se permiten subcarpetas dentro de las carpetas oficiales.

Ejemplo válido:

```text
ADQUISICION\
├── logs\
├── hashes\
└── metadata\
```

Ejemplo inválido:

```text
<CASO>\
├── ADQUISICION\
├── hashes\
├── logs\
└── metadata\
```

Los artefactos técnicos de adquisición deben vivir dentro de `ADQUISICION`.

---

## 6. Estructura inicial a crear

Al crear un caso nuevo, debe existir exactamente:

```text
<CASO>\
├── case.json
├── IDENTIFICACION\
├── ADQUISICION\
├── ANALISIS\
├── RESULTADOS\
└── REPORTE\
```

No crear por defecto subcarpetas adicionales salvo que ya sean necesarias para funcionalidades existentes.

Si se requieren por compatibilidad interna, deben estar justificadas y dentro de la carpeta oficial correspondiente.

---

## 7. case.json

Crear `case.json` en la raíz de cada caso.

Debe actuar como índice maestro.

En Sprint 02.5 debe contener como mínimo:

```json
{
  "schema_version": 1,
  "case_number": "CASO-2026-001",
  "status": "READY",
  "paths": {
    "case_root": "...",
    "identificacion": "...",
    "adquisicion": "...",
    "analisis": "...",
    "resultados": "...",
    "reporte": "..."
  },
  "source": {
    "disk_number": 0,
    "physical_drive": "\\\\.\\PhysicalDrive0",
    "friendly_name": "...",
    "serial_number": "...",
    "size_bytes": 0,
    "bus_type": "...",
    "is_read_only": true,
    "is_system": false,
    "is_boot": false
  },
  "destination": {
    "root": "...",
    "filesystem": "...",
    "total_bytes": 0,
    "free_bytes": 0
  },
  "identification": {
    "status": "PENDING"
  },
  "acquisition": {
    "status": "PENDING"
  },
  "analysis": {
    "status": "PENDING"
  },
  "results": {
    "status": "PENDING"
  },
  "report": {
    "status": "PENDING"
  }
}
```

Los nombres exactos pueden adaptarse a los modelos existentes, pero deben conservar el significado.

No inventar datos.

---

## 8. Persistencia segura de case.json

Escribir `case.json` de forma segura.

Preferir:

1. serializar a archivo temporal;
2. flush;
3. reemplazo atómico cuando sea posible.

No dejar JSON truncado si ocurre un error.

Codificación:

`UTF-8`

Formato legible:

indentación consistente.

---

## 9. Schema version

Agregar:

```json
"schema_version": 1
```

El objetivo es permitir migraciones futuras.

No asumir que el formato de `case.json` nunca cambiará.

---

## 10. CaseContext

Adaptar `CaseContext` a la estructura definitiva.

Debe poder exponer como mínimo:

```text
case_number
case_root
identification_dir
acquisition_dir
analysis_dir
results_dir
report_dir
case_json_path
source_disk_snapshot
source_disk_revalidated
destination_volume_info
status
```

Eliminar o deprecar referencias principales a:

```text
evidence_directory
logs_directory
metadata_directory
hashes_directory
reports_directory
```

si representan carpetas raíz antiguas.

Si la lógica existente requiere esas rutas para Sprint 03:

reubicarlas conceptualmente dentro de:

`ADQUISICION`

por ejemplo:

```text
acquisition_logs_dir
acquisition_hashes_dir
acquisition_metadata_dir
```

---

## 11. Compatibilidad con Sprint 03

El resultado de Sprint 02.5 debe permitir que Sprint 03 guarde:

```text
<CASO>\ADQUISICION\<CASO>.E01
```

y, si necesita subcarpetas:

```text
<CASO>\ADQUISICION\logs\
<CASO>\ADQUISICION\hashes\
<CASO>\ADQUISICION\metadata\
```

No modificar Sprint 03 todavía salvo referencias inevitables en modelos compartidos.

---

## 12. Carpeta IDENTIFICACION

Debe crearse vacía en este sprint.

No implementar análisis de imágenes todavía.

No OCR.

No visión.

No transcripción.

Solo preparar la ubicación definitiva.

---

## 13. Carpeta ANALISIS

Debe crearse vacía en este sprint.

No integrar AXIOM.

No generar XLS/XLSX.

Solo preparar la ubicación definitiva.

---

## 14. Carpeta RESULTADOS

Debe crearse vacía en este sprint.

No crear Portable Case.

No comprimir.

No calcular hash del portable.

Solo preparar la ubicación definitiva.

---

## 15. Carpeta REPORTE

Debe crearse vacía en este sprint.

No generar Word.

No analizar informes históricos.

Solo preparar la ubicación definitiva.

---

## 16. Caso existente

Mantener la política de Sprint 02:

si la carpeta del caso ya existe:

ABORTAR.

No sobrescribir.

No intentar migrar automáticamente casos existentes reales.

La migración de casos históricos será un sprint futuro diferente.

---

## 17. Estado del caso

El estado final de Sprint 02.5 debe seguir siendo:

`READY`

si todas las validaciones previas siguen correctas.

`case.json` debe reflejar ese estado.

---

## 18. AppState

Mantener `AppState`.

No cambiar estados válidos de Sprint 01/02 salvo que sea necesario.

Si existe estado `CREATING_CASE`, debe seguir funcionando.

No introducir estados futuros de AXIOM o reporte todavía salvo que ya estén definidos de forma no intrusiva.

---

## 19. Rutas relativas vs absolutas

Internamente se pueden conservar rutas absolutas para ejecución.

En `case.json`, preferir:

- rutas relativas al `case_root` para artefactos internos;
- rutas absolutas solo donde sean necesarias.

Ejemplo preferido:

```json
"paths": {
  "identificacion": "IDENTIFICACION",
  "adquisicion": "ADQUISICION",
  "analisis": "ANALISIS",
  "resultados": "RESULTADOS",
  "reporte": "REPORTE"
}
```

y:

```json
"case_root": "D:\\EVIDENCIAS\\CASO-2026-001"
```

Esto facilita mover el caso completo en el futuro.

---

## 20. No romper trazabilidad

La información ya recopilada por Sprint 01 y Sprint 02 debe conservarse.

Como mínimo:

- disk number;
- PhysicalDrive;
- modelo;
- serial;
- tamaño;
- bus;
- read-only;
- system;
- boot;
- filesystem destino;
- espacio total;
- espacio libre.

Debe quedar disponible tanto en `CaseContext` como en `case.json`.

---

## 21. No duplicar fuentes de verdad

Evitar mantener el mismo valor con nombres distintos en múltiples lugares sin necesidad.

Definir claramente:

- modelo en memoria: `CaseContext`;
- persistencia: `case.json`.

No crear un segundo JSON maestro paralelo.

---

## 22. Tests existentes

Ejecutar todos los tests existentes antes de modificar.

Después de la migración:

todos los tests funcionalmente válidos deben continuar pasando.

Los tests que verificaban carpetas antiguas deben actualizarse a la nueva estructura.

No borrar tests solo porque fallen después de la migración.

Actualizar su expectativa.

---

## 23. Tests nuevos obligatorios

Agregar pruebas para:

### Estructura exacta
Verificar:

```text
IDENTIFICACION
ADQUISICION
ANALISIS
RESULTADOS
REPORTE
case.json
```

### No crear estructura antigua
Verificar que no se creen como carpetas principales:

```text
evidence
logs
metadata
hashes
reports
```

### case.json válido
Debe parsear correctamente.

### schema_version
Debe ser:

```text
1
```

### case_number
Debe coincidir con entrada.

### source
Debe reflejar snapshot real simulado.

### destination
Debe reflejar destino simulado.

### estados de fases
Inicialmente:

```text
identification: PENDING
acquisition: PENDING
analysis: PENDING
results: PENDING
report: PENDING
```

### status global
Al final:

```text
READY
```

### caso existente
Debe seguir bloqueando.

### error durante escritura de case.json
No dejar archivo corrupto final.

### rutas internas
Deben resolver correctamente.

---

## 24. Actualización de tests de Sprint 02

Cualquier test que espere:

```text
evidence
logs
metadata
hashes
reports
```

debe cambiarse para esperar la nueva arquitectura.

No cambiar tests de seguridad.

---

## 25. Documentación

Actualizar documentación interna relevante para indicar que la estructura definitiva es:

```text
IDENTIFICACION
ADQUISICION
ANALISIS
RESULTADOS
REPORTE
```

Eliminar documentación que presente la estructura antigua como vigente.

No borrar historial técnico si está documentado como antiguo.

---

## 26. Búsqueda de referencias antiguas

Antes de terminar:

buscar en todo el proyecto referencias a:

```text
evidence
reports
portable_case
metadata
hashes
logs
```

Distinguir:

- referencias legítimas como nombres conceptuales;
- rutas antiguas incompatibles.

Corregir únicamente las rutas que contradigan la estructura oficial.

---

## 27. No realizar todavía

Prohibido en Sprint 02.5:

- ejecutar `ewfacquire`;
- crear E01;
- ejecutar `ewfverify`;
- integrar AXIOM;
- analizar fotografías;
- OCR;
- generar XLSX;
- crear Portable Case;
- comprimir resultados;
- generar Word;
- integrar Ollama.

---

## 28. Definición de terminado

Sprint 02.5 se considera COMPLETO cuando:

- [ ] se leyó el nuevo `PROMPT_MAESTRO.md`;
- [ ] todos los tests previos fueron ejecutados antes de modificar;
- [ ] estructura antigua fue reemplazada;
- [ ] `IDENTIFICACION` se crea;
- [ ] `ADQUISICION` se crea;
- [ ] `ANALISIS` se crea;
- [ ] `RESULTADOS` se crea;
- [ ] `REPORTE` se crea;
- [ ] `case.json` se crea;
- [ ] `schema_version=1`;
- [ ] `CaseContext` fue adaptado;
- [ ] datos del source se conservan;
- [ ] datos del destination se conservan;
- [ ] estado final sigue siendo READY;
- [ ] caso existente sigue bloqueándose;
- [ ] no se crean carpetas principales antiguas;
- [ ] tests antiguos válidos pasan;
- [ ] tests nuevos pasan;
- [ ] no se ejecutó adquisición;
- [ ] no se integró AXIOM;
- [ ] no se generó reporte.

---

## 29. Reporte final de TRAE

Al terminar:

```text
SPRINT 02.5: COMPLETADO / INCOMPLETO

TESTS ANTES DE MIGRACIÓN:
...

ARCHIVOS CREADOS:
...

ARCHIVOS MODIFICADOS:
...

ESTRUCTURA ANTERIOR:
...

ESTRUCTURA NUEVA:
...

CAMBIOS EN CaseContext:
...

case.json:
...

PRUEBAS:
...

RESULTADOS:
...

REGRESIONES:
...

RIESGOS / LIMITACIONES:
...

ESTADO:
READY / NO READY PARA SPRINT 03

SIGUIENTE SPRINT:
Sprint 03 — Integración controlada de ewfacquire usando ADQUISICION.
```

Si queda incompleto, indicar exactamente qué criterio falta.

---

## 30. Instrucción de inicio

TRAE:

1. lee `PROMPT_MAESTRO.md`;
2. lee `SPRINT_02_5.md`;
3. ejecuta toda la suite existente;
4. inspecciona `CaseContext`, `creator.py`, `main.py` y tests de Sprint 02;
5. migra la estructura del caso;
6. implementa `case.json`;
7. adapta rutas;
8. actualiza tests afectados;
9. agrega tests nuevos;
10. busca referencias antiguas en todo el repositorio;
11. corrige hasta que toda la suite pase;
12. NO ejecutes `ewfacquire`;
13. termina en estado READY para Sprint 03.

Comienza ahora.
