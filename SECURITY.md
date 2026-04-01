# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| main branch | ✅ Active support |
| feature branches | ⚠️ Development only |

## Reporting a Vulnerability

This project is an IT Business Continuity Planning / IT Service Continuity Management (BCP/ITSCM) system.
Security vulnerabilities should be reported responsibly.

### How to Report

**Please do NOT report security vulnerabilities via public GitHub Issues.**

Instead, use one of the following methods:

1. **GitHub Private Vulnerability Reporting** (preferred):
   Navigate to the [Security tab](../../security/advisories/new) and click "Report a vulnerability".

2. **Email**: Contact the maintainer directly via the GitHub profile associated with this repository.

### What to Include

- Type of vulnerability (e.g., SQL injection, XSS, authentication bypass)
- Location (file path, line number, URL endpoint)
- Steps to reproduce
- Potential impact assessment
- Any suggested fixes (optional)

### Response Timeline

| Phase | Target |
|-------|--------|
| Acknowledgement | Within 72 hours |
| Initial assessment | Within 7 days |
| Fix / Mitigation | Within 30 days (critical), 90 days (high/medium) |
| Public disclosure | After fix is deployed |

## Security Standards

This system is designed to comply with:

| Standard | Requirement | Area |
|----------|-------------|------|
| ISO 27001:2022 | A.5.29 — IS continuity during adversity | BCP/ITSCM core |
| ISO 27001:2022 | A.5.30 — ICT readiness for business continuity | Infrastructure |
| ISO 20000-1:2018 | Clause 8.7 — Service continuity management | ITSM integration |
| NIST CSF 2.0 | RECOVER RC — Recovery planning & improvements | Incident response |

## Known Deferred Vulnerabilities

The following vulnerabilities are known and tracked for future remediation:

| CVE / GHSA | Component | Severity | Tracking Issue | Target Fix |
|------------|-----------|----------|----------------|------------|
| CVE-2025-54121 | starlette (via FastAPI) | Medium | [#73](../../issues/73) | FastAPI 0.120.x+ upgrade |
| CVE-2025-62727 | starlette (via FastAPI) | Medium | [#73](../../issues/73) | FastAPI 0.120.x+ upgrade |
| GHSA-9g9p-9gw9-jx7f | Next.js < 16 | High | [#72](../../issues/72) | Next.js 16 upgrade |
| GHSA-h25m-26qc-wcjf | Next.js < 16 | High | [#72](../../issues/72) | Next.js 16 upgrade |
| GHSA-ggv3-7p47-pfv8 | Next.js < 16 | High | [#72](../../issues/72) | Next.js 16 upgrade |
| GHSA-3x4c-7xq6-9pq8 | Next.js < 16 | High | [#72](../../issues/72) | Next.js 16 upgrade |

These are actively monitored via automated Security Scan CI (weekly, Mondays 03:00 UTC).

## Security Scan CI

Automated vulnerability scanning runs weekly and on-demand:

- **Python backend**: `pip-audit` against `requirements.txt`
- **Node.js frontend**: `npm audit --audit-level=critical`
- **Container images**: Trivy scan (CRITICAL + HIGH severity)

CI workflow: [`.github/workflows/security-scan.yml`](.github/workflows/security-scan.yml)
