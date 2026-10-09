"""
PDF page rendering module using Windows.Data.Pdf and Windows OCR.
"""
import asyncio
import io
from typing import List, Tuple
from pathlib import Path
import winsdk.windows.data.pdf as win_pdf
import winsdk.windows.storage as win_storage
import winsdk.windows.storage.streams as win_streams
from PIL import Image

from agente_forense.petition.ocr import WindowsOcrProvider
from agente_forense.petition.errors import PdfRenderError

class RenderedPdfPage:
    def __init__(self, page_index: int, raw_text: str, width: int, height: int):
        self.page_index = page_index
        self.raw_text = raw_text
        self.width = width
        self.height = height

class PdfRendererOcr:
    def __init__(self, ocr_provider: WindowsOcrProvider = None):
        self.ocr_provider = ocr_provider or WindowsOcrProvider()

    def render_and_ocr_pdf(self, pdf_path: Path, language_tag: str = "es-ES") -> List[RenderedPdfPage]:
        """
        Renders PDF pages using Windows.Data.Pdf API, converts each stream to PIL Image,
        and delegates recognition to WindowsOcrProvider.recognize_image_file or recognize_software_bitmap.
        """
        abs_path = str(pdf_path.resolve())
        max_dim = self.ocr_provider.get_max_image_dimension(language_tag)

        async def _async_render():
            storage_file = await win_storage.StorageFile.get_file_from_path_async(abs_path)
            doc = await win_pdf.PdfDocument.load_from_file_async(storage_file)
            page_results = []

            for page_idx in range(doc.page_count):
                page = doc.get_page(page_idx)
                stream = win_streams.InMemoryRandomAccessStream()
                options = win_pdf.PdfPageRenderOptions()
                
                # Check scale if needed
                w = page.size.width
                h = page.size.height
                if w > max_dim or h > max_dim:
                    scale = min(max_dim / w, max_dim / h)
                    options.destination_width = int(w * scale)
                    options.destination_height = int(h * scale)
                else:
                    options.destination_width = int(w)
                    options.destination_height = int(h)

                await page.render_to_stream_async(stream, options)
                
                # Read stream into Python bytes
                reader = win_streams.DataReader(stream.get_input_stream_at(0))
                await reader.load_async(stream.size)
                buf = bytearray(stream.size)
                reader.read_bytes(buf)

                # Open via PIL
                with Image.open(io.BytesIO(buf)) as img:
                    width, height = img.size
                    img = img.convert("RGBA")
                    
                    # Convert to BGRA for OCR SoftwareBitmap
                    raw = img.tobytes()
                    bgra_bytes = bytearray(width * height * 4)
                    for i in range(0, len(raw), 4):
                        bgra_bytes[i] = raw[i+2]
                        bgra_bytes[i+1] = raw[i+1]
                        bgra_bytes[i+2] = raw[i]
                        bgra_bytes[i+3] = raw[i+3]

                    writer = win_streams.DataWriter()
                    writer.write_bytes(bytes(bgra_bytes))
                    bmp_buf = writer.detach_buffer()

                    import winsdk.windows.graphics.imaging as win_imaging
                    sb = win_imaging.SoftwareBitmap.create_copy_from_buffer(
                        bmp_buf,
                        win_imaging.BitmapPixelFormat.BGRA8,
                        width,
                        height,
                        win_imaging.BitmapAlphaMode.PREMULTIPLIED
                    )

                    # Recognize bitmap directly inside the running loop
                    engine_lang = win_pdf.win_glob.Language(language_tag) if hasattr(win_pdf, "win_glob") else None
                    import winsdk.windows.globalization as win_glob
                    import winsdk.windows.media.ocr as win_ocr
                    
                    lang = win_glob.Language(language_tag)
                    engine = win_ocr.OcrEngine.try_create_from_language(lang)
                    ocr_res = await engine.recognize_async(sb)
                    txt = str(ocr_res.text) if ocr_res and ocr_res.text else ""

                    page_results.append(RenderedPdfPage(page_idx, txt, width, height))

            return page_results

        try:
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None

            if loop and loop.is_running():
                import nest_asyncio
                nest_asyncio.apply()
                pages = loop.run_until_complete(_async_render())
            else:
                pages = asyncio.run(_async_render())
            return pages
        except Exception as e:
            raise PdfRenderError(f"Failed to render scanned PDF page via Windows.Data.Pdf: {str(e)}") from e
