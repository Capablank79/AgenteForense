"""
Generador de fixtures sintéticos para las pruebas del Pipeline de Petitorios (Sprint R05.1).
Crea archivos de prueba controlados en tests/fixtures/petition/
"""

import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "petition"


def generate_petition_fixtures():
    """Genera todos los archivos de prueba sintéticos necesarios."""
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Imagen PNG limpia con OCR nítido
    img_clean = Image.new("RGB", (1000, 700), color=(255, 255, 255))
    draw = ImageDraw.Draw(img_clean)
    text = (
        "MINISTERIO PUBLICO DE CHILE\n"
        "FISCALIA LOCAL DE VALPARAISO\n\n"
        "OFICIO ORDINARIO N: 458-2026\n"
        "RUC: 2400123456-7\n"
        "NUE: 8849201\n\n"
        "MAT: Solicita peritaje informatico forense a dispositivo incautado.\n"
        "UNIDAD REQUIRENTE: UNIDAD DE DEPOSITOS Y EVIDENCIAS\n"
        "FISCAL SOLICITANTE: JUAN PEREZ ALVAREZ\n"
    )
    draw.text((40, 40), text, fill=(0, 0, 0))
    img_clean.save(FIXTURES_DIR / "petition.png")

    # 2. Imagen JPG limpia
    img_clean.save(FIXTURES_DIR / "petition.jpg", "JPEG")

    # 3. PDF Escaneado sin capa de texto (generado convirtiendo imagen a PDF)
    img_clean.save(FIXTURES_DIR / "petition_scanned.pdf", "PDF")

    # 4. PDF conflicto por múltiples RUCs
    img_mult_ruc = Image.new("RGB", (1000, 700), color=(255, 255, 255))
    draw_mruc = ImageDraw.Draw(img_mult_ruc)
    text_mruc = (
        "MINISTERIO PUBLICO\n"
        "OFICIO N: 100-2026\n"
        "RUC PRINCIPAL: 2400123456-7\n"
        "RUC ASOCIADO: 2500987654-3\n"
        "NUE: 1234567\n"
    )
    draw_mruc.text((40, 40), text_mruc, fill=(0, 0, 0))
    img_mult_ruc.save(FIXTURES_DIR / "petition_conflict.pdf", "PDF")

    # 5. PDF sin RUC
    img_no_ruc = Image.new("RGB", (1000, 700), color=(255, 255, 255))
    draw_noruc = ImageDraw.Draw(img_no_ruc)
    text_noruc = (
        "SOLICITUD DE PERITAJE\n"
        "OFICIO: 555-2026\n"
        "NUE: 9988776\n"
        "SOLICITANTE: FISCALIA DE ANTOFAGASTA\n"
    )
    draw_noruc.text((40, 40), text_noruc, fill=(0, 0, 0))
    img_no_ruc.save(FIXTURES_DIR / "petition_missing_ruc.pdf", "PDF")

    # 6. PDF sin NUE
    img_no_nue = Image.new("RGB", (1000, 700), color=(255, 255, 255))
    draw_nonue = ImageDraw.Draw(img_no_nue)
    text_nonue = (
        "SOLICITUD DE PERITAJE\n"
        "OFICIO: 777-2026\n"
        "RUC: 2400123456-7\n"
        "UNIDAD REQUIRENTE: OS9 CARABINEROS\n"
    )
    draw_nonue.text((40, 40), text_nonue, fill=(0, 0, 0))
    img_no_nue.save(FIXTURES_DIR / "petition_missing_nue.pdf", "PDF")

    # 7. Imagen / PDF vacío o en blanco (OCR_EMPTY)
    img_blank = Image.new("RGB", (500, 500), color=(255, 255, 255))
    img_blank.save(FIXTURES_DIR / "petition_blank.png")
    img_blank.save(FIXTURES_DIR / "petition_blank.pdf", "PDF")


if __name__ == "__main__":
    generate_petition_fixtures()
    print("Fixtures creados exitosamente en", FIXTURES_DIR)
