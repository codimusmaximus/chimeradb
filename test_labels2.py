#!/usr/bin/env python3
"""
Testing Labels - Using cypher_create_node() function
"""
import sys
sys.path.insert(0, '.')

from sqlite_kg import KnowledgeGraph
import json

kg = KnowledgeGraph(db_path="test_labels2.db")

print("=" * 80)
print("Testing: Using cypher_create_node() Function")
print("=" * 80)

# ============================================================================
# Method 1: Use cypher_create_node() function (official way)
# ============================================================================
print("\n[Method 1] Using cypher_create_node()")

# Create node with label
cursor = kg.conn.execute(
    "SELECT cypher_create_node(?, ?) as node_id",
    ("Person", json.dumps({"name": "Alice", "age": 30}))
)
alice_id = cursor.fetchone()[0]
print(f"✓ Created Alice with label 'Person', ID: {alice_id}")

cursor = kg.conn.execute(
    "SELECT cypher_create_node(?, ?) as node_id",
    ("Person", json.dumps({"name": "Bob", "age": 25}))
)
bob_id = cursor.fetchone()[0]
print(f"✓ Created Bob with label 'Person', ID: {bob_id}")

kg.conn.commit()

# Check database
print("\nDatabase contents:")
results = kg.conn.execute("SELECT id, labels, properties FROM graph_nodes").fetchall()
for node_id, labels, props in results:
    print(f"  ID {node_id}: labels={labels}, props={props}")

# Now try Cypher query
print("\n[Query] MATCH (p:Person) RETURN p.name, p.age")
cypher_query = "MATCH (p:Person) RETURN p.name, p.age"
try:
    result = kg.conn.execute("SELECT cypher_execute(?)", (cypher_query,)).fetchone()
    data = json.loads(result[0]) if result else []
    print(f"✅ Success! Results: {data}")
except Exception as e:
    print(f"❌ Error: {e}")

# ============================================================================
# Method 2: Direct SQL insert with labels
# ============================================================================
print("\n[Method 2] Direct SQL INSERT with labels column")

kg.conn.execute(
    "INSERT INTO graph_nodes (labels, properties) VALUES (?, ?)",
    (json.dumps(["Engineer"]), json.dumps({"name": "Carol", "skill": "Python"}))
)
kg.conn.commit()
print("✓ Inserted Carol with label 'Engineer'")

# Try to query Carol
print("\n[Query] MATCH (e:Engineer) RETURN e.name, e.skill")
cypher_query = "MATCH (e:Engineer) RETURN e.name, e.skill"
try:
    result = kg.conn.execute("SELECT cypher_execute(?)", (cypher_query,)).fetchone()
    data = json.loads(result[0]) if result else []
    print(f"Result: {data}")
    if data:
        print("✅ Direct SQL insert works too!")
    else:
        print("❌ No results")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 80)
print("Summary")
print("=" * 80)
print("\n✅ Use cypher_create_node() for creating nodes with labels")
print("✅ Or use: INSERT INTO graph_nodes (labels, properties) VALUES (...)")
print("🔑 Key: labels must be a JSON array like [\"Person\"] or [\"Person\", \"Employee\"]")
print("=" * 80)

kg.close()
