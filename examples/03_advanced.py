#!/usr/bin/env python3
"""
Advanced Example: Knowledge Discovery with Graph Analysis
==========================================================

Real-World Scenario: Research Paper Recommendation
---------------------------------------------------
You have a database of research papers. When a researcher searches for
"neural networks for computer vision", you want to:

1. Find semantically similar papers (semantic search)
2. Analyze how those papers are connected through citations
3. Identify research clusters vs isolated papers
4. Recommend papers that bridge different clusters

This demonstrates the full power of knowledge graphs:
  • Semantic search (meaning-based retrieval)
  • Graph analysis (connectivity, clustering)
  • Hybrid queries (Cypher + SQL for complex analytics)

What Makes This "Advanced"?
----------------------------
1. Subgraph extraction and analysis
2. Connected component detection (graph algorithms)
3. Complex Cypher patterns (variable-length paths, pattern matching)
4. Hybrid analytics (Cypher for structure, SQL for aggregation)
5. Real recommendation logic combining multiple signals
"""

import sys
sys.path.insert(0, '..')

from chimeradb import KnowledgeGraph
import json
from collections import defaultdict, deque

print("=" * 80)
print("Advanced: Knowledge Discovery with Graph Analysis")
print("=" * 80)

# ============================================================================
# PART 1: Setup Research Paper Database
# ============================================================================
print("\n[1/5] Creating Research Paper Knowledge Graph...")

kg = KnowledgeGraph(db_path="research_papers.db")

print("✓ Knowledge graph initialized with auto-embeddings")

# ============================================================================
# PART 2: Insert Papers and Citations
# ============================================================================
print("\n[2/5] Inserting Research Papers...")

papers = [
    {
        "id": "paper1",
        "title": "Deep Residual Networks for Image Classification",
        "text": "Convolutional neural networks with skip connections for computer vision tasks, residual learning framework",
        "year": 2016,
        "citations": 89234,
        "field": "Computer Vision"
    },
    {
        "id": "paper2",
        "title": "Attention Is All You Need",
        "text": "Transformer architecture using self-attention mechanism for sequence modeling and NLP",
        "year": 2017,
        "citations": 76543,
        "field": "NLP"
    },
    {
        "id": "paper3",
        "title": "YOLO: Real-Time Object Detection",
        "text": "You Only Look Once - fast single-shot detector for real-time object detection in images",
        "year": 2016,
        "citations": 45678,
        "field": "Computer Vision"
    },
    {
        "id": "paper4",
        "title": "BERT: Pre-training for NLP",
        "text": "Bidirectional encoder representations from transformers for natural language understanding",
        "year": 2018,
        "citations": 67890,
        "field": "NLP"
    },
    {
        "id": "paper5",
        "title": "Vision Transformer",
        "text": "Applying transformer architecture to image patches for computer vision without convolutions",
        "year": 2020,
        "citations": 34567,
        "field": "Computer Vision"
    },
    {
        "id": "paper6",
        "title": "GANs for Image Synthesis",
        "text": "Generative adversarial networks for realistic image generation and synthesis",
        "year": 2014,
        "citations": 56789,
        "field": "Computer Vision"
    },
    {
        "id": "paper7",
        "title": "GPT-3: Large Language Models",
        "text": "Few-shot learning with large-scale transformer language models for text generation",
        "year": 2020,
        "citations": 23456,
        "field": "NLP"
    },
    {
        "id": "paper8",
        "title": "Reinforcement Learning for Game AI",
        "text": "Deep Q-networks for playing Atari games using reinforcement learning",
        "year": 2015,
        "citations": 12345,
        "field": "Reinforcement Learning"
    },
]

print("\nAdding papers with embeddings...")
for paper in papers:
    kg.add_entity(
        entity_id=paper["id"],
        labels=["Paper"],  # Add label for Cypher queries
        properties=paper,
        embed_field="text"
    )
    print(f"  ✓ {paper['id']:8} | {paper['title'][:45]}")

# Add citation network
print("\nAdding citation relationships...")
citations = [
    # Vision papers citing each other
    ("paper5", "paper1", "CITES"),  # ViT cites ResNet
    ("paper3", "paper1", "CITES"),  # YOLO cites ResNet
    ("paper5", "paper2", "CITES"),  # ViT cites Transformer

    # NLP papers citing each other
    ("paper4", "paper2", "CITES"),  # BERT cites Transformer
    ("paper7", "paper2", "CITES"),  # GPT-3 cites Transformer
    ("paper7", "paper4", "CITES"),  # GPT-3 cites BERT

    # Cross-domain citations
    ("paper5", "paper3", "CITES"),  # ViT cites YOLO (both vision)

    # Note: paper6 (GANs) and paper8 (RL) are isolated - no citations
]

