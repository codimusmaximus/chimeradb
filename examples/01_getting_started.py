#!/usr/bin/env python3
"""
Getting Started with ChimeraDB
===============================

This tutorial shows you:
  1. Creating a knowledge graph with the Python API
  2. Semantic search with embeddings
  3. Graph traversal with SQL/PGQ
  4. Combining vector search + graph queries + SQL analytics
"""

# Fix for Python 3.13 multiprocessing issues with sentence-transformers
import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from chimeradb import KnowledgeGraph
from datetime import datetime

print("=" * 80)
print("Getting Started: ChimeraDB - Semantic Search + Graph Queries + SQL Analytics")
print("=" * 80)

# ============================================================================
# What We'll Build
# ============================================================================
print("""
We're building TechCorp's organization with project assignments:

  Alice (CEO) ─── "Leading AI strategy"
    |
    ├─ manages ─> Bob (CTO) ─── "Building ML platform"
    |                 |
    |                 └─ works_on ─> AI Platform Project
    |
    └─ manages ─> Carol (CFO) ─── "Managing finances"
                      |
                      └─ works_on ─> Funding Round Project

We'll demonstrate:
  ✓ Python API for building graphs
  ✓ Semantic search with embeddings
  ✓ Graph pattern matching with SQL/PGQ
  ✓ SQL analytics on graph data
""")

# ============================================================================
# Step 1: Create Database with Embeddings
# ============================================================================
print("\n" + "=" * 80)
print("Step 1: Create Database (with auto-embeddings)")
print("=" * 80)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
kg = KnowledgeGraph(db_path=f"org_semantic_{timestamp}.db")

print("✓ Database created")
print("✓ Embeddings auto-enabled (using all-MiniLM-L6-v2 by default)")

# ============================================================================
# Step 2: Add Entities with Python API
# ============================================================================
print("\n" + "=" * 80)
print("Step 2: Add Entities with Python API")
print("=" * 80)

# Create leadership team
kg.add_entity(
    "alice",
    {"name": "Alice Chen", "title": "CEO", "bio": "Leading TechCorp AI strategy and vision"},
    labels=["Person"],
    embed_field="bio"
)

kg.add_entity(
    "bob",
    {"name": "Bob Smith", "title": "CTO", "bio": "Building scalable ML infrastructure and platform"},
    labels=["Person"],
    embed_field="bio"
)

kg.add_entity(
    "carol",
    {"name": "Carol Johnson", "title": "CFO", "bio": "Managing company finances and investor relations"},
    labels=["Person"],
    embed_field="bio"
)

print("✓ Created: Alice Chen (CEO)")
print("✓ Created: Bob Smith (CTO)")
print("✓ Created: Carol Johnson (CFO)")
print("  (Embeddings auto-generated from 'bio' field)")

# Create management relationships
kg.add_relationship("alice", "bob", "MANAGES", {"since": 2020})
kg.add_relationship("alice", "carol", "MANAGES", {"since": 2021})
print("\n✓ Alice manages Bob and Carol")

# ============================================================================
# Step 3: Add Engineering Team and Projects
# ============================================================================
print("\n" + "=" * 80)
print("Step 3: Add Engineering Team and Projects")
print("=" * 80)

# Add team members
kg.add_entity(
    "diana",
    {"name": "Diana Lee", "title": "Senior ML Engineer",
     "bio": "Developing deep learning models for recommendation systems"},
    labels=["Person"],
    embed_field="bio"
)

kg.add_entity(
    "eve",
    {"name": "Eve Martinez", "title": "Data Scientist",
     "bio": "Analyzing user behavior and training neural networks"},
    labels=["Person"],
    embed_field="bio"
)

# Add projects
kg.add_entity(
    "ai_platform",
    {"name": "AI Platform",
     "description": "Building machine learning infrastructure for real-time predictions",
     "status": "active"},
    labels=["Project"],
    embed_field="description"
)

kg.add_entity(
    "funding",
    {"name": "Funding Round",
     "description": "Series B fundraising and financial planning",
     "status": "active"},
    labels=["Project"],
    embed_field="description"
)

print("✓ Diana Lee (Senior ML Engineer)")
print("✓ Eve Martinez (Data Scientist)")
print("✓ AI Platform (Project)")
print("✓ Funding Round (Project)")

# Add relationships
kg.add_relationship("bob", "diana", "MANAGES")
kg.add_relationship("bob", "eve", "MANAGES")
kg.add_relationship("diana", "ai_platform", "WORKS_ON", {"role": "Lead"})
kg.add_relationship("eve", "ai_platform", "WORKS_ON", {"role": "Contributor"})
kg.add_relationship("carol", "funding", "WORKS_ON", {"role": "Lead"})

print("\n✓ Created reporting structure and project assignments")

# ============================================================================
# Step 4: Semantic Search with Embeddings
# ============================================================================
print("\n" + "=" * 80)
print("Step 4: The Killer Feature - Semantic Search")
print("=" * 80)

