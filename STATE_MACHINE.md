# Especificación de Máquina de Estados — Agente Forense

## 1. Estados Conceptuales Reconocidos
La máquina de estados del Agente Forense reconoce un total de 17 estados conceptuales:

```text
NEW
IDENTIFICATION_PENDING
IDENTIFICATION_COMPLETED
ACQUISITION_READY
ACQUIRING
ACQUISITION_COMPLETED
ACQUISITION_VERIFIED
ANALYSIS_PENDING
PROCESSING_AXIOM
ANALYSIS_COMPLETED
RESULTS_PENDING
PORTABLE_CREATED
REPORT_PENDING
REPORT_GENERATED
COMPLETED
FAILED
ABORTED
```

## 2. Clasificación de Estados en Sprint R04

### Estados Operativos Activos
Estados completamente habilitados para transiciones operativas en el Sprint R04:
- `NEW`: Caso recién creado en el sistema.
- `IDENTIFICATION_PENDING`: Proceso de identificación asistida en curso.
- `IDENTIFICATION_COMPLETED`: Identificación de RUC, NUE, Especie y DSM finalizada.
- `ACQUISITION_READY`: Estructura validada y listo para adquisición futura.
- `FAILED`: El caso ha fallado por un error crítico no recuperable.
- `ABORTED`: Cancelación explícita realizada por un operador humano.

### Estados Reservados (Futuros Sprints)
No está permitido transicionar ni simular los siguientes estados en Sprint R04:
- `ACQUIRING`
- `ACQUISITION_COMPLETED`
- `ACQUISITION_VERIFIED`
- `ANALYSIS_PENDING`
- `PROCESSING_AXIOM`
- `ANALYSIS_COMPLETED`
- `RESULTS_PENDING`
- `PORTABLE_CREATED`
- `REPORT_PENDING`
- `REPORT_GENERATED`
- `COMPLETED`

## 3. Matriz de Transiciones Legales

| Estado Origen | Acción | Estado Destino | Reclama Confirmación Humana | Políticas Requeridas |
|---|---|---|---|---|
| `NEW` | `START_IDENTIFICATION` | `IDENTIFICATION_PENDING` | No | `CASE_EXISTS`, `CASE_STRUCTURE_VALID`, `STATE_TRANSITION_ALLOWED` |
| `IDENTIFICATION_PENDING` | `COMPLETE_IDENTIFICATION_MOCK` | `IDENTIFICATION_COMPLETED` | No | `CASE_EXISTS`, `HAS_NUE`, `HAS_SPECIES`, `CASE_STRUCTURE_VALID` |
| `IDENTIFICATION_COMPLETED` | `PREPARE_ACQUISITION` | `ACQUISITION_READY` | Sí (Human Gate) | `CASE_EXISTS`, `HAS_NUE`, `HAS_SPECIES`, `HAS_DSM`, `CASE_JSON_MATCH`, `NO_CRITICAL_RECONCILIATION_ERROR` |
| *Cualquier Operativo* | `ABORT_CASE` | `ABORTED` | Sí (Human Gate) | `CASE_EXISTS`, `STATE_TRANSITION_ALLOWED` |
| *Cualquier Operativo* | `FAIL_CASE` | `FAILED` | No | `CASE_EXISTS` |

## 4. Transiciones Prohibidas (No Saltar Estados)
Queda estrictamente prohibido cualquier salto entre estados fuera de la matriz legal. Ejemplos denegados automáticamente:
- `NEW` → `ACQUISITION_READY` (DENIED)
- `NEW` → `ACQUISITION_COMPLETED` (DENIED)
- `IDENTIFICATION_PENDING` → `ANALYSIS_PENDING` (DENIED)
