# PDF Render & Windows OCR Runtime Validation — Sprint R05.0.2

## ENVIRONMENT
- **OS**: Windows 10 Pro
- **WINDOWS BUILD**: 10.0.19045
- **PYTHON**: 3.10.11
- **WINSDK**: 1.0.0b10

## PDF FIXTURE
- **Fixture Path**: Temporary synthetic 2-page PDF (`scanned_petition_synthetic.pdf`)
- **Page 1 Source Image SHA256**: `a202c5a41c62b3c18e660f4d8e5115bdbd6a6cdac628bd0f2ac5777a54e33a16`
- **Page 2 Source Image SHA256**: `d7581b8a7e7b1cd086cd1bec98610fbd7cb1d28e1fd334d9d4b997f90535a52d`
- **PDF SHA256 (Before)**: `aa9193f885a6695c9a804dd007bd9500a2396c17bea0e76dc4a13e1a2aa7a352`

## TEXT LAYER CHECK
- **Status**: ABSENT / INSUFFICIENT
- **Detail**: Raw inspection of PDF stream bytes confirmed absence of text strings ("RUC", "12345678", etc.). PDF represents pure image-based scanned pages.

## PDFDOCUMENT LOAD
- **Status**: SUCCESS
- **API**: `winsdk.windows.data.pdf.PdfDocument.load_from_file_async(StorageFile)`
- **Is Password Protected**: `False`

## PAGE COUNT
- **Page Count**: 2

## RENDER API
- **API Method**: `winsdk.windows.data.pdf.PdfPage.render_to_stream_async(InMemoryRandomAccessStream)`

## RENDER OUTPUT
- **Page 0 Output Stream Size**: 13455 bytes
- **Page 0 Render SHA256**: `849c890fcd3da3ace44b43837891361a0ad19823f550e982a201babc878ad825`
- **Page 1 Output Stream Size**: 16180 bytes
- **Page 1 Render SHA256**: `293587f249821fd32b6973bc456887ac04f49597490ec38f853241fa56fcfede`

## RENDER DIMENSIONS
- **Native Page Size**: 1066.67 x 800.0 pt
- **SoftwareBitmap Format**: `BitmapPixelFormat.BGRA8`
- **SoftwareBitmap Dimensions**: 1067 x 800 px

## OCR ENGINE
- **Class**: `winsdk.windows.media.ocr.OcrEngine`
- **Language**: `winsdk.windows.globalization.Language('es-ES')`
- **Method**: `recognize_async(SoftwareBitmap)`

## OCR TEXT & REPEATABILITY
Executed 3 consecutive end-to-end runs:

### Run 1:
- **Render Latency**: 0.213 s (P0: 0.169s, P1: 0.044s)
- **OCR Latency**: 0.049 s (P0: 0.025s, P1: 0.024s)
- **Total Latency**: 0.308 s
- **Page 0 OCR Text**: `RUC 12345678 NUE777777`
- **Page 1 OCR Text**: `OFICIO 123 SOLICITADILIGENCIAFORENSE`

### Run 2:
- **Render Latency**: 0.091 s (P0: 0.045s, P1: 0.046s)
- **OCR Latency**: 0.052 s (P0: 0.025s, P1: 0.027s)
- **Total Latency**: 0.158 s
- **Page 0 OCR Text**: `RUC 12345678 NUE777777`
- **Page 1 OCR Text**: `OFICIO 123 SOLICITADILIGENCIAFORENSE`

### Run 3:
- **Render Latency**: 0.088 s (P0: 0.042s, P1: 0.046s)
- **OCR Latency**: 0.046 s (P0: 0.023s, P1: 0.023s)
- **Total Latency**: 0.151 s
- **Page 0 OCR Text**: `RUC 12345678 NUE777777`
- **Page 1 OCR Text**: `OFICIO 123 SOLICITADILIGENCIAFORENSE`

## PAGE PROVENANCE
- Page 0 text strictly map to `page_index: 0`
- Page 1 text strictly map to `page_index: 1`
- Provenance correctly preserved without arbitrary concatenation loss.

## TOKENS VALIDATION
- **Expected Tokens**: `["RUC", "12345678", "NUE", "777777", "OFICIO", "123", "SOLICITA", "DILIGENCIA", "FORENSE"]`
- **Matched Tokens**: `["RUC", "12345678", "NUE", "777777", "OFICIO", "123", "SOLICITA", "DILIGENCIA", "FORENSE"]` (9 / 9 matched, 100%)

## ORIGINAL HASH AFTER
- **PDF SHA256 (After)**: `aa9193f885a6695c9a804dd007bd9500a2396c17bea0e76dc4a13e1a2aa7a352`
- **Integrity Verified**: YES (Hash before == Hash after)

## ERROR TESTS
1. **Non-PDF File**: Controlled handling. Caught `OSError` (`[WinError -2147188716] Windows Error 0x80048014`).
2. **Corrupt PDF File**: Controlled handling. Caught `OSError` (`[WinError -2147188712] Windows Error 0x80048018`).
3. **Missing File**: Controlled handling. Caught `FileNotFoundError` (`[WinError -2147024894]`).

## CONCLUSION
`Windows.Data.Pdf` via `winsdk` successfully renders scanned PDF pages to bitmap streams in memory, which seamlessly feed into `Windows.Media.Ocr` (`es-ES`), extracting 100% of expected forensic tokens without any cloud or external dependencies.

## RECOMMENDATION
Proceed to **R05.1** (Integración de Renderizado PDF + Windows OCR al Pipeline Forense). No external renderer (PyMuPDF / Poppler) required.