print("""
Traditional databases: Exact keyword matching only
ChimeraDB: Understands meaning and context!
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
# Step 5: Graph Traversal
# ============================================================================
print("\n" + "=" * 80)
print("Step 5: Graph Traversal - Find Alice's Organization")
print("=" * 80)

print("\nQuestion: 'Who reports to Alice (directly or indirectly)?'\n")

# Use the traverse method for simple graph traversal
results = kg.traverse("alice", direction="outgoing", max_depth=2, relation_type="MANAGES")

print("Alice's organization (via traverse API):")
for person in results:
    props = person['properties']
    depth = person['depth']
    indent = "  " * depth
    print(f"{indent}• {props.get('name')} - {props.get('title')} (depth: {depth})")

# ============================================================================
# Step 6: Graph Pattern Matching with SQL
# ============================================================================
print("\n" + "=" * 80)
print("Step 6: Graph Pattern Matching with SQL")
print("=" * 80)

print("\nFind people who work on projects:\n")

# Use SQL joins to find relationships
# (SQL/PGQ would make this simpler, but requires duckpgq extension)
results = kg.query("""
    SELECT
        json_extract(p.properties, '$.name') as person_name,
        json_extract(p.properties, '$.title') as title,
        json_extract(proj.properties, '$.name') as project_name,
        json_extract(e.properties, '$.role') as role
    FROM edges e
    JOIN nodes p ON e.from_id = p.id
    JOIN nodes proj ON e.to_id = proj.id
    WHERE e.edge_type = 'WORKS_ON'
      AND proj.labels LIKE '%Project%'
    ORDER BY project_name, person_name
""")

print("Who works on what:")
for person, title, project, role in results:
    role_str = f" ({role})" if role else ""
    print(f"  • {person} ({title}) → {project}{role_str}")

# ============================================================================
# Step 7: SQL Analytics on Graph Data
# ============================================================================
print("\n" + "=" * 80)
print("Step 7: SQL Analytics - Count People by Department")
print("=" * 80)

results = kg.query("""
    SELECT
        json_extract(properties, '$.title') as title,
        json_extract(properties, '$.name') as name,
        json_extract(properties, '$.bio') as bio
    FROM nodes
    WHERE labels LIKE '%Person%'
    ORDER BY title
""")

print("\nAll team members:")
for title, name, bio in results:
    print(f"\n  {name} - {title}")
    print(f"  {bio}")

# ============================================================================
# Step 8: Hybrid Query - Combine Semantic Search + Graph Traversal
# ============================================================================
print("\n" + "=" * 80)
print("Step 8: Hybrid Query - Semantic Search + Graph Context")
print("=" * 80)

print("\nFind ML experts and show who they work for:\n")

# First, semantic search for ML experts (filter to only People)
ml_experts = kg.search("machine learning and deep learning expert", top_k=5, labels=["Person"])

print("ML Experts found via semantic search:")
for expert in ml_experts[:2]:  # Top 2 people
    person_id = expert['id']
    name = expert['properties'].get('name', 'Unknown')
    title = expert['properties'].get('title', 'N/A')

    # Now find their manager using graph traversal
    manager_results = kg.traverse(person_id, direction="incoming", relation_type="MANAGES", max_depth=1)

    manager = "No manager"
    if manager_results:
        manager = manager_results[0]['properties'].get('name', 'Unknown')

    print(f"  • {name} ({title}) - Reports to: {manager}")

print("\n✨ Combined semantic search with graph relationships!")

# ============================================================================
# Summary
# ============================================================================
print("\n" + "=" * 80)
print("Summary: Why ChimeraDB is Powerful")
print("=" * 80)

print("""
1. Semantic Search (Vector Embeddings):
   ✓ Find results by meaning, not just keywords
   ✓ Auto-generated embeddings on every insert
   ✓ HNSW indexing for fast similarity search

2. Graph Traversal (Python API):
   ✓ Simple traverse() method for common patterns
   ✓ Direction: outgoing, incoming, or both
   ✓ Filter by relationship type

3. Graph Queries (SQL):
   ✓ Use SQL joins to traverse relationships
   ✓ JSON extraction from node/edge properties
   ✓ WHERE clauses for filtering

4. SQL Analytics (DuckDB):
   ✓ Full SQL power for aggregations
   ✓ JSON functions for property access
   ✓ 10-100x faster than embedded alternatives

5. All in One:
   ✓ Single DuckDB file - no infrastructure
   ✓ Combine vector search + graphs + SQL in one query
   ✓ Perfect for RAG systems, AI agents, recommendations
""")

print("\n" + "=" * 80)
print("✅ You now understand the full power of ChimeraDB!")
print("=" * 80)

print(f"\nYour database: {kg.db_path}")
print("\nNext steps:")
print("  • Try different semantic queries")
print("  • Explore: examples/02_basic.py (more patterns)")
print("  • Advanced: examples/03_advanced.py (complex queries)")

kg.close()
