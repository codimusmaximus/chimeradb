# Getting Started with ChimeraDB

Complete guide to installing and using ChimeraDB.

## Quick Install (Recommended)

```bash
pip install chimeradb
```

That's it! You're ready to use ChimeraDB.

## Development Setup (From Source)

### Prerequisites

- **macOS** (ARM64 or Intel)
- **Python 3.8+**
- **Git**

### 1. Clone the Repository

```bash
git clone https://github.com/codimusmaximus/chimeradb.git
cd chimeradb
```

### 2. Run Automated Setup

The setup script handles everything automatically:

```bash
./setup.sh
```

This script will:
- ✅ Create a Python virtual environment with `uv`
- ✅ Install Python dependencies
- ✅ Download sqlite-graph extension (Cypher support)
- ✅ Download sqlite-vector extension (semantic search)
- ✅ Install the chimeradb package in editable mode

**Note:** If you don't have `uv` installed, the script will install it automatically.

### 3. Activate the Virtual Environment

```bash
source .venv/bin/activate
```

You should see `(.venv)` in your terminal prompt.

### 4. Verify Installation

```bash
# Quick test
python3 -c "from chimeradb import KnowledgeGraph; print('✓ Installation successful!')"
```

## Running the Examples

All examples use timestamped databases to ensure a fresh start every time.

### Example 1: Getting Started (Basic Operations)

```bash
python3 examples/01_getting_started.py
```

**What it demonstrates:**
- Creating nodes with Cypher CREATE
- Creating nodes with Python API
- Creating nodes with SQL INSERT
- Querying with Cypher MATCH
- Querying with SQL
- When to use each approach

**Runtime:** ~5 seconds

### Example 2: Supply Chain Analytics

```bash
python3 examples/02_basic.py
```

**What it demonstrates:**
- **Real-world workflow**: Semantic search → Graph discovery → SQL analytics
- Search for "port in shanghai" without knowing exact ID
- Discover companies shipping through that port
- Traverse the full supply chain network
- Aggregate shipment statistics with SQL

**Scenario:** "Which companies ship through Shanghai?"
- Start with natural language query
- Find entities by semantic meaning
- Follow graph relationships
- Analyze data with powerful SQL

**Runtime:** ~10 seconds (includes embedding generation)

**Note:** First run downloads the sentence-transformers model (~80MB)

### Example 3: Advanced Graph Analysis

```bash
python3 examples/03_advanced.py
```

**What it demonstrates:**
- Research paper knowledge graph
- Semantic search for relevant papers
- Connected component detection
- Graph algorithms (BFS)
- Complex SQL queries for graph analysis

**Runtime:** ~15 seconds

## Understanding the Output

Each example generates a timestamped database file:
```
examples/getting_started_20241123_143022.db
examples/supply_chain_20241123_143045.db
examples/research_papers_20241123_143112.db
```

These files persist between runs, allowing you to inspect them:

```bash
# Inspect database with sqlite3
sqlite3 examples/getting_started_20241123_143022.db

# List tables
.tables

# View nodes
SELECT id, labels, properties FROM graph_nodes;

# Exit
.quit
```

## Clean Up Old Databases

```bash
# Remove all example databases
rm -f examples/*.db

# Or keep only the most recent
ls -t examples/*.db | tail -n +4 | xargs rm -f
```

## Next Steps

### Create Your Own Knowledge Graph

```python
from chimeradb import KnowledgeGraph

# Create a new graph
kg = KnowledgeGraph("my_graph.db")

# Add some data
kg.add_entity("1", labels=["Person"], properties={"name": "Alice"})
kg.add_entity("2", labels=["Person"], properties={"name": "Bob"})
kg.add_relationship("1", "2", "KNOWS")

# Query it
result = kg.conn.execute(
    "SELECT cypher_execute(?)", 
    ("MATCH (p:Person) RETURN p",)
).fetchone()

print(result)
kg.close()
```

### With Semantic Search

```python
from chimeradb import KnowledgeGraph

# Auto-embeddings enabled by default!
kg = KnowledgeGraph("semantic_graph.db")

# Add entities (embeddings generated automatically)
kg.add_entity(
    "doc1",
    labels=["Document"],
    properties={"text": "Machine learning and artificial intelligence"},
    embed_field="text"  # Which field to embed
)

# Search by meaning
results = kg.search("AI and ML", top_k=5)
print(results)

kg.close()
```

## Troubleshooting

### Issue: `ModuleNotFoundError: No module named 'chimeradb'`

**Solution:** Install the package in editable mode:
```bash
source .venv/bin/activate
uv pip install -e .
```

### Issue: `RuntimeError: Could not load graph extension`

**Solution:** Extensions weren't downloaded. Run setup again:
```bash
./setup.sh
```

### Issue: `Failed to open root iterator` (Cypher errors)

**Possible causes:**
1. **Old database with corrupted schema** - Use timestamped databases (examples do this automatically)
2. **Unsupported Cypher pattern** - See [LIMITATIONS.md](LIMITATIONS.md) for workarounds
3. **Quote escaping issue** - Use parameterized queries:
   ```python
   # ✓ Correct
   kg.conn.execute("SELECT cypher_execute(?)", ("CREATE (p:Person {name: 'Alice'})",))
   
   # ✗ Wrong
   kg.conn.execute('SELECT cypher_execute(\'CREATE (p:Person {name: "Alice"})\')')
   ```

### Issue: Embeddings taking too long

**Solution:** Use a smaller/faster model or reduce batch size:
```python
kg = KnowledgeGraph(
    embedding_model="all-MiniLM-L6-v2",  # Faster than all-mpnet-base-v2
    embedding_dim=384
)
```

## Documentation

- **[README.md](../README.md)** - Overview and features
- **[LIMITATIONS.md](LIMITATIONS.md)** - Cypher limitations and SQL workarounds
- **[CYPHER_GUIDE.md](CYPHER_GUIDE.md)** - Cypher usage examples
- **[LABELS_GUIDE.md](LABELS_GUIDE.md)** - Label handling best practices

## Support

- 🐛 **Issues:** Report bugs on GitHub Issues
- 📖 **Examples:** See `examples/` directory
- 💬 **Questions:** GitHub Discussions

---

**You're all set!** 🎉

Start with `python3 examples/01_getting_started.py` and explore from there.
