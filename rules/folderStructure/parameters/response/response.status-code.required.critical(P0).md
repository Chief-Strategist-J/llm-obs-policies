# Parameter Specification: `statusCode`

| Attribute | Specification |
| :--- | :--- |
| **Identifier** | `statusCode` |
| **Category** | `response` |
| **Surface** | Response JSON Envelope Root Field |
| **Requirement Level** | **MANDATORY** |
| **Criticality Tier** | **CRITICAL (P0)** |
| **Standard / Reference** | HTTP Transport Status Code Integer |
| **Schema Type** | `integer` |

---

### 1. Architectural Purpose & Scope
Mirror of the actual HTTP transport response status code. Guarantees that clients operating behind proxies that mangle HTTP status codes can reliably inspect status.

---

### 2. Open Standard Contract Schema (OpenAPI 3.1 & JSON Schema 2020-12)

```yaml
name: statusCode
in: body
required: true
schema:
  type: integer
  pattern: "^[2-5][0-9]{2}$"
```

---

### 3. Wire Grammar (ABNF — RFC 5234)

```abnf
statusCode = 3DIGIT
```

---

### 4. Normative Lifecycle Protocol (IETF RFC 2119)

1. The server MUST set `statusCode` integer in the envelope root to exactly mirror the HTTP response status code line.

---

### 5. Deterministic Decision Table (DMN / Invariant Truth Table)

| Input Condition | Predicate Evaluation | Output Value | Secondary Effect |
| :--- | :--- | :--- | :--- |
| All responses | `true` | `http_status_code` | Exact mirror of transport status |

---

### 6. Declarative Logic Expression (CEL — Common Expression Language)

```cel
http_status_code
```

---

### 7. Failure & Security Enforcement
- Must exactly match HTTP transport status code.
- Discrepancies between transport status and body statusCode are strict violations.

---

### 8. Protocol Wire Example

```http
"statusCode": 200
```
