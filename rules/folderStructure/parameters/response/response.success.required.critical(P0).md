# Parameter Specification: `success`

| Attribute | Specification |
| :--- | :--- |
| **Identifier** | `success` |
| **Category** | `response` |
| **Surface** | Response JSON Envelope Root Field |
| **Requirement Level** | **MANDATORY** |
| **Criticality Tier** | **CRITICAL (P0)** |
| **Standard / Reference** | Strict Boolean (`true` | `false`) |
| **Schema Type** | `boolean` |

---

### 1. Architectural Purpose & Scope
Unambiguous binary indicator of operation outcome. MUST be true for all 2xx responses; MUST be false for all 4xx/5xx responses.

---

### 2. Open Standard Contract Schema (OpenAPI 3.1 & JSON Schema 2020-12)

```yaml
name: success
in: body
required: true
schema:
  type: boolean
  pattern: "^(true|false)$"
```

---

### 3. Wire Grammar (ABNF — RFC 5234)

```abnf
success = "true" / "false"
```

---

### 4. Normative Lifecycle Protocol (IETF RFC 2119)

1. IF HTTP status is in the 2xx class, the server MUST set `success: true`.
2. IF HTTP status is in the 4xx or 5xx class, the server MUST set `success: false`.
3. The server MUST NEVER invert or omit this boolean.

---

### 5. Deterministic Decision Table (DMN / Invariant Truth Table)

| Input Condition | Predicate Evaluation | Output Value | Secondary Effect |
| :--- | :--- | :--- | :--- |
| Status code 200..299 | `status_code >= 200 && status_code < 300` | `true` | Render success envelope |
| Status code 400..599 | `status_code >= 400` | `false` | Render error envelope |

---

### 6. Declarative Logic Expression (CEL — Common Expression Language)

```cel
status_code >= 200 && status_code < 300
```

---

### 7. Failure & Security Enforcement
- Never inverted; success: false must never accompany a 200 OK.
- Root signal consumed by all client SDKs before payload unpacking.

---

### 8. Protocol Wire Example

```http
"success": true
```
