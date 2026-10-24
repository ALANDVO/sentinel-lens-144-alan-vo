"""Audit run models"""

import enum
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Text, DateTime, Enum, JSON, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db import Base


class AuditStatus(str, enum.Enum):
    """Audit run status"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AuditProfile(str, enum.Enum):
    """Audit profile determining depth and cost"""

    QUICK = "quick"
    STANDARD = "standard"
    DEEP = "deep"


class AuditRun(Base):
    """Audit run record"""

    __tablename__ = "audit_runs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    target_repo: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    target_ref: Mapped[str] = mapped_column(String(200), nullable=True)  # branch/tag/commit
    profile: Mapped[AuditProfile] = mapped_column(Enum(AuditProfile), nullable=False, default=AuditProfile.STANDARD)
    status: Mapped[AuditStatus] = mapped_column(Enum(AuditStatus), nullable=False, default=AuditStatus.PENDING, index=True)
    config: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    findings: Mapped[list["Finding"]] = relationship(back_populates="audit_run", cascade="all, delete-orphan")
    coverage_units: Mapped[list["CoverageUnit"]] = relationship(back_populates="audit_run", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_audit_runs_target_repo_status", "target_repo", "status"),
        Index("ix_audit_runs_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<AuditRun(id={self.id}, repo={self.target_repo}, status={self.status})>"
