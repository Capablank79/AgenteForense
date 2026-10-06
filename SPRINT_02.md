# SPRINT_02.md

# Sprint 02 — Caso, destino y revalidación previa del dispositivo

## 1. Objetivo

Extender el Agente Forense Local para que, después de seleccionar y confirmar un disco válido en Sprint 01:

1. solicite y valide el número de caso;
2. solicite y valide la ruta de destino;
3. cree la estructura del caso;
4. compruebe el filesystem y espacio del destino;
5. determine que el destino no pertenece al mismo disco físico seleccionado como evidencia;
6. reconsulte el disco origen;
7. compruebe que sigue siendo exactamente el mismo dispositivo;
8. confirme que continúa cumpliendo las reglas forenses;
9. deje el sistema en estado READY para el Sprint 03.

Este sprint NO debe ejecutar todavía `ewfacquire.exe`.

No integrar Ollama.

---

## 2. Regla previa obligatoria

Antes de comenzar:

1. leer completamente `G:\AgenteForense\PROMPT_MAESTRO.md`;
2. leer este archivo `SPRINT_02.md`;
3. inspeccionar el código existente del Sprint 01;
4. ejecutar la suite existente;
5. no romper ninguna prueba anterior.

---

## 3. Flujo esperado

El flujo conceptual será:

```text
DETECTAR DISCOS
      ↓
SELECCIONAR DISCO
      ↓
CONFIRMAR "SI"
      ↓
NÚMERO DE CASO
      ↓
RUTA DESTINO
      ↓
VALIDAR CASO
      ↓
VALIDAR DESTINO
      ↓
CREAR ESTRUCTURA
      ↓
RECONSULTAR DISCO
      ↓
COMPARAR IDENTIDAD
      ↓
REVALIDAR READ-ONLY / SYSTEM / BOOT
      ↓
READY
```

---

## 4. Número de caso

Solicitar al operador:

```text
Número de caso:
>
```

Debe aceptarse un identificador como:

```text
CASO-2026-001
2026-001
FISCALIA-12345
RIT-1234-2026
```

Debe rechazarse cualquier valor que pueda provocar:

- path traversal;
- rutas absolutas;
- rutas relativas;
- caracteres inválidos para nombres Windows;
- nombres reservados;
- componentes vacíos;
- espacios únicamente;
- puntos únicamente.

Debe rechazarse, entre otros:

```text
..\..\Windows
C:\Temp
\\servidor\share
.
..
CON
PRN
AUX
NUL
COM1
LPT1
CASO/001
CASO\001
CASO:001
CASO*001
CASO?001
CASO"001
CASO<001
CASO>001
CASO|001
```

Se puede permitir:

- letras;
- números;
- guion;
- guion bajo;
- espacios internos si se consideran seguros.

Preferir una política restrictiva y predecible.

No modificar silenciosamente el identificador introducido por el operador.

Si no es válido:

rechazar y solicitar nuevamente.

---

## 5. Ruta destino

Solicitar:

```text
Ruta donde almacenar la evidencia:
>
```

Ejemplos:

```text
D:\EVIDENCIAS
E:\CASOS
F:\FORENSE
```

Validar:

- ruta Windows válida;
- unidad existente;
- destino accesible;
- permisos de escritura;
- ruta no apuntando al dispositivo origen;
- posibilidad de crear la carpeta del caso.

No formatear ni modificar la unidad destino.

No cambiar sus atributos.

---

## 6. Estructura del caso

Una vez validados número de caso y ruta:

crear:

```text
<RUTA_DESTINO>\
└── <NUMERO_CASO>\
    ├── evidence\
    ├── logs\
    ├── metadata\
    ├── hashes\
    └── reports\
```

Ejemplo:

```text
D:\EVIDENCIAS\
└── CASO-2026-001\
    ├── evidence\
    ├── logs\
    ├── metadata\
    ├── hashes\
    └── reports\
```

No crear todavía archivos E01.

La creación de estas carpetas sí forma parte de Sprint 02.

---

## 7. Caso existente

Si ya existe:

```text
D:\EVIDENCIAS\CASO-2026-001
```

NO sobrescribir silenciosamente.

NO borrar contenido existente.

NO vaciar carpetas.

Bloquear por defecto y mostrar:

```text
CASO YA EXISTENTE

La ruta del caso ya existe:

D:\EVIDENCIAS\CASO-2026-001

No se modificará el contenido existente.
```

No implementar todavía "reanudar caso" ni "continuar adquisición".

Eso será una decisión futura.

---

## 8. Información del destino

Obtener y conservar como mínimo:

- ruta raíz;
- letra de volumen;
- filesystem;
- tamaño total;
- espacio libre;
- identificador del volumen cuando sea posible;
- disco físico que contiene el volumen destino cuando pueda determinarse.

No inventar valores.

---

## 9. Filesystem destino

Para la futura imagen E01 única y grande, registrar el filesystem.

No ejecutar todavía adquisición.

Estados sugeridos:

```text
NTFS      -> APTO
ReFS      -> evaluar y registrar
exFAT     -> evaluar y registrar
FAT32     -> NO APTO PARA E01 ÚNICO GRANDE
UNKNOWN   -> BLOQUEAR O ADVERTIR SEGÚN EVIDENCIA DISPONIBLE
```

En este sprint:

- implementar la detección;
- registrar el resultado;
- bloquear FAT32 para el flujo futuro de un solo E01 si el tamaño potencial supera el límite de archivo;
- no formatear automáticamente.

Preferir una validación basada en límite real del filesystem y tamaño del origen.

---

## 10. Espacio disponible

Obtener:

```text
source_size_bytes
destination_free_bytes
```

Conservar valores exactos.

Mostrar también valores legibles.

No asumir una tasa fija de compresión.

Debido a que en Sprint 03 se utilizará E01 con compresión alta, el tamaño final puede ser menor que el RAW, pero no está garantizado.

Clasificación sugerida:

### Espacio >= tamaño RAW

```text
ESPACIO: SUFICIENTE PARA ESCENARIO SIN COMPRESIÓN
```

### Espacio < tamaño RAW

```text
ADVERTENCIA:
El espacio libre es menor que el tamaño físico del origen.

La compresión E01 podría reducir el tamaño final,
pero no existe garantía de que sea suficiente.
```

Para Sprint 02, registrar esta condición.

No iniciar adquisición.

---

## 11. Destino no puede estar en el disco origen

Esta validación es CRÍTICA.

El agente debe determinar a qué disco físico pertenece la ruta de destino.

Ejemplo:

```text
Destino:
D:\EVIDENCIAS

Volumen D:
↓
Disk Number 4
↓
\\.\PhysicalDrive4
```

Comparar con:

```text
Origen:
\\.\PhysicalDrive6
```

Si corresponden al mismo disco físico:

ABORTAR.

Mensaje:

```text
DESTINO NO VÁLIDO

La ruta de destino pertenece al mismo disco físico
seleccionado como evidencia.

Origen:
\\.\PhysicalDrive6

Destino físico:
\\.\PhysicalDrive6

No se continuará.
```

Esta regla no puede ser ignorada manualmente.

---

## 12. Snapshot inicial de identidad

Al confirmar el disco en Sprint 01 existe un `PhysicalDisk` inmutable.

Tratarlo como snapshot inicial.

Debe contener como mínimo:

```text
disk_number
physical_drive
friendly_name
serial_number
size_bytes
bus_type
is_read_only
is_system
is_boot
operational_status
health_status
```

No alterar ese snapshot.

---

## 13. Reconsulta obligatoria

Después de:

- introducir caso;
- validar destino;
- crear estructura;

pero ANTES de declarar READY:

volver a ejecutar la detección real de discos.

Buscar nuevamente el mismo `Disk Number`.

No reutilizar únicamente la información guardada previamente.

---

## 14. Comparación de identidad

Comparar snapshot inicial vs. disco reconsultado.

Campos críticos:

- disk_number;
- physical_drive;
- serial_number;
- size_bytes;
- friendly_name;
- is_read_only;
- is_system;
- is_boot.

