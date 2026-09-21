# Parameter Specification: `x-request-id`

| Attribute | Specification |
| :--- | :--- |
| **Identifier** | `x-request-id` |
| **Category** | `headers` |
| **Surface** | Outbound HTTP Transport Response Header |
| **Requirement Level** | **MANDATORY** |
| **Criticality Tier** | **CRITICAL (P0)** |
| **Standard / Reference** | Execution Identifier |
| **Schema Type** | `string` |

---

### 1. Architectural Purpose & Scope
Echoes the resolved request identifier on all outbound HTTP responses. Exactly matches meta.requestId in the response envelope.

---

### 2. Open Standard Contract Schema (OpenAPI 3.1 & JSON Schema 2020-12)

```yaml
name: x-request-id
in: header
required: true
schema:
  type: string
  pattern: "^[a-zA-Z0-9_-]{16,64}$"
```

---

### 3. Wire Grammar (ABNF — RFC 5234)

```abnf
x-request-id = 16*64( ALPHA / DIGIT / "-" / "_" )
```

---

### 4. Normative Lifecycle Protocol (IETF RFC 2119)

1. The server MUST echo the resolved `request_id` in response header `x-request-id`.
2. The value MUST exactly match `meta.requestId`.

---

### 5. Deterministic Decision Table (DMN / Invariant Truth Table)

| Input Condition | Predicate Evaluation | Output Value | Secondary Effect |
| :--- | :--- | :--- | :--- |
| All HTTP responses | `true` | `resolved_request_id` | Inject header |

---

### 6. Declarative Logic Expression (CEL — Common Expression Language)

```cel
resolved_request_id
```

---

### 7. Failure & Security Enforcement
- Must be included in all success and failure responses.
- Crucial for client-side debugging and correlating support tickets.

---

### 8. Protocol Wire Example

```http
x-request-id: req-1700000000000-a1b2c3
```
