"""
Context Retriever Agent - Retrieves relevant context using RAG
Enhanced with semantic search using embeddings and vector database
"""
from typing import Dict, Any, List
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

class ContextRetriever:
    """
    Retrieves relevant context from past tasks and notes using semantic search.

    Enhanced with:
    - Sentence transformers for embeddings
    - ChromaDB for vector storage
    - Semantic similarity search
    """

    def __init__(self, use_semantic_search: bool = True):
        self.name = "ContextRetriever"
        self.use_embeddings = use_semantic_search
        self.semantic_search = None

        # Initialize semantic search if enabled
        if self.use_embeddings:
            self._initialize_semantic_search()

    def _initialize_semantic_search(self):
        """Initialize semantic search service."""
        try:
            from src.rag.semantic_search import SemanticSearch

            self.semantic_search = SemanticSearch()
            logger.info("Semantic search initialized successfully")

        except Exception as e:
            logger.warning(f"Could not initialize semantic search: {e}")
            self.use_embeddings = False
            self.semantic_search = None

    def retrieve_similar_tasks(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve tasks similar to the query using semantic search.

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            List of similar tasks with similarity scores
        """
        if self.use_embeddings and self.semantic_search:
            try:
                # Use semantic search
                results = self.semantic_search.search(query, n_results=limit)

                logger.info(f"Context: Found {len(results)} similar tasks for: '{query}'")

                # Format results
                similar_tasks = []
                for result in results:
                    similar_tasks.append({
                        'task_id': result['task_id'],
                        'title': result['metadata'].get('title', result['text']),
                        'text': result['text'],
                        'similarity': result['similarity'],
                        'priority': result['metadata'].get('priority', 5),
                        'mode': result['metadata'].get('mode', 'work')
                    })

                return similar_tasks

            except Exception as e:
                logger.error(f"Error in semantic search: {e}")
                return []
        else:
            # Fallback: return empty list
            logger.info(f"Context: Semantic search disabled, returning empty results")
            return []

    def retrieve_context(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Retrieve relevant context for the current input using semantic search.

        Args:
            state: Current agent state

        Returns:
            Updated state with context
        """
        try:
            input_text = state.get("input", "")

            # Retrieve similar tasks using semantic search
            similar_tasks = self.retrieve_similar_tasks(input_text, limit=5)

            # Extract similarity scores
            similarity_scores = [task.get('similarity', 0) for task in similar_tasks]

            # Create context data
            context = {
                "relevant_tasks": similar_tasks,
                "relevant_notes": [],  # Future: notes search
                "similarity_scores": similarity_scores,
                "search_query": input_text,
                "num_results": len(similar_tasks)
            }

            # Update state
            state["context"] = context
            state["current_agent"] = self.name

            # Add to agent path
            if "agent_path" not in state:
                state["agent_path"] = []
            if self.name not in state["agent_path"]:
                state["agent_path"].append(self.name)

            if similar_tasks:
                logger.info(
                    f"Context: Retrieved {len(similar_tasks)} similar tasks "
                    f"(top similarity: {similarity_scores[0]:.2f})"
                )
            else:
                logger.info("Context: No similar tasks found")

            return state

        except Exception as e:
            logger.error(f"Context retriever error: {e}")
            # Return state with empty context
            state["context"] = {
                "relevant_tasks": [],
                "relevant_notes": [],
                "similarity_scores": [],
                "error": str(e)
            }
            return state

    def build_context_string(self, state: Dict[str, Any]) -> str:
        """
        Build a formatted context string for LLM prompts.

        Args:
            state: Current state with context

        Returns:
            Formatted context string
        """
        context_data = state.get("context", {})
        relevant_tasks = context_data.get("relevant_tasks", [])
        similarity_scores = context_data.get("similarity_scores", [])

        if not relevant_tasks:
            return "No relevant past context found."

        context_parts = ["**Relevant Past Tasks:**"]
        for i, task in enumerate(relevant_tasks[:3], 1):
            title = task.get("title", "Unknown")
            similarity = similarity_scores[i-1] if i-1 < len(similarity_scores) else 0
            priority = task.get("priority", 5)
            mode = task.get("mode", "work")

            context_parts.append(
                f"{i}. {title} "
                f"(Similarity: {similarity:.0%}, Priority: {priority}/10, Mode: {mode})"
            )

        return "\n".join(context_parts)

    def index_task(self, task: Dict[str, Any]):
        """
        Index a task for semantic search.

        Args:
            task: Task dictionary to index
        """
        if self.use_embeddings and self.semantic_search:
            try:
                self.semantic_search.index_task(task)
                logger.debug(f"Indexed task {task.get('id')} for semantic search")
            except Exception as e:
                logger.error(f"Error indexing task: {e}")

    def get_search_stats(self) -> Dict[str, Any]:
        """Get semantic search statistics."""
        if self.use_embeddings and self.semantic_search:
            try:
                return self.semantic_search.get_stats()
            except Exception as e:
                logger.error(f"Error getting stats: {e}")
                return {'error': str(e)}
        else:
            return {
                'status': 'disabled',
                'use_embeddings': False
            }
