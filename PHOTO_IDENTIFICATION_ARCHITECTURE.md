# Arquitectura de Identificación Fotográfica Asistida

## 1. Visión General y Principios Forenses
El módulo `agente_forense.identification` implementa la ingesta, análisis, clasificación, extracción de atributos y renombrado seguro de evidencia fotográfica en el marco del sistema AGENTE FORENSE.

- **Inmutabilidad Absoluta**: Se verifica el hash SHA-256 pre y post análisis (`SHA256_BEFORE` == `SHA256_AFTER`). Prohibida la recompresión o edición de imágenes originales.
- **Motor local verificable**: Windows OCR (`es-ES`) como fuente primaria de texto visual.
- **Asistente LLM Opcional**: Qwen2.5:3b (Text-Only via Ollama) opera en modo auxiliar con timeout estricto de 3 segundos. Fallbacks limpios a OCR + reglas en caso de indisponibilidad.
- **Reglas Anti-Invención**: Verificación de validez contra texto OCR crudo. Prohibida la inferencia comercial o de color sin sustento directo.
- **Renombrado Determinístico e Inmutable**: Nomenclatura `NUE_{nue}_ESPECIE{sp}_[DSM{dsm}_]{clasificacion}_{seq:02d}.ext` ejecutada tras vista previa, chequeo previo de colisiones y verificación de hash con rollback atómico.

## 2. Flujo de Datos
```text
Fotografía (JPG/PNG)
  │
  ├── 1. Ingesta (Cálculo SHA-256 pre/post)
  ├── 2. Windows.Media.Ocr (es-ES) -> Texto OCR
  ├── 3. Clasificación Textual (SERIAL, ETIQUETA, NO_CLASIFICADA)
  ├── 4. Extractor Determinista Regex (Serial, Marca, Modelo, Capacidad, P/N, IMEI, MAC)
  ├── 5. Asistente Qwen2.5:3b Text-Only (opcional, timeout 3s)
  ├── 6. Barrera Anti-Invención (rechazo de marcas/modelos no sustentados)
  ├── 7. Detección de Conflictos (SERIAL_MULTIPLE_VALUES, BRAND_CONFLICT, etc.)
  ├── 8. Revisión Humana (Human Gate / Confirmación u Operador)
  ├── 9. Vista previa & Renombrado Atómico en Disco
  └── 10. Generación de identification.json y Sincronización case.json / PostgreSQL
```
