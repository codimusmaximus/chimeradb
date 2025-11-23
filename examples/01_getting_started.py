#!/usr/bin/env python3
"""
Getting Started with SQLite Knowledge Graph
============================================

What is a Knowledge Graph?
--------------------------
A knowledge graph stores information as:
- NODES (entities): People, places, things, concepts
- EDGES (relationships): How entities connect to each other
- PROPERTIES: Attributes on nodes and edges

Example: Alice MANAGES Bob, Bob WORKS_AT CompanyX
         ^node  ^edge   ^node  ^edge      ^node

Why Knowledge Graphs?
---------------------
1. Relationships are first-class citizens (not just foreign keys)
2. Flexible schema - add new node types and relationships anytime
3. Graph queries express "who knows who" much more naturally than SQL joins
4. Perfect for: social networks, recommendations, knowledge bases, org charts

This Tutorial Covers:
---------------------
1. Creating a graph database
2. Inserting data with SQL vs Python API
3. Querying with Cypher vs SQL
4. When to use each approach
"""

import sys
sys.path.insert(0, '..')

from sqlite_kg import KnowledgeGraph
import json

print("=" * 80)
print("Getting Started: Knowledge Graphs in SQLite")
print("=" * 80)

# ============================================================================
# PART 1: Setup
# ============================================================================
print("\n[1/5] Creating Knowledge Graph...")

# Create an in-memory graph database
kg = KnowledgeGraph(db_path="getting_started.db")

print("""✓ Knowledge graph initialized
  Behind the scenes:
    • Loaded sqlite-graph extension (Cypher support)
    • Loaded sqlite-vector extension (semantic search)
    • Created tables: graph_nodes, graph_edges""")

# ============================================================================
# PART 2: Inserting Data - Starting with Cypher
# ============================================================================
print("""
[2/5] Inserting Data - Method 1: Cypher CREATE

Why start with Cypher?
  • Automatic label handling
  • Initializes graph for hybrid SQL + Cypher workflow
  • Clean, declarative syntax""")

# Create first nodes with Cypher
print("\nCreating initial nodes with Cypher...")
kg.conn.execute("SELECT cypher_execute(?)", ("CREATE (p:Person {name: 'Alice', role: 'Engineering Manager', department: 'AI'})",))
kg.conn.execute("SELECT cypher_execute(?)", ("CREATE (p:Person {name: 'Bob', role: 'Senior Engineer', department: 'AI'})",))
kg.conn.commit()
print("  ✓ Created Alice and Bob with Cypher")

# Now add more nodes with SQL INSERT
print("\nAdding more nodes with SQL INSERT...")
print("(After Cypher CREATE, SQL inserts work with Cypher queries)")

people_sql = [
    (["Person"], {"name": "Carol", "role": "Data Scientist", "department": "Analytics"}),
]

for labels, props in people_sql:
    kg.conn.execute(
        "INSERT INTO graph_nodes (labels, properties) VALUES (?, ?)",
        (json.dumps(labels), json.dumps(props))
    )
    print(f"  ✓ Created {props['name']} with SQL (labels: {labels})")

kg.conn.commit()

# Insert edges using raw SQL
print("\nInserting edges (relationships)...")
# Alice (1) manages Bob (2), Bob (2) collaborates with Carol (3)
edges_sql = [
    (1, 2, "MANAGES", {"since": "2023"}),
    (2, 3, "COLLABORATES_WITH", {"projects": ["ML Pipeline", "Data Lake"]}),
]

for src, tgt, edge_type, props in edges_sql:
    kg.conn.execute(
        "INSERT INTO graph_edges (source, target, edge_type, properties) VALUES (?, ?, ?, ?)",
        (src, tgt, edge_type, json.dumps(props))
    )
    # Get names from database
    src_name = kg.conn.execute("SELECT json_extract(properties, '$.name') FROM graph_nodes WHERE id = ?", (src,)).fetchone()[0]
    tgt_name = kg.conn.execute("SELECT json_extract(properties, '$.name') FROM graph_nodes WHERE id = ?", (tgt,)).fetchone()[0]
    print(f"  ✓ Created edge: {src_name} --[{edge_type}]--> {tgt_name}")

kg.conn.commit()

# ============================================================================
# PART 3: Inserting Data with Python API
# ============================================================================
print("""
[3/5] Inserting Data - Method 2: Python API

Why use the Python API?
  • Cleaner code, less boilerplate
  • Automatic embedding generation (if configured)
  • Type safety and validation""")

# Add more nodes using Python API
print("\nInserting more nodes using API...")

kg.add_entity(
    entity_id="4",
    labels=["Person"],
    properties={"name": "Diana", "role": "Product Manager", "department": "Product"}
)
print("  ✓ Created node 4: Diana (with Person label)")

kg.add_entity(
    entity_id="5",
    labels=["Person"],
    properties={"name": "Eve", "role": "Designer", "department": "Design"}
)
print("  ✓ Created node 5: Eve (with Person label)")

# Or use Cypher CREATE (automatically handles labels!)
print("\n--- Alternative: Cypher CREATE ---")
print("Cypher CREATE handles labels automatically:")
print("  CREATE (p:Person {name: 'Frank', role: 'Analyst'})")

kg.conn.execute("SELECT cypher_execute(?)", ("CREATE (p:Person {name: 'Frank', role: 'Analyst'})",))
kg.conn.commit()
print("  ✓ Created Frank with Cypher (auto-labeled as Person)")

