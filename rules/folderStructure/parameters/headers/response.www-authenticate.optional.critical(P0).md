# Parameter Specification: `WWW-Authenticate`

| Attribute | Specification |
| :--- | :--- |
| **Identifier** | `WWW-Authenticate` |
| **Category** | `headers` |
| **Surface** | Outbound HTTP Transport Response Header |
| **Requirement Level** | **MANDATORY on 401 Unauthenticated** |
| **Criticality Tier** | **CRITICAL (P0)** |
| **Standard / Reference** | RFC 6750 OAuth 2.0 Challenge Specification |
| **Schema Type** | `string` |

---

### 1. Architectural Purpose & Scope
Returns authentication challenge details to the client when access is denied due to missing, expired, or invalid credentials.

---

### 2. Open Standard Contract Schema (OpenAPI 3.1 & JSON Schema 2020-12)

```yaml
name: WWW-Authenticate
in: header
required: true
schema:
  type: string
  pattern: "^Bearer\s+error="[a-zA-Z0-9_]+"(,\s*error_description=".*")?$"
```

---

### 3. Wire Grammar (ABNF — RFC 5234)

```abnf
WWW-Authenticate = "Bearer" [ RWS 1#auth-param ]
auth-param       = token68 / ( token "=" ( token / quoted-string ) )
```

---

### 4. Normative Lifecycle Protocol (IETF RFC 2119)

1. On any HTTP 401 response, the server MUST include `WWW-Authenticate` header declaring the Bearer challenge and error reason.

---

### 5. Deterministic Decision Table (DMN / Invariant Truth Table)

| Input Condition | Predicate Evaluation | Output Value | Secondary Effect |
| :--- | :--- | :--- | :--- |
| Status is 401 | `status_code == 401` | `Bearer error="error_code", error_description="error_desc"` | Inject header |
| Status is not 401 | `status_code != 401` | `null` | Omit header |

---

### 6. Declarative Logic Expression (CEL — Common Expression Language)

```cel
status_code == 401 ? 'Bearer error="' + error_code + '", error_description="' + error_description + '"' : null
```

---

### 7. Failure & Security Enforcement
- Must be present on every HTTP 401 response.
- Directs client whether to re-authenticate or refresh expired token.

---

### 8. Protocol Wire Example

```http
WWW-Authenticate: Bearer error="invalid_token", error_description="The access token expired or is invalid."
```
