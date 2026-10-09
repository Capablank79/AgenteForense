# EWFACQUIRE_CAPABILITIES — Investigación y Caracterización de ewfacquire

## 1. BASELINE
- **Python**: 3.10.11 (win32)
- **OS**: Windows (Platform win32)
- **PostgreSQL**: Local / Configurado según SPRINT_R01
- **Git Branch**: `main`
- **Git Commit**: `e1bf433` (Sprint R00: inicializa reconstruccion tecnica desde cero)
- **Pytest Baseline**: 208 passed (0 failures, 17 warnings)
- **Estado Previo (R07.1)**: `DISK_BINDING_READY`

---

## 2. BINARY PATH & IDENTIFICATION
- **Full Path**: `J:\AgenteForense\ewftools-x64\ewfacquire.exe`
- **Exists**: `True`
- **File Size**: `1,175,040` bytes (1.12 MB)
- **Last Modified**: `2024-07-11T09:44:59`
- **SHA-256**: `3cae1f37ece0b88746dc17810198b0171f4ca00ecb9c328e756baab5682e6791`

---

## 3. VERSION & HELP OUTPUT SUMMARY

### 3.1 Versión
- **Comando**: `ewfacquire.exe -V`
- **Exit Code**: `0`
- **Version String**: `ewfacquire 20230405`
- **Copyright**: Joachim Metz (Copyright (C) 2006-2023)
- **Encoding**: ASCII / UTF-8 (`\r\n`)
- **Latency**: ~0.19s

### 3.2 Help Output Summary
- **Comando**: `ewfacquire.exe -h`
- **Exit Code**: `0`
- **Summary**: Binario nativo de la suite libewf/ewftools x64 para adquisición de imágenes EWF.
- **Sintaxis general**:
  `ewfacquire [ -A codepage ] [ -b number_of_sectors ] [ -B number_of_bytes ] [ -c compression_values ] [ -C case_number ] [ -d digest_type ] [ -D description ] [ -e examiner_name ] [ -E evidence_number ] [ -f format ] [ -g number_of_sectors ] [ -j jobs ] [ -l log_filename ] [ -m media_type ] [ -M media_flags ] [ -N notes ] [ -o offset ] [ -p process_buffer_size ] [ -P bytes_per_sector ] [ -r read_error_retries ] [ -S segment_file_size ] [ -t target ] [ -T toc_file ] [ -2 secondary_target ] [ -hqRsuvVwx ] source`

---

## 4. SUPPORTED FORMATS & E01 FORMAT
- **Format Flag**: `-f <format>`
- **Format Options**: `ewf`, `smart`, `ftk`, `encase2`, `encase3`, `encase4`, `encase5`, `encase6` (default), `encase7`, `encase7-v2`, `linen5`, `linen6`, `linen7`, `ewfx`
- **E01 Format Selection**: `encase6` (default). Corresponde al estándar de formato E01/EnCase v6 de amplio soporte forense.

---

## 5. COMPRESSION
- **Compression Flag**: `-c <level>` o `-c <method:level>`
- **Method Options**: `deflate` (default)
- **Level Options**: `none` (default), `empty-block`, `fast`, `best`
- **Selección Recomendada AGENTE FORENSE**: `-c fast` (Balance óptimo entre throughput de adquisición I/O y tasa de compresión determinista).

---

## 6. HASH ALGORITHMS
- **Native Hashes**:
  - **MD5**: Siempre se calcula por defecto (`MD5 hash calculated over data`).
  - **Secondary Digest (`-d`)**: `sha1`, `sha256`.
- **Media Hash vs Container Hash**:
  - El stdout / log muestra `MD5 hash calculated over data` y `SHA256 hash calculated over data` (Hashes calculados sobre la totalidad de los datos crudos/medios leídos).
  - Los hashes de contenedores/secciones E01 son gestionados internamente dentro de la estructura de segmentos libewf.

---

