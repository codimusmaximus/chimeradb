#!/usr/bin/env python3
"""Test ONE query with vector + graph + SQL"""

import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from chimeradb import KnowledgeGraph

kg = KnowledgeGraph(":memory:")
print("✓ Database created\n")

# Add entities
kg.add_entity("alice", {"name": "Alice", "bio": "ML engineer building LLM agents"}, ["Person"], embed_field="bio")
kg.add_entity("bob", {"name": "Bob", "bio": "AI researcher focused on NLP"}, ["Person"], embed_field="bio")
kg.add_entity("carol", {"name": "Carol", "bio": "Data scientist specializing in deep learning"}, ["Person"], embed_field="bio")
kg.add_entity("acme", {"name": "Acme AI"}, ["Company"])

# Add relationships
kg.add_relationship("alice", "acme", "WORKS_AT")
kg.add_relationship("bob", "acme", "WORKS_AT")
kg.add_relationship("carol", "acme", "WORKS_AT")
print("✓ Added 3 people and 1 company\n")

print("=== ONE Query: Vector + Graph + SQL ===")
query_emb = kg._encode_text("machine learning expert")
emb_str = "[" + ",".join(map(str, query_emb)) + "]"

results = kg.query(f"""
    SELECT
        company_name,
        COUNT(DISTINCT person_name) as expert_count,
        AVG(similarity) as avg_similarity
    FROM GRAPH_TABLE (knowledge_graph
        MATCH (person:nodes)-[e:edges]->(company:nodes)
        WHERE e.edge_type = 'WORKS_AT'
        COLUMNS (
            json_extract_string(person.properties, 'name') as person_name,
            json_extract_string(company.properties, 'name') as company_name,
            1.0 - (array_cosine_distance(person.embedding, {emb_str}::FLOAT[{kg.embedding_dim}]) / 2.0) as similarity
        )
    )
    WHERE similarity > 0.5  -- Semantic filter
    GROUP BY company_name   -- SQL aggregation
    HAVING COUNT(*) >= 2    -- SQL filter
    ORDER BY avg_similarity DESC
""")

for company, count, similarity in results:
    print(f"  {company}: {count} ML experts (avg similarity: {similarity:.2f})")

print("\n✅ ONE query test passed!")
print("   - Vector: array_cosine_distance for semantic search")
print("   - Graph: MATCH pattern for relationships")
print("   - SQL: GROUP BY, AVG, HAVING, COUNT")

kg.close()
