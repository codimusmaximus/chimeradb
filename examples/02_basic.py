#!/usr/bin/env python3
"""
Basic Example: Semantic Search + Hybrid Queries
================================================

Why Semantic Search for LLMs?
------------------------------
When an LLM needs to answer questions, it can't make 10 round trips asking:
  "Give me top 10 documents"
  "Give me next 10 documents"
  "Give me next 10 documents"
  ...

Instead, we use semantic search with embeddings to find the MOST RELEVANT information
in ONE query. This is crucial for:
  • RAG (Retrieval Augmented Generation)
  • Question answering systems
  • Chatbots that need context
  • Any LLM application that references external data

Hybrid Queries: Cypher + SQL
-----------------------------
Best practice is to combine graph and relational queries:

  1. CYPHER: Find relevant entities using graph patterns
     Example: "Find all servers connected to the web tier"

  2. SQL: Aggregate/analyze the data from those entities
     Example: "Calculate average CPU usage for those servers"

This gives you graph flexibility + SQL power.

Real-World Example:
-------------------
We'll build a system monitoring graph:
  • Servers with semantic descriptions (embedded)
  • Dependencies between servers (edges)
  • Timeseries metrics in a separate table
  • Use semantic search to find servers
  • Use graph traversal to find dependencies
  • Use SQL to aggregate metrics
"""

import sys
sys.path.insert(0, '..')

from sqlite_kg import KnowledgeGraph
import json
import random
from datetime import datetime, timedelta

print("=" * 80)
print("Basic Example: Semantic Search + Hybrid Queries")
print("=" * 80)

# ============================================================================
# PART 1: Setup with Embeddings
# ============================================================================
print("""
[1/6] Creating Knowledge Graph with Embeddings...

Why embeddings?
  • Turn text into vectors (numbers)
  • Similar meanings = similar vectors
  • Find relevant data based on MEANING, not just keywords""")

# Create graph with auto-embedding enabled
kg = KnowledgeGraph(
    db_path="monitoring.db",
    embedding_model="all-MiniLM-L6-v2",  # Fast, small model
    embedding_dim=384,
    auto_embed=True
)

print("✓ Graph initialized with embedding model: all-MiniLM-L6-v2")

# ============================================================================
# PART 2: Insert Server Data
# ============================================================================
print("\n[2/6] Inserting Server Infrastructure...")

servers = [
    {
        "id": "web-1",
        "text": "Frontend web server handling HTTP requests, serves React application, nginx reverse proxy",
        "type": "web",
        "region": "us-east",
    },
    {
        "id": "web-2",
        "text": "Frontend web server for production traffic, load balanced, serves static assets",
        "type": "web",
        "region": "us-west",
    },
    {
        "id": "api-1",
        "text": "REST API server handling business logic, processes user requests, Node.js backend",
        "type": "api",
        "region": "us-east",
    },
    {
        "id": "db-1",
        "text": "Primary PostgreSQL database storing user data, transactions, and application state",
        "type": "database",
        "region": "us-east",
    },
    {
        "id": "cache-1",
        "text": "Redis cache for session storage and query result caching",
        "type": "cache",
        "region": "us-east",
    },
    {
        "id": "ml-1",
        "text": "Machine learning inference server running TensorFlow models for recommendations",
        "type": "ml",
        "region": "us-west",
    },
]

print("\nAdding servers with automatic embedding generation...")
for server in servers:
    # The auto_embed=True setting will automatically generate embeddings from 'text' field
    kg.add_entity(
        entity_id=server["id"],
        labels=["Server"],  # Add label for Cypher queries
        properties=server,
        embed_field="text"  # Use the 'text' field for embedding
    )
    print(f"  ✓ Added {server['id']:12} | {server['text'][:50]}...")

# Add dependencies (edges)
print("\nAdding dependencies...")
dependencies = [
    ("web-1", "api-1", "DEPENDS_ON"),
    ("web-2", "api-1", "DEPENDS_ON"),
    ("api-1", "db-1", "DEPENDS_ON"),
    ("api-1", "cache-1", "DEPENDS_ON"),
    ("api-1", "ml-1", "CALLS"),
]

for src, tgt, rel in dependencies:
    kg.add_relationship(src, tgt, rel)
    print(f"  ✓ {src:12} --[{rel}]--> {tgt}")

# ============================================================================
# PART 3: Create Timeseries Data
# ============================================================================
print("""
[3/6] Creating Timeseries Metrics Table...

Note: Timeseries data often lives in a separate table, not the graph.
      We'll use Cypher to find servers, then SQL to query their metrics.""")

# Create a traditional SQL table for metrics
kg.conn.execute("""
    CREATE TABLE IF NOT EXISTS metrics (
        server_id TEXT,
        timestamp INTEGER,
        cpu_percent REAL,
        memory_percent REAL,
        requests_per_sec INTEGER
    )
""")

# Generate sample metrics
print("\nGenerating sample metrics for last 24 hours...")
now = datetime.now()
for server in servers:
    for i in range(24):  # 24 hours of data
        timestamp = int((now - timedelta(hours=i)).timestamp())
        cpu = random.uniform(10, 90)
        memory = random.uniform(30, 80)
        requests = random.randint(100, 5000) if server["type"] in ["web", "api"] else 0

        kg.conn.execute(
            "INSERT INTO metrics VALUES (?, ?, ?, ?, ?)",
            (server["id"], timestamp, cpu, memory, requests)
        )

