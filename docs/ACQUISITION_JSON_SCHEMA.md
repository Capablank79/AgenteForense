# Schema: `acquisition.json`

## Estructura JSON de Artefactos de Adquisición
El archivo `acquisition.json` se genera de forma atómica en el directorio de destino tras la adquisición exitosa.

```json
{
  "schema_version": "1.0.0",
  "case_id": "UUID",
  "ruc": "12345678-9",
  "nue": 100,
  "species": 1,
  "dsm": 1,
  "binding_id": "UUID",
  "source_snapshot": {
    "physical_drive": "\\\\.\\PhysicalDrive2",
    "serial_number": "WD-WCC4N1234567",
    "size_bytes": 1000000000
  },
  "destination": "E:\\Caso_100\\NUE_100_ESPECIE1_DSM1",
  "ewfacquire": {
    "path": "J:\\AgenteForense\\ewftools-x64\\ewfacquire.exe",
    "sha256": "3cae1f37ece0b88746dc17810198b0171f4ca00ecb9c328e756baab5682e6791",
    "version": "ewftools 20240506"
  },
  "command": ["ewfacquire.exe", "-u", "-f", "encase6", "-c", "best", "-d", "sha256", "-S", "0"],
  "format": "encase6",
  "compression": "best",
  "hashes_requested": ["md5", "sha256"],
  "segment_strategy": "single_file",
  "human_confirmation": {
    "exact": "ADQUIRIR",
    "operator": "PeritoForensic",
    "confirmed_at": "2026-10-08T10:00:00Z"
  },
  "job_id": "JOB-12345678",
  "pid": 1234,
  "started_at": "2026-10-08T10:00:00Z",
  "finished_at": "2026-10-08T10:05:00Z",
  "exit_code": 0,
  "generated_files": ["E:\\Caso_100\\NUE_100_ESPECIE1_DSM1\\NUE_100_ESPECIE1_DSM1.E01"],
  "generated_segment_count": 1,
  "reported_hashes": {
    "md5": "5d41402abc4b2a76b9719d911017c592",
    "sha256": "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
  },
  "status": "COMPLETED",
  "errors": [],
  "tool_versions": {
    "ewfacquire": "ewftools 20240506",
    "agente_forense": "1.0.0"
  }
}
```
