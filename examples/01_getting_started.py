#!/usr/bin/env python3
"""
Getting Started with SQLite Knowledge Graph
============================================

This tutorial shows you:
  1. Building a graph with Cypher (clean, declarative)
  2. Bulk loading with SQL (fast, efficient)
  3. Why Cypher shines for traversals (vs messy SQL)
  4. Semantic search with embeddings (the killer feature!)
"""

from chimeradb import KnowledgeGraph
from datetime import datetime
import json

print("=" * 80)
print("Getting Started: Knowledge Graphs with Semantic Search")
print("=" * 80)

# ============================================================================
# What We'll Build
# ============================================================================
print("""
We're building TechCorp's organization with project assignments:

  Alice (CEO) ─── "Leads AI strategy"
    |
    ├─ manages ─> Bob (CTO) ─── "Building ML platform"
    |                 |
    |                 └─ works_on ─> AI Platform Project
    |
    └─ manages ─> Carol (CFO) ─── "Manages company finances"
                      |
                      └─ works_on ─> Funding Round Project

  + More team members and projects...

We'll see:
  ✓ How to mix Cypher and SQL
  ✓ Why Cypher is better for traversals
  ✓ How semantic search finds "who works on machine learning?"
""")

# ============================================================================
# Step 1: Create Database with Embeddings
# ============================================================================
print("\n" + "=" * 80)
print("Step 1: Create Database (with embedding support)")
print("=" * 80)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
kg = KnowledgeGraph(db_path=f"org_semantic_{timestamp}.db")

print("✓ Database created")
print("✓ Embeddings auto-enabled (using all-MiniLM-L6-v2 by default)")

# ============================================================================
# Step 2: Create Core Leadership with Cypher
# ============================================================================
print("\n" + "=" * 80)
print("Step 2: Create Leadership Team with Cypher")
print("=" * 80)

print("\nWhy Cypher? Clean syntax for creating nodes + relationships together:\n")

cypher_commands = [
    # Create Alice
    """CREATE (alice:Person {
        name: 'Alice Chen',
        title: 'CEO',
        bio: 'Leading TechCorp AI strategy and vision',
        department: 'Executive'
    })""",

    # Create Bob
    """CREATE (bob:Person {
        name: 'Bob Smith',
        title: 'CTO',
        bio: 'Building scalable ML infrastructure and platform',
        department: 'Engineering'
    })""",

    # Create Carol
    """CREATE (carol:Person {
        name: 'Carol Johnson',
        title: 'CFO',
        bio: 'Managing company finances and investor relations',
        department: 'Finance'
    })""",
]

for cmd in cypher_commands:
    kg.cypher(cmd, auto_commit=False)

kg.commit()

print("✓ Created: Alice Chen (CEO)")
print("✓ Created: Bob Smith (CTO)")
print("✓ Created: Carol Johnson (CFO)")
print("  (Embeddings auto-generated from 'bio' field)")

# Create management relationships
kg.add_relationship("1", "2", "MANAGES", {"since": "2020"})
kg.add_relationship("1", "3", "MANAGES", {"since": "2021"})
print("\n✓ Alice manages Bob and Carol")

# ============================================================================
# Step 3: Bulk Load Engineering Team with SQL
# ============================================================================
print("\n" + "=" * 80)
print("Step 3: Bulk Load Engineering Team with SQL")
print("=" * 80)

print("\nWhy SQL? Efficient for bulk inserts from data files:\n")

# Simulate loading from a CSV or database
team_members = [
    {
        "labels": ["Person"],
        "props": {
            "name": "Diana Lee",
            "title": "Senior ML Engineer",
            "bio": "Developing deep learning models for recommendation systems",
            "department": "Engineering"
        }
    },
    {
        "labels": ["Person"],
        "props": {
            "name": "Eve Martinez",
            "title": "Data Scientist",
            "bio": "Analyzing user behavior and training neural networks",
            "department": "Engineering"
        }
    },
    {
        "labels": ["Project"],
        "props": {
            "name": "AI Platform",
            "description": "Building machine learning infrastructure for real-time predictions",
            "status": "active"
        }
    },
    {
        "labels": ["Project"],
        "props": {
            "name": "Funding Round",
            "description": "Series B fundraising and financial planning",
            "status": "active"
        }
    },
]

