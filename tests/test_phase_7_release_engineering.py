"""Offline tests for Phase 7 release-engineering controls."""

import asyncio
from pathlib import Path
import httpx

from bot.status_api import app
from levi.deployment.environment import validate_environment
from scripts.performance_baseline import measure
from scripts.security_audit import audit

ROOT = Path(__file__).resolve().parents[1]


def request(path):
    async def call():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.get(path)
    return asyncio.run(call())


def test_development_environment_is_safe_by_default():
    result = validate_environment({})
    assert result.valid and result.warnings


def test_production_requires_encryption_key():
    result = validate_environment({"LEVI_ENV": "production", "LEVI_CORS_ORIGINS": "https://app.test"})
    assert "LEVI_EVIDENCE_ENCRYPTION_KEY is required in production" in result.errors


def test_production_requires_explicit_cors():
    result = validate_environment({"LEVI_ENV": "production", "LEVI_EVIDENCE_ENCRYPTION_KEY": "configured"})
    assert "LEVI_CORS_ORIGINS is required in production" in result.errors


def test_production_rejects_plaintext_evidence():
    result = validate_environment({"LEVI_ENV": "production", "LEVI_EVIDENCE_ENCRYPTION_KEY": "x", "LEVI_CORS_ORIGINS": "https://app.test", "LEVI_ALLOW_PLAINTEXT_EVIDENCE": "true"})
    assert not result.valid


def test_environment_rejects_auto_execution():
    assert not validate_environment({"AUTO_EXECUTE": "true"}).valid


def test_environment_rejects_non_paper_mode():
    assert not validate_environment({"TASTYTRADE_PAPER": "false"}).valid


def test_errors_do_not_contain_secret_value():
    secret = "do-not-leak-this-value"
    result = validate_environment({"LEVI_ENV": "production", "LEVI_EVIDENCE_ENCRYPTION_KEY": secret})
    assert secret not in " ".join(result.errors)


def test_health_endpoint_reports_version():
    response = request("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert response.json()["version"] == "0.1.0-alpha"


def test_ready_endpoint_accepts_safe_development_environment(monkeypatch):
    monkeypatch.delenv("AUTO_EXECUTE", raising=False)
    monkeypatch.delenv("LEVI_ENV", raising=False)
    assert request("/ready").status_code == 200


def test_ready_endpoint_fails_closed(monkeypatch):
    monkeypatch.setenv("AUTO_EXECUTE", "true")
    response = request("/ready")
    assert response.status_code == 503
    assert response.json()["detail"]["status"] == "not_ready"


def test_dockerfile_is_hardened():
    text = (ROOT / "Dockerfile").read_text()
    assert "python:3.11-slim" in text and "USER levi" in text and "/ready" in text


def test_dockerignore_excludes_sensitive_content():
    entries = (ROOT / ".dockerignore").read_text().splitlines()
    assert {".env", "workspace", ".git"}.issubset(entries)


def test_local_compose_is_paper_only_and_has_postgres():
    text = (ROOT / "docker-compose.yml").read_text()
    assert "postgres:16-alpine" in text and 'AUTO_EXECUTE: "false"' in text


def test_production_compose_requires_security_configuration():
    text = (ROOT / "docker-compose.prod.yml").read_text()
    assert "LEVI_EVIDENCE_ENCRYPTION_KEY:?" in text and "LEVI_CORS_ORIGINS:?" in text


def test_release_workflow_is_tag_gated():
    text = (ROOT / ".github/workflows/release.yml").read_text()
    assert '"v*"' in text and "--verify-tag" in text and "workflow_dispatch" not in text


def test_required_release_script_entrypoints_exist():
    required = ["install.ps1", "install.sh", "security_check.py", "performance_check.py", "smoke_test.py"]
    assert all((ROOT / "scripts" / name).is_file() for name in required)


def test_ci_runs_frontend_install_test_lint_and_build():
    text = (ROOT / ".github/workflows/ci.yml").read_text()
    assert all(command in text for command in ("npm ci", "npm test", "npm run lint", "npm run build"))


def test_dashboard_exposes_offline_test_command():
    text = (ROOT / "dashboard/package.json").read_text()
    assert '"test"' in text and "node --test" in text


def test_security_audit_detects_private_key(tmp_path):
    (tmp_path / "leak.txt").write_text("-----BEGIN PRIVATE KEY-----")
    assert audit(tmp_path) == ["possible embedded secret: leak.txt"]


def test_security_audit_detects_dotenv(tmp_path):
    (tmp_path / ".env").write_text("SAFE=not-inspected")
    assert audit(tmp_path) == ["forbidden release file: .env"]


def test_repository_security_audit_passes():
    assert audit(ROOT) == []


def test_performance_baseline_meets_targets():
    result = measure()
    assert result["startup_under_5s"] and result["response_under_1s"]


def test_public_documentation_inventory_exists():
    expected = [
        "README.md", "SECURITY.md", "CHANGELOG.md",
        "docs/GETTING_STARTED.md", "docs/API_REFERENCE.md",
        "docs/TROUBLESHOOTING.md", "docs/FAQ.md",
        "docs/CONTRIBUTING.md", "docs/SECURITY.md",
        "docs/ARCHITECTURE.md", "docs/PHASE_7_DEPLOYMENT.md",
    ]
    assert all((ROOT / name).is_file() for name in expected)


def test_release_notes_are_explicitly_draft():
    text = (ROOT / "docs/releases/v0.1.0-alpha.md").read_text().lower()
    assert "draft" in text and "not tagged or published" in text
