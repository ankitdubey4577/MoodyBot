"""
Semantic Search - High-level interface for semantic task search
"""
from typing import List, Dict, Any, Optional
import logging

from src.rag.embedding_service import EmbeddingService
from src.rag.vector_database import VectorDatabase

logger = logging.getLogger(__name__)

class SemanticSearch:
    """
    High-level semantic search service combining embeddings and vector DB.
    """

    def __init__(self, embedding_service: EmbeddingService = None,
                 vector_db: VectorDatabase = None):
        """
        Initialize semantic search.

        Args:
            embedding_service: Embedding service instance
            vector_db: Vector database instance
        """
        self.embedding_service = embedding_service or EmbeddingService()
        self.vector_db = vector_db or VectorDatabase()

    def index_task(self, task: Dict[str, Any]):
        """
        Index a single task for semantic search.

        Args:
            task: Task dictionary with 'id', 'title', and optionally 'description'
        """
        try:
            # Generate embedding
            embedding = self.embedding_service.encode_task(task)

            # Create text for storage
            title = task.get('title', '')
            description = task.get('description', '')
            text = f"{title}. {description}" if description else title

            # Prepare metadata
            metadata = {
                'title': title,
                'priority': task.get('priority', 5),
                'mode': task.get('mode', 'work'),
                'status': task.get('status', 'pending'),
                'created_at': str(task.get('created_at', ''))
            }

            # Add to vector DB
            self.vector_db.add_task(
                task_id=str(task['id']),
                embedding=embedding.tolist(),
                text=text,
                metadata=metadata
            )

            logger.debug(f"Indexed task {task['id']}")

        except Exception as e:
            logger.error(f"Error indexing task: {e}")

    def index_tasks_batch(self, tasks: List[Dict[str, Any]]):
        """
        Index multiple tasks in batch.

        Args:
            tasks: List of task dictionaries
        """
        if not tasks:
            return

        try:
            task_ids = []
            embeddings = []
            texts = []
            metadatas = []

            for task in tasks:
                # Generate embedding
                embedding = self.embedding_service.encode_task(task)

                # Create text
                title = task.get('title', '')
                description = task.get('description', '')
                text = f"{title}. {description}" if description else title

                # Prepare metadata
                metadata = {
                    'title': title,
                    'priority': task.get('priority', 5),
                    'mode': task.get('mode', 'work'),
                    'status': task.get('status', 'pending'),
                    'created_at': str(task.get('created_at', ''))
                }

                task_ids.append(str(task['id']))
                embeddings.append(embedding.tolist())
                texts.append(text)
                metadatas.append(metadata)

            # Add batch to vector DB
            self.vector_db.add_tasks_batch(
                task_ids=task_ids,
                embeddings=embeddings,
                texts=texts,
                metadatas=metadatas
            )

            logger.info(f"Indexed {len(tasks)} tasks")

        except Exception as e:
            logger.error(f"Error indexing tasks batch: {e}")

    def search(self, query: str, n_results: int = 5,
              filter_mode: Optional[str] = None,
              filter_status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search for similar tasks using natural language query.

        Args:
            query: Search query (natural language)
            n_results: Number of results to return
            filter_mode: Filter by mode ('work' or 'personal')
            filter_status: Filter by status

        Returns:
            List of similar tasks with similarity scores
        """
        try:
            # Generate query embedding
            query_embedding = self.embedding_service.encode(query)

            # Prepare filters
            filter_metadata = {}
            if filter_mode:
                filter_metadata['mode'] = filter_mode
            if filter_status:
                filter_metadata['status'] = filter_status

            # Search vector DB
            results = self.vector_db.search_similar_tasks(
                query_embedding=query_embedding.tolist(),
                n_results=n_results,
                filter_metadata=filter_metadata if filter_metadata else None
            )

            logger.debug(f"Found {len(results)} similar tasks for query: '{query}'")

            return results

        except Exception as e:
            logger.error(f"Error searching tasks: {e}")
            return []

    def search_similar_to_task(self, task: Dict[str, Any],
                               n_results: int = 5) -> List[Dict[str, Any]]:
        """
        Find tasks similar to a given task.

        Args:
            task: Task dictionary
            n_results: Number of results to return

        Returns:
            List of similar tasks
        """
        try:
            # Generate task embedding
            task_embedding = self.embedding_service.encode_task(task)

            # Search
            results = self.vector_db.search_similar_tasks(
                query_embedding=task_embedding.tolist(),
                n_results=n_results + 1  # +1 because the task itself might be in results
            )

            # Filter out the task itself
            task_id = str(task.get('id', ''))
            results = [r for r in results if r['task_id'] != task_id][:n_results]

            return results

        except Exception as e:
            logger.error(f"Error finding similar tasks: {e}")
            return []

    def delete_task(self, task_id: int):
        """
        Remove a task from the index.

        Args:
            task_id: Task ID to remove
        """
        self.vector_db.delete_task(str(task_id))

    def reindex_all_tasks(self, tasks: List[Dict[str, Any]]):
        """
        Clear index and reindex all tasks.

        Args:
            tasks: List of all tasks
        """
        logger.info("Clearing and reindexing all tasks...")
        self.vector_db.clear_all()
        self.index_tasks_batch(tasks)
        logger.info(f"Reindexed {len(tasks)} tasks")

    def get_stats(self) -> Dict[str, Any]:
        """Get semantic search statistics."""
        embedding_info = self.embedding_service.get_info()
        db_stats = self.vector_db.get_collection_stats()

        return {
            'embedding_service': embedding_info,
            'vector_database': db_stats,
            'status': 'operational' if embedding_info['model_loaded'] else 'fallback_mode'
        }
