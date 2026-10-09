"""
Text normalization utilities for Petition processing.
"""
import re
import unicodedata

def normalize_petition_text(raw_text: str) -> str:
    """
    Normalizes raw extracted text safely:
    - Normalizes Unicode (NFC)
    - CRLF -> LF
    - Collapses repeated spaces/tabs (preserving newlines)
    - Cleans non-printable control characters (except tab and newline)
    """
    if not raw_text:
        return ""
    
    # Unicode NFC
    text = unicodedata.normalize("NFC", raw_text)
    
    # CRLF -> LF
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    
    # Strip unprintable control chars (preserve \n and \t)
    text = "".join(ch for ch in text if ch in ("\n", "\t") or (ord(ch) >= 32 and ord(ch) != 127))
    
    # Collapse multiple horizontal spaces/tabs into a single space on each line
    lines = []
    for line in text.split("\n"):
        line_clean = re.sub(r"[ ]+", " ", line).strip()
        lines.append(line_clean)
        
    return "\n".join(lines).strip()
