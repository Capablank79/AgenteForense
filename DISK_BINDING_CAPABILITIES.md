# DISK_BINDING_CAPABILITIES — Investigación y Validación del Vínculo Seguro DSM ↔ PhysicalDrive

## 1. BASELINE

- **Python**: 3.10.11
- **OS**: Windows 10 Pro build 19045 (10.0.19045.0)
- **PostgreSQL**: 18.6 (localhost:5432 / forensic DB)
- **Web App**: FastAPI 127.0.0.1:8085
- **Pytest**: 203 passed (0 failures, 17 warnings)
- **Estado Forense previo**: `PHOTO_IDENTIFICATION_READY`

---

## 2. WINDOWS

- **Product Name**: Windows 10 Pro
- **ReleaseId / DisplayVersion**: 22H2 / 19045.6456
- **Architecture**: x64
- **Host Execution Environment**: PowerShell 5.1 (ConsoleHost)

---

## 3. POWERSHELL

- **Executable Path**: `C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe`
- **Version**: 5.1.19041.6456
- **Edition**: Desktop
- **pwsh.exe (PowerShell Core 7+)**: No instalado en el sistema local.
- **Modo de ejecución futuro requerido**:
  ```python
  subprocess.run(
      ["C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe", "-NoProfile", "-Command", cmd],
      shell=False,
      timeout=15,
      capture_output=True,
      text=True,
      encoding="windows-1252" # o utf-8 dependiendo de salida
  )
  ```

---

## 4. STORAGE MODULE

- **ModuleName**: Storage
- **Version**: 2.0.0.0
- **Path**: `C:\WINDOWS\system32\WindowsPowerShell\v1.0\Modules\Storage\Storage.psd1`
- **Cmdlets provistos**: `Get-Disk`, `Get-PhysicalDisk`, `Set-Disk`, `Initialize-Disk`, etc.

---

## 5. GET-DISK COMMAND

- **Cmdlet**: `Get-Disk` (Module: `Storage`)
- **Help / Synopsys**: Obtains one or more disk objects visible to the operating system.
- **Sintaxis de invocación segura para recolección**:
  ```powershell
  Get-Disk | Select-Object Number, FriendlyName, SerialNumber, UniqueId, Path, Size, BusType, PartitionStyle, IsReadOnly, IsSystem, IsBoot, IsOffline, OperationalStatus, HealthStatus | ConvertTo-Json -Depth 4 -Compress
  ```

---

## 6. GET-DISK REAL OUTPUT SHAPE

Estructura obtenida del entorno REAL (anonimizada/ejemplo real del sistema):

```json
[
    {
        "Number": 1,
        "FriendlyName": "KINGSTON SKC6001024G",
        "SerialNumber": "50026B77836AADBE",
        "UniqueId": "50026B77836AADBE",
        "Path": "\\\\?\\scsi#disk&ven_&prod_kingston_skc6001#4&5ecf4f&0&020000#{53f56307-b6bf-11d0-94f2-00a0c91efb8b}",
        "Size": 1024209543168,
        "BusType": "SATA",
        "PartitionStyle": "MBR",
        "IsReadOnly": false,
        "IsSystem": true,
        "IsBoot": true,
        "IsOffline": false,
        "OperationalStatus": "Online",
        "HealthStatus": "Healthy"
    },
    {
        "Number": 4,
        "FriendlyName": "WDC WD20EADS-32S2B0",
        "SerialNumber": "     WD-WCAVY3676912",
        "UniqueId": "50014E2EAF221130",
        "Path": "\\\\?\\scsi#disk&ven_wdc&prod_wd20eads-32s2b0#4&5ecf4f&0&030000#{53f56307-b6bf-11d0-94f2-00a0c91efb8b}",
        "Size": 2000398934016,
        "BusType": "SATA",
        "PartitionStyle": "GPT",
        "IsReadOnly": false,
        "IsSystem": false,
        "IsBoot": false,
        "IsOffline": false,
        "OperationalStatus": "Online",
        "HealthStatus": "Healthy"
    },
    {
        "Number": 3,
        "FriendlyName": "WDC WD80 EFAX-68KNBN0",
        "SerialNumber": "EC0000003113",
        "UniqueId": "USBSTOR\\DISK&VEN_WDC_WD80&PROD_EFAX-68KNBN0&REV_81.0\\3113000000CE&0:FRED-LFL",
        "Path": "\\\\?\\usbstor#disk&ven_wdc_wd80&prod_efax-68knbn0&rev_81.0#3113000000ce&0#{53f56307-b6bf-11d0-94f2-00a0c91efb8b}",
        "Size": 8001563222016,
        "BusType": "USB",
        "PartitionStyle": "GPT",
        "IsReadOnly": false,
        "IsSystem": false,
        "IsBoot": false,
        "IsOffline": false,
        "OperationalStatus": "Online",
        "HealthStatus": "Healthy"
    }
]
```

