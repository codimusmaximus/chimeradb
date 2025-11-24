#!/usr/bin/env python3
"""
Industrial IoT Example: Heating Monitoring with Knowledge Graphs

Demonstrates how an LLM would answer: "Which rooms in Building A are using too much heating?"

This shows the three-step reasoning workflow:
1. RAG: Search knowledge graph for relevant concepts
2. Graph Traversal: Find specific entities (buildings → rooms → sensors)
3. SQL Analytics: Query and analyze data against baselines
"""

import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from chimeradb import KnowledgeGraph
import random
from datetime import datetime, timedelta

print("=" * 70)
print("Industrial IoT Example: Smart Building Heating Monitoring")
print("=" * 70)

# Create knowledge graph
kg = KnowledgeGraph("industrial_iot.db")
print("\n✓ Created knowledge graph database")

# ============================================================================
# Step 1: Build the Knowledge Graph (Ontology + Entities)
# ============================================================================

print("\n" + "=" * 70)
print("STEP 1: Building Knowledge Graph")
print("=" * 70)

# Add Building A
kg.add_entity(
    "building_a",
    {
        "name": "Building A",
        "type": "Commercial Office",
        "address": "123 Tech Park Drive",
        "description": "Modern office building with mixed-use spaces including offices, server rooms, and parking"
    },
    ["Building"],
    embed_field="description"
)
print("\n✓ Added Building A")

# Add Rooms with expected heating baselines
rooms = [
    {
        "id": "room_office_201",
        "name": "Office 201",
        "room_type": "Office",
        "floor": 2,
        "area_sqm": 20,
        "baseline_watts": 50,  # Expected heating consumption
        "description": "Standard office space with workstation and natural lighting"
    },
    {
        "id": "room_office_202",
        "name": "Office 202",
        "room_type": "Office",
        "floor": 2,
        "area_sqm": 25,
        "baseline_watts": 60,
        "description": "Corner office with large windows and meeting area"
    },
    {
        "id": "room_server",
        "name": "Server Room",
        "room_type": "Technical",
        "floor": 1,
        "area_sqm": 15,
        "baseline_watts": 0,  # No heating needed - cooled instead
        "description": "Climate-controlled server room with precision cooling system"
    },
    {
        "id": "room_garage",
        "name": "Underground Garage",
        "room_type": "Parking",
        "floor": -1,
        "area_sqm": 200,
        "baseline_watts": 0,  # No heating expected
        "description": "Underground parking garage with vehicle access"
    },
    {
        "id": "room_conference",
        "name": "Conference Room A",
        "room_type": "Meeting",
        "floor": 2,
        "area_sqm": 40,
        "baseline_watts": 100,
        "description": "Large conference room with AV equipment and seating for 20"
    }
]

for room in rooms:
    room_id = room.pop("id")
    kg.add_entity(
        room_id,
        room,
        ["Room"],
        embed_field="description"
    )
    # Connect room to building
    kg.add_relationship("building_a", room_id, "CONTAINS")
    print(f"  ✓ Added {room['name']} (baseline: {room['baseline_watts']}W)")

# Add Power Sensors
sensors = [
    {
        "id": "sensor_pwr_201",
        "sensor_type": "PowerMeter",
        "name": "PWR-201-A",
        "room_name": "Office 201",
        "measurement": "power_watts",
        "description": "Power consumption meter for office heating system"
    },
    {
        "id": "sensor_pwr_202",
        "sensor_type": "PowerMeter",
        "name": "PWR-202-A",
        "room_name": "Office 202",
        "measurement": "power_watts",
        "description": "Power consumption meter for corner office HVAC"
    },
    {
        "id": "sensor_pwr_server",
        "sensor_type": "PowerMeter",
        "name": "PWR-SRV-01",
        "room_name": "Server Room",
        "measurement": "power_watts",
        "description": "Power meter for server room cooling system"
    },
    {
        "id": "sensor_pwr_garage",
        "sensor_type": "PowerMeter",
        "name": "PWR-GAR-01",
        "room_name": "Underground Garage",
        "measurement": "power_watts",
        "description": "Power meter for garage ventilation and lighting"
    },
    {
        "id": "sensor_pwr_conf",
        "sensor_type": "PowerMeter",
        "name": "PWR-CONF-A",
        "room_name": "Conference Room A",
        "measurement": "power_watts",
        "description": "Power meter for conference room climate control"
    }
]

