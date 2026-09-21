# Parameter Specification: `x-audit-log-id`

| Attribute | Specification |
| :--- | :--- |
| **Identifier** | `x-audit-log-id` |
| **Category** | `headers` |
| **Surface** | Outbound HTTP Transport Response Header |
| **Requirement Level** | **MANDATORY on Audited Mutations & Security Failures** |
| **Criticality Tier** | **CRITICAL (P0)** |
| **Standard / Reference** | audit-{unix_ms}-{random_hex} |
| **Schema Type** | `string` |

---

### 1. Architectural Purpose & Scope
Cryptographically unforgeable audit ledger record identifier. Informs caller that state mutation or security failure was durably committed to the audit trail.

---

### 2. Open Standard Contract Schema (OpenAPI 3.1 & JSON Schema 2020-12)

```yaml
name: x-audit-log-id
in: header
required: true
schema:
  type: string
  pattern: "^audit-[0-9]{13,}-[a-fA-F0-9]{8,}$"
```

---

### 3. Wire Grammar (ABNF — RFC 5234)

```abnf
x-audit-log-id = "audit-" 13*DIGIT "-" 8*HEXDIG
```

---

### 4. Normative Lifecycle Protocol (IETF RFC 2119)

1. Upon completing a state mutation or recording a security event, the server MUST synchronously generate an immutable audit ledger entry.
2. The server MUST inject `x-audit-log-id` into response headers.
3. The value MUST exactly mirror `meta.auditLogId`.

---

### 5. Deterministic Decision Table (DMN / Invariant Truth Table)

| Input Condition | Predicate Evaluation | Output Value | Secondary Effect |
| :--- | :--- | :--- | :--- |
| Audited mutation or security rejection | `audit_log_id != null` | `audit_log_id` | Inject header and meta.auditLogId |
| Read-only non-audited query | `audit_log_id == null` | `null` | Omit header |

---

### 6. Declarative Logic Expression (CEL — Common Expression Language)

```cel
audit_log_id != null ? audit_log_id : null
```

---

### 7. Failure & Security Enforcement
- Must be present on any mutating operation (POST/PUT/PATCH/DELETE) that alters persistent state.
- Must be present on security rejections (401/403/409) for compliance forensic verification.

---

### 8. Protocol Wire Example

```http
x-audit-log-id: audit-9c4f-7b1a2d3e-4418
```
