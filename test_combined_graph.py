#!/usr/bin/env python3
"""Test the combined graph query from README"""

import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from chimeradb import KnowledgeGraph

# Create database with automatic embeddings
kg = KnowledgeGraph(":memory:")
print("✓ Database created")

# Add entities
kg.add_entity("alice", {"name": "Alice", "bio": "ML engineer building LLM agents"}, ["Person"], embed_field="bio")
kg.add_entity("bob", {"name": "Bob", "bio": "AI researcher focused on NLP"}, ["Person"], embed_field="bio")
kg.add_entity("carol", {"name": "Carol", "bio": "Data scientist specializing in deep learning"}, ["Person"], embed_field="bio")
kg.add_entity("acme", {"name": "Acme AI"}, ["Company"])
kg.add_entity("techcorp", {"name": "TechCorp Industries"}, ["Company"])
print("✓ Added 3 people and 2 companies")

# Add relationships
kg.add_relationship("alice", "acme", "WORKS_AT")
kg.add_relationship("bob", "acme", "WORKS_AT")
kg.add_relationship("carol", "techcorp", "WORKS_AT")
kg.add_relationship("acme", "techcorp", "PARTNERED_WITH")
print("✓ Added relationships")

print("\n=== Combined: Vector search + GRAPH_TABLE pattern matching + SQL aggregation ===")

# First, get similar people using vector search
query_emb = kg._encode_text("artificial intelligence researcher")
similar_people = kg.query(f"""
    SELECT id, array_cosine_distance(embedding, ?::FLOAT[{kg.embedding_dim}]) as distance
    FROM nodes
    WHERE labels LIKE '%Person%' AND embedding IS NOT NULL
    ORDER BY distance LIMIT 10
""", [query_emb])

print(f"  Found {len(similar_people)} similar people")
similar_ids = [p[0] for p in similar_people]
ids_str = "','".join(similar_ids)

# Now use SQL/PGQ MATCH to find company networks through graph pattern matching
results = kg.query(f"""
    SELECT
        json_extract_string(company.properties, 'name') as company_name,
        COUNT(DISTINCT person.id) as expert_count,
        CAST(path_length AS INTEGER) as hops
    FROM GRAPH_TABLE (knowledge_graph
        MATCH (person:nodes)-[e1:edges]->(company:nodes)-[e2:edges {{0,1}}]->(partner:nodes)
        WHERE person.id IN ('{ids_str}')
          AND e1.edge_type = 'WORKS_AT'
          AND (e2.edge_type = 'PARTNERED_WITH' OR e2.edge_type IS NULL)
        COLUMNS (
            person.id,
            company.id,
            company.properties,
            PATH_LENGTH(person, company, partner) as path_length
        )
    )
    GROUP BY company_name, hops
    ORDER BY expert_count DESC, hops ASC
""")

for company, count, hops in results:
    hop_text = "direct" if hops == 1 else f"{hops}-hop"
    print(f"  {company}: {count} AI experts ({hop_text})")

kg.close()
print("\n✅ Combined graph query test passed!")