## 7. SEGMENT SIZE & SINGLE-E01 FEASIBILITY
- **Segment Size Flag**: `-S <size>`
- **Supported Units**: `B` (bytes), `k` / `K` / `KiB`, `m` / `M` / `MiB`, `g` / `G` / `GiB` (Sintaxis exacta observada en libewf/ewfacquire). Nota: No soporta notación decimal como `1.5GiB`.
- **Default Segment Size**: `1.4 GiB` (1,500,000,000 bytes aprox, 1400MiB / 1.4G).
- **Single-E01 Strategy / No-Split**:
  - Pasar `-S 0` desactiva la segmentación por tamaño y fuerza a crear un único archivo `.E01` (o hasta el límite máximo de formato de 7.9 EiB para EnCase 6).
  - Validado empíricamente: `-S 0` generó únicamente `target.E01` sin generar `.E02`.
- **Feasibility Evaluation**: **SINGLE-E01 IS FEASIBLE AND GUARANTEED** cuando se invoca con `-S 0`, sujeto a que el sistema de archivos de destino no sea FAT32 (límite de 4 GB).

---

## 8. TARGET & SOURCE SEMANTICS
- **Target Flag**: `-t <target_basename>`
  - **Semántica**: Especifica la ruta base del archivo destino **sin extensión**.
  - `ewfacquire` añade automáticamente la extensión `.E01` (y `.E02`, etc. si se segmenta).
  - Ejemplo: `-t D:\Evidencias\NUE_12345_ESPECIE1_DSM1` genera `D:\Evidencias\NUE_12345_ESPECIE1_DSM1.E01`.
  - **Collision Behavior**: Si `target.E01` ya existe, `ewfacquire` en modo `-u` **no falla ni sobreescribe** si se completa una nueva adquisición, pero la regla de negocio de AGENTE FORENSE bloqueará la ejecución previa si existen artefactos preexistentes.
- **Source Semantics**:
  - **Sintaxis**: `source` al final del comando.
  - Para discos físicos en Windows: `\\.\PhysicalDriveN` (ejemplo `\\.\PhysicalDrive1`).
  - Para archivos RAW/dd de prueba: `path/to/image.raw`.

---

## 9. METADATA FLAGS
- `-C <case_number>`: Número de Caso / RUC.
- `-E <evidence_number>`: Número de Evidencia / NUE / Especie.
- `-e <examiner_name>`: Nombre del Examinador / Perito.
- `-D <description>`: Descripción de la Evidencia / DSM.
- `-N <notes>`: Notas adicionales de adquisición.
- `-m <media_type>`: `fixed` (default), `removable`, `optical`, `memory`.
- `-M <media_flags>`: `physical` (default), `logical`.

---

## 10. INTERACTIVE BEHAVIOR, STDIN, STDOUT, STDERR & ENCODING
- **Unattended Flag (`-u`)**:
  - **Totalmente No-Interactivo**: Con `-u`, `ewfacquire` no solicita ningún input por `stdin` si se le pasan los argumentos CLI requeridos (`-t`, `-f`, `-c`, `-d`, `-S`, `source`).
  - **STDIN**: Se mantiene cerrado/no utilizado en modo no-interactivo.
- **STDOUT**:
  - Contiene información de medios, progreso, hora de inicio/fin, bytes escritos y valores hash (`MD5 hash calculated over data: ...`, `SHA256 hash calculated over data: ...`, `ewfacquire: SUCCESS`).
- **STDERR**:
  - Contiene advertencias o errores nativos de libewf (ej. `Unsupported maximum segment size defaulting to...` o `Unable to open file(s) or device`).
- **Encoding**: Standard ASCII / CP1252 (Windows).
- **Exit Codes Observados**:
  - `0`: Éxito / Help (`-h`) / Version (`-V`).
  - `1`: Error de sintaxis / Argumentos faltantes / Dispositivo o archivo no encontrado / Falla de apertura.

---

## 11. PRIVILEGES & DESTINATION REQUIREMENTS
- **Privilegios de Ejecución**:
  - `-h`, `-V` y adquisiciones de archivos regulares ejecutan en espacio de usuario no elevado.
  - La lectura de `\\.\PhysicalDriveN` requerirá privilegios de Administrador (Windows Elevation / SeBackupPrivilege) durante el runtime de ejecución real.
