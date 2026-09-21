# Parameter Specification: `meta.apiVersion`

| Attribute | Specification |
| :--- | :--- |
| **Identifier** | `meta.apiVersion` |
| **Category** | `response` |
| **Surface** | Response JSON Metadata Field |
| **Requirement Level** | **MANDATORY** |
| **Criticality Tier** | **CRITICAL (P0)** |
| **Standard / Reference** | CalVer or Major Version String |
| **Schema Type** | `string` |

---

### 1. Architectural Purpose & Scope
Declares the active API contract version that produced this response. Identical to response header x-api-version.

---

### 2. Open Standard Contract Schema (OpenAPI 3.1 & JSON Schema 2020-12)

```yaml
name: meta.apiVersion
in: meta
required: true
schema:
  type: string
  pattern: "^(\d{4}-\d{2}-\d{2}|v\d+)$"
```

---

### 3. Wire Grammar (ABNF — RFC 5234)

```abnf
meta-apiVersion = 4DIGIT "-" 2DIGIT "-" 2DIGIT / "v" 1*DIGIT
```

---

### 4. Normative Lifecycle Protocol (IETF RFC 2119)

1. The server MUST inject resolved contract version into `meta.apiVersion`.

---

### 5. Deterministic Decision Table (DMN / Invariant Truth Table)

| Input Condition | Predicate Evaluation | Output Value | Secondary Effect |
| :--- | :--- | :--- | :--- |
| All responses | `true` | `resolved_api_version` | Inject into meta |

---

### 6. Declarative Logic Expression (CEL — Common Expression Language)

```cel
resolved_api_version
```

---

### 7. Failure & Security Enforcement
- Ensures contract version is accessible even if transport headers are stripped by intermediaries.
- Must match header x-api-version.

---

### 8. Protocol Wire Example

```http
"apiVersion": "2024-11-01"
```
