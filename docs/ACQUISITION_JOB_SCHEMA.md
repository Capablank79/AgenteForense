# Schema: `forensic.acquisition_jobs` & `forensic.acquisitions`

## Tabla `forensic.acquisition_jobs`
Registra la ejecución detallada de cada trabajo de adquisición.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | UUID | Clave primaria. |
| `job_id` | VARCHAR(128) | Identificador único del trabajo (`JOB-...`). |
| `acquisition_id` | UUID | Referencia a `forensic.acquisitions`. |
| `case_id` | UUID | Referencia a `forensic.cases`. |
| `dsm_id` | UUID | Referencia a `forensic.dsms`. |
| `binding_id` | UUID | Referencia a `forensic.dsm_disk_bindings`. |
| `status` | VARCHAR(64) | Estado del ciclo de vida (`PREPARED`, `WAITING_CONFIRMATION`, `STARTING`, `RUNNING`, `COMPLETED`, `FAILED`, `ABORTED`). |
| `pid` | INTEGER | PID del subproceso `ewfacquire.exe`. |
| `command_json` | JSONB | Lista de argumentos CLI ejecutados. |
| `stdout_path` | TEXT | Ruta al archivo de captura `stdout.log`. |
| `stderr_path` | TEXT | Ruta al archivo de captura `stderr.log`. |
| `native_log_path` | TEXT | Ruta al archivo de log nativo `native.log` (`-l`). |
| `started_at` | TIMESTAMPTZ | Fecha/hora de inicio de ejecución. |
| `finished_at` | TIMESTAMPTZ | Fecha/hora de finalización. |
| `exit_code` | INTEGER | Código de salida devuelto por `ewfacquire.exe`. |
| `error_code` | VARCHAR(128) | Código de error unificado. |
| `human_confirmation_exact` | VARCHAR(64) | Texto de confirmación recibido (debe ser `"ADQUIRIR"`). |
| `human_confirmed_at` | TIMESTAMPTZ | Fecha/hora de confirmación humana. |
| `operator` | VARCHAR(128) | Identificador del operador forense. |
| `details` | JSONB | Detalles adicionales de ejecución y rutas de destino. |
| `created_at` | TIMESTAMPTZ | Timestamp de creación. |
| `updated_at` | TIMESTAMPTZ | Timestamp de última actualización. |