- **Destination Validation Rules**:
  1. `destination_directory` debe existir y ser escribible.
  2. `destination_filesystem` debe ser validado (si FAT32 y tamaño disco > 4GB -> BLOQUEO).
  3. `destination_free_bytes` >= `source_disk_size_bytes * 1.05` (Margen de seguridad del 5%).
  4. `source_physical_drive` != `destination_physical_drive` (Validación física estricta vía R07.1).
  5. `target_basename.E01` y cualquier extensión relacionada no deben existir previante en el destino.

---

## 12. REVALIDATION CONTRACT WITH R07.1
Antes de autorizar y lanzar la invocación de `ewfacquire`, el orquestador debe re-ejecutar `HardwareDiscoveryService.get_system_disks()` para confirmar:
1. `DiskBinding` actual de R07.1 permanece vigente (`DISK_BINDING_READY`).
2. `IsReadOnly == True` en la política/filtro de seguridad de origen.
3. `IsSystem == False` y `IsBoot == False`.
4. El número de serie, modelo y tamaño del `PhysicalDrive` de origen coinciden exactamente con la foto de binding previa.
5. El disco físico que alberga el directorio de destino es distinto al `PhysicalDrive` de origen.

---

## 13. COMMAND BUILDER DESIGN (`EwfAcquireCommandBuilder`)
El componente `EwfAcquireCommandBuilder` generará una lista pura de argumentos (`List[str]`), evitando invocación por shell.

```python
class EwfAcquireCommandBuilder:
    def __init__(self, ewfacquire_path: str):
        self.ewfacquire_path = ewfacquire_path

    def build_command(
        self,
        source_path: str,
        target_basename: str,
        case_number: str,
        evidence_number: str,
        examiner: str,
        description: str,
        notes: str,
        compression: str = "fast",
        format_type: str = "encase6",
        digest: str = "sha256",
        segment_size: str = "0",
        log_file: str | None = None,
    ) -> list[str]:
        cmd = [
            self.ewfacquire_path,
            "-u",  # Unattended mode
            "-t", target_basename,
            "-f", format_type,
            "-c", compression,
            "-d", digest,
            "-S", segment_size,
            "-C", case_number,
            "-E", evidence_number,
            "-e", examiner,
            "-D", description,
            "-N", notes,
            "-m", "fixed",
            "-M", "physical",
        ]
        if log_file:
            cmd.extend(["-l", log_file])
        cmd.append(source_path)
        return cmd
```

---

## 14. HUMAN GATE
Antes de pasar a `ACQUIRING`, la interfaz/CLI presentará el Human Gate obligando a confirmación explícita del operador:

```text
================================================================================
                    HUMAN GATE: CONFIRMACIÓN DE ADQUISICIÓN E01
================================================================================
CASO / RUC        : {case_id}
NUE / EVIDENCIA   : {nue} / ESPECIE {especie_num}
DSM ID            : {dsm_id}
DISCO ORIGEN      : \\.\PhysicalDrive{drive_number}
  - Modelo        : {model}
  - Serie         : {serial}
  - Tamaño        : {size_bytes} bytes ({size_gb:.2f} GB)
  - Atributos     : ReadOnly={is_readonly} | System={is_system} | Boot={is_boot}
DESTINO BASE      : {target_basename}
  - Disco Destino : PhysicalDrive{dest_drive_number} ({dest_filesystem})
  - Espacio Libre : {free_bytes} bytes ({free_gb:.2f} GB)
BINARIO EWF      : {ewfacquire_path} (SHA256: {sha256_short})
CONFIGURACIÓN     : Formato={format} | Compresión={compression} | Hashes=MD5+{digest} | Segmento={segment_size} (Single-E01)
================================================================================
```

---

## 15. PERSISTED JOB MODEL & ACQUISITION.JSON DESIGN

