# AGENTE FORENSE — ROADMAP MAESTRO DE RECONSTRUCCIÓN DESDE CERO

## 0. Estado de partida

Este roadmap parte de las siguientes condiciones reales:

- El código fuente anterior se considera perdido.
- La suite de tests anterior se considera perdida.
- La reconstrucción se realiza **FROM_SCRATCH**.
- Los sprints históricos se conservan únicamente como documentación y fuente de requisitos/decisiones.
- El producto objetivo es un **Agente Forense local, persistente, auditable, fail-closed y end-to-end**, con interfaz web en localhost.
- PostgreSQL será la base de datos principal **si la inspección real de la instalación confirma versión, servicio, conectividad, autenticación y disponibilidad compatibles**.
- Los archivos del caso se almacenarán en filesystem controlado; la E01 queda fuera de PostgreSQL por volumen, pero se registra completamente por nombre, ruta, tamaño, hashes, estado y trazabilidad.
- `case.json` se conserva como representación portable/snapshot del caso individual.
- La base de datos global mantiene la memoria operacional estructurada de todos los casos.
- El agente podrá aprender workflows, reglas, plantillas y feedback mediante memoria estructurada/RAG; no se reentrenarán automáticamente pesos de un modelo con cada caso.

## 1. Visión final

```text
OPERADOR
   │
   ▼
WEB LOCALHOST
   │
   ├── carga OFICIO PETITORIO
   ├── carga FOTOGRAFÍAS
   ├── revisa/excepciona datos cuando corresponda
   └── ordena INICIAR PERITAJE
   │
   ▼
FORENSIC API / ORQUESTADOR
   │
   ├── STATE ENGINE
   ├── POLICY ENGINE
   ├── AUDIT ENGINE
   ├── MEMORY / RAG
   └── HUMAN APPROVAL GATE
   │
   ▼
POSTGRESQL + FILE STORE + case.json
   │
   ▼
PETITORIO → IDENTIFICACIÓN → ADQUISICIÓN → VERIFICACIÓN
   │
   ▼
AXIOM PROCESS → AXIOM EXPERT → PORTABLE → RAR → HASH
   │
   ▼
INFORME WORD FINAL
```

## 2. Contratos permanentes

### 2.1 Modelo jerárquico

```text
RUC
└── NUE
    └── ESPECIE
        └── DSM
```

- RUC = caso.
- NUE = evidencia.
- ESPECIE = objeto físico.
- DSM = medio/dispositivo de almacenamiento digital.
- Deben mantenerse `SELF_STORAGE` y `CONTAINED_STORAGE`.
- El nombre futuro de E01 debe derivar del DSM, por ejemplo:

```text
NUE_<NUE>_ESPECIE<n>_DSM<m>.E01
```

### 2.2 Persistencia

Tres capas:

```text
PostgreSQL
= memoria operacional global y relaciones

case.json
= snapshot portable y contrato del caso

filesystem controlado
= petitorios, fotos, XLSX, logs, informes, Portable, RAR, E01, etc.
```

La E01 no se guarda dentro de PostgreSQL.

### 2.3 Seguridad

- No modificar evidencia.
- Nunca admitir `IsSystem=True`.
- Nunca admitir `IsBoot=True`.
- Para adquisición física real: `IsReadOnly=True`.
- No seleccionar origen por letra de unidad.
- Origen físico: `\\.\PhysicalDriveN`.
- No formatear, inicializar, reparar, cambiar atributos, particionar ni escribir en el origen.
- Fail-closed ante ambigüedad material.
- Operaciones críticas auditadas.
- El LLM no sustituye al Policy Engine.

### 2.4 Aprendizaje

El agente aprende:

- procedimientos;
- workflows;
- reglas;
- plantillas;
- patrones de informes;
- feedback del perito;
- conocimiento AXIOM;
- documentación oficial;
- contexto operacional.

No aprende como hechos globales:

- seriales de otros casos;
- nombres;
- fechas;
- hashes;
- conclusiones particulares;
- datos probatorios de un caso anterior.

