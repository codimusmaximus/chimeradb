"""
ChimeraDB Knowledge Graph

Semantic search + graph queries + SQL analytics in one database.
Powered by DuckDB for production-grade performance and reliability.
"""

import duckdb
import json
from typing import List, Dict, Any, Optional, Tuple, Callable
import warnings

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

class KnowledgeGraph:
    """
    A unified database combining:
    - Property graphs (SQL/PGQ standard for graph pattern matching)
    - Vector embeddings (HNSW indexing for semantic search)
    - Full SQL analytics (DuckDB's columnar engine)

    All in a single DuckDB file with zero infrastructure.
    """

    def __init__(
        self,
        db_path: str = ":memory:",
        embedding_model: Optional[str] = "distilbert-base-uncased",
        embedding_function: Optional[Callable[[str], List[float]]] = None,
        auto_embed: bool = True
    ):
        """
        Initialize Knowledge Graph with DuckDB backend.

        Args:
            db_path: Path to database file, or ":memory:" for in-memory
            embedding_model: HuggingFace transformers model name (e.g., "distilbert-base-uncased"), or None to disable
            embedding_function: Custom function that takes text and returns embedding vector
            auto_embed: Automatically generate embeddings for new nodes
        """
        self.db_path = db_path
        self.embedding_model_name = embedding_model
        self.tokenizer = None
        self.model = None
        self.embedding_function = embedding_function
        self.embedding_dim = None

        # Priority: custom function > model name > disable
        if embedding_function is not None:
            # Use custom embedding function
            self.auto_embed = True
            try:
                # Detect embedding dimension by running a test
                test_emb = embedding_function("test")
                self.embedding_dim = len(test_emb)
            except Exception as e:
                warnings.warn(f"Failed to test custom embedding function: {e}")
                self.auto_embed = False
        elif embedding_model:
            # Use HuggingFace transformers
            self.auto_embed = auto_embed
            try:
                if not TORCH_AVAILABLE:
                    raise ImportError("PyTorch not available")

                from transformers import AutoTokenizer, AutoModel
                self.tokenizer = AutoTokenizer.from_pretrained(embedding_model)
                self.model = AutoModel.from_pretrained(embedding_model)

                # Get embedding dimension
                test_emb = self._encode_text("test")
                self.embedding_dim = len(test_emb)
            except ImportError as e:
                warnings.warn(
                    f"transformers or torch not installed. Install with: "
                    f"pip install transformers torch. Error: {e}"
                )
                self.auto_embed = False
            except Exception as e:
                warnings.warn(f"Failed to load embedding model '{embedding_model}': {e}")
                self.auto_embed = False
        else:
            # Embeddings disabled
            self.auto_embed = False

        # Connect to DuckDB with HNSW persistence enabled
        config = {}
        if db_path != ":memory:":
            config['hnsw_enable_experimental_persistence'] = 'true'

        self.conn = duckdb.connect(db_path, config=config)

        # Install and load extensions
        self._setup_extensions()

        # Initialize schema
        self._init_schema()

    def _setup_extensions(self):
        """Install and load DuckDB extensions."""
        extensions_loaded = {"duckpgq": False, "vss": False}

        # Try to load duckpgq
        try:
            self.conn.execute("INSTALL duckpgq FROM community")
            self.conn.execute("LOAD duckpgq")
            extensions_loaded["duckpgq"] = True
        except Exception as e:
            raise RuntimeError(
                f"Failed to load duckpgq extension. ChimeraDB requires duckpgq for "
                f"graph queries. Error: {e}"
            )

        # Try to load vss
        try:
            self.conn.execute("INSTALL vss")
            self.conn.execute("LOAD vss")
            extensions_loaded["vss"] = True
        except Exception as e:
            raise RuntimeError(
                f"Failed to load vss extension. ChimeraDB requires vss for "
                f"vector similarity search. Error: {e}"
            )

    def _init_schema(self):
        """Initialize database schema with nodes, edges, and property graph."""
        emb_type = f"FLOAT[{self.embedding_dim}]" if self.embedding_dim else "FLOAT[]"

        # Create nodes table
        self.conn.execute(f"""
            CREATE TABLE IF NOT EXISTS nodes (
                id VARCHAR PRIMARY KEY,
                labels VARCHAR,  -- JSON array of labels
                properties JSON,
                embedding {emb_type}
            )
        """)

        # Create edges table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS edges (
                from_id VARCHAR,
                to_id VARCHAR,
                edge_type VARCHAR,
                properties JSON,
                FOREIGN KEY (from_id) REFERENCES nodes(id),
                FOREIGN KEY (to_id) REFERENCES nodes(id)
            )
        """)

        # Create HNSW index for vector similarity if embeddings enabled
        if self.embedding_dim:
            try:
                self.conn.execute("""
                    CREATE INDEX IF NOT EXISTS nodes_embedding_idx
                    ON nodes USING HNSW (embedding)
                """)
            except Exception:
                pass  # Index might already exist

        # Create property graph
        try:
            self.conn.execute("""
                CREATE OR REPLACE PROPERTY GRAPH knowledge_graph
                VERTEX TABLES (nodes)
                EDGE TABLES (
                    edges
                    SOURCE KEY (from_id) REFERENCES nodes (id)
                    DESTINATION KEY (to_id) REFERENCES nodes (id)
                )
            """)
        except Exception as e:
            raise RuntimeError(
                f"Failed to create property graph. This typically means duckpgq extension "
                f"is not available. Error: {e}"
            )

    def _encode_text(self, text: str) -> List[float]:
        """
        Encode text using HuggingFace transformers with mean pooling.

        Args:
            text: Text to encode

        Returns:
            Embedding vector as list of floats
        """
        if not self.tokenizer or not self.model:
            raise ValueError("No tokenizer or model available")

        # Tokenize
        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=512
        )

        # Generate embeddings
        with torch.no_grad():
            outputs = self.model(**inputs)

        # Mean pooling
        embeddings = outputs.last_hidden_state.mean(dim=1)

        # Convert to list
        return embeddings[0].tolist()

    def add_entity(
        self,
        entity_id: str,
        properties: Dict[str, Any],
        labels: Optional[List[str]] = None,
        embedding: Optional[List[float]] = None,
        auto_embed: Optional[bool] = None,
        embed_field: str = "text"
    ) -> str:
        """
        Add a node to the graph.

        Args:
            entity_id: Unique identifier for the node
            properties: Dictionary of node properties
            labels: List of labels/types for the node
            embedding: Pre-computed embedding vector
            auto_embed: Override default auto_embed setting
            embed_field: Property field to use for embedding generation

        Returns:
            entity_id
        """
        labels = labels or []
        labels_json = json.dumps(labels)
        properties_json = json.dumps(properties)

        # Generate embedding if requested
        should_embed = (auto_embed if auto_embed is not None else self.auto_embed)
        if should_embed and embedding is None and embed_field in properties:
            text = properties[embed_field]
            if text:
                # Use custom function if provided
                if self.embedding_function:
                    embedding = self.embedding_function(text)
                # Otherwise use transformers
                elif self.tokenizer and self.model:
                    embedding = self._encode_text(text)

        # Insert or update node
        self.conn.execute("""
            INSERT OR REPLACE INTO nodes (id, labels, properties, embedding)
            VALUES (?, ?, ?::JSON, ?)
        """, [entity_id, labels_json, properties_json, embedding])

        return entity_id

    def add_relationship(
        self,
        from_id: str,
        to_id: str,
        relation_type: str,
        properties: Optional[Dict[str, Any]] = None
    ):
        """
        Add an edge between two nodes.

        Args:
            from_id: Source node ID
            to_id: Target node ID
            relation_type: Type/label of the relationship
            properties: Optional edge properties
        """
        properties = properties or {}
        properties_json = json.dumps(properties)

        self.conn.execute("""
            INSERT INTO edges (from_id, to_id, edge_type, properties)
            VALUES (?, ?, ?, ?::JSON)
        """, [from_id, to_id, relation_type, properties_json])

    def search(
        self,
        query: str,
        top_k: int = 10,
        labels: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Semantic search using vector similarity.

        Args:
            query: Search query text
            top_k: Number of results to return
            labels: Optional filter by node labels

        Returns:
            List of matching nodes with similarity scores
        """
        if not self.tokenizer and not self.model and not self.embedding_function:
            raise ValueError("No embedding model or function configured")

        # Generate query embedding using custom function or transformers
        if self.embedding_function:
            query_emb = self.embedding_function(query)
        elif self.tokenizer and self.model:
            query_emb = self._encode_text(query)

        # Build label filter
        label_filter = ""
        if labels:
            label_conditions = " OR ".join([f"labels LIKE '%{label}%'" for label in labels])
            label_filter = f"WHERE ({label_conditions})"

        # Search with vector similarity
        results = self.conn.execute(f"""
            SELECT
                id,
                labels,
                properties,
                1.0 - (array_distance(embedding, ?::FLOAT[{self.embedding_dim}]) / 10.0) as similarity
            FROM nodes
            {label_filter}
            ORDER BY array_distance(embedding, ?::FLOAT[{self.embedding_dim}])
            LIMIT ?
        """, [query_emb, query_emb, top_k]).fetchall()

        return [
            {
                "id": row[0],
                "labels": json.loads(row[1]) if row[1] else [],
                "properties": json.loads(row[2]) if row[2] else {},
                "similarity": max(0.0, row[3]) if row[3] else 0.0
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
            start_id: Starting node ID
            relation_type: Optional relationship type to follow
            max_depth: Maximum traversal depth
            direction: "outgoing", "incoming", or "both"

        Returns:
            List of reachable nodes with depth info
        """
        # Build CTE based on direction
        if direction == "outgoing":
            join_cond = "c.id = e.from_id"
            next_id = "e.to_id"
        elif direction == "incoming":
            join_cond = "c.id = e.to_id"
            next_id = "e.from_id"
        else:  # both
            join_cond = "(c.id = e.from_id OR c.id = e.to_id)"
            next_id = "CASE WHEN c.id = e.from_id THEN e.to_id ELSE e.from_id END"

        rel_filter = f"AND e.edge_type = '{relation_type}'" if relation_type else ""

        query = f"""
            WITH RECURSIVE traversal(id, depth, path) AS (
                SELECT id, 0, id
                FROM nodes WHERE id = ?
                UNION
                SELECT n.id, c.depth + 1, c.path || ',' || n.id
                FROM traversal c
                JOIN edges e ON {join_cond}
                JOIN nodes n ON n.id = {next_id}
                WHERE c.depth < ? {rel_filter}
                  AND position(',' || n.id || ',' IN ',' || c.path || ',') = 0
            )
            SELECT DISTINCT t.id, t.depth, n.properties
            FROM traversal t
            JOIN nodes n ON t.id = n.id
            WHERE t.depth > 0
            ORDER BY t.depth, t.id
        """

        results = self.conn.execute(query, [start_id, max_depth]).fetchall()

        return [
            {
                "id": row[0],
                "depth": row[1],
                "properties": json.loads(row[2]) if row[2] else {}
            }
            for row in results
        ]

    def query(self, sql: str, params: Optional[Tuple] = None) -> List[Tuple]:
        """
        Execute raw SQL query.

        Args:
            sql: SQL query string
            params: Optional query parameters

        Returns:
            Query results as list of tuples
        """
        if params:
            return self.conn.execute(sql, params).fetchall()
        return self.conn.execute(sql).fetchall()

    def get_entity(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a node by ID.

        Args:
            entity_id: Node ID

        Returns:
            Node data or None if not found
        """
        result = self.conn.execute(
            "SELECT id, labels, properties FROM nodes WHERE id = ?",
            [entity_id]
        ).fetchone()

        if not result:
            return None

        return {
            "id": result[0],
            "labels": json.loads(result[1]) if result[1] else [],
            "properties": json.loads(result[2]) if result[2] else {}
        }

    def commit(self):
        """Commit transaction (no-op for DuckDB which auto-commits)."""
        pass  # DuckDB auto-commits by default

    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