# Add more relationships using Python API
print("\nInserting more edges using API...")
kg.add_relationship("1", "4", "WORKS_WITH", {"projects": ["AI Platform"]})
print("  ✓ Created edge: Alice --[WORKS_WITH]--> Diana")

kg.add_relationship("4", "5", "COLLABORATES_WITH", {"frequency": "daily"})
print("  ✓ Created edge: Diana --[COLLABORATES_WITH]--> Eve")

# ============================================================================
# PART 4: Querying with Cypher
# ============================================================================
print("""
[4/5] Querying - Method 1: Cypher

What is Cypher?
  • Graph query language (like SQL but for graphs)
  • Uses ASCII-art patterns: (node)-[edge]->(node)
  • Great for: pattern matching, traversal, path finding""")

print("\n" + "-" * 80)
print("Query 1: Find all people by label")
print("-" * 80)

print("\nCypher: MATCH (p:Person) RETURN p")
print("(Using Python API: kg.cypher_query() returns node IDs)")

# Use the Python API to run Cypher queries
node_ids = kg.cypher_query('MATCH (p:Person) RETURN p')
print(f"\n✓ Found {len(node_ids)} people with Person label")
print(f"  Node IDs: {node_ids}")

# Use SQL to get properties
print("\nUsing SQL to extract properties:")
sql_results = kg.query("""
    SELECT
        json_extract(properties, '$.name'),
        json_extract(properties, '$.role'),
        json_extract(properties, '$.department')
    FROM graph_nodes
    WHERE labels LIKE '%Person%'
    ORDER BY json_extract(properties, '$.name')
""")
print("\nExtracted properties:")
for name, role, dept in sql_results:
    if name:  # Skip nodes without name
        print(f"  {name:10} | {role:20} | {dept or 'N/A'}")

print("\n" + "-" * 80)
print("Query 2: Find relationships")
print("-" * 80)

print("\nCypher: MATCH (a)-[r]->(b) RETURN a, r, b")
print("(Finds all relationships in the graph)")

# Cypher query returns node IDs involved in relationships
node_ids = kg.cypher_query('MATCH (a)-[r]->(b) RETURN a, r, b')
print(f"\n✓ Cypher matched {len(node_ids)} nodes involved in relationships")

# Use SQL to see relationship details
print("\nRelationship details via SQL:")
sql_results = kg.query("""
    SELECT
        json_extract(n1.properties, '$.name') as from_name,
        e.edge_type,
        json_extract(n2.properties, '$.name') as to_name
    FROM graph_edges e
    JOIN graph_nodes n1 ON e.source = n1.id
    JOIN graph_nodes n2 ON e.target = n2.id
    LIMIT 3
""")
for from_name, rel_type, to_name in sql_results:
    print(f"  {from_name} --[{rel_type}]--> {to_name}")

# ============================================================================
# PART 5: Querying with SQL
# ============================================================================
print("""
[5/5] Querying - Method 2: SQL

When to use SQL instead of Cypher?
  • Aggregations (COUNT, SUM, AVG, GROUP BY)
  • Joins with non-graph tables (e.g., timeseries data)
  • Complex analytics and reporting
  • When you need precise control over query execution""")

print("\n" + "-" * 80)
print("Query 3: Count relationships by type (Aggregation)")
print("-" * 80)

sql_query = """
    SELECT edge_type, COUNT(*) as count
    FROM graph_edges
    GROUP BY edge_type
    ORDER BY count DESC
"""
print(f"\nSQL:{sql_query}")

results = kg.query(sql_query)
print("Results:")
for edge_type, count in results:
    print(f"  {edge_type:25} | {count} connections")

print("\n" + "-" * 80)
print("Query 4: Find all people in AI department (Filtering)")
print("-" * 80)

sql_query = """
    SELECT
        json_extract(properties, '$.name') as name,
        json_extract(properties, '$.role') as role
    FROM graph_nodes
    WHERE json_extract(properties, '$.department') = 'AI'
"""
print(f"\nSQL:{sql_query}")

results = kg.query(sql_query)
print("\nResults (AI Department):")
for name, role in results:
    print(f"  {name:10} | {role}")

# ============================================================================
# Summary
# ============================================================================
print("\n" + "=" * 80)
print("Summary: When to Use What")
print("=" * 80)

print("""
📊 SQL vs Cypher vs Python API:

  Inserting Data:
    • SQL:        Bulk imports, must include labels column
                  INSERT INTO graph_nodes (id, labels, properties) VALUES ...
    • Python API: Clean code, pass labels=['Person']
                  kg.add_entity(id, labels=['Person'], properties={...})
    • Cypher:     Automatic label handling
                  CREATE (p:Person {name: "Alice"})

  Querying:
    • Cypher:     Pattern matching by label: MATCH (p:Person) RETURN p
                  Returns whole nodes (property access coming soon)
    • SQL:        Extract properties, aggregations, analytics
                  WHERE labels LIKE '%Person%'
    • Python API: Convenience methods: kg.search(), kg.traverse()

  🔑 Key Point: Labels are required for Cypher queries!
     Always include labels when creating nodes (SQL, Python API, or Cypher)""")

print("\n✅ You now understand knowledge graphs and how to use them!")
print("=" * 80)

kg.close()
