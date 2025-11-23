#!/usr/bin/env python3
"""
Labels: The RIGHT Way - Using Cypher CREATE
"""
import sys
sys.path.insert(0, '.')

from sqlite_kg import KnowledgeGraph
import json

kg = KnowledgeGraph(db_path="test_labels_final.db")

print("=" * 80)
print("Labels: The RIGHT Way")
print("=" * 80)

# ============================================================================
# Create nodes with labels using Cypher CREATE
# ============================================================================
print("\n[1] Creating nodes with Cypher CREATE")

print("\nCypher: CREATE (p:Person {name: 'Alice', age: 30})")
kg.conn.execute("SELECT cypher_execute('CREATE (p:Person {name: \"Alice\", age: 30})')")

print("Cypher: CREATE (p:Person {name: 'Bob', age: 25})")
kg.conn.execute("SELECT cypher_execute('CREATE (p:Person {name: \"Bob\", age: 25})')")

print("Cypher: CREATE (e:Engineer {name: 'Carol', skill: 'Python'})")
kg.conn.execute("SELECT cypher_execute('CREATE (e:Engineer {name: \"Carol\", skill: \"Python\"})')")

kg.conn.commit()
print("✓ Created 3 nodes")

# Check what's in database
print("\n[2] What's in the database?")
results = kg.conn.execute("SELECT id, labels, properties FROM graph_nodes ORDER BY id").fetchall()
for node_id, labels, props in results:
    print(f"  ID {node_id}: labels={labels}, props={props}")

# ============================================================================
# Query with Cypher by label
# ============================================================================
print("\n[3] Querying by label with Cypher")

print("\n--- Query 1: MATCH (p:Person) RETURN p.name, p.age ---")
result = kg.conn.execute("SELECT cypher_execute('MATCH (p:Person) RETURN p.name, p.age')").fetchone()
data = json.loads(result[0])
print(f"Results: {data}")

print("\n--- Query 2: MATCH (e:Engineer) RETURN e.name, e.skill ---")
result = kg.conn.execute("SELECT cypher_execute('MATCH (e:Engineer) RETURN e.name, e.skill')").fetchone()
data = json.loads(result[0])
print(f"Results: {data}")

print("\n--- Query 3: MATCH (p:Person) WHERE p.age > 25 RETURN p.name ---")
result = kg.conn.execute("SELECT cypher_execute('MATCH (p:Person) WHERE p.age > 25 RETURN p.name')").fetchone()
data = json.loads(result[0])
print(f"Results: {data}")

# ============================================================================
# Now try SQL INSERT with labels
# ============================================================================
print("\n[4] Can we also INSERT with SQL?")

print("\nSQL: INSERT INTO graph_nodes (labels, properties) VALUES ...")
kg.conn.execute(
    "INSERT INTO graph_nodes (labels, properties) VALUES (?, ?)",
    (json.dumps(["Manager"]), json.dumps({"name": "Diana", "team": "AI"}))
)
kg.conn.commit()
print("✓ Inserted Diana with label 'Manager'")

# Try to query Diana
print("\nCypher: MATCH (m:Manager) RETURN m.name, m.team")
result = kg.conn.execute("SELECT cypher_execute('MATCH (m:Manager) RETURN m.name, m.team')").fetchone()
data = json.loads(result[0])
print(f"Results: {data}")

if data:
    print("✅ SQL INSERT works too!")

# ============================================================================
# Summary
# ============================================================================
print("\n" + "=" * 80)
print("Summary: How Labels Work")
print("=" * 80)

print("\n📌 Creating Nodes with Labels:")
print("  Method 1 (Recommended): Use Cypher CREATE")
print("    cypher_execute('CREATE (p:Person {name: \"Alice\"})')")
print()
print("  Method 2: Direct SQL INSERT")
print("    INSERT INTO graph_nodes (labels, properties) VALUES")
print("    (['Person'], '{\"name\": \"Alice\"}')")
print()

print("📌 Querying by Labels:")
print("  Use Cypher MATCH with label syntax:")
print("    MATCH (p:Person) RETURN p.name")
print("    MATCH (p:Person) WHERE p.age > 25 RETURN p")
print()

print("📌 Key Points:")
print("  ✅ Labels are stored as JSON array in graph_nodes.labels column")
print("  ✅ Use Cypher CREATE for nodes (it handles labels automatically)")
print("  ✅ Use Cypher MATCH (p:Label) for queries")
print("  ✅ SQL INSERT also works if you set the labels column properly")

print("\n" + "=" * 80)

kg.close()
