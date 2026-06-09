"""Realistic padding pool for the pressure-zone test.

Each entry is a self-contained mini-dialog fragment that mirrors what real long research
dialogs contain BEYOND the load-bearing decisions: prior iterations that got revised,
tangents that ended in 'let's not pursue this', vendor comparisons that didn't commit,
repetitions of already-decided items, exploratory questions never answered.

None of this content is in the case6 GT. Padding is hand-written, deterministic, and
labelled by category. The padder interleaves these between case6 turns so the dialog
flows naturally but the load-bearing structure is unchanged.
"""

# Prior-iteration noise: earlier versions of decisions that got revised.
PRIOR_ITERATION = [
    [
        {"role": "user", "content": "Earlier we floated using Redis with TTL-based invalidation. I want to circle back: TTL invalidation has the staleness window problem we discussed but it's operationally simple."},
        {"role": "assistant", "content": "TTL-based invalidation is simple but you accept up to TTL seconds of staleness on cached entries. For online lookups that's hard to swallow."},
        {"role": "user", "content": "Yeah, the staleness window is a problem at our latency budget. Let's drop the TTL idea. We already decided default-no on Redis anyway."},
        {"role": "assistant", "content": "Right, that's superseded by the default-no Redis decision. Setting this aside."},
    ],
    [
        {"role": "user", "content": "Going back to the snapshot frequency question — at one point I was thinking 1-minute snapshots for tighter freshness. Why did we land on 5 minutes again?"},
        {"role": "assistant", "content": "1-minute snapshots produce ~5x the snapshot volume. Storage cost and snapshot pipeline load become problematic. 5 minutes was the compromise the data team accepted."},
        {"role": "user", "content": "Right. 1-minute would have been nicer but the data team OK'd 5. We're not revisiting that."},
        {"role": "assistant", "content": "Five minutes stands."},
    ],
    [
        {"role": "user", "content": "I had an earlier idea about using ScyllaDB instead of Cassandra. Same wire protocol, better per-node throughput. Why didn't we pick it?"},
        {"role": "assistant", "content": "Operational maturity. Cassandra is well-understood; Scylla is a smaller ecosystem and we'd be the first in the org to run it. The throughput edge wasn't worth the unknown."},
        {"role": "user", "content": "Right. We default to the more boring choice when capabilities are similar."},
        {"role": "assistant", "content": "Cassandra it is. Scylla shelved indefinitely."},
    ],
    [
        {"role": "user", "content": "Earlier draft of the rollout plan had a phased canary — 1% traffic, then 10%, then 50%. We dropped that for the cut-over approach. Why again?"},
        {"role": "assistant", "content": "Canary doesn't help when the new system is functionally different at the data layer. The data has to be identical at cut-over time; you can't canary that. Validation gates replace canary in our case."},
        {"role": "user", "content": "Right. Canary is for compute-layer changes, not data-layer cut-overs."},
        {"role": "assistant", "content": "Cut-over with validation gates stands."},
    ],
    [
        {"role": "user", "content": "Going back to authentication: we considered using API keys instead of OAuth for service-to-service. Why did we pick mTLS in the end?"},
        {"role": "assistant", "content": "API keys are bearer tokens — anyone with the key has access. mTLS ties identity to a certificate that's harder to exfiltrate and easier to rotate. For service-to-service inside our infrastructure, mTLS is the higher bar."},
        {"role": "user", "content": "Yeah, mTLS for service-to-service is correct. API keys would be a regression."},
        {"role": "assistant", "content": "mTLS for the ingestion service stays. API keys are not on the table."},
    ],
]

