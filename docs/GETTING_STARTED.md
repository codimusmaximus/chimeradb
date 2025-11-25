# Getting Started with ChimeraDB

Complete guide to installing and using ChimeraDB - the database that combines vector embeddings, property graphs, and SQL analytics in one DuckDB file.

## Quick Install

```bash
pip install chimeradb
```

That's it! ChimeraDB automatically installs:
- DuckDB 1.1.3+
- DuckDB extensions (duckpgq for graphs, vss for vector search)
- Transformers + PyTorch for embeddings

## Quick Start

```python
from chimeradb import KnowledgeGraph

# Create database with auto-embeddings
kg = KnowledgeGraph("my.db")

# Add entities with embeddings
kg.add_entity("alice", {"name": "Alice", "bio": "ML engineer"}, ["Person"], embed_field="bio")
kg.add_entity("bob", {"name": "Bob", "bio": "AI researcher"}, ["Person"], embed_field="bio")
kg.add_entity("acme", {"name": "Acme AI"}, ["Company"])

# Add relationships
kg.add_relationship("alice", "acme", "WORKS_AT")
kg.add_relationship("bob", "acme", "WORKS_AT")

# 1. Semantic search
results = kg.search("machine learning expert", top_k=2)
for r in results:
    print(f"{r['properties']['name']}: {r['similarity']:.2f}")

# 2. Graph traversal
employees = kg.traverse("acme", direction="incoming", relation_type="WORKS_AT")
print(f"Acme has {len(employees)} employees")

# 3. SQL/PGQ graph queries
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

# 4. Combined: Vector + Graph + SQL in ONE query
query_emb = kg._encode_text("AI expert")
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
    WHERE similarity > 0.5
    GROUP BY company_name
    HAVING COUNT(*) >= 2
""")

kg.close()
```

## Running the Examples

### Example 1: Getting Started

```bash
python examples/01_getting_started.py
```

Demonstrates basic operations with the Python API.

### Example 2: Real-World Workflow

```bash
python examples/02_basic.py
```

Shows the full workflow: semantic search → graph traversal → SQL analytics on a supply chain dataset.

### Example 3: Research Papers

```bash
python examples/03_advanced.py
```

Graph analysis on research papers with citations.

### Example 4: Industrial IoT (Recommended!)

```bash
python examples/04_industrial_iot.py
```

Production-ready example showing how to:
- Store metadata (embedded) separately from timeseries data (not embedded)
- Join knowledge graph with timeseries using SQL
- Demonstrates the full LLM reasoning workflow

## Development Setup (From Source)

```bash
git clone https://github.com/codimusmaximus/chimeradb.git
cd chimeradb
pip install -e .
```

## Key Concepts

### 1. Auto-Embeddings

By default, embeddings are automatically generated using `distilbert-base-uncased`:

```python
kg = KnowledgeGraph("my.db")  # Auto-embeddings enabled

# Specify which field(s) to embed
kg.add_entity("doc1", {
    "title": "Machine Learning",
    "content": "A guide to ML",
    "author": "Alice"
}, embed_field="content")  # Only embed 'content'

# Or embed multiple fields
kg.add_entity("doc2", {
    "title": "Deep Learning",
    "content": "Neural networks guide"
}, embed_field=["title", "content"])  # Concatenate both

# Or use default (concatenate all string fields)
kg.add_entity("doc3", {
    "title": "NLP",
    "content": "Text processing"
})  # Embeds: "Text processing NLP" (sorted alphabetically)
```

### 2. Disable Embeddings

For pure graph/SQL use cases without semantic search:

```python
kg = KnowledgeGraph("my.db", embedding_model=None)
```

### 3. Custom Embedding Function

```python
def my_embedder(text: str) -> List[float]:
    # Your custom embedding logic
    return openai.embeddings.create(input=text, model="text-embedding-3-small")

kg = KnowledgeGraph("my.db", embedding_function=my_embedder)
```

### 4. SQL/PGQ Graph Queries

ChimeraDB uses SQL/PGQ (SQL:2023 standard) for graph pattern matching:

```python
# Find all people working at companies
results = kg.query("""
    SELECT person_name, company_name
    FROM GRAPH_TABLE (knowledge_graph
        MATCH (person:nodes)-[e:edges]->(company:nodes)
        WHERE e.edge_type = 'WORKS_AT'
          AND company.labels LIKE '%Company%'
        COLUMNS (
            json_extract_string(person.properties, 'name') as person_name,
            json_extract_string(company.properties, 'name') as company_name
        )
    )
""")
```

See [DuckPGQ documentation](https://duckpgq.org/documentation/sql_pgq/) for full SQL/PGQ syntax.

### 5. Vector Similarity Search

```python
# Search by meaning (cosine similarity)
results = kg.search("artificial intelligence researcher", top_k=10)

# Filter by labels
results = kg.search("AI expert", top_k=10, labels=["Person"])

# Access results
for r in results:
    print(f"ID: {r['id']}")
    print(f"Similarity: {r['similarity']}")  # 0.0-1.0
    print(f"Properties: {r['properties']}")
```

### 6. Distance Metrics

```python
# Cosine distance (default, best for most use cases)
kg = KnowledgeGraph("my.db", distance_metric="cosine")

# L2 squared distance
kg = KnowledgeGraph("my.db", distance_metric="l2sq")

# Inner product
kg = KnowledgeGraph("my.db", distance_metric="ip")
```

## Troubleshooting

### Issue: `ModuleNotFoundError: No module named 'transformers'`

**Solution:** Install transformers and torch:
```bash
pip install transformers torch
```

### Issue: `RuntimeError: Failed to load duckpgq extension`

**Solution:** This usually means DuckDB version incompatibility. ChimeraDB requires DuckDB 1.1.3+:
```bash
pip install "duckdb>=1.1.3,<1.2.0"
```

### Issue: Embeddings taking too long

**Solution:** Use a smaller/faster model:
```python
kg = KnowledgeGraph(
    "my.db",
    embedding_model="distilbert-base-uncased"  # Faster than larger models
)
```

Or disable embeddings if you don't need semantic search:
```python
kg = KnowledgeGraph("my.db", embedding_model=None)
```

## Documentation

- **[README.md](../README.md)** - Overview and features
- **[SQL/PGQ Guide](https://duckpgq.org/documentation/sql_pgq/)** - Graph query syntax
- **[DuckDB VSS Extension](https://duckdb.org/2024/05/03/vector-similarity-search-vss)** - Vector similarity search
- **[Examples](../examples/)** - Working code examples

## Support

- 🐛 **Issues:** [GitHub Issues](https://github.com/codimusmaximus/chimeradb/issues)
- 📖 **Examples:** [examples/](../examples/) directory
- 💬 **Questions:** GitHub Discussions

---

**You're all set!** 🎉

Try the examples: `python examples/01_getting_started.py`
