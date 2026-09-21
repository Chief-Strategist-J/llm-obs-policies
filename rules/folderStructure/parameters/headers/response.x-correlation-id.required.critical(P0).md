# Parameter Specification: `x-correlation-id`

| Attribute | Specification |
| :--- | :--- |
| **Identifier** | `x-correlation-id` |
| **Category** | `headers` |
| **Surface** | Outbound HTTP Transport Response Header |
| **Requirement Level** | **MANDATORY** |
| **Criticality Tier** | **CRITICAL (P0)** |
| **Standard / Reference** | Correlation Identifier |
| **Schema Type** | `string` |

---

### 1. Architectural Purpose & Scope
Echoes the business transaction correlation identifier. Exactly matches meta.correlationId in the response envelope.

---

### 2. Open Standard Contract Schema (OpenAPI 3.1 & JSON Schema 2020-12)

```yaml
name: x-correlation-id
in: header
required: true
schema:
  type: string
  pattern: "^[a-zA-Z0-9_-]{16,64}$"
```

---

### 3. Wire Grammar (ABNF — RFC 5234)

```abnf
x-correlation-id = 16*64( ALPHA / DIGIT / "-" / "_" )
```

---

### 4. Normative Lifecycle Protocol (IETF RFC 2119)

1. The server MUST echo the resolved `correlation_id` in response header `x-correlation-id`.
2. The value MUST exactly match `meta.correlationId`.

---

### 5. Deterministic Decision Table (DMN / Invariant Truth Table)

| Input Condition | Predicate Evaluation | Output Value | Secondary Effect |
| :--- | :--- | :--- | :--- |
| All HTTP responses | `true` | `resolved_correlation_id` | Inject header |

---

### 6. Declarative Logic Expression (CEL — Common Expression Language)

```cel
resolved_correlation_id
```

---

### 7. Failure & Security Enforcement
- Must be present on all responses.
- Enables tracking end-to-end multi-step flows across services.

---

### 8. Protocol Wire Example

```http
x-correlation-id: corr-1700000000000-x9y8z7
```