# Abandoned tangent noise: questions that got asked but didn't lead anywhere binding.
ABANDONED_TANGENT = [
    [
        {"role": "user", "content": "Out of curiosity: what would the system look like if we wrote it in Rust instead of using the JVM-based JanusGraph?"},
        {"role": "assistant", "content": "Rust would mean writing our own graph engine. The engineering cost is enormous — we'd be a graph-database company instead of a customer-facing analytics company. Not viable."},
        {"role": "user", "content": "Yeah, that was just curiosity. Not a real proposal."},
        {"role": "assistant", "content": "Right. JanusGraph stays."},
    ],
    [
        {"role": "user", "content": "Have you ever seen anyone use Datalog as the query language for a system like this?"},
        {"role": "assistant", "content": "Datalog is elegant for graph reasoning but most teams find it too unfamiliar to maintain. There are systems like Datomic that use it. Not relevant to our pick though."},
        {"role": "user", "content": "Just wondering. Moving on."},
        {"role": "assistant", "content": "Sure."},
    ],
    [
        {"role": "user", "content": "What about edge-compute caching? Could we put a JanusGraph read replica at edge POPs to reduce latency for geographically distributed users?"},
        {"role": "assistant", "content": "Edge replicas for graph data are a significant operational complexity multiplier. And our users aren't geographically distributed in a way that would benefit — most traffic is from one or two regions."},
        {"role": "user", "content": "Then it's overkill. Not pursuing."},
        {"role": "assistant", "content": "Edge caching shelved."},
    ],
    [
        {"role": "user", "content": "Random thought: what if we used a graph neural network to predict hot paths and pre-warm the cache?"},
        {"role": "assistant", "content": "ML-based cache warming exists in research papers but in practice the deterministic 'most-recently-used' or 'most-frequently-used' heuristics get you 90% of the way. ML adds operational complexity for marginal gain."},
        {"role": "user", "content": "Yeah, not for v1. Maybe v3 if we have the data to train it."},
        {"role": "assistant", "content": "Deferred indefinitely."},
    ],
    [
        {"role": "user", "content": "Have we considered offering a GraphQL gateway in front of the REST API for clients who want declarative queries?"},
        {"role": "assistant", "content": "GraphQL on top of our constrained REST would be a thin shim. It would add a layer to operate without adding new capabilities. Most clients are internal services that already use REST."},
        {"role": "user", "content": "Not worth it then."},
        {"role": "assistant", "content": "GraphQL not pursued."},
    ],
]

# Vendor / tooling comparison that ended without commitment
VENDOR_COMPARISON = [
    [
        {"role": "user", "content": "How does our setup compare to Stardog, Ontotext, or other commercial graph platforms? Anything we're missing?"},
        {"role": "assistant", "content": "Stardog and Ontotext target the semantic-web / RDF / SPARQL world. Strong on inference and reasoning, weaker on the raw-edge-count throughput we need. Our property-graph workload doesn't benefit from their semantic strengths."},
        {"role": "user", "content": "So they're solving a different problem. Not applicable."},
        {"role": "assistant", "content": "Different problem domain. No action."},
    ],
    [
        {"role": "user", "content": "What about Amazon Neptune? Managed graph DB on AWS, supports both Gremlin and SPARQL."},
        {"role": "assistant", "content": "Neptune at 50B edges would be expensive — their pricing is per-instance-hour and we'd need a large instance. Also vendor lock-in to AWS, which has come up in other contexts as a concern."},
        {"role": "user", "content": "Both are real issues. Plus the proprietary Gremlin extensions wouldn't migrate. Not pursuing."},
        {"role": "assistant", "content": "Neptune not pursued for cost and lock-in reasons."},
    ],
    [
        {"role": "user", "content": "Has anyone here used Memgraph? In-memory graph DB, supposedly very fast."},
        {"role": "assistant", "content": "Memgraph is fast in-memory but the in-memory footprint at 50B edges is prohibitive. We'd need terabytes of RAM. Not realistic for our budget."},
        {"role": "user", "content": "Yeah, 50B edges in RAM is out. Memgraph would be great at maybe 1B."},
        {"role": "assistant", "content": "Memgraph shelved at our scale."},
    ],
    [
        {"role": "user", "content": "What about ArangoDB? Multi-model, has good graph performance."},
        {"role": "assistant", "content": "ArangoDB is solid but the operational story at our scale is less mature than Cassandra. We'd be relying on the multi-model promise that we don't actually need — we'd use it as a graph store, period."},
        {"role": "user", "content": "Don't pay for capabilities we won't use."},
        {"role": "assistant", "content": "ArangoDB not picked."},
    ],
    [
        {"role": "user", "content": "OrientDB? It's been around forever, multi-model like Arango."},
        {"role": "assistant", "content": "OrientDB's been in maintenance-mode for years. The community has thinned. Not a safe bet for new infrastructure."},
        {"role": "user", "content": "Right, hard pass."},
        {"role": "assistant", "content": "OrientDB rejected on ecosystem health."},
    ],
]

