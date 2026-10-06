# SPRINT_05A_INTEGRACION_FLUJO_NUEVA_ADQUISICION.md

# Sprint 05A — Integración del flujo guiado de caso con “Nueva Adquisición”

## 1. Objetivo

Integrar en un único flujo operativo la creación de la estructura lógica del caso y la preparación de una nueva adquisición.

Desde la perspectiva del operador, el punto de entrada debe ser:

```text
NUEVA ADQUISICIÓN
```

y no una secuencia manual separada de:

```text
crear caso
crear identificación
crear adquisición
```

El flujo debe solicitar los datos estructurales necesarios:

```text
RUC
→ NUE
→ ESPECIE
→ relación SELF_STORAGE / CONTAINED_STORAGE
→ DSM
```

y, a partir de esas respuestas:

1. construir o actualizar el caso Schema v2;
2. crear automáticamente la estructura correspondiente en `IDENTIFICACION`;
3. crear automáticamente la estructura correspondiente en `ADQUISICION`;
4. informar al operador la ruta exacta donde debe depositar las 3 fotografías;
5. permitir seleccionar el DSM que se desea adquirir;
6. continuar después con el flujo forense de selección y validación del `PhysicalDrive`.

Este sprint es de integración de flujo y UX. No implementa un nuevo motor de visión y no ejecutará una adquisición real durante desarrollo/pruebas.

## 2. Regla permanente obligatoria

Antes de modificar código, TRAE debe leer:

```text
G:\AgenteForense\PROMPT_MAESTRO.md
G:\AgenteForense\REGLA_PERMANENTE_PRE_SPRINT.md
```

Antes de implementar:
- ejecutar la suite completa y registrar baseline real;
- revisar reportes Sprint 04.5 y Sprint 05;
- inspeccionar `guided.py`, `creator.py`, `hierarchy.py`, `case.py`, el entrypoint real y el workflow vigente de adquisición;
- localizar cómo se seleccionan hoy el caso, DSM y `PhysicalDrive`;
- comprobar que la integración no debilite ninguna validación forense.

No inventar APIs, funciones, comandos o estados que no correspondan con el código real.

## 3. Baseline

Baseline esperado:

```text
195 passed, 4 subtests passed
```

Si la suite real contiene más pruebas legítimas, registrar el valor real. No aceptar regresiones.

## 4. Jerarquía obligatoria

```text
RUC
└── NUE
    └── ESPECIE
        └── DSM
```

Definiciones:

```text
RUC     = número de caso
NUE     = evidencia
ESPECIE = objeto físico
DSM     = dispositivo de almacenamiento digital
```

No cambiar este modelo.

## 5. Punto de entrada

```text
NUEVA ADQUISICIÓN
        ↓
RUC
        ↓
NUE
        ↓
ESPECIES
        ↓
SELF_STORAGE / CONTAINED_STORAGE
        ↓
DSM
        ↓
RESUMEN
        ↓
CONFIRMACIÓN
        ↓
CREAR / ACTUALIZAR ESTRUCTURA
        ↓
MOSTRAR RUTAS DE FOTOS
        ↓
SELECCIONAR DSM A ADQUIRIR
        ↓
SELECCIONAR PhysicalDrive
        ↓
VALIDACIONES FORENSES EXISTENTES
        ↓
ADQUISICIÓN
```

En este sprint la última etapa se prueba solo con mocks. No ejecutar `ewfacquire` real.

## 6. Entrada RUC

Preguntar:

```text
Ingrese CLAVE RUC:
```

El identificador lógico será:

```text
RUC_<CLAVE_RUC>
```

Mantener la validación segura de filesystem ya implementada. No inventar validación jurídica/formal adicional del RUC.

## 7. RUC nuevo versus existente

Si el RUC no existe:
- crear un `CaseStructureDraft`;
- continuar con NUE → ESPECIES → DSM.

Si el RUC ya existe:
- no sobrescribir;
- cargar `case.json`;
- si es Schema v2, permitir integrar una nueva adquisición sobre la jerarquía existente;
- no duplicar RUC/NUE/ESPECIE/DSM;
- no convertir automáticamente Schema v1 a Schema v2.

Si existe inconsistencia:

```text
CASE_STRUCTURE_CONFLICT
```

y detener la modificación.

## 8. Ingreso NUE

Preguntar:

```text
Ingrese NUE:
```

El sistema construye:

```text
NUE_<NUE>
```

Debe soportar múltiples NUE por RUC.

Después de completar una NUE:

```text
¿La RUC contiene otra NUE?
SI / NO
```

No permitir NUE duplicada dentro del mismo RUC.

## 9. Ingreso de ESPECIES

