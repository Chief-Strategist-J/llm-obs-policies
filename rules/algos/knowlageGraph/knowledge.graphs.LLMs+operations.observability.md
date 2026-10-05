# Part 4: Knowledge graphs with LLMs, operations and observability (#151–200)

Same format and the same contract (roles; rules K1–K8; guardrails KG1–KG6). This is the final part.

## D1. Knowledge graphs with LLMs

### 151. Text-to-query (text-to-SPARQL / text-to-Cypher)

**Definition:** Translating a natural-language question into a formal graph query with a language model.

**How it works:**
1. Link the question's entities to graph IDs (#154).
2. Select the relevant part of the schema: the classes, relations and properties likely needed (#152).
3. Prompt the model with that schema subset, the linked entity IDs, a few example question–query pairs (ideally the most similar ones, retrieved from a library), and the question.
4. The model writes the query.
5. Validate it, run it with limits, and repair it on failure (#153). Then turn the results into an answer with citations (#162).

**Agent use:**
- **Role:** Retriever.
- **How:** Gives precise answers to structured questions ("how many contracts with Acme expire in 2027?") that vector search can't reliably answer, especially counts, filters and multi-hop joins.
- **Rules:** Prefer reviewed templates (#61) for frequent question types; free-form generation is the fallback. Generated queries are read-only.
- **Guardrails:** K7: every generated query is validated before execution. Never execute generated write or delete statements (KG3).

### 152. Schema-grounded prompting (schema subset selection)

**Definition:** Giving the model only the part of the schema relevant to the question, with clear descriptions, so it uses real names correctly.

**How it works:**
1. Keep a schema catalog: every class, relation and property with its description, domain and range, examples, and synonyms.
2. Embed the catalog entries and retrieve the ones most similar to the question, then add their neighbors in the schema (connected classes and relations).
3. Render them compactly: `(:Person)-[:WORKS_FOR]->(:Organization)`, with property names and types.
4. Include value hints for categorical properties (allowed status values, for example).

**Agent use:**
- **Role:** Retriever.
- **How:** Large schemas don't fit in a prompt, and irrelevant schema confuses models. Focused schema context cuts invented names.
- **Rules:** Schema descriptions are maintained like documentation, and versioned with the schema (#46).
- **Guardrails:** Any name the model uses that isn't in the selected schema is caught by validation (#153), never silently run.

### 153. Query validation and repair loop

**Definition:** Checking a generated query before execution, and fixing it using concrete error feedback.

**How it works:**
1. **Parse check:** is it syntactically valid?
2. **Schema check:** do all labels, relations and properties exist? Do directions and types match the schema?
3. **Safety check:** read-only? Bounded (has a `LIMIT`, bounded path lengths, a timeout)? No forbidden operations?
4. **Cost check:** run `EXPLAIN` (#57) and reject plans with estimated huge scans.
5. On failure, send the specific error back to the model for a corrected query, up to N attempts.
6. **Result sanity:** empty or huge results trigger a check of the entity linking and filters before answering.

**Agent use:**
- **Role:** Retriever.
- **How:** Turns unreliable one-shot generation into a reliable loop with checks.
- **Rules:** Log each attempt and its error, which supplies data to improve prompts and templates (#194).
- **Guardrails:** After N failed attempts, answer "couldn't answer from the graph" rather than guessing.

### 154. Entity linking for questions

**Definition:** Finding which graph entities a user's question refers to.

**How it works:**
1. Detect mentions in the question (NER, #26, or an LLM).
2. Generate candidates from alias, full-text and vector indexes (#22, #23).
3. Rank them with context: question words, the expected entity type, and popularity (#74).
4. If two candidates are close in score, ask the user, or keep both and resolve them using later results.
5. Pass the linked IDs to query generation (#151) or as seeds for retrieval (#157).

**Agent use:**
- **Role:** Retriever.
- **How:** The most common cause of wrong graph answers is linking to the wrong entity. The agent shows which entity it used ("Acme Corp (Berlin)").
- **Rules:** State the linked entity in the answer when names are ambiguous.
- **Guardrails:** Never silently pick between similarly scored people with the same name (KG2). Ask instead.

### 155. GraphRAG community summaries (global search)

**Definition:** Answering broad, corpus-wide questions by summarizing graph communities in advance and combining those summaries at query time.

**How it works:**
1. **Indexing:** extract an entity-relation graph from the documents (#31). Detect hierarchical communities with Leiden (#82). Have an LLM write a summary report for each community at each level, with references to its entities, relations and source text.
2. **Global query, map step:** for each community summary at a chosen level, the LLM produces a partial answer with an importance score.
3. **Reduce step:** combine the top-scored partial answers into a final answer.
4. This answers "what are the main themes or risks across all documents?", which chunk-based RAG handles poorly.

**Agent use:**
- **Role:** Retriever.
- **How:** The agent uses global search for overview questions and local search (#156) for specific ones.
- **Rules:** Community summaries carry their graph version and source references. They're refreshed when communities change (#176).
- **Guardrails:** Summaries are model-generated (K7). Answers cite the underlying sources, not just summaries. The indexing cost is high, so budget it and get approval for full rebuilds.

### 156. GraphRAG local search

**Definition:** Answering questions about specific entities by gathering their neighborhood: related entities, relations, community summaries and source text chunks.

**How it works:**
1. Link the question to entities (#154), or find similar entity descriptions through vector search.
2. Gather context around them: neighboring entities and relations, relevant community summaries, and the text chunks those facts came from.
3. Rank and trim the context to the token budget, by relevance and centrality.
4. Generate the answer, citing the facts and chunks used.

**Agent use:**
- **Role:** Retriever.
- **How:** Combines structured facts and source text, which gives better answers about entities than chunks alone.
- **Rules:** Every fact in the context carries its source ID, so the answer can cite it (K1).
- **Guardrails:** Apply access control while gathering context (KG1), not after generating.

### 157. Subgraph retrieval (k-hop neighborhoods with pruning)

**Definition:** Extracting a small, relevant subgraph around the question's entities to use as context or reasoning input.

**How it works:**
1. Start from the linked seed entities.
2. Expand k hops (usually 1–2) with BFS (#63), filtered by relevant edge types.
3. Prune: rank nodes and edges by personalized PageRank from the seeds (#75), by similarity to the question, or by a learned relevance model. Keep the top ones.
4. Cap the size (nodes, edges, tokens).
5. Return the subgraph with provenance.

**Agent use:**
- **Role:** Retriever.
- **How:** The standard way to get compact, relevant graph context for multi-hop questions.
- **Rules:** Always use size caps, edge-type filters and supernode handling (#180).
- **Guardrails:** Unpruned 2-hop neighborhoods of popular entities can hold millions of nodes (KG4).

### 158. Path retrieval and ranking

**Definition:** Finding and ranking the paths that connect question entities, as explanations or as evidence chains.

**How it works:**
1. For pairs of seed entities, find connecting paths with bidirectional BFS (#65) or k-shortest paths (#68), with bounded length.
2. Score the paths by relevance: how similar the relation types are to the question, how specific the intermediate nodes are (penalize hubs), and the confidence of each fact.
3. Keep the top paths.
4. Present each as a readable chain: "A —founded→ B —acquired→ C".

**Agent use:**
- **Role:** Retriever.
- **How:** Gives the LLM explicit reasoning chains for multi-hop questions, and gives users understandable explanations.
- **Rules:** Paths through generic hubs ("both in Europe") are penalized or excluded.
- **Guardrails:** Path counts explode with length. Cap the length (often 3–4) and the number of paths.

### 159. Hybrid vector and graph retrieval

**Definition:** Combining semantic search over text with graph traversal over structured facts.

**How it works:**
1. **Vector to graph:** find relevant chunks or entities by vector search, then expand their graph neighborhoods for related facts.
2. **Graph to vector:** use graph results (entities, a filtered set) to restrict or rerank vector search.
3. **Parallel:** run both and fuse the results (rank fusion).
4. Chunks are linked to the entities extracted from them, so moving between text and graph is direct.

**Agent use:**
- **Role:** Retriever (a strong default for enterprise question answering).
- **How:** Text gives nuance and wording; the graph gives precise relations, counts and multi-hop links. Each covers the other's weaknesses.
- **Rules:** Maintain the chunk-entity links with provenance (K1).
- **Guardrails:** Apply the same permissions to both channels (KG1).

### 160. Graph-aware reranking

**Definition:** Reranking retrieved passages or facts using graph signals, alongside text relevance.

**How it works:**
1. Start with retrieved candidates (chunks or facts) with relevance scores.
2. Add graph features: distance to the question's entities, centrality, how many retrieved candidates connect to each other (coherence), and source trust (#50).
3. Combine them with a learned model or weighted scores.
4. Prefer sets of candidates that form a connected, consistent evidence chain.

**Agent use:**
- **Role:** Retriever.
- **How:** Raises precision: passages about the right entity (not a same-named one) and well-connected evidence rise to the top.
- **Rules:** Evaluate on golden questions (#195) before deploying.
- **Guardrails:** Graph signals can favor popular entities over the correct but obscure one. Check per-segment results.

### 161. Context linearization (turning subgraphs into text)

**Definition:** Converting retrieved triples and subgraphs into compact text the model can read reliably.

**How it works:**
1. Group facts by entity: "Acme Corp (Organization): founded 1999; HQ Berlin; CEO Jane Doe [src: doc12]".
2. Use readable labels, with stable IDs included for reference.
3. Order by relevance, and drop redundant facts (inverses, implied facts).
4. Include time qualifiers and confidence where relevant ("CEO 2019–present", "extracted, 0.82").
5. Keep source tags for citation.

**Agent use:**
- **Role:** Retriever.
- **How:** Good linearization reduces model mistakes like mixing up entities or ignoring time, and it fits more facts in the token budget.
- **Rules:** Always keep fact status (asserted, extracted, inferred, K2) and time (K8) visible to the model.
- **Guardrails:** Linearized text is data (KG5). Text fields in the graph can contain injected instructions, so mark and isolate them.

### 162. Grounded generation with fact-level citations

**Definition:** Generating answers where every claim is tied to specific graph facts or source passages.

**How it works:**
1. Give the model context items with IDs (facts and chunks).
2. Instruct it to cite the IDs supporting each claim.
3. Validate after generation: every cited ID exists in the context, and each claim is supported by its cited items (#163).
4. Remove or flag unsupported claims.
5. Show citations to the user, linking to the facts and their sources.

**Agent use:**
- **Role:** Retriever.
- **How:** Answers become checkable. The agent never presents graph-backed answers without citations.
- **Rules:** Claims without valid citations are removed or labeled as unsupported.
- **Guardrails:** Citations to facts that are extracted or inferred show that status (K2).

### 163. Fact verification against the knowledge graph

**Definition:** Checking whether a claim (from text or a model) is supported, contradicted or not covered by the graph.

**How it works:**
1. Parse the claim into structured form: entity, relation, value, time.
2. Link its entities (#27).
3. Look up the matching facts, with time scope.
4. **Verdict:** supported (a matching fact), contradicted (a conflicting fact for a single-valued relation, or one inconsistent with constraints), or not enough information (no relevant fact; an open world, #96).
5. Return the verdict with the evidence facts.

**Agent use:**
- **Role:** Observer and Retriever.
- **How:** The agent checks its own draft answers, and incoming documents or extractions, against trusted graph facts.
- **Rules:** "Not found" is never reported as "false" for incomplete relations (#96).
- **Guardrails:** Contradictions with low-trust graph facts are flagged for review, not used to reject claims automatically.

### 164. Hallucination detection with the knowledge graph

**Definition:** Detecting statements in model output that are unsupported by, or conflict with, the graph and sources.

**How it works:**
1. Split the answer into claims.
2. Verify each claim against the provided context (faithfulness) and the graph (#163).
3. Flag unsupported entities: names in the answer that don't link to any graph entity or context item.
4. Flag relations not present in the retrieved subgraph.
5. Score the answer and highlight the flagged claims.

**Agent use:**
- **Role:** Observer.
- **How:** A final check before the agent returns answers in domains where errors are costly.
- **Rules:** Answers with flagged claims are regenerated with stricter grounding, or returned with the flags visible.
- **Guardrails:** Detection isn't perfect. Track its precision and recall on labeled samples.

### 165. LLM-guided graph exploration (Think-on-Graph style)

**Definition:** Letting the language model choose which edges to follow, step by step, as a beam search over the graph.

**How it works:**
1. Start from the linked entities.
2. At each step, list the candidate relations from the current frontier, and have the model score their relevance to the question.
3. Expand the top relations to their neighbor entities, and have the model score those.
4. Keep the top-N paths (the beam).
5. After each step, the model decides whether it has enough information to answer, or should continue (up to a maximum depth).

**Agent use:**
- **Role:** Retriever.
- **How:** Handles questions where the needed path isn't known in advance and query generation is hard. The model explores like a person following links.
- **Rules:** Cap depth, beam width and the number of model calls. Log the explored paths for explanation.
- **Guardrails:** Cost and latency grow quickly. Use it only when templates and text-to-query fail.

### 166. ReAct-style agent with graph tools

**Definition:** An agent that alternates reasoning and tool calls (entity search, neighbor lookup, query execution) to answer questions over a graph.

**How it works:**
1. Tools: `search_entities(text)`, `get_neighbors(id, relation, limit)`, `get_facts(id)`, `run_query(template, params)`, `find_paths(a, b, max_len)`.
2. The agent reasons about what it needs, calls a tool, reads the result, and reasons again.
3. It continues until it can answer, or hits its step budget.
4. The final answer cites the facts gathered.
5. Tool outputs are bounded and structured.

**Agent use:**
- **Role:** Retriever.
- **How:** A flexible way to answer complex questions with small, safe tools rather than one big generated query.
- **Rules:** Tools enforce limits and permissions themselves (K6, KG1). The agent can't bypass them.
- **Guardrails:** Tool results are data (KG5). Graph text fields can't issue instructions to the agent. Set a step budget and stop cleanly when it runs out.

### 167. Temporal knowledge graph as agent memory

**Definition:** Storing what an agent learns from conversations and documents as a time-aware graph of entities and facts.

**How it works:**
1. From each interaction, extract entities and facts (#31), and link them to existing memory entities (#27).
2. Each fact gets valid time and recording time (K8), plus its source (which conversation or document).
3. When new information contradicts an old fact, close the old fact's validity instead of deleting it ("the user moved from Berlin to Munich in May").
4. Retrieval combines semantic search, keyword search and graph traversal, with recency weighting.
5. Episodes (the raw interactions) are kept and linked to the facts derived from them.

**Agent use:**
- **Role:** Curator and Retriever (agent memory).
- **How:** Long-running agents remember users, projects and decisions with history: what's true now, and what was true before.
- **Rules:** Store only what policy allows. Memory facts carry their source and time.
- **Guardrails:** KG2: sensitive personal data is minimized and protected. Users can see and delete memory (#185). Never store secrets or credentials.

### 168. Memory consolidation and forgetting

**Definition:** Merging, summarizing and expiring agent memory, so it stays accurate, compact and appropriate.

**How it works:**
1. **Deduplicate** repeated facts and entities (#35–39).
2. **Consolidate** many episodic details into durable summary facts, keeping links to the episodes.
3. **Supersede** outdated facts (close their validity, #12).
4. **Decay:** lower the retrieval weight of old, rarely used items.
5. **Expire:** delete items past their retention period, or on user request (#185).

**Agent use:**
- **Role:** Curator.
- **How:** Prevents memory from filling with stale, duplicated or contradictory facts that degrade answers.
- **Rules:** Consolidated summaries keep references to their sources (K1).
- **Guardrails:** Forgetting requests are absolute: deletion includes derived summaries and embeddings (#185).

### 169. LLM-assisted curation with human review

**Definition:** Using a language model to propose graph changes, with structured human approval before they're applied.

**How it works:**
1. The model proposes: new facts, corrections, merges, type assignments, schema additions.
2. Each proposal comes with evidence (source quotes, paths, rules) and confidence.
3. Proposals are checked automatically: shapes (#5), consistency (#97), duplicates.
4. Proposals are queued for review, prioritized by impact and uncertainty (#148).
5. Approved proposals are applied by the Curator, with full provenance (who approved, when, what evidence).

**Agent use:**
- **Role:** Curator.
- **How:** Scales curation, since the model does the preparation and people make the decisions.
- **Rules:** K7: proposals never bypass review, except low-risk categories that are explicitly auto-approved by policy.
- **Guardrails:** Track reviewer agreement and rejection rates. A rising rejection rate signals a degraded extractor.

### 170. KG-to-text generation (verbalization)

**Definition:** Turning graph facts into natural-language descriptions.

**How it works:**
1. Select the facts to describe (an entity profile, a path, a subgraph).
2. Order them logically: identity, key attributes, relations, recent events.
3. Generate text with templates (fully faithful) or with an LLM (more fluent).
4. Check faithfulness: every sentence maps back to input facts. No extra facts are added.

**Agent use:**
- **Role:** Retriever.
- **How:** Creates readable entity summaries, path explanations and reports from the graph.
- **Rules:** Use templates for high-stakes text, and LLMs with faithfulness checks elsewhere.
- **Guardrails:** Models can add plausible extra facts during verbalization. Verify output against the input facts (#164).

## D2. Operations and updates

### 171. Incremental graph updates from change data capture

**Definition:** Streaming changes from source systems into the graph continuously, instead of periodic full reloads.

**How it works:**
1. Capture source changes (database logs, events) with keys and versions.
2. Map each change to graph operations: upsert nodes and edges, close validity, delete.
3. Apply them in order per entity, idempotently (#172).
4. Trigger follow-up work: inference maintenance (#91), embeddings and summaries (#175).
5. Track the stream offsets for recovery.

**Agent use:**
- **Role:** Curator.
- **How:** Keeps the graph current without expensive full rebuilds.
- **Rules:** Process deletes with the highest priority.
- **Guardrails:** Monitor consumer lag (#191). A stalled stream silently serves stale facts.

### 172. MERGE and upsert semantics

**Definition:** Writing nodes and edges by matching on keys first, creating them only if they don't exist.

**How it works:**
1. Match on a unique key, such as `MERGE (o:Organization {externalId: $id})`, backed by a unique constraint (#47).
2. If found, update its properties. If not, create it.
3. For edges, match both endpoints by key, then merge the edge, by type and optionally a key (such as a validity start date).
4. Under concurrency, the unique constraint prevents two writers from creating duplicates.
5. Merge only on key properties; set other properties separately.

**Agent use:**
- **Role:** Curator.
- **How:** Every write the agent makes is a merge on stable keys (K5), so retries and re-runs never duplicate entities.
- **Rules:** Never merge on display names or other non-unique properties.
- **Guardrails:** A merge pattern with too many properties creates a new node whenever any property differs, which is a common duplication bug. Merge on keys only.

### 173. Entity and fact versioning (bitemporal updates)

**Definition:** Updating facts in a way that keeps their history and the record of corrections.

**How it works:**
1. **A real-world change** ("moved to Munich"): close the old fact's valid time, and add the new fact with its own valid time.
2. **A correction** (the old fact was wrong): close the old fact's recording time (it's no longer believed), and add the corrected fact.
3. Current queries filter on "valid now" and "currently believed".
4. Historical queries specify the dates.
5. Store who or what made each change (K1).

**Agent use:**
- **Role:** Curator and Retriever.
- **How:** The agent can answer "what's true now", "what was true then" and "what did we believe then", which matters for audits and debugging.
- **Rules:** Updates never overwrite facts in place (K8).
- **Guardrails:** Deletion requests for personal data (#185) override history retention. Corrections aren't the same as erasure.

### 174. Entity merge and split operations

**Definition:** Combining duplicate entities into one, or separating a wrongly merged entity, safely and reversibly.

**How it works:**
1. **Merge:** pick the surviving ID (#39). Move all edges from the merged entities onto it, deduplicating edges. Combine properties according to precedence rules. Keep the old IDs as aliases and redirects (K4). Record a merge event with the evidence.
2. **Split:** using the merge record and per-fact provenance, assign each fact and edge back to the correct entity. Restore the old IDs or mint new ones.
3. Re-run inference maintenance (#91) and refresh derived data (#175).

**Agent use:**
- **Role:** Curator.
- **How:** The agent performs merges as recorded, reversible transactions, never as blind edge rewiring.
- **Rules:** Every merge stores enough provenance to split it later.
- **Guardrails:** Merges of high-degree or high-importance entities need approval (KG3). Take a snapshot first (#24).

### 175. Change propagation to derived data

**Definition:** Updating everything computed from the graph (inferences, embeddings, summaries, caches, indexes) when the graph changes.

**How it works:**
1. Keep a dependency map: which derived items depend on which entities and facts (lineage).
2. When facts change, mark the dependent items stale: inferred facts, entity embeddings, community summaries, text indexes, query caches.
3. Recompute stale items by priority (frequently used first), in batches.
4. Track the staleness: how many derived items are out of date, and for how long.

**Agent use:**
- **Role:** Operator.
- **How:** Prevents answers built on stale summaries or embeddings that still reflect old facts.
- **Rules:** Every derived item records the graph version it was computed from.
- **Guardrails:** Deletions propagate with the highest priority, especially for personal data (#185).

### 176. Incremental community detection and summary refresh

**Definition:** Updating communities and their LLM summaries after graph changes, without recomputing everything.

**How it works:**
1. After changes, find the affected communities: those containing changed nodes or edges.
2. Re-run community detection locally (starting from previous assignments) or periodically in full.
3. Compare the new communities to the old ones by overlap. Keep the IDs of communities that are mostly unchanged.
4. Regenerate summaries only for communities whose membership or key facts changed significantly.
5. Re-index the summaries for GraphRAG (#155).

**Agent use:**
- **Role:** Operator.
- **How:** Keeps GraphRAG summaries current at a fraction of the cost of full re-indexing.
- **Rules:** Set thresholds for when a change warrants a new summary.
- **Guardrails:** Summaries must not keep content about deleted facts (#185). Regenerate them when deletions affect them.

### 177. Incremental PageRank

**Definition:** Updating PageRank scores after graph changes, without starting from scratch.

**How it works:**
1. Start from the previous scores.
2. Apply the changes: added or removed edges change some nodes' outgoing shares.
3. Propagate only the differences, using push-based updates (residuals) or a few power iterations warm-started from the old scores.
4. Converges much faster than a full recompute when changes are small.

**Agent use:**
- **Role:** Operator.
- **How:** Keeps importance scores (used in ranking and linking) fresh on constantly changing graphs.
- **Rules:** Run a full recompute periodically to correct accumulated approximation error.
- **Guardrails:** None specific.

### 178. Distributed graph processing (Pregel / bulk synchronous parallel)

**Definition:** A model for running graph algorithms across many machines in synchronized rounds of vertex computation and message passing.

**How it works:**
1. "Think like a vertex": each vertex runs the same function every round (superstep).
2. In each superstep, a vertex reads messages from the last round, updates its state, and sends messages to its neighbors.
3. A global barrier separates supersteps.
4. Vertices with nothing to do vote to halt. The computation ends when all have halted and no messages remain.
5. PageRank, connected components and shortest paths all map naturally to this model.

**Agent use:**
- **Role:** Operator.
- **How:** Used for analytics on graphs too large for one machine (centrality, communities, embeddings).
- **Rules:** Run analytics on snapshots (#14), and record the snapshot version.
- **Guardrails:** Supernodes create huge message volumes and slow supersteps. Combine or aggregate messages at the sender.

### 179. Access control on graphs

**Definition:** Enforcing who can see or change which nodes, edges and properties.

**How it works:**
1. **RBAC (role-based):** permissions granted by user role, per label, relation type or named graph.
2. **ABAC (attribute-based):** policies based on attributes ("user's department = document's department").
3. **Fine-grained:** permissions per node, edge and property (hide salary but show the employee).
4. Enforcement inside query execution: filtered traversal, so hidden nodes aren't traversed or revealed through paths, counts or aggregates.
5. Inferred facts and summaries inherit the restrictions of their sources.

**Agent use:**
- **Role:** Retriever (every query).
- **How:** The agent always queries with the end user's identity and permissions, never with an all-access service account.
- **Rules:** KG1: enforcement happens in the engine. Derived data (inferences, community summaries, embeddings) carries the access level of its most restricted source.
- **Guardrails:** Test for leaks through paths and aggregates. A count or path can reveal an entity the user can't see directly.

### 180. Supernode handling

**Definition:** Managing nodes with extremely many connections, which make traversals slow and results noisy.

**How it works:**
1. Detect supernodes by degree thresholds (#73, #189).
2. **Query side:** cap neighbor expansion, filter by edge type and properties first, sample neighbors, or skip supernodes as intermediate path steps.
3. **Modeling side:** split edges by type or time bucket, add intermediate nodes (per-year or per-category groups), or model very common values as properties instead of edges ("country" as a property rather than an edge to a Country node).
4. **Storage side:** some engines group a node's edges by type and direction for faster filtering.

**Agent use:**
- **Role:** Retriever and Operator.
- **How:** Prevents runaway traversals (KG4) and meaningless paths ("everything connects through USA").
- **Rules:** Traversal tools enforce per-node fan-out limits automatically.
- **Guardrails:** Alert when new supernodes appear. They often indicate a modeling or data error, such as a placeholder value like "Unknown" becoming a hub.

### 181. Bulk import

**Definition:** Loading large datasets into a graph efficiently, bypassing the slower transactional write path.

**How it works:**
1. Prepare node and edge files (CSV or Parquet), with stable IDs and types.
2. Deduplicate and validate beforehand (shapes, key uniqueness).
3. Use the database's offline or parallel bulk loader, which writes storage files directly, sorted.
4. Build the indexes after loading, not during.
5. Verify the counts, then run validation and sample queries.

**Agent use:**
- **Role:** Operator.
- **How:** Initial loads and full rebuilds run far faster than transactional inserts, often by orders of magnitude.
- **Rules:** Bulk-load into a new database or graph, validate, then switch over.
- **Guardrails:** Bulk loaders often skip constraint checks. Validate the data before loading.

### 182. Partition rebalancing

**Definition:** Moving graph data between machines to fix load imbalance or after adding capacity.

**How it works:**
1. Measure the load per partition: storage, query traffic, cross-partition hops.
2. Plan the moves: which nodes or subgraphs go where, minimizing new cut edges.
3. Copy the data, sync the changes made during the copy, switch the routing, and delete the old copies.
4. Verify the counts and query results after the move.

**Agent use:**
- **Role:** Operator.
- **How:** The agent plans moves from measurements and runs them gradually.
- **Rules:** Throttle rebalancing to protect query latency.
- **Guardrails:** Verify before deleting source copies. Keep the old routing available for rollback.

### 183. Backup, restore and consistency checks

**Definition:** Making recoverable copies of the graph and proving they can be restored correctly.

**How it works:**
1. Take consistent snapshots (all stores at the same point in time), plus transaction logs for point-in-time recovery.
2. Store them separately from the live system, encrypted.
3. Test restores regularly in an isolated environment.
4. After a restore: compare counts, check constraints (#47), run validation (#5) and reference-integrity checks (no edges pointing to missing nodes), and run sample queries.
5. Also back up schema, shapes, mappings and configuration.

**Agent use:**
- **Role:** Operator.
- **How:** The agent includes restore tests in operations and reports the measured recovery time.
- **Rules:** Take a backup or snapshot before every bulk change (KG6).
- **Guardrails:** Backups keep deleted personal data until they expire. The retention policy must state this (#185).

### 184. Schema migration in production

**Definition:** Applying schema changes to a live graph without downtime or data loss.

**How it works:**
1. Plan with expand and contract (#46): add new labels, properties and relations alongside the old ones.
2. Backfill the data into the new structure in batches, with checkpoints.
3. Update writers to write both forms, then update readers to read the new form.
4. Validate: counts match, and the new shapes pass.
5. Remove the old structure after a waiting period, and update prompts, templates and schema catalogs (#152).

**Agent use:**
- **Role:** Operator.
- **How:** The agent runs migrations as staged plans with checks between stages.
- **Rules:** Text-to-query catalogs and templates update in the same release as the schema.
- **Guardrails:** KG3 approval for breaking changes, with a rollback plan (KG6).

### 185. Right to erasure in knowledge graphs

**Definition:** Fully removing a person's data from the graph and from everything derived from it.

**How it works:**
1. Find every node and fact about the person, through entity IDs, aliases and linked records (provenance, K1).
2. Delete or anonymize them, including edges and properties referencing them on other nodes.
3. Remove derived data: inferred facts (#91), entity and text embeddings, community summaries mentioning them (#176), caches, agent memory (#167) and search indexes.
4. Check: queries, vector search and summaries no longer return their data.
5. Track the removal from backups according to policy, and record the evidence.

**Agent use:**
- **Role:** Curator and Operator.
- **How:** The agent runs erasure as a complete checklist with verification, since graphs spread personal data into many derived places.
- **Rules:** Erasure overrides history retention (#173).
- **Guardrails:** KG2: the scope and policy decisions are set by people. The agent reports any places where data remains (backups) and until when.

## D3. Observability and quality

### 186. Knowledge graph quality dashboard

**Definition:** Ongoing measurement of accuracy, completeness, consistency and coverage, per entity type and source.

**How it works:**
1. **Accuracy:** regular random samples of facts, reviewed by people or verified against trusted sources, giving an accuracy estimate with confidence intervals.
2. **Completeness:** the fill rate of required and important properties per type.
3. **Consistency:** violation counts (#187).
4. **Coverage:** entity counts compared with reference lists or expected volumes.
5. Show trends over time and by source.

**Agent use:**
- **Role:** Observer.
- **How:** The agent reports quality with numbers and trends, so curation effort goes to the weakest areas.
- **Rules:** Report sample sizes and methods.
- **Guardrails:** Don't optimize the dashboard metric at the expense of real quality (for example, filling properties with defaults).

### 187. Constraint violation monitoring

**Definition:** Continuously tracking schema and logical violations in the graph.

**How it works:**
1. Run shape validation (#5) on new data at write time, and on the whole graph periodically.
2. Run logical consistency checks (#97): disjoint classes, functional properties with several values, impossible timelines (#99), cycles in acyclic relations (#80).
3. Count violations by type, source and age.
4. Alert on new spikes and route violations to owners.

**Agent use:**
- **Role:** Observer.
- **How:** Catches broken extractors, bad source data and bad merges quickly.
- **Rules:** Each violation type has an owner and a target resolution time.
- **Guardrails:** A sudden spike after a deployment means roll back first, then investigate.

### 188. Query performance monitoring and plan regression

**Definition:** Tracking query latency, resource use and plan changes, to catch slow queries and regressions.

**How it works:**
1. Log query templates (normalized, without literal values) with latency percentiles, rows scanned and rows returned.
2. Capture plans for the important templates, and detect when a plan changes.
3. Detect regressions: a template slowing down after a data or statistics change.
4. Identify the heaviest templates by total cost.

**Agent use:**
- **Role:** Observer.
- **How:** The agent finds expensive generated queries (#151) and turns frequent ones into optimized templates (#61).
- **Rules:** Refresh statistics after bulk loads.
- **Guardrails:** Log templates and parameter types, not personal values (KG2).

### 189. Degree distribution and growth drift

**Definition:** Monitoring how the graph's structure and size change over time.

**How it works:**
1. Track node and edge counts per type, and growth rates.
2. Track degree distributions per type: percentiles and the top-degree nodes.
3. Compare against baselines, and flag sudden changes: a type's count doubling, a new supernode, a relation disappearing.
4. Link the changes to deployments and source loads.

**Agent use:**
- **Role:** Observer.
- **How:** Structural drift often reveals pipeline bugs (an extractor creating edges to a placeholder node) before users notice.
- **Rules:** Annotate expected changes (planned imports), so they don't trigger false alarms.
- **Guardrails:** Investigate unexplained jumps before running downstream jobs (embeddings, summaries) on the changed data.

### 190. Orphans, dangling edges and islands

**Definition:** Finding disconnected or broken parts of the graph.

**How it works:**
1. **Orphans:** nodes with no edges at all.
2. **Dangling references:** edges or IDs pointing to missing or deleted nodes.
3. **Islands:** small connected components separated from the main graph (#79).
4. **Unreferenced aliases:** redirects pointing to IDs that don't exist.
5. Report them by type and source.

**Agent use:**
- **Role:** Observer and Curator.
- **How:** Orphans and islands often signal failed entity linking (entities that should have connected but didn't). Dangling references signal broken deletes or merges.
- **Rules:** Run these checks after merges, deletes and imports.
- **Guardrails:** Some orphans are legitimate (new entities). Use thresholds and trends, not zero tolerance.

### 191. Freshness lag

**Definition:** The delay between a change in the source and its appearance in the graph and derived data.

**How it works:**
1. Each change carries its source time.
2. Measure: source time to graph write, to inference updated, to embeddings and summaries updated.
3. Track the percentiles per source and per stage.
4. Measure end to end with probes (#197).
5. Track deletions separately (#185).

**Agent use:**
- **Role:** Observer.
- **How:** The agent knows how current its answers are, and can say so ("as of 10 minutes ago").
- **Rules:** Set SLOs for freshness of facts, derived data and deletions.
- **Guardrails:** Alert on SLO breaches. Stale graphs produce confidently wrong answers.

### 192. Duplicate entity rate estimation

**Definition:** Estimating how many entities in the graph are unrecognized duplicates.

**How it works:**
1. Sample entities at random.
2. For each, search for likely duplicates with blocking and similarity matching (#35–37).
3. Have reviewers judge the candidate pairs.
4. Estimate the duplicate rate per type and source, with a confidence interval.
5. Track the trend after each entity-resolution improvement.

**Agent use:**
- **Role:** Observer.
- **How:** Duplicates silently break counts, aggregations and multi-hop answers. The agent quantifies how much.
- **Rules:** Use random samples, not only flagged entities.
- **Guardrails:** None specific.

### 193. Provenance coverage

**Definition:** The share of facts that carry complete provenance: source, method, version, time and confidence.

**How it works:**
1. Check each fact (or a sample) for the required provenance fields (K1).
2. Report coverage per source, type and pipeline.
3. Check that source references resolve (the source document still exists and is accessible).
4. Flag facts with missing or broken provenance.

**Agent use:**
- **Role:** Observer.
- **How:** Facts without provenance can't be cited, verified, corrected or erased reliably. The agent treats them as lower trust.
- **Rules:** Writes without provenance are rejected (K1).
- **Guardrails:** Legacy facts without provenance are marked, and excluded from high-stakes answers until fixed.

### 194. Text-to-query accuracy

**Definition:** Measuring how often generated graph queries return the correct answer.

**How it works:**
1. Build a test set: questions with gold queries and expected results, covering important question types.
2. Run the text-to-query pipeline on each question.
3. **Execution accuracy:** do the generated query's results match the expected results?
4. Also track validity rates, repair-loop success (#153), and errors by category: wrong entity, wrong relation, wrong direction, missing filter, wrong aggregation.
5. Re-run on every prompt, model, schema or template change.

**Agent use:**
- **Role:** Observer.
- **How:** The agent knows which question types it answers reliably, and routes the weak ones to templates or human help.
- **Rules:** Execution accuracy (results match), not query text similarity, is the main metric.
- **Guardrails:** Block changes that lower accuracy on the test set.

### 195. GraphRAG and graph-grounded QA evaluation

**Definition:** Measuring the quality of answers that use graph retrieval.

**How it works:**
1. **Golden question set:** factual, multi-hop, aggregate and global (thematic) questions, with expected answers or reference points.
2. **Retrieval metrics:** were the needed entities, facts or paths retrieved (recall)?
3. **Answer metrics:** correctness, faithfulness to the retrieved context (#164), citation validity (#162), completeness.
4. For global questions, compare comprehensiveness and diversity, often with LLM judges calibrated against people.
5. Compare against a plain vector-RAG baseline, to confirm the graph actually helps.

**Agent use:**
- **Role:** Observer.
- **How:** The agent justifies graph features (community summaries, path retrieval) with measured gains, not assumptions.
- **Rules:** Version the golden set and the judges. Keep a held-out portion.
- **Guardrails:** LLM judges have biases. Check agreement with people regularly.

### 196. Prediction quality monitoring

**Definition:** Tracking the real-world accuracy of predicted and inferred facts after they're used.

**How it works:**
1. For predicted facts (completion, typing, links), track their review outcomes and later confirmations or contradictions from new data.
2. Compute precision per model, relation and confidence band.
3. Compare against the calibration curve (#144). Diverging means recalibrate or retrain.
4. Track it over time, since data drift reduces accuracy.

**Agent use:**
- **Role:** Observer.
- **How:** The agent adjusts auto-accept thresholds based on measured precision, not the original benchmarks.
- **Rules:** Predicted facts can be traced to their model version (K1), so a bad model's facts can be found and removed.
- **Guardrails:** If precision drops below the threshold, auto-acceptance stops and predictions go to review.

### 197. Canary queries and probes

**Definition:** Fixed test queries and test writes run continuously to check the graph system end to end.

**How it works:**
1. **Canary reads:** fixed queries with known answers (an entity's key facts, a path, a count range).
2. **Write probes:** insert a marker fact, measure the time until it's queryable and reflected in derived data, then delete it and measure the time until it's gone.
3. **Access probes:** query as a restricted user for data they must not see. Expect nothing.
4. **Text-to-query probes:** a few fixed natural-language questions with expected answers.
5. Alert on any failure or slowdown.

**Agent use:**
- **Role:** Observer.
- **How:** Detects broken deployments, stalled pipelines and access-control regressions within minutes.
- **Rules:** Probes cover reads, writes, deletes, permissions and LLM pipelines.
- **Guardrails:** Probe data is clearly marked and excluded from analytics and real answers.

### 198. Audit logging

**Definition:** A tamper-evident record of who accessed or changed what in the graph, and why.

**How it works:**
1. Log writes (who or what, when, what changed, the before and after values or references, the reason or approval reference).
2. Log sensitive reads (queries touching restricted data), with user identity.
3. Log agent actions: tool calls, generated queries, approvals received.
4. Store the logs append-only, with integrity protection (hash chaining or write-once storage), separate from the graph.
5. Set retention by policy.

**Agent use:**
- **Role:** Observer.
- **How:** Every agent change can be traced to a plan, an approval and evidence. Investigations can reconstruct what happened.
- **Rules:** Agent writes always include a reason and a reference to the plan or request.
- **Guardrails:** Audit logs contain sensitive information. Restrict access, and apply minimization (KG2).

### 199. Cost monitoring

**Definition:** Tracking the cost of graph storage, queries, analytics and LLM-based features.

**How it works:**
1. Attribute costs: storage per graph or tenant, compute per query template, analytics jobs, LLM tokens for extraction, summaries, text-to-query and judges.
2. Compute unit costs: per extracted document, per answered question, per community summary refresh.
3. Track trends, and alert on spikes (runaway agent loops, repeated failed repairs).
4. Compare cost against quality gains.

**Agent use:**
- **Role:** Observer and Operator.
- **How:** The agent picks cheaper paths when quality allows: templates over free-form generation, local over global search, incremental over full refresh.
- **Rules:** Each pipeline has a budget and an owner.
- **Guardrails:** Hard limits on LLM calls per question and per job prevent runaway costs.

### 200. Feedback loop for continuous improvement

**Definition:** Systematically turning observed failures into fixes in extraction, linking, schema, retrieval and prompts.

**How it works:**
1. **Collect signals:** user feedback, failed queries (#194), hallucination flags (#164), review rejections (#169), violations (#187), quality samples (#186).
2. **Cluster failures by cause:** wrong linking, missing schema relation, extraction gap, a bad template, a retrieval miss.
3. **Fix the right layer:** extractor prompts, linking features, schema additions, templates, retrieval settings.
4. **Lock it in:** add the failing cases to test sets (#194, #195).
5. **Validate** on the full test sets, deploy, and monitor.

**Agent use:**
- **Role:** Operator.
- **How:** The agent runs this cycle continuously, so the knowledge graph and its AI layer get measurably better over time.
- **Rules:** Every change links to the failures it fixes and the metrics that prove it.
- **Guardrails:** Schema changes, bulk merges and policy changes still need human approval (KG3).

---

## How the 200 entries fit together

1. **Model:** standards-based schema (#1–12), shapes (#5), stable IDs (#8), time (#12), provenance (#9–10).
2. **Build:** extraction (#25–34) → entity resolution (#35–39) → normalization (#40, #49) → validation (#5, #47) → truth discovery (#50), with MERGE writes (#172) and review (#169).
3. **Reason:** rules and ontologies (#85–94), mined rules (#95), consistency (#97, #100), with inferred facts marked (K2).
4. **Learn:** embeddings and GNNs (#101–130) for completion, typing and alignment (#131–143), calibrated (#144), explained (#145), evaluated without leakage (#149).
5. **Answer:** entity linking (#154) → templates or text-to-query with validation (#61, #151–153) → subgraph, path and hybrid retrieval (#157–160) → GraphRAG local or global (#155–156) → grounded, cited answers (#161–164).
6. **Operate:** CDC updates (#171), versioning (#173), merges and splits (#174), change propagation (#175), access control (#179), supernode handling (#180), erasure (#185).
7. **Observe:** quality (#186–193), text-to-query and QA evaluation (#194–195), prediction monitoring (#196), probes (#197), audits (#198), cost (#199), and the feedback loop (#200).