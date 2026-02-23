"""
Vector Database - Manages ChromaDB for semantic search
"""
from typing import List, Dict, Any, Optional
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class VectorDatabase:
    """
    Vector database using ChromaDB for semantic search.

    Collections:
    - tasks: Task embeddings with metadata
    - notes: Note embeddings (future)
    """

    def __init__(self, persist_directory: str = "chroma_db"):
        """
        Initialize vector database.

        Args:
            persist_directory: Directory to persist ChromaDB data
        """
        self.persist_directory = persist_directory
        self.client = None
        self.tasks_collection = None

        self._initialize_db()

    def _initialize_db(self):
        """Initialize ChromaDB client and collections."""
        try:
            import chromadb
            from chromadb.config import Settings

            logger.info(f"Initializing ChromaDB at {self.persist_directory}")

            # Create client with persistent storage
            self.client = chromadb.Client(Settings(
                persist_directory=self.persist_directory,
                anonymized_telemetry=False
            ))

            # Get or create tasks collection
            self.tasks_collection = self.client.get_or_create_collection(
                name="tasks",
                metadata={"description": "Task embeddings for semantic search"}
            )

            logger.info(f"ChromaDB initialized. Tasks collection size: {self.tasks_collection.count()}")

        except ImportError:
            logger.warning("ChromaDB not installed, using in-memory fallback")
            self._initialize_fallback()
        except Exception as e:
            logger.error(f"Error initializing ChromaDB: {e}")
            self._initialize_fallback()

    def _initialize_fallback(self):
        """Initialize fallback in-memory storage."""
        self.client = None
        self.tasks_collection = None
        self._fallback_storage = {
            'embeddings': [],
            'documents': [],
            'metadatas': [],
            'ids': []
        }

    def add_task(self, task_id: str, embedding: List[float],
                 text: str, metadata: Dict[str, Any] = None):
        """
        Add a task to the vector database.

        Args:
            task_id: Unique task ID
            embedding: Task embedding vector
            text: Task text (title + description)
            metadata: Additional task metadata
        """
        if self.tasks_collection is not None:
            try:
                self.tasks_collection.add(
                    ids=[str(task_id)],
                    embeddings=[embedding],
                    documents=[text],
                    metadatas=[metadata or {}]
                )
                logger.debug(f"Added task {task_id} to vector DB")
            except Exception as e:
                logger.error(f"Error adding task to ChromaDB: {e}")
                self._add_to_fallback(task_id, embedding, text, metadata)
        else:
            self._add_to_fallback(task_id, embedding, text, metadata)

    def add_tasks_batch(self, task_ids: List[str],
                       embeddings: List[List[float]],
                       texts: List[str],
                       metadatas: List[Dict[str, Any]] = None):
        """
        Add multiple tasks in batch.

        Args:
            task_ids: List of task IDs
            embeddings: List of embeddings
            texts: List of texts
            metadatas: List of metadata dicts
        """
        if self.tasks_collection is not None:
            try:
                self.tasks_collection.add(
                    ids=[str(tid) for tid in task_ids],
                    embeddings=embeddings,
                    documents=texts,
                    metadatas=metadatas or [{} for _ in task_ids]
                )
                logger.info(f"Added {len(task_ids)} tasks to vector DB")
            except Exception as e:
                logger.error(f"Error adding tasks batch: {e}")
        else:
            for i, tid in enumerate(task_ids):
                metadata = metadatas[i] if metadatas else {}
                self._add_to_fallback(tid, embeddings[i], texts[i], metadata)

    def search_similar_tasks(self, query_embedding: List[float],
                            n_results: int = 5,
                            filter_metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Search for similar tasks using vector similarity.

        Args:
            query_embedding: Query embedding
            n_results: Number of results to return
            filter_metadata: Optional metadata filters

        Returns:
            List of similar tasks with metadata and similarity scores
        """
        if self.tasks_collection is not None:
            try:
                results = self.tasks_collection.query(
                    query_embeddings=[query_embedding],
                    n_results=n_results,
                    where=filter_metadata
                )

                # Format results
                similar_tasks = []
                for i in range(len(results['ids'][0])):
                    similar_tasks.append({
                        'task_id': results['ids'][0][i],
                        'text': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i],
                        'similarity': 1 - results['distances'][0][i]  # Convert distance to similarity
                    })

                return similar_tasks

            except Exception as e:
                logger.error(f"Error searching ChromaDB: {e}")
                return self._search_fallback(query_embedding, n_results)
        else:
            return self._search_fallback(query_embedding, n_results)

    def delete_task(self, task_id: str):
        """
        Delete a task from the vector database.

        Args:
            task_id: Task ID to delete
        """
        if self.tasks_collection is not None:
            try:
                self.tasks_collection.delete(ids=[str(task_id)])
                logger.debug(f"Deleted task {task_id} from vector DB")
            except Exception as e:
                logger.error(f"Error deleting task: {e}")
        else:
            self._delete_from_fallback(task_id)

    def update_task(self, task_id: str, embedding: List[float] = None,
                   text: str = None, metadata: Dict[str, Any] = None):
        """
        Update a task in the vector database.

        Args:
            task_id: Task ID
            embedding: New embedding (optional)
            text: New text (optional)
            metadata: New metadata (optional)
        """
        if self.tasks_collection is not None:
            try:
                update_kwargs = {'ids': [str(task_id)]}
                if embedding is not None:
                    update_kwargs['embeddings'] = [embedding]
                if text is not None:
                    update_kwargs['documents'] = [text]
                if metadata is not None:
                    update_kwargs['metadatas'] = [metadata]

                self.tasks_collection.update(**update_kwargs)
                logger.debug(f"Updated task {task_id} in vector DB")
            except Exception as e:
                logger.error(f"Error updating task: {e}")

    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector database."""
        if self.tasks_collection is not None:
            return {
                'total_tasks': self.tasks_collection.count(),
                'backend': 'ChromaDB',
                'persist_directory': self.persist_directory
            }
        else:
            return {
                'total_tasks': len(self._fallback_storage['ids']),
                'backend': 'In-Memory Fallback',
                'persist_directory': None
            }

    def clear_all(self):
        """Clear all data from the database."""
        if self.tasks_collection is not None:
            try:
                # Delete collection and recreate
                self.client.delete_collection("tasks")
                self.tasks_collection = self.client.create_collection(
                    name="tasks",
                    metadata={"description": "Task embeddings for semantic search"}
                )
                logger.info("Cleared all tasks from vector DB")
            except Exception as e:
                logger.error(f"Error clearing database: {e}")
        else:
            self._fallback_storage = {
                'embeddings': [],
                'documents': [],
                'metadatas': [],
                'ids': []
            }

    # Fallback methods for when ChromaDB is not available

    def _add_to_fallback(self, task_id: str, embedding: List[float],
                        text: str, metadata: Dict[str, Any]):
        """Add to fallback in-memory storage."""
        self._fallback_storage['ids'].append(str(task_id))
        self._fallback_storage['embeddings'].append(embedding)
        self._fallback_storage['documents'].append(text)
        self._fallback_storage['metadatas'].append(metadata or {})

    def _search_fallback(self, query_embedding: List[float],
                        n_results: int) -> List[Dict[str, Any]]:
        """Search using fallback storage with cosine similarity."""
        import numpy as np

        if not self._fallback_storage['embeddings']:
            return []

        query_emb = np.array(query_embedding)
        candidate_embs = np.array(self._fallback_storage['embeddings'])

        # Normalize
        query_norm = query_emb / np.linalg.norm(query_emb)
        candidate_norms = candidate_embs / np.linalg.norm(candidate_embs, axis=1, keepdims=True)

        # Compute similarities
        similarities = np.dot(candidate_norms, query_norm)

        # Get top k
        top_indices = np.argsort(similarities)[::-1][:n_results]

        results = []
        for idx in top_indices:
            results.append({
                'task_id': self._fallback_storage['ids'][idx],
                'text': self._fallback_storage['documents'][idx],
                'metadata': self._fallback_storage['metadatas'][idx],
                'similarity': float(similarities[idx])
            })

        return results

    def _delete_from_fallback(self, task_id: str):
        """Delete from fallback storage."""
        try:
            idx = self._fallback_storage['ids'].index(str(task_id))
            for key in self._fallback_storage:
                del self._fallback_storage[key][idx]
        except (ValueError, IndexError):
            pass