### 15.1 Structure of `acquisition.json`
```json
{
  "job_id": "ACQ-20261008-001",
  "case_id": "CASO-2026-001",
  "dsm_id": "DSM-001",
  "binding_id": "BIND-88942-001",
  "source_snapshot": {
    "device_path": "\\\\.\\PhysicalDrive1",
    "serial_number": "XYZ123456",
    "size_bytes": 500107862016
  },
  "destination": "D:\\Evidencias\\NUE_1001_ESPECIE1_DSM1",
  "ewfacquire_path": "J:\\AgenteForense\\ewftools-x64\\ewfacquire.exe",
  "ewfacquire_sha256": "3cae1f37ece0b88746dc17810198b0171f4ca00ecb9c328e756baab5682e6791",
  "ewfacquire_version": "ewfacquire 20230405",
  "capabilities": {
    "single_e01": true,
    "hash_types": ["md5", "sha256"]
  },
  "format": "encase6",
  "compression": "fast",
  "hash_algorithms": ["md5", "sha256"],
  "segment_size": "0",
  "command_redacted": ["ewfacquire.exe", "-u", "-t", "...", "-f", "encase6", "..."],
  "started_at": "2026-10-08T12:00:00Z",
  "finished_at": "2026-10-08T12:35:10Z",
  "exit_code": 0,
  "generated_files": ["NUE_1001_ESPECIE1_DSM1.E01"],
  "generated_segment_count": 1,
  "status": "ACQUISITION_COMPLETED"
}
```

### 15.2 Log Design
Estructura de logs dentro de `ADQUISICION\<DSM_ID>\logs\`:
- `agent_acquisition.log`: Eventos del orquestador Python.
- `ewfacquire_native.log`: Archivo generado por `-l` de `ewfacquire`.
- `stdout.log`: Captura de stdout del subproceso.
- `stderr.log`: Captura de stderr del subproceso.

---

## 16. STATE MACHINE & POLICY ENGINE IMPACT
- **Nuevos Estados en State Machine**:
  - `ACQUISITION_READY`
  - `ACQUIRING`
  - `ACQUISITION_COMPLETED`
  - `FAILED`
  - `ABORTED`
- **Reglas del Policy Engine**:
  - `RULE_EWF_SINGLE_DISK_CHECK`: Origen != Destino.
  - `RULE_EWF_READONLY_SOURCE`: Origen ReadOnly confirmado.
  - `RULE_EWF_SPACE_CHECK`: Espacio libre >= 1.05 * Tamaño origen.
  - `RULE_EWF_NO_TARGET_COLLISION`: Inexistencia previa de `target_basename.E01`.

---

## 17. API / WEB DESIGN
Endpoints planned for future sprints (R08.1 / R09):
- `GET /api/v1/acquisition/readiness`: Revalida contrato R07.1 y espacio en disco.
- `POST /api/v1/acquisition/prepare`: Genera payload para Human Gate.
- `POST /api/v1/acquisition/confirm`: Recibe confirmación humana.
- `POST /api/v1/acquisition/start`: Inicia job persistente en background (`subprocess.Popen`).
- `GET /api/v1/acquisition/job/{job_id}`: Consulta estado y tail de logs.
- `POST /api/v1/acquisition/cancel/{job_id}`: Termina el proceso (`SIGTERM` / `terminate()`) y pasa a `ABORTED`.

---

## 18. DEPENDENCIES FOR R08.1
- Implementación de `EwfAcquireCommandBuilder`.
- Implementación de `EwfAcquireJobManager` para control de procesos y persistencia de `acquisition.json`.
- Integración de validaciones pre-flight de destino y espacio.

---

## 19. RISKS & BLOCKERS
- **Risks**:
  - Intentar adquisición en discos con sectores defectuosos sin configurar adecuadamente `-r` (retries) y `-w` (zero-fill).
  - Sistemas de archivos destino FAT32 que causen fallos al superar 4 GB con `-S 0`.
- **Blockers**: Ninguno identificado. `ewfacquire.exe` responde adecuadamente en el entorno local.

---

## 20. CONCLUSION & STATUS
Todos los objetivos de caracterización, descubrimiento de capabilities y diseño de integración para `ewfacquire.exe` han sido cumplidos sin ejecutar ninguna adquisición física real ni modificar evidencias.

**ESTADO FINAL**:
```text
EWFACQUIRE_CAPABILITIES_VERIFIED
```
