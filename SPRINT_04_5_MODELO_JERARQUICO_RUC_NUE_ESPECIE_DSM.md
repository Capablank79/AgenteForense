# SPRINT_04_5_MODELO_JERARQUICO_RUC_NUE_ESPECIE_DSM.md

# Sprint 04.5 — Modelo jerárquico RUC → NUE → ESPECIE → DSM

## 1. Objetivo

Migrar la arquitectura de casos nuevos al modelo oficial:

```text
RUC
└── NUE
    └── ESPECIE
        └── DSM
```

Definiciones permanentes:

```text
RUC     = identificador del caso
NUE     = evidencia
ESPECIE = objeto físico
DSM     = dispositivo de almacenamiento digital
```

Este sprint debe implementar la creación guiada del caso ANTES de cualquier adquisición y preparar la estructura que luego usarán Identificación, Adquisición, AXIOM y Reporte.

No implementar todavía OCR, visión, petitorio automático, AXIOM ni Word.

---

## 2. Regla previa obligatoria

Antes de modificar código:

1. leer `PROMPT_MAESTRO.md`;
2. confirmar que contiene la regla permanente de investigación previa;
3. revisar reportes Sprint 01–04.1;
4. ejecutar toda la suite actual y registrar baseline;
5. inspeccionar `CaseContext`, `case.json`, planner, runner, workflow y validadores;
6. localizar dependencias actuales de `case_number`;
7. localizar rutas que todavía asuman `<CASO>\ADQUISICION\<CASO>.E01`.

No empezar hasta entender completamente el impacto.

---

## 3. Identificador del caso

Para casos nuevos:

```text
RUC = CASE ID
```

La carpeta raíz será:

```text
RUC_<CLAVE_RUC>
```

No inventar algoritmo de dígito verificador ni longitud si todavía no ha sido formalmente definida por ejemplos reales.

Aplicar únicamente validación segura de filesystem:

- no vacío;
- sin `..`;
- sin ruta absoluta;
- sin UNC;
- sin caracteres inválidos de Windows;
- sin nombres reservados;
- sin separadores de ruta;
- conservar el RUC original como dato.

---

## 4. Múltiples NUE

Un RUC puede contener una o más NUE.

Ejemplo:

```text
RUC_XXXXXXXX├── NUE_777777
└── NUE_888888
```

No asumir una NUE única por caso.

---

## 5. Múltiples ESPECIES

Cada NUE puede contener una o más especies.

Numeración correlativa dentro de cada NUE:

```text
NUE_777777_ESPECIE1
NUE_777777_ESPECIE2
NUE_777777_ESPECIE3
```

---

## 6. Múltiples DSM

Cada especie puede contener uno o más DSM.

La numeración DSM se reinicia por especie:

```text
NUE_777777_ESPECIE1_DSM1
NUE_777777_ESPECIE1_DSM2

NUE_777777_ESPECIE2_DSM1
```

---

## 7. Relación entre ESPECIE y DSM

Crear enum explícito:

```text
StorageRelation
```

con:

```text
SELF_STORAGE
CONTAINED_STORAGE
```

### SELF_STORAGE

La especie es físicamente el mismo dispositivo que el DSM.

Ejemplos:

- pendrive;
- disco externo;
- SSD externo;
- tarjeta SD;
- microSD.

Modelo:

```text
NUE_777777_ESPECIE1
└── NUE_777777_ESPECIE1_DSM1
```

Persistir:

```text
same_physical_object_as_species = true
```

DSM1 se crea automáticamente.

No duplicar fotografías.

### CONTAINED_STORAGE

La especie contiene uno o más DSM distintos.

Ejemplos:

- notebook;
- computador AIO;
- desktop;
- servidor;
- DVR/NVR.

Modelo:

```text
NUE_777777_ESPECIE1
├── NUE_777777_ESPECIE1_DSM1
└── NUE_777777_ESPECIE1_DSM2
```

Persistir:

```text
same_physical_object_as_species = false
```

El operador debe indicar cuántos DSM contiene.

---

## 8. Flujo guiado previo a adquisición

El flujo debe ser:

```text
INGRESAR RUC
↓
AGREGAR NUE
↓
DEFINIR CANTIDAD DE ESPECIES
↓
POR CADA ESPECIE:
    SELF_STORAGE o CONTAINED_STORAGE
↓
SI CONTAINED_STORAGE:
    indicar cantidad DSM
↓
MOSTRAR ESTRUCTURA COMPLETA
↓
CONFIRMACIÓN HUMANA
↓
CREAR CARPETAS
↓
LISTO PARA FOTOS Y FUTURA ADQUISICIÓN
```

