# Parameter Specification: `x-api-version`

| Attribute | Specification |
| :--- | :--- |
| **Identifier** | `x-api-version` |
| **Category** | `headers` |
| **Surface** | Outbound HTTP Transport Response Header |
| **Requirement Level** | **MANDATORY** |
| **Criticality Tier** | **CRITICAL (P0)** |
| **Standard / Reference** | CalVer or Version Tag |
| **Schema Type** | `string` |

---

### 1. Architectural Purpose & Scope
Declares the active contract version used by the server to construct the response payload.

---

### 2. Open Standard Contract Schema (OpenAPI 3.1 & JSON Schema 2020-12)

```yaml
name: x-api-version
in: header
required: true
schema:
  type: string
  pattern: "^(\d{4}-\d{2}-\d{2}|v\d+)$"
```

---

### 3. Wire Grammar (ABNF — RFC 5234)

```abnf
x-api-version = 4DIGIT "-" 2DIGIT "-" 2DIGIT / "v" 1*DIGIT
```

---

### 4. Normative Lifecycle Protocol (IETF RFC 2119)

1. The server MUST echo the resolved contract version in response header `x-api-version`.
2. The value MUST exactly match `meta.apiVersion`.

---

### 5. Deterministic Decision Table (DMN / Invariant Truth Table)

| Input Condition | Predicate Evaluation | Output Value | Secondary Effect |
| :--- | :--- | :--- | :--- |
| All HTTP responses | `true` | `resolved_version` | Inject header |

---

### 6. Declarative Logic Expression (CEL — Common Expression Language)

```cel
resolved_version
```

---

### 7. Failure & Security Enforcement
- Must match meta.apiVersion exactly.
- Clients verify this header to detect silent version shifts.

---

### 8. Protocol Wire Example

```http
x-api-version: 2024-11-01
```