print("Inserting 4 entities with SQL INSERT:")
for item in team_members:
    kg.execute(
        "INSERT INTO graph_nodes (labels, properties) VALUES (?, ?)",
        (json.dumps(item["labels"]), json.dumps(item["props"]))
    )
    entity_type = item["labels"][0]
    name = item["props"].get("name", "Unknown")
    print(f"  ✓ {name} ({entity_type})")

kg.commit()
print("  (Embeddings auto-generated for all entities)")

# Add relationships (Bob manages Diana and Eve, they work on projects)
relationships = [
    (2, 4, "MANAGES", {}),  # Bob -> Diana
    (2, 5, "MANAGES", {}),  # Bob -> Eve
    (4, 6, "WORKS_ON", {"role": "Lead"}),  # Diana -> AI Platform
    (5, 6, "WORKS_ON", {"role": "Contributor"}),  # Eve -> AI Platform
    (3, 7, "WORKS_ON", {"role": "Lead"}),  # Carol -> Funding Round
]

for src, tgt, rel_type, props in relationships:
    kg.conn.execute(
        "INSERT INTO graph_edges (source, target, edge_type, properties) VALUES (?, ?, ?, ?)",
        (src, tgt, rel_type, json.dumps(props))
    )

kg.conn.commit()
print("\n✓ Created reporting structure and project assignments")

# ============================================================================
# Step 4: Query Comparison - Cypher vs SQL
# ============================================================================
print("\n" + "=" * 80)
print("Step 4: The Power of Cypher - Traversal Queries")
print("=" * 80)

print("\nQuestion: 'Who reports to Alice (directly or indirectly)?'\n")

print("=" * 40)
print("Cypher (Clean & Readable):")
print("=" * 40)
print("""
MATCH (alice:Person {name: 'Alice Chen'})
      -[:MANAGES*1..2]->(report:Person)
RETURN report
""")

print("\nThis finds everyone 1-2 hops away through MANAGES relationships.")
print("Simple, declarative, and easy to understand!")

print("\n" + "=" * 40)
print("SQL (Messy & Complex):")
print("=" * 40)
print("""
WITH RECURSIVE reporting_chain AS (
  -- Anchor: Direct reports
  SELECT n2.id, n2.properties, 1 as level
  FROM graph_edges e
  JOIN graph_nodes n1 ON e.source = n1.id
  JOIN graph_nodes n2 ON e.target = n2.id
  WHERE json_extract(n1.properties, '$.name') = 'Alice Chen'
    AND e.edge_type = 'MANAGES'

  UNION ALL

  -- Recursive: Reports of reports
  SELECT n2.id, n2.properties, rc.level + 1
  FROM reporting_chain rc
  JOIN graph_edges e ON e.source = rc.id
  JOIN graph_nodes n2 ON e.target = n2.id
  WHERE e.edge_type = 'MANAGES'
    AND rc.level < 2
)
SELECT DISTINCT json_extract(properties, '$.name')
FROM reporting_chain;
""")

print("\nSame query, but verbose and error-prone!")
print("This is why graph databases exist! 🎯")

# Let's actually run the SQL version to show it works
print("\n" + "-" * 80)
print("Running the complex SQL query:")
print("-" * 80)

