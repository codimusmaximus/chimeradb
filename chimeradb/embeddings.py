"""
Embedding generation utilities
"""

from typing import List, Union
import warnings


class EmbeddingGenerator:
    """Generate embeddings using various models"""

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """
        Initialize embedding generator.

        Args:
            model_name: Model name (sentence-transformers or openai)
        """
        self.model_name = model_name
        self.model = None

        if model_name.startswith("sentence-transformers/") or "/" not in model_name:
            self._init_sentence_transformer(model_name)
        elif model_name.startswith("text-embedding"):
            self._init_openai(model_name)
        else:
            raise ValueError(f"Unknown model type: {model_name}")

    def _init_sentence_transformer(self, model_name: str):
        """Initialize sentence-transformers model"""
        try:
            from sentence_transformers import SentenceTransformer

            # Remove prefix if present
            if model_name.startswith("sentence-transformers/"):
                model_name = model_name.replace("sentence-transformers/", "")

            self.model = SentenceTransformer(model_name)
            self.model_type = "sentence-transformer"
        except ImportError:
            raise ImportError(
                "sentence-transformers not installed. "
                "Install with: pip install sentence-transformers"
            )

    def _init_openai(self, model_name: str):
        """Initialize OpenAI embedding model"""
        try:
            import openai
            import os

            self.model = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            self.model_type = "openai"
        except ImportError:
            raise ImportError(
                "openai not installed. Install with: pip install openai"
            )

    def generate(self, text: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        """
        Generate embedding(s) for text.

        Args:
            text: Single text string or list of strings

        Returns:
            Embedding vector or list of embedding vectors
        """
        if isinstance(text, str):
            return self._generate_single(text)
        else:
            return self._generate_batch(text)

    def _generate_single(self, text: str) -> List[float]:
        """Generate embedding for single text"""
        if self.model_type == "sentence-transformer":
            embedding = self.model.encode(text, convert_to_numpy=True, normalize_embeddings=False)
            return embedding.tolist()

        elif self.model_type == "openai":
            response = self.model.embeddings.create(
                model=self.model_name, input=text
            )
            return response.data[0].embedding

    def _generate_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        if self.model_type == "sentence-transformer":
            embeddings = self.model.encode(texts, convert_to_numpy=True, normalize_embeddings=False)
            return embeddings.tolist()

        elif self.model_type == "openai":
            response = self.model.embeddings.create(
                model=self.model_name, input=texts
            )
            return [item.embedding for item in response.data]

    @property
    def dimension(self) -> int:
        """Get embedding dimension"""
        if self.model_type == "sentence-transformer":
            return self.model.get_sentence_embedding_dimension()
        elif self.model_type == "openai":
            # Common dimensions for OpenAI models
            dims = {
                "text-embedding-3-small": 1536,
                "text-embedding-3-large": 3072,
                "text-embedding-ada-002": 1536,
            }
            return dims.get(self.model_name, 1536)
        return 384  # Default
