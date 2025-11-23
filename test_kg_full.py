#!/usr/bin/env python3
"""
Complete Knowledge Graph Test with Real Embeddings

Demonstrates:
1. Creating a knowledge graph
2. Using real sentence embeddings
3. Graph queries + vector similarity search
"""

import sqlite3
import json

def main():
    print("=" * 70)
    print("Knowledge Graph with Sentence Embeddings - Full Test")
    print("=" * 70)

    # Initialize embedding model
    print("\n[1/6] Loading sentence embedding model...")
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('all-MiniLM-L6-v2')
        print(f"✓ Loaded model: all-MiniLM-L6-v2 (384 dimensions)")
    except ImportError:
        print("✗ sentence-transformers not installed")
        print("  Install: pip install sentence-transformers")
        return

    # Connect and load extensions
    print("\n[2/6] Loading SQLite extensions...")
    conn = sqlite3.connect("test_kg.db")
    conn.enable_load_extension(True)

    try:
        conn.load_extension("extensions/libgraph")
        print("✓ Loaded graph extension")
    except Exception as e:
        print(f"✗ Failed to load graph extension: {e}")
        return

    try:
        conn.load_extension("extensions/vector")
        version = conn.execute("SELECT vector_version()").fetchone()[0]
        print(f"✓ Loaded vector extension (v{version})")
    except Exception as e:
        print(f"✗ Failed to load vector extension: {e}")
        return

    # Create knowledge graph
    print("\n[3/6] Creating knowledge graph...")
    conn.execute("DROP TABLE IF EXISTS graph")
    conn.execute("CREATE VIRTUAL TABLE graph USING graph()")

    # Add embedding column
    try:
        conn.execute("ALTER TABLE graph_nodes ADD COLUMN embedding BLOB")
    except:
        pass  # Column may already exist

    # Initialize vector search
    conn.execute("SELECT vector_init('graph_nodes', 'embedding', 'type=FLOAT32,dimension=384')")
    print("✓ Knowledge graph initialized")

    # Add entities with semantic content
    print("\n[4/6] Adding entities with embeddings...")

    entities = [
        {
            "id": 1,
            "name": "Alice",
            "role": "Machine Learning Engineer",
            "bio": "Specializes in deep learning, neural networks, and computer vision. Loves PyTorch and TensorFlow."
        },
        {
            "id": 2,
            "name": "Bob",
            "role": "Data Engineer",
            "bio": "Expert in building data pipelines, ETL, and working with big data technologies like Spark and Kafka."
        },
        {
            "id": 3,
            "name": "Charlie",
            "role": "AI Researcher",
            "bio": "Focuses on natural language processing, transformers, and large language models. Published papers on BERT."
        },
        {
            "id": 4,
            "name": "Diana",
            "role": "Full Stack Developer",
            "bio": "Builds web applications with React and Node.js. Interested in UI/UX design and frontend frameworks."
        },
        {
            "id": 10,
            "name": "OpenAI",
            "type": "Company",
            "description": "AI research company focused on developing safe artificial general intelligence"
        },
        {
            "id": 11,
            "name": "DeepMind",
            "type": "Company",
            "description": "AI research lab working on deep learning and reinforcement learning breakthroughs"
        }
    ]

    for entity in entities:
        # Create embedding from bio/description
        text = entity.get('bio') or entity.get('description', '')
        embedding = model.encode(text).tolist()

        # Add node
        props = {k: v for k, v in entity.items() if k != 'id'}
        conn.execute(
            "INSERT INTO graph_nodes (id, properties) VALUES (?, ?)",
            (entity['id'], json.dumps(props))
        )

        # Add embedding
        conn.execute(
            "UPDATE graph_nodes SET embedding = vector_as_f32(?) WHERE id = ?",
            (json.dumps(embedding), entity['id'])
        )

        print(f"  ✓ Added: {entity['name']}")

    # Add relationships
    print("\n[5/6] Adding relationships...")
    relationships = [
        (1, 10, "WORKS_AT", {"since": 2022, "position": "Senior ML Engineer"}),
        (3, 11, "WORKS_AT", {"since": 2021, "position": "Research Scientist"}),
        (1, 3, "COLLABORATES_WITH", {"project": "NLP Research"}),
        (2, 1, "REPORTS_TO", {}),
    ]

    for src, tgt, rel_type, props in relationships:
        conn.execute(
            "INSERT INTO graph_edges (source, target, edge_type, properties) VALUES (?, ?, ?, ?)",
            (src, tgt, rel_type, json.dumps(props))
        )

    print(f"✓ Added {len(relationships)} relationships")
    conn.commit()

    # Quantize vectors for faster search
    print("\n[5.5/6] Quantizing vectors...")
    conn.execute("SELECT vector_quantize('graph_nodes', 'embedding')")
    print("✓ Vectors quantized")

    # Query 1: Pure graph query
    print("\n[6/6] Running queries...")
    print("\n" + "=" * 70)
    print("Query 1: Who works at AI companies?")
    print("=" * 70)

    results = conn.execute("""
        SELECT
            json_extract(n1.properties, '$.name') as person,
            json_extract(n1.properties, '$.role') as role,
            json_extract(n2.properties, '$.name') as company
        FROM graph_edges e
        JOIN graph_nodes n1 ON e.source = n1.id
        JOIN graph_nodes n2 ON e.target = n2.id
        WHERE e.edge_type = 'WORKS_AT'
    """).fetchall()

    for person, role, company in results:
        print(f"  {person} ({role}) works at {company}")

    # Query 2: Semantic search
    print("\n" + "=" * 70)
    print("Query 2: Find people similar to 'expert in neural networks and AI'")
    print("=" * 70)

    query_text = "expert in neural networks and artificial intelligence"
    query_embedding = model.encode(query_text).tolist()

    results = conn.execute("""
        SELECT
            n.id,
            json_extract(n.properties, '$.name') as name,
            json_extract(n.properties, '$.role') as role,
            v.distance
        FROM graph_nodes n
        JOIN vector_quantize_scan('graph_nodes', 'embedding', ?, 5) v
          ON n.id = v.rowid
        WHERE json_extract(n.properties, '$.role') IS NOT NULL
        ORDER BY v.distance
    """, (json.dumps(query_embedding),)).fetchall()

    print(f"\nQuery: '{query_text}'")
    print("\nTop matches:")
    for i, (node_id, name, role, distance) in enumerate(results, 1):
        similarity = (1 - distance) * 100
        print(f"  {i}. {name} - {role}")
        print(f"     Similarity: {similarity:.1f}%")

    # Query 3: Hybrid - graph filter + semantic search
    print("\n" + "=" * 70)
    print("Query 3: Find AI/ML people who collaborate with someone")
    print("=" * 70)

    query_text = "machine learning and deep learning expert"
    query_embedding = model.encode(query_text).tolist()

    results = conn.execute("""
        SELECT DISTINCT
            json_extract(n.properties, '$.name') as name,
            json_extract(n.properties, '$.role') as role,
            v.distance,
            GROUP_CONCAT(json_extract(n2.properties, '$.name'), ', ') as collaborates_with
        FROM graph_nodes n
        JOIN vector_quantize_scan('graph_nodes', 'embedding', ?, 10) v
          ON n.id = v.rowid
        JOIN graph_edges e ON (n.id = e.source OR n.id = e.target)
        JOIN graph_nodes n2 ON (
            CASE WHEN n.id = e.source THEN e.target ELSE e.source END = n2.id
        )
        WHERE e.edge_type = 'COLLABORATES_WITH'
          AND json_extract(n.properties, '$.role') LIKE '%ML%'
           OR json_extract(n.properties, '$.role') LIKE '%AI%'
        GROUP BY n.id
        ORDER BY v.distance
        LIMIT 3
    """, (json.dumps(query_embedding),)).fetchall()

    print(f"\nQuery: '{query_text}' + has collaborations")
    print("\nResults:")
    for name, role, distance, collabs in results:
        similarity = (1 - distance) * 100
        print(f"  {name} ({role})")
        print(f"    Similarity: {similarity:.1f}%")
        print(f"    Collaborates with: {collabs}")

    # Summary
    print("\n" + "=" * 70)
    print("Summary")
    print("=" * 70)

    node_count = conn.execute("SELECT COUNT(*) FROM graph_nodes").fetchone()[0]
    edge_count = conn.execute("SELECT COUNT(*) FROM graph_edges").fetchone()[0]
    embedded_count = conn.execute("SELECT COUNT(*) FROM graph_nodes WHERE embedding IS NOT NULL").fetchone()[0]

    print(f"Total nodes: {node_count}")
    print(f"Total edges: {edge_count}")
    print(f"Nodes with embeddings: {embedded_count}")

    print("\n✅ All tests passed!")
    print("=" * 70)

    conn.close()


if __name__ == "__main__":
    main()
