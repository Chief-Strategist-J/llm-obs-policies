# Parameter Specification: `error`

| Attribute | Specification |
| :--- | :--- |
| **Identifier** | `error` |
| **Category** | `response` |
| **Surface** | Response JSON Envelope Root Field |
| **Requirement Level** | **MANDATORY on Failure; FORBIDDEN on Success** |
| **Criticality Tier** | **CRITICAL (P0)** |
| **Standard / Reference** | Canonical Error Object |
| **Schema Type** | `object` |

---

### 1. Architectural Purpose & Scope
Structured container for failure diagnostics. Holds canonical machine-readable error code, sanitized human message, retryable flag, and field validation violations.

---

### 2. Open Standard Contract Schema (OpenAPI 3.1 & JSON Schema 2020-12)

```yaml
name: error
in: body
required: true
schema:
  type: object
  pattern: "N/A"
```

---

### 3. Wire Grammar (ABNF — RFC 5234)

```abnf
error = "{" code-entry "," message-entry "," retryable-entry [ "," details-entry ] "}"
```

---

### 4. Normative Lifecycle Protocol (IETF RFC 2119)

1. IF response is an error, the server MUST include `error` object containing `code`, `message`, and `retryable`.
2. IF validation checks failed, the server MUST include `details` array.
3. IF response is a success, `error` key MUST NOT exist.

---

### 5. Deterministic Decision Table (DMN / Invariant Truth Table)

| Input Condition | Predicate Evaluation | Output Value | Secondary Effect |
| :--- | :--- | :--- | :--- |
| Error response | `!is_success` | `Canonical Error Object` | Populate error block |
| Success response | `is_success` | `OMITTED` | Error key must not exist |

---

### 6. Declarative Logic Expression (CEL — Common Expression Language)

```cel
!is_success ? {"code": error_code, "message": error_message, "retryable": is_retryable, "details": error_details} : null
```

---

### 7. Failure & Security Enforcement
- Forbidden on success responses.
- Code must match the Canonical Error Code Dictionary.
- Must never leak SQL syntax, raw exceptions, or internal paths.

---

### 8. Protocol Wire Example

```http
"error": { "code": "VALIDATION_FAILED", "message": "Field validation failed.", "retryable": false }
```
