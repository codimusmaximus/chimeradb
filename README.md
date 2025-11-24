# ChimeraDB

**Knowledge graph + vector search + SQL analytics in SQLite.**

For LLM apps that need structured memory: RAG, AI agents, question answering, recommendations.

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

# Auto-embeddings enabled by default
kg = KnowledgeGraph("my.db")

# Create nodes with Cypher
kg.cypher("CREATE (d:Document {text: 'LLMs are transforming software'})")
kg.cypher("CREATE (d:Document {text: 'RAG combines retrieval with generation'})")

# Or bulk insert with SQL
import json
kg.execute(
    "INSERT INTO graph_nodes (labels, properties) VALUES (?, ?)",
    (json.dumps(["Document"]), json.dumps({"text": "Vector databases enable semantic search"}))
)
kg.commit()

# Semantic search
results = kg.search("how do AI apps work?", top_k=3)
for r in results:
    print(f"{r['properties']['text'][:50]}: {r['similarity']:.1%}")

# Graph traversal
network = kg.traverse("node_id", direction="outgoing", max_depth=3)

# SQL analytics
stats = kg.query("SELECT COUNT(*) FROM graph_nodes")
```

## What You Get

- **Semantic search**: Embeddings auto-generated on every insert
- **Graph queries**: Cypher for patterns, SQL for complex analytics
- **Zero infrastructure**: Single SQLite file, runs anywhere
- **Any language**: Pure SQL extensions work with Python, Node.js, Go, Rust, etc.

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
