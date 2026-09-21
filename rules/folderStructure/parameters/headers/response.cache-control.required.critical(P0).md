# Parameter Specification: `Cache-Control`

| Attribute | Specification |
| :--- | :--- |
| **Identifier** | `Cache-Control` |
| **Category** | `headers` |
| **Surface** | Outbound HTTP Transport Response Header |
| **Requirement Level** | **MANDATORY on All Responses** |
| **Criticality Tier** | **CRITICAL (P0)** |
| **Standard / Reference** | RFC 9111 HTTP Caching Directives |
| **Schema Type** | `string` |

---

### 1. Architectural Purpose & Scope
Directs intermediate proxies, CDNs, and client browsers regarding response cacheability. Mutation, sensitive, and PII endpoints must enforce 'no-store'.

---

### 2. Open Standard Contract Schema (OpenAPI 3.1 & JSON Schema 2020-12)

```yaml
name: Cache-Control
in: header
required: true
schema:
  type: string
  pattern: "^(no-store|private|public)(,\s*[a-zA-Z0-9_=-]+)*$"
```

---

### 3. Wire Grammar (ABNF — RFC 5234)

```abnf
Cache-Control = 1#cache-directive
cache-directive = token [ "=" ( token / quoted-string ) ]
```

---

### 4. Normative Lifecycle Protocol (IETF RFC 2119)

1. The server MUST enforce `no-store` on any response containing authenticated, mutating, sensitive, or PII data.
2. Public cacheable read endpoints SHALL declare explicit `max-age` and revalidation directives.

---

### 5. Deterministic Decision Table (DMN / Invariant Truth Table)

| Input Condition | Predicate Evaluation | Output Value | Secondary Effect |
| :--- | :--- | :--- | :--- |
| Mutating method or sensitive/authenticated payload | `is_mutation || is_sensitive` | `no-store` | Prevent caching across proxies |
| Public read-only response with cache policy | `!is_mutation && cache_policy.max_age > 0` | `public, max-age={seconds}, must-revalidate` | Enable CDN caching |

---

### 6. Declarative Logic Expression (CEL — Common Expression Language)

```cel
is_mutation || is_sensitive || cache_max_age == 0 ? "no-store" : "public, max-age=" + string(cache_max_age) + ", must-revalidate"
```

---

### 7. Failure & Security Enforcement
- Responses containing user credentials, tokens, or PII must strictly return no-store.
- Prevents stale or contaminated caches.

---

### 8. Protocol Wire Example

```http
Cache-Control: no-store
```