kg.conn.commit()
print(f"✓ Generated {len(servers) * 24} metric records")

# ============================================================================
# PART 4: Semantic Search
# ============================================================================
print("\n[4/6] Semantic Search - Finding Relevant Servers")
print("\n" + "-" * 80)
print("Scenario: LLM needs to answer 'What servers handle web traffic?'")
print("-" * 80)

query = "servers that handle HTTP web requests and user traffic"
print(f"\nQuery: '{query}'")
print("\nHow it works:")
print("  1. Convert query to embedding vector")
print("  2. Compare with all server embeddings using cosine similarity")
print("  3. Return top matches (most semantically similar)")

results = kg.search(query, top_k=3)

print("\nTop 3 most relevant servers:")
for i, result in enumerate(results, 1):
    props = result['properties']
    similarity = result['similarity']
    print(f"\n  {i}. {props['id']:12} (similarity: {similarity:.2%})")
    print(f"     {props['text']}")

print("\n💡 Key Point: We found relevant servers based on MEANING, not keywords!")
print("   The query didn't contain 'nginx' or 'React', but we still found web-1.")

# ============================================================================
# PART 5: Graph Traversal with Python API
# ============================================================================
print("\n[5/6] Graph Traversal - Finding Dependencies")
print("\n" + "-" * 80)
print("Scenario: Find all systems that web-1 depends on (directly or indirectly)")
print("-" * 80)

print("\nUsing Python API method: kg.traverse()")
print("  • Start from web-1")
print("  • Follow outgoing edges")
print("  • Max depth: 3 hops")

traversal_result = kg.traverse(
    start_id="web-1",
    direction="outgoing",
    max_depth=3
)

print(f"\nFound {len(traversal_result)} dependencies:")
for node in traversal_result:
    depth = node['depth']
    props = node['properties']
    indent = "  " + "  " * depth
    print(f"{indent}└─ [{depth} hop(s)] {props['id']:12} | {props.get('type', 'unknown')}")

print("\n💡 Key Point: Graph traversal naturally expresses 'what depends on what'")
print("   Much simpler than recursive SQL joins!")

# ============================================================================
# PART 6: Hybrid Query - Cypher + SQL
# ============================================================================
print("\n[6/6] Hybrid Query - Cypher for Graph, SQL for Aggregation")
print("\n" + "-" * 80)
print("Scenario: Find avg CPU usage of all web servers and their direct dependencies")
print("-" * 80)

print("\nStep 1: Use Cypher to find relevant servers (graph pattern)")
cypher_query = "MATCH (s:Server) RETURN s"
print(f"Cypher: {cypher_query}")
print("(Finding all Server nodes)")

# Use the cypher_query() method which extracts node IDs
node_ids = kg.cypher_query(cypher_query)

# Get server IDs from node properties
server_ids = []
for nid in node_ids:
    node = kg.get_entity(str(nid))
    if node and 'id' in node['properties']:
        server_ids.append(node['properties']['id'])

print(f"Found {len(server_ids)} servers: {sorted(server_ids)}")

print("\nStep 2: Use SQL to aggregate metrics for those servers")
if server_ids:
    placeholders = ','.join('?' * len(server_ids))
    sql_query = f"""
        SELECT
            server_id,
            AVG(cpu_percent) as avg_cpu,
            AVG(memory_percent) as avg_memory,
            AVG(requests_per_sec) as avg_requests
        FROM metrics
        WHERE server_id IN ({placeholders})
        GROUP BY server_id
        ORDER BY avg_cpu DESC
    """

    print(f"SQL: {sql_query}")

    results = kg.conn.execute(sql_query, list(server_ids)).fetchall()

    print("\nAggregated Metrics:")
    print(f"  {'Server':12} | {'Avg CPU':8} | {'Avg Memory':10} | {'Avg Req/sec':12}")
    print("  " + "-" * 60)
    for server_id, cpu, memory, requests in results:
        print(f"  {server_id:12} | {cpu:7.1f}% | {memory:9.1f}% | {requests:12.0f}")

print("\n💡 Key Point: Hybrid queries give you the best of both worlds!")
print("   • Cypher: Expressive graph patterns")
print("   • SQL: Powerful aggregations and analytics")

# ============================================================================
# Summary
# ============================================================================
print("\n" + "=" * 80)
print("Summary: What We Learned")
print("=" * 80)

print("""
1. Semantic Search
   • Embeddings convert text to vectors
   • Find relevant data by MEANING, not keywords
   • Critical for LLMs to avoid multiple round trips
   • kg.search(query, top_k=N) returns most similar entities

2. Graph Traversal
   • kg.traverse() follows relationships to any depth
   • Much simpler than recursive SQL for graph patterns
   • Perfect for: dependencies, social networks, org charts

3. Hybrid Queries (The Secret Sauce)
   • Cypher: Find entities using graph patterns
   • SQL: Aggregate/analyze those entities
   • Example: Cypher finds servers → SQL calculates metrics
   • Best practice for production systems

4. Real-World Architecture
   • Graph: Entities and relationships
   • Separate tables: Timeseries, logs, high-volume data
   • Combine them with hybrid queries""")

print("\n✅ You now understand semantic search and hybrid queries!")
print("=" * 80)

kg.close()