---

## 7. GET-PHYSICALDISK

- **Cmdlet**: `Get-PhysicalDisk` (Module: `Storage`)
- **Propiedades relevantes adicionadas/diferenciales**:
  - `DeviceId` (Coincide con `Disk.Number` como string en la mayoría de discos).
  - `MediaType` (`SSD`, `HDD`, `Unspecified`).
  - `OperationalStatus` (`OK`, `Degraded`, `Lost Communication`, etc.).
  - `SerialNumber`: Se observó que en algunos discos USB `Get-PhysicalDisk` elimina espacios leading (ej. `"WD-WCAVY3676912"` vs `"     WD-WCAVY3676912"` en `Get-Disk`).
  - `UniqueId`: Presenta GUIDs formateados en algunos controladores (ej. `"{12485027-825f-1818-f5e1-0d5907818c30}"`) a diferencia de la ruta USBSTOR en `Get-Disk`.

---

## 8. WIN32_DISKDRIVE

- **WMI / CIM Class**: `Win32_DiskDrive` (`Get-CimInstance Win32_DiskDrive`)
- **Propiedades clave**:
  - `Index` (Integer: 0, 1, 2, 4, 5... Corresponde exactamente a `Get-Disk.Number`).
  - `DeviceID` (String: `\\.\PHYSICALDRIVE0`, `\\.\PHYSICALDRIVE1`, `\\.\PHYSICALDRIVE4`, etc.).
  - `Model` (String: Nombre de modelo del fabricante + bus, ej. `"WDC WD80 EFAX-68KNBN0 USB Device"`).
  - `PNPDeviceID` (ID de Plug and Play de Windows).
  - `Size` (Bytes reportados por WMI, ej. 2000396321280 B vs 2000398934016 B en Get-Disk por alineación de sectores/geometría).

---

## 9. DISK NUMBER ↔ PHYSICALDRIVE

Se verificó en el entorno REAL mediante la correlación entre `Get-Disk` y `Win32_DiskDrive`:

$$\text{Get-Disk.Number } N \iff \text{Win32\_DiskDrive.Index } N \iff \text{DeviceID } \texttt{\\\\.\\PHYSICALDRIVEN}$$

Ejemplo real observado:
- `Get-Disk Number = 4` $\rightarrow$ `Win32_DiskDrive Index = 4` $\rightarrow$ `DeviceID = \\.\PHYSICALDRIVE4`.
- **Regla forense**: No se debe asumir que los números de disco son secuenciales contiguos (en el sistema de prueba se observaron los índices 0, 1, 2, 3, 4, 5, pero la desconexión de unidades puede dejar huecos).

---

## 10. ENCODING

- **Observaciones**:
  - En PowerShell 5.1 con `ConvertTo-Json`, caracteres especiales (como `&`) se codifican en Unicode escapes (`\u0026`).
  - Nombres de dispositivos o modelos pueden contener caracteres no-ASCII dependiendo del idioma del firmware/driver.
  - Al ejecutar `subprocess.run`, se debe decodificar el JSON devuelto con `json.loads()` asegurando lectura de `stdout` en `utf-8` o `windows-1252` previo al parsing.

---

## 11. LATENCY

- **Medición REAL**:
  - `Get-Disk | ... | ConvertTo-Json`: ~2.78 segundos.
  - `Get-PhysicalDisk + Win32_DiskDrive`: ~0.45 segundos.
- **Conclusión de rendimiento**: La ejecución de `Get-Disk` mediante subproceso de PowerShell 5.1 toma aproximadamente 2.5–3.0 segundos debido a la inicialización del motor PowerShell y la resolución del módulo `Storage`. Se debe establecer un `timeout` mínimo de 15 segundos en `subprocess.run`.

---

## 12. PRIVILEGES

- **Ejecución como usuario estándar**:
  - `Get-Disk`, `Get-PhysicalDisk` y `Get-CimInstance Win32_DiskDrive` funcionan correctamente para CONSULTA de metadatos sin elevación de privilegios (Administrator).
- **Acceso futuro a `\\.\PhysicalDriveN`**: Requerirá privilegios de Administrador (`Run as Administrator`), pero las consultas de descubrimiento y validación en R07 operan 100% en modo no elevado.