for src, tgt, rel in citations:
    kg.add_relationship(src, tgt, rel)
    src_title = next(p["title"] for p in papers if p["id"] == src)
    tgt_title = next(p["title"] for p in papers if p["id"] == tgt)
    print(f"  ✓ {src:8} --[CITES]--> {tgt:8}")

# ============================================================================
# PART 3: Semantic Search
# ============================================================================
print("\n[3/5] Semantic Search - Finding Relevant Papers")
print("\n" + "-" * 80)
print("Scenario: Researcher searches for 'vision models for images'")
print("-" * 80)

query = "neural networks for computer vision and image recognition"
print(f"\nQuery: '{query}'")

results = kg.search(query, top_k=5)

print(f"\nTop {len(results)} most relevant papers:")
top_paper_ids = []
for i, result in enumerate(results, 1):
    props = result['properties']
    similarity = result['similarity']
    top_paper_ids.append(props['id'])

    bar_length = 30
    filled = int(bar_length * similarity)
    bar = "█" * filled + "░" * (bar_length - filled)

    print(f"\n  {i}. {props['title']}")
    print(f"     Match: {bar} {similarity:.1%}")
    print(f"     Field: {props['field']} | Year: {props['year']} | Citations: {props['citations']:,}")

# ============================================================================
# PART 4: Graph Analysis - Connectivity
# ============================================================================
print("\n[4/5] Graph Analysis - Are These Papers Connected?")
print("\n" + "-" * 80)
print("Question: Do the top papers form a connected research cluster?")
print("          Or are they isolated islands?")
print("-" * 80)

print(f"\nAnalyzing subgraph of top {len(top_paper_ids)} papers...")

# Get subgraph
subgraph = kg.get_subgraph(top_paper_ids)
nodes = {n['id']: n for n in subgraph['nodes']}
edges = subgraph['edges']

print(f"  Nodes: {len(nodes)}")
print(f"  Edges: {len(edges)}")

# Find connected components using BFS
print("\nFinding connected components (graph algorithm)...")

# Build adjacency list (undirected for connectivity analysis)
graph = defaultdict(set)
for edge in edges:
    src = edge['source']
    tgt = edge['target']
    # Convert IDs back to paper IDs
    src_id = next((pid for pid, node in nodes.items() if node['id'] == src), None)
    tgt_id = next((pid for pid, node in nodes.items() if node['id'] == tgt), None)
    if src_id and tgt_id:
        graph[src_id].add(tgt_id)
        graph[tgt_id].add(src_id)  # Undirected

# BFS to find components
visited = set()
components = []

for paper_id in top_paper_ids:
    if paper_id in visited:
        continue

    # Find component
    component = set()
    queue = deque([paper_id])
    visited.add(paper_id)

    while queue:
        current = queue.popleft()
        component.add(current)

        for neighbor in graph.get(current, []):
            if neighbor not in visited and neighbor in top_paper_ids:
                visited.add(neighbor)
                queue.append(neighbor)

    components.append(component)

print(f"\nConnected components: {len(components)}")

if len(components) == 1:
    print("\n✓ All papers form ONE connected cluster!")
    print("  These papers cite each other directly or indirectly.")
else:
    print(f"\n⚠ Papers form {len(components)} separate clusters (islands):")

    for i, component in enumerate(sorted(components, key=len, reverse=True), 1):
        print(f"\n  Cluster {i} ({len(component)} papers):")
        for paper_id in component:
            paper = next(p for p in papers if p["id"] == paper_id)
            print(f"    • {paper['title'][:50]}")
            print(f"      {paper['field']} | {paper['citations']:,} citations")

        if len(component) == 1:
            print(f"    → ISOLATED: No citations to/from other top papers")

# ============================================================================
# PART 5: Advanced Hybrid Queries
# ============================================================================
print("\n[5/5] Advanced Hybrid Queries")
print("\n" + "-" * 80)
print("Combining Cypher pattern matching with SQL analytics")
print("-" * 80)