print()
for sensor in sensors:
    sensor_id = sensor.pop("id")
    kg.add_entity(
        sensor_id,
        sensor,
        ["Sensor", "PowerMeter"],
        embed_field="description"
    )
    # Connect sensor to corresponding room
    room_mapping = {
        "Office 201": "room_office_201",
        "Office 202": "room_office_202",
        "Server Room": "room_server",
        "Underground Garage": "room_garage",
        "Conference Room A": "room_conference"
    }
    room_id = room_mapping[sensor["room_name"]]
    kg.add_relationship(room_id, sensor_id, "MONITORED_BY")
    print(f"  ✓ Added sensor {sensor['name']} → {sensor['room_name']}")

# ============================================================================
# Add Timeseries Data (NOT embedded - stored in separate table)
# ============================================================================

print("\n" + "=" * 70)
print("Adding Timeseries Data (No Embeddings)")
print("=" * 70)

# Create a separate table for timeseries data - NOT in the knowledge graph
kg.conn.execute("""
    CREATE TABLE IF NOT EXISTS power_readings (
        sensor_id VARCHAR,
        timestamp TIMESTAMP,
        power_watts FLOAT,
        temperature_celsius FLOAT
    )
""")
print("\n✓ Created power_readings table (separate from knowledge graph)")

# Insert simulated timeseries data for the past 7 days
from datetime import datetime, timedelta
import random

print("✓ Inserting simulated readings for past 7 days...")

# Simulate readings: Office 201 and Conference Room using too much power
sensor_configs = {
    'sensor_pwr_201': {'mean': 95, 'std': 10},      # OVERUSE
    'sensor_pwr_202': {'mean': 55, 'std': 8},       # OK
    'sensor_pwr_server': {'mean': 5, 'std': 2},     # OK (minimal)
    'sensor_pwr_garage': {'mean': 2, 'std': 1},     # OK (minimal)
    'sensor_pwr_conf': {'mean': 145, 'std': 15}     # OVERUSE
}

base_time = datetime.now() - timedelta(days=7)
readings = []

for sensor_id, config in sensor_configs.items():
    # Generate hourly readings for 7 days
    for hour in range(7 * 24):
        timestamp = base_time + timedelta(hours=hour)
        power = max(0, random.gauss(config['mean'], config['std']))
        temp = random.gauss(21, 2)  # Room temperature
        readings.append((sensor_id, timestamp, power, temp))

# Batch insert for efficiency
kg.conn.executemany("""
    INSERT INTO power_readings (sensor_id, timestamp, power_watts, temperature_celsius)
    VALUES (?, ?, ?, ?)
""", readings)

print(f"✓ Inserted {len(readings)} timeseries readings (NOT embedded)")
print(f"  → {len(sensor_configs)} sensors × 168 hours = {len(readings)} data points")
print("  → Timeseries data is stored separately and NOT embedded")
print("  → Only metadata (rooms, sensors) are embedded for semantic search")

print("\n✓ Knowledge graph built with 1 building, 5 rooms, 5 sensors")
print(f"✓ Timeseries table has {len(readings)} readings")

# ============================================================================
# Step 2: LLM Reasoning Workflow - Answer "Which rooms use too much heating?"
# ============================================================================

print("\n" + "=" * 70)
print("STEP 2: LLM Reasoning Workflow")
print("=" * 70)
print("\nUser Question: 'Which rooms in Building A are using too much heating?'\n")

# ---------- Step 2.1: RAG - Search for relevant concepts ----------
print("─" * 70)
print("Step 2.1: RAG - Search Knowledge Graph for Relevant Concepts")
print("─" * 70)

search_query = "heating power consumption room sensor monitoring"
concepts = kg.search(search_query, top_k=8)

print(f"\nQuery: '{search_query}'")
print(f"Found {len(concepts)} relevant entities:\n")

