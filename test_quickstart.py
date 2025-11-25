#!/usr/bin/env python3
"""Test the Quick Start example from README"""

import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from chimeradb import KnowledgeGraph

# Create database with automatic embeddings (uses distilbert-base-uncased)
kg = KnowledgeGraph("quickstart_test.db")
print("✓ Database created with auto-embeddings enabled")

# Add entities - embeddings automatically generated from 'bio' field
kg.add_entity("alice", {"name": "Alice", "bio": "ML engineer building LLM agents"}, ["Person"], embed_field="bio")
kg.add_entity("bob", {"name": "Bob", "bio": "AI researcher focused on NLP"}, ["Person"], embed_field="bio")
kg.add_entity("acme", {"name": "Acme AI"}, ["Company"])
print("✓ Added 2 people and 1 company")

# Add relationships
kg.add_relationship("alice", "acme", "WORKS_AT")
kg.add_relationship("bob", "acme", "WORKS_AT")
print("✓ Added employment relationships")

# 1. Semantic Search - Find by MEANING, not exact keywords
print("\n=== Semantic Search ===")
results = kg.search("who works on language models?", top_k=2)
for r in results:
    name = r['properties']['name']
    bio = r['properties'].get('bio', 'N/A')
    similarity = r['similarity']
    print(f"  {name}: {bio} (similarity: {similarity:.2f})")

# 2. Graph Traversal - Follow relationships
print("\n=== Graph Traversal ===")
employees = kg.traverse("acme", direction="incoming", relation_type="WORKS_AT")
print(f"  Acme has {len(employees)} employees:")
for emp in employees:
    print(f"    - {emp['properties']['name']}")

# 3. SQL/PGQ - Graph pattern matching (SQL:2023 standard)
print("\n=== SQL/PGQ Pattern Matching ===")
results = kg.query("""
    SELECT *
    FROM GRAPH_TABLE (knowledge_graph
        MATCH (p:nodes)-[e:edges]->(c:nodes)
        WHERE c.id = 'acme'
        COLUMNS (
            json_extract_string(p.properties, 'name') as person,
            e.edge_type
        )
    )
""")
for person, edge_type in results:
    print(f"  {person} --[{edge_type}]--> Acme AI")

# 4. SQL Analytics - Aggregate data
print("\n=== SQL Analytics ===")
stats = kg.query("""
    SELECT
        json_extract_string(n.properties, 'name') as company,
        COUNT(*) as employee_count
    FROM nodes n
    JOIN edges e ON e.to_id = n.id
    WHERE n.labels LIKE '%Company%'
    GROUP BY company
""")
for company, count in stats:
    print(f"  {company}: {count} employees")

kg.close()
print("\n✅ Quick Start example completed successfully!")