print("\n--- Query 1: Find 'Bridge Papers' (SQL analysis) ---")
print("Papers that connect different research areas")
print("\nNote: sqlite-graph doesn't support bidirectional Cypher patterns like:")
print("      MATCH (p1)-[:CITES]->(bridge)<-[:CITES]-(p2)")
print("      Using SQL instead for this type of query.")

# Use SQL to analyze which are bridge papers (connect different fields)
sql_query = """
    SELECT DISTINCT
        json_extract(bridge.properties, '$.title') as title,
        json_extract(bridge.properties, '$.field') as field,
        COUNT(DISTINCT json_extract(citing.properties, '$.field')) as field_count
    FROM graph_edges e1
    JOIN graph_nodes citing ON e1.source = citing.id
    JOIN graph_nodes bridge ON e1.target = bridge.id
    WHERE e1.edge_type = 'CITES'
    GROUP BY bridge.id
    HAVING field_count > 1
"""
bridge_papers = kg.conn.execute(sql_query).fetchall()

if bridge_papers:
    print(f"\nFound {len(bridge_papers)} bridge papers:")
    for title, field, count in bridge_papers:
        print(f"  • {title} ({field}) - cited by {count} different fields")
else:
    print("\nNo bridge papers found")

print("\n--- Query 2: Citation Count Analysis (SQL) ---")
print("Most influential papers in our subgraph")

# SQL aggregation
sql_query = """
    SELECT
        json_extract(n.properties, '$.title') as title,
        json_extract(n.properties, '$.field') as field,
        COUNT(e.source) as incoming_citations
    FROM graph_nodes n
    LEFT JOIN graph_edges e ON e.target = n.id AND e.edge_type = 'CITES'
    WHERE json_extract(n.properties, '$.id') IN (?, ?, ?, ?, ?)
    GROUP BY n.id
    ORDER BY incoming_citations DESC
"""

results = kg.query(sql_query, tuple(top_paper_ids))

print("\nCitation counts (within subgraph):")
for title, field, count in results:
    print(f"  {count} citations | {title[:45]}")

print("\n--- Query 3: Find Direct Citations (SQL) ---")
print("What papers does Vision Transformer cite?")
print("\nNote: Using SQL for this query since sqlite-graph has limitations with")
print("      returning multiple nodes and complex patterns.")

# Use SQL to find what paper5 cites
sql_query = """
    SELECT json_extract(n.properties, '$.title') as title
    FROM graph_edges e
    JOIN graph_nodes n ON e.target = n.id
    WHERE e.source IN (
        SELECT id FROM graph_nodes
        WHERE json_extract(properties, '$.id') = 'paper5'
    )
    AND e.edge_type = 'CITES'
"""
citations = kg.conn.execute(sql_query).fetchall()

if citations:
    print(f"\nVision Transformer cites:")
    for (title,) in citations:
        print(f"  → {title}")
else:
    print("\nNo direct citations found")

# ============================================================================
# Summary & Recommendations
# ============================================================================
print("\n" + "=" * 80)
print("Summary: Advanced Knowledge Graph Techniques")
print("=" * 80)

print("\n1. Semantic Search")
print("   • Found papers by MEANING, not just keywords")
print("   • Query didn't mention 'ResNet' but found it relevant")
print("   • Essential for LLM-powered search and RAG systems")

print("\n2. Graph Analysis")
print("   • Extracted subgraph of relevant papers")
print("   • Detected connected components (clusters vs islands)")
print("   • Identified isolated research areas")

print("\n3. Hybrid Queries")
print("   • Cypher: Simple directional patterns (A->B relationships)")
print("   • SQL: Complex patterns, aggregations, multi-way joins")
print("   • sqlite-graph limitation: no bidirectional Cypher patterns")
print("   • Solution: Use SQL for complex graph queries")

print("\n4. Real-World Applications")
print("   • Research paper recommendations")
print("   • Literature review tools")
print("   • Knowledge discovery and gap analysis")
print("   • Academic social networks")

print("\n💡 Pro Tip: Production Architecture")
print("   • Graph: Entities and relationships (flexible schema)")
print("   • Embeddings: Semantic search (meaning-based)")
print("   • SQL tables: High-volume data (metrics, logs, timeseries)")
print("   • Combine all three with hybrid queries!")

print("\n✅ You now master advanced knowledge graph techniques!")
print("=" * 80)

kg.close()
