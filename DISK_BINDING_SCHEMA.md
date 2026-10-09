# Esquema de Base de Datos y Estructuras Data - Disk Binding

## 1. Migración PostgreSQL: `forensic.dsm_disk_bindings`

La migración `004` define la estructura del historial de vinculación de discos con DSMs de manera append-oriented.

### Definición SQL DDL (`src/agente_forense/persistence/migrations_004.py`)

```sql
CREATE TABLE IF NOT EXISTS forensic.dsm_disk_bindings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID NOT NULL REFERENCES forensic.cases(id) ON DELETE RESTRICT,
    dsm_id UUID NOT NULL REFERENCES forensic.dsms(id) ON DELETE RESTRICT,
    disk_number INTEGER NOT NULL,
    physical_drive VARCHAR(100) NOT NULL,
    serial_number VARCHAR(255) NULL,
    unique_id TEXT NULL,
    friendly_name TEXT NULL,
    size_bytes BIGINT NOT NULL,
    bus_type VARCHAR(50) NULL,
    is_read_only BOOLEAN NOT NULL,
    is_system BOOLEAN NOT NULL,
    is_boot BOOLEAN NOT NULL,
    is_offline BOOLEAN NULL,
    observed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    confirmed_at TIMESTAMPTZ NULL,
    status VARCHAR(50) NOT NULL,
    snapshot_json JSONB NOT NULL,
    request_id UUID NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_dsm_disk_bindings_case_dsm 
ON forensic.dsm_disk_bindings(case_id, dsm_id);

CREATE INDEX IF NOT EXISTS idx_dsm_disk_bindings_status 
ON forensic.dsm_disk_bindings(status);
```

## 2. Definición del Snapshot de Disco (`DiskSnapshot`)

Estructura Pydantic `frozen` que captura el estado físico e inmutable del disco en el instante del escaneo:

```python
class DiskSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True)

    disk_number: int
    physical_drive: str          # Ej: "\\.\PhysicalDrive2"
    friendly_name: Optional[str]
    serial_number: Optional[str]
    unique_id: Optional[str]
    path: Optional[str]
    size_bytes: int
    bus_type: Optional[str]
    partition_style: Optional[str]
    is_read_only: bool
    is_system: bool
    is_boot: bool
    is_offline: Optional[bool]
    operational_status: Optional[str]
    health_status: Optional[str]
    pnp_device_id: Optional[str]
    observed_at: datetime
    source: str = "WINDOWS_STORAGE_API"
```

## 3. Integración en `case.json`

Cuando un binding de disco se confirma para un DSM, el archivo de metadatos `case.json` se actualiza de manera atómica (`os.replace` previa escritura en temporal) incluyendo una sección `active_disk_binding`:

```json
{
  "schema_version": 1,
  "case_id": "c7450a3d-4052-4927-99f7-7266253c8197",
  "ruc": "RUC123456-7",
  "status": "ACQUISITION_READY",
  "nues": [
    {
      "nue": "NUE_001",
      "species": [
        {
          "species_number": 1,
          "label": "Evidencia 1",
          "dsms": [
            {
              "dsm_number": 1,
              "label": "Disco Kingston",
              "active_disk_binding": {
                "binding_id": "a9b8c7d6-e5f4-3210-9876-543210fedcba",
                "disk_number": 3,
                "physical_drive": "\\\\.\\PhysicalDrive3",
                "serial_number": "KNG123456789",
                "size_bytes": 64000000000,
                "is_read_only": true,
                "status": "CONFIRMED",
                "confirmed_at": "2026-10-08T14:30:00Z"
              }
            }
          ]
        }
      ]
    }
  ]
}
```
