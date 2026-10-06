# REGLA_PERMANENTE_PRE_SPRINT.md

# Regla permanente — Investigación previa obligatoria antes de crear sprints

Esta sección debe incorporarse permanentemente a `PROMPT_MAESTRO.md`.

## Regla principal

**NO crear, aprobar ni ejecutar un sprint técnico sin investigar previamente todo lo necesario para que sus requisitos sean compatibles con la herramienta, versión, formato, entorno y comportamiento real involucrados.**

No construir criterios críticos sobre supuestos verificables.

## Antes de redactar cualquier sprint

Revisar, según corresponda:

1. estado actual del repositorio;
2. `PROMPT_MAESTRO.md`;
3. sprints anteriores y reportes finales;
4. suite de tests actual;
5. herramientas realmente instaladas;
6. versión exacta;
7. ayuda local;
8. documentación técnica primaria;
9. código fuente oficial si es necesario;
10. semántica real de flags;
11. semántica real de outputs;
12. hashes, estados y exit codes;
13. diferencias entre versiones;
14. casos límite;
15. criterios reales de éxito/fallo;
16. datos observados vs almacenados vs calculados vs inferidos;
17. información que la herramienta realmente puede producir;
18. riesgos forenses y de seguridad;
19. dependencias con fases futuras;
20. pruebas automatizadas y reales requeridas.

## Jerarquía de fuentes

Para comportamiento de herramientas:

1. binario local y ayuda local;
2. salida real capturada;
3. documentación oficial/primaria;
4. código fuente oficial;
5. documentación secundaria como apoyo.

Si hay discrepancia, no asumir: documentar y resolver antes de cerrar el sprint.

## Criterios de aceptación

Todo criterio crítico debe tener justificación técnica.

No exigir:

- campos inexistentes;
- etiquetas que una versión no utiliza;
- algoritmos no soportados;
- redundancias sin valor técnico;
- operaciones incompatibles con la semántica real de la herramienta.

Fail-closed significa:

**rechazar ante evidencia insuficiente, contradictoria o insegura.**

No significa:

**inventar requisitos imposibles o innecesarios.**

## Regla de detención

Si falta información material:

**NO crear todavía el sprint. Investigar primero.**

## Checklist obligatorio antes de entregar un sprint

Responder:

- ¿Conozco la versión real?
- ¿Conozco la semántica real de sus opciones?
- ¿Conozco el output real o esperado?
- ¿Los criterios de aceptación pueden cumplirse?
- ¿Los criterios de fallo representan fallos reales?
- ¿Hay alguna exigencia inventada o redundante?
- ¿Revisé los resultados previos?
- ¿Se preserva la evidencia?
- ¿Se evita trabajo forense innecesario/repetido?
- ¿Los tests cubren la semántica real?
- ¿Existe auditabilidad suficiente?

Si una respuesta material es `NO`, el sprint no está listo.

## Corrección de errores conceptuales

Si un sprint descubre que una política anterior estaba mal definida:

1. conservar el error en auditoría;
2. no ocultarlo;
3. corregir la política;
4. evitar repetir operaciones forenses si los artefactos existentes permiten reconciliar;
5. agregar tests que eviten recurrencia.

Esta regla aplica permanentemente a todos los sprints futuros del proyecto AGENTE FORENSE.