### Serial disponible

Si el snapshot inicial contiene serial:

debe coincidir exactamente con el serial reconsultado.

Si cambia:

ABORTAR.

### Serial no disponible

Si no existe serial:

usar una política conservadora combinando:

- disk number;
- tamaño exacto;
- modelo;
- bus;
- otros identificadores disponibles.

Registrar explícitamente que el serial no estaba disponible.

No afirmar identidad criptográfica o absoluta.

---

## 15. Revalidación de seguridad

El disco reconsultado debe seguir cumpliendo:

```text
IsReadOnly == True
IsSystem   == False
IsBoot     == False
```

Si `IsReadOnly` cambia a `False`:

ABORTAR.

Si `IsSystem=True`:

ABORTAR.

Si `IsBoot=True`:

ABORTAR.

No ofrecer override.

---

## 16. Cambio de tamaño

Si:

```text
initial.size_bytes != current.size_bytes
```

ABORTAR.

Mostrar ambos valores.

---

## 17. Disco desaparecido

Si el `Disk Number` seleccionado ya no existe:

ABORTAR.

No seleccionar automáticamente otro disco.

No buscar "uno parecido" para sustituirlo.

---

## 18. Estado READY

Solo declarar:

```text
READY
```

cuando:

- caso válido;
- destino válido;
- estructura creada;
- destino no está en disco origen;
- disco original sigue presente;
- identidad coincide;
- tamaño coincide;
- ReadOnly sigue True;
- IsSystem sigue False;
- IsBoot sigue False.

Mostrar resumen:

```text
============================================================
LISTO PARA PREPARAR ADQUISICIÓN
============================================================

Caso:
CASO-2026-001

Origen:
\\.\PhysicalDrive6

Modelo:
...

Serial:
...

Tamaño:
...

Windows ReadOnly:
TRUE

Destino:
D:\EVIDENCIAS\CASO-2026-001

Filesystem destino:
NTFS

Espacio libre:
...

Estado:
READY

Todavía NO se ha ejecutado ninguna adquisición.
```

---

## 19. Modelo de datos del caso

Crear una estructura explícita para el contexto de caso.

Ejemplo conceptual:

```text
CaseContext
```

Debe poder conservar al menos:

```text
case_number
destination_root
case_directory
evidence_directory
logs_directory
metadata_directory
hashes_directory
reports_directory
source_disk_snapshot
source_disk_revalidated
destination_volume_info
status
```

No es obligatorio utilizar exactamente estos nombres.

Debe diseñarse para Sprint 03.

---

## 20. Estados

Implementar o ampliar un modelo de estado claro.

Como mínimo:

```text
INITIALIZING
DISK_SELECTED
WAITING_CASE
VALIDATING_CASE
WAITING_DESTINATION
VALIDATING_DESTINATION
CREATING_CASE
REVALIDATING_SOURCE
READY
FAILED
ABORTED
```

Los estados deben ser deterministas.

No usar strings dispersos si puede centralizarse con Enum u otra estructura apropiada.

---

## 21. Logging de Sprint 02

Todavía no es necesario implementar el audit log forense definitivo si la arquitectura lo pospone.

Pero registrar errores de aplicación de manera controlada.

Si ya existe infraestructura de logging, reutilizarla.

No generar logs dentro del dispositivo origen.

---

## 22. Tests obligatorios

Mantener los 23 tests del Sprint 01.

Agregar pruebas para Sprint 02.

Cubrir al menos:

### Caso válido
Número de caso válido.

Resultado:
aceptado.

### Path traversal
```text
..\..\Windows
```

Resultado:
rechazado.

### Nombre reservado
```text
CON
```

Resultado:
rechazado.

### Carácter inválido
```text
CASO:001
```

Resultado:
rechazado.

### Destino válido
Ruta escribible simulada.

Resultado:
aceptada.

### Caso existente
Directorio del caso ya existe.

Resultado:
bloqueado.

### Creación de estructura
Verificar exactamente:

```text
evidence
logs
metadata
hashes
reports
```

### Destino en mismo disco
Origen y destino resuelven al mismo PhysicalDrive.

Resultado:
bloqueado.

### Disco desaparece
No aparece en segunda detección.

Resultado:
abortado.

### Serial cambia
Resultado:
abortado.

### Tamaño cambia
Resultado:
abortado.

### IsReadOnly cambia a False
Resultado:
abortado.

### IsSystem cambia a True
Resultado:
abortado.

### IsBoot cambia a True
Resultado:
abortado.

### Mismo dispositivo intacto
Resultado:
READY.

### Serial ausente
Verificar estrategia conservadora de identidad.

### Espacio menor al RAW
Resultado:
advertencia registrada, sin inventar compresión.

### FAT32
Detectado y evaluado según límite de tamaño de archivo.

---

## 23. Pruebas reales permitidas

Se permite:

- consultar discos;
- consultar volúmenes;
- consultar filesystem;
- consultar espacio;
- crear carpetas de prueba en un destino normal;
- borrar exclusivamente las carpetas temporales creadas por la suite de tests.

No se permite:

- ejecutar `ewfacquire`;
- leer masivamente el PhysicalDrive;
- escribir al origen;
- cambiar atributos;
- DiskPart;
- Set-Disk;
- formatear;
- iniciar adquisición.

---

## 24. No integrar aún

Fuera de alcance:

- `ewfacquire`;
- parámetros E01;
- compresión;
- tamaño de segmento;
- `ewfverify`;
- hashes de adquisición;
- metadata final;
- audit log final;
- Ollama;
- GUI.

---

## 25. Definición de terminado

Sprint 02 es COMPLETO cuando:

- [ ] Sprint 01 sigue pasando;
- [ ] número de caso se solicita;
- [ ] número de caso se valida;
- [ ] path traversal se bloquea;
- [ ] nombres Windows reservados se bloquean;
- [ ] ruta destino se solicita;
- [ ] volumen destino se identifica;
- [ ] filesystem destino se detecta;
- [ ] espacio total/libre se detecta;
- [ ] se determina el disco físico del destino;
- [ ] se bloquea destino en mismo disco que origen;
- [ ] se crea estructura del caso;
- [ ] caso existente no se sobrescribe;
- [ ] disco origen se reconsulta;
- [ ] serial se compara cuando existe;
- [ ] tamaño se compara;
- [ ] modelo/identidad se comprueba conservadoramente;
- [ ] IsReadOnly se revalida;
- [ ] IsSystem se revalida;
- [ ] IsBoot se revalida;
- [ ] cambio crítico aborta;
- [ ] estado READY funciona;
- [ ] ninguna adquisición se ejecuta;
- [ ] existen tests nuevos;
- [ ] todos los tests pasan.

---

## 26. Reporte final de TRAE

Al terminar:

```text
SPRINT 02: COMPLETADO / INCOMPLETO

ARCHIVOS CREADOS:
...

ARCHIVOS MODIFICADOS:
...

FUNCIONALIDADES:
...

PRUEBAS:
...

RESULTADOS:
...

VALIDACIONES DE SEGURIDAD:
...

RIESGOS / LIMITACIONES:
...

SIGUIENTE SPRINT:
Sprint 03 — Integración controlada de ewfacquire y preparación de E01.
```

Si queda incompleto, indicar exactamente qué criterio falta.

---

## 27. Instrucción de inicio

TRAE:

1. lee `PROMPT_MAESTRO.md`;
2. lee `SPRINT_02.md`;
3. ejecuta todos los tests existentes;
4. inspecciona la arquitectura del Sprint 01;
5. implementa número de caso;
6. implementa validación de destino;
7. implementa identificación del disco físico destino;
8. implementa estructura del caso;
9. implementa reconsulta del origen;
10. implementa comparación de identidad;
11. implementa revalidaciones;
12. agrega tests;
13. corrige hasta que toda la suite pase;
14. termina en estado READY;
15. NO ejecutes `ewfacquire`.

Comienza ahora.