---

## 13. FIELD PROVENANCE

Para garantizar la auditabilidad forense del origen de cada dato, se registrará la procedencia por campo:

| Campo | Valor Ejemplo | Comando Fuente (`source_command`) | Propiedad Fuente (`source_property`) |
| :--- | :--- | :--- | :--- |
| `disk_number` | `4` | `Get-Disk` | `Number` |
| `physical_drive` | `\\.\PHYSICALDRIVE4` | `Win32_DiskDrive` | `DeviceID` |
| `friendly_name` | `WDC WD20EADS-32S2B0` | `Get-Disk` | `FriendlyName` |
| `serial_number` | `WD-WCAVY3676912` | `Get-Disk` / `Get-PhysicalDisk` | `SerialNumber` |
| `unique_id` | `50014E2EAF221130` | `Get-Disk` | `UniqueId` |
| `size_bytes` | `2000398934016` | `Get-Disk` | `Size` |
| `is_read_only` | `true` / `false` | `Get-Disk` | `IsReadOnly` |
| `is_system` | `false` | `Get-Disk` | `IsSystem` |
| `is_boot` | `false` | `Get-Disk` | `IsBoot` |

---

## 14. DISK SNAPSHOT MODEL

Modelo de datos inmutable propuesto para representar la observación puntual de un disco físico (`DiskSnapshot`):

```python
class DiskSnapshot(BaseModel):
    disk_number: int
    physical_drive: str  # ej: "\\\\.\\PHYSICALDRIVE4"
    friendly_name: Optional[str] = None
    serial_number: Optional[str] = None
    unique_id: Optional[str] = None
    path: Optional[str] = None
    size_bytes: int
    bus_type: Optional[str] = None  # SATA, USB, RAID, NVMe
    partition_style: Optional[str] = None  # MBR, GPT, RAW
    is_read_only: bool
    is_system: bool
    is_boot: bool
    is_offline: bool
    operational_status: Optional[str] = None
    health_status: Optional[str] = None
    pnp_device_id: Optional[str] = None
    observed_at: datetime
    source: str = "WINDOWS_STORAGE_API"
```

---

## 15. FORENSIC CANDIDATE POLICY

Regla estricta e inquebrantable de clasificación de discos forenses:

Un disco sólo es `FORENSIC_CANDIDATE` si y sólo si:
- `IsReadOnly == True`
- `IsSystem == False`
- `IsBoot == False`

Matriz de clasificación:

```text
SI IsReadOnly == False                    -> BLOCKED_NOT_READ_ONLY
SI IsSystem == True                       -> BLOCKED_SYSTEM_DISK
SI IsBoot == True                         -> BLOCKED_BOOT_DISK
SI IsReadOnly == False Y IsSystem == True -> BLOCKED_MULTIPLE_REASONS
SI Parse Error / Missing critical metadata -> UNSUPPORTED_DISK_REPRESENTATION
```

---

## 16. GET-DISK LIMITATIONS

1. **Discos Dinámicos / LDM**: Microsoft documenta que discos con configuración LDM o volúmenes dinámicos legacy pueden no ser devueltos por `Get-Disk`.
2. **Fail-closed**: Si un disco físico es visible en `Win32_DiskDrive` pero `Get-Disk` devuelve `NOT_RETURNED_BY_GET_DISK` o no puede determinar `IsReadOnly`, el sistema **DEBE** marcar el estado como `UNSUPPORTED_DISK_REPRESENTATION` y bloquear el proceso.

---

## 17. DSM DATA AVAILABLE

Campos inspeccionados en la tabla `forensic.dsms` (`DsmModel`):

- `id`: UUID (Primary Key)
- `species_id`: UUID (Foreign Key)
- `dsm_number`: Integer
- `label`: String(128)
- `same_physical_object_as_species`: Boolean
- `device_type`: String(64) (ej. "Disco Duro Externo", "Pendrive")
- `brand`: String(128) (ej. "Western Digital", "Kingston")
- `model`: String(128) (ej. "WD20EADS")
- `serial`: String(128) (ej. "WD-WCAVY3676912")
- `capacity_bytes`: BigInteger (ej. 2000398934016)

---

## 18. MATCHING MODEL

Motor de comparación DSM ↔ Disk Candidate:

- **`MATCH`**: Serial normalizado coincide exactamente + Capacidad dentro de margen + Marca/Modelo compatible.
- **`COMPATIBLE`**: Modelo/Marca coincide y Capacidad cercana, pero Serial ausente en DSM o en Disco.
- **`CONFLICT`**: Serial de DSM existe y Serial de Disco existe, pero NO coinciden.
- **`INSUFFICIENT_DATA`**: DSM no posee Serial registrado y posee datos ambiguos.
- **`NOT_COMPARABLE`**: Tipos de medio o arquitecturas incompatibles.

---

## 19. SERIAL POLICY

- **Normalización**: Trimming de espacios leading/trailing (ej. `"     WD-WCAVY3676912"`.strip() $\rightarrow$ `"WD-WCAVY3676912"`).
- **Inmutable**: No se inventa, trunca ni autocompleta ningún serial.
- **Conflicto**: Coincidencia parcial o discrepancia en seriales confirmados resulta en `CONFLICT` automático.

---

## 20. CAPACITY POLICY

- Distinción entre **Capacidad Comercial Nominal** (ej. 2 TB = $2 \times 10^{12}$ bytes) y **Bytes Físicos OS** (ej. 2,000,398,934,016 bytes).
- La validación tolera diferencias entre unidades comerciales y sectores físicos reportados por el controlador, pero requiere confirmación humana.

---

## 21. AMBIGUITY POLICY

- Si múltiples discos físicos califican como `FORENSIC_CANDIDATE` y coinciden con un DSM, el sistema devuelve `MULTIPLE_CANDIDATES`.
- Queda totalmente **PROHIBIDO** realizar binding automático o resolución heurística por software.

---

## 22. BINDING MODEL

Flujo de vinculación seguro:

```text
SELECCIÓN LOGICA DSM
  └── DISCOVERY DISCOS WINDOWS
        └── FILTRADO POLICY (IsReadOnly=True, IsSystem=False, IsBoot=False)
              └── MATCHING ENGINE (Propuestas)
                    └── PROPOSED_BINDING
                          └── HUMAN GATE (Revisión y Selección)
                                └── CONFIRMED_BINDING
```

---

## 23. REBINDING POLICY

- No se permite sobrescribir silenciosamente un binding en estado `CONFIRMED`.
- Cualquier cambio de asignación genera un registro histórico desvinculado con evento de auditoría `DISK_BINDING_INVALIDATED` y nuevo `DISK_BINDING_PROPOSED`.

---

## 24. REVALIDATION POLICY

Inmediatamente antes de iniciar cualquier fase futura de adquisición:
1. Volver a consultar metadatos del disco en Windows.
2. Verificar: `disk_number`, `physical_drive`, `serial_number`, `unique_id`, `size_bytes`, `is_read_only`, `is_system`, `is_boot`.
3. Si `IsReadOnly` cambia a `False` o si la UniqueId/Serial cambia $\rightarrow$ Emitir error `SOURCE_CHANGED` y BLOQUEAR adquisición.

---

## 25. HUMAN GATE

El operador humano debe visualizar en la interfaz web:
- **Datos DSM del Caso**: RUC, NUE, Especie, DSM Number, Marca, Modelo, Serial registrado, Capacidad declarada.
- **Datos del Disco Físico Candidato**: Disk Number, PhysicalDrive, FriendlyName, Serial reportado por OS, UniqueId, Tamaño real OS, BusType, Estado `IsReadOnly` (Verificado por OS).
- **Resultado de Matching**: Match / Compatible / Warning.
- **Acción explícita**: Botón de confirmación humana `CONFIRM_DISK_BINDING`.

---

## 26. DATABASE DESIGN

Recomendación de arquitectura de persistencia:

**Opción seleccionada**: Tabla append-oriented `forensic.dsm_disk_bindings` separada de `forensic.dsms`.
- *Razón*: Mantiene la identidad lógica forense del DSM limpia e inmutable respecto a las observaciones de hardware físico y reinserciones de discos en distintos puertos/buses.

Esquema propuesto para la tabla futura:

```sql
CREATE TABLE forensic.dsm_disk_bindings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID NOT NULL REFERENCES forensic.cases(id),
    dsm_id UUID NOT NULL REFERENCES forensic.dsms(id),
    disk_number INT NOT NULL,
    physical_drive VARCHAR(255) NOT NULL,
    serial_number VARCHAR(255),
    unique_id TEXT,
    size_bytes BIGINT NOT NULL,
    bus_type VARCHAR(64),
    is_read_only BOOLEAN NOT NULL,
    is_system BOOLEAN NOT NULL,
    is_boot BOOLEAN NOT NULL,
    observed_at TIMESTAMPTZ NOT NULL,
    confirmed_at TIMESTAMPTZ NOT NULL,
    operator VARCHAR(255) NOT NULL,
    snapshot_json JSONB NOT NULL,
    status VARCHAR(64) NOT NULL DEFAULT 'CONFIRMED',
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);
```

