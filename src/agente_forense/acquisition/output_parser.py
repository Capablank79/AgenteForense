"""
Parseador de la salida stdout/stderr y logs nativos de ewfacquire.exe.
"""

import re
from typing import Dict, Any, Optional


class EwfOutputParser:
    """
    Parsea la salida nativa de ewfacquire para extraer bytes adquiridos,
    hashes MD5/SHA256 reportados y estado de finalización.
    """

    @staticmethod
    def parse_stdout(stdout_text: str) -> Dict[str, Any]:
        result = {
            "bytes_acquired": None,
            "md5": None,
            "sha256": None,
            "success_marker": False,
            "status": "UNKNOWN"
        }

        if not stdout_text:
            return result

        # MD5 hash calculated over data: <md5>
        md5_match = re.search(r"MD5\s+hash\s+calculated\s+over\s+data:\s*([a-fA-F0-9]{32})", stdout_text, re.IGNORECASE)
        if md5_match:
            result["md5"] = md5_match.group(1).lower()

        # SHA256 hash calculated over data: <sha256>
        sha256_match = re.search(r"SHA256\s+hash\s+calculated\s+over\s+data:\s*([a-fA-F0-9]{64})", stdout_text, re.IGNORECASE)
        if sha256_match:
            result["sha256"] = sha256_match.group(1).lower()

        # ewfacquire: SUCCESS
        if "ewfacquire: SUCCESS" in stdout_text or "Acquisition completed" in stdout_text:
            result["success_marker"] = True
            result["status"] = "SUCCESS"

        # Bytes written / acquired
        bytes_match = re.search(r"Acquired\s+(\d+)\s+bytes", stdout_text, re.IGNORECASE)
        if bytes_match:
            result["bytes_acquired"] = int(bytes_match.group(1))

        return result
