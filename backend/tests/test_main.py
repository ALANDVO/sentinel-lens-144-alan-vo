"""Backend tests"""

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import create_app
from app.db import Base, engine, async_session_maker
from app.models.audit import AuditRun, AuditStatus, AuditProfile
from app.models.finding import Finding, FindingStatus, FindingSeverity
from app.models.coverage import CoverageUnit, CoverageStatus


@pytest.fixture(scope="session")
def app():
    return create_app()


@pytest.fixture(scope="function")
async def db_session():
    """Create a fresh database for each test"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    async with async_session_maker() as session:
        yield session
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_health_check(client):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "1.0.0"


@pytest.mark.asyncio
async def test_create_audit_run(client):
    response = await client.post("/api/audits", json={
        "target_repo": "https://github.com/example/repo",
        "target_ref": "main",
        "profile": "standard",
        "config": {}
    })
    assert response.status_code == 201
    data = response.json()
    assert data["target_repo"] == "https://github.com/example/repo"
    assert data["target_ref"] == "main"
    assert data["profile"] == "standard"
    assert data["status"] == "pending"
    assert data["id"] > 0


@pytest.mark.asyncio
async def test_list_audit_runs(client):
    # Create a few runs
    for i in range(3):
        await client.post("/api/audits", json={
            "target_repo": f"https://github.com/example/repo{i}",
            "profile": "quick",
        })
    
    response = await client.get("/api/audits")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert all(r["profile"] == "quick" for r in data)


@pytest.mark.asyncio
async def test_get_audit_run(client):
    create_resp = await client.post("/api/audits", json={
        "target_repo": "https://github.com/example/test",
        "profile": "deep",
    })
    audit_id = create_resp.json()["id"]
    
    response = await client.get(f"/api/audits/{audit_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == audit_id
    assert data["target_repo"] == "https://github.com/example/test"
    assert data["profile"] == "deep"


@pytest.mark.asyncio
async def test_get_nonexistent_audit(client):
    response = await client.get("/api/audits/99999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_findings_empty(client):
    create_resp = await client.post("/api/audits", json={"target_repo": "test"})
    audit_id = create_resp.json()["id"]
    
    response = await client.get(f"/api/audits/{audit_id}/findings")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_list_coverage_empty(client):
    create_resp = await client.post("/api/audits", json={"target_repo": "test"})
    audit_id = create_resp.json()["id"]
    
    response = await client.get(f"/api/audits/{audit_id}/coverage")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_import_prior_run(client):
    # Create two audit runs
    run1 = await client.post("/api/audits", json={"target_repo": "repo1", "profile": "standard"})
    run1_id = run1.json()["id"]
    
    run2 = await client.post("/api/audits", json={"target_repo": "repo2", "profile": "standard"})
    run2_id = run2.json()["id"]
    
    # Import from run1 into run2
    response = await client.post(f"/api/audits/{run2_id}/import", json={"prior_run_id": run1_id})
    assert response.status_code == 200
    assert response.json()["imported"] == 0  # No confirmed findings in run1


@pytest.mark.asyncio
async def test_export_audit(client):
    create_resp = await client.post("/api/audits", json={"target_repo": "export-test"})
    audit_id = create_resp.json()["id"]
    
    response = await client.get(f"/api/audits/{audit_id}/export")
    assert response.status_code == 200
    data = response.json()
    assert data["audit_run"]["id"] == audit_id
    assert data["audit_run"]["target_repo"] == "export-test"
    assert "findings" in data
    assert "coverage" in data


@pytest.mark.asyncio
async def test_pagination(client):
    for i in range(25):
        await client.post("/api/audits", json={"target_repo": f"repo{i}"})
    
    # Test limit
    response = await client.get("/api/audits?limit=10")
    assert response.status_code == 200
    assert len(response.json()) == 10
    
    # Test offset
    response = await client.get("/api/audits?limit=10&offset=10")
    assert response.status_code == 200
    assert len(response.json()) == 10


@pytest.mark.asyncio
async def test_filter_by_target_repo(client):
    await client.post("/api/audits", json={"target_repo": "filter-test-a"})
    await client.post("/api/audits", json={"target_repo": "filter-test-b"})
    
    response = await client.get("/api/audits?target_repo=filter-test-a")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["target_repo"] == "filter-test-a"


@pytest.mark.asyncio
async def test_filter_by_status(client):
    await client.post("/api/audits", json={"target_repo": "status-test-1"})
    await client.post("/api/audits", json={"target_repo": "status-test-2"})
    
    response = await client.get("/api/audits?status=pending")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert all(r["status"] == "pending" for r in data)