# Repetition: a topic that comes up again later in slightly different framing
REPETITION = [
    [
        {"role": "user", "content": "Just to make sure I have it straight — the analytical staleness window is 5 minutes, right?"},
        {"role": "assistant", "content": "Yes, 5 minutes is the hard requirement from the data team. We refresh the Parquet snapshot every 5 minutes from the Cassandra source of truth."},
        {"role": "user", "content": "Got it."},
        {"role": "assistant", "content": "Confirmed."},
    ],
    [
        {"role": "user", "content": "And online lookups have to be under 50ms at p99?"},
        {"role": "assistant", "content": "Yes, p99 under 50ms, p50 under 10ms, sustained at 5k QPS with bursts to 20k."},
        {"role": "user", "content": "Right."},
        {"role": "assistant", "content": "That's the latency budget."},
    ],
    [
        {"role": "user", "content": "Are we still going with JanusGraph or did we revisit that?"},
        {"role": "assistant", "content": "Still JanusGraph. The decision stood through the various sanity checks — Postgres-with-AGE wouldn't scale, Neo4j cost was too high. Production rollout is conditional on operational expertise."},
        {"role": "user", "content": "OK, still JanusGraph then."},
        {"role": "assistant", "content": "Yes."},
    ],
    [
        {"role": "user", "content": "Just confirming — no Redis cache in v1, right?"},
        {"role": "assistant", "content": "Right. Default-no on Redis in v1. Reconsider only if production measurements force it."},
        {"role": "user", "content": "OK."},
        {"role": "assistant", "content": "Confirmed."},
    ],
    [
        {"role": "user", "content": "And we're at 99.9% availability target, no multi-region active-active?"},
        {"role": "assistant", "content": "Right, three nines, single-region. Multi-region was discussed and explicitly deferred."},
        {"role": "user", "content": "Got it."},
        {"role": "assistant", "content": "Three nines stands."},
    ],
    [
        {"role": "user", "content": "Just want to double-check the cut-over plan — replay-based migration, not dual-write?"},
        {"role": "assistant", "content": "Replay-based from a known checkpoint. Dual-write was rejected because it would double write load."},
        {"role": "user", "content": "Right."},
        {"role": "assistant", "content": "Replay it is."},
    ],
]

# Exploratory question never answered: something asked, not resolved, not added to GT
EXPLORATORY = [
    [
        {"role": "user", "content": "I keep wondering about disaster-recovery RTO/RPO targets. Have we written those down?"},
        {"role": "assistant", "content": "We haven't actually written formal DR targets. The implicit assumption is the Cassandra RF=3 plus object-storage backups give us 'good enough' DR, but we haven't measured."},
        {"role": "user", "content": "We should formalize that eventually. Adding to my mental list, not blocking anything."},
        {"role": "assistant", "content": "Noted, not actioned."},
    ],
    [
        {"role": "user", "content": "Have we thought about what happens if Cassandra has a poison-pill query that takes down a node?"},
        {"role": "assistant", "content": "Cassandra has some query-killer capabilities but they're imperfect. We'd want to add query monitoring at the JanusGraph layer to catch pathological queries before they hit Cassandra."},
        {"role": "user", "content": "Probably an ops concern more than design-time. Park it."},
        {"role": "assistant", "content": "Parked."},
    ],
    [
        {"role": "user", "content": "Do we have a plan for what happens when JanusGraph releases a major version update?"},
        {"role": "assistant", "content": "Major version updates of a production data system are always painful. We'd do a parallel cluster with replay-based migration, similar to our initial cut-over plan."},
        {"role": "user", "content": "OK, but we don't need to plan that for v1. It's a future-team problem."},
        {"role": "assistant", "content": "Future problem."},
    ],
    [
        {"role": "user", "content": "What's the bus-factor on this whole thing? If two people get hit by buses, is the system maintainable?"},
        {"role": "assistant", "content": "Honestly, bus-factor is probably 2 right now. That's not a system property, it's an org property. We need documentation and cross-training as part of the rollout."},
        {"role": "user", "content": "Add it to my mental list. Not blocking."},
        {"role": "assistant", "content": "Noted."},
    ],
    [
        {"role": "user", "content": "Do we have a story for graceful degradation if Cassandra has a partial outage?"},
        {"role": "assistant", "content": "Cassandra with RF=3 tolerates one node down per replication group transparently. Beyond that, we'd be serving stale/partial data. Graceful degradation policy isn't formalized — we'd need to decide whether to fail open or fail closed."},
        {"role": "user", "content": "Another formalization gap. Park it."},
        {"role": "assistant", "content": "Parked."},
    ],
    [
        {"role": "user", "content": "Have we costed out a chaos-engineering practice? Periodic node kills, network partitions, etc."},
        {"role": "assistant", "content": "Chaos engineering is best-practice but adds engineering load. For v1 we'd probably stop at game-day exercises and add chaos-engineering tooling later."},
        {"role": "user", "content": "Game-days first, chaos automation later. Fine."},
        {"role": "assistant", "content": "Agreed."},
    ],
]

ALL_POOLS = {
    "prior_iteration": PRIOR_ITERATION,
    "abandoned_tangent": ABANDONED_TANGENT,
    "vendor_comparison": VENDOR_COMPARISON,
    "repetition": REPETITION,
    "exploratory": EXPLORATORY,
}
