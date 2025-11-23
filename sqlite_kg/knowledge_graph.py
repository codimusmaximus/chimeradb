"""
Main KnowledgeGraph class - High-level API for graph operations with embeddings
"""

import sqlite3
import json
import os
import sys
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path


class KnowledgeGraph:
    """
    A knowledge graph with vector embeddings for semantic search.

    Features:
    - Graph database (nodes and edges)
    - Vector embeddings on nodes
    - Semantic similarity search
    - Hybrid graph + vector queries
    """

    def __init__(
        self,
        db_path: str = ":memory:",
        embedding_model: Optional[str] = None,
        embedding_dim: int = 384,
        auto_embed: bool = False,
    ):
        """
        Initialize a knowledge graph.

        Args:
            db_path: Path to SQLite database (":memory:" for in-memory)
            embedding_model: Model name for auto-embedding (optional)
            embedding_dim: Dimension of embedding vectors
            auto_embed: Automatically generate embeddings on insert
        """
        self.db_path = db_path
        self.embedding_dim = embedding_dim
        self.auto_embed = auto_embed
        self.embedding_model = embedding_model

        # Initialize embedding generator if requested
        self.embedder = None
        if auto_embed and embedding_model:
            from .embeddings import EmbeddingGenerator

            self.embedder = EmbeddingGenerator(embedding_model)

        # Connect to database
        self.conn = sqlite3.connect(db_path)
        self.conn.enable_load_extension(True)

        # Load extensions
        self._load_extensions()

        # Initialize schema
        self._init_schema()

    def _load_extensions(self):
        """Load sqlite-graph and sqlite-vector extensions"""
        # Determine extension paths
        if sys.platform == "darwin":
            graph_ext = "extensions/libgraph"
            vector_ext = "extensions/vector"
        else:
            graph_ext = "extensions/libgraph"
            vector_ext = "extensions/vector"

        # Check if extensions exist
        ext_dir = Path(__file__).parent.parent / "extensions"

        # Try relative path first, then absolute
        possible_paths = [
            ext_dir,
            Path.cwd() / "extensions",
            Path(__file__).parent.parent.parent / "extensions",
        ]

        graph_loaded = False
        vector_loaded = False

        for base_path in possible_paths:
            if not graph_loaded:
                graph_path = base_path / (
                    "libgraph.dylib" if sys.platform == "darwin" else "libgraph.so"
                )
                if graph_path.exists():
                    try:
                        self.conn.load_extension(str(graph_path).replace(".dylib", "").replace(".so", ""))
                        graph_loaded = True
                    except sqlite3.OperationalError:
                        pass

            if not vector_loaded:
                vector_path = base_path / (
                    "vector.dylib" if sys.platform == "darwin" else "vector.so"
                )
                if vector_path.exists():
                    try:
                        self.conn.load_extension(str(vector_path).replace(".dylib", "").replace(".so", ""))
                        vector_loaded = True
                    except sqlite3.OperationalError:
                        pass

            if graph_loaded and vector_loaded:
                break

        if not graph_loaded:
            raise RuntimeError(
                "Could not load graph extension. "
                "Please run setup.sh or manually download extensions."
            )

        if not vector_loaded:
            raise RuntimeError(
                "Could not load vector extension. "
                "Please run setup.sh or manually download extensions."
            )

    def _init_schema(self):
        """Initialize database schema"""
        # Create graph virtual table
        self.conn.execute("CREATE VIRTUAL TABLE IF NOT EXISTS graph USING graph()")

        # IMPORTANT: Do NOT alter graph_nodes table - it breaks Cypher queries!
        # Instead, create a separate table for embeddings
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS node_embeddings (
                node_id INTEGER PRIMARY KEY,
                embedding BLOB,
                FOREIGN KEY (node_id) REFERENCES graph_nodes(id)
            )
        """)

        # Initialize vector search on the separate embeddings table
        try:
            self.conn.execute(
                f"SELECT vector_init('node_embeddings', 'embedding', "
                f"'type=FLOAT32,dimension={self.embedding_dim}')"
            )
        except sqlite3.OperationalError:
            # Already initialized
            pass

        self.conn.commit()

    def add_entity(
        self,
        entity_id: str,
        properties: Dict[str, Any],
        labels: Optional[List[str]] = None,
        embedding: Optional[List[float]] = None,
        auto_embed: Optional[bool] = None,
        embed_field: str = "text",
    ) -> int:
        """
        Add an entity (node) to the knowledge graph.

        Args:
            entity_id: Unique identifier for the entity
            properties: Dictionary of properties
            labels: Optional list of labels for the entity
            embedding: Optional pre-computed embedding vector
            auto_embed: Override global auto_embed setting
            embed_field: Field to use for auto-embedding

        Returns:
            Row ID of inserted entity
        """
        # Use provided embedding or generate if requested
        should_auto_embed = auto_embed if auto_embed is not None else self.auto_embed

        if embedding is None and should_auto_embed and self.embedder:
            text = properties.get(embed_field, "")
            if text:
                embedding = self.embedder.generate(text)

        # Convert entity_id to integer if needed
        try:
            node_id = int(entity_id)
        except ValueError:
            # Hash string ID to integer
            node_id = hash(entity_id) % (2**31)

        # Insert node with labels
        props_json = json.dumps(properties)
        labels_json = json.dumps(labels if labels else [])

        self.conn.execute(
            "INSERT OR REPLACE INTO graph_nodes (id, labels, properties) VALUES (?, ?, ?)",
            (node_id, labels_json, props_json),
        )

        # Add embedding if provided - store in separate table
        if embedding:
            self.conn.execute(
                "INSERT OR REPLACE INTO node_embeddings (node_id, embedding) VALUES (?, vector_as_f32(?))",
                (node_id, json.dumps(embedding)),
            )

        self.conn.commit()
        return node_id

    def add_relationship(
        self,
        from_id: str,
        to_id: str,
        relation_type: str,
        properties: Optional[Dict[str, Any]] = None,
    ) -> int:
        """
        Add a relationship (edge) between two entities.

        Args:
            from_id: Source entity ID
            to_id: Target entity ID
            relation_type: Type of relationship (e.g., "KNOWS", "WORKS_AT")
            properties: Optional properties for the relationship

        Returns:
            Row ID of inserted relationship
        """
        # Convert IDs
        try:
            from_node = int(from_id)
        except ValueError:
            from_node = hash(from_id) % (2**31)

        try:
            to_node = int(to_id)
        except ValueError:
            to_node = hash(to_id) % (2**31)

        props = properties or {}
        props_json = json.dumps(props)

        # Use direct INSERT instead of graph_edge_add function
        cursor = self.conn.execute(
            "INSERT INTO graph_edges (source, target, edge_type, properties) VALUES (?, ?, ?, ?)",
            (from_node, to_node, relation_type, props_json),
        )

        self.conn.commit()
        return cursor.lastrowid

    def search(
        self,
        query: str,
        top_k: int = 10,
        min_similarity: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """
        Semantic search for similar entities.

        Args:
            query: Search query text
            top_k: Number of results to return
            min_similarity: Minimum similarity threshold (optional)

        Returns:
            List of matching entities with similarity scores
        """
        if not self.embedder:
            raise RuntimeError(
                "Embedding model not configured. "
                "Initialize with embedding_model parameter."
            )

        # Generate query embedding
        query_embedding = self.embedder.generate(query)

        # Ensure vector quantization table is built
        try:
            self.conn.execute("SELECT vector_quantize('node_embeddings', 'embedding')")
        except sqlite3.OperationalError:
            # Already quantized
            pass

        # Search using vector similarity on separate embeddings table
        results = self.conn.execute(
            """
            SELECT n.id, n.properties, v.distance
            FROM graph_nodes n
            JOIN node_embeddings e ON n.id = e.node_id
            JOIN vector_quantize_scan('node_embeddings', 'embedding', ?, ?) v
            ON e.rowid = v.rowid
            ORDER BY v.distance ASC
            """,
            (json.dumps(query_embedding), top_k),
        ).fetchall()

        # Convert to list of dicts
        output = []
        for node_id, props_json, distance in results:
            similarity = 1.0 - distance  # Convert distance to similarity

            if min_similarity and similarity < min_similarity:
                continue

            props = json.loads(props_json) if props_json else {}
            output.append(
                {
                    "id": node_id,
                    "properties": props,
                    "similarity": similarity,
                    "distance": distance,
                }
            )

        return output

    def query(self, sql: str, params: Optional[Tuple] = None) -> List[Tuple]:
        """
        Execute a raw SQL query.

        Args:
            sql: SQL query string
            params: Optional query parameters

        Returns:
            Query results as list of tuples
        """
        if params:
            cursor = self.conn.execute(sql, params)
        else:
            cursor = self.conn.execute(sql)

        return cursor.fetchall()

    def cypher_query(self, cypher: str) -> List[int]:
        """
        Execute a Cypher query and return node IDs.

        Note: Current alpha returns Node(id) format, not full properties.
        Use the returned IDs with SQL queries to get properties.

        Example:
            # Find Person nodes
            node_ids = kg.cypher_query('MATCH (p:Person) RETURN p')

            # Get properties with SQL
            for nid in node_ids:
                node = kg.get_entity(str(nid))
                print(node)

        Args:
            cypher: Cypher query string

        Returns:
            List of node IDs found by the query
        """
        from .cypher_utils import extract_node_ids

        result = self.conn.execute("SELECT cypher_execute(?)", (cypher,)).fetchone()
        if result:
            return extract_node_ids(result[0])
        return []

    def get_entity(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Get an entity by ID"""
        try:
            node_id = int(entity_id)
        except ValueError:
            node_id = hash(entity_id) % (2**31)

        result = self.conn.execute(
            "SELECT id, properties FROM graph_nodes WHERE id = ?",
            (node_id,),
        ).fetchone()

        if result:
            return {"id": result[0], "properties": json.loads(result[1])}
        return None

    def get_neighbors(
        self, entity_id: str, relation_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get neighboring entities"""
        try:
            node_id = int(entity_id)
        except ValueError:
            node_id = hash(entity_id) % (2**31)

        if relation_type:
            query = """
                SELECT n.id, n.properties, e.edge_type
                FROM graph_edges e
                JOIN graph_nodes n ON e.target = n.id
                WHERE e.source = ? AND e.edge_type = ?
            """
            results = self.conn.execute(query, (node_id, relation_type)).fetchall()
        else:
            query = """
                SELECT n.id, n.properties, e.edge_type
                FROM graph_edges e
                JOIN graph_nodes n ON e.target = n.id
                WHERE e.source = ?
            """
            results = self.conn.execute(query, (node_id,)).fetchall()

        return [
            {
                "id": row[0],
                "properties": json.loads(row[1]) if row[1] else {},
                "relation_type": row[2],
            }
            for row in results
        ]

    def hybrid_search(
        self,
        query_text: str,
        graph_filter: str,
        top_k: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Combine graph filtering with vector search.

        Args:
            query_text: Text query for semantic search
            graph_filter: SQL WHERE clause to filter entities
            top_k: Number of results

        Returns:
            Filtered and ranked results
        """
        if not self.embedder:
            raise RuntimeError("Embedding model not configured")

        query_embedding = self.embedder.generate(query_text)

        # Ensure vector quantization table is built
        try:
            self.conn.execute("SELECT vector_quantize('node_embeddings', 'embedding')")
        except sqlite3.OperationalError:
            # Already quantized
            pass

        sql = f"""
            SELECT n.id, n.properties, v.distance
            FROM graph_nodes n
            JOIN node_embeddings e ON n.id = e.node_id
            JOIN vector_quantize_scan('node_embeddings', 'embedding', ?, ?) v
            ON e.rowid = v.rowid
            WHERE {graph_filter}
            ORDER BY v.distance ASC
        """

        results = self.conn.execute(
            sql, (json.dumps(query_embedding), top_k)
        ).fetchall()

        return [
            {
                "id": row[0],
                "properties": json.loads(row[1]) if row[1] else {},
                "similarity": 1.0 - row[2],
                "distance": row[2],
            }
            for row in results
        ]

    def traverse(
        self,
        start_id: str,
        relation_type: Optional[str] = None,
        max_depth: int = 3,
        direction: str = "outgoing"
    ) -> List[Dict[str, Any]]:
        """
        Traverse the graph from a starting node.

        Args:
            start_id: Starting entity ID
            relation_type: Optional relationship type to follow
            max_depth: Maximum traversal depth
            direction: "outgoing", "incoming", or "both"

        Returns:
            List of reachable entities with depth info
        """
        try:
            node_id = int(start_id)
        except ValueError:
            node_id = hash(start_id) % (2**31)

        # Build traversal query based on direction
        if direction == "outgoing":
            join_cond = "c.id = e.source"
            next_id = "e.target"
        elif direction == "incoming":
            join_cond = "c.id = e.target"
            next_id = "e.source"
        else:  # both
            join_cond = "c.id = e.source OR c.id = e.target"
            next_id = "(CASE WHEN c.id = e.source THEN e.target ELSE e.source END)"

        rel_filter = f"AND e.edge_type = '{relation_type}'" if relation_type else ""

        query = f"""
            WITH RECURSIVE traversal(id, depth, path) AS (
                SELECT id, 0, CAST(id AS TEXT)
                FROM graph_nodes WHERE id = ?
                UNION
                SELECT n.id, c.depth + 1, c.path || ',' || CAST(n.id AS TEXT)
                FROM traversal c
                JOIN graph_edges e ON {join_cond}
                JOIN graph_nodes n ON n.id = {next_id}
                WHERE c.depth < ? {rel_filter}
                  AND (',' || c.path || ',') NOT LIKE ('%,' || CAST(n.id AS TEXT) || ',%')
            )
            SELECT DISTINCT t.id, t.depth, n.properties
            FROM traversal t
            JOIN graph_nodes n ON t.id = n.id
            WHERE t.depth > 0
            ORDER BY t.depth, t.id
        """

        results = self.conn.execute(query, (node_id, max_depth)).fetchall()

        return [
            {
                "id": row[0],
                "depth": row[1],
                "properties": json.loads(row[2]) if row[2] else {}
            }
            for row in results
        ]

    def find_path(
        self,
        from_id: str,
        to_id: str,
        max_depth: int = 5
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Find a path between two entities.

        Args:
            from_id: Starting entity ID
            to_id: Target entity ID
            max_depth: Maximum path length

        Returns:
            Path as list of entities, or None if no path exists
        """
        try:
            from_node = int(from_id)
        except ValueError:
            from_node = hash(from_id) % (2**31)

        try:
            to_node = int(to_id)
        except ValueError:
            to_node = hash(to_id) % (2**31)

        query = """
            WITH RECURSIVE paths(id, path, depth) AS (
                SELECT id, CAST(id AS TEXT), 0
                FROM graph_nodes WHERE id = ?
                UNION
                SELECT n.id, p.path || ',' || CAST(n.id AS TEXT), p.depth + 1
                FROM paths p
                JOIN graph_edges e ON p.id = e.source OR p.id = e.target
                JOIN graph_nodes n ON (CASE WHEN p.id = e.source THEN e.target ELSE e.source END) = n.id
                WHERE p.depth < ?
                  AND (',' || p.path || ',') NOT LIKE ('%,' || CAST(n.id AS TEXT) || ',%')
                  AND n.id = ?
            )
            SELECT path FROM paths WHERE id = ? LIMIT 1
        """

        result = self.conn.execute(query, (from_node, max_depth, to_node, to_node)).fetchone()

        if not result:
            return None

        # Convert path to list of entities
        node_ids = [int(nid) for nid in result[0].split(',')]
        entities = []
        for nid in node_ids:
            entity = self.get_entity(str(nid))
            if entity:
                entities.append(entity)

        return entities

    def get_subgraph(
        self,
        node_ids: List[str]
    ) -> Dict[str, Any]:
        """
        Get subgraph containing specified nodes and edges between them.

        Args:
            node_ids: List of entity IDs

        Returns:
            Dict with 'nodes' and 'edges' lists
        """
        # Convert to integers
        int_ids = []
        for nid in node_ids:
            try:
                int_ids.append(int(nid))
            except ValueError:
                int_ids.append(hash(nid) % (2**31))

        # Get nodes
        placeholders = ','.join('?' * len(int_ids))
        nodes_query = f"SELECT id, properties FROM graph_nodes WHERE id IN ({placeholders})"
        nodes = self.conn.execute(nodes_query, int_ids).fetchall()

        # Get edges between these nodes
        edges_query = f"""
            SELECT source, target, edge_type, properties
            FROM graph_edges
            WHERE source IN ({placeholders}) AND target IN ({placeholders})
        """
        edges = self.conn.execute(edges_query, int_ids + int_ids).fetchall()

        return {
            "nodes": [
                {"id": n[0], "properties": json.loads(n[1]) if n[1] else {}}
                for n in nodes
            ],
            "edges": [
                {
                    "source": e[0],
                    "target": e[1],
                    "type": e[2],
                    "properties": json.loads(e[3]) if e[3] else {}
                }
                for e in edges
            ]
        }

    def close(self):
        """Close the database connection"""
        self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
