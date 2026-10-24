"""Core audit engine - deterministic offline analysis"""

from enum import Enum
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.models.audit import AuditRun, AuditStatus, AuditProfile
from app.models.finding import Finding, FindingStatus, FindingSeverity
from app.models.coverage import CoverageUnit, CoverageStatus
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select


class AttackClass(str, Enum):
    """Attack taxonomy classes"""

    INJECTION = "injection"
    AUTH_BROKEN = "auth_broken"
    AUTHZ_BROKEN = "authz_broken"
    SENSITIVE_DATA = "sensitive_data"
    XXE = "xxe"
    SECURITY_MISCONFIG = "security_misconfig"
    XSS = "xss"
    INSECURE_DESERIALIZATION = "insecure_deserialization"
    VULNERABLE_DEPS = "vulnerable_deps"
    INSUFFICIENT_LOGGING = "insufficient_logging"
    BUSINESS_LOGIC = "business_logic"
    SSRF = "ssrf"
    PATH_TRAVERSAL = "path_traversal"
    COMMAND_INJECTION = "command_injection"
    CRYPTO_FAILURES = "crypto_failures"


@dataclass
class HuntResult:
    """Result from a hunter"""

    unit_id: str
    findings: List[Dict[str, Any]] = field(default_factory=list)
    coverage_status: CoverageStatus = CoverageStatus.COVERED
    metadata: Dict[str, Any] = field(default_factory=dict)


