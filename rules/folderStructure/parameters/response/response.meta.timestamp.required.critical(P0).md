# Parameter Specification: `meta.timestamp`

| Attribute | Specification |
| :--- | :--- |
| **Identifier** | `meta.timestamp` |
| **Category** | `response` |
| **Surface** | Response JSON Metadata Field |
| **Requirement Level** | **MANDATORY** |
| **Criticality Tier** | **CRITICAL (P0)** |
| **Standard / Reference** | RFC 3339 / ISO-8601 UTC with Millisecond Precision and literal 'Z' suffix |
| **Schema Type** | `string` |

---

### 1. Architectural Purpose & Scope
Authoritative server clock timestamp at the time of response completion. Used by clients to calculate local clock skew and measure network transit latency.

---

### 2. Open Standard Contract Schema (OpenAPI 3.1 & JSON Schema 2020-12)

```yaml
name: meta.timestamp
in: meta
required: true
schema:
  type: string
  pattern: "^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$"
```

---

### 3. Wire Grammar (ABNF — RFC 5234)

```abnf
meta-timestamp = 4DIGIT "-" 2DIGIT "-" 2DIGIT "T" 2DIGIT ":" 2DIGIT ":" 2DIGIT "." 3DIGIT "Z"
```

---

### 4. Normative Lifecycle Protocol (IETF RFC 2119)

1. The server MUST format `meta.timestamp` as ISO-8601 UTC with millisecond precision and literal `Z` suffix.

---

### 5. Deterministic Decision Table (DMN / Invariant Truth Table)

| Input Condition | Predicate Evaluation | Output Value | Secondary Effect |
| :--- | :--- | :--- | :--- |
| All responses | `true` | `ISO8601_UTC_NOW` | Inject into meta block |

---

### 6. Declarative Logic Expression (CEL — Common Expression Language)

```cel
iso8601_utc_timestamp
```

---

### 7. Failure & Security Enforcement
- Must use literal 'Z' suffix, never offset notation like '+00:00'.
- Must include millisecond precision (.123Z).

---

### 8. Protocol Wire Example

```http
"timestamp": "2026-08-23T13:12:00.012Z"
```