---

# 3. ROADMAP POR SPRINT

## SPRINT R00 — Reinicialización técnica controlada

### Objetivo
Crear el baseline real de reconstrucción.

### Alcance
- Confirmar repositorio, branch, commit y estado Git.
- Confirmar que no existe código recuperado.
- Confirmar Python disponible.
- Crear paquete Python mínimo.
- Crear nueva suite de tests desde 0.
- Crear `RECONSTRUCTION_STATUS.md`.
- Centralizar configuración de rutas.
- No ejecutar ninguna operación forense.
- No tocar evidencia real.
- Resolver/documentar discrepancias históricas de rutas G:/J:.

### Resultado
```text
RECONSTRUCTION_BASELINE_READY
```

---

## SPRINT R01 — Infraestructura de persistencia: PostgreSQL + File Store

### Investigación previa obligatoria
Verificar en la máquina real:

- versión exacta de PostgreSQL;
- servicio Windows;
- `psql`;
- puerto;
- autenticación;
- bases existentes;
- usuario técnico a utilizar;
- permisos;
- política de backup;
- encoding/locale;
- comportamiento transaccional requerido;
- driver Python compatible.

### Objetivo
Crear la persistencia base del Agente Forense.

### Implementar
- conexión PostgreSQL;
- configuración segura mediante entorno/config local;
- migraciones;
- repositorios;
- transacciones;
- audit log básico;
- File Store controlado;
- hashing SHA-256 de archivos ingresados;
- identificadores internos;
- timestamps UTC/local claramente definidos;
- esquema inicial.

### Tablas base
- `cases`
- `nues`
- `species`
- `dsms`
- `documents`
- `files`
- `photos`
- `hashes`
- `case_events`
- `audit_events`
- `tool_versions`

### Resultado
```text
PERSISTENCE_FOUNDATION_READY
```

---

## SPRINT R02 — API local + interfaz web localhost

### Objetivo
Construir la primera interfaz oficial del producto.

### Implementar
- backend/API local;
- binding restringido a localhost por defecto;
- health check;
- dashboard;
- formulario "Nuevo caso";
- carga documental;
- carga fotográfica;
- visualización de estados;
- manejo de errores comprensible;
- consulta de auditoría;
- tests de API/UI básicos.

### No implementar todavía
- adquisición real;
- AXIOM;
- razonamiento autónomo.

### Resultado
```text
LOCAL_WEB_FOUNDATION_READY
```

---

## SPRINT R03 — Modelo de dominio RUC → NUE → ESPECIE → DSM

### Objetivo
Implementar el modelo forense central desde cero.

### Implementar
- RUC;
- múltiples NUE por RUC;
- múltiples especies;
- múltiples DSM;
- `SELF_STORAGE`;
- `CONTAINED_STORAGE`;
- reglas de integridad;
- `CaseStructureDraft`;
- creación de estructura física;
- `case.json`;
- sincronización PostgreSQL ↔ `case.json`;
- rebuild controlado de índice desde `case.json`;
- nomenclatura E01 futura por DSM.

### Resultado
```text
CASE_DOMAIN_READY
```

---

## SPRINT R04 — Máquina de estados + Policy Engine + Orquestador base

### Objetivo
Crear el cerebro determinista del workflow.

### Implementar
- state machine persistente;
- transiciones válidas;
- Policy Engine;
- permisos;
- Human Approval Gateway;
- job model;
- reanudación después de reinicio;
- locking por caso/DSM;
- event log append-only;
- cálculo de `next_action`.

### Estados iniciales
Incluir, según diseño final:

- NEW
- PETITION_PENDING
- PETITION_REVIEW
- IDENTIFICATION_PENDING
- IDENTIFICATION_COMPLETED
- ACQUISITION_READY
- ACQUIRING
- ACQUISITION_COMPLETED
- ACQUISITION_VERIFIED
- ANALYSIS_PENDING
- PROCESSING_AXIOM
- ANALYSIS_COMPLETED
- RESULTS_PENDING
- PORTABLE_CREATED
- REPORT_PENDING
- REPORT_GENERATED
- COMPLETED
- FAILED
- ABORTED

