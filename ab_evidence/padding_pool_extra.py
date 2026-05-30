"""Additional padding pool — extends padding_pool.py.

Total target: enough fragments that 30k-100k padded dialogs don't need many repetitions of
the same fragment. Each fragment is hand-written, distinct, and NOT in any case GT.
"""

PRIOR_ITERATION_2 = [
    [
        {"role": "user", "content": "We had a whole thread early on about using ElasticSearch as a secondary index. Why did we drop it?"},
        {"role": "assistant", "content": "ES would have given us flexible full-text search but JanusGraph composite indexes cover our enumerated query patterns. Adding ES would be a second data store to keep in sync, which violates the simpler-stack principle."},
        {"role": "user", "content": "Right, sync between two stores is its own problem. ES stays off the table."},
        {"role": "assistant", "content": "ES not pursued."},
    ],
    [
        {"role": "user", "content": "Earlier we discussed CRDT-based conflict resolution for cross-region writes. Did we ever resolve that?"},
        {"role": "assistant", "content": "It got absorbed into the 'no multi-region active-active for v1' decision. If we ever go active-active, CRDT design becomes a real conversation."},
        {"role": "user", "content": "OK so CRDT is post-v1 territory."},
        {"role": "assistant", "content": "Tied to active-active decision. Post-v1."},
    ],
    [
        {"role": "user", "content": "At some point we floated the idea of a write-through cache that synchronously writes to both Cassandra and Redis. Why didn't that fly?"},
        {"role": "assistant", "content": "Write-through means every write pays double latency and you have a coherence problem if one side fails. Plus we now have default-no on Redis anyway."},
        {"role": "user", "content": "Right, both problems. Dropped."},
        {"role": "assistant", "content": "Write-through cache shelved."},
    ],
    [
        {"role": "user", "content": "There was an earlier proposal to use Kafka as the write log so we could replay. We went with something else, right?"},
        {"role": "assistant", "content": "Cassandra's commit log effectively serves as our write log via the incremental backup mechanism. Adding Kafka would be a parallel system for the same purpose."},
        {"role": "user", "content": "Yeah, don't duplicate. Cassandra's log is enough."},
        {"role": "assistant", "content": "Kafka not added."},
    ],
    [
        {"role": "user", "content": "Going back to the schema-versioning discussion: I had drafted a proposal where every vertex carries a schema version. We did something simpler in the end?"},
        {"role": "assistant", "content": "Per-vertex schema version is heavyweight. We landed on a single global migration log version stored in a control vertex."},
        {"role": "user", "content": "Right, additive rule means we don't need per-vertex versions."},
        {"role": "assistant", "content": "Global migration version stands."},
    ],
    [
        {"role": "user", "content": "I remember we briefly considered ZeroMQ for the ingestion-to-storage path. Why isn't that in the final picture?"},
        {"role": "assistant", "content": "ZeroMQ is excellent at low-latency message passing but doesn't give us durability. We need durable queuing so we landed on a managed durable queue with at-least-once semantics."},
        {"role": "user", "content": "Right, we need durability. ZeroMQ stays out."},
        {"role": "assistant", "content": "ZMQ rejected on durability grounds."},
    ],
    [
        {"role": "user", "content": "Early in the discussion we talked about exposing a streaming API for real-time updates to analytical clients. We dropped that, right?"},
        {"role": "assistant", "content": "Real-time analytical updates is on the explicitly-deferred list (D26). Clients accept the 5-minute snapshot window."},
        {"role": "user", "content": "Right, that's post-v1."},
        {"role": "assistant", "content": "Streaming API deferred."},
    ],
    [
        {"role": "user", "content": "Did we ever get to a decision on whether to store derived metrics (vertex degree, page-rank, etc.) in the graph itself or compute them on demand?"},
        {"role": "assistant", "content": "It got absorbed into the 'analytical layer for any non-trivial computation' principle. We don't pre-compute derived metrics in the online store; analytical handles it."},
        {"role": "user", "content": "Right, online stays narrow."},
        {"role": "assistant", "content": "Derived metrics go through analytical."},
    ],
]

