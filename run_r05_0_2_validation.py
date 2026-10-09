import asyncio
import hashlib
import json
import os
import sys
import tempfile
import time
import winsdk.windows.storage as storage
import winsdk.windows.storage.streams as streams
import winsdk.windows.data.pdf as pdf
import winsdk.windows.graphics.imaging as imaging
import winsdk.windows.media.ocr as ocr
import winsdk.windows.globalization as glob
from PIL import Image, ImageDraw

def calculate_sha256(file_path):
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def calculate_bytes_sha256(data_bytes):
    return hashlib.sha256(data_bytes).hexdigest()

def create_synthetic_scanned_pdf(output_pdf_path):
    tmp_dir = tempfile.mkdtemp()
    img1_path = os.path.join(tmp_dir, "page1.png")
    img2_path = os.path.join(tmp_dir, "page2.png")
    
    # Page 1
    img1 = Image.new("RGB", (800, 600), color="white")
    draw1 = ImageDraw.Draw(img1)
    draw1.text((60, 60), "RUC 12345678", fill="black")
    draw1.text((60, 120), "NUE 777777", fill="black")
    img1.save(img1_path)
    
    # Page 2
    img2 = Image.new("RGB", (800, 600), color="white")
    draw2 = ImageDraw.Draw(img2)
    draw2.text((80, 60), "OFICIO 123", fill="black")
    draw2.text((80, 120), "SOLICITA DILIGENCIA FORENSE", fill="black")
    img2.save(img2_path)
    img2.close()
    
    # Convert images to 2-page PDF (Image only, no embedded text layer)
    i1 = Image.open(img1_path)
    i2 = Image.open(img2_path)
    i1.save(output_pdf_path, "PDF", save_all=True, append_images=[i2])
    
    sha1 = calculate_sha256(img1_path)
    sha2 = calculate_sha256(img2_path)
    return img1_path, sha1, img2_path, sha2

def check_pdf_text_layer(pdf_path):
    # Check if raw text strings like RUC, NUE exist in plain PDF stream bytes
    with open(pdf_path, "rb") as f:
        content = f.read()
    keywords = [b"RUC", b"12345678", b"NUE", b"777777", b"OFICIO", b"SOLICITA"]
    found = [kw for kw in keywords if kw in content]
    if not found:
        return "ABSENT", "No raw text strings found in PDF bytes (pure image PDF)"
    else:
        return "PRESENT", f"Found raw strings: {found}"

async def run_single_pipeline(pdf_path):
    start_total = time.perf_counter()
    
    file = await storage.StorageFile.get_file_from_path_async(pdf_path)
    doc = await pdf.PdfDocument.load_from_file_async(file)
    
    page_results = []
    total_render_time = 0.0
    total_ocr_time = 0.0
    
    lang = glob.Language("es-ES")
    ocr_engine = ocr.OcrEngine.try_create_from_language(lang)
    
    for page_idx in range(doc.page_count):
        page = doc.get_page(page_idx)
        
        # Render
        t0_render = time.perf_counter()
        stream = streams.InMemoryRandomAccessStream()
        await page.render_to_stream_async(stream)
        t1_render = time.perf_counter()
        render_duration = t1_render - t0_render
        total_render_time += render_duration
        
        # Stream read for metadata / hash
        reader = streams.DataReader(stream.get_input_stream_at(0))
        await reader.load_async(stream.size)
        buf = bytearray(stream.size)
        reader.read_bytes(buf)
        render_bytes = bytes(buf)
        render_sha256 = calculate_bytes_sha256(render_bytes)
        
        # Reset stream position for decoder
        stream.seek(0)
        decoder = await imaging.BitmapDecoder.create_async(stream)
        software_bitmap = await decoder.get_software_bitmap_async()
        
        # OCR
        t0_ocr = time.perf_counter()
        ocr_result = await ocr_engine.recognize_async(software_bitmap)
        t1_ocr = time.perf_counter()
        ocr_duration = t1_ocr - t0_ocr
        total_ocr_time += ocr_duration
        
        page_results.append({
            "page_index": page_idx,
            "page_width": page.size.width,
            "page_height": page.size.height,
            "render_stream_size": stream.size,
            "render_sha256": render_sha256,
            "bitmap_format": str(software_bitmap.bitmap_pixel_format),
            "bitmap_width": software_bitmap.pixel_width,
            "bitmap_height": software_bitmap.pixel_height,
            "render_latency_s": render_duration,
            "ocr_latency_s": ocr_duration,
            "text": ocr_result.text.strip()
        })
    
    total_duration = time.perf_counter() - start_total
    return {
        "page_count": doc.page_count,
        "is_password_protected": doc.is_password_protected,
        "total_render_latency_s": total_render_time,
        "total_ocr_latency_s": total_ocr_time,
        "total_latency_s": total_duration,
        "pages": page_results
    }

