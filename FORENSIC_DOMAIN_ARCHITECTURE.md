# Arquitectura del Dominio Forense (R03)

## 1. Modelo Operacional
El AGENTE FORENSE se rige bajo la jerarquía de dominio:

```text
RUC (Rol Único Causa / Caso)
└── NUE (Número Único de Evidencia)
    └── ESPECIE (Objeto Físico)
        └── DSM (Dispositivo / Medio de Almacenamiento Digital)
```

### Definiciones
- **RUC**: Identificador único causa / caso judicial.
- **NUE**: Identificador de la evidencia entregada en el marco de la causa.
- **ESPECIE**: Objeto físico observado (ej: teléfono, disco duro externo, pendrive, notebook).
- **DSM**: Dispositivo o medio de almacenamiento digital susceptible de extracción / adquisición forense.

## 2. Topología y Relaciones Físicas

Se definen dos tipos de relaciones físicas de almacenamiento:

1. **`SELF_STORAGE`**:
   - El objeto físico ES en sí mismo el medio de almacenamiento digital (ej. pendrive, tarjeta SD, disco externo).
   - `same_physical_object_as_species = True`.
   - Exige exactamente 1 DSM por Especie (`dsm_number = 1`).

2. **`CONTAINED_STORAGE`**:
   - El objeto físico CONTIENE uno o más medios de almacenamiento (ej. un servidor o notebook con 2 SSDs internos en RAID/separados).
   - `same_physical_object_as_species = False`.
   - Permite 1 o más DSMs (`dsm_number >= 1`).

## 3. Identidad y Etiquetado Determinístico
- Identificador primario en PostgreSQL: `UUID` interno.
- Nombres de etiquetas (Labels) derivadas y determinísticas:
  - `RUC_<RUC>`
  - `NUE_<NUE>`
  - `NUE_<NUE>_ESPECIE<n>`
  - `NUE_<NUE>_ESPECIE<n>_DSM<m>`

El usuario no edita ni altera manualmente las etiquetas derivadas.

## 4. Invariantes del Dominio y Errores
- No invención de metadata: campos desconocidos permanecen `NULL` o `PENDING`.
- Autenticidad técnica: Validación de RUC y NUE contra path traversal y nombres reservados de Windows.
- Unicidad de RUC en el sistema.
- Unicidad de NUE por RUC.
- Unicidad de Especie por NUE (números correlativos 1..N).
- Unicidad de DSM por Especie (números correlativos 1..M).
- Atomicidad en persitencia DB y en archivos snapshot `case.json`.
