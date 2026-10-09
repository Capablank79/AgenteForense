"""
Abstract base class and implementations for OCR Providers (Windows OCR).
"""
import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple, List
import winsdk.windows.media.ocr as win_ocr
import winsdk.windows.graphics.imaging as win_imaging
import winsdk.windows.globalization as win_glob
import winsdk.windows.storage.streams as win_streams
from PIL import Image

from agente_forense.petition.errors import OcrUnavailableError, OcrLanguageUnavailableError, OcrProcessingError

class PageOcrResult:
    def __init__(self, raw_text: str, page_index: int = 0):
        self.raw_text = raw_text
        self.page_index = page_index

class OcrProvider(ABC):
    @abstractmethod
    def is_available(self) -> bool:
        pass

    @abstractmethod
    def recognize_software_bitmap(self, bitmap: Any, language_tag: str = "es-ES") -> str:
        pass

    @abstractmethod
    def recognize_image_file(self, image_path: str, language_tag: str = "es-ES") -> str:
        pass

    @abstractmethod
    def process_image_file(self, image_path: str, language_tag: str = "es-ES") -> List[PageOcrResult]:
        pass


class WindowsOcrProvider(OcrProvider):
    def is_available(self) -> bool:
        try:
            return win_ocr.OcrEngine.is_language_supported(win_glob.Language("es-ES"))
        except Exception:
            return False

    def get_max_image_dimension(self, language_tag: str = "es-ES") -> int:
        lang = win_glob.Language(language_tag)
        if not win_ocr.OcrEngine.is_language_supported(lang):
            raise OcrLanguageUnavailableError(f"Language '{language_tag}' is not supported by Windows OCR runtime.")
        engine = win_ocr.OcrEngine.try_create_from_language(lang)
        if engine is None:
            raise OcrUnavailableError("Failed to create Windows OcrEngine instance.")
        return int(win_ocr.OcrEngine.max_image_dimension)

    def recognize_software_bitmap(self, bitmap: Any, language_tag: str = "es-ES") -> str:
        lang = win_glob.Language(language_tag)
        if not win_ocr.OcrEngine.is_language_supported(lang):
            raise OcrLanguageUnavailableError(f"Language '{language_tag}' is not supported by Windows OCR runtime.")
        engine = win_ocr.OcrEngine.try_create_from_language(lang)
        if engine is None:
            raise OcrUnavailableError("Failed to create Windows OcrEngine instance.")
        
        async def _run():
            return await engine.recognize_async(bitmap)
        
        try:
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None

            if loop and loop.is_running():
                import nest_asyncio
                nest_asyncio.apply()
                res = loop.run_until_complete(engine.recognize_async(bitmap))
            else:
                res = asyncio.run(_run())
            return str(res.text) if res and res.text else ""
        except Exception as e:
            raise OcrProcessingError(f"Windows OCR recognition failed: {str(e)}") from e

    def recognize_image_file(self, image_path: str, language_tag: str = "es-ES") -> str:
        """
        Loads JPG/PNG image via Pillow, resizes if exceeding max_image_dimension,
        converts to SoftwareBitmap, and runs Windows OCR.
        """
        max_dim = self.get_max_image_dimension(language_tag)
        with Image.open(image_path) as img:
            img = img.convert("RGBA")
            width, height = img.size
            
            # Check scale requirement
            if width > max_dim or height > max_dim:
                scale = min(max_dim / width, max_dim / height)
                new_w = int(width * scale)
                new_h = int(height * scale)
                img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                width, height = new_w, new_h

            # Convert RGBA bytes to SoftwareBitmap BGRA8 via DataWriter buffer
            bgra_bytes = bytearray(width * height * 4)
            raw = img.tobytes()
            # Raw is RGBA -> convert to BGRA
            for i in range(0, len(raw), 4):
                r, g, b, a = raw[i], raw[i+1], raw[i+2], raw[i+3]
                bgra_bytes[i] = b
                bgra_bytes[i+1] = g
                bgra_bytes[i+2] = r
                bgra_bytes[i+3] = a

            writer = win_streams.DataWriter()
            writer.write_bytes(bytes(bgra_bytes))
            buf = writer.detach_buffer()

            sb = win_imaging.SoftwareBitmap.create_copy_from_buffer(
                buf,
                win_imaging.BitmapPixelFormat.BGRA8,
                width,
                height,
                win_imaging.BitmapAlphaMode.PREMULTIPLIED
            )
            return self.recognize_software_bitmap(sb, language_tag)

    def process_image_file(self, image_path: str, language_tag: str = "es-ES") -> List[PageOcrResult]:
        """Process image file and return list of PageOcrResult objects with raw_text attribute."""
        txt = self.recognize_image_file(image_path, language_tag)
        return [PageOcrResult(raw_text=txt, page_index=0)]
