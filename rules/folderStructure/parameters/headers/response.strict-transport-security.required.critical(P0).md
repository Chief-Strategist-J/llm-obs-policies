# Parameter Specification: `Strict-Transport-Security`

| Attribute | Specification |
| :--- | :--- |
| **Identifier** | `Strict-Transport-Security` |
| **Category** | `headers` |
| **Surface** | Outbound HTTP Transport Response Header |
| **Requirement Level** | **MANDATORY on All Responses** |
| **Criticality Tier** | **CRITICAL (P0)** |
| **Standard / Reference** | RFC 6797 HSTS Directive |
| **Schema Type** | `string` |

---

### 1. Architectural Purpose & Scope
Instructs user agents and clients to enforce encrypted TLS connections for all future interactions, preventing SSL-stripping and man-in-the-middle attacks.

---

### 2. Open Standard Contract Schema (OpenAPI 3.1 & JSON Schema 2020-12)

```yaml
name: Strict-Transport-Security
in: header
required: true
schema:
  type: string
  pattern: "^max-age=[0-9]+; includeSubDomains; preload$"
```

---

### 3. Wire Grammar (ABNF — RFC 5234)

```abnf
Strict-Transport-Security = directive *( OWS ";" OWS directive )
directive                 = "max-age=" 1*DIGIT / "includeSubDomains" / "preload"
```

---

### 4. Normative Lifecycle Protocol (IETF RFC 2119)

1. The server MUST include `Strict-Transport-Security` header with `max-age=63072000; includeSubDomains; preload` on all HTTPS responses.

---

### 5. Deterministic Decision Table (DMN / Invariant Truth Table)

| Input Condition | Predicate Evaluation | Output Value | Secondary Effect |
| :--- | :--- | :--- | :--- |
| All HTTPS responses | `is_https` | `max-age=63072000; includeSubDomains; preload` | Inject security header |

---

### 6. Declarative Logic Expression (CEL — Common Expression Language)

```cel
"max-age=63072000; includeSubDomains; preload"
```

---

### 7. Failure & Security Enforcement
- Must be present on all responses over HTTPS.
- Essential for banking, enterprise, and SOC2 compliance.

---

### 8. Protocol Wire Example

```http
Strict-Transport-Security: max-age=63072000; includeSubDomains; preload
```
