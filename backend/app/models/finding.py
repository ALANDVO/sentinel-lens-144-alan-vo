"""Finding models"""

import enum
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Text, DateTime, Enum, JSON, ForeignKey, Index, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db import Base


class FindingStatus(str, enum.Enum):
    """Finding verification status"""

    PROPOSED = "proposed"
    NEEDS_VALIDATION = "needs_validation"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    DEFERRED = "deferred"


class FindingSeverity(str, enum.Enum):
    """Finding severity levels"""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"
    HARDENING = "hardening"


class Finding(Base):
    """Security finding record"""

    __tablename__ = "findings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    audit_run_id: Mapped[int] = mapped_column(ForeignKey("audit_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    status: Mapped[FindingStatus] = mapped_column(Enum(FindingStatus), nullable=False, default=FindingStatus.PROPOSED, index=True)
    severity: Mapped[FindingSeverity] = mapped_column(Enum(FindingSeverity), nullable=False, default=FindingSeverity.MEDIUM, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    file_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    line_start: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    line_end: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    attack_class: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    evidence: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    remediation: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    verification: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    llm_explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
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
    audit_run: Mapped["AuditRun"] = relationship(back_populates="findings")

    __table_args__ = (
        Index("ix_findings_audit_run_status", "audit_run_id", "status"),
        Index("ix_findings_attack_class", "attack_class"),
        Index("ix_findings_severity", "severity"),
    )

    def __repr__(self) -> str:
        return f"<Finding(id={self.id}, audit_run={self.audit_run_id}, status={self.status}, severity={self.severity})>"
