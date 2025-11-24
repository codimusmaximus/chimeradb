# Cypher Query Guide for SQLite Knowledge Graph

## TL;DR - What Works (v0.1.0)

**✅ Fully Supported:**
- Creating nodes with Cypher: `CREATE (p:Person {name: "Alice"})`
- Creating nodes with SQL INSERT: `INSERT INTO graph_nodes (id, labels, properties) ...`
- Creating nodes with Python API: `kg.add_entity(..., labels=["Person"])`
- Pattern matching: `MATCH (a)-[r]->(b)`
- Label-based queries: `MATCH (p:Person) RETURN p`
- Hybrid SQL + Cypher workflows

**⚠️ Important:**
- **Do NOT** use `ALTER TABLE` on `graph_nodes` or `graph_edges` - it breaks Cypher queries
- Labels must be JSON arrays: `["Person"]` not `"Person"`
- The KnowledgeGraph class uses a separate `node_embeddings` table to avoid modifying graph_nodes

## Understanding Cypher Results

### Return Format

Cypher queries return a special format, not standard JSON:

```python
kg.cypher_query('MATCH (p:Person) RETURN p')
# Raw result: [{"p":Node(1)},{"p":Node(2)}]
```

The `Node(id)` format is NOT valid JSON - it's a placeholder showing node IDs.

### Using the Python API

The `cypher_query()` method automatically extracts node IDs:

```python
# Get node IDs from Cypher
node_ids = kg.cypher_query('MATCH (p:Person) RETURN p')
# Returns: [1, 2, 3]

# Then get full properties with SQL or the API
for nid in node_ids:
    entity = kg.get_entity(str(nid))
    print(entity['properties'])
```

### Manual Parsing

If using raw `cypher_execute()`, use the utility functions:

```python
from sqlite_kg import extract_node_ids

result = kg.conn.execute("SELECT cypher_execute('MATCH (p:Person) RETURN p')").fetchone()
node_ids = extract_node_ids(result[0])

# Then query with SQL
placeholders = ','.join('?' * len(node_ids))
sql = f"SELECT properties FROM graph_nodes WHERE id IN ({placeholders})"
nodes = kg.conn.execute(sql, node_ids).fetchall()
```

## Best Practices

### 1. Hybrid Approach (Recommended)

Use Cypher for pattern matching, SQL for data extraction:

```python
# Step 1: Use Cypher to find relevant nodes
node_ids = kg.cypher_query('MATCH (p:Person)-[:WORKS_AT]->(c:Company) RETURN p')

# Step 2: Use SQL to get properties and aggregate
sql = """
    SELECT
        json_extract(properties, '$.name'),
        json_extract(properties, '$.role')
    FROM graph_nodes
    WHERE id IN ({})
""".format(','.join('?' * len(node_ids)))

results = kg.conn.execute(sql, node_ids).fetchall()
```

### 2. Creating Nodes

**Option A: Cypher CREATE** (Handles labels automatically)
```python
kg.conn.execute("SELECT cypher_execute('CREATE (p:Person {name: \"Alice\", age: 30})')")
```

**Option B: SQL INSERT** (Must include labels)
```python
kg.conn.execute(
    "INSERT INTO graph_nodes (labels, properties) VALUES (?, ?)",
    (json.dumps(["Person"]), json.dumps({"name": "Alice", "age": 30}))
)
```

**Option C: Python API** (Clean and simple)
```python
kg.add_entity(
    entity_id="1",
    labels=["Person"],
    properties={"name": "Alice", "age": 30}
)
```

### 3. Querying Patterns

**Simple label match:**
```python
node_ids = kg.cypher_query('MATCH (p:Person) RETURN p')
```

**Relationship pattern:**
```python
node_ids = kg.cypher_query('MATCH (a)-[:KNOWS]->(b) RETURN a, b')
```

**With property filter (if supported):**
```python
node_ids = kg.cypher_query('MATCH (p:Person) WHERE p.age > 25 RETURN p')
```

## Common Gotchas

### Gotcha #1: Property Access in RETURN

❌ **Doesn't work yet:**
```python
kg.cypher_query('MATCH (p:Person) RETURN p.name, p.age')
# Error: Property projection not implemented
```

✅ **Workaround:**
```python
node_ids = kg.cypher_query('MATCH (p:Person) RETURN p')
# Then use SQL to get properties
```

### Gotcha #2: Missing Labels

❌ **Will fail:**
```python
# Insert without labels
kg.conn.execute(
    "INSERT INTO graph_nodes (properties) VALUES (?)",
    (json.dumps({"name": "Alice"}),)
)

# Cypher can't find it
kg.cypher_query('MATCH (p:Person) RETURN p')  # Empty result
```

✅ **Always include labels:**
```python
kg.conn.execute(
    "INSERT INTO graph_nodes (labels, properties) VALUES (?, ?)",
    (json.dumps(["Person"]), json.dumps({"name": "Alice"}))
)
```

### Gotcha #3: String Values in Cypher

❌ **Single quotes cause issues:**
```cypher
CREATE (p:Person {name: 'Alice'})  # May fail due to SQL escaping
```

