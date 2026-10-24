"""Coverage ledger models"""

import enum
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Text, DateTime, Enum, JSON, ForeignKey, Index, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db import Base


class CoverageStatus(str, enum.Enum):
    """Coverage unit status"""

    PLANNED = "planned"
    HUNTING = "hunting"
    COVERED = "covered"
    DEFERRED = "deferred"
    OUT_OF_SCOPE = "out_of_scope"
    PRIOR_COVERED_SAME_SOURCE = "prior_covered_same_source"
    PRIOR_NEEDS_VALIDATION = "prior_needs_validation"
    PRIOR_CONFIRMED_SAME_SOURCE = "prior_confirmed_same_source"


class CoverageUnit(Base):
    """Coverage ledger unit"""

    __tablename__ = "coverage_units"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    audit_run_id: Mapped[int] = mapped_column(ForeignKey("audit_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    unit_id: Mapped[str] = mapped_column(String(200), nullable=False, index=True)  # e.g., "file.py:func"
    unit_type: Mapped[str] = mapped_column(String(50), nullable=False)  # function, class, module, config
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    line_start: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    line_end: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    attack_class: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    status: Mapped[CoverageStatus] = mapped_column(Enum(CoverageStatus), nullable=False, default=CoverageStatus.PLANNED, index=True)
    hunter_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    hunter_result: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    verifier_result: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    prior_run_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    metadata: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    audit_run: Mapped["AuditRun"] = relationship(back_populates="coverage_units")

    __table_args__ = (
        Index("ix_coverage_units_audit_run_status", "audit_run_id", "status"),
        Index("ix_coverage_units_unit_id", "unit_id"),
        Index("ix_coverage_units_attack_class", "attack_class"),
    )

    def __repr__(self) -> str:
        return f"<CoverageUnit(id={self.id}, unit_id={self.unit_id}, status={self.status})>"
