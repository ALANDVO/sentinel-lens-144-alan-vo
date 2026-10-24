"""API routes"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from app.db import get_db
from app.models.audit import AuditRun, AuditStatus, AuditProfile
from app.models.finding import Finding, FindingStatus, FindingSeverity
from app.models.coverage import CoverageUnit, CoverageStatus

router = APIRouter()


# Pydantic schemas
class AuditRunCreate(BaseModel):
    target_repo: str = Field(..., min_length=1, max_length=500)
    target_ref: Optional[str] = Field(None, max_length=200)
    profile: AuditProfile = Field(default=AuditProfile.STANDARD)
    config: dict = Field(default_factory=dict)


class AuditRunResponse(BaseModel):
    id: int
    target_repo: str
    target_ref: Optional[str]
    profile: AuditProfile
    status: AuditStatus
    config: dict
    error_message: Optional[str]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    findings_count: int = 0
    coverage_units_count: int = 0

    class Config:
        from_attributes = True


class FindingResponse(BaseModel):
    id: int
    audit_run_id: int
    status: FindingStatus
    severity: FindingSeverity
    title: str
    description: str
    file_path: Optional[str]
    line_start: Optional[int]
    line_end: Optional[int]
    attack_class: str
    evidence: dict
    remediation: dict
    verification: dict
    llm_explanation: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CoverageUnitResponse(BaseModel):
    id: int
    audit_run_id: int
    unit_id: str
    unit_type: str
    file_path: str
    line_start: Optional[int]
    line_end: Optional[int]
    attack_class: str
    status: CoverageStatus
    hunter_id: Optional[str]
    hunter_result: dict
    verifier_result: dict
    prior_run_id: Optional[int]
    metadata: dict
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class HealthResponse(BaseModel):
    status: str
    version: str


@router.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(status="healthy", version="1.0.0")


# Audit Runs
@router.post("/audits", response_model=AuditRunResponse, status_code=201)
async def create_audit_run(run: AuditRunCreate, db: AsyncSession = Depends(get_db)):
    audit_run = AuditRun(
        target_repo=run.target_repo,
        target_ref=run.target_ref,
        profile=run.profile,
        config=run.config,
        status=AuditStatus.PENDING,
    )
    db.add(audit_run)
    await db.commit()
    await db.refresh(audit_run)
    return AuditRunResponse(
        **audit_run.__dict__,
        findings_count=0,
        coverage_units_count=0,
    )


@router.get("/audits", response_model=List[AuditRunResponse])
async def list_audit_runs(
    target_repo: Optional[str] = Query(None),
    status: Optional[AuditStatus] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    query = select(AuditRun).options(
        selectinload(AuditRun.findings),
        selectinload(AuditRun.coverage_units),
    )
    if target_repo:
        query = query.where(AuditRun.target_repo == target_repo)
    if status:
        query = query.where(AuditRun.status == status)
    query = query.order_by(AuditRun.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(query)
    runs = result.scalars().all()
    return [
        AuditRunResponse(
            **run.__dict__,
            findings_count=len(run.findings),
            coverage_units_count=len(run.coverage_units),
        )
        for run in runs
    ]


@router.get("/audits/{audit_id}", response_model=AuditRunResponse)
async def get_audit_run(audit_id: int, db: AsyncSession = Depends(get_db)):
    query = select(AuditRun).options(
        selectinload(AuditRun.findings),
        selectinload(AuditRun.coverage_units),
    ).where(AuditRun.id == audit_id)
    result = await db.execute(query)
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Audit run not found")
    return AuditRunResponse(
        **run.__dict__,
        findings_count=len(run.findings),
        coverage_units_count=len(run.coverage_units),
    )


@router.get("/audits/{audit_id}/findings", response_model=List[FindingResponse])
async def list_findings(
    audit_id: int,
    status: Optional[FindingStatus] = Query(None),
    severity: Optional[FindingSeverity] = Query(None),
    attack_class: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    query = select(Finding).where(Finding.audit_run_id == audit_id)
    if status:
        query = query.where(Finding.status == status)
    if severity:
        query = query.where(Finding.severity == severity)
    if attack_class:
        query = query.where(Finding.attack_class == attack_class)
    query = query.order_by(Finding.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/audits/{audit_id}/coverage", response_model=List[CoverageUnitResponse])
async def get_coverage(
    audit_id: int,
    status: Optional[CoverageStatus] = Query(None),
    attack_class: Optional[str] = Query(None),
    limit: int = Query(200, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    query = select(CoverageUnit).where(CoverageUnit.audit_run_id == audit_id)
    if status:
        query = query.where(CoverageUnit.status == status)
    if attack_class:
        query = query.where(CoverageUnit.attack_class == attack_class)
    query = query.order_by(CoverageUnit.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/audits/{audit_id}/import")
async def import_prior_run(
    audit_id: int,
    prior_run_id: int,
    db: AsyncSession = Depends(get_db),
):
    # Verify both runs exist
    audit_run = await db.get(AuditRun, audit_id)
    if not audit_run:
        raise HTTPException(status_code=404, detail="Audit run not found")
    prior_run = await db.get(AuditRun, prior_run_id)
    if not prior_run:
        raise HTTPException(status_code=404, detail="Prior audit run not found")
    
    # Import confirmed findings as prior_covered_same_source coverage units
    prior_findings = await db.execute(
        select(Finding).where(Finding.audit_run_id == prior_run_id, Finding.status == FindingStatus.CONFIRMED)
    )
    imported = 0
    for finding in prior_findings.scalars():
        coverage = CoverageUnit(
            audit_run_id=audit_id,
            unit_id=f"{finding.file_path}:{finding.line_start}-{finding.line_end}" if finding.file_path else f"finding-{finding.id}",
            unit_type="finding",
            file_path=finding.file_path or "",
            line_start=finding.line_start,
            line_end=finding.line_end,
            attack_class=finding.attack_class,
            status=CoverageStatus.PRIOR_COVERED_SAME_SOURCE,
            prior_run_id=prior_run_id,
            metadata={"source_finding_id": finding.id, "source_severity": finding.severity.value},
        )
        db.add(coverage)
        imported += 1
    
    await db.commit()
    return {"imported": imported, "prior_run_id": prior_run_id}


@router.get("/audits/{audit_id}/export")
async def export_audit(
    audit_id: int,
    format: str = Query("json", pattern="^(json|csv)$"),
    db: AsyncSession = Depends(get_db),
):
    audit_run = await db.get(AuditRun, audit_id)
    if not audit_run:
        raise HTTPException(status_code=404, detail="Audit run not found")
    
    findings = await db.execute(select(Finding).where(Finding.audit_run_id == audit_id))
    coverage = await db.execute(select(CoverageUnit).where(CoverageUnit.audit_run_id == audit_id))
    
    return {
        "audit_run": {
            "id": audit_run.id,
            "target_repo": audit_run.target_repo,
            "target_ref": audit_run.target_ref,
            "profile": audit_run.profile.value,
            "status": audit_run.status.value,
            "created_at": audit_run.created_at.isoformat(),
            "completed_at": audit_run.completed_at.isoformat() if audit_run.completed_at else None,
        },
        "findings": [
            {
                "id": f.id,
                "status": f.status.value,
                "severity": f.severity.value,
                "title": f.title,
                "description": f.description,
                "file_path": f.file_path,
                "line_start": f.line_start,
                "line_end": f.line_end,
                "attack_class": f.attack_class,
                "evidence": f.evidence,
                "remediation": f.remediation,
                "verification": f.verification,
                "llm_explanation": f.llm_explanation,
                "created_at": f.created_at.isoformat(),
            }
            for f in findings.scalars()
        ],
        "coverage": [
            {
                "id": c.id,
                "unit_id": c.unit_id,
                "unit_type": c.unit_type,
                "file_path": c.file_path,
                "line_start": c.line_start,
                "line_end": c.line_end,
                "attack_class": c.attack_class,
                "status": c.status.value,
                "hunter_id": c.hunter_id,
                "hunter_result": c.hunter_result,
                "verifier_result": c.verifier_result,
                "prior_run_id": c.prior_run_id,
                "metadata": c.metadata,
                "created_at": c.created_at.isoformat(),
            }
            for c in coverage.scalars()
        ],
    }