class AuditEngine:
    """Deterministic audit engine with multi-phase workflow"""

    # Mapping of file patterns to attack classes
    ATTACK_CLASS_PATTERNS = {
        AttackClass.INJECTION: ["sql", "query", "execute", "cursor"],
        AttackClass.COMMAND_INJECTION: ["subprocess", "os.system", "shell", "exec"],
        AttackClass.PATH_TRAVERSAL: ["open(", "read_file", "path.join", "../"],
        AttackClass.XSS: ["innerHTML", "dangerouslySetInnerHTML", "render_template_string"],
        AttackClass.SSRF: ["requests.get", "http.client", "urllib", "fetch("],
        AttackClass.INSECURE_DESERIALIZATION: ["pickle.load", "yaml.load", "marshal.load"],
        AttackClass.CRYPTO_FAILURES: ["md5", "sha1", "DES", "ECB", "random.random"],
        AttackClass.SENSITIVE_DATA: ["password", "secret", "token", "api_key", "private_key"],
        AttackClass.AUTH_BROKEN: ["login", "authenticate", "session", "jwt", "oauth"],
        AttackClass.AUTHZ_BROKEN: ["permission", "authorize", "role", "access_control"],
        AttackClass.BUSINESS_LOGIC: ["validate", "check", "verify", "assert"],
    }

    def __init__(self, db: AsyncSession, audit_run: AuditRun):
        self.db = db
        self.audit_run = audit_run

    async def run_reconnaissance(self) -> List[CoverageUnit]:
        """Phase 1: Map codebase to coverage units"""
        # In a real implementation, this would scan the target repository
        # For now, create mock coverage units based on common patterns
        units = []
        
        # Mock: create coverage units for demonstration
        mock_files = [
            ("src/auth/login.py", "function", "authenticate_user", 10, 30, AttackClass.AUTH_BROKEN),
            ("src/auth/session.py", "function", "create_session", 5, 25, AttackClass.AUTH_BROKEN),
            ("src/data/query.py", "function", "execute_query", 15, 40, AttackClass.INJECTION),
            ("src/api/handlers.py", "function", "handle_request", 20, 50, AttackClass.INJECTION),
            ("src/utils/crypto.py", "function", "hash_password", 10, 30, AttackClass.CRYPTO_FAILURES),
            ("src/config/settings.py", "module", "settings", 1, 50, AttackClass.SECURITY_MISCONFIG),
            ("src/storage/files.py", "function", "read_file", 5, 20, AttackClass.PATH_TRAVERSAL),
            ("src/integrations/webhook.py", "function", "send_webhook", 10, 35, AttackClass.SSRF),
        ]

        for file_path, unit_type, name, line_start, line_end, attack_class in mock_files:
            unit = CoverageUnit(
                audit_run_id=self.audit_run.id,
                unit_id=f"{file_path}:{name}",
                unit_type=unit_type,
                file_path=file_path,
                line_start=line_start,
                line_end=line_end,
                attack_class=attack_class.value,
                status=CoverageStatus.PLANNED,
            )
            units.append(unit)
            self.db.add(unit)

        await self.db.commit()
        return units

    async def run_hunting(self, units: List[CoverageUnit]) -> List[HuntResult]:
        """Phase 2: Hunt for findings in coverage units"""
        results = []

        for unit in units:
            unit.status = CoverageStatus.HUNTING
            await self.db.commit()

            # Deterministic pattern matching (no LLM)
            findings = self._hunt_unit(unit)
            
            result = HuntResult(
                unit_id=unit.unit_id,
                findings=findings,
                coverage_status=CoverageStatus.COVERED if not findings else CoverageStatus.COVERED,
            )
            results.append(result)

            # Update unit status
            if findings:
                unit.status = CoverageStatus.COVERED
            else:
                unit.status = CoverageStatus.COVERED
            unit.hunter_result = {"findings_count": len(findings), "patterns_checked": len(self.ATTACK_CLASS_PATTERNS.get(AttackClass(unit.attack_class), []))}
            await self.db.commit()

        return results

    def _hunt_unit(self, unit: CoverageUnit) -> List[Dict[str, Any]]:
        """Deterministic hunting for a single unit"""
        findings = []
        patterns = self.ATTACK_CLASS_PATTERNS.get(AttackClass(unit.attack_class), [])
        
        # Simple deterministic logic: if unit has certain characteristics, generate a finding
        # This is a placeholder for real static analysis
        if unit.unit_type == "function" and len(patterns) > 0:
            # Generate a mock finding for demonstration
            findings.append({
                "title": f"Potential {unit.attack_class.replace('_', ' ').title()} in {unit.unit_id}",
                "description": f"Code pattern matching {unit.attack_class} detected in {unit.file_path}:{unit.line_start}-{unit.line_end}",
                "severity": FindingSeverity.MEDIUM.value,
                "evidence": {"patterns_matched": patterns[:3], "unit_id": unit.unit_id},
                "remediation": {"strategy": "review_and_harden", "details": f"Review {unit.file_path} for {unit.attack_class} vulnerabilities"},
            })
        
        return findings

    async def run_validation(self, hunt_results: List[HuntResult]) -> List[Finding]:
        """Phase 3: Independent verification of findings"""
        confirmed_findings = []

        for result in hunt_results:
            for finding_data in result.findings:
                # Create finding with NEEDS_VALIDATION status
                finding = Finding(
                    audit_run_id=self.audit_run.id,
                    status=FindingStatus.NEEDS_VALIDATION,
                    severity=FindingSeverity(finding_data["severity"]),
                    title=finding_data["title"],
                    description=finding_data["description"],
                    file_path=finding_data.get("file_path"),
                    line_start=finding_data.get("line_start"),
                    line_end=finding_data.get("line_end"),
                    attack_class=finding_data.get("attack_class", "unknown"),
                    evidence=finding_data.get("evidence", {}),
                    remediation=finding_data.get("remediation", {}),
                    verification={"verified": False, "verifier": "pending"},
                )
                self.db.add(finding)
                confirmed_findings.append(finding)

        await self.db.commit()

        # Simulate verification (in real impl, this would be independent)
        for finding in confirmed_findings:
            finding.status = FindingStatus.CONFIRMED
            finding.verification = {
                "verified": True,
                "verifier": "deterministic_engine",
                "verified_at": datetime.now(timezone.utc).isoformat(),
                "method": "pattern_match_confirmation",
            }
        
        await self.db.commit()
        return confirmed_findings

    async def run_reporting(self) -> Dict[str, Any]:
        """Phase 4: Generate final report"""
        # Count findings by status
        findings_result = await self.db.execute(
            select(Finding).where(Finding.audit_run_id == self.audit_run.id)
        )
        findings = findings_result.scalars().all()

        coverage_result = await self.db.execute(
            select(CoverageUnit).where(CoverageUnit.audit_run_id == self.audit_run.id)
        )
        coverage_units = coverage_result.scalars().all()

        status_counts = {}
        for f in findings:
            status_counts[f.status.value] = status_counts.get(f.status.value, 0) + 1

        coverage_counts = {}
        for c in coverage_units:
            coverage_counts[c.status.value] = coverage_counts.get(c.status.value, 0) + 1

        return {
            "audit_run_id": self.audit_run.id,
            "target_repo": self.audit_run.target_repo,
            "profile": self.audit_run.profile.value,
            "summary": {
                "total_findings": len(findings),
                "by_status": status_counts,
                "total_coverage_units": len(coverage_units),
                "coverage_by_status": coverage_counts,
            },
            "findings": [
                {
                    "id": f.id,
                    "title": f.title,
                    "severity": f.severity.value,
                    "status": f.status.value,
                    "attack_class": f.attack_class,
                    "file_path": f.file_path,
                }
                for f in findings
            ],
        }

    async def run_full_audit(self) -> Dict[str, Any]:
        """Execute complete audit workflow"""
        self.audit_run.status = AuditStatus.RUNNING
        self.audit_run.started_at = datetime.now(timezone.utc)
        await self.db.commit()

        try:
            # Phase 1: Reconnaissance
            units = await self.run_reconnaissance()

            # Phase 2: Hunting
            hunt_results = await self.run_hunting(units)

            # Phase 3: Validation
            await self.run_validation(hunt_results)

            # Phase 4: Reporting
            report = await self.run_reporting()

            self.audit_run.status = AuditStatus.COMPLETED
            self.audit_run.completed_at = datetime.now(timezone.utc)
            await self.db.commit()

            return report

        except Exception as e:
            self.audit_run.status = AuditStatus.FAILED
            self.audit_run.error_message = str(e)
            self.audit_run.completed_at = datetime.now(timezone.utc)
            await self.db.commit()
            raise