ABANDONED_TANGENT_2 = [
    [
        {"role": "user", "content": "Random thought: what if we used homomorphic encryption so the cloud provider can't see our graph data even if they wanted to?"},
        {"role": "assistant", "content": "Homomorphic encryption for graph operations is hundreds of times slower than plaintext. Latency budget would be destroyed."},
        {"role": "user", "content": "Yeah, the latency tradeoff makes it a non-starter."},
        {"role": "assistant", "content": "HE shelved."},
    ],
    [
        {"role": "user", "content": "I saw a paper about using LSM-tree variants tuned for graph workloads. Anyone tried that?"},
        {"role": "assistant", "content": "It's a research direction. Production-ready implementations are scarce. RocksDB-with-tuning is the closest mainstream answer."},
        {"role": "user", "content": "Research-grade stuff isn't where we should be."},
        {"role": "assistant", "content": "Mainstream LSM via Cassandra/RocksDB is enough."},
    ],
    [
        {"role": "user", "content": "What if we open-sourced the parts of our system that aren't customer-specific?"},
        {"role": "assistant", "content": "Open-sourcing is a legal and product decision more than a technical one. Not in scope of this design conversation."},
        {"role": "user", "content": "Right, that's an exec call. Not here."},
        {"role": "assistant", "content": "Out of scope."},
    ],
    [
        {"role": "user", "content": "Could we use bloom filters somewhere to short-circuit existence queries?"},
        {"role": "assistant", "content": "JanusGraph already uses bloom filters in its Cassandra storage layer. They're transparent — we benefit without doing anything specific."},
        {"role": "user", "content": "Good, already covered."},
        {"role": "assistant", "content": "Bloom filters are in there by default."},
    ],
    [
        {"role": "user", "content": "What if we built a query plan analyzer that warns developers about expensive queries before they ship?"},
        {"role": "assistant", "content": "Static query analysis on Gremlin/Cypher is hard because the cost depends on data shapes. Best-effort tools exist but they're imperfect."},
        {"role": "user", "content": "Sounds like nice-to-have but not essential."},
        {"role": "assistant", "content": "Nice-to-have, post-v1."},
    ],
    [
        {"role": "user", "content": "Random idea: integrate with our user-data warehouse via change-data-capture so the warehouse knows when a user is erased."},
        {"role": "assistant", "content": "CDC integration with the warehouse is a separate project. The warehouse team has their own pipelines."},
        {"role": "user", "content": "Right, separate team's problem."},
        {"role": "assistant", "content": "Out of scope."},
    ],
    [
        {"role": "user", "content": "What about temporal queries — 'show me the graph as it was a week ago'?"},
        {"role": "assistant", "content": "Temporal queries on a graph that doesn't track per-vertex history would require expensive reconstruction from snapshots. We're not building that in v1; daily snapshots give partial time-travel for analytical."},
        {"role": "user", "content": "Daily snapshots are enough for now."},
        {"role": "assistant", "content": "Temporal queries via snapshot history. No first-class temporal."},
    ],
    [
        {"role": "user", "content": "I'm curious about edge weights — do we support weighted edges in the schema?"},
        {"role": "assistant", "content": "JanusGraph supports properties on edges, so weights are just a property. No special weighted-edge plumbing needed; queries that care about weights filter on the property."},
        {"role": "user", "content": "Good, no special case needed."},
        {"role": "assistant", "content": "Weights are just edge properties."},
    ],
]