Por cada NUE:

```text
¿Cuántas especies contiene NUE_<NUE>?
```

Asignar correlativamente:

```text
NUE_<NUE>_ESPECIE1
NUE_<NUE>_ESPECIE2
...
```

El operador no escribe manualmente la etiqueta completa.

## 10. Relación física

Por cada especie:

```text
¿Esta especie es directamente un dispositivo de almacenamiento digital?

1. Sí — SELF_STORAGE
2. No — contiene uno o más DSM
```

## 11. SELF_STORAGE

Ejemplos: pendrive, HDD externo, SSD externo, SD, microSD.

Crear automáticamente:

```text
NUE_<NUE>_ESPECIE<n>
NUE_<NUE>_ESPECIE<n>_DSM1
```

Persistir:

```text
storage_relation = SELF_STORAGE
same_physical_object_as_species = true
photos_reference = SPECIES_PHOTOS
```

No duplicar fotografías.

## 12. CONTAINED_STORAGE

Preguntar:

```text
¿Cuántos DSM contiene NUE_<NUE>_ESPECIE<n>?
```

Crear:

```text
NUE_<NUE>_ESPECIE<n>_DSM1
...
NUE_<NUE>_ESPECIE<n>_DSM<m>
```

Persistir:

```text
storage_relation = CONTAINED_STORAGE
same_physical_object_as_species = false
```

## 13. Resumen previo

Antes de tocar filesystem, mostrar la estructura propuesta y reutilizar la confirmación segura ya implementada en Sprint 04.5.

No crear estructura parcial antes de confirmar.

## 14. Estructura oficial

```text
RUC_<RUC>\
├── case.json
├── IDENTIFICACION\
├── ADQUISICION\
├── ANALISIS\
├── RESULTADOS\
└── REPORTE\
```

## 15. IDENTIFICACION — SELF_STORAGE

```text
IDENTIFICACION\
└── NUE_<NUE>\
    └── NUE_<NUE>_ESPECIE<n>\
        └── FOTOS_PENDIENTES\
```

El operador coloca aquí exactamente 3 fotografías.

Esta carpeta representa físicamente tanto la ESPECIE como DSM1.

No crear una segunda carpeta de fotos para DSM1.

## 16. IDENTIFICACION — CONTAINED_STORAGE

```text
IDENTIFICACION\
└── NUE_<NUE>\
    └── NUE_<NUE>_ESPECIE<n>\
        ├── ESPECIE\
        │   └── FOTOS_PENDIENTES\
        └── DSM\
            ├── NUE_<NUE>_ESPECIE<n>_DSM1\
            │   └── FOTOS_PENDIENTES\
            └── NUE_<NUE>_ESPECIE<n>_DSM2\
                └── FOTOS_PENDIENTES\
```

Cada objeto físico recibe exactamente 3 fotografías.

## 17. ADQUISICION

Crear simultáneamente:

```text
ADQUISICION\
└── NUE_<NUE>\
    └── NUE_<NUE>_ESPECIE<n>\
        └── NUE_<NUE>_ESPECIE<n>_DSM1\
```

Para múltiples DSM, crear una carpeta por DSM.

No crear todavía E01 al construir la estructura.

## 18. Mostrar ruta exacta de las fotos

Para SELF_STORAGE, mostrar al operador:

```text
Coloque exactamente 3 fotografías del dispositivo en:

<RUTA_CASO>\IDENTIFICACION\NUE_<NUE>\NUE_<NUE>_ESPECIE<n>\FOTOS_PENDIENTES
```

Para CONTAINED_STORAGE, mostrar una ruta por objeto físico:

```text
ESPECIE:
...\NUE_<NUE>_ESPECIE<n>\ESPECIE\FOTOS_PENDIENTES

DSM1:
...\DSM\NUE_<NUE>_ESPECIE<n>_DSM1\FOTOS_PENDIENTES
```

No obligar al operador a deducir rutas.

## 19. Fotografías

El operador NO debe renombrarlas manualmente.

Puede copiar:

```text
IMG_001.JPG
IMG_002.JPG
IMG_003.JPG
```

El análisis posterior será responsable del renombrado.

## 20. Las fotos no son condición forense de adquisición

La falta de fotografías afecta:

```text
identification.status
```

pero no debe convertirse en una condición técnica artificial para `ewfacquire`.

Las reglas críticas de adquisición siguen siendo:

```text
IsReadOnly = True
IsSystem   = False
IsBoot     = False
origen físico != destino físico
revalidación
confirmaciones
```

Si faltan fotos, informar:

```text
IDENTIFICATION_PHOTOS_PENDING
```

