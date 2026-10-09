# SPRINT_R08_2 — Validación Física Controlada de Adquisición E01

## 1. Objetivo
Validar el motor de R08.1 mediante una única adquisición física real controlada sobre un medio de laboratorio conectado mediante write-blocker.

Flujo:
```text
DSM lógico
→ binding confirmado
→ PhysicalDrive real read-only
→ preflight
→ Human Gate
→ ewfacquire real
→ E01 real
→ logs/hashes/metadata
→ ACQUISITION_COMPLETED
```

Estado esperado:
```text
REAL_ACQUISITION_VALIDATED
```
o:
```text
REAL_ACQUISITION_REJECTED
```

No ejecutar `ewfverify`.

## 2. Documentación obligatoria
Leer completos:
```text
PROMPT_MAESTRO.md
REGLA_PERMANENTE_PRE_SPRINT.md
SPRINT_R07_1.md
SPRINT_R08.md
SPRINT_R08_1.md
SPRINT_R08_2.md
DISK_BINDING_ARCHITECTURE.md
EWFACQUIRE_CAPABILITIES.md
EWF_ACQUISITION_ARCHITECTURE.md
ACQUISITION_JOB_SCHEMA.md
ACQUISITION_JSON_SCHEMA.md
```

## 3. Baseline
Esperado:
```text
227 passed
EWF_ACQUISITION_ENGINE_READY
DISK_BINDING_READY
```

Si hay regresión: detener y no adquirir.

## 4. Medio permitido
Usar exclusivamente medio de laboratorio, NO evidencia real.

Preferir dispositivo pequeño:
```text
pendrive
SSD/HDD de laboratorio
```

Debe conectarse mediante write-blocker físico si ese es el flujo operacional previsto.

## 5. Condición crítica
Antes de continuar:
```text
IsReadOnly = True
IsSystem   = False
IsBoot     = False
```

Si `IsReadOnly=False`:
```text
REAL_ACQUISITION_REJECTED
```

No cambiar atributos. No ejecutar `Set-Disk`.

## 6. Binding real
Debe existir:
```text
CONFIRMED_BINDING
DISK_BINDING_CURRENT
```

No adquirir PhysicalDrive huérfano.

## 7. Revalidación inmediata
Comparar:
```text
disk_number
physical_drive
serial_number
unique_id
size_bytes
is_read_only
is_system
is_boot
```

Cambio crítico:
```text
SOURCE_CHANGED
```
y abortar.

## 8. Destino
Validar:
```text
filesystem
writable
free_bytes >= source_size_bytes
source physical disk != destination physical disk
target absent
```

No formatear.

## 9. Configuración ewfacquire
Usar:
```text
version: 20230405
format: encase6
compression: best
digest: sha256
segment strategy: -S 0
unattended: -u
shell=False
```

Binario:
```text
J:\AgenteForense\ewftools-x64\ewfacquire.exe
```

SHA-256 esperado:
```text
3cae1f37ece0b88746dc17810198b0171f4ca00ecb9c328e756baab5682e6791
```

Si cambia: abortar.

## 10. Human Gate
Mostrar resumen completo y exigir entrada manual exacta:
```text
ADQUIRIR
```

No autogenerarla.

## 11. Adquisición real
Ejecutar una sola vez.

Capturar:
```text
job_id
pid
started_at
finished_at
exit_code
stdout
stderr
native log
```

No repetir adquisición si la primera es válida.

## 12. Seguridad
No ejecutar:
```text
Set-Disk
DiskPart
CHKDSK
format
initialize
repair
```

No escribir al origen.

## 13. Resultado esperado
Debe existir exactamente:
```text
NUE_<NUE>_ESPECIE<n>_DSM<m>.E01
```

Debe tener tamaño > 0.

No deben aparecer:
```text
.E02
.E03
...
```

Si aparecen:
```text
UNEXPECTED_SEGMENTATION
```
y resultado REJECTED.

No borrar segmentos.

## 14. Hashes
Registrar los hashes reportados por ewfacquire:
```text
MD5
SHA256
```

No ejecutar todavía `ewfverify`.

## 15. acquisition.json
Verificar que incluya:
```text
case_id
ruc
nue
species
dsm
binding_id
source_snapshot
destination
ewfacquire path/version/hash
format
compression
hashes requested
segment strategy
human confirmation
job_id
pid
timestamps
exit_code
generated files
segment count
reported hashes
status
```

