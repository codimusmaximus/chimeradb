# ChimeraDB - Simple Usage

Dead simple knowledge graph with automatic embeddings.

## Quick Start

```python
from chimeradb import KnowledgeGraph

# That's it! Embeddings auto-enabled by default
kg = KnowledgeGraph("my_graph.db")

# Create nodes with Cypher - embeddings generated automatically
kg.cypher("CREATE (p:Person {name: 'Alice', bio: 'AI researcher'})")
kg.cypher("CREATE (p:Person {name: 'Bob', bio: 'Chef specializing in Italian food'})")

# Or use SQL for bulk inserts
import json
kg.execute(
    "INSERT INTO graph_nodes (labels, properties) VALUES (?, ?)",
    (json.dumps(["Person"]), json.dumps({"name": "Carol", "bio": "Neuroscientist"}))
)
kg.commit()

# Semantic search - just works!
results = kg.search("Who works on artificial intelligence?")
for result in results:
    print(f"{result['properties']['name']}: {result['similarity']:.2%}")
# Output:
# Alice: 15.2%
# Carol: 12.8%
# Bob: 8.1%
```

## Configuration (Optional)

```python
# Disable embeddings
kg = KnowledgeGraph("my.db", embedding_model=None)

# Use different model
kg = KnowledgeGraph("my.db", embedding_model="text-embedding-3-small")

# Specify which field to embed
kg = KnowledgeGraph("my.db", embed_field="description")
```

## Key Features

✅ **Automatic embeddings** - No configuration needed, just works
✅ **Mix Cypher & SQL** - Use the right tool for each job
✅ **Semantic search** - Understanding, not just keywords
✅ **Pure SQLite** - No external services, simple deployment

## API Methods

```python
# Create with Cypher (auto-embeds)
kg.cypher("CREATE (n:Label {prop: 'value'})")

# Create with SQL (auto-embeds)
kg.execute("INSERT INTO graph_nodes ...")

# Create with Python API (auto-embeds)
kg.add_entity(
    entity_id="1",
    labels=["Person"],
    properties={"name": "Alice", "bio": "..."}
)

# Search semantically
results = kg.search("your query", top_k=5)

# Query with SQL
results = kg.query("SELECT * FROM graph_nodes WHERE ...")

# Commit changes
kg.commit()
```

That's it! No complex setup, no configuration files, just a simple Python API with powerful features.
