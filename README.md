# ChimeraDB

**Semantic search + graph queries + SQL analytics. All in one SQLite file.**

The only database that combines vector embeddings, Cypher graph patterns, and full SQL for LLM apps. No separate vector DB, no separate graph DB, no infrastructure.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

[Examples](examples/) • [Docs](docs/)

---

## Quick Start

```bash
pip install chimeradb
```

```python
from chimeradb import KnowledgeGraph

kg = KnowledgeGraph("my.db")  # Auto-embeddings enabled

# 1. Vector embeddings - semantic search
kg.cypher("CREATE (p:Person {name: 'Alice', bio: 'ML engineer building LLM agents'})")
kg.cypher("CREATE (p:Person {name: 'Bob', bio: 'AI researcher focused on NLP'})")

results = kg.search("who works on language models?", top_k=2)
# Finds both Alice and Bob even though query doesn't match exactly

# 2. Cypher - graph relationships
kg.cypher("CREATE (alice:Person {name: 'Alice'})")
kg.cypher("CREATE (bob:Person {name: 'Bob'})")
kg.cypher("CREATE (acme:Company {name: 'Acme AI'})")
kg.cypher("MATCH (alice:Person {name: 'Alice'}), (acme:Company) CREATE (alice)-[:WORKS_AT]->(acme)")

# Simple pattern matching - no messy SQL joins
colleagues = kg.cypher("MATCH (p:Person)-[:WORKS_AT]->(:Company)<-[:WORKS_AT]-(colleague) RETURN colleague")

# 3. SQL - analytics and aggregation
stats = kg.query("""
    SELECT
        json_extract(properties, '$.name') as company,
        COUNT(*) as employee_count
    FROM graph_nodes
    WHERE labels LIKE '%Company%'
    GROUP BY company
""")

# The power: combine all three in one query!
```

## Why ChimeraDB?

**Three powerful tools, one simple database:**

1. **Vector embeddings** - Search by meaning, not keywords. Find "machine learning expert" when the text says "AI researcher"
2. **Cypher graph queries** - Express relationships naturally: `MATCH (person)-[:WORKS_AT]->(company)` beats complex SQL joins
3. **Full SQL analytics** - Aggregate, filter, join with the full power of SQLite when you need it

**The combination is the killer feature:**
- RAG systems: Semantic search + relationship context
- AI agents: Graph traversal + analytical reasoning
- Recommendations: Similarity search + collaborative filtering

**Zero infrastructure:**
- One SQLite file
- Runs anywhere (laptop, server, edge device)
- Works with any language (Python, Node.js, Go, Rust...)

## Installation

### Python Package

```bash
pip install chimeradb
```

Or from source:
```bash
git clone https://github.com/codimusmaximus/chimeradb.git
cd chimeradb
./setup.sh && source .venv/bin/activate
```

### SQL Only (Any Language)

```bash
# macOS ARM64
mkdir -p extensions
curl -L https://github.com/agentflare-ai/sqlite-graph/releases/latest/download/libgraph.dylib -o extensions/libgraph.dylib
curl -L https://github.com/sqliteai/sqlite-vector/releases/latest/download/vector-macos-arm64.dylib -o extensions/vector.dylib
```

Then load in any SQLite client:
```sql
.load extensions/libgraph
.load extensions/vector
```

Use from Python, Node.js, Go, Rust, Java, C++, or any language with SQLite support.

## Python API

```python
from chimeradb import KnowledgeGraph

# Create database
kg = KnowledgeGraph("my_graph.db")  # Or ":memory:"

# Optional: disable embeddings or use different model
# kg = KnowledgeGraph("my.db", embedding_model=None)
# kg = KnowledgeGraph("my.db", embedding_model="text-embedding-3-small")

# Add nodes
kg.add_entity(
    entity_id="person1",
    labels=["Person"],
    properties={"name": "Alice", "bio": "AI researcher"},
    embed_field="bio"
)

# Add relationships
kg.add_relationship(
    from_id="person1",
    to_id="company1",
    relation_type="WORKS_AT",
    properties={"since": 2020}
)

# Semantic search
results = kg.search("machine learning expert", top_k=10)

# Graph traversal
network = kg.traverse("person1", direction="outgoing", max_depth=3)

# SQL queries
data = kg.query("""
    SELECT json_extract(properties, '$.name') as name
    FROM graph_nodes
    WHERE json_extract(properties, '$.role') = 'Engineer'
""")

kg.close()
```

## Examples

- **[00_sql_only.sql](examples/00_sql_only.sql)**: Pure SQL usage (no Python)
- **[01_getting_started.py](examples/01_getting_started.py)**: Python API basics
- **[02_basic.py](examples/02_basic.py)**: Semantic search + graph traversal + SQL analytics
- **[03_advanced.py](examples/03_advanced.py)**: Research paper recommendations with graph analysis

## Requirements

- Python 3.8+
- macOS (ARM64 or Intel) - Linux and Windows coming soon
- `sentence-transformers` (auto-installed by setup.sh)

## Documentation

- [Getting Started Guide](docs/GETTING_STARTED.md)
- [Cypher Guide](docs/CYPHER_GUIDE.md)
- [Labels Guide](docs/LABELS_GUIDE.md)
- [Limitations](docs/LIMITATIONS.md)

## Tech Stack

Built on:
- [SQLite](https://sqlite.org) - World's most deployed database
- [sqlite-vector](https://github.com/sqliteai/sqlite-vector) - Vector similarity search
- [sqlite-graph](https://github.com/agentflare-ai/sqlite-graph) - Cypher queries

## License

MIT - see [LICENSE](LICENSE)
