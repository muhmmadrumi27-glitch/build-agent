"""Tests for Action Executor."""
import pytest
from agents.executor.executor import ActionExecutor, ActionResult


class TestActionResult:
    """Test suite for ActionResult."""

    def test_result_creation(self):
        """Test creating an action result."""
        result = ActionResult(
            success=True,
            action_type="mouse_click",
            parameters={"x": 100, "y": 200},
            result="Clicked at (100, 200)",
            duration_ms=150,
        )
        assert result.success is True
        assert result.action_type == "mouse_click"
        assert result.duration_ms == 150

    def test_result_to_dict(self):
        """Test result serialization."""
        result = ActionResult(
            success=False,
            action_type="browser_navigate",
            parameters={"url": "https://example.com"},
            error="Connection timeout",
        )
        data = result.to_dict()
        assert data["success"] is False
        assert data["error"] == "Connection timeout"


class TestActionExecutor:
    """Test suite for ActionExecutor."""

    @pytest.fixture
    def executor(self):
        return ActionExecutor()

    @pytest.mark.asyncio
    async def test_execute_screenshot(self, executor):
        """Test screenshot execution."""
        result = await executor.execute_action("screenshot", {})

        assert isinstance(result, ActionResult)
        assert result.success is True
        assert result.action_type == "screenshot"

    @pytest.mark.asyncio
    async def test_execute_wait(self, executor):
        """Test wait execution."""
        result = await executor.execute_action("wait", {"duration": 0.1})

        assert result.success is True
        assert "Waited" in (result.result or "")

    @pytest.mark.asyncio
    async def test_execute_vision_analyze(self, executor):
        """Test vision analysis execution."""
        result = await executor.execute_action("vision_analyze", {})

        assert isinstance(result, ActionResult)
        assert result.action_type == "vision_analyze"

    @pytest.mark.asyncio
    async def test_execute_keyboard_shortcut(self, executor):
        """Test keyboard shortcut execution."""
        result = await executor.execute_action(
            "keyboard_shortcut",
            {"shortcut": "ctrl+c"},
        )

        assert isinstance(result, ActionResult)
        assert result.action_type == "keyboard_shortcut"

    @pytest.mark.asyncio
    async def test_execute_invalid_action(self, executor):
        """Test invalid action handling."""
        result = await executor.execute_action("invalid_action", {})

        assert result.success is False
        assert "Unknown action type" in (result.error or "")

    @pytest.mark.asyncio
    async def test_security_validation(self, executor):
        """Test security validation during execution."""
        # Try to access sensitive file
        result = await executor.execute_action(
            "browser_download",
            {"url": "file:///etc/passwd"},
        )

        assert result.success is False


class TestExecutorIntegration:
    """Integration tests for Action Executor."""

    @pytest.mark.asyncio
    async def test_action_sequence(self):
        """Test executing a sequence of actions."""
        executor = ActionExecutor()

        actions = [
            ("screenshot", {}),
            ("wait", {"duration": 0.1}),
            ("vision_analyze", {}),
        ]

        results = []
        for action_type, params in actions:
            result = await executor.execute_action(action_type, params)
            results.append(result)

        assert len(results) == 3
        assert all(isinstance(r, ActionResult) for r in results)
