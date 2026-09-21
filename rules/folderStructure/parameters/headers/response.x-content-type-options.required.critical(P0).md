# Parameter Specification: `X-Content-Type-Options`

| Attribute | Specification |
| :--- | :--- |
| **Identifier** | `X-Content-Type-Options` |
| **Category** | `headers` |
| **Surface** | Outbound HTTP Transport Response Header |
| **Requirement Level** | **MANDATORY on All Responses** |
| **Criticality Tier** | **CRITICAL (P0)** |
| **Standard / Reference** | W3C Fetch Standard nosniff Directive |
| **Schema Type** | `string` |

---

### 1. Architectural Purpose & Scope
Prevents browsers and HTTP clients from MIME-sniffing a response away from the declared Content-Type, mitigating script execution and drive-by download vulnerabilities.

---

### 2. Open Standard Contract Schema (OpenAPI 3.1 & JSON Schema 2020-12)

```yaml
name: X-Content-Type-Options
in: header
required: true
schema:
  type: string
  pattern: "^nosniff$"
```

---

### 3. Wire Grammar (ABNF — RFC 5234)

```abnf
X-Content-Type-Options = "nosniff"
```

---

### 4. Normative Lifecycle Protocol (IETF RFC 2119)

1. The server MUST include `X-Content-Type-Options: nosniff` on every HTTP response.

---

### 5. Deterministic Decision Table (DMN / Invariant Truth Table)

| Input Condition | Predicate Evaluation | Output Value | Secondary Effect |
| :--- | :--- | :--- | :--- |
| All responses | `true` | `nosniff` | Inject security header |

---

### 6. Declarative Logic Expression (CEL — Common Expression Language)

```cel
"nosniff"
```

---

### 7. Failure & Security Enforcement
- Must be present on every HTTP response.
- Protects JSON endpoints against polyglot and MIME-confusion exploits.

---

### 8. Protocol Wire Example

```http
X-Content-Type-Options: nosniff
```
