"""Memory Engine for storing and retrieving agent memories."""
import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

import chromadb
from chromadb.config import Settings as ChromaSettings
from loguru import logger

from config import settings


class MemoryEngine:
    """Memory engine using ChromaDB for vector storage."""

    def __init__(self):
        self.client = None
        self.collection = None
        self._init_chroma()
        logger.info("MemoryEngine initialized")

    def _init_chroma(self) -> None:
        """Initialize ChromaDB client."""
        try:
            self.client = chromadb.HttpClient(
                host=settings.chroma_host,
                port=settings.chroma_port,
                settings=ChromaSettings(
                    anonymized_telemetry=False,
                    allow_reset=True,
                ),
            )

            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name=settings.chroma_collection,
                metadata={"hnsw:space": "cosine"},
            )

            logger.info(f"ChromaDB collection initialized: {settings.chroma_collection}")
        except Exception as e:
            logger.error(f"ChromaDB initialization failed: {e}")
            # Fallback to in-memory client
            self.client = chromadb.Client(
                ChromaSettings(
                    is_persistent=False,
                    anonymized_telemetry=False,
                )
            )
            self.collection = self.client.get_or_create_collection(
                name=settings.chroma_collection,
            )
            logger.info("ChromaDB fallback to in-memory mode")

    def store(
        self,
        content: str,
        entry_type: str,
        metadata: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
        task_id: Optional[str] = None,
        embedding: Optional[List[float]] = None,
    ) -> str:
        """Store a memory entry."""
        entry_id = str(uuid.uuid4())

        if metadata is None:
            metadata = {}

        metadata.update({
            "entry_type": entry_type,
            "session_id": session_id or "",
            "task_id": task_id or "",
            "timestamp": datetime.utcnow().isoformat(),
        })

        try:
            self.collection.add(
                ids=[entry_id],
                documents=[content],
                metadatas=[metadata],
                embeddings=[embedding] if embedding else None,
            )
            logger.debug(f"Memory stored: {entry_id} ({entry_type})")
            return entry_id
        except Exception as e:
            logger.error(f"Failed to store memory: {e}")
            return entry_id

    def retrieve(
        self,
        query: str,
        entry_type: Optional[str] = None,
        session_id: Optional[str] = None,
        task_id: Optional[str] = None,
        n_results: int = 5,
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant memories using semantic search."""
        try:
            where_filter = {}

            if entry_type:
                where_filter["entry_type"] = entry_type
            if session_id:
                where_filter["session_id"] = session_id
            if task_id:
                where_filter["task_id"] = task_id

            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where_filter if where_filter else None,
            )

            memories = []
            if results["ids"] and results["ids"][0]:
                for i, entry_id in enumerate(results["ids"][0]):
                    memory = {
                        "id": entry_id,
                        "content": results["documents"][0][i] if results["documents"] else "",
                        "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                        "distance": results["distances"][0][i] if results["distances"] else 0.0,
                    }
                    memories.append(memory)

            return memories
        except Exception as e:
            logger.error(f"Memory retrieval failed: {e}")
            return []

    def get_by_id(self, entry_id: str) -> Optional[Dict[str, Any]]:
        """Get a memory entry by ID."""
        try:
            result = self.collection.get(ids=[entry_id])

            if result["ids"]:
                return {
                    "id": result["ids"][0],
                    "content": result["documents"][0] if result["documents"] else "",
                    "metadata": result["metadatas"][0] if result["metadatas"] else {},
                }

            return None
        except Exception as e:
            logger.error(f"Failed to get memory by ID: {e}")
            return None

    def update(
        self,
        entry_id: str,
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Update a memory entry."""
        try:
            update_data = {}

            if content is not None:
                update_data["documents"] = [content]

            if metadata is not None:
                update_data["metadatas"] = [metadata]

            if update_data:
                self.collection.update(
                    ids=[entry_id],
                    **update_data,
                )
                logger.debug(f"Memory updated: {entry_id}")
                return True

            return False
        except Exception as e:
            logger.error(f"Failed to update memory: {e}")
            return False

    def delete(self, entry_id: str) -> bool:
        """Delete a memory entry."""
        try:
            self.collection.delete(ids=[entry_id])
            logger.debug(f"Memory deleted: {entry_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete memory: {e}")
            return False

    def store_task(
        self,
        task_description: str,
        task_result: str,
        session_id: Optional[str] = None,
        task_id: Optional[str] = None,
    ) -> str:
        """Store a completed task memory."""
        content = f"Task: {task_description}\nResult: {task_result}"
        return self.store(
            content=content,
            entry_type="task",
            session_id=session_id,
            task_id=task_id,
            metadata={"task_description": task_description, "task_result": task_result},
        )

    def store_action(
        self,
        action_type: str,
        parameters: Dict[str, Any],
        result: str,
        session_id: Optional[str] = None,
        task_id: Optional[str] = None,
    ) -> str:
        """Store an action execution memory."""
        content = f"Action: {action_type}\nParameters: {json.dumps(parameters)}\nResult: {result}"
        return self.store(
            content=content,
            entry_type="action",
            session_id=session_id,
            task_id=task_id,
            metadata={"action_type": action_type, "parameters": parameters, "result": result},
        )

    def store_failure(
        self,
        task_description: str,
        error: str,
        recovery_strategy: str,
        session_id: Optional[str] = None,
        task_id: Optional[str] = None,
    ) -> str:
        """Store a failure and recovery memory."""
        content = f"Failure: {task_description}\nError: {error}\nRecovery: {recovery_strategy}"
        return self.store(
            content=content,
            entry_type="failure",
            session_id=session_id,
            task_id=task_id,
            metadata={"error": error, "recovery_strategy": recovery_strategy},
        )

    def store_screenshot(
        self,
        description: str,
        file_path: str,
        session_id: Optional[str] = None,
        task_id: Optional[str] = None,
    ) -> str:
        """Store a screenshot memory."""
        content = f"Screenshot: {description}\nPath: {file_path}"
        return self.store(
            content=content,
            entry_type="screenshot",
            session_id=session_id,
            task_id=task_id,
            metadata={"file_path": file_path, "description": description},
        )

    def store_preference(
        self,
        preference_type: str,
        value: Any,
        user_id: Optional[str] = None,
    ) -> str:
        """Store a user preference."""
        content = f"Preference: {preference_type} = {value}"
        return self.store(
            content=content,
            entry_type="preference",
            metadata={"preference_type": preference_type, "value": value, "user_id": user_id},
        )

    def get_similar_tasks(
        self,
        task_description: str,
        n_results: int = 3,
    ) -> List[Dict[str, Any]]:
        """Get similar previously completed tasks."""
        return self.retrieve(
            query=task_description,
            entry_type="task",
            n_results=n_results,
        )

    def get_similar_failures(
        self,
        error_description: str,
        n_results: int = 3,
    ) -> List[Dict[str, Any]]:
        """Get similar previous failures and their recoveries."""
        return self.retrieve(
            query=error_description,
            entry_type="failure",
            n_results=n_results,
        )

    def get_session_context(
        self,
        session_id: str,
        n_results: int = 10,
    ) -> List[Dict[str, Any]]:
        """Get all memories for a session."""
        try:
            results = self.collection.get(
                where={"session_id": session_id},
                limit=n_results,
            )

            memories = []
            if results["ids"]:
                for i, entry_id in enumerate(results["ids"]):
                    memories.append({
                        "id": entry_id,
                        "content": results["documents"][i] if results["documents"] else "",
                        "metadata": results["metadatas"][i] if results["metadatas"] else {},
                    })

            return memories
        except Exception as e:
            logger.error(f"Failed to get session context: {e}")
            return []

    def clear_session(self, session_id: str) -> bool:
        """Clear all memories for a session."""
        try:
            self.collection.delete(where={"session_id": session_id})
            logger.info(f"Cleared memories for session: {session_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to clear session memories: {e}")
            return False

    def count_memories(self, entry_type: Optional[str] = None) -> int:
        """Count total memories."""
        try:
            if entry_type:
                result = self.collection.count(where={"entry_type": entry_type})
            else:
                result = self.collection.count()
            return result
        except Exception as e:
            logger.error(f"Failed to count memories: {e}")
            return 0


# Global memory engine instance
memory_engine = MemoryEngine()
