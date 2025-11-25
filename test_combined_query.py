#!/usr/bin/env python3
"""Test the combined query from README"""

import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from chimeradb import KnowledgeGraph

# Create database with automatic embeddings (uses distilbert-base-uncased)
kg = KnowledgeGraph(":memory:")
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

# 5. COMBINED: Vector Search + Graph + SQL Analytics
print("\n=== Combined Query: Find similar people, deduplicate companies, get avg similarity ===")

query_emb = kg._encode_text("machine learning expert") if kg.model else kg.embedding_function("machine learning expert")
results = kg.query(f"""
    WITH similar_people AS (
        SELECT
            id,
            json_extract_string(properties, 'name') as name,
            array_cosine_distance(embedding, ?::FLOAT[{kg.embedding_dim}]) as distance
        FROM nodes
        WHERE labels LIKE '%Person%'
        ORDER BY distance
        LIMIT 5
    ),
    people_with_companies AS (
        SELECT DISTINCT
            sp.name as person,
            json_extract_string(n.properties, 'name') as company,
            sp.distance
        FROM similar_people sp
        JOIN edges e ON e.from_id = sp.id
        JOIN nodes n ON n.id = e.to_id
        WHERE e.edge_type = 'WORKS_AT'
    )
    SELECT
        company,
        COUNT(DISTINCT person) as expert_count,
        AVG(1.0 - distance/2.0) as avg_similarity
    FROM people_with_companies
    GROUP BY company
    ORDER BY avg_similarity DESC
""", [query_emb])

for company, count, similarity in results:
    print(f"  {company}: {count} ML experts (avg similarity: {similarity:.2f})")

kg.close()
print("\n✅ Combined query test passed!")
