"""
Text extraction from searchable PDFs using pypdf.
"""
from pathlib import Path
from typing import List, Tuple
from pypdf import PdfReader
from agente_forense.petition.errors import PdfTextExtractionError

def extract_text_from_pdf(pdf_path: Path) -> List[Tuple[int, str]]:
    """
    Extracts raw text per page using pypdf.
    
    Returns:
        List of tuples: [(page_index, raw_text)]
    """
    try:
        reader = PdfReader(str(pdf_path))
        results = []
        for i, page in enumerate(reader.pages):
            txt = page.extract_text() or ""
            results.append((i, txt))
        return results
    except Exception as e:
        raise PdfTextExtractionError(f"pypdf text extraction failed: {str(e)}") from e
