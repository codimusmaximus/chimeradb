"""
SQLite Knowledge Graph - Easy-to-use knowledge graph with vector embeddings
"""

from .knowledge_graph import KnowledgeGraph
from .embeddings import EmbeddingGenerator
from .cypher_utils import extract_node_ids, extract_relationship_ids, parse_cypher_result

__version__ = "0.1.0"
__all__ = [
    "KnowledgeGraph",
    "EmbeddingGenerator",
    "extract_node_ids",
    "extract_relationship_ids",
    "parse_cypher_result",
]
