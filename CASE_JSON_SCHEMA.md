# Especificación de Esquema case.json (R03)

## 1. Propósito
`case.json` actúa como la foto o snapshot portable del caso forense.
- **PostgreSQL**: Memoria operacional global, índices y estado vivo.
- **case.json**: Snapshot portable por cada RUC / contrato interoperable de intercambio.

## 2. Schema Version
- **`schema_version = 1`**: Decisión formal para la reconstrucción del AGENTE FORENSE. Se utiliza 1 como baseline claro y verificado sin acoplamientos históricos obsoletos.

## 3. Estructura JSON Mínima Exigida

```json
{
  "schema_version": 1,
  "case_id": "uuid-string",
  "ruc": "12345678-9",
  "status": "NEW",
  "created_at": "2026-10-07T12:00:00+00:00",
  "updated_at": "2026-10-07T12:00:00+00:00",
  "nues": [
    {
      "nue": "777777",
      "species": [
        {
          "species_number": 1,
          "label": "NUE_777777_ESPECIE1",
          "storage_relation": "CONTAINED_STORAGE",
          "identification_status": "PENDING",
          "storage_devices": [
            {
              "dsm_number": 1,
              "label": "NUE_777777_ESPECIE1_DSM1",
              "same_physical_object_as_species": false,
              "physical_drive": null,
              "acquisition_status": "PENDING",
              "verification_status": "PENDING"
            }
          ]
        }
      ]
    }
  ]
}
```

## 4. Escritura Atómica
Para evitar corrupción de snapshots en caídas de energía o del sistema, la escritura de `case.json` utiliza el patrón:
1. Creación de un archivo temporal `.tmp` en el mismo directorio objetivo.
2. Flush de buffers y `fsync` explícito en sistema operativo.
3. Reemplazo atómico (`os.replace`) sobre `case.json`.

## 5. Reconciliación DB ↔ case.json
El motor de reconciliación evalúa los siguientes estados:
- **`MATCH`**: DB y `case.json` están 100% en sincronía estructural y de contenido.
- **`MISSING_FILE`**: `case.json` no existe en el disco.
- **`INVALID_JSON`**: El archivo en disco está corrupto o no es JSON válido.
- **`SCHEMA_MISMATCH`**: La versión de `schema_version` no coincide.
- **`CONTENT_MISMATCH`**: Inconsistencia entre los registros en DB y los declarados en `case.json`.

Ninguna inconsistencia es corregida de forma silenciosa. Se registra en auditoría y requiere intervención explícita.
