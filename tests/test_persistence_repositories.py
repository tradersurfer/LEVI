import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from levi.persistence.audit import record_audit
from levi.persistence.models import Base
from levi.persistence.repositories import AuditRepository, DecisionRepository, EvidenceRepository, ProfileRepository, TradeRepository, UserRepository


@pytest.fixture
def session():
    engine=create_engine("sqlite://",connect_args={"check_same_thread":False},poolclass=StaticPool)
    Base.metadata.create_all(engine)
    with Session(engine) as value:
        users=UserRepository(value); users.upsert("u1","u1@test.com","email"); users.upsert("u2","u2@test.com","google")
        yield value


def test_user_upsert_and_get(session): assert UserRepository(session).get("u1").email == "u1@test.com"
def test_profile_is_tenant_scoped(session):
    repo=ProfileRepository(session); record=repo.add("u1",payload={"mode":"swing"})
    assert repo.get("u1",record.id) is record and repo.get("u2",record.id) is None
def test_trade_is_tenant_scoped(session):
    repo=TradeRepository(session); record=repo.add("u1",symbol="SPY",status="paper",quantity=1,price=1.2,payload={})
    assert repo.list("u2") == [] and repo.list("u1") == [record]
def test_evidence_is_tenant_scoped(session):
    repo=EvidenceRepository(session); record=repo.add("u1",evidence_type="chart",source_name="test",payload={})
    assert repo.get("u2",record.id) is None
def test_decision_is_tenant_scoped(session):
    repo=DecisionRepository(session); repo.add("u1",decision_type="consensus",outcome="no_trade",payload={})
    assert len(repo.list("u1")) == 1 and repo.list("u2") == []
def test_cross_tenant_delete_fails(session):
    repo=TradeRepository(session); record=repo.add("u1",symbol="SPY",status="paper",quantity=1,price=1,payload={})
    assert repo.delete("u2",record.id) is False and repo.get("u1",record.id)
def test_owner_delete_succeeds(session):
    repo=EvidenceRepository(session); record=repo.add("u1",evidence_type="pdf",source_name="test",payload={})
    assert repo.delete("u1",record.id) is True
def test_audit_redacts_secret_values(session):
    record=record_audit(AuditRepository(session),user_id="u1",action="login",entity_type="session",details={"access_token":"secret","safe":"ok"})
    assert record.details == {"access_token":"[REDACTED]","safe":"ok"}

def test_audit_redacts_evidence_encryption_keys(session):
    record=record_audit(AuditRepository(session),user_id="u1",action="configure",entity_type="evidence",details={"encryption_key":"one","LEVI_EVIDENCE_ENCRYPTION_KEY":"two","safe":"ok"})
    assert record.details == {"encryption_key":"[REDACTED]","LEVI_EVIDENCE_ENCRYPTION_KEY":"[REDACTED]","safe":"ok"}
