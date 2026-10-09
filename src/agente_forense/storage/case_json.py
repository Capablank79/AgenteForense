"""
Servicio para la generación, persistencia atómica y reconciliación de case.json.
"""

import json
import os
import tempfile
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from agente_forense.persistence.models import CaseModel
from agente_forense.persistence.repositories import (
    CaseRepository, NueRepository, SpeciesRepository, DsmRepository, AuditRepository
)
from agente_forense.domain.enums import ReconciliationStatus
from agente_forense.domain.errors import ReconciliationError

SCHEMA_VERSION = 1


class CaseJsonService:
    """
    Servicio encargado de la creación atómica de case.json y reconciliación DB <-> snapshot.
    """

    def __init__(self, session: Session, storage_root: Optional[Path] = None):
        self.session = session
        self.storage_root = storage_root
        self.case_repo = CaseRepository(session)
        self.nue_repo = NueRepository(session)
        self.species_repo = SpeciesRepository(session)
        self.dsm_repo = DsmRepository(session)
        self.audit_repo = AuditRepository(session)

    def generate_case_json_data(self, case_id: UUID) -> Dict[str, Any]:
        """
        Construye la estructura dict conforme a la especificación de case.json:
        schema_version = 1
        case_id, ruc, status, created_at, updated_at, nues[...]
        """
        case = self.case_repo.get_by_id(case_id)
        if not case:
            raise ValueError(f"Caso {case_id} no encontrado.")

        nues = self.nue_repo.list_by_case(case_id)
        nues_data = []

        for nue in nues:
            species_list = self.species_repo.list_by_nue(nue.id)
            species_data = []
            for sp in species_list:
                dsms = self.dsm_repo.list_by_species(sp.id)
                dsm_data = []
                for d in dsms:
                    # Obtener binding confirmado si existe
                    binding_info = None
                    from agente_forense.hardware.bindings import DsmDiskBindingModel, BindingStatus
                    b = self.session.query(DsmDiskBindingModel).filter(
                        DsmDiskBindingModel.dsm_id == d.id,
                        DsmDiskBindingModel.status == BindingStatus.CONFIRMED.value
                    ).first()
                    if b:
                        binding_info = {
                            "disk_number": b.disk_number,
                            "physical_drive": b.physical_drive,
                            "serial_number": b.serial_number,
                            "status": b.status,
                            "confirmed_at": b.confirmed_at.isoformat() if b.confirmed_at else None
                        }

                    dsm_data.append({
                        "dsm_number": d.dsm_number,
                        "label": d.label,
                        "same_physical_object_as_species": d.same_physical_object_as_species,
                        "physical_drive": b.physical_drive if b else None,
                        "acquisition_status": d.status or "PENDING",
                        "verification_status": "PENDING",
                        "disk_binding": binding_info
                    })
                species_data.append({
                    "species_number": sp.species_number,
                    "label": sp.label,
                    "storage_relation": sp.storage_relation,
                    "identification_status": sp.status or "PENDING",
                    "storage_devices": dsm_data
                })

            nues_data.append({
                "nue": nue.nue_number,
                "species": species_data
            })

        # Obtener datos de la petición (Petition) si existen para el RUC/caso
        petition_info = None
        from agente_forense.persistence.models import PetitionModel
        pet = self.session.query(PetitionModel).filter(PetitionModel.ruc == case.ruc).order_by(PetitionModel.created_at.desc()).first()
        if pet:
            petition_info = {
                "petition_id": str(pet.id),
                "sha256": pet.sha256,
                "status": pet.review_status,
                "petition_number": pet.petition_number
            }

        return {
            "schema_version": SCHEMA_VERSION,
            "case_id": str(case.id),
            "ruc": case.ruc,
            "status": case.status,
            "petition": petition_info,
            "created_at": case.created_at.isoformat() if case.created_at else None,
            "updated_at": case.updated_at.isoformat() if case.updated_at else None,
            "nues": nues_data
        }

    def write_case_json_atomic(
        self,
        case_id: UUID,
        target_dir: Path,
        actor: str = "SYSTEM",
        request_id: Optional[str] = None
    ) -> Path:
        """
        Escribe case.json de manera atómica:
        1. Genera JSON en memoria.
        2. Escribe a un archivo temporal en la misma carpeta/dispositivo.
        3. Realiza flush y fsync.
        4. Realiza reemplazo atómico (os.replace).
        """
        data = self.generate_case_json_data(case_id)
        target_dir.mkdir(parents=True, exist_ok=True)
        final_path = target_dir / "case.json"

        # Escribir temporal
        temp_fd, temp_path_str = tempfile.mkstemp(dir=target_dir, prefix="case_json_", suffix=".tmp")
        temp_path = Path(temp_path_str)

        try:
            with os.fdopen(temp_fd, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())

            os.replace(temp_path, final_path)

            # Auditar CASE_JSON_WRITTEN
            self.audit_repo.append(
                actor=actor,
                module="STORAGE",
                tool="CaseJsonService",
                tool_version="1.0.0",
                event_type="CASE_JSON_WRITTEN",
                action="WRITE_SNAPSHOT",
                result="SUCCESS",
                case_id=case_id,
                destination=str(final_path),
                details={"schema_version": SCHEMA_VERSION, "request_id": request_id}
            )
            self.session.commit()
            return final_path
        except Exception as e:
            if temp_path.exists():
                try:
                    os.remove(temp_path)
                except Exception:
                    pass
            raise e

    def reconcile(
        self,
        case_id: UUID,
        case_json_path: Path,
        actor: str = "SYSTEM",
        request_id: Optional[str] = None
    ) -> Tuple[ReconciliationStatus, Optional[str]]:
        """
        Reconcilia el estado en PostgreSQL con la foto portable en case.json.
        Retorna (ReconciliationStatus, detalle_string).
        NO corrige silenciosamente.
        """
        if not case_json_path.exists():
            status = ReconciliationStatus.MISSING_FILE
            msg = f"El archivo case.json no existe en {case_json_path}"
            self._audit_reconciliation(case_id, status, msg, actor, request_id)
            return status, msg

        try:
            with open(case_json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            status = ReconciliationStatus.INVALID_JSON
            msg = f"No se pudo parsear el archivo JSON: {str(e)}"
            self._audit_reconciliation(case_id, status, msg, actor, request_id)
            return status, msg

        if not isinstance(data, dict):
            status = ReconciliationStatus.INVALID_JSON
            msg = "El contenido de case.json no es un objeto JSON válido."
            self._audit_reconciliation(case_id, status, msg, actor, request_id)
            return status, msg

        # Verificar schema_version
        v = data.get("schema_version")
        if v != SCHEMA_VERSION:
            status = ReconciliationStatus.SCHEMA_MISMATCH
            msg = f"Versión de esquema no coincide. Esperada: {SCHEMA_VERSION}, Encontrada: {v}"
            self._audit_reconciliation(case_id, status, msg, actor, request_id)
            return status, msg

        # Comparar datos contra DB
        db_data = self.generate_case_json_data(case_id)

        # Comparación estructural de campos clave
        if (
            db_data.get("ruc") != data.get("ruc") or
            db_data.get("case_id") != data.get("case_id") or
            len(db_data.get("nues", [])) != len(data.get("nues", []))
        ):
            status = ReconciliationStatus.CONTENT_MISMATCH
            msg = f"Diferencia de contenido entre DB y snapshot case.json."
            self._audit_reconciliation(case_id, status, msg, actor, request_id)
            return status, msg

        # Verificar detalle de nues y species
        db_nues = {n["nue"]: n for n in db_data.get("nues", [])}
        json_nues = {n["nue"]: n for n in data.get("nues", [])}

        if set(db_nues.keys()) != set(json_nues.keys()):
            status = ReconciliationStatus.CONTENT_MISMATCH
            msg = "Descalce en los números de NUE entre DB y case.json."
            self._audit_reconciliation(case_id, status, msg, actor, request_id)
            return status, msg

        status = ReconciliationStatus.MATCH
        msg = "Reconciliación exitosa. DB y case.json están 100% sincronizados."
        self._audit_reconciliation(case_id, status, msg, actor, request_id)
        return status, msg

    def _audit_reconciliation(
        self,
        case_id: UUID,
        status: ReconciliationStatus,
        message: str,
        actor: str,
        request_id: Optional[str]
    ) -> None:
        self.audit_repo.append(
            actor=actor,
            module="RECONCILIATION",
            tool="CaseJsonService",
            tool_version="1.0.0",
            event_type="CASE_JSON_RECONCILED",
            action="RECONCILE",
            result="SUCCESS" if status == ReconciliationStatus.MATCH else "FAILURE",
            case_id=case_id,
            details={
                "status": status.value,
                "message": message,
                "request_id": request_id
            }
        )
        self.session.commit()