---

## 27. WEB FLOW

1. Navegación a detalle de DSM dentro del Caso (`/cases/{id}/dsms/{dsm_id}`).
2. Sección "Vínculo de Disco Físico".
3. Botón "Escanear Discos Candidatos" $\rightarrow$ Llama a API de descubrimiento.
4. Renderizado de lista de candidatos filtrados por Policy Engine (`FORENSIC_CANDIDATE`).
5. Selección del candidato por el operador $\rightarrow$ Presentación de comparativa (DSM vs PhysicalDrive).
6. Confirmación humana $\rightarrow$ Envío de POST con CSRF token.

---

## 28. API CONTRACT

Endpoints diseñados para la futura implementación:

- `GET /api/system/disks`: Lista todos los discos del OS con su clasificación forense.
- `GET /api/cases/{case_id}/dsms/{dsm_id}/disk-candidates`: Obtiene discos escaneados clasificados y comparados con el DSM especificado.
- `POST /api/cases/{case_id}/dsms/{dsm_id}/disk-binding/propose`: Crea una propuesta temporal de vínculo.
- `POST /api/cases/{case_id}/dsms/{dsm_id}/disk-binding/confirm`: Confirma el vínculo (Human Gate). Requiere CSRF.
- `GET /api/cases/{case_id}/dsms/{dsm_id}/disk-binding`: Obtiene el vínculo activo y verificado.
- `POST /api/cases/{case_id}/dsms/{dsm_id}/disk-binding/revalidate`: Revalida que el disco físico siga conectado y en `IsReadOnly=True`.

---

## 29. POLICY ENGINE IMPACT

Nuevas políticas a incorporar en `PolicyEngine`:

- `DSM_SELECTED`: Evalúa si un DSM válido ha sido seleccionado.
- `PHYSICAL_DRIVE_DETECTED`: Evalúa si Windows reporta el disco especificado.
- `SOURCE_READ_ONLY`: Evalúa `IsReadOnly == True`. (Política CRÍTICA / Bloqueante).
- `SOURCE_NOT_SYSTEM`: Evalúa `IsSystem == False`. (Política CRÍTICA / Bloqueante).
- `SOURCE_NOT_BOOT`: Evalúa `IsBoot == False`. (Política CRÍTICA / Bloqueante).
- `DISK_BINDING_CONFIRMED`: Evalúa si existe un binding confirmado por operador.
- `DISK_BINDING_CURRENT`: Evalúa si el recheck de presencia física y estado concuerda con la foto del binding.

---

## 30. STATE MACHINE IMPACT

- El estado general del caso o flujo avanza de `PHOTO_IDENTIFICATION_READY` a `ACQUISITION_READY` únicamente cuando:
  1. DSM está identificado y validado.
  2. Disco físico candidato posee `IsReadOnly = True`, `IsSystem = False`, `IsBoot = False`.
  3. Operador humano confirmó el vínculo.
  4. Revalidación inmediata reporta `ALLOW`.
- R07 **NO** realiza la transición a `ACQUISITION_READY` ni marca `ACQUIRING`.

---

## 31. DEPENDENCIES FOR R07.1

Para SPRINT_R07.1 (o implementación del módulo):
1. Módulo Python `agente_forense.hardware.disks` con parser de PowerShell y cliente WMI/CIM.
2. Fixtures/Mocks de `Get-Disk` con `IsReadOnly=True` para suite de pruebas en CI/CD donde no existan write-blockers físicos.
3. Tabla `forensic.dsm_disk_bindings` en PostgreSQL.

---

## 32. RISKS

- **Discos sin Write-Blocker Físico**: En entornos de laboratorio sin bloqueador de hardware activo, Windows reporta `IsReadOnly = False`, lo que impide por policy seleccionar discos físicos reales. Esto se aborda mediante fixtures/mocks de validación en R07.
- **Rutas de `UniqueId` complejas**: Discos USB montados sobre ciertas controladoras pueden cambiar su `UniqueId` si son reconectados en un puerto USB diferente.

---

## 33. BLOCKERS

Actualmente **NO EXISTEN BLOQUEADORES** técnicos para el avance hacia R07.1. Se ha verificado la capacidad completa de Windows PowerShell, WMI y la API de Storage para la identificación segura de discos.

---

## 34. ESTADO DE CAPACIDADES R07

```text
DISK_BINDING_CAPABILITIES_VERIFIED
```