---

## 9. Preguntas obligatorias

### RUC

```text
Ingrese CLAVE RUC:
```

### NUE

```text
Ingrese NUE:
```

Después:

```text
¿La RUC contiene otra NUE?
SI / NO
```

### ESPECIES

Por cada NUE:

```text
¿Cuántas especies contiene esta NUE?
```

Asignar correlativamente ESPECIE1..N.

### TIPO DE RELACIÓN

Por cada especie:

```text
¿La especie es directamente un dispositivo de almacenamiento digital?

1. Sí — SELF_STORAGE
2. No — contiene uno o más DSM
```

Si SELF_STORAGE:

```text
DSM1 automático
```

Si CONTAINED_STORAGE:

```text
¿Cuántos DSM contiene esta especie?
```

Crear DSM1..N.

---

## 10. Confirmación de estructura

Antes de crear directorios, mostrar resumen completo.

Ejemplo:

```text
RUC: XXXXXXXX

NUE_777777
  ESPECIE1
    CONTAINED_STORAGE
    DSM1
    DSM2

  ESPECIE2
    SELF_STORAGE
    DSM1
```

Requerir confirmación exacta:

```text
CREAR
```

Cualquier otra entrada debe cancelar sin crear una estructura parcial.

---

## 11. Estructura raíz

```text
RUC_<RUC>\
├── case.json
├── IDENTIFICACION\
├── ADQUISICION\
├── ANALISIS\
├── RESULTADOS\
└── REPORTE\
```

---

## 12. IDENTIFICACION — CONTAINED_STORAGE

Ejemplo:

```text
IDENTIFICACION\
└── NUE_777777\
    └── NUE_777777_ESPECIE1\
        ├── ESPECIE\
        │   └── FOTOS_PENDIENTES\
        └── DSM\
            ├── NUE_777777_ESPECIE1_DSM1\
            │   └── FOTOS_PENDIENTES\
            └── NUE_777777_ESPECIE1_DSM2\
                └── FOTOS_PENDIENTES\
```

La especie tendrá exactamente 3 fotografías.

Cada DSM tendrá exactamente 3 fotografías.

---

## 13. IDENTIFICACION — SELF_STORAGE

Para un pendrive u otro objeto que sea especie y DSM a la vez:

```text
IDENTIFICACION\
└── NUE_777777\
    └── NUE_777777_ESPECIE2\
        └── FOTOS_PENDIENTES\
```

El DSM lógico:

```text
NUE_777777_ESPECIE2_DSM1
```

debe referenciar esas mismas tres fotografías.

No crear un segundo juego de imágenes.

---

## 14. Regla permanente de fotografías

```text
EXACTAMENTE 3 FOTOGRAFÍAS POR OBJETO FÍSICO IDENTIFICABLE
```

Ejemplos:

Notebook + 1 SSD:

```text
Notebook = 3
SSD = 3
Total = 6
```

Notebook + 2 DSM:

```text
Notebook = 3
DSM1 = 3
DSM2 = 3
Total = 9
```

Pendrive SELF_STORAGE:

```text
Pendrive = 3
DSM1 referencia las mismas 3
Total = 3
```

---

## 15. Fotos depositadas por el operador

El usuario podrá copiar fotografías con nombres arbitrarios:

```text
IMG_001.JPG
IMG_002.JPG
IMG_003.JPG
```

a `FOTOS_PENDIENTES`.

Sprint 04.5 NO analiza ni renombra fotos.

Eso corresponde al Sprint 05.

Implementar validación:

```text
0 fotos  -> PENDING
1-2      -> INCOMPLETE
3        -> READY
>3       -> REVIEW_REQUIRED
```

No borrar sobrantes.

---

## 16. Estructura ADQUISICION

Debe reflejar la misma jerarquía:

```text
ADQUISICION\
└── NUE_777777\
    ├── NUE_777777_ESPECIE1\
    │   ├── NUE_777777_ESPECIE1_DSM1\
    │   └── NUE_777777_ESPECIE1_DSM2\
    └── NUE_777777_ESPECIE2\
        └── NUE_777777_ESPECIE2_DSM1\
```

---

## 17. Nombre oficial de imagen E01

Regla permanente:

```text
NUE_<NUE>_ESPECIE<n>_DSM<m>.E01
```

Ejemplo:

```text
NUE_777777_ESPECIE1_DSM1.E01
```

El RUC identifica el caso.

El DSM identifica la imagen forense.

---

