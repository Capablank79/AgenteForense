# Motor de Políticas — Agente Forense (Policy Engine)

## 1. Reglas y Principios
El Motor de Políticas (`PolicyEngine`) evalúa reglas de negocio deterministas de manera estática antes de autorizar cualquier cambio de estado.

- **Evaluación determinista:** Sin llamadas a modelos de lenguaje (LLM) para decisiones de seguridad o integridad de evidencia.
- **Fail-Closed:** Si una política falla o no se puede evaluar, la decisión por defecto es `DENY`.
- **Resultados de decisión:** `ALLOW`, `DENY` o `REQUIRES_CONFIRMATION`.

## 2. Políticas Implementadas en Sprint R04

1. `CASE_EXISTS`: Verifica que el ID del caso exista en la base de datos PostgreSQL.
2. `CASE_STRUCTURE_VALID`: Verifica que el caso posea una estructura y RUC válidos.
3. `HAS_NUE`: Exige al menos una NUE asociada al caso.
4. `HAS_SPECIES`: Exige al menos una especie asociada a las NUEs del caso.
5. `HAS_DSM`: Exige al menos un dispositivo de almacenamiento (DSM) registrado en la especie.
6. `CASE_JSON_MATCH`: Valida la existencia, sintaxis JSON y coincidencia estructural entre PostgreSQL y `case.json`.
7. `NO_CRITICAL_RECONCILIATION_ERROR`: Verifica la ausencia de errores críticos en el informe de reconciliación.
8. `STATE_TRANSITION_ALLOWED`: Valida que el estado objetivo sea legal y pertenezca al conjunto de `OperativeState` activos (bloquea transiciones a `ReservedState`).

## 3. Políticas Reservadas para Sprints Futuros
Las siguientes políticas han sido registradas en el catálogo pero devuelven `DENY` por defecto en R04 hasta que las herramientas o componentes de hardware correspondientes sean integrados:
- `SOURCE_READ_ONLY`
- `SOURCE_NOT_SYSTEM`
- `SOURCE_NOT_BOOT`
- `PHYSICAL_DRIVE_BOUND`
- `DESTINATION_SAFE`
- `E01_NOT_EXISTS`
- `HUMAN_CONFIRMATION_PRESENT`

## 4. Auditoría de Políticas
Cada evaluación de políticas es registrada en la tabla append-only `forensic.audit_events` con el tipo de evento `POLICY_EVALUATED`, incluyendo la decisión tomada y la razón técnica correspondiente.
