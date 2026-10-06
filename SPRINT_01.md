# SPRINT_01.md

# Sprint 01 — Detección y selección segura del disco de evidencia

## 1. Objetivo

Construir la primera unidad funcional del Agente Forense Local para Windows.

Este sprint debe resolver únicamente:

- detección de discos físicos;
- clasificación segura;
- selección explícita del disco por el operador;
- validación de que el candidato está en solo lectura;
- bloqueo de discos de sistema/arranque.

No realizar adquisición real.

No integrar `ewfacquire`.

No integrar Ollama.

---

## 2. Regla previa obligatoria

Antes de comenzar:

1. leer completamente `G:\AgenteForense\PROMPT_MAESTRO.md`;
2. inspeccionar el proyecto actual;
3. respetar todas las reglas permanentes.

---

## 3. Resultado esperado

Al ejecutar la aplicación, el operador debe visualizar los discos físicos detectados.

Ejemplo conceptual:

```text
============================================================
AGENTE FORENSE
MÓDULO DE DETECCIÓN DE EVIDENCIA
============================================================

Discos detectados:

[0]
PhysicalDrive : \\.\PhysicalDrive0
Modelo        : Samsung SSD
Serial        : XXXXX
Tamaño        : 1 TB
Bus           : NVMe
ReadOnly      : NO
System        : SI
Boot          : SI

Estado:
BLOQUEADO - DISCO DEL SISTEMA


[2]
PhysicalDrive : \\.\PhysicalDrive2
Modelo        : WDC WD20EZAZ
Serial        : WD-XXXXXX
Tamaño        : 2 TB
Bus           : USB
ReadOnly      : SI
System        : NO
Boot          : NO

Estado:
CANDIDATO FORENSE
```

El operador debe poder seleccionar un candidato válido.

Ejemplo:

```text
Seleccione el disco de evidencia:
> 2
```

Luego mostrar nuevamente:

```text
DISPOSITIVO SELECCIONADO

PhysicalDrive : \\.\PhysicalDrive2
Modelo        : WDC WD20EZAZ
Serial        : WD-XXXXXX
Tamaño        : 2 TB
Bus           : USB
ReadOnly      : TRUE
System        : FALSE
Boot          : FALSE
```

Finalmente preguntar:

```text
¿Trabajar con este disco?

Escriba SI para confirmar:
>
```

En este sprint, después de confirmar, NO iniciar adquisición.

Mostrar:

```text
DISPOSITIVO ACEPTADO

El disco ha sido seleccionado y validado para el siguiente módulo.

No se ha realizado ninguna adquisición.
```

---

## 4. Fuentes de datos

Utilizar mecanismos nativos de Windows.

Se permite utilizar PowerShell `Get-Disk` invocado de forma controlada.

Obtener como mínimo:

- Number
- FriendlyName
- SerialNumber
- Size
- BusType
- IsReadOnly
- IsSystem
- IsBoot
- OperationalStatus
- HealthStatus

Convertir el número de disco a:

`\\.\PhysicalDriveN`

---

## 5. Clasificación obligatoria

Un disco solo será:

`CANDIDATO FORENSE`

si:

```text
IsReadOnly == True
IsSystem   == False
IsBoot     == False
```

Si `IsSystem=True`:

`BLOQUEADO - DISCO DEL SISTEMA`

Si `IsBoot=True`:

`BLOQUEADO - DISCO DE ARRANQUE`

Si `IsReadOnly=False`:

`BLOQUEADO - NO ESTÁ EN SOLO LECTURA`

Si existe una combinación de bloqueos, mostrar un mensaje claro que refleje las condiciones críticas.

---

## 6. Selección

El operador debe seleccionar por número de disco.

No permitir seleccionar un disco bloqueado.

No permitir seleccionar un número inexistente.

No usar índices artificiales si pueden confundirse con `Disk Number`.

Mostrar siempre el valor real de `Get-Disk Number`.

---

## 7. Confirmación

Después de seleccionar un candidato:

- mostrar todos sus datos;
- exigir confirmación textual exacta `SI`;
- cualquier otra entrada cancela la selección.

No adquirir nada todavía.

---

## 8. Estado en memoria

Después de confirmación válida, mantener una representación estructurada del disco seleccionado.

Debe incluir como mínimo:

- disk_number;
- physical_drive;
- friendly_name;
- serial_number;
- size_bytes;
- bus_type;
- is_read_only;
- is_system;
- is_boot;
- operational_status;
- health_status.

Diseñar esta representación para reutilizarla en Sprint 02.

Preferir un modelo explícito, por ejemplo dataclass, TypedDict, Pydantic solo si ya existe como dependencia, u otra estructura clara.

No añadir dependencias innecesarias.

---

## 9. Seguridad

En este sprint está prohibido:

- ejecutar `ewfacquire`;
- abrir el PhysicalDrive en modo escritura;
- montar;
- desmontar;
- cambiar atributos;
- ejecutar `Set-Disk`;
- ejecutar DiskPart;
- formatear;
- inicializar;
- reparar;
- escribir en el dispositivo;
- iniciar adquisición real.

