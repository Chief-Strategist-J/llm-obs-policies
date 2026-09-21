# Parameter Specification: `X-RateLimit-Limit`

| Attribute | Specification |
| :--- | :--- |
| **Identifier** | `X-RateLimit-Limit` |
| **Category** | `headers` |
| **Surface** | Outbound HTTP Transport Response Header |
| **Requirement Level** | **MANDATORY on All Responses** |
| **Criticality Tier** | **CRITICAL (P0)** |
| **Standard / Reference** | Positive Integer |
| **Schema Type** | `integer` |

---

### 1. Architectural Purpose & Scope
Communicates the maximum request budget allocated to the tenant or client IP in the current rate limit quota window.

---

### 2. Open Standard Contract Schema (OpenAPI 3.1 & JSON Schema 2020-12)

```yaml
name: X-RateLimit-Limit
in: header
required: true
schema:
  type: integer
  pattern: "^[0-9]+$"
```

---

### 3. Wire Grammar (ABNF — RFC 5234)

```abnf
X-RateLimit-Limit = 1*DIGIT
```

---

### 4. Normative Lifecycle Protocol (IETF RFC 2119)

1. The server MUST return the quota allocation ceiling in `X-RateLimit-Limit` header on every response.

---

### 5. Deterministic Decision Table (DMN / Invariant Truth Table)

| Input Condition | Predicate Evaluation | Output Value | Secondary Effect |
| :--- | :--- | :--- | :--- |
| All HTTP responses | `true` | `string(rate_quota.limit)` | Inject header |

---

### 6. Declarative Logic Expression (CEL — Common Expression Language)

```cel
string(rate_quota.limit)
```

---

### 7. Failure & Security Enforcement
- Informs callers of their burst and sustained throughput caps.
- Standard across API gateways.

---

### 8. Protocol Wire Example

```http
X-RateLimit-Limit: 1000
```