VENDOR_COMPARISON_2 = [
    [
        {"role": "user", "content": "What about RedisGraph? Redis with a graph module on top, all in-memory."},
        {"role": "assistant", "content": "RedisGraph is fast in-memory but Redis itself was abandoned by Redis Labs for graph use cases — they shut it down in 2023. So it's not a live option."},
        {"role": "user", "content": "Oh, didn't know it was discontinued. Hard pass then."},
        {"role": "assistant", "content": "RedisGraph dead. Not pursued."},
    ],
    [
        {"role": "user", "content": "Has anyone here used Dgraph in production?"},
        {"role": "assistant", "content": "Dgraph has interesting GraphQL-native design. Operational reports are mixed at scale. The company had instability issues in 2022-2023 which affects long-term confidence."},
        {"role": "user", "content": "Vendor stability is a real concern. Not safe to bet on for new infra."},
        {"role": "assistant", "content": "Dgraph not pursued on stability grounds."},
    ],
    [
        {"role": "user", "content": "What about NebulaGraph? It's open source from China, allegedly scales well."},
        {"role": "assistant", "content": "NebulaGraph has good benchmarks but the documentation outside Chinese is patchy. Operational support for an English-speaking team would be a challenge."},
        {"role": "user", "content": "Documentation matters. JanusGraph stays."},
        {"role": "assistant", "content": "Nebula not pursued."},
    ],
    [
        {"role": "user", "content": "Anyone want to argue for Cosmos DB with the Gremlin API?"},
        {"role": "assistant", "content": "Cosmos pricing is famously expensive at high throughput. The Gremlin API on Cosmos has some quirks vs reference Gremlin. And vendor lock-in to Azure."},
        {"role": "user", "content": "Cost plus lock-in is what killed Neptune for us. Same applies to Cosmos."},
        {"role": "assistant", "content": "Cosmos not pursued."},
    ],
    [
        {"role": "user", "content": "What about AllegroGraph? Mature semantic-web graph DB."},
        {"role": "assistant", "content": "AllegroGraph is RDF/SPARQL-focused like Stardog. Different problem domain. We're property-graph, not semantic-web."},
        {"role": "user", "content": "Right, wrong tool."},
        {"role": "assistant", "content": "AllegroGraph not relevant."},
    ],
    [
        {"role": "user", "content": "Hugegraph? Another open-source Chinese option."},
        {"role": "assistant", "content": "Hugegraph is interesting but smaller community than JanusGraph and less English documentation."},
        {"role": "user", "content": "Same answer as Nebula. Not pursuing."},
        {"role": "assistant", "content": "Hugegraph not pursued."},
    ],
]

REPETITION_2 = [
    [
        {"role": "user", "content": "Just to verify — Spark is out, right?"},
        {"role": "assistant", "content": "Right, Spark is dropped. DuckDB handles our analytical layer."},
        {"role": "user", "content": "OK."},
        {"role": "assistant", "content": "Confirmed."},
    ],
    [
        {"role": "user", "content": "And we're not adding Gremlin to the analytical side?"},
        {"role": "assistant", "content": "Correct. SQL only on analytical. Gremlin not pursued."},
        {"role": "user", "content": "Right."},
        {"role": "assistant", "content": "SQL-only on analytical."},
    ],
    [
        {"role": "user", "content": "Are the validation gates for cut-over still all three required?"},
        {"role": "assistant", "content": "Yes: bit-exact match on holdout, 1.5x throughput, 7-day soak. All three are hard gates."},
        {"role": "user", "content": "OK, three hard gates."},
        {"role": "assistant", "content": "Three hard gates confirmed."},
    ],
    [
        {"role": "user", "content": "And no Friday cut-overs, no pre-holiday, no PTO?"},
        {"role": "assistant", "content": "Right, all three scheduling constraints. They're a hard rule."},
        {"role": "user", "content": "Got it."},
        {"role": "assistant", "content": "Scheduling rule confirmed."},
    ],
    [
        {"role": "user", "content": "GDPR erasure still propagates within one snapshot window?"},
        {"role": "assistant", "content": "Yes, 5 minutes worst-case for analytical. Online is immediate."},
        {"role": "user", "content": "5 minutes for analytical, immediate for online."},
        {"role": "assistant", "content": "Confirmed."},
    ],
    [
        {"role": "user", "content": "Are we still encrypting both at rest and in transit?"},
        {"role": "assistant", "content": "Yes, both. Cassandra and Parquet at rest, all client connections in transit. KMS for keys."},
        {"role": "user", "content": "OK."},
        {"role": "assistant", "content": "Encryption confirmed."},
    ],
    [
        {"role": "user", "content": "Just confirming the 14-day daily plus 12-month monthly retention?"},
        {"role": "assistant", "content": "Right. 14 days at daily granularity, then monthly snapshots out to 12 months."},
        {"role": "user", "content": "Got it."},
        {"role": "assistant", "content": "Retention policy stands."},
    ],
    [
        {"role": "user", "content": "Cluster size is 15 nodes, static, no autoscaling?"},
        {"role": "assistant", "content": "Yes, 15 nodes sized for the 20k burst. No storage-layer autoscaling."},
        {"role": "user", "content": "15 static nodes."},
        {"role": "assistant", "content": "Confirmed."},
    ],
]