Solo detección, lectura de metadata y selección.

---

## 10. Arquitectura

No colocar toda la lógica en `main.py`.

Crear módulos separados.

Estructura sugerida:

```text
src\
    main.py
    disks\
        __init__.py
        detector.py
        validator.py
        models.py
    utils\
        __init__.py
        formatting.py
```

TRAE puede ajustar nombres si mejora claridad.

---

## 11. Tests obligatorios

Crear tests sin depender de discos físicos reales.

Usar mocks/fakes para datos de discos.

Cubrir al menos:

### Caso 1
```text
IsReadOnly=True
IsSystem=False
IsBoot=False
```

Resultado:

`CANDIDATO FORENSE`

### Caso 2
```text
IsReadOnly=False
IsSystem=False
IsBoot=False
```

Resultado:

bloqueado.

### Caso 3
```text
IsReadOnly=True
IsSystem=True
IsBoot=False
```

Resultado:

bloqueado.

### Caso 4
```text
IsReadOnly=True
IsSystem=False
IsBoot=True
```

Resultado:

bloqueado.

### Caso 5
Selección de número inexistente.

Resultado:

rechazada sin excepción no controlada.

### Caso 6
Selección de disco bloqueado.

Resultado:

rechazada.

### Caso 7
Confirmación distinta de `SI`.

Resultado:

cancelada.

### Caso 8
Un único disco retornado por PowerShell en forma de objeto JSON y no array.

Resultado:

normalizado correctamente.

### Caso 9
Cero discos retornados.

Resultado:

mensaje controlado.

---

## 12. Manejo de errores

Considerar como mínimo:

- PowerShell no disponible;
- `Get-Disk` falla;
- salida JSON inválida;
- salida vacía;
- permisos insuficientes;
- datos faltantes;
- serial vacío;
- OperationalStatus con más de un valor;
- excepción inesperada.

La aplicación no debe terminar mostrando solo un traceback.

Los mensajes deben ser comprensibles.

---

## 13. Formato de tamaño

Mostrar tamaño legible:

- GB;
- TB;

pero conservar siempre `size_bytes` exacto internamente.

No redondear el valor interno.

---

## 14. Serial

No asumir que todos los dispositivos reportan serial.

Si no existe:

mostrar:

`No disponible`

pero conservar `None` o equivalente internamente.

No inventar seriales.

---

## 15. Estado visual

Diferenciar claramente:

- candidato;
- bloqueado;
- error.

No agregar colores si comprometen compatibilidad de consola.

Si se usan colores, deben degradar correctamente en terminales sin soporte.

---

## 16. Herramientas instaladas

Durante este sprint se permite inspeccionar:

`G:\AgenteForense\ew\ewftools-x64`

pero NO integrar todavía `ewfacquire`.

Puede registrarse la existencia del ejecutable para conocimiento futuro.

No ejecutar adquisición.

---

## 17. Definición de terminado

Sprint 01 se considera COMPLETO únicamente cuando:

- [ ] `PROMPT_MAESTRO.md` fue leído;
- [ ] el proyecto fue inspeccionado;
- [ ] los discos Windows se detectan;
- [ ] PhysicalDriveN se construye correctamente;
- [ ] modelo se muestra;
- [ ] serial se muestra;
- [ ] tamaño se muestra;
- [ ] BusType se muestra;
- [ ] IsReadOnly se muestra;
- [ ] IsSystem se muestra;
- [ ] IsBoot se muestra;
- [ ] candidatos se clasifican correctamente;
- [ ] discos del sistema están bloqueados;
- [ ] discos de arranque están bloqueados;
- [ ] discos no ReadOnly están bloqueados;
- [ ] operador puede seleccionar candidato;
- [ ] selección inválida se rechaza;
- [ ] confirmación `SI` funciona;
- [ ] ninguna adquisición se ejecuta;
- [ ] existen tests;
- [ ] tests pasan;
- [ ] código está separado en módulos;
- [ ] no se modificó ningún dispositivo.

---

## 18. Reporte final de TRAE

Al terminar el sprint, responder con:

```text
SPRINT 01: COMPLETADO / INCOMPLETO

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

RIESGOS / LIMITACIONES:
...

SIGUIENTE SPRINT:
Sprint 02 — Caso, destino y revalidación previa.
```

Si el sprint queda incompleto, especificar exactamente qué criterio falta.

---

## 19. Instrucción de inicio

TRAE:

1. lee `PROMPT_MAESTRO.md`;
2. inspecciona `G:\AgenteForense`;
3. inspecciona la versión de Python disponible;
4. crea la estructura mínima necesaria;
5. implementa detección;
6. implementa validación;
7. implementa selección;
8. crea tests;
9. ejecuta tests;
10. corrige hasta que pasen;
11. no avances a adquisición.

Comienza ahora.
