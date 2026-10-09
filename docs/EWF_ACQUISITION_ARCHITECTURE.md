# EWF Acquisition Architecture (Sprint R08.1)

## Resumen Arquitectónico
El motor de adquisición física E01 del **AGENTE FORENSE** proporciona una arquitectura determinista, no interactiva y de fail-closed para la adquisición forense de evidencias utilizando `ewfacquire.exe`.

## Componentes Principales
1. **Capabilities (`EwfBinaryVerifier`)**:
   - Localiza `ewfacquire.exe` en `J:\AgenteForense\ewftools-x64\ewfacquire.exe`.
   - Verifica el hash SHA-256 estricto (`3cae1f37ece0b88746dc17810198b0171f4ca00ecb9c328e756baab5682e6791`).
   - Aborta de forma fail-closed con `EwfBinaryChangedError` si el binario no coincide.

2. **Command Builder (`EwfAcquireCommandBuilder`)**:
   - Construye listas puras de argumentos CLI (`List[str]`).
   - Forzado de parámetros forenses: `-u` (no interactivo), `-f encase6`, `-c best`, `-d sha256`, `-S 0` (Single E01).

3. **Preflight & Destination Validation (`revalidate_source_disk`, `DestinationValidator`)**:
   - Revalida el origen físico (R07.1) asegurando `is_read_only=True`, `is_system=False`, `is_boot=False` y coincidencia de número de serie.
   - Verifica que el espacio libre en el destino supere la capacidad raw del disco fuente.
   - Previene colisiones de nombres y bloquea la adquisición si el destino coincide con el disco físico de origen.

4. **Human Gate (`confirm_human_gate`)**:
   - Exige la confirmación explícita mediante el texto exacto `"ADQUIRIR"`. Cualquier otro valor aborta el trabajo.

5. **Runner & Durable Job Management (`EwfAcquireRunner`, `AcquisitionJobManager`)**:
   - Invocación mediante subproceso `Popen` desacoplado con captura de `stdout`, `stderr` y logs nativos (`-l`).
   - Persistencia durable del ciclo de vida en PostgreSQL (`forensic.acquisition_jobs` y `forensic.acquisitions`).
   - Recovery automático tras reinicio inesperado (`PROCESS_MISSING_REVIEW_REQUIRED`).

6. **Artefactos Forenses (`AcquisitionArtifactsManager`)**:
   - Escritura atómica de `acquisition.json`.
   - Reconciliación atómica de `case.json` (`CaseJsonService`).