for i, entity in enumerate(concepts[:5], 1):
    name = entity['properties'].get('name', entity['id'])
    labels = ', '.join(entity.get('labels', []))
    similarity = entity['similarity']
    print(f"  {i}. {name:30s} [{labels:20s}] (similarity: {similarity:.3f})")

print("\n✓ LLM now knows: Buildings have Rooms, Rooms have Sensors, Sensors measure power")

# ---------- Step 2.2: Graph Traversal - Find specific entities ----------
print("\n" + "─" * 70)
print("Step 2.2: Graph Traversal - Find Specific Entities")
print("─" * 70)

# Traverse from Building A to find all rooms
building_rooms = kg.traverse("building_a", direction="outgoing", relation_type="CONTAINS")
print(f"\nBuilding A contains {len(building_rooms)} rooms:")
for room in building_rooms:
    print(f"  - {room['properties']['name']}")

# For each room, find its sensors and baseline
print("\nFinding sensors and baselines for each room:\n")

room_sensor_map = []
for room in building_rooms:
    room_id = room['id']
    room_name = room['properties']['name']
    baseline = room['properties']['baseline_watts']
    room_type = room['properties']['room_type']

    # Get sensors for this room
    sensors = kg.traverse(room_id, direction="outgoing", relation_type="MONITORED_BY")

    for sensor in sensors:
        sensor_name = sensor['properties']['name']
        room_sensor_map.append({
            'room_id': room_id,
            'room_name': room_name,
            'room_type': room_type,
            'sensor_id': sensor['id'],
            'sensor_name': sensor_name,
            'baseline': baseline
        })
        print(f"  {room_name:25s} → {sensor_name:15s} (baseline: {baseline}W, type: {room_type})")

print(f"\n✓ Mapped {len(room_sensor_map)} room-sensor relationships")

# ---------- Step 2.3: SQL Analytics - Query and analyze ----------
print("\n" + "─" * 70)
print("Step 2.3: SQL Analytics - Join Knowledge Graph with Timeseries Data")
print("─" * 70)

# THIS IS THE KEY: Join knowledge graph (nodes) with timeseries (power_readings)
# The knowledge graph provides context (room names, baselines, room types)
# The timeseries table provides actual measurements
print("\nJoining knowledge graph with timeseries data using SQL:\n")

query_results = kg.query("""
    WITH sensor_averages AS (
        -- Aggregate timeseries data
        SELECT
            sensor_id,
            AVG(power_watts) as avg_power,
            MAX(power_watts) as max_power,
            MIN(power_watts) as min_power
        FROM power_readings
        WHERE timestamp >= NOW() - INTERVAL '7 days'
        GROUP BY sensor_id
    )
    -- Join with knowledge graph to get room context
    SELECT
        json_extract_string(room.properties, 'name') as room_name,
        json_extract_string(room.properties, 'room_type') as room_type,
        CAST(json_extract_string(room.properties, 'baseline_watts') AS INTEGER) as baseline,
        CAST(sa.avg_power AS INTEGER) as current_avg,
        CAST(sa.max_power AS INTEGER) as max_reading,
        sensor.id as sensor_id
    FROM nodes room
    JOIN edges e ON e.from_id = room.id AND e.edge_type = 'MONITORED_BY'
    JOIN nodes sensor ON sensor.id = e.to_id
    JOIN sensor_averages sa ON sa.sensor_id = sensor.id
    WHERE room.labels LIKE '%Room%'
    ORDER BY current_avg DESC
""")

print("Room Power Analysis (7-day average):\n")

overuse_rooms = []
for room_name, room_type, baseline, current_avg, max_reading, sensor_id in query_results:
    excess = current_avg - baseline
    status = "⚠️  OVERUSE" if excess > baseline * 0.1 and baseline > 0 else "✓ OK"

    print(f"  {room_name:25s}: {current_avg:3d}W (baseline: {baseline:3d}W, max: {max_reading:3d}W) [{status}]")

    if excess > baseline * 0.1 and baseline > 0:
        overuse_rooms.append({
            'room': room_name,
            'current': current_avg,
            'baseline': baseline,
            'excess': excess,
            'percent_over': (excess / baseline * 100)
        })