## 16. case.json
Al finalizar correctamente:
```text
acquisition.status = ACQUISITION_COMPLETED
```

Nunca `ACQUISITION_VERIFIED`.

## 17. PostgreSQL
Verificar coherencia con:
```text
forensic.acquisition_jobs
forensic.acquisitions
forensic.audit_events
```

## 18. Auditoría
Comprobar:
```text
ACQUISITION_PREPARED
ACQUISITION_CONFIRMATION_REQUESTED
ACQUISITION_CONFIRMED
ACQUISITION_STARTED
ACQUISITION_COMPLETED
```

## 19. Pruebas negativas sin nueva adquisición
Después de la adquisición real, validar sin repetir operación física:
- `IsReadOnly=False` bloquea.
- destino en mismo PhysicalDrive bloquea.
- target `.E01` preexistente bloquea.
- `SOURCE_CHANGED` bloquea.

## 20. Artefactos parciales
Si falla/cancela:
- preservar E01 parcial;
- preservar logs;
- preservar metadata;
- preservar audit;
- no borrar silenciosamente.

## 21. Tests finales
Ejecutar suite completa.

Esperado:
```text
227 passed
```
o más.

## 22. No realizar
No ejecutar:
```text
ewfverify
AXIOM
Ollama
OpenClaw
Portable
RAR
Word
```

No usar evidencia real.

## 23. Criterio de aceptación
Aceptar solo si:
- baseline verde;
- medio de laboratorio;
- binding confirmado;
- Windows reporta read-only;
- system/boot false;
- binario hash coincide;
- Human Gate manual;
- exit code compatible con éxito;
- exactamente un `.E01`;
- E01 > 0 bytes;
- hashes registrados;
- acquisition.json coherente;
- case.json = ACQUISITION_COMPLETED;
- auditoría completa;
- origen no modificado;
- suite final verde.

Resultado:
```text
REAL_ACQUISITION_VALIDATED
```

## 24. Reporte final obligatorio
```text
SPRINT R08.2:
COMPLETADO / REJECTED / BLOCKED

BASELINE:
...
TESTS BEFORE:
...
LAB MEDIUM:
Type:
Model:
Serial:
Size:
WRITE BLOCKER:
Used:
Observed Windows ReadOnly:
DSM:
...
BINDING:
...
SOURCE:
PhysicalDrive:
IsReadOnly:
IsSystem:
IsBoot:
DESTINATION:
Path:
Filesystem:
Free bytes:
PhysicalDrive:
EWFACQUIRE:
Path:
Version:
SHA256:
Hash match:
COMMAND SUMMARY:
...
HUMAN CONFIRMATION:
ADQUIRIR entered manually: YES / NO
JOB:
ID:
PID:
Start:
End:
Exit code:
E01:
Path:
Size:
Segments:
HASHES REPORTED:
MD5:
SHA256:
STDOUT:
...
STDERR:
...
NATIVE LOG:
...
ACQUISITION.JSON:
VALID / INVALID
CASE.JSON:
...
POSTGRESQL:
...
AUDIT:
...
NEGATIVE TESTS:
ReadOnly false:
Same disk destination:
Target collision:
Source changed:
SOURCE MODIFIED:
NO / YES / UNKNOWN
SET-DISK:
NO
DISKPART:
NO
EWFVERIFY:
NO
AXIOM:
NO
REAL EVIDENCE:
NO
TESTS FINAL:
...
RISKS:
...
OBSERVATIONS:
...
STATUS:
REAL_ACQUISITION_VALIDATED / REAL_ACQUISITION_REJECTED / REAL_ACQUISITION_BLOCKED
```

## 25. Instrucción final
TRAE:
1. lee documentación vigente;
2. ejecuta baseline;
3. prepara caso y DSM de laboratorio;
4. conecta medio mediante write-blocker;
5. verifica read-only;
6. confirma binding;
7. valida destino;
8. verifica hash de ewfacquire;
9. muestra resumen;
10. espera ingreso manual exacto `ADQUIRIR`;
11. ejecuta una sola adquisición real;
12. inspecciona artefactos;
13. conserva cualquier parcial;
14. ejecuta pruebas negativas sin repetir adquisición;
15. ejecuta suite final;
16. entrega reporte;
17. detente;
18. NO ejecutes `ewfverify`;
19. NO inicies R09.

Comienza ahora.