EXPLORATORY_2 = [
    [
        {"role": "user", "content": "Has anyone thought about how we'd handle a malformed-data ingestion incident? Bad data from upstream that corrupts a chunk of the graph."},
        {"role": "assistant", "content": "We'd roll back to the last clean Cassandra snapshot and replay good data from the write log. Recovery time depends on how far back the corruption goes."},
        {"role": "user", "content": "Not v1 priority but a real operational concern. Park it."},
        {"role": "assistant", "content": "Parked for ops planning."},
    ],
    [
        {"role": "user", "content": "Do we have any sense of what happens if our partner Alpha onboards 10x the queries we expected?"},
        {"role": "assistant", "content": "Their rate limit at the gateway would kick in. We'd see lots of 429s on their end and not be impacted ourselves."},
        {"role": "user", "content": "Right, technical answer is fine. Contract is a separate conversation."},
        {"role": "assistant", "content": "Tech side handled by rate limits."},
    ],
    [
        {"role": "user", "content": "What's the on-call rotation look like for this system?"},
        {"role": "assistant", "content": "On-call structure is a people/process question. The team that builds it should own first-line."},
        {"role": "user", "content": "Yeah, that's an org conversation. Park."},
        {"role": "assistant", "content": "Parked."},
    ],
    [
        {"role": "user", "content": "If we have to do a full data re-ingest from upstream, what's the timeline?"},
        {"role": "assistant", "content": "At our bulk-load throughput, re-ingesting 50B edges would take days."},
        {"role": "user", "content": "Days. Good to know."},
        {"role": "assistant", "content": "Days bound recorded informally."},
    ],
    [
        {"role": "user", "content": "Do analytical users have a way to know if their query result is stale relative to the latest snapshot?"},
        {"role": "assistant", "content": "We expose the snapshot timestamp in the query response metadata."},
        {"role": "user", "content": "OK, so transparency at the query level. Good."},
        {"role": "assistant", "content": "Snapshot timestamp in response metadata."},
    ],
    [
        {"role": "user", "content": "If a partner contract changes mid-quarter, how fast can we update their scope?"},
        {"role": "assistant", "content": "View definitions are quick to update. New scope is live within hours."},
        {"role": "user", "content": "Hours for live scope changes. Good."},
        {"role": "assistant", "content": "Fast partner-scope changes possible."},
    ],
    [
        {"role": "user", "content": "I'm wondering about the cost of running shadow queries continuously."},
        {"role": "assistant", "content": "Shadow queries are a tiny fraction of production traffic — every 10 minutes against a sample. Cost is negligible."},
        {"role": "user", "content": "Right, negligible cost."},
        {"role": "assistant", "content": "Shadow queries are cheap."},
    ],
    [
        {"role": "user", "content": "Anyone thought about how this system would migrate if we changed cloud providers?"},
        {"role": "assistant", "content": "Cassandra and DuckDB are portable. JanusGraph is portable. The architecture is largely cloud-agnostic by design."},
        {"role": "user", "content": "Good, that wasn't accidental."},
        {"role": "assistant", "content": "Cloud-agnostic by design."},
    ],
]

EXTRA_POOLS = {
    "prior_iteration": PRIOR_ITERATION_2,
    "abandoned_tangent": ABANDONED_TANGENT_2,
    "vendor_comparison": VENDOR_COMPARISON_2,
    "repetition": REPETITION_2,
    "exploratory": EXPLORATORY_2,
}
