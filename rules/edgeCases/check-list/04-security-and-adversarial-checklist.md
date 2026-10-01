# Checklist 04: Security & Adversarial Defense

**Source Reference**: [Security and Adversarial Edge Cases (Parts 29–43)](file:///home/btpl-lap-22/live/llm-obs-infra/policies/rules/edgeCases/security-and-adversarial-edge-cases.md)  
**Objective**: Harden trust boundaries, eliminate confused deputy bugs, enforce tenant isolation, prevent business logic abuse, and secure cryptographic operations.

---

## 1. Authentication & Session Lifecycle Gate

- [ ] **Credential vs. Identity Separation**:
  - [ ] Are authentication credentials (passwords, MFA tokens, API keys) separated from immutable identity IDs?
  - [ ] Are passwords hashed using memory-hard algorithms (Argon2id, bcrypt with high work factor, PBKDF2), never plain SHA-256?
- [ ] **Token Revocation & Rotation**:
  - [ ] Are refresh tokens single-use with automatic token family revocation upon reuse detection?
  - [ ] Is there an active revocation list or short TTL ($< 15\text{ mins}$) for stateless JWTs to support emergency user logout / credential reset?
  - [ ] Does changing a password or revoking permissions immediately invalidate all existing sessions and refresh tokens?
- [ ] **MFA & Recovery Edge Cases**:
  - [ ] Does step-up authentication or MFA challenge require validation *before* executing sensitive actions?
  - [ ] Are recovery codes hashed at rest, single-use, and rate-limited against brute-force attempts?

---

## 2. Authorization & Tenant Isolation Gate

- [ ] **Elimination of BOLA / IDOR (Broken Object-Level Auth)**:
  - [ ] Does every query accessing tenant resources enforce a composite tenant check:
    ```sql
    -- Compliant Tenant Isolation
    SELECT * FROM documents 
    WHERE id = :doc_id AND tenant_id = :authenticated_tenant_id;
    ```
  - [ ] Are database-level policies (Postgres Row-Level Security `USING (tenant_id = current_setting('app.current_tenant_id'))`) implemented to prevent cross-tenant data leaks?
- [ ] **State-Based & Function-Level Authorization**:
  - [ ] Are permissions checked against the *target state* of an entity (e.g., cannot edit an invoice that is in `PAID` or `AUDITED` status)?
  - [ ] Are internal API endpoints protected by authorization interceptors rather than assuming perimeter firewall safety?
- [ ] **Confused Deputy & Ambient Authority Defenses**:
  - [ ] When a service acts on behalf of a user, does it pass both user identity and explicit scoped permissions (delegated authorization)?

---

## 3. Cryptography & Secrets Management

- [ ] **Zero Hardcoded Secrets**:
  - [ ] Are all API keys, database credentials, and signing secrets loaded via secure vault / secret managers (Vault, AWS Secrets Manager, GCP Secret Manager)?
  - [ ] Are automated pre-commit scanners (TruffleHog, Gitleaks) running in CI to block credential leaks?
- [ ] **Envelope Encryption & Key Rotation**:
  - [ ] Is sensitive at-rest data (PII, bank accounts, tokens) encrypted using envelope encryption (KMS Key Encryption Keys + local Data Encryption Keys)?
  - [ ] Does the system support automatic key rotation without breaking existing encrypted ciphertext?
- [ ] **Constant-Time Comparison**:
  - [ ] Are HMACs, tokens, and hashes compared using constant-time equality functions (`crypto.timingSafeEqual`, `subtle.timingSafeEqual`) to prevent timing side-channel attacks?

---

## 4. Injection, Deserialization & Parser Differentials

- [ ] **Parameterized Execution Everywhere**:
  - [ ] Are 100% of database queries parameterized (ORMs or prepared statements), with zero string interpolation in SQL/CQL/NoSQL queries?
- [ ] **Safe Deserialization**:
  - [ ] Are untrusted payloads prohibited from using polymorphic deserialization (Python `pickle`, Java serialized objects, YAML `unsafe_load`)?
  - [ ] Is JSON parsing validated against rigid schemas with limits on object depth ($< 32$) and payload size ($< 10\text{MB}$)?
- [ ] **Parser Discrepancy Hardening**:
  - [ ] Are reverse proxy (Nginx/Traefik) and backend application URL path decoders aligned to prevent path-traversal and request-smuggling bypasses?

---

## 5. Business Logic Abuse & Anti-Fraud

- [ ] **Concurrency Race Condition Defenses**:
  - [ ] Are promotional codes, coupons, and referral credits claimed using atomic database locks or conditional updates to prevent concurrent double-spend exploits?
- [ ] **Resource Exhaustion & Asymmetry of Effort**:
  - [ ] Are high-cost operations (password hashing, image resizing, regex matching, export generation) protected by strict rate limits and proof-of-work/CAPTCHA gates?
  - [ ] Are Regular Expressions evaluated with timeout limits or tested with tools to prevent ReDoS (Regular Expression Denial of Service)?
- [ ] **Inventory & Booking Reservation Expiry**:
  - [ ] Do temporary checkouts or item locks have strict time-to-live timeouts that automatically release held inventory?

---

## 6. Privacy, Audit Trail & Incident Response

- [ ] **PII Scrubbing in Logs & Traces**:
  - [ ] Are credit card numbers, passwords, auth tokens, and health/personal identifiers masked or redacted before reaching logging pipelines?
- [ ] **Immutable Audit Logging**:
  - [ ] Are all administrative operations, permission changes, data exports, and tenant config updates recorded in an append-only, tamper-evident audit log?
- [ ] **GDPR / Right-to-be-Forgotten Compliance**:
  - [ ] Is there an automated workflow for cascading user deletion/anonymization across databases, search indexes, backups, and third-party SaaS tools?
