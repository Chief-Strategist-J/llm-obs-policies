# Policies & AI Policy Orchestrator TODO

For the full architectural blueprint, API roadmap, and component tracker, see the submodule document:
👉 [policy-orchestrator/TODO.md](file:///home/btpl-lap-22/live/llm-obs-infra/policies/policy-orchestrator/TODO.md)

### Quick Roadmap Highlights:
- [x] **Hexagonal Architecture Core**: Abstract Ports (`LLMProviderPort`, `VectorStorePort`, `GraphStorePort`, `KnowledgeSourcePort`) and Adapters (`OpenAICompatibleAdapter`, `MockLLMAdapter`, `InMemoryCosineVectorAdapter`, `QdrantVectorAdapter`, `InMemoryGraphAdapter`, `Neo4jGraphAdapter`, `PolicyRulesMarkdownLoader`).
- [x] **Hybrid RAG Service**: BM25 inverted index + dense vector cosine similarity + Reciprocal Rank Fusion (RRF) grounded directly in `policies/rules/`.
- [x] **AI Policy Agent**: Autonomous ReAct reasoning loop with tool execution (`search_policy_rules`, `run_repo_audit`, `generate_refactoring_plan`).
- [x] **Knowledge Graph Service**: Policy contract entity and relationship extraction (`(:Rule)-[:BELONGS_TO]->(:Category)`, `(:Rule)-[:ENFORCES]->(:ArchitecturePattern)`).
- [x] **REST API & CLI**: Standardized response envelope `{meta, data, errors}`, W3C traceparent context, OpenAPI v3 spec.
- [x] **Docker Compose Stack**: Multi-stage `policy-orchestrator` + `qdrant` vector database + `neo4j` graph database.
- [ ] **Streaming Telemetry**: SSE endpoint for token & reasoning streaming.
- [ ] **AST-Safe Automated Code Refactoring**: Integration with LibCST and Tree-sitter.
- [ ] **Live Web Policy Verification**: Real-time CVE/RFC checking via search provider.
