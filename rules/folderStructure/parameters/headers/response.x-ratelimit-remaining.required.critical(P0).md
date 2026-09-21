# Parameter Specification: `X-RateLimit-Remaining`

| Attribute | Specification |
| :--- | :--- |
| **Identifier** | `X-RateLimit-Remaining` |
| **Category** | `headers` |
| **Surface** | Outbound HTTP Transport Response Header |
| **Requirement Level** | **MANDATORY on All Responses** |
| **Criticality Tier** | **CRITICAL (P0)** |
| **Standard / Reference** | Non-negative Integer |
| **Schema Type** | `integer` |

---

### 1. Architectural Purpose & Scope
Communicates remaining request budget remaining in the current sliding window.

---

### 2. Open Standard Contract Schema (OpenAPI 3.1 & JSON Schema 2020-12)

```yaml
name: X-RateLimit-Remaining
in: header
required: true
schema:
  type: integer
  pattern: "^[0-9]+$"
```

---

### 3. Wire Grammar (ABNF — RFC 5234)

```abnf
X-RateLimit-Remaining = 1*DIGIT
```

---

### 4. Normative Lifecycle Protocol (IETF RFC 2119)

1. The server MUST return remaining budget integer clamped at zero.

---

### 5. Deterministic Decision Table (DMN / Invariant Truth Table)

| Input Condition | Predicate Evaluation | Output Value | Secondary Effect |
| :--- | :--- | :--- | :--- |
| Quota remaining >= 0 | `rate_quota.remaining >= 0` | `string(rate_quota.remaining)` | Inject header |
| Quota exhausted | `rate_quota.remaining < 0` | `0` | Inject 0 |

---

### 6. Declarative Logic Expression (CEL — Common Expression Language)

```cel
string(rate_quota.remaining >= 0 ? rate_quota.remaining : 0)
```

---

### 7. Failure & Security Enforcement
- Reaching 0 signals imminent 429 Too Many Requests rejection.
- Allows smart clients to proactively back off.

---

### 8. Protocol Wire Example

```http
X-RateLimit-Remaining: 994
```
