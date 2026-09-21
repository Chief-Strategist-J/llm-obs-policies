# Parameter Specification: `request.body`

| Attribute | Specification |
| :--- | :--- |
| **Identifier** | `request.body` |
| **Category** | `request` |
| **Surface** | Inbound HTTP Request Body Payload |
| **Requirement Level** | **MANDATORY on POST / PUT / PATCH** |
| **Criticality Tier** | **CRITICAL (P0)** |
| **Standard / Reference** | JSON Object (Closed Schema / No Undeclared Properties) |
| **Schema Type** | `object` |

---

### 1. Architectural Purpose & Scope
Contains the mutation data payload. Strictly validated against closed JSON schema where additionalProperties=false.

---

### 2. Open Standard Contract Schema (OpenAPI 3.1 & JSON Schema 2020-12)

```yaml
name: request.body
in: body
required: true
schema:
  type: object
  pattern: "N/A (JSON Object)"
```

---

### 3. Wire Grammar (ABNF — RFC 5234)

```abnf
request-body = JSON-text
```

---

### 4. Normative Lifecycle Protocol (IETF RFC 2119)

1. The server MUST validate inbound request body against strict closed JSON schema.
2. The server MUST reject undeclared properties (`additionalProperties: false`).
3. IF validation fails, the server MUST return HTTP 400 VALIDATION_FAILED with field-level details.

---

### 5. Deterministic Decision Table (DMN / Invariant Truth Table)

| Input Condition | Predicate Evaluation | Output Value | Secondary Effect |
| :--- | :--- | :--- | :--- |
| All required fields present, zero undeclared fields | `has_required && no_undeclared` | `VALID` | Proceed to domain execution |
| Missing required field | `!has_required` | `ERROR 400` | Reject with VALIDATION_FAILED field required |
| Undeclared additional property present | `has_undeclared` | `ERROR 400` | Reject with VALIDATION_FAILED undeclared property forbidden |

---

### 6. Declarative Logic Expression (CEL — Common Expression Language)

```cel
schema.required.all(f, has(request.body[f])) && request.body.keys().all(k, k in schema.properties)
  ? "VALID"
  : "ERROR_VALIDATION_FAILED"
```

---

### 7. Failure & Security Enforcement
- Closed schema enforcement prevents mass-assignment vulnerabilities.
- Validation errors must return 400 VALIDATION_FAILED with field details.

---

### 8. Protocol Wire Example

```http
{
  "customerEmail": "user@example.com",
  "totalAmount": { "amount": "99.50", "currency": "USD" }
}
```