sin debilitar ni reemplazar las validaciones de adquisición.

## 21. Selección de DSM

Después de crear la estructura, mostrar DSM disponibles:

```text
Seleccione DSM a adquirir:

1. NUE_777777_ESPECIE1_DSM1
2. NUE_777777_ESPECIE1_DSM2
3. NUE_777777_ESPECIE2_DSM1
```

En Schema v2 no se permite preparar adquisición sin DSM seleccionado.

## 22. Selección de PhysicalDrive

Solo después del DSM:

```text
detectar discos
→ mostrar candidatos
→ seleccionar PhysicalDrive
```

Mantener:

```text
IsReadOnly = True
IsSystem = False
IsBoot = False
```

Regla:

```text
SIN READ-ONLY = NO HAY ADQUISICIÓN
```

Sin bypass.

## 23. Vinculación DSM ↔ PhysicalDrive

Persistir la asociación de planificación:

```text
NUE_777777_ESPECIE1_DSM1
        ↕
\\.\PhysicalDriveN
```

`PhysicalDriveN` no reemplaza el identificador lógico DSM.

## 24. Target E01

Schema v2:

```text
NUE_<NUE>_ESPECIE<n>_DSM<m>.E01
```

Ruta:

```text
ADQUISICION\
NUE_<NUE>\
NUE_<NUE>_ESPECIE<n>\
NUE_<NUE>_ESPECIE<n>_DSM<m>\
NUE_<NUE>_ESPECIE<n>_DSM<m>.E01
```

Schema v1 conserva comportamiento legacy.

## 25. Caso existente

Si RUC Schema v2 ya existe:
- permitir agregar una NUE nueva sin reescribir las existentes;
- permitir agregar una nueva especie a una NUE existente usando el siguiente índice válido;
- preservar todos los campos previos;
- si hay inconsistencia de numeración, usar:

```text
STRUCTURE_REVIEW_REQUIRED
```

y no adivinar.

## 26. Legacy

No migrar automáticamente Schema v1.

`TEST-ACQ-001` debe permanecer intacto.

## 27. Persistencia

Mantener persistencia atómica:

```text
temporary file
flush
fsync
os.replace
```

Preservar campos desconocidos existentes.

## 28. Auditoría

Registrar, según el mecanismo real existente:

```text
new_acquisition_started
ruc_entered
existing_case_loaded
nue_added
species_added
dsm_added
structure_previewed
structure_confirmed
directories_created
photo_destination_presented
dsm_selected
physical_drive_selected
acquisition_plan_prepared
```

No inventar datos.

## 29. Prueba funcional principal

Simular con un pendrive:

```text
NUEVA ADQUISICIÓN
RUC = <laboratorio>
NUE = <laboratorio>
Cantidad especies = 1
SELF_STORAGE
DSM1 automático
```

Debe crear:

```text
RUC_<RUC>\
├── case.json
├── IDENTIFICACION\
│   └── NUE_<NUE>\
│       └── NUE_<NUE>_ESPECIE1\
│           └── FOTOS_PENDIENTES\
├── ADQUISICION\
│   └── NUE_<NUE>\
│       └── NUE_<NUE>_ESPECIE1\
│           └── NUE_<NUE>_ESPECIE1_DSM1\
├── ANALISIS\
├── RESULTADOS\
└── REPORTE\
```

Y mostrar explícitamente la ruta donde copiar las 3 fotos.

## 30. No implementar visión

Sprint 05 permanece:

```text
IMPLEMENTATION_COMPLETE_VISION_BLOCKED
```

Este sprint no instala modelos, no descarga VLM, no ejecuta OCR inexistente y no inventa análisis.

## 31. No ejecutar operaciones forenses reales

Durante Sprint 05A:

- NO ejecutar `ewfacquire`;
- NO ejecutar `ewfverify`;
- NO abrir `PhysicalDrive` real;
- NO crear E01 real;
- NO modificar evidencia;
- NO formatear destinos.

Usar mocks hasta el punto de adquisición preparada.

## 32. Tests obligatorios

Mantener toda la suite existente y agregar como mínimo:

