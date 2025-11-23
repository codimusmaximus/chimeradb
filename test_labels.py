#!/usr/bin/env python3
"""
Testing Labels in SQL vs Cypher
"""
import sys
sys.path.insert(0, '.')

from sqlite_kg import KnowledgeGraph
import json

kg = KnowledgeGraph(db_path="test_labels.db")

print("=" * 80)
print("Testing: Labels with SQL and Cypher")
print("=" * 80)

# ============================================================================
# Test 1: Insert WITHOUT labels (current approach)
# ============================================================================
print("\n[Test 1] Insert without labels (current approach)")

kg.conn.execute(
    "INSERT INTO graph_nodes (id, properties) VALUES (?, ?)",
    (1, json.dumps({"name": "Alice", "role": "Engineer"}))
)
kg.conn.commit()

print("✓ Inserted node 1 (Alice) WITHOUT labels")

# Check what was inserted
result = kg.conn.execute("SELECT id, labels, properties FROM graph_nodes WHERE id = 1").fetchone()
print(f"  Database: id={result[0]}, labels={result[1]}, properties={result[2]}")

# Query with Cypher - try to match by label
print("\nTrying to query with Cypher: MATCH (p:Person) RETURN p.name")
cypher_query = "MATCH (p:Person) RETURN p.name"
try:
    result = kg.conn.execute("SELECT cypher_execute(?)", (cypher_query,)).fetchone()
    data = json.loads(result[0]) if result else []
    print(f"Result: {data}")
    if not data:
        print("❌ No results! Node has no label.")
except Exception as e:
    print(f"❌ Error: {e}")
    print("   (Cypher can't query nodes without labels)")

# ============================================================================
# Test 2: Insert WITH labels
# ============================================================================
print("\n[Test 2] Insert WITH labels")

kg.conn.execute(
    "INSERT INTO graph_nodes (id, labels, properties) VALUES (?, ?, ?)",
    (2, json.dumps(["Person"]), json.dumps({"name": "Bob", "role": "Manager"}))
)
kg.conn.commit()

print("✓ Inserted node 2 (Bob) WITH label 'Person'")

# Check what was inserted
result = kg.conn.execute("SELECT id, labels, properties FROM graph_nodes WHERE id = 2").fetchone()
print(f"  Database: id={result[0]}, labels={result[1]}, properties={result[2]}")

# Query again
print("\nTrying to query with Cypher: MATCH (p:Person) RETURN p.name, p.role")
cypher_query = "MATCH (p:Person) RETURN p.name, p.role"
try:
    result = kg.conn.execute("SELECT cypher_execute(?)", (cypher_query,)).fetchone()
    data = json.loads(result[0]) if result else []
    print(f"Result: {data}")
    if data:
        print("✓ Found Bob! Labels work.")
    else:
        print("❌ No results")
except Exception as e:
    print(f"❌ Error: {e}")

# ============================================================================
# Test 3: Multiple labels
# ============================================================================
print("\n[Test 3] Insert with MULTIPLE labels")

kg.conn.execute(
    "INSERT INTO graph_nodes (id, labels, properties) VALUES (?, ?, ?)",
    (3, json.dumps(["Person", "Employee", "Engineer"]), json.dumps({"name": "Carol"}))
)
kg.conn.commit()

print("✓ Inserted node 3 (Carol) WITH labels: Person, Employee, Engineer")

# Query by different labels
for label in ["Person", "Employee", "Engineer"]:
    cypher_query = f"MATCH (p:{label}) RETURN p.name"
    try:
        result = kg.conn.execute("SELECT cypher_execute(?)", (cypher_query,)).fetchone()
        data = json.loads(result[0]) if result else []
        print(f"  MATCH (p:{label}) → {data}")
    except Exception as e:
        print(f"  MATCH (p:{label}) → Error: {e}")

# ============================================================================
# Test 4: Check what's in the database
# ============================================================================
print("\n[Test 4] What's in the database?")

results = kg.conn.execute("SELECT id, labels, properties FROM graph_nodes").fetchall()
print("\nAll nodes:")
for node_id, labels, props in results:
    print(f"  ID {node_id}: labels={labels}, props={props}")

# ============================================================================
# Summary
# ============================================================================
print("\n" + "=" * 80)
print("Summary")
print("=" * 80)
print("\n📌 Key Points:")
print("  1. graph_nodes table has THREE columns: id, labels, properties")
print("  2. labels is a JSON array: ['Person'] or ['Person', 'Employee']")
print("  3. If you don't insert labels, Cypher label matching won't work")
print("  4. SQL: INSERT INTO graph_nodes (id, labels, properties) VALUES (?, ?, ?)")
print("  5. Cypher: MATCH (p:Person) requires the 'Person' label to exist")
print("\n✅ Always include labels when inserting with SQL!")
print("=" * 80)

kg.close()
