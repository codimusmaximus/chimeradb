# SQLite-KG Quick Start Guide

## Setup (5 minutes)

### Step 1: Navigate to the project

```bash
cd /Users/alexanderleirvag/apps/sandbox/sqlitegraph/sqlite-kg
```

### Step 2: Run the setup script

```bash
./setup.sh
```

This will:
- Create a Python virtual environment
- Install dependencies
- Download sqlite-graph and sqlite-vector extensions
- Run tests to verify installation

**Expected output:**
```
=========================================
SQLite Knowledge Graph Setup
=========================================
Detected: Darwin arm64

[1/5] Creating virtual environment...
✓ Virtual environment created

[2/5] Installing Python dependencies...
✓ Dependencies installed

[3/5] Setting up extensions directory...
✓ Extensions directory created

[4/5] Downloading sqlite-graph extension...
✓ Built and copied libgraph.dylib

[5/5] Downloading sqlite-vector extension...
✓ Downloaded vector.dylib

=========================================
Testing installation...
=========================================
✓ Graph extension loaded
✓ Vector extension loaded (v0.9.52)
✓ Graph table created

✅ Installation successful!
```

### Step 3: Activate the environment

```bash
source venv/bin/activate
```

## Run Examples

### Example 1: Quickstart (No embeddings)

```bash
python examples/01_quickstart.py
```

This demonstrates:
- Creating a knowledge graph
- Adding entities (people, companies)
- Creating relationships
- Querying the graph
- Finding neighbors

### Example 2: RAG System (Document retrieval)

```bash
python examples/02_rag_system.py
```

This demonstrates:
- Storing documents as graph nodes
- Creating citation/reference relationships
- Querying by category
- Finding related documents

## Interactive Testing

### Test 1: Python REPL

```bash
python
```

```python
from sqlite_kg import KnowledgeGraph

# Create knowledge graph
kg = KnowledgeGraph()

# Add an entity
kg.add_entity("person_1", {
    "name": "Alice",
    "role": "Engineer"
})

# Add another
kg.add_entity("company_1", {
    "name": "OpenAI",
    "industry": "AI"
})

# Create relationship
kg.add_relationship("person_1", "company_1", "WORKS_AT")

# Query
results = kg.query("SELECT COUNT(*) FROM graph_nodes")
print(f"Total nodes: {results[0][0]}")

# Get neighbors
neighbors = kg.get_neighbors("person_1")
print(f"Neighbors: {neighbors}")

kg.close()
```

### Test 2: Direct SQL

```bash
sqlite3 test.db
```

```sql
.load extensions/libgraph
.load extensions/vector

CREATE VIRTUAL TABLE graph USING graph();

INSERT INTO graph_nodes (id, properties)
VALUES (1, '{"name": "Alice"}');

SELECT * FROM graph_nodes;

.quit
```

## Common Operations

### 1. Create a Knowledge Graph

```python
from sqlite_kg import KnowledgeGraph

# In-memory (temporary)
kg = KnowledgeGraph()

# Persistent (saved to disk)
kg = KnowledgeGraph(db_path="my_graph.db")

# With embeddings (requires sentence-transformers)
kg = KnowledgeGraph(
    db_path="my_graph.db",
    embedding_model="sentence-transformers/all-MiniLM-L6-v2",
    auto_embed=True
)
```

### 2. Add Entities

```python
# Simple entity
kg.add_entity("1", {"name": "Alice", "age": 30})

# With multiple properties
kg.add_entity("2", {
    "name": "Bob",
    "role": "Engineer",
    "skills": ["Python", "SQL", "ML"],
    "location": "San Francisco"
})

# Auto-generate embedding (if model configured)
kg.add_entity("3",
    {"text": "Expert in machine learning and NLP"},
    auto_embed=True,
    embed_field="text"
)
```

### 3. Add Relationships

```python
# Simple relationship
kg.add_relationship("1", "2", "KNOWS")

# With properties
kg.add_relationship("1", "2", "WORKS_WITH", {
    "since": 2020,
    "project": "ML Platform"
})
```

### 4. Query the Graph

```python
# SQL queries
people = kg.query("""
    SELECT id, properties
    FROM graph_nodes
    WHERE json_extract(properties, '$.role') = 'Engineer'
""")

# Get entity
entity = kg.get_entity("1")
print(entity)  # {"id": 1, "properties": {...}}

# Get neighbors
neighbors = kg.get_neighbors("1", relation_type="KNOWS")
```

### 5. Semantic Search (if embeddings configured)

```python
# Search for similar entities
results = kg.search("machine learning expert", top_k=5)

for result in results:
    print(f"{result['properties']['name']}: {result['similarity']:.2f}")
```

### 6. Hybrid Search

```python
# Combine graph filtering with vector search
results = kg.hybrid_search(
    query_text="AI researcher",
    graph_filter="json_extract(properties, '$.role') = 'Researcher'",
    top_k=10
)
```

## Troubleshooting

### Extensions not loading

```bash
# Check extensions exist
ls -lh extensions/

# Should show:
# libgraph.dylib (or .so on Linux)
# vector.dylib (or .so on Linux)

# Re-run setup
./setup.sh
```

### Import errors

```bash
# Make sure venv is activated
source venv/bin/activate

# Verify Python can find the module
python -c "import sqlite_kg; print('OK')"
```

### Database locked errors

```python
# Always close connections
kg.close()

# Or use context manager
with KnowledgeGraph() as kg:
    kg.add_entity("1", {"name": "Alice"})
    # Automatically closed
```

## Next Steps

1. **Read the full README**: `README.md`
2. **Explore examples**: `examples/`
3. **API documentation**: (coming soon)
4. **Add your own data**: Start building!

## File Structure

```
sqlite-kg/
├── README.md              # Full documentation
├── QUICKSTART.md          # This file
├── setup.sh               # Installation script
├── setup.py               # Python package setup
├── requirements.txt       # Dependencies
│
├── sqlite_kg/             # Main package
│   ├── __init__.py
│   ├── knowledge_graph.py # KnowledgeGraph class
│   └── embeddings.py      # Embedding utilities
│
├── examples/              # Example scripts
│   ├── 01_quickstart.py
│   └── 02_rag_system.py
│
├── extensions/            # SQLite extensions
│   ├── libgraph.dylib
│   └── vector.dylib
│
└── tests/                 # Tests (coming soon)
```

## Quick Commands Reference

```bash
# Setup
./setup.sh

# Activate environment
source venv/bin/activate

# Run examples
python examples/01_quickstart.py
python examples/02_rag_system.py

# Interactive Python
python
>>> from sqlite_kg import KnowledgeGraph
>>> kg = KnowledgeGraph()

# Deactivate environment
deactivate
```

## Support

- Documentation: See `README.md`
- Examples: See `examples/`
- Issues: GitHub Issues (if you make this a repo)

---

**You're ready to build!** 🚀

Try creating your first knowledge graph:

```bash
python examples/01_quickstart.py
```
