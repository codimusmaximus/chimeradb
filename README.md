# SQLite Knowledge Graph (sqlite-kg)

A batteries-included SQLite knowledge graph with vector embeddings for semantic search, RAG applications, and recommendations.

## Features

✨ **Graph Database** - Nodes, edges, and properties powered by [sqlite-graph](https://github.com/agentflare-ai/sqlite-graph)
🔍 **Vector Search** - Semantic similarity search using [sqlite-vector](https://github.com/sqliteai/sqlite-vector)
🚀 **Easy Setup** - One command to install and start building
🐍 **Python API** - Simple, intuitive interface
📦 **No Dependencies** - Pure SQLite, runs anywhere
⚡ **Fast** - In-memory or persistent, your choice

## Quick Start

### Installation

```bash
# Clone or download this repo
cd sqlite-kg

# Run the setup script (downloads extensions, sets up venv)
./setup.sh

# Activate the environment
source venv/bin/activate
```

### Your First Knowledge Graph in 60 Seconds

```python
from sqlite_kg import KnowledgeGraph

# Create a knowledge graph
kg = KnowledgeGraph()

# Add entities with embeddings
kg.add_entity("person_1", {
    "name": "Alice",
    "role": "AI Researcher",
    "bio": "Works on deep learning and NLP"
})

kg.add_entity("person_2", {
    "name": "Bob",
    "role": "Software Engineer",
    "bio": "Builds distributed systems"
})

kg.add_entity("company_1", {
    "name": "OpenAI",
    "industry": "AI Research"
})

# Add relationships
kg.add_relationship("person_1", "company_1", "WORKS_AT")
kg.add_relationship("person_1", "person_2", "KNOWS")

# Semantic search (auto-generates embeddings if you have a model configured)
similar = kg.search("machine learning expert", top_k=5)
print(similar)

# Graph queries
results = kg.query("""
    SELECT * FROM entities
    WHERE json_extract(properties, '$.role') = 'AI Researcher'
""")

# Hybrid: Graph + Vector search
researchers = kg.find_similar_in_subgraph(
    query="deep learning",
    filter_query="SELECT id FROM entities WHERE role = 'AI Researcher'",
    top_k=3
)
```

## Use Cases

### 1. 🤖 RAG (Retrieval-Augmented Generation)

Store document chunks with embeddings and relationships:

```python
kg = KnowledgeGraph()

# Add document chunks
kg.add_entity("chunk_1", {
    "text": "Machine learning is a subset of AI...",
    "source": "ml_textbook.pdf",
    "page": 1
})

# Find relevant context
context = kg.search("What is machine learning?", top_k=3)
```

### 2. 💡 Recommendation Engine

```python
# Add users and items with embeddings
kg.add_entity("user_123", {"interests": "sci-fi, AI, space"})
kg.add_entity("movie_456", {"title": "Interstellar", "genre": "sci-fi"})

# Add interactions
kg.add_relationship("user_123", "movie_456", "WATCHED", {"rating": 5})

# Find similar users or items
similar_users = kg.search_similar_to("user_123", entity_type="user")
recommendations = kg.recommend_for_user("user_123")
```

### 3. 🔗 Knowledge Base / Wiki

```python
# Add concepts with relationships
kg.add_entity("concept_ai", {"name": "Artificial Intelligence", ...})
kg.add_entity("concept_ml", {"name": "Machine Learning", ...})
kg.add_relationship("concept_ml", "concept_ai", "IS_SUBSET_OF")

# Traverse the graph
related = kg.find_related("concept_ml", relationship="IS_SUBSET_OF")
```

## Python API

### Creating a Knowledge Graph

```python
from sqlite_kg import KnowledgeGraph

# In-memory (fast, temporary)
kg = KnowledgeGraph()

# Persistent (saved to disk)
kg = KnowledgeGraph(db_path="my_knowledge_graph.db")

# With custom embedding model
kg = KnowledgeGraph(
    embedding_model="sentence-transformers/all-MiniLM-L6-v2",
    embedding_dim=384
)
```

### Adding Data

```python
# Add entity (node)
kg.add_entity(
    entity_id="person_1",
    properties={"name": "Alice", "role": "Engineer"},
    labels=["Person", "Employee"]
)

# Add with automatic embedding
kg.add_entity(
    entity_id="doc_1",
    properties={"text": "This is a document about AI"},
    auto_embed=True,  # Automatically generate embedding from text
    embed_field="text"
)

# Add relationship (edge)
kg.add_relationship(
    from_id="person_1",
    to_id="company_1",
    relation_type="WORKS_AT",
    properties={"since": 2020}
)
```

### Querying

```python
# Semantic search (vector similarity)
results = kg.search(
    query="AI researcher",
    top_k=10,
    min_similarity=0.7
)

# Graph queries (SQL)
results = kg.query("""
    SELECT e.id, e.properties
    FROM entities e
    WHERE json_extract(e.properties, '$.role') = 'Engineer'
""")

# Traverse relationships
neighbors = kg.get_neighbors("person_1", relation_type="WORKS_AT")

# Path finding
path = kg.shortest_path("person_1", "person_2")

# Hybrid query
results = kg.hybrid_search(
    query_text="machine learning expert",
    graph_filter="labels LIKE '%Person%'",
    top_k=5
)
```

### Batch Operations

```python
# Batch insert
entities = [
    {"id": f"person_{i}", "properties": {...}}
    for i in range(1000)
]
kg.add_entities_batch(entities)

# Batch embed
kg.generate_embeddings_batch(
    entity_ids=["doc_1", "doc_2", "doc_3"],
    field="text"
)
```

## Architecture

```
┌─────────────────────────────────────────┐
│         Your Application                │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│      sqlite_kg (Python API)             │
│  - KnowledgeGraph                       │
│  - Entity management                    │
│  - Vector search                        │
│  - Graph queries                        │
└─────────────┬───────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│          SQLite Database                │
│  ┌────────────────┐  ┌────────────────┐ │
│  │  sqlite-graph  │  │ sqlite-vector  │ │
│  │  extension     │  │  extension     │ │
│  └────────────────┘  └────────────────┘ │
│                                          │
│  Tables:                                 │
│  - entities (nodes + embeddings)         │
│  - relationships (edges)                 │
└─────────────────────────────────────────┘
```

## Installation Details

The `setup.sh` script automatically:

1. ✅ Creates Python virtual environment
2. ✅ Downloads sqlite-graph extension (graph database)
3. ✅ Downloads sqlite-vector extension (vector search)
4. ✅ Installs Python dependencies
5. ✅ Runs tests to verify installation

### Manual Installation

If you prefer manual setup:

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Download extensions (macOS ARM64 example)
mkdir -p extensions
curl -L https://github.com/agentflare-ai/sqlite-graph/releases/latest/download/libgraph.dylib \
  -o extensions/libgraph.dylib
curl -L https://github.com/sqliteai/sqlite-vector/releases/latest/download/vector-macos-arm64.dylib \
  -o extensions/vector.dylib

# Test
python -m pytest tests/
```

## Examples

See the `examples/` directory:

- `01_quickstart.py` - Basic usage
- `02_rag_system.py` - Document RAG system
- `03_recommendations.py` - Movie recommendation engine
- `04_knowledge_base.py` - Wikipedia-style knowledge base
- `05_social_network.py` - Social network with interests
- `06_hybrid_search.py` - Combining graph + vector queries

Run any example:

```bash
python examples/01_quickstart.py
```

## Configuration

Create a `.env` file or configure programmatically:

```python
kg = KnowledgeGraph(
    db_path="my_kg.db",
    embedding_model="sentence-transformers/all-MiniLM-L6-v2",
    embedding_dim=384,
    auto_embed=True,  # Auto-generate embeddings on insert
    cache_embeddings=True,  # Cache model in memory
)
```

### Supported Embedding Models

- **sentence-transformers** (recommended)
  - `all-MiniLM-L6-v2` (384 dim, fast)
  - `all-mpnet-base-v2` (768 dim, better quality)
- **OpenAI** (requires API key)
  - `text-embedding-3-small` (1536 dim)
  - `text-embedding-3-large` (3072 dim)
- **Custom** - Bring your own embeddings

## Performance

- **In-memory**: 1M+ nodes, 10M+ edges
- **Vector search**: Sub-millisecond for 100k embeddings
- **Graph queries**: Optimized with SQLite indexes
- **Batch operations**: 10k+ inserts/second

## Testing

```bash
# Run all tests
pytest

# Run specific test
pytest tests/test_basic.py

# With coverage
pytest --cov=sqlite_kg tests/
```

## Requirements

- **Python**: 3.8+
- **Platform**: macOS (ARM64/x86_64), Linux (x86_64), Windows (WSL)
- **Optional**:
  - `sentence-transformers` for auto-embedding
  - `openai` for OpenAI embeddings

## Roadmap

- [x] Core graph + vector integration
- [x] Python API
- [x] Batch operations
- [ ] Async API support
- [ ] GraphQL interface
- [ ] Web UI for visualization
- [ ] Graph algorithms (PageRank, community detection)
- [ ] Full-text search integration
- [ ] Import/export (GraphML, JSON, CSV)

## Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT License - see [LICENSE](LICENSE)

## Credits

Built on top of:
- [sqlite-graph](https://github.com/agentflare-ai/sqlite-graph) - Graph database extension
- [sqlite-vector](https://github.com/sqliteai/sqlite-vector) - Vector search extension

## Support

- 📖 Documentation: [docs/](docs/)
- 💬 Discussions: GitHub Discussions
- 🐛 Issues: GitHub Issues
- 📧 Email: [your-email]

---

**Quick Links:**
- [Installation Guide](docs/installation.md)
- [API Reference](docs/api.md)
- [Examples](examples/)
- [FAQ](docs/faq.md)
