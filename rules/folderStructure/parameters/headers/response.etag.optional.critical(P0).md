# Parameter Specification: `ETag`

| Attribute | Specification |
| :--- | :--- |
| **Identifier** | `ETag` |
| **Category** | `headers` |
| **Surface** | Outbound HTTP Transport Response Header |
| **Requirement Level** | **MANDATORY on Mutating & Read Responses for Versioned Entities** |
| **Criticality Tier** | **CRITICAL (P0)** |
| **Standard / Reference** | RFC 9110 Strong Entity Tag |
| **Schema Type** | `string` |

---

### 1. Architectural Purpose & Scope
Entity tag representing the specific version of the resource representation. Used by clients in subsequent If-Match headers for optimistic concurrency control.

---

### 2. Open Standard Contract Schema (OpenAPI 3.1 & JSON Schema 2020-12)

```yaml
name: ETag
in: header
required: true
schema:
  type: string
  pattern: "^"[a-zA-Z0-9_-]+"$"
```

---

### 3. Wire Grammar (ABNF — RFC 5234)

```abnf
ETag = entity-tag
entity-tag = DQUOTE 1*( VCHAR ) DQUOTE
```

---

### 4. Normative Lifecycle Protocol (IETF RFC 2119)

1. On versioned entity operations, the server MUST calculate and return the current strong entity tag.
2. The server MUST format the value enclosed in double quotes.

---

### 5. Deterministic Decision Table (DMN / Invariant Truth Table)

| Input Condition | Predicate Evaluation | Output Value | Secondary Effect |
| :--- | :--- | :--- | :--- |
| Versioned resource response | `resource.is_versioned && resource.etag != null` | `"resource.etag"` | Inject ETag header |
| Non-versioned resource | `!resource.is_versioned` | `null` | Omit header |

---

### 6. Declarative Logic Expression (CEL — Common Expression Language)

```cel
resource.etag != null ? '"' + resource.etag + '"' : null
```

---

### 7. Failure & Security Enforcement
- Must be returned on successful POST, PUT, PATCH, and GET for versioned entities.
- Must be updated atomically upon every state change.

---

### 8. Protocol Wire Example

```http
ETag: "018f6e2c-9999-7d4e-b3f2-1a2b3c4d5e6f"
```
