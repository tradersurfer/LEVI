"""Shared tenant repository; every owned operation requires user_id."""
from typing import Any, Generic, TypeVar
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..models import AuditModel, DecisionModel, EvidenceModel, ProfileModel, SessionModel, TradeModel

T = TypeVar("T", ProfileModel, TradeModel, EvidenceModel, DecisionModel, AuditModel, SessionModel)

class TenantRepository(Generic[T]):
    model: type[T]
    def __init__(self, session: Session): self.session = session
    def add(self, user_id: str, **values: Any) -> T:
        record=self.model(user_id=user_id, **values); self.session.add(record); self.session.flush(); return record
    def get(self, user_id: str, record_id: str) -> T | None:
        return self.session.scalar(select(self.model).where(self.model.id == record_id, self.model.user_id == user_id))
    def list(self, user_id: str) -> list[T]:
        return list(self.session.scalars(select(self.model).where(self.model.user_id == user_id).order_by(self.model.created_at)).all())
    def delete(self, user_id: str, record_id: str) -> bool:
        record=self.get(user_id, record_id)
        if record is None: return False
        self.session.delete(record); self.session.flush(); return True
