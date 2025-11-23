# sqlite-graph Limitations (Current Version)

This document outlines the current limitations of the `sqlite-graph` extension used in this library.

## ⚠️ Cypher Query Limitations

The following Cypher features are **NOT YET SUPPORTED** in the current version of sqlite-graph:

### 🚧 Coming Soon (v0.2.0 - Q1 2026)

According to [sqlite-graph documentation](https://github.com/agentflare-ai/sqlite-graph):

- **Bidirectional relationships** `<-[r]-`, `-[r]-`
- **Variable-length paths** `[r*1..3]`
- **Complex WHERE expressions** (AND, OR, NOT)
- **Aggregations** (COUNT, SUM, AVG, etc.)
- **Property projection in RETURN** `n.property`
- **ORDER BY, SKIP, LIMIT**

### ✅ Currently Supported

- **Simple directional patterns**: `MATCH (a)-[:REL]->(b)`
- **CREATE statements**: `CREATE (n:Label {prop: value})`
- **Basic MATCH queries**: `MATCH (n:Label) RETURN n`
- **Single node returns**: `RETURN n` (not `RETURN n, m`)

## 🛠️ Workarounds

For unsupported features, **use SQL instead**:

### Example 1: Bidirectional Pattern

❌ **Not Supported:**
```cypher
MATCH (p1:Paper)-[:CITES]->(bridge:Paper)<-[:CITES]-(p2:Paper)
RETURN bridge
```

✅ **Use SQL Instead:**
```sql
SELECT DISTINCT
    json_extract(bridge.properties, '$.title') as title
FROM graph_edges e1
JOIN graph_nodes bridge ON e1.target = bridge.id
JOIN graph_edges e2 ON e2.target = bridge.id
WHERE e1.edge_type = 'CITES' AND e2.edge_type = 'CITES'
  AND e1.source != e2.source
```

### Example 2: Aggregations

❌ **Not Supported:**
```cypher
MATCH (n:Person)
RETURN n.department, COUNT(n)
```

✅ **Use SQL Instead:**
```sql
SELECT 
    json_extract(properties, '$.department') as department,
    COUNT(*) as count
FROM graph_nodes
WHERE labels LIKE '%Person%'
GROUP BY department
```

### Example 3: Variable-Length Paths

❌ **Not Supported:**
```cypher
MATCH (a:Person)-[:KNOWS*1..3]->(b:Person)
RETURN a, b
```

✅ **Use Recursive CTE in SQL:**
```sql
WITH RECURSIVE paths AS (
    -- Base case: direct connections
    SELECT source, target, 1 as depth
    FROM graph_edges
    WHERE edge_type = 'KNOWS'
    
    UNION ALL
    
    -- Recursive case: extend paths
    SELECT p.source, e.target, p.depth + 1
    FROM paths p
    JOIN graph_edges e ON p.target = e.source
    WHERE p.depth < 3 AND e.edge_type = 'KNOWS'
)
SELECT DISTINCT source, target FROM paths;
```

## 💡 Best Practices

1. **Use Cypher for simple patterns**: When you just need to match nodes by label
2. **Use SQL for complex queries**: Aggregations, multi-way joins, analytics
3. **Hybrid approach**: Combine both in your application logic
4. **Check the examples**: See `examples/03_advanced.py` for real-world patterns

## 📚 Related Documentation

- [CYPHER_GUIDE.md](CYPHER_GUIDE.md) - Cypher usage with examples
- [LABELS_GUIDE.md](LABELS_GUIDE.md) - Label handling best practices  
- [sqlite-graph repo](https://github.com/agentflare-ai/sqlite-graph) - Upstream extension

## 🗓️ Roadmap

Check the [sqlite-graph roadmap](https://github.com/agentflare-ai/sqlite-graph#roadmap) for upcoming features and release timeline.
