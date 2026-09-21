# Parameter Specification: `meta.executionTimeMs`

| Attribute | Specification |
| :--- | :--- |
| **Identifier** | `meta.executionTimeMs` |
| **Category** | `response` |
| **Surface** | Response JSON Metadata Field |
| **Requirement Level** | **MANDATORY** |
| **Criticality Tier** | **CRITICAL (P0)** |
| **Standard / Reference** | Positive Integer |
| **Schema Type** | `integer` |

---

### 1. Architectural Purpose & Scope
Server-side execution time in milliseconds, measured from request receipt at gateway to response serialization. Excludes network transit latency.

---

### 2. Open Standard Contract Schema (OpenAPI 3.1 & JSON Schema 2020-12)

```yaml
name: meta.executionTimeMs
in: meta
required: true
schema:
  type: integer
  pattern: "^[0-9]+$"
```

---

### 3. Wire Grammar (ABNF — RFC 5234)

```abnf
executionTimeMs = 1*DIGIT
```

---

### 4. Normative Lifecycle Protocol (IETF RFC 2119)

1. The server MUST compute elapsed processing duration in milliseconds and inject into `meta.executionTimeMs`.

---

### 5. Deterministic Decision Table (DMN / Invariant Truth Table)

| Input Condition | Predicate Evaluation | Output Value | Secondary Effect |
| :--- | :--- | :--- | :--- |
| All responses | `true` | `max(0, completion_time - start_time)` | Inject duration |

---

### 6. Declarative Logic Expression (CEL — Common Expression Language)

```cel
max(0, completion_epoch_ms - start_epoch_ms)
```

---

### 7. Failure & Security Enforcement
- Enables clients to distinguish server latency from network transit delay.
- Crucial metric for SLA monitoring and performance regression detection.

---

### 8. Protocol Wire Example

```http
"executionTimeMs": 14
```
