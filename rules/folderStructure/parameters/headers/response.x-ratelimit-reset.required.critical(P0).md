# Parameter Specification: `X-RateLimit-Reset`

| Attribute | Specification |
| :--- | :--- |
| **Identifier** | `X-RateLimit-Reset` |
| **Category** | `headers` |
| **Surface** | Outbound HTTP Transport Response Header |
| **Requirement Level** | **MANDATORY on All Responses** |
| **Criticality Tier** | **CRITICAL (P0)** |
| **Standard / Reference** | Unix Epoch Seconds Integer |
| **Schema Type** | `integer` |

---

### 1. Architectural Purpose & Scope
Unix epoch timestamp in seconds at which the current rate limit quota window resets and full budget is restored.

---

### 2. Open Standard Contract Schema (OpenAPI 3.1 & JSON Schema 2020-12)

```yaml
name: X-RateLimit-Reset
in: header
required: true
schema:
  type: integer
  minimum: 0
```

---

### 3. Wire Grammar (ABNF — RFC 5234)

```abnf
X-RateLimit-Reset = 10*DIGIT
```

---

### 4. Normative Lifecycle Protocol (IETF RFC 2119)

1. The server MUST declare the exact epoch timestamp in seconds when the quota window refreshes.

---

### 5. Deterministic Decision Table (DMN / Invariant Truth Table)

| Input Condition | Predicate Evaluation | Output Value | Secondary Effect |
| :--- | :--- | :--- | :--- |
| All HTTP responses | `true` | `string(rate_quota.reset_epoch_seconds)` | Inject header |

---

### 6. Declarative Logic Expression (CEL — Common Expression Language)

```cel
string(rate_quota.reset_epoch_seconds)
```

---

### 7. Failure & Security Enforcement
- Provides exact timestamp when quota refreshes.
- Paired with Retry-After on 429 errors.

---

### 8. Protocol Wire Example

```http
X-RateLimit-Reset: 1700000060
```
