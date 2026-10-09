# Arquitectura de Vinculación de Discos (Disk Binding Architecture)

## 1. Visión General

El módulo de vinculación de discos (`agente_forense.hardware`) proporciona una capa segura, no destructiva y bajo políticas estrictas de *fail-closed* para asociar dispositivos de almacenamiento físicos (`PhysicalDriveN`) del sistema operativo Windows con las especificaciones lógicas DSM (Device Specification Metadata) del dominio forense.

## 2. Principios de Seguridad Forense (Fail-Closed)

Para evitar la contaminación, sobreescritura accidental o alteración de evidencia física, un disco detectado en el host solo se clasifica como candidato forense (`FORENSIC_CANDIDATE`) si cumple simultáneamente tres condiciones deterministas:

1. `is_read_only == True`: El disco físico cuenta con protección contra escritura activa a nivel de bus o controladora (bloqueador de hardware o política en Windows).
2. `is_system == False`: El disco no aloja la instalación activa del sistema operativo Windows (`IsSystem`).
3. `is_boot == False`: El disco no contiene particiones de arranque activas (`IsBoot`).

Cualquier incumplimiento de estas condiciones invalida inmediatamente el disco con clasificaciones de bloqueo explícitas (`BLOCKED_NOT_READ_ONLY`, `BLOCKED_SYSTEM_DISK`, `BLOCKED_BOOT_DISK`, `BLOCKED_MULTIPLE_REASONS`, etc.).

## 3. Flujo de Vida del Binding y Human Gate

El proceso de vinculación **nunca es automático**. Sigue estrictamente un flujo supervisado con intervención humana explícita:

```text
               +----------------------+
               |    Physical Scan     |
               +----------+-----------+
                          |
                          v
               +----------------------+
               |   Classification &   |
               |       Matching       |
               +----------+-----------+
                          |
                          v
               +----------------------+
               |   PROPOSED_BINDING   |
               +----------+-----------+
                          |
                          v
               +----------------------+
               |      Human Gate      |
               | (Human Confirmation) |
               +----------+-----------+
                          |
                          v
               +----------------------+
               |  CONFIRMED_BINDING   |
               +----------+-----------+
                          |
                          v
               +----------------------+
               | Dynamic Revalidation |
               +----------+-----------+
                          |
             +------------+------------+
             |                         |
             v                         v
     [ Integrity OK ]         [ Integrity Changed ]
             |                         |
             v                         v
   ACQUISITION_READY            INVALIDATED &
                             SourceChangedError
```

## 4. Persistencia e Historial Append-Oriented

El historial de vinculación se mantiene en la tabla PostgreSQL `forensic.dsm_disk_bindings` sin sobreescribir ni modificar los registros históricos:

- **PROPOSED**: Propuesto por la interfaz de usuario o API tras la verificación del candidato.
- **CONFIRMED**: Confirmado por el operador humano a través del Human Gate. Al confirmar un nuevo binding para un DSM, cualquier binding `CONFIRMED` anterior para dicho DSM se marca automáticamente como `INVALIDATED`.
- **INVALIDATED**: Invalidado por sustitución de binding, revalidación fallida (`SourceChangedError`) o desconexión del medio.
- **REJECTED**: Rechazado explícitamente por el operador humano durante la confirmación.

## 5. Revalidación Dinámica y Auditoría

Antes de autorizar la transición del caso hacia `ACQUISITION_READY`, el `DiskRevalidator` re-evalúa el estado en caliente del disco físico:
- Verifica la presencia del mismo `disk_number` y `physical_drive`.
- Compara la coincidencia exacta de `serial_number`, `unique_id` y `size_bytes`.
- Garantiza que `is_read_only` continúe siendo `True` y que `is_system` y `is_boot` sigan siendo `False`.

En caso de cualquier discrepancia, se dispara una excepción `SourceChangedError`, invalidando el binding y bloqueando el avance en el motor de políticas (Policy Engine).
