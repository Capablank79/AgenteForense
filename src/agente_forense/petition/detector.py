"""
Format and type detector for Petition documents.
"""
from pathlib import Path
from typing import Tuple
from pypdf import PdfReader
from agente_forense.petition.errors import UnsupportedPetitionFormatError

ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}

def detect_petition_type(file_path: Path) -> Tuple[str, bool, int]:
    """
    Detects document extension, whether PDF has usable text layer, and page count.
    
    Returns:
        Tuple[extension (str), is_text_pdf (bool), page_count (int)]
    """
    ext = file_path.suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise UnsupportedPetitionFormatError(f"Extension '{ext}' is not supported for petition processing.")
    
    if ext != ".pdf":
        return ext, False, 1
    
    # Analyze PDF
    try:
        reader = PdfReader(str(file_path))
        page_count = len(reader.pages)
        total_text_length = 0
        for page in reader.pages:
            txt = page.extract_text() or ""
            total_text_length += len(txt.strip())
        
        # Criterion for TEXT_LAYER_USABLE: total extracted non-space text >= 20 characters
        is_text_pdf = total_text_length >= 20
        return ext, is_text_pdf, page_count
    except Exception:
        # If pypdf fails to parse, treat as unusable text (or let pdf renderer handle scanned)
        return ext, False, 1
