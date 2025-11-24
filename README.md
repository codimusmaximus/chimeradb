# ChimeraDB

**Semantic search + graph queries + SQL analytics. All in one DuckDB file.**

The only database that combines vector embeddings, property graphs (SQL/PGQ), and full SQL analytics for LLM apps. No separate vector DB, no separate graph DB, no infrastructure.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

[Examples](examples/) • [Docs](docs/)

---

## Quick Start

```bash
pip install chimeradb
```

```python
from chimeradb import KnowledgeGraph

# Create database with automatic embeddings (uses distilbert-base-uncased)
kg = KnowledgeGraph("my.db")
print("✓ Database created with auto-embeddings enabled")

# Add entities - embeddings automatically generated from 'bio' field
kg.add_entity("alice", {"name": "Alice", "bio": "ML engineer building LLM agents"}, ["Person"], embed_field="bio")
kg.add_entity("bob", {"name": "Bob", "bio": "AI researcher focused on NLP"}, ["Person"], embed_field="bio")
kg.add_entity("acme", {"name": "Acme AI"}, ["Company"])
print("✓ Added 2 people and 1 company")

# Add relationships
kg.add_relationship("alice", "acme", "WORKS_AT")
kg.add_relationship("bob", "acme", "WORKS_AT")
print("✓ Added employment relationships")

# 1. Semantic Search - Find by MEANING, not exact keywords
print("\n=== Semantic Search ===")
results = kg.search("who works on language models?", top_k=2)
for r in results:
    name = r['properties']['name']
    bio = r['properties'].get('bio', 'N/A')
    similarity = r['similarity']
    print(f"  {name}: {bio} (similarity: {similarity:.2f})")
# Output:
#   Bob: AI researcher focused on NLP (similarity: 0.90)
#   Alice: ML engineer building LLM agents (similarity: 0.84)
# Notice: Found both even though "language models" doesn't appear in their bios!

# 2. Graph Traversal - Follow relationships
print("\n=== Graph Traversal ===")
employees = kg.traverse("acme", direction="incoming", relation_type="WORKS_AT")
print(f"  Acme has {len(employees)} employees:")
for emp in employees:
    print(f"    - {emp['properties']['name']}")
# Output:
#   Acme has 2 employees:
#     - Alice
#     - Bob

# 3. SQL/PGQ - Graph pattern matching (SQL:2023 standard)
print("\n=== SQL/PGQ Pattern Matching ===")
results = kg.query("""
    SELECT *
    FROM GRAPH_TABLE (knowledge_graph
        MATCH (p:nodes)-[e:edges]->(c:nodes)
        WHERE c.id = 'acme'
        COLUMNS (
            json_extract_string(p.properties, 'name') as person,
            e.edge_type
        )
    )
""")
for person, edge_type in results:
    print(f"  {person} --[{edge_type}]--> Acme AI")
# Output:
#   Alice --[WORKS_AT]--> Acme AI
#   Bob --[WORKS_AT]--> Acme AI

# 4. SQL Analytics - Aggregate data
print("\n=== SQL Analytics ===")
stats = kg.query("""
    SELECT
        json_extract_string(n.properties, 'name') as company,
        COUNT(*) as employee_count
    FROM nodes n
    JOIN edges e ON e.to_id = n.id
    WHERE n.labels LIKE '%Company%'
    GROUP BY company
""")
for company, count in stats:
    print(f"  {company}: {count} employees")
# Output:
#   Acme AI: 2 employees

kg.close()
```

**Key Results:**
- ✅ Semantic search finds relevant people by MEANING (0.84-0.90 similarity scores)
- ✅ Graph traversal follows relationships naturally (finds 2 employees)
- ✅ SQL/PGQ provides clean pattern matching syntax
- ✅ Full SQL power for aggregations and analytics
- ✅ All in a single DuckDB file with no infrastructure needed

## Why ChimeraDB?

**Three powerful tools, one simple database:**

1. **Vector embeddings** - Search by meaning, not keywords. Find "machine learning expert" when the text says "AI researcher"
2. **Property graphs** - Express relationships naturally with SQL/PGQ: `MATCH (person)-[edge]->(company)`
3. **Full SQL analytics** - Aggregate, filter, join with the full power of DuckDB

**The combination is the killer feature:**
- RAG systems: Semantic search + relationship context
- AI agents: Graph traversal + analytical reasoning
- Recommendations: Similarity search + collaborative filtering

**Zero infrastructure:**
- One DuckDB file
- Runs anywhere (laptop, server, edge device)
- 10-100x faster than other embedded options
- Production-ready extensions (duckpgq, vss)

## Installation

### Python Package

```bash
pip install chimeradb duckdb
```

**Platform Support:**
- ✅ macOS (Intel x86_64 & Apple Silicon ARM64)
- ✅ Linux (x86_64)
- ✅ Linux ARM64 (with DuckDB v1.1.3)
- ⚠️ Windows: DuckDB extensions may need manual installation

Or from source:
```bash
git clone https://github.com/codimusmaximus/chimeradb.git
cd chimeradb
pip install -e .
```

### DuckDB Extensions

ChimeraDB automatically installs these DuckDB extensions:
- **duckpgq**: Property graph queries with SQL/PGQ
- **vss**: Vector similarity search with HNSW indexing

## How LLMs Use ChimeraDB

**The Problem**: Getting an LLM to answer data-driven questions is hard—not because you lack data, but because the LLM doesn't know *what data exists* or *where it lives*.

**Example Question**: *"Which rooms in Building A are using too much heating?"*