### Resultado
```text
ORCHESTRATION_CORE_READY
```

---

## SPRINT R05 — Oficio Petitorio: ingestión, OCR y extracción estructurada

### Objetivo
Convertir el oficio petitorio en entrada semántica principal del caso.

### Pipeline
```text
PETITORIO
→ almacenamiento original
→ SHA-256
→ OCR
→ texto bruto
→ extracción estructurada
→ validación determinista
→ CaseStructureDraft
→ revisión solo si hay conflicto/ambigüedad
```

### Intentar extraer
- RUC;
- RUT u otros identificadores presentes;
- unidad solicitante;
- NUE(s);
- descripción de evidencia;
- diligencias solicitadas;
- preguntas periciales;
- fechas relevantes;
- referencias administrativas.

### Regla
El OCR no crea hechos definitivos sin validación.

### Resultado
```text
PETITION_INGESTION_READY
```

---

## SPRINT R06 — Identificación fotográfica asistida

### Objetivo
Identificar físicamente ESPECIE/DSM usando fotos.

### Pipeline
```text
FOTOS
→ hash
→ OCR
→ observaciones
→ propuesta estructurada
→ validación anti-invención
→ correlación con petitorio
→ revisión humana solo si es necesaria
→ identificación persistida
```

### Campos
- tipo;
- marca;
- modelo;
- serial;
- capacidad;
- etiquetas visibles;
- relación ESPECIE/DSM;
- fuente fotográfica de cada valor.

### Resultado
```text
IDENTIFICATION_READY
```

---

## SPRINT R07 — Detección segura de discos y asociación DSM ↔ PhysicalDrive

### Investigación previa
Verificar comportamiento real de Windows/PowerShell y ambiente.

### Objetivo
Detectar y presentar únicamente candidatos forenses válidos.

### Reglas
- `IsReadOnly=True`;
- `IsSystem=False`;
- `IsBoot=False`;
- origen ≠ disco físico de destino;
- registrar Number, FriendlyName, SerialNumber, Size, BusType y estados;
- no escribir en el medio;
- correlacionar dispositivo técnico con DSM del caso.

### Resultado
```text
ACQUISITION_SOURCE_READY
```

---

## SPRINT R08 — Investigación e integración real de ewfacquire

### Investigación previa
Obligatoria sobre el binario local real:

- ruta;
- versión;
- `-h`;
- flags;
- compresión;
- segmentación;
- exit codes;
- logs;
- comportamiento single-E01;
- límites reales.

### Objetivo
Implementar adquisición E01 determinista y auditada.

### Resultado
```text
E01_ACQUISITION_READY
```

---

## SPRINT R09 — Verificación EWF independiente

### Investigación previa
Verificar `ewfverify` real y semántica exacta.

### Implementar
- verificación independiente;
- hashes;
- reconciliación acquisition vs verification;
- metadata;
- estados;
- errores;
- transición automática a `ANALYSIS_PENDING` solo si corresponde.

### Resultado
```text
EWF_VERIFICATION_READY
```

---

## SPRINT R10 — Investigación AXIOM y decisión de automatización

### Objetivo
NO automatizar todavía. Determinar cómo puede automatizarse realmente la versión instalada.

### Investigar
- versión exacta de Magnet AXIOM;
- Process;
- Examine;
- APIs;
- CLI;
- mecanismos oficiales;
- Magnet AUTOMATE si existe/licenciado;
- automatización soportada;
- creación de caso;
- incorporación E01;
- selección de artefactos;
- inicio de procesamiento;
- monitoreo;
- Portable Case;
- exportaciones;
- filtros;
- categorías;
- etiquetas;
- posibilidades de automatización de Examine.

### Salida
Documento de capabilities y estrategia oficial.

### Resultado
```text
AXIOM_AUTOMATION_STRATEGY_DEFINED
```

---

