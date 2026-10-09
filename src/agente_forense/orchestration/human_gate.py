"""
Gestión del Human Gate para confirmaciones humanas en acciones sensibles.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List
from uuid import UUID, uuid4
from sqlalchemy.orm import Session
from agente_forense.persistence.models import HumanConfirmationModel


class ConfirmationStatus(str, Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


@dataclass
class HumanConfirmationRecord:
    confirmation_id: str
    case_id: UUID
    requested_action: str
    summary: str
    status: ConfirmationStatus
    operator: Optional[str]
    request_id: Optional[str]
    requested_at: datetime
    confirmed_at: Optional[datetime]


class HumanGate:
    """Gestor de confirmaciones humanas (Human Gate)."""

    def __init__(self, session: Session):
        self.session = session

    def create_confirmation(
        self,
        case_id: UUID,
        requested_action: str,
        summary: str,
        operator: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> HumanConfirmationRecord:
        conf_id = f"conf-{uuid4().hex[:12]}"
        model = HumanConfirmationModel(
            confirmation_id=conf_id,
            case_id=case_id,
            requested_action=requested_action,
            summary=summary,
            status=ConfirmationStatus.PENDING.value,
            operator=operator,
            request_id=request_id,
            requested_at=datetime.now(timezone.utc),
        )
        self.session.add(model)
        self.session.flush()
        return self._to_record(model)

    def get_confirmation(self, confirmation_id: str) -> Optional[HumanConfirmationRecord]:
        model = (
            self.session.query(HumanConfirmationModel)
            .filter(HumanConfirmationModel.confirmation_id == confirmation_id)
            .first()
        )
        return self._to_record(model) if model else None

    def get_pending_by_case(self, case_id: UUID) -> List[HumanConfirmationRecord]:
        models = (
            self.session.query(HumanConfirmationModel)
            .filter(
                HumanConfirmationModel.case_id == case_id,
                HumanConfirmationModel.status == ConfirmationStatus.PENDING.value,
            )
            .all()
        )
        return [self._to_record(m) for m in models]

    def confirm(self, confirmation_id: str, operator: Optional[str] = None) -> HumanConfirmationRecord:
        model = (
            self.session.query(HumanConfirmationModel)
            .filter(HumanConfirmationModel.confirmation_id == confirmation_id)
            .first()
        )
        if not model:
            from agente_forense.orchestration.errors import ConfirmationNotFoundError
            raise ConfirmationNotFoundError(f"Confirmación no encontrada: {confirmation_id}")

        if model.status != ConfirmationStatus.PENDING.value:
            from agente_forense.orchestration.errors import ConfirmationAlreadyResolvedError
            raise ConfirmationAlreadyResolvedError(
                f"La confirmación {confirmation_id} ya se encuentra en estado {model.status}"
            )

        model.status = ConfirmationStatus.CONFIRMED.value
        model.confirmed_at = datetime.now(timezone.utc)
        if operator:
            model.operator = operator
        self.session.flush()
        return self._to_record(model)

    def reject(self, confirmation_id: str, operator: Optional[str] = None) -> HumanConfirmationRecord:
        model = (
            self.session.query(HumanConfirmationModel)
            .filter(HumanConfirmationModel.confirmation_id == confirmation_id)
            .first()
        )
        if not model:
            from agente_forense.orchestration.errors import ConfirmationNotFoundError
            raise ConfirmationNotFoundError(f"Confirmación no encontrada: {confirmation_id}")

        if model.status != ConfirmationStatus.PENDING.value:
            from agente_forense.orchestration.errors import ConfirmationAlreadyResolvedError
            raise ConfirmationAlreadyResolvedError(
                f"La confirmación {confirmation_id} ya se encuentra en estado {model.status}"
            )

        model.status = ConfirmationStatus.REJECTED.value
        model.confirmed_at = datetime.now(timezone.utc)
        if operator:
            model.operator = operator
        self.session.flush()
        return self._to_record(model)

    def _to_record(self, model: HumanConfirmationModel) -> HumanConfirmationRecord:
        return HumanConfirmationRecord(
            confirmation_id=model.confirmation_id,
            case_id=model.case_id,
            requested_action=model.requested_action,
            summary=model.summary,
            status=ConfirmationStatus(model.status),
            operator=model.operator,
            request_id=model.request_id,
            requested_at=model.requested_at,
            confirmed_at=model.confirmed_at,
        )