To answer this, the LLM needs to know about:
- Power consumption data and temperature readings
- Physical layout (sensors per room, rooms per building)
- Context (which rooms should be heated vs. garages/outdoors)
- How to define "overuse" and calculate baselines

Traditional approaches fail because they treat data as documents to search. But you can't search effectively if you don't understand the structure of what you're searching for.

**The Solution**: Use ChimeraDB as a knowledge graph that captures:
1. What information exists (ontology/schema)
2. What specific things exist (entities/instances)
3. How they're connected (relationships)
4. Where the data lives (data sources)

### The LLM Reasoning Workflow

**Step 1: Understand What Exists** (RAG on Knowledge Graph)
```python
# LLM searches the knowledge graph for relevant concepts
concepts = kg.search("heating power consumption room sensor", top_k=10)
# Finds: Building, Room, PowerSensor, TemperatureSensor, Timeseries
```

**Step 2: Find Specific Entities** (Graph Traversal)
```python
# Traverse from Building A to find all rooms and their sensors
building_a_rooms = kg.traverse("building_a", direction="outgoing", relation_type="CONTAINS")
# Returns: [{'id': 'office_201', 'type': 'Room'}, {'id': 'garage', 'type': 'Room'}, ...]

# For each room, get its power sensors
sensors = []
for room in building_a_rooms:
    room_sensors = kg.traverse(room['id'], direction="outgoing", relation_type="MONITORED_BY")
    sensors.extend(room_sensors)
# Now we know: Office 201 → PWR-201-A, Garage → PWR-GAR-01, etc.
```

**Step 3: Query Actual Data** (SQL Analytics)
```python
# Get sensor metadata and baseline expectations from knowledge graph
sensor_metadata = kg.query("""
    SELECT
        s.id as sensor_id,
        json_extract_string(s.properties, 'room_name') as room,
        json_extract_string(s.properties, 'baseline_watts') as baseline,
        json_extract_string(s.properties, 'room_type') as room_type
    FROM nodes s
    WHERE s.id IN ('PWR-201-A', 'PWR-GAR-01', 'PWR-SRV-01')
""")

# Now query the actual timeseries data
# (This would typically go to a separate timeseries DB, but could be in ChimeraDB too)
usage_data = external_db.query("""
    SELECT sensor_id, AVG(power_watts) as avg_power
    FROM power_readings
    WHERE sensor_id IN ('PWR-201-A', 'PWR-GAR-01', 'PWR-SRV-01')
      AND timestamp > NOW() - INTERVAL '7 days'
    GROUP BY sensor_id
""")

# Compare actual usage to baselines
for room in usage_data:
    baseline = sensor_metadata[room['sensor_id']]['baseline']
    if room['avg_power'] > baseline:
        print(f"{room['room']}: {room['avg_power']}W (baseline: {baseline}W) ⚠️ OVERUSE")
```

**Result**: "Office 201 is using 45W more than expected (95W vs 50W baseline). The Garage is correctly unheated."

**Why This Works**:
- **RAG** finds what concepts and entities exist (semantic search over knowledge graph)
- **Graph traversal** discovers relationships (Building → Rooms → Sensors)
- **SQL analytics** aggregates data and compares to baselines (actual computation)

Each step informs the next. The LLM can't query timeseries data without knowing which sensors exist. It can't find sensors without knowing which rooms exist. It can't interpret results without knowing baseline expectations. The knowledge graph makes all this discoverable.

## Examples

- **[01_getting_started.py](examples/01_getting_started.py)**: Python API basics
- **[02_basic.py](examples/02_basic.py)**: Semantic search + graph traversal + SQL analytics
- **[03_advanced.py](examples/03_advanced.py)**: Research paper recommendations with graph analysis
- **[04_industrial_iot.py](examples/04_industrial_iot.py)**: Industrial IoT - Smart building heating monitoring (demonstrates the full LLM reasoning workflow)

## Requirements

- Python 3.8+
- DuckDB 1.1.3+ (automatically installed with chimeradb)
- `sentence-transformers` (for embeddings, auto-installed)

## Documentation

- [Getting Started Guide](docs/GETTING_STARTED.md)
- [SQL/PGQ Guide](https://duckpgq.org/documentation/sql_pgq/)
- [DuckDB VSS Extension](https://duckdb.org/2024/05/03/vector-similarity-search-vss)

## Tech Stack

Built on:
- [DuckDB](https://duckdb.org) - Fast analytical database engine
- [duckpgq](https://duckpgq.org/) - SQL/PGQ property graph queries
- [vss extension](https://duckdb.org/docs/extensions/vss) - Vector similarity search

## Performance

DuckDB provides **10-100x better performance** than traditional embedded databases for analytical queries:
- Columnar storage for fast aggregations
- Vectorized query execution
- Zero-copy data access
- Production-ready HNSW indexing

## Migration from v0.1.x (SQLite)

ChimeraDB v0.2.0+ uses DuckDB instead of SQLite for better performance and reliability. Key changes:

**Removed:**
- `cypher()` method - Use SQL/PGQ with `query()` instead
- Cypher query language - Use SQL/PGQ (SQL:2023 standard)
- SQLite extensions - Now use DuckDB extensions

**New/Updated:**
- Property graphs use SQL/PGQ syntax
- 10-100x faster for analytics
- No corruption bugs from global state
- Same Python API for add_entity(), add_relationship(), search(), traverse()

See [SQL/PGQ documentation](https://duckpgq.org/documentation/sql_pgq/) for graph query syntax.

## License

MIT - see [LICENSE](LICENSE)
