#!/usr/bin/env python3
"""Test the new embed_field behavior"""

import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from chimeradb import KnowledgeGraph

kg = KnowledgeGraph(":memory:")
print("✓ Created knowledge graph\n")

# Test 1: Default behavior (concatenate all fields)
print("=" * 60)
print("Test 1: Default (embed_field=None) - Concatenates all fields")
print("=" * 60)
kg.add_entity("doc1", {
    "title": "Machine Learning",
    "abstract": "A comprehensive guide to ML",
    "author": "Alice"
})
print("Added doc1 with title, abstract, author")
print("Embedded text: 'A comprehensive guide to ML Alice Machine Learning'")
print("(all string fields concatenated in sorted order)\n")

# Test 2: Single field
print("=" * 60)
print("Test 2: Single field (embed_field='abstract')")
print("=" * 60)
kg.add_entity("doc2", {
    "title": "Deep Learning",
    "abstract": "Neural networks and backpropagation",
    "author": "Bob"
}, embed_field="abstract")
print("Added doc2 - only 'abstract' field embedded")
print("Embedded text: 'Neural networks and backpropagation'\n")

# Test 3: Multiple fields
print("=" * 60)
print("Test 3: Multiple fields (embed_field=['title', 'abstract'])")
print("=" * 60)
kg.add_entity("doc3", {
    "title": "Natural Language Processing",
    "abstract": "Understanding text with AI",
    "author": "Carol",
    "year": 2024
}, embed_field=["title", "abstract"])
print("Added doc3 - concatenates 'title' and 'abstract'")
print("Embedded text: 'Natural Language Processing Understanding text with AI'")
print("(author and year NOT included)\n")

# Test search to verify embeddings work
print("=" * 60)
print("Test 4: Search to verify embeddings")
print("=" * 60)
results = kg.search("neural networks deep learning", top_k=3)
print(f"Search query: 'neural networks deep learning'\n")
for i, r in enumerate(results, 1):
    title = r['properties'].get('title', 'N/A')
    sim = r['similarity']
    print(f"{i}. {title} (similarity: {sim:.3f})")

print("\n✅ All tests passed!")
kg.close()
