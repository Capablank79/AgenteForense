"""
Integración con Qwen2.5:3b (Text-Only via Ollama) para estructurar texto OCR.
No está en la ruta crítica: si falla o expira el timeout, el sistema continúa con OCR y reglas.
"""

import json
import urllib.request
import urllib.error
from typing import Dict, Any, Optional

def query_qwen_text_analysis(ocr_text: str, timeout_seconds: float = 3.0) -> Optional[Dict[str, Any]]:
    """
    Envía texto OCR a Ollama `qwen2.5:3b` para solicitar extracción JSON estricta.
    Si Ollama no está disponible, falla o excede el timeout, retorna None.
    """
    if not ocr_text or not ocr_text.strip():
        return None

    prompt = f"""Eres un asistente forense que analiza TEXTO OCR de etiquetas de hardware.
Extrae únicamente los datos soportados explícitamente en el texto a continuación.
Devuelve EXCLUSIVAMENTE un objeto JSON válido con estas claves exactas:
{{
  "brand": string o null,
  "model": string o null,
  "serial": string o null,
  "capacity": string o null,
  "part_number": string o null,
  "visible_labels": array de strings
}}

Reglas estrictas:
- No inventes marcas, modelos ni números de serie.
- Si una marca o modelo no aparece explícitamente en el texto, pon null.
- Devuelve SOLO el JSON sin texto introductorio ni explicaciones.

TEXTO OCR:
{ocr_text}
"""

    payload = {
        "model": "qwen2.5:3b",
        "prompt": prompt,
        "stream": False,
        "format": "json"
    }

    try:
        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            "http://127.0.0.1:11434/api/generate",
            data=data_bytes,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=timeout_seconds) as resp:
            if resp.status == 200:
                res_body = resp.read().decode("utf-8")
                res_json = json.loads(res_body)
                response_text = res_json.get("response", "").strip()
                parsed = json.loads(response_text)
                if isinstance(parsed, dict):
                    return parsed
    except Exception:
        pass

    return None
