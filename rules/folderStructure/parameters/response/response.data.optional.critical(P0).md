# Parameter Specification: `data`

| Attribute | Specification |
| :--- | :--- |
| **Identifier** | `data` |
| **Category** | `response` |
| **Surface** | Response JSON Envelope Root Field |
| **Requirement Level** | **MANDATORY on Success; FORBIDDEN on Failure** |
| **Criticality Tier** | **CRITICAL (P0)** |
| **Standard / Reference** | Resource Payload Object or Array |
| **Schema Type** | `object | array` |

---

### 1. Architectural Purpose & Scope
Container for domain payload. On success, holds resource object or list of objects. On failure, MUST BE OMITTED ENTIRELY.

---

### 2. Open Standard Contract Schema (OpenAPI 3.1 & JSON Schema 2020-12)

```yaml
name: data
in: body
required: true
schema:
  type: object | array
  pattern: "N/A"
```

---

### 3. Wire Grammar (ABNF — RFC 5234)

```abnf
data = JSON-value
```

---

### 4. Normative Lifecycle Protocol (IETF RFC 2119)

1. IF response is successful, the server MUST include `data` field.
2. Collections MUST return empty array `[]` when no items match, never `null`.
3. IF response is an error, the server MUST NOT include `data` key.

---

### 5. Deterministic Decision Table (DMN / Invariant Truth Table)

| Input Condition | Predicate Evaluation | Output Value | Secondary Effect |
| :--- | :--- | :--- | :--- |
| Success response with payload | `is_success && payload != null` | `payload` | Render data container |
| Success response on empty collection | `is_success && is_collection && size == 0` | `[]` | Render empty array (never null) |
| Failure / error response | `!is_success` | `OMITTED` | Data key must not exist |

---

### 6. Declarative Logic Expression (CEL — Common Expression Language)

```cel
is_success ? (payload != null ? payload : {}) : null
```

---

### 7. Failure & Security Enforcement
- Collections must return empty array [] when no items exist, never null.
- Data key must not exist on failure responses.

---

### 8. Protocol Wire Example

```http
"data": { "orderId": "018f6e2c-9999", "status": "CONFIRMED" }
```
