# How Labels Work in SQLite Knowledge Graph

## TL;DR

**✅ Labels ARE supported** in sqlite-graph, but with some limitations in the current alpha version.

## Creating Nodes with Labels

### Method 1: Cypher CREATE (Recommended)
```python
kg.conn.execute("SELECT cypher_execute('CREATE (p:Person {name: \"Alice\", age: 30})')")
```

### Method 2: SQL INSERT
```python
kg.conn.execute(
    "INSERT INTO graph_nodes (labels, properties) VALUES (?, ?)",
    (json.dumps(["Person"]), json.dumps({"name": "Alice", "age": 30}))
)
```

**⚠️ Important:** The `labels` column MUST be a JSON array: `["Person"]` or `["Person", "Employee"]`

## Querying by Labels

### ✅ What Works
```python
# Return entire node
cursor = kg.conn.execute("SELECT cypher_execute('MATCH (p:Person) RETURN p')")
result = cursor.fetchone()
# Returns: [{"p":Node(1)},{"p":Node(2)}]
```

### ❌ What Doesn't Work (Yet)
```python
# Accessing individual properties in RETURN
cursor = kg.conn.execute("SELECT cypher_execute('MATCH (p:Person) RETURN p.name, p.age')")
# Error: Failed to open root iterator
```

## Current Limitations

The sqlite-graph extension is in **alpha** and has these known limitations:

1. **RETURN clause**: Can only return whole nodes (`RETURN p`), not properties (`RETURN p.name`)
2. **Output format**: Returns `Node(id)` format instead of full JSON properties

## Database Schema

When you insert nodes, they go into the `graph_nodes` table:

```sql
CREATE TABLE graph_nodes (
    id INTEGER PRIMARY KEY,
    labels TEXT,      -- JSON array: ["Person"] or ["Person", "Employee"]
    properties TEXT   -- JSON object: {"name": "Alice", "age": 30}
);
```

## Examples

### Example 1: Insert with SQL, include labels

```python
from chimeradb import KnowledgeGraph
import json

kg = KnowledgeGraph(db_path="test.db")

# SQL insert - MUST include labels column
kg.conn.execute(
    "INSERT INTO graph_nodes (labels, properties) VALUES (?, ?)",
    (
        json.dumps(["Person"]),  # ← Labels as JSON array
        json.dumps({"name": "Alice", "role": "Engineer"})
    )
)
kg.conn.commit()

# Check what was inserted
result = kg.conn.execute("SELECT id, labels, properties FROM graph_nodes WHERE id = 1").fetchone()
print(f"ID: {result[0]}")
print(f"Labels: {result[1]}")        # ["Person"]
print(f"Properties: {result[2]}")    # {"name":"Alice","role":"Engineer"}
```

### Example 2: Insert with Cypher CREATE

```python
# Cypher CREATE automatically handles labels
kg.conn.execute("SELECT cypher_execute('CREATE (p:Person {name: \"Alice\", role: \"Engineer\"})')")
kg.conn.commit()

# Query by label
cursor = kg.conn.execute("SELECT cypher_execute('MATCH (p:Person) RETURN p')")
result = cursor.fetchone()
print(result[0])  # [{"p":Node(1)}]
```

### Example 3: Multiple labels

```python
# SQL insert with multiple labels
kg.conn.execute(
    "INSERT INTO graph_nodes (labels, properties) VALUES (?, ?)",
    (
        json.dumps(["Person", "Employee", "Engineer"]),  # Multiple labels
        json.dumps({"name": "Bob"})
    )
)
```

## Recommendations for Examples

For the sqlite-kg examples, we should:

1. **For SQL inserts**: Always include the `labels` column
   ```python
   kg.conn.execute(
       "INSERT INTO graph_nodes (labels, properties) VALUES (?, ?)",
       (json.dumps(["Person"]), json.dumps(props))
   )
   ```

2. **For Cypher queries**: Stick to returning whole nodes for now
   ```python
   # This works:
   cursor = kg.conn.execute("SELECT cypher_execute('MATCH (p:Person) RETURN p')")

   # This doesn't (yet):
   cursor = kg.conn.execute("SELECT cypher_execute('MATCH (p:Person) RETURN p.name')")
   ```

3. **For complex queries**: Use SQL to extract properties after getting node IDs from Cypher
   ```python
   # Step 1: Use Cypher to get nodes by label
   cursor = kg.conn.execute("SELECT cypher_execute('MATCH (p:Person) RETURN p')")

   # Step 2: Use SQL to get full properties
   nodes = kg.conn.execute(
       "SELECT properties FROM graph_nodes WHERE labels LIKE '%Person%'"
   ).fetchall()
   ```

## Why This Matters

When we insert with SQL in our examples (as we currently do), we **MUST** include labels if we want Cypher queries by label to work:

```python
# ❌ Current approach (no labels)
kg.conn.execute(
    "INSERT INTO graph_nodes (id, properties) VALUES (?, ?)",
    (node_id, json.dumps(props))
)

# ✅ Fixed approach (with labels)
kg.conn.execute(
    "INSERT INTO graph_nodes (id, labels, properties) VALUES (?, ?, ?)",
    (node_id, json.dumps(["Person"]), json.dumps(props))
)
```

## Testing

Run the test script to see labels in action:

```bash
python3 test_labels_final.py
```

This creates nodes with Cypher CREATE and SQL INSERT, then queries by label.