## 18. Futuro contenido de cada carpeta DSM

Cuando corresponda adquirir:

```text
NUE_777777_ESPECIE1_DSM1\
├── NUE_777777_ESPECIE1_DSM1.E01
├── logs\
├── hashes\
└── metadata\
```

Sprint 04.5 prepara estas rutas, pero NO ejecuta adquisición real.

---

## 19. Selección lógica antes del PhysicalDrive

La adquisición futura debe comenzar seleccionando primero:

```text
¿QUÉ DSM SE VA A ADQUIRIR?
```

Ejemplo:

```text
1. NUE_777777_ESPECIE1_DSM1
2. NUE_777777_ESPECIE1_DSM2
3. NUE_777777_ESPECIE2_DSM1
```

Solo después se vincula el DSM lógico al `PhysicalDrive`.

No permitir adquisición de un PhysicalDrive sin DSM asignado.

---

## 20. Modelo ESPECIE

Debe poder representar:

```text
label
nue
species_number
storage_relation
type
brand
model
serial
color
description
photos
identification_status
storage_devices
```

En Sprint 04.5 los campos visuales deben permanecer `null` o `PENDING`.

No inferir información.

---

## 21. Modelo DSM

Debe poder representar:

```text
label
nue
species_label
dsm_number
same_physical_object_as_species
photo_reference
physical_drive
friendly_name
model
serial
size_bytes
bus_type
e01_path
acquisition_status
verification_status
```

No inventar campos todavía desconocidos.

---

## 22. case.json schema v2

La nueva jerarquía requiere:

```text
schema_version = 2
```

para casos nuevos.

Ejemplo conceptual:

```json
{
  "schema_version": 2,
  "ruc": "XXXXXXXX",
  "case_id": "RUC_XXXXXXXX",
  "nues": [
    {
      "nue": "777777",
      "species": [
        {
          "species_number": 1,
          "label": "NUE_777777_ESPECIE1",
          "storage_relation": "CONTAINED_STORAGE",
          "photos": {
            "expected": 3,
            "status": "PENDING"
          },
          "storage_devices": [
            {
              "dsm_number": 1,
              "label": "NUE_777777_ESPECIE1_DSM1",
              "same_physical_object_as_species": false,
              "photos": {
                "expected": 3,
                "status": "PENDING"
              },
              "acquisition": {
                "status": "PENDING"
              }
            }
          ]
        }
      ]
    }
  ]
}
```

---

## 23. SELF_STORAGE en case.json

Ejemplo:

```json
{
  "storage_relation": "SELF_STORAGE",
  "photos": {
    "expected": 3
  },
  "storage_devices": [
    {
      "dsm_number": 1,
      "same_physical_object_as_species": true,
      "photos_reference": "SPECIES_PHOTOS"
    }
  ]
}
```

---

## 24. Compatibilidad legacy

`TEST-ACQ-001` debe permanecer intacto.

No:

- migrarlo automáticamente;
- renombrar su E01;
- mover carpetas;
- inventarle RUC;
- inventarle NUE.

El schema actual debe seguir siendo legible como legacy/schema v1.

Crear adaptador explícito si es necesario:

```text
schema v1 -> legacy
schema v2 -> hierarchical
```

---

## 25. Persistencia

Mantener escritura atómica:

- temporal;
- flush;
- fsync;
- `os.replace`;
- limpieza segura.

---

## 26. Petitorio

Sprint 04.5 NO debe implementar lectura automática de petitorios.

La arquitectura sí debe preparar un modelo intermedio:

```text
CaseStructureDraft
```

El modo manual debe producir ese draft.

En un sprint posterior:

```text
PetitorioParser -> CaseStructureDraft
```

Así manual y petitorio terminarán en el mismo modelo.

Nunca crear automáticamente estructura definitiva desde OCR sin revisión humana.

---

## 27. Integración con adquisición existente

Adaptar únicamente la resolución de target para que el futuro comando de adquisición use:

```text
...\ADQUISICION\
NUE_x\
NUE_x_ESPECIEy\
NUE_x_ESPECIEy_DSMz\
NUE_x_ESPECIEy_DSMz
```

El resultado esperado será:

```text
NUE_x_ESPECIEy_DSMz.E01
```

No ejecutar `ewfacquire`.

---

## 28. Seguridad heredada

La nueva arquitectura no puede romper:

- `IsReadOnly=True`;
- bloqueo System/Boot;
- origen y destino distintos;
- revalidación de origen;
- single-E01;
- `shell=False`;
- verificación EWF;
- persistencia atómica;
- auditoría.

