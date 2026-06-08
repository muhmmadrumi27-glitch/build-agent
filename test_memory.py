"""Tests for Memory Engine."""
import pytest
from agents.memory.memory import MemoryEngine


class TestMemoryEngine:
    """Test suite for MemoryEngine."""

    @pytest.fixture
    def memory(self):
        return MemoryEngine()

    def test_store_and_retrieve(self, memory):
        """Test storing and retrieving memories."""
        content = "Test memory content"
        entry_id = memory.store(content, "test", metadata={"key": "value"})
        assert entry_id is not None
        assert len(entry_id) > 0

        retrieved = memory.get_by_id(entry_id)
        assert retrieved is not None
        assert retrieved["content"] == content

    def test_retrieve_similar(self, memory):
        """Test semantic retrieval."""
        memory.store("The quick brown fox", "test")
        memory.store("A fast red dog", "test")
        memory.store("Machine learning is great", "test")

        results = memory.retrieve("fast animal", n_results=2)
        assert len(results) > 0

    def test_store_task(self, memory):
        """Test storing task memory."""
        entry_id = memory.store_task(
            "Open browser and navigate to Google",
            "Successfully opened Google",
            session_id="test-session",
        )
        assert entry_id is not None

    def test_store_action(self, memory):
        """Test storing action memory."""
        entry_id = memory.store_action(
            "mouse_click",
            {"x": 100, "y": 200},
            "Clicked successfully",
        )
        assert entry_id is not None

    def test_store_failure(self, memory):
        """Test storing failure memory."""
        entry_id = memory.store_failure(
            "Click button",
            "Button not found",
            "Try alternative selector",
        )
        assert entry_id is not None

    def test_get_similar_tasks(self, memory):
        """Test getting similar tasks."""
        memory.store_task("Open Chrome browser", "Success", task_id="task-1")
        memory.store_task("Open Firefox browser", "Success", task_id="task-2")

        similar = memory.get_similar_tasks("Open web browser", n_results=2)
        assert isinstance(similar, list)

    def test_get_similar_failures(self, memory):
        """Test getting similar failures."""
        memory.store_failure("Click login", "Element not found", "Use ID selector")

        similar = memory.get_similar_failures("Element not found error", n_results=1)
        assert isinstance(similar, list)

    def test_update_memory(self, memory):
        """Test updating memory."""
        entry_id = memory.store("Original content", "test")
        success = memory.update(entry_id, content="Updated content")
        assert success is True

        retrieved = memory.get_by_id(entry_id)
        assert retrieved["content"] == "Updated content"

    def test_delete_memory(self, memory):
        """Test deleting memory."""
        entry_id = memory.store("To be deleted", "test")
        success = memory.delete(entry_id)
        assert success is True

        retrieved = memory.get_by_id(entry_id)
        assert retrieved is None

    def test_session_context(self, memory):
        """Test session context retrieval."""
        session_id = "test-session-123"
        memory.store("Task 1", "task", session_id=session_id)
        memory.store("Task 2", "task", session_id=session_id)
        memory.store("Other task", "task", session_id="other-session")

        context = memory.get_session_context(session_id)
        assert len(context) == 2

    def test_clear_session(self, memory):
        """Test clearing session memories."""
        session_id = "clear-test-session"
        memory.store("Task 1", "task", session_id=session_id)

        success = memory.clear_session(session_id)
        assert success is True

        context = memory.get_session_context(session_id)
        assert len(context) == 0

    def test_count_memories(self, memory):
        """Test memory counting."""
        initial_count = memory.count_memories()
        memory.store("Count test", "test")
        new_count = memory.count_memories()
        assert new_count >= initial_count


class TestMemoryIntegration:
    """Integration tests for Memory Engine."""

    def test_full_workflow(self):
        """Test complete memory workflow."""
        memory = MemoryEngine()

        # Store multiple entries
        id1 = memory.store("First task", "task", session_id="s1")
        id2 = memory.store("Second task", "task", session_id="s1")
        id3 = memory.store("Action result", "action", session_id="s1")

        # Retrieve all
        all_memories = memory.get_session_context("s1")
        assert len(all_memories) == 3

        # Query specific
        results = memory.retrieve("task", entry_type="task")
        assert len(results) >= 2

        # Update
        memory.update(id1, content="Updated first task")

        # Delete
        memory.delete(id2)

        # Verify
        final = memory.get_session_context("s1")
        assert len(final) == 2
