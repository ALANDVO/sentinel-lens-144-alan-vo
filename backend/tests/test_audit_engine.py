"""Audit engine tests"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from app.services.audit_engine import AuditEngine, AttackClass, HuntResult
from app.models.audit import AuditRun, AuditStatus, AuditProfile
from app.models.finding import Finding, FindingStatus, FindingSeverity
from app.models.coverage import CoverageUnit, CoverageStatus
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture
def mock_db():
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def sample_audit_run():
    return AuditRun(
        id=1,
        target_repo="https://github.com/test/repo",
        target_ref="main",
        profile=AuditProfile.STANDARD,
        status=AuditStatus.PENDING,
        config={},
        created_at=datetime.now(timezone.utc),
    )


@pytest.mark.asyncio
async def test_audit_engine_initialization(mock_db, sample_audit_run):
    engine = AuditEngine(mock_db, sample_audit_run)
    assert engine.db == mock_db
    assert engine.audit_run == sample_audit_run


@pytest.mark.asyncio
async def test_run_reconnaissance_creates_coverage_units(mock_db, sample_audit_run):
    engine = AuditEngine(mock_db, sample_audit_run)
    
    # Mock db.add and db.commit
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()
    
    units = await engine.run_reconnaissance()
    
    assert len(units) > 0
    assert all(isinstance(u, CoverageUnit) for u in units)
    assert all(u.audit_run_id == sample_audit_run.id for u in units)
    assert all(u.status == CoverageStatus.PLANNED for u in units)
    assert mock_db.add.call_count == len(units)
    assert mock_db.commit.call_count >= 1


@pytest.mark.asyncio
async def test_hunt_unit_injection_pattern():
    engine = AuditEngine(AsyncMock(), AuditRun(id=1, target_repo="test", profile=AuditProfile.STANDARD, status=AuditStatus.PENDING, config={}, created_at=datetime.now(timezone.utc)))
    
    unit = CoverageUnit(
        id=1,
        audit_run_id=1,
        unit_id="test:func",
        unit_type="function",
        file_path="src/db/query.py",
        line_start=10,
        line_end=30,
        attack_class=AttackClass.INJECTION.value,
        status=CoverageStatus.PLANNED,
    )
    
    findings = engine._hunt_unit(unit)
    
    assert len(findings) > 0
    assert findings[0]["attack_class"] == AttackClass.INJECTION.value
    assert "evidence" in findings[0]
    assert "remediation" in findings[0]


@pytest.mark.asyncio
async def test_hunt_unit_no_patterns():
    engine = AuditEngine(AsyncMock(), AuditRun(id=1, target_repo="test", profile=AuditProfile.STANDARD, status=AuditStatus.PENDING, config={}, created_at=datetime.now(timezone.utc)))
    
    unit = CoverageUnit(
        id=1,
        audit_run_id=1,
        unit_id="test:func",
        unit_type="class",
        file_path="src/models/user.py",
        line_start=1,
        line_end=50,
        attack_class=AttackClass.BUSINESS_LOGIC.value,
        status=CoverageStatus.PLANNED,
    )
    
    findings = engine._hunt_unit(unit)
    
    # Business logic has patterns so should find something
    assert isinstance(findings, list)


@pytest.mark.asyncio
async def test_attack_class_patterns_coverage():
    """Verify all attack classes have patterns defined"""
    for attack_class in AttackClass:
        patterns = AuditEngine.ATTACK_CLASS_PATTERNS.get(attack_class, [])
        assert len(patterns) > 0, f"Attack class {attack_class} has no patterns"


@pytest.mark.asyncio
async def test_run_hunting_updates_unit_status(mock_db, sample_audit_run):
    engine = AuditEngine(mock_db, sample_audit_run)
    
    units = [
        CoverageUnit(
            id=i,
            audit_run_id=1,
            unit_id=f"test:func{i}",
            unit_type="function",
            file_path=f"src/test{i}.py",
            line_start=10,
            line_end=20,
            attack_class=AttackClass.INJECTION.value,
            status=CoverageStatus.PLANNED,
        )
        for i in range(3)
    ]
    
    mock_db.commit = AsyncMock()
    
    results = await engine.run_hunting(units)
    
    assert len(results) == 3
    assert all(isinstance(r, HuntResult) for r in results)
    assert all(r.coverage_status == CoverageStatus.COVERED for r in results)
    assert mock_db.commit.call_count >= 3


@pytest.mark.asyncio
async def test_run_validation_creates_findings(mock_db, sample_audit_run):
    engine = AuditEngine(mock_db, sample_audit_run)
    
    hunt_results = [
        HuntResult(
            unit_id="test:func1",
            findings=[
                {
                    "title": "Test Finding",
                    "description": "Test description",
                    "severity": FindingSeverity.MEDIUM.value,
                    "evidence": {"patterns_matched": ["sql", "query"]},
                    "remediation": {"strategy": "review_and_harden"},
                }
            ],
            coverage_status=CoverageStatus.COVERED,
        )
    ]
    
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()
    
    findings = await engine.run_validation(hunt_results)
    
    assert len(findings) == 1
    assert findings[0].status == FindingStatus.CONFIRMED
    assert findings[0].verification["verified"] is True
    assert findings[0].verification["verifier"] == "deterministic_engine"


@pytest.mark.asyncio
async def test_run_reporting_generates_summary(mock_db, sample_audit_run):
    engine = AuditEngine(mock_db, sample_audit_run)
    
    # Add mock findings and coverage
    mock_findings = [
        Finding(id=1, audit_run_id=1, status=FindingStatus.CONFIRMED, severity=FindingSeverity.HIGH, title="Test", description="Test", attack_class="injection", evidence={}, remediation={}, verification={}, created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc)),
        Finding(id=2, audit_run_id=1, status=FindingStatus.REJECTED, severity=FindingSeverity.MEDIUM, title="Test2", description="Test2", attack_class="xss", evidence={}, remediation={}, verification={}, created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc)),
    ]
    mock_coverage = [
        CoverageUnit(id=1, audit_run_id=1, unit_id="a", unit_type="function", file_path="a.py", attack_class="injection", status=CoverageStatus.COVERED, hunter_result={}, verifier_result={}, metadata={}, created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc)),
        CoverageUnit(id=2, audit_run_id=1, unit_id="b", unit_type="function", file_path="b.py", attack_class="xss", status=CoverageStatus.DEFERRED, hunter_result={}, verifier_result={}, metadata={}, created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc)),
    ]
    
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = mock_findings
    mock_db.execute.return_value = mock_result
    
    mock_result2 = MagicMock()
    mock_result2.scalars.return_value.all.return_value = mock_coverage
    mock_db.execute.return_value = mock_result2
    
    # Need to alternate return values
    mock_db.execute.side_effect = [mock_result, mock_result2]
    
    report = await engine.run_reporting()
    
    assert report["audit_run_id"] == 1
    assert report["summary"]["total_findings"] == 2
    assert report["summary"]["by_status"]["confirmed"] == 1
    assert report["summary"]["by_status"]["rejected"] == 1
    assert report["summary"]["total_coverage_units"] == 2
    assert report["summary"]["coverage_by_status"]["covered"] == 1
    assert report["summary"]["coverage_by_status"]["deferred"] == 1


@pytest.mark.asyncio
async def test_full_audit_workflow(mock_db, sample_audit_run):
    engine = AuditEngine(mock_db, sample_audit_run)
    
    # Mock all the internal methods
    engine.run_reconnaissance = AsyncMock(return_value=[
        CoverageUnit(id=1, audit_run_id=1, unit_id="test", unit_type="function", file_path="test.py", attack_class="injection", status=CoverageStatus.PLANNED, hunter_result={}, verifier_result={}, metadata={}, created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc))
    ])
    engine.run_hunting = AsyncMock(return_value=[
        HuntResult(unit_id="test", findings=[], coverage_status=CoverageStatus.COVERED)
    ])
    engine.run_validation = AsyncMock(return_value=[])
    engine.run_reporting = AsyncMock(return_value={"audit_run_id": 1, "summary": {}})
    
    mock_db.commit = AsyncMock()
    
    report = await engine.run_full_audit()
    
    assert sample_audit_run.status == AuditStatus.COMPLETED
    assert sample_audit_run.started_at is not None
    assert sample_audit_run.completed_at is not None
    assert report["audit_run_id"] == 1
