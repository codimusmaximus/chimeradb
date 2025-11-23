# Fix Summary: Cypher MATCH "Failed to open root iterator" Error

## Problem

When using the KnowledgeGraph class, all Cypher MATCH queries failed with:
```
Error: Failed to open root iterator
```

## Root Cause

The issue was in `_init_schema()` method:

```python
# ❌ THIS BREAKS CYPHER:
conn.execute("ALTER TABLE graph_nodes ADD COLUMN embedding BLOB")
```

**Why it breaks:**
- The sqlite-graph extension creates and manages `graph_nodes` and `graph_edges` as backing tables for the virtual table
- Using `ALTER TABLE` on these managed tables modifies the schema without the extension knowing
- This breaks the virtual table's internal state, causing Cypher queries to fail

## Solution

Use a **separate embeddings table** instead of modifying graph_nodes:

```python
# ✅ THIS WORKS:
conn.execute("""
    CREATE TABLE node_embeddings (
        node_id INTEGER PRIMARY KEY,
        embedding BLOB,
        FOREIGN KEY (node_id) REFERENCES graph_nodes(id)
    )
""")
```

## Changes Made

### 1. `sqlite_kg/knowledge_graph.py`

**Updated `_init_schema()`:**
- Removed `ALTER TABLE graph_nodes ADD COLUMN embedding`
- Created separate `node_embeddings` table
- Updated `vector_init()` to use `node_embeddings` instead of `graph_nodes`

**Updated `add_entity()`:**
- Changed from `UPDATE graph_nodes SET embedding...`
- To `INSERT INTO node_embeddings...`

**Updated `search()` and `hybrid_search()`:**
- Updated JOIN logic to use `node_embeddings` table
- Query structure: `graph_nodes` JOIN `node_embeddings` JOIN `vector_quantize_scan`

### 2. `CYPHER_GUIDE.md`

- Updated TL;DR section to remove workaround about needing Cypher CREATE first
- Added warning about never using ALTER TABLE on virtual table backing tables
- Updated troubleshooting section with actual root cause
- Updated best practices

## Verification

All Cypher operations now work correctly:

✅ Cypher CREATE
✅ Cypher MATCH (generic)
✅ Cypher MATCH (label-based)
✅ SQL INSERT with labels
✅ Python API with labels
✅ Hybrid SQL + Cypher queries
✅ Vector search (separate table)

Tested in:
- ✅ `01_getting_started.py` - Full test passed
- ✅ Standalone simple tests - All passed
- ⏭️  `02_basic.py` - Requires sentence-transformers (optional dependency)
- ⏭️  `03_advanced.py` - Requires sentence-transformers (optional dependency)

## Key Takeaway

**Never use ALTER TABLE on virtual table backing tables.**

If you need to store additional data:
1. Create a separate table
2. Join with the main table using foreign keys
3. This preserves the virtual table's schema and internal state