---

## 29. Tests obligatorios

Mantener toda la suite existente y agregar, como mínimo:

1. RUC seguro;
2. RUC vacío;
3. path traversal en RUC;
4. múltiples NUE;
5. NUE duplicada;
6. múltiples ESPECIES;
7. numeración correlativa;
8. SELF_STORAGE crea DSM1;
9. SELF_STORAGE `same_physical_object=true`;
10. CONTAINED_STORAGE un DSM;
11. CONTAINED_STORAGE varios DSM;
12. DSM reinicia numeración por especie;
13. estructura IDENTIFICACION contained;
14. estructura IDENTIFICACION self;
15. estructura ADQUISICION;
16. `expected_photos=3`;
17. 0 fotos PENDING;
18. 1-2 INCOMPLETE;
19. 3 READY;
20. >3 REVIEW_REQUIRED;
21. no borrar sobrantes;
22. target E01 usa DSM label;
23. DSM requerido antes de adquirir;
24. schema v2;
25. persistencia atómica;
26. bloqueo sobre RUC existente;
27. schema v1 legible;
28. TEST-ACQ-001 intacto;
29. no E01 generado;
30. no `ewfacquire`;
31. no `ewfverify`;
32. no PhysicalDrive real;
33. manual input produce `CaseStructureDraft`.

---

## 30. Prueba funcional simulada

Crear únicamente caso temporal/mock:

```text
RUC: XXXXXXXX
NUE: 777777

ESPECIE1:
CONTAINED_STORAGE
DSM count: 2

ESPECIE2:
SELF_STORAGE
```

Debe producir la jerarquía exacta esperada en IDENTIFICACION y ADQUISICION.

No crear ningún E01.

---

## 31. Fuera de alcance

No implementar:

- OCR;
- visión;
- renombrado de fotos;
- descripción automática;
- parser de petitorio;
- AXIOM;
- XLS/XLSX;
- Portable Case;
- ZIP;
- Word;
- Ollama.

---

## 32. Definición de terminado

Sprint 04.5 queda COMPLETO cuando:

- RUC es Case ID en schema v2;
- múltiples NUE soportadas;
- múltiples especies soportadas;
- múltiples DSM soportados;
- SELF_STORAGE implementado;
- CONTAINED_STORAGE implementado;
- estructura IDENTIFICACION creada;
- estructura ADQUISICION creada;
- regla de 3 fotos persistida;
- SELF_STORAGE no duplica fotos;
- rutas E01 derivadas de DSM;
- `case.json` schema v2;
- legacy v1 preservado;
- `TEST-ACQ-001` intacto;
- ninguna operación forense real ejecutada;
- todos los tests pasan.

---

## 33. Reporte final de TRAE

Entregar:

```text
SPRINT 04.5: COMPLETADO / INCOMPLETO

BASELINE:
...

ARQUITECTURA:
RUC -> NUE -> ESPECIE -> DSM

SCHEMA:
...

ARCHIVOS CREADOS:
...

ARCHIVOS MODIFICADOS:
...

MODELOS NUEVOS:
...

FLUJO GUIADO:
...

SELF_STORAGE:
...

CONTAINED_STORAGE:
...

ESTRUCTURA IDENTIFICACION:
...

ESTRUCTURA ADQUISICION:
...

REGLA 3 FOTOS:
...

E01 TARGET:
...

LEGACY COMPATIBILITY:
...

TEST-ACQ-001:
INTACTO / ALTERADO

TESTS NUEVOS:
...

TESTS FINALES:
...

OPERACIONES FORENSES REALES:
NINGUNA

RIESGOS / LIMITACIONES:
...

ESTADO:
LISTO / NO LISTO PARA SPRINT 05
```

No iniciar Sprint 05.

---

## 34. Instrucción final para TRAE

1. lee `PROMPT_MAESTRO.md`;
2. confirma la regla permanente pre-sprint;
3. lee este Sprint 04.5 completo;
4. ejecuta baseline;
5. inspecciona dependencias existentes de `case_number`;
6. implementa schema v2 RUC/NUE/ESPECIE/DSM;
7. preserva schema v1;
8. implementa flujo guiado;
9. implementa estructura de carpetas;
10. implementa regla de 3 fotografías;
11. adapta targets futuros por DSM;
12. NO ejecutes adquisición;
13. NO ejecutes verificación;
14. NO accedas a PhysicalDrive;
15. agrega tests;
16. deja toda la suite en verde;
17. entrega reporte final;
18. NO inicies Sprint 05.

Comienza ahora.
