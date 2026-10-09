"""
Crea fixtures sintéticas de imágenes para el test suite del agente de identificación fotográfica.
Genera imágenes JPG y PNG con texto dibujado por Pillow para simular OCR de Windows.
"""

from pathlib import Path
from PIL import Image, ImageDraw

def create_synthetic_photo_fixtures(output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. photo_serial.jpg
    img1 = Image.new("RGB", (600, 200), color=(255, 255, 255))
    d1 = ImageDraw.Draw(img1)
    d1.text((20, 40), "WESTERN DIGITAL\nMODEL WD10EZEX\nS/N: WCC6Y0123456\n1.0 TB", fill=(0, 0, 0))
    img1.save(output_dir / "photo_serial.jpg", format="JPEG")

    # 2. photo_label.jpg
    img2 = Image.new("RGB", (600, 200), color=(255, 255, 255))
    d2 = ImageDraw.Draw(img2)
    d2.text((20, 40), "SEAGATE BARRACUDA\nMODEL: ST2000DM008\nP/N: 2FR102-300\nS/N: Z520ABCD", fill=(0, 0, 0))
    img2.save(output_dir / "photo_label.jpg", format="JPEG")

    # 3. photo_capacity.png
    img3 = Image.new("RGBA", (600, 200), color=(255, 255, 255, 255))
    d3 = ImageDraw.Draw(img3)
    d3.text((20, 40), "KINGSTON A400\nCAPACITY: 500 GB\nS/N: 50026B768291A", fill=(0, 0, 0, 255))
    img3.save(output_dir / "photo_capacity.png", format="PNG")

    # 4. photo_no_text.jpg
    img4 = Image.new("RGB", (300, 300), color=(128, 128, 128))
    img4.save(output_dir / "photo_no_text.jpg", format="JPEG")

    # 5. photo_conflict_1.jpg
    img5 = Image.new("RGB", (600, 200), color=(255, 255, 255))
    d5 = ImageDraw.Draw(img5)
    d5.text((20, 40), "S/N: SERIALAAAA1111", fill=(0, 0, 0))
    img5.save(output_dir / "photo_conflict_1.jpg", format="JPEG")

    # 6. photo_conflict_2.jpg
    img6 = Image.new("RGB", (600, 200), color=(255, 255, 255))
    d6 = ImageDraw.Draw(img6)
    d6.text((20, 40), "S/N: SERIALBBBB2222", fill=(0, 0, 0))
    img6.save(output_dir / "photo_conflict_2.jpg", format="JPEG")

if __name__ == "__main__":
    fixtures_path = Path(__file__).parent / "fixtures" / "photos"
    create_synthetic_photo_fixtures(fixtures_path)
    print(f"Fixtures sintéticas fotográficas creadas en {fixtures_path}")