results = kg.query("""
WITH RECURSIVE reporting_chain AS (
  SELECT n2.id, n2.properties, 1 as level
  FROM graph_edges e
  JOIN graph_nodes n1 ON e.source = n1.id
  JOIN graph_nodes n2 ON e.target = n2.id
  WHERE json_extract(n1.properties, '$.name') = 'Alice Chen'
    AND e.edge_type = 'MANAGES'

  UNION ALL

  SELECT n2.id, n2.properties, rc.level + 1
  FROM reporting_chain rc
  JOIN graph_edges e ON e.source = rc.id
  JOIN graph_nodes n2 ON e.target = n2.id
  WHERE e.edge_type = 'MANAGES'
    AND rc.level < 2
)
SELECT DISTINCT json_extract(properties, '$.name'), json_extract(properties, '$.title')
FROM reporting_chain
ORDER BY json_extract(properties, '$.name')
""")

print("\nAlice's organization (direct + indirect reports):")
for name, title in results:
    print(f"  • {name} - {title}")

# ============================================================================
# Step 5: Semantic Search with Embeddings
# ============================================================================
print("\n" + "=" * 80)
print("Step 5: The Killer Feature - Semantic Search")
print("=" * 80)

print("""
Traditional databases: Exact keyword matching only
Knowledge graphs + embeddings: Understand meaning and context!
""")

print("\n" + "-" * 80)
print("Query: 'Who works on machine learning?'")
print("-" * 80)
print("\nNote: Nobody's bio contains exactly 'machine learning'!")

# Search using semantic similarity
results = kg.search(
    query="Who works on machine learning and AI infrastructure?",
    top_k=3
)

print("\nSemantic search results (ranked by relevance):")
for i, result in enumerate(results, 1):
    props = result['properties']
    similarity = result['similarity']
    name = props.get('name', 'Unknown')
    bio = props.get('bio', props.get('description', 'N/A'))

    print(f"\n{i}. {name} (similarity: {similarity:.3f})")
    print(f"   Bio: {bio}")

print("\n✨ The embeddings found relevant people even without exact keywords!")

# ============================================================================
# Another Semantic Search Example
# ============================================================================
print("\n" + "-" * 80)
print("Query: 'Who handles money and investments?'")
print("-" * 80)

results = kg.search(
    query="Who handles money and investments?",
    top_k=2
)

print("\nSemantic search results:")
for i, result in enumerate(results, 1):
    props = result['properties']
    similarity = result['similarity']
    name = props.get('name', 'Unknown')
    title = props.get('title', 'N/A')

    print(f"{i}. {name} ({title}) - similarity: {similarity:.3f}")

print("\n✨ Found Carol and the Funding project without exact keyword matches!")

# ============================================================================
# Summary
# ============================================================================
print("\n" + "=" * 80)
print("Summary: Why This Stack is Powerful")
print("=" * 80)

print("""
1. Cypher for Graph Operations:
   ✓ Clean syntax for creating connected data
   ✓ Pattern matching (MATCH) beats complex SQL
   ✓ Traversals are simple: -[:MANAGES*1..2]->

2. SQL for Bulk Operations:
   ✓ Efficient bulk inserts from files
   ✓ Analytics and aggregations when needed
   ✓ Fallback for complex custom queries

3. Embeddings for Intelligence (Auto-Enabled!):
   ✓ Semantic search: meaning, not just keywords
   ✓ Automatic on every insert - no configuration needed
   ✓ Context-aware: understands synonyms and concepts
   ✓ Just use: kg = KnowledgeGraph("my.db")

4. Mix and Match:
   ✓ Use the right tool for each job
   ✓ Cypher + SQL + Embeddings = Complete solution
   ✓ All in SQLite = Simple deployment, no infrastructure
""")

print("\n" + "=" * 80)
print("✅ You now understand the full power of this stack!")
print("=" * 80)

print(f"\nYour database: {kg.db_path}")
print("\nNext steps:")
print("  • Try different semantic queries")
print("  • Explore: examples/02_basic.py (more Cypher patterns)")
print("  • Advanced: examples/03_advanced.py (graph algorithms)")

kg.close()