## SPRINT R11 — AXIOM Process: creación y procesamiento automático

### Objetivo
Automatizar el ciclo Process.

### Implementar según R10
- crear/abrir caso;
- agregar E01 verificada;
- aplicar workflow;
- iniciar procesamiento;
- monitorizar;
- persistir job;
- sobrevivir reinicios;
- capturar errores/advertencias;
- registrar versión/configuración;
- exportar datos estructurados requeridos.

### Resultado
```text
AXIOM_PROCESS_AUTOMATION_READY
```

---

## SPRINT R12 — AXIOM Expert Knowledge Base

### Objetivo
Convertir al agente en experto consultable de AXIOM.

### Fuentes
- manual oficial correspondiente a la versión instalada;
- documentación oficial;
- procedimientos internos;
- workflows validados;
- catálogo de etiquetas;
- feedback del perito.

### Implementar
- RAG local;
- indexación versionada;
- source citations internas;
- version mismatch;
- knowledge provenance;
- consultas del agente.

### Regla
El manual enseña cómo funciona AXIOM; el perito enseña cómo trabaja la organización.

### Resultado
```text
AXIOM_KNOWLEDGE_READY
```

---

## SPRINT R13 — AXIOM Examine asistido: filtros, categorías, etiquetas y relevancia

### Objetivo
Iniciar análisis experto asistido.

### Implementar incrementalmente
- lectura de resultados;
- filtros;
- categorías;
- etiquetas;
- workflows;
- propuestas `RELEVANTE / NO_RELEVANTE / REVISAR`;
- explicación de la propuesta;
- feedback humano persistente;
- trazabilidad de cada decisión.

### Regla
No eliminar ni ocultar evidencia por decisión libre del LLM.

### Resultado
```text
AXIOM_EXPERT_ASSISTED_READY
```

---

## SPRINT R14 — Portable Case + RAR + hashes

### Investigación previa
Verificar herramienta RAR real instalada:

- WinRAR/rar.exe u otra;
- versión;
- CLI;
- flags;
- exit codes;
- método;
- comportamiento real.

### Implementar
- creación/exportación Portable;
- preservar Portable original;
- compresión RAR;
- SHA-256 del RAR;
- tamaño;
- versión herramienta;
- timestamps;
- auditoría;
- persistencia.

### Resultado
```text
RESULTS_PACKAGE_READY
```

---

## SPRINT R15 — Generador de informe Word

### Objetivo
Generar el informe final siguiendo informes históricos reales.

### Entradas
- petitorio;
- identificación;
- fotos;
- adquisición;
- E01;
- hashes;
- AXIOM;
- resultados;
- Portable;
- RAR;
- auditoría;
- plantillas/peritajes históricos.

### Implementar
- perfil documental aprendido/validado;
- fotografías;
- tablas;
- hashes;
- metodología;
- resultados;
- conclusiones sustentadas;
- trazabilidad;
- DOCX listo para revisión/impresión.

### Resultado
```text
REPORT_GENERATION_READY
```

---

## SPRINT R16 — Memoria persistente y aprendizaje operacional

### Objetivo
Transformar feedback y experiencia en conocimiento reutilizable.

### Separar
```text
FORENSIC DATA
= hechos de casos

KNOWLEDGE
= procedimientos reutilizables
```

### Persistir
- workflows;
- reglas;
- etiquetas;
- decisiones confirmadas;
- feedback;
- patrones de informes;
- patrones AXIOM;
- conocimiento versionado.

### No realizar
- fine-tuning automático por caso;
- contaminación cruzada de hechos.

### Resultado
```text
OPERATIONAL_MEMORY_READY
```

---

## SPRINT R17 — Runtime de agente / evaluación OpenClaw

### Objetivo
Evaluar si OpenClaw u otro runtime de agente aporta valor sin debilitar el núcleo forense.

### Investigar
- ejecución local Windows;
- localhost;
- memoria;
- tools/skills;
- permisos;
- approvals;
- long-running jobs;
- filesystem restrictions;
- integración Python/API;
- Ollama;
- capacidad de limitar comandos.

