"""
Embedding Service - Generates embeddings using Sentence Transformers
"""
from typing import List, Union
import numpy as np
import logging

logger = logging.getLogger(__name__)

class EmbeddingService:
    """
    Service for generating embeddings using sentence-transformers.

    Model: all-MiniLM-L6-v2
    - Dimensions: 384
    - Speed: Fast (suitable for real-time)
    - Quality: Good for semantic similarity
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize embedding service.

        Args:
            model_name: Name of the sentence-transformer model
        """
        self.model_name = model_name
        self.model = None
        self.embedding_dim = 384

        self._load_model()

    def _load_model(self):
        """Load the sentence transformer model."""
        try:
            from sentence_transformers import SentenceTransformer

            logger.info(f"Loading embedding model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            self.embedding_dim = self.model.get_sentence_embedding_dimension()
            logger.info(f"Model loaded successfully. Embedding dimension: {self.embedding_dim}")

        except ImportError:
            logger.warning("sentence-transformers not installed, using fallback embeddings")
            self.model = None
        except Exception as e:
            logger.error(f"Error loading embedding model: {e}")
            self.model = None

    def encode(self, texts: Union[str, List[str]],
               normalize: bool = True) -> np.ndarray:
        """
        Generate embeddings for text(s).

        Args:
            texts: Single text or list of texts
            normalize: Whether to normalize embeddings (recommended for cosine similarity)

        Returns:
            Embeddings as numpy array (shape: [n_texts, embedding_dim])
        """
        if self.model is None:
            return self._fallback_embedding(texts)

        # Convert single string to list
        is_single = isinstance(texts, str)
        if is_single:
            texts = [texts]

        try:
            # Generate embeddings
            embeddings = self.model.encode(
                texts,
                normalize_embeddings=normalize,
                show_progress_bar=False
            )

            # Return single embedding if input was single string
            if is_single:
                return embeddings[0]

            return embeddings

        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            return self._fallback_embedding(texts)

    def encode_task(self, task: dict) -> np.ndarray:
        """
        Generate embedding for a task.

        Args:
            task: Task dictionary with 'title' and optionally 'description'

        Returns:
            Task embedding
        """
        # Combine title and description
        title = task.get('title', '')
        description = task.get('description', '')

        # Create combined text
        if description:
            text = f"{title}. {description}"
        else:
            text = title

        return self.encode(text)

    def compute_similarity(self, embedding1: np.ndarray,
                          embedding2: np.ndarray) -> float:
        """
        Compute cosine similarity between two embeddings.

        Args:
            embedding1: First embedding
            embedding2: Second embedding

        Returns:
            Similarity score (0-1, higher is more similar)
        """
        # Ensure embeddings are normalized
        embedding1 = embedding1 / np.linalg.norm(embedding1)
        embedding2 = embedding2 / np.linalg.norm(embedding2)

        # Compute cosine similarity
        similarity = np.dot(embedding1, embedding2)

        return float(similarity)

    def find_most_similar(self, query_embedding: np.ndarray,
                         candidate_embeddings: np.ndarray,
                         top_k: int = 5) -> List[tuple]:
        """
        Find most similar embeddings to query.

        Args:
            query_embedding: Query embedding (1D array)
            candidate_embeddings: Candidate embeddings (2D array)
            top_k: Number of results to return

        Returns:
            List of (index, similarity_score) tuples
        """
        # Normalize query
        query_embedding = query_embedding / np.linalg.norm(query_embedding)

        # Normalize candidates
        norms = np.linalg.norm(candidate_embeddings, axis=1, keepdims=True)
        normalized_candidates = candidate_embeddings / norms

        # Compute similarities
        similarities = np.dot(normalized_candidates, query_embedding)

        # Get top k
        top_indices = np.argsort(similarities)[::-1][:top_k]

        results = [(int(idx), float(similarities[idx])) for idx in top_indices]

        return results

    def _fallback_embedding(self, texts: Union[str, List[str]]) -> np.ndarray:
        """
        Fallback embedding when model is not available.
        Uses simple TF-IDF-like approach.

        Args:
            texts: Text(s) to embed

        Returns:
            Fallback embeddings
        """
        is_single = isinstance(texts, str)
        if is_single:
            texts = [texts]

        embeddings = []
        for text in texts:
            # Simple hash-based embedding
            words = text.lower().split()
            embedding = np.zeros(self.embedding_dim)

            for i, word in enumerate(words[:50]):  # Limit to 50 words
                # Use hash to distribute words across embedding dimensions
                hash_val = hash(word)
                for j in range(min(5, self.embedding_dim)):
                    idx = (hash_val + j * 7) % self.embedding_dim
                    embedding[idx] += 1.0 / (i + 1)  # Weight by position

            # Normalize
            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = embedding / norm

            embeddings.append(embedding)

        embeddings = np.array(embeddings)

        if is_single:
            return embeddings[0]

        return embeddings

    def is_model_loaded(self) -> bool:
        """Check if the embedding model is loaded."""
        return self.model is not None

    def get_info(self) -> dict:
        """Get embedding service information."""
        return {
            'model_name': self.model_name,
            'embedding_dim': self.embedding_dim,
            'model_loaded': self.is_model_loaded(),
            'using_fallback': not self.is_model_loaded()
        }
