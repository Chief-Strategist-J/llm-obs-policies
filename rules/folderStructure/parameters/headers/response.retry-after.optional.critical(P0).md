# Parameter Specification: `Retry-After`

| Attribute | Specification |
| :--- | :--- |
| **Identifier** | `Retry-After` |
| **Category** | `headers` |
| **Surface** | Outbound HTTP Transport Response Header |
| **Requirement Level** | **MANDATORY on 429 Too Many Requests and 503 Service Unavailable** |
| **Criticality Tier** | **CRITICAL (P0)** |
| **Standard / Reference** | RFC 9110 Seconds Integer or HTTP-Date |
| **Schema Type** | `integer` |

---

### 1. Architectural Purpose & Scope
Instructs client exactly how many seconds it must wait before retrying the failed request. Crucial for circuit breaking and overload shedding.

---

### 2. Open Standard Contract Schema (OpenAPI 3.1 & JSON Schema 2020-12)

```yaml
name: Retry-After
in: header
required: true
schema:
  type: integer
  pattern: "^[0-9]+$"
```

---

### 3. Wire Grammar (ABNF — RFC 5234)

```abnf
Retry-After = 1*DIGIT / HTTP-date
```

---

### 4. Normative Lifecycle Protocol (IETF RFC 2119)

1. IF HTTP status is 429 or 503, the server MUST include `Retry-After` header declaring backoff delay in seconds.
2. Client retry engines MUST NOT retry prior to the elapsed duration.

---

### 5. Deterministic Decision Table (DMN / Invariant Truth Table)

| Input Condition | Predicate Evaluation | Output Value | Secondary Effect |
| :--- | :--- | :--- | :--- |
| Status is 429 or 503 with retry delay | `status_code in [429, 503] && retry_delay != null` | `string(retry_delay)` | Inject header |
| Other status codes | `!(status_code in [429, 503])` | `null` | Omit header |

---

### 6. Declarative Logic Expression (CEL — Common Expression Language)

```cel
status_code in [429, 503] && retry_delay != null ? string(retry_delay) : null
```

---

### 7. Failure & Security Enforcement
- Must be respected by all SDK retry engines and backoff handlers.
- Prevents thundering-herd retry storms against overloaded backends.

---

### 8. Protocol Wire Example

```http
Retry-After: 30
```