print("\n💡 Key Insight:")
print("   Knowledge graph provides: room names, baselines, room types (EMBEDDED)")
print("   Timeseries table provides: actual power readings (NOT EMBEDDED)")
print("   SQL joins them together for analysis")

# ============================================================================
# Step 3: LLM Generates Answer
# ============================================================================

print("\n" + "=" * 70)
print("STEP 3: LLM Answer")
print("=" * 70)

if overuse_rooms:
    print(f"\n🔍 Found {len(overuse_rooms)} room(s) with excessive heating:\n")
    for room_info in overuse_rooms:
        print(f"  • {room_info['room']}:")
        print(f"      Current:  {room_info['current']}W")
        print(f"      Baseline: {room_info['baseline']}W")
        print(f"      Excess:   +{room_info['excess']}W ({room_info['percent_over']:.1f}% over baseline)")
        print()

    print("💡 Recommendations:")
    print("  - Check thermostat settings in these rooms")
    print("  - Verify window/door seals for heat loss")
    print("  - Consider HVAC system maintenance")
else:
    print("\n✓ All rooms are within expected heating baselines")

# ============================================================================
# Bonus: Show SQL/PGQ Pattern Matching
# ============================================================================

print("\n" + "=" * 70)
print("BONUS: SQL/PGQ Pattern Matching")
print("=" * 70)

print("\nFind all Office rooms with their sensors using SQL/PGQ:\n")

results = kg.query("""
    SELECT *
    FROM GRAPH_TABLE (knowledge_graph
        MATCH (b:nodes)-[contains:edges]->(r:nodes)-[monitored:edges]->(s:nodes)
        WHERE b.id = 'building_a'
          AND r.labels LIKE '%Room%'
          AND json_extract_string(r.properties, 'room_type') = 'Office'
        COLUMNS (
            json_extract_string(r.properties, 'name') as room_name,
            json_extract_string(r.properties, 'baseline_watts') as baseline,
            json_extract_string(s.properties, 'name') as sensor_name
        )
    )
""")

for room_name, baseline, sensor_name in results:
    print(f"  {room_name} ({baseline}W baseline) → {sensor_name}")

# ============================================================================
# Bonus: Show the data architecture
# ============================================================================

print("\n" + "=" * 70)
print("DATA ARCHITECTURE: Embedded vs. Non-Embedded Data")
print("=" * 70)

print("\nWhat gets EMBEDDED (stored in nodes table with vector embeddings):")
print("  ✓ Buildings, Rooms, Sensors (metadata)")
print("  ✓ Descriptions and context for semantic search")
print("  ✓ Baselines, room types, configuration")
print("  → Total: 11 entities with embeddings")

print("\nWhat does NOT get embedded (stored in separate tables):")
print("  ✓ Timeseries data (power_readings table)")
print("  ✓ 840 readings × no embeddings = efficient storage")
print("  → Columnar DuckDB format for fast aggregation")

print("\nHow they connect:")
print("  • Join using sensor_id as foreign key")
print("  • Knowledge graph provides context")
print("  • Timeseries provides actual measurements")

# Show table sizes
node_count = kg.query("SELECT COUNT(*) FROM nodes")[0][0]
reading_count = kg.query("SELECT COUNT(*) FROM power_readings")[0][0]

print(f"\nStorage efficiency:")
print(f"  • Nodes table: {node_count} entities (WITH embeddings)")
print(f"  • Timeseries table: {reading_count} readings (NO embeddings)")
print(f"  • Embeddings only where needed for semantic search!")

# Close database
kg.close()
print("\n" + "=" * 70)
print("✅ Industrial IoT Example Complete!")
print("=" * 70)
print("\nKey Takeaway:")
print("The LLM combined RAG (finding concepts) + Graph Traversal (finding entities)")
print("+ SQL Analytics (comparing to baselines) to answer a complex data question.")
print("\nData Architecture:")
print("• Metadata (buildings, rooms, sensors) = EMBEDDED for semantic search")
print("• Timeseries (readings over time) = NOT EMBEDDED, stored separately")
print("• SQL joins them together for efficient analysis")
print("=" * 70)