✅ **Use double quotes:**
```cypher
CREATE (p:Person {name: "Alice"})  # Works correctly
```

### Gotcha #4: Complex WHERE Clauses

❌ **Not yet supported:**
```cypher
MATCH (p:Person) WHERE p.age > 25 AND p.dept = 'IT' RETURN p
```

✅ **Use SQL for complex filters:**
```python
sql = """
    SELECT id FROM graph_nodes
    WHERE json_extract(properties, '$.age') > 25
      AND json_extract(properties, '$.dept') = 'IT'
      AND labels LIKE '%Person%'
"""
node_ids = [r[0] for r in kg.conn.execute(sql).fetchall()]
```

### Gotcha #5: Variable-Length Paths

❌ **Not yet supported:**
```cypher
MATCH (a)-[:KNOWS*1..3]->(b) RETURN b
```

✅ **Use SQL recursive CTEs:**
```sql
WITH RECURSIVE paths(id, depth) AS (
  SELECT target, 1 FROM graph_edges WHERE source = ? AND edge_type = 'KNOWS'
  UNION
  SELECT e.target, p.depth + 1
  FROM paths p
  JOIN graph_edges e ON p.id = e.source
  WHERE p.depth < 3 AND e.edge_type = 'KNOWS'
)
SELECT DISTINCT id FROM paths
```

## Examples

### Example 1: Find and Analyze

```python
from sqlite_kg import KnowledgeGraph

kg = KnowledgeGraph("my_graph.db")

# Create nodes
kg.add_entity("1", labels=["Person"], properties={"name": "Alice", "age": 30})
kg.add_entity("2", labels=["Person"], properties={"name": "Bob", "age": 25})
kg.add_relationship("1", "2", "KNOWS")

# Query with Cypher
node_ids = kg.cypher_query('MATCH (p:Person) RETURN p')
print(f"Found {len(node_ids)} people")

# Get details with SQL
for nid in node_ids:
    entity = kg.get_entity(str(nid))
    print(f"  {entity['properties']['name']}: {entity['properties']['age']}")
```

### Example 2: Pattern Matching + Aggregation

```python
# Find all managers
manager_ids = kg.cypher_query('MATCH (m)-[:MANAGES]->(e) RETURN m')

# Count their direct reports (SQL aggregation)
sql = """
    SELECT
        json_extract(n.properties, '$.name') as manager,
        COUNT(e.target) as report_count
    FROM graph_nodes n
    JOIN graph_edges e ON n.id = e.source
    WHERE e.edge_type = 'MANAGES'
      AND n.id IN ({})
    GROUP BY n.id
""".format(','.join('?' * len(manager_ids)))

results = kg.conn.execute(sql, manager_ids).fetchall()
for manager, count in results:
    print(f"{manager}: {count} direct reports")
```

## Future Improvements

These features are planned for future releases:

1. **Property projection**: `RETURN p.name, p.age`
2. **Complex WHERE**: `WHERE p.age > 25 AND p.dept = 'IT'`
3. **Variable-length paths**: `[:KNOWS*1..3]`
4. **Aggregations**: `COUNT()`, `SUM()`, `AVG()`
5. **ORDER BY / LIMIT / SKIP**: Result modifiers
6. **Full property JSON**: Instead of `Node(id)` format

Until then, combine Cypher's graph pattern matching with SQL's analytical power for best results!

## Troubleshooting

### "Failed to open root iterator"

**Symptoms:** Cypher MATCH queries fail with this error

**Most Common Cause:** Using `ALTER TABLE` on graph_nodes or graph_edges

The sqlite-graph virtual table manages these backing tables internally. When you modify their schema with `ALTER TABLE`, it breaks the virtual table's internal state.

**Solution:** **Never use ALTER TABLE on graph_nodes or graph_edges**

If you need to store additional data:
- Create a separate table and join with `graph_nodes.id`
- Example: The KnowledgeGraph class uses a `node_embeddings` table instead of adding an embedding column to graph_nodes

```python
# ❌ DON'T: Breaks Cypher!
conn.execute("ALTER TABLE graph_nodes ADD COLUMN embedding BLOB")

# ✅ DO: Create separate table
conn.execute("""
    CREATE TABLE node_embeddings (
        node_id INTEGER PRIMARY KEY,
        embedding BLOB,
        FOREIGN KEY (node_id) REFERENCES graph_nodes(id)
    )
""")
```

### Empty Results

**Check:**
1. Do nodes have labels? `SELECT labels FROM graph_nodes`
2. Are labels JSON arrays? Should be `["Person"]` not `"Person"`
3. Did Cypher CREATE succeed? Check with `SELECT * FROM graph_nodes`

## Summary

**Best Practices:**
1. Use Cypher CREATE, SQL INSERT with labels, or Python API for creating nodes
2. Use Cypher MATCH for graph pattern matching (returns Node IDs)
3. Use SQL queries to extract properties and perform analytics
4. Combine both: Cypher finds structure, SQL extracts data
5. **Never use ALTER TABLE on graph_nodes or graph_edges** - use separate tables instead

**This hybrid approach gives you the best of both worlds!**