### Decisión
Una de:

```text
USE_OPENCLAW_AS_AGENT_RUNTIME
```

o

```text
KEEP_NATIVE_ORCHESTRATOR
```

### Regla
El runtime nunca sustituye Policy Engine, State Engine, Database ni Audit Engine.

### Resultado
```text
AGENT_RUNTIME_DECISION_COMPLETE
```

---

## SPRINT R18 — Agente conversacional local

### Objetivo
Permitir órdenes naturales desde la web.

Ejemplos:

```text
"Procesa este caso."
"Continúa la pericia."
"Muéstrame qué falta."
"¿Qué casos están pendientes de informe?"
"Busca los DSM Samsung de 1 TB."
```

### Implementar
- Qwen/Ollama u otro modelo local verificado;
- tool calling controlado;
- consultas a PostgreSQL mediante capa segura;
- RAG;
- explicaciones;
- permisos;
- no shell libre;
- no SQL libre generado contra producción.

### Resultado
```text
FORENSIC_CHAT_READY
```

---

## SPRINT R19 — Workflow autónomo end-to-end

### Objetivo
Ejecutar un caso completo desde ingreso hasta informe.

### Flujo
```text
PETITORIO + FOTOS + DSM CONECTADO
        ↓
EXTRACCIÓN
        ↓
CREACIÓN CASO
        ↓
IDENTIFICACIÓN
        ↓
DETECCIÓN DSM
        ↓
ADQUISICIÓN
        ↓
VERIFICACIÓN
        ↓
AXIOM PROCESS
        ↓
AXIOM EXPERT
        ↓
PORTABLE
        ↓
RAR
        ↓
HASH
        ↓
DOCX
        ↓
REVISIÓN FINAL
```

### Human-in-the-loop
Solo cuando:
- hay conflicto;
- hay ambigüedad;
- falla una política;
- hay riesgo de seleccionar el DSM incorrecto;
- una acción crítica requiere autorización según política;
- revisión final del informe.

### Resultado
```text
END_TO_END_AUTONOMY_READY
```

---

## SPRINT R20 — Hardening, recuperación y operación de laboratorio

### Objetivo
Preparar operación estable.

### Implementar/probar
- backup PostgreSQL;
- restore;
- reconstrucción desde `case.json`;
- recuperación de jobs;
- reinicio Windows;
- caída AXIOM;
- caída PostgreSQL;
- espacio insuficiente;
- archivos parciales;
- hash mismatch;
- logging rotativo;
- seguridad localhost;
- cuentas/roles;
- pruebas de desastre;
- documentación operacional.

### Resultado
```text
PRODUCTION_LAB_READY
```

---

# 4. Regla de ejecución de este roadmap

Este archivo NO autoriza ejecutar todos los sprints seguidos.

Para cada sprint:

1. leer `PROMPT_MAESTRO.md`;
2. leer `REGLA_PERMANENTE_PRE_SPRINT.md`;
3. leer este roadmap;
4. leer el informe final del sprint anterior;
5. inspeccionar el repositorio real;
6. inspeccionar herramientas/versiones reales involucradas;
7. investigar documentación primaria;
8. redactar el sprint técnico detallado;
9. ejecutarlo;
10. ejecutar tests;
11. revisar seguridad;
12. entregar informe final;
13. detener;
14. solo después diseñar el siguiente sprint.

Si falta información material:

```text
DETENER
INVESTIGAR
DOCUMENTAR
NO INVENTAR
```

# 5. Principio final

El objetivo no es construir scripts desconectados.

El producto final es:

> **Un Agente Forense local, persistente, auditable y autónomo, operado desde una interfaz web localhost, alimentado por petitorios y fotografías, capaz de administrar RUC/NUE/ESPECIE/DSM, ejecutar adquisición y verificación forense, automatizar y comprender AXIOM, generar resultados/Portable/RAR/hash, aprender workflows mediante memoria estructurada y producir un informe Word final trazable y listo para revisión.**
