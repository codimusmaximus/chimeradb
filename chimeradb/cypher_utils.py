"""
Utilities for working with Cypher query results
"""
import re
from typing import List, Tuple


def extract_node_ids(cypher_result: str) -> List[int]:
    """
    Extract node IDs from Cypher result string.

    Cypher returns results like: [{"p":Node(1)},{"p":Node(2)}]
    This extracts the node IDs: [1, 2]

    Args:
        cypher_result: Raw result string from cypher_execute()

    Returns:
        List of node IDs as integers
    """
    matches = re.findall(r'Node\((\d+)\)', cypher_result)
    return [int(nid) for nid in matches]


def extract_relationship_ids(cypher_result: str) -> List[int]:
    """
    Extract relationship IDs from Cypher result string.

    Cypher returns results like: [{"r":Relationship(1)}]
    This extracts the relationship IDs: [1]

    Args:
        cypher_result: Raw result string from cypher_execute()

    Returns:
        List of relationship IDs as integers
    """
    matches = re.findall(r'Relationship\((\d+)\)', cypher_result)
    return [int(rid) for rid in matches]


def parse_cypher_result(cypher_result: str) -> Tuple[List[int], List[int]]:
    """
    Parse Cypher result to extract both node and relationship IDs.

    Args:
        cypher_result: Raw result string from cypher_execute()

    Returns:
        Tuple of (node_ids, relationship_ids)
    """
    node_ids = extract_node_ids(cypher_result)
    rel_ids = extract_relationship_ids(cypher_result)
    return node_ids, rel_ids