1. entrada Nueva Adquisición;
2. RUC nuevo;
3. RUC Schema v2 existente;
4. no overwrite;
5. agregar NUE;
6. NUE duplicada;
7. múltiples NUE;
8. múltiples especies;
9. SELF_STORAGE crea DSM1;
10. CONTAINED_STORAGE crea N DSM;
11. estructura IDENTIFICACION self;
12. estructura IDENTIFICACION contained;
13. estructura ADQUISICION;
14. ruta exacta de fotos self;
15. rutas de fotos contained;
16. no exigir renombrado manual;
17. fotos faltantes no alteran validación forense;
18. fotos faltantes → IDENTIFICATION_PHOTOS_PENDING;
19. DSM obligatorio Schema v2;
20. DSM seleccionado antes de PhysicalDrive;
21. target E01 por DSM;
22. asociación DSM ↔ mock PhysicalDrive;
23. IsReadOnly=False bloquea;
24. IsSystem=True bloquea;
25. IsBoot=True bloquea;
26. mismo disco destino bloquea;
27. cancelación no deja árbol parcial;
28. persistencia atómica;
29. campos previos preservados;
30. schema v1 intacto;
31. TEST-ACQ-001 intacto;
32. no ewfacquire;
33. no ewfverify;
34. no acceso real a PhysicalDrive;
35. paquete de identificación Sprint 05 sin regresión.

## 33. Criterios de aceptación

Sprint 05A queda completo si:

- baseline pasa;
- Nueva Adquisición inicia el flujo jerárquico;
- RUC se solicita primero;
- NUE se solicita;
- especies se construyen;
- relación SELF/CONTAINED se obtiene;
- DSM se generan correctamente;
- case.json Schema v2 queda coherente;
- IDENTIFICACION y ADQUISICION se crean automáticamente;
- se muestran rutas exactas para fotos;
- SELF_STORAGE usa una sola carpeta de 3 fotos;
- DSM se selecciona antes de PhysicalDrive;
- target E01 deriva del DSM;
- validaciones forenses previas permanecen intactas;
- Schema v1 y TEST-ACQ-001 permanecen intactos;
- Sprint 05 sigue compatible;
- no se ejecuta operación forense real;
- suite completa queda en verde.

## 34. Fuera de alcance

No implementar:
- motor de visión;
- OCR;
- descarga de modelos;
- análisis automático de fotos;
- lectura de petitorio;
- AXIOM;
- Portable Case;
- XLS/XLSX;
- Word;
- Ollama como orquestador;
- adquisición real.

## 35. Reporte final de TRAE

```text
SPRINT 05A: COMPLETADO / INCOMPLETO

BASELINE:
...

INVESTIGACIÓN PREVIA:
...

ENTRYPOINT INSPECCIONADO:
...

FLUJO ANTERIOR:
...

FLUJO NUEVO:
...

RUC NUEVO:
...

RUC EXISTENTE:
...

NUE:
...

ESPECIES:
...

SELF_STORAGE:
...

CONTAINED_STORAGE:
...

CARPETAS IDENTIFICACION:
...

CARPETAS ADQUISICION:
...

RUTAS DE FOTOS MOSTRADAS AL OPERADOR:
...

DSM SELECCIONADO ANTES DE PHYSICALDRIVE:
SI / NO

TARGET E01:
...

VALIDACIONES FORENSES PRESERVADAS:
...

SCHEMA V1:
INTACTO / ALTERADO

TEST-ACQ-001:
INTACTO / ALTERADO

SPRINT 05:
COMPATIBLE / REGRESIÓN

TESTS NUEVOS:
...

TESTS FINALES:
...

OPERACIONES FORENSES REALES:
NINGUNA

RIESGOS / LIMITACIONES:
...

ESTADO:
LISTO / NO LISTO PARA 05.1
```

No iniciar Sprint 05.1.

## 36. Instrucción final para TRAE

1. lee `PROMPT_MAESTRO.md`;
2. lee `REGLA_PERMANENTE_PRE_SPRINT.md`;
3. revisa reportes 04.5 y 05;
4. ejecuta baseline;
5. inspecciona el entrypoint y flujo real de adquisición;
6. reutiliza `CaseStructureDraft` y la jerarquía existente;
7. integra la creación guiada dentro de Nueva Adquisición;
8. solicita RUC;
9. solicita NUE;
10. construye especies;
11. pregunta SELF_STORAGE / CONTAINED_STORAGE;
12. construye DSM;
13. muestra resumen;
14. requiere confirmación;
15. crea IDENTIFICACION y ADQUISICION;
16. muestra rutas exactas donde colocar las 3 fotografías;
17. no exige nombres manuales;
18. no convierte falta de fotos en validación forense;
19. requiere DSM antes de PhysicalDrive;
20. conserva todas las validaciones de adquisición;
21. preserva Schema v1;
22. preserva TEST-ACQ-001;
23. no implementes visión;
24. no ejecutes ewfacquire;
25. no ejecutes ewfverify;
26. no accedas a PhysicalDrive real;
27. agrega tests;
28. deja toda la suite en verde;
29. entrega reporte final;
30. NO inicies Sprint 05.1.

Comienza ahora.
