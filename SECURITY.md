# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability, please report it privately.

**Do not open a public GitHub issue for security vulnerabilities.**

Email: vinodwaghmare890@gmail.com

Include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

You will receive an acknowledgment within 48 hours.

## Current Security Model

### Authentication
- Phase 0-9: Header-based user identification (`X-User-ID` header)
- Phase 11 (planned): JWT authentication with token validation

### User Isolation
- Row-level security enabled on the `memories` table
- Every database query filters by `user_id`
- No cross-user data access is possible through the API

### Data Protection
- Soft delete: deleted memories are flagged, not removed from the database
- Audit logging: all operations are logged to an append-only table
- PII detection: regex-based filtering for credit cards, SSNs, API keys
- Phase 11 (planned): encryption at rest via KMS, Microsoft Presidio for PII

### API Security
- CORS restricted to configured origins in production
- No sensitive data in URL parameters
- API keys stored as environment variables, not in code

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | Yes       |