async def run_error_tests(tmp_dir):
    error_reports = []
    
    # 1. Non-PDF file
    non_pdf_path = os.path.join(tmp_dir, "test.txt")
    with open(non_pdf_path, "w", encoding="utf-8") as f:
        f.write("This is not a PDF file.")
    try:
        file = await storage.StorageFile.get_file_from_path_async(non_pdf_path)
        doc = await pdf.PdfDocument.load_from_file_async(file)
        error_reports.append({"test": "non_pdf", "status": "UNEXPECTED_SUCCESS", "details": f"Loaded pages: {doc.page_count}"})
    except Exception as e:
        error_reports.append({"test": "non_pdf", "status": "HANDLED_ERROR", "exception_type": type(e).__name__, "message": str(e)})
        
    # 2. Corrupt PDF file
    corrupt_pdf_path = os.path.join(tmp_dir, "corrupt.pdf")
    with open(corrupt_pdf_path, "wb") as f:
        f.write(b"%PDF-1.4 header followed by corrupted garbage bytes 0x90 0xFF 0x00 0x12 0x34")
    try:
        file = await storage.StorageFile.get_file_from_path_async(corrupt_pdf_path)
        doc = await pdf.PdfDocument.load_from_file_async(file)
        error_reports.append({"test": "corrupt_pdf", "status": "UNEXPECTED_SUCCESS", "details": f"Loaded pages: {doc.page_count}"})
    except Exception as e:
        error_reports.append({"test": "corrupt_pdf", "status": "HANDLED_ERROR", "exception_type": type(e).__name__, "message": str(e)})

    # 3. Non-existent file
    missing_path = os.path.join(tmp_dir, "does_not_exist.pdf")
    try:
        file = await storage.StorageFile.get_file_from_path_async(missing_path)
        doc = await pdf.PdfDocument.load_from_file_async(file)
        error_reports.append({"test": "missing_file", "status": "UNEXPECTED_SUCCESS", "details": f"Loaded pages: {doc.page_count}"})
    except Exception as e:
        error_reports.append({"test": "missing_file", "status": "HANDLED_ERROR", "exception_type": type(e).__name__, "message": str(e)})
        
    return error_reports

async def main():
    tmp_dir = tempfile.mkdtemp()
    pdf_path = os.path.join(tmp_dir, "scanned_petition_synthetic.pdf")
    
    img1_path, img1_sha, img2_path, img2_sha = create_synthetic_scanned_pdf(pdf_path)
    pdf_sha_before = calculate_sha256(pdf_path)
    
    text_layer_status, text_layer_detail = check_pdf_text_layer(pdf_path)
    
    runs = []
    for r in range(1, 4):
        res = await run_single_pipeline(pdf_path)
        runs.append(res)
        
    pdf_sha_after = calculate_sha256(pdf_path)
    hash_unchanged = (pdf_sha_before == pdf_sha_after)
    
    error_results = await run_error_tests(tmp_dir)
    
    # Expected tokens
    expected_tokens = ["RUC", "12345678", "NUE", "777777", "OFICIO", "123", "SOLICITA", "DILIGENCIA", "FORENSE"]
    all_ocr_text = " ".join([page["text"] for page in runs[0]["pages"]])
    matched_tokens = [tok for tok in expected_tokens if tok in all_ocr_text or tok in all_ocr_text.replace(" ", "")]
    
    output = {
        "pdf_path": pdf_path,
        "pdf_sha_before": pdf_sha_before,
        "pdf_sha_after": pdf_sha_after,
        "hash_unchanged": hash_unchanged,
        "img1_sha256": img1_sha,
        "img2_sha256": img2_sha,
        "text_layer_status": text_layer_status,
        "text_layer_detail": text_layer_detail,
        "runs": runs,
        "error_results": error_results,
        "expected_tokens": expected_tokens,
        "matched_tokens": matched_tokens,
        "all_ocr_text": all_ocr_text
    }
    
    print(json.dumps(output, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
