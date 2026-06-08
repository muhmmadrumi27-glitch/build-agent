"""Tests for Task Planner."""
import pytest
from agents.planner.planner import ActionPlan, PlanStep, PlanStepStatus, TaskPlanner


class TestPlanStep:
    """Test suite for PlanStep."""

    def test_step_creation(self):
        """Test creating a plan step."""
        step = PlanStep(
            description="Click the login button",
            action_type="mouse_click",
            parameters={"x": 100, "y": 200},
            expected_result="Login page opens",
            order=0,
        )
        assert step.description == "Click the login button"
        assert step.action_type == "mouse_click"
        assert step.status == PlanStepStatus.PENDING

    def test_step_to_dict(self):
        """Test step serialization."""
        step = PlanStep(
            description="Test step",
            action_type="screenshot",
            parameters={},
            order=1,
        )
        data = step.to_dict()
        assert data["description"] == "Test step"
        assert data["action_type"] == "screenshot"
        assert data["order"] == 1

    def test_step_status_transitions(self):
        """Test step status transitions."""
        step = PlanStep(description="Test", action_type="wait")

        assert step.status == PlanStepStatus.PENDING

        # Simulate execution
        step.status = PlanStepStatus.IN_PROGRESS
        assert step.status == PlanStepStatus.IN_PROGRESS

        step.status = PlanStepStatus.COMPLETED
        assert step.status == PlanStepStatus.COMPLETED


class TestActionPlan:
    """Test suite for ActionPlan."""

    @pytest.fixture
    def sample_plan(self):
        plan = ActionPlan(
            task_description="Test task",
            goal="Complete the test",
        )
        plan.steps = [
            PlanStep(description="Step 1", action_type="screenshot", order=0),
            PlanStep(description="Step 2", action_type="mouse_click", order=1),
            PlanStep(description="Step 3", action_type="keyboard_type", order=2),
        ]
        return plan

    def test_plan_creation(self, sample_plan):
        """Test plan creation."""
        assert sample_plan.task_description == "Test task"
        assert sample_plan.goal == "Complete the test"
        assert len(sample_plan.steps) == 3

    def test_current_step(self, sample_plan):
        """Test current step tracking."""
        assert sample_plan.current_step == sample_plan.steps[0]
        sample_plan.current_step_index = 1
        assert sample_plan.current_step == sample_plan.steps[1]

    def test_is_complete(self, sample_plan):
        """Test completion check."""
        assert not sample_plan.is_complete

        for step in sample_plan.steps:
            step.status = PlanStepStatus.COMPLETED

        assert sample_plan.is_complete

    def test_has_failed(self, sample_plan):
        """Test failure detection."""
        assert not sample_plan.has_failed

        sample_plan.steps[0].status = PlanStepStatus.FAILED
        sample_plan.steps[0].retry_count = 3
        sample_plan.steps[0].max_retries = 3

        assert sample_plan.has_failed

    def test_mark_step_complete(self, sample_plan):
        """Test marking step complete."""
        step = sample_plan.steps[0]
        sample_plan.mark_step_complete(step.id, "Success")

        assert step.status == PlanStepStatus.COMPLETED
        assert step.result == "Success"

    def test_mark_step_failed(self, sample_plan):
        """Test marking step failed."""
        step = sample_plan.steps[0]
        sample_plan.mark_step_failed(step.id, "Error occurred")

        assert step.status == PlanStepStatus.FAILED
        assert step.error == "Error occurred"
        assert step.retry_count == 1

    def test_retry_step(self, sample_plan):
        """Test step retry."""
        step = sample_plan.steps[0]
        sample_plan.mark_step_failed(step.id, "Error")

        success = sample_plan.retry_step(step.id)
        assert success is True
        assert step.status == PlanStepStatus.PENDING

    def test_retry_exhausted(self, sample_plan):
        """Test retry exhaustion."""
        step = sample_plan.steps[0]
        step.retry_count = 3
        step.max_retries = 3

        success = sample_plan.retry_step(step.id)
        assert success is False

    def test_get_step_by_id(self, sample_plan):
        """Test getting step by ID."""
        step = sample_plan.steps[0]
        found = sample_plan.get_step_by_id(step.id)
        assert found == step

    def test_get_next_step(self, sample_plan):
        """Test getting next pending step."""
        next_step = sample_plan.get_next_step()
        assert next_step == sample_plan.steps[0]

        sample_plan.steps[0].status = PlanStepStatus.COMPLETED
        next_step = sample_plan.get_next_step()
        assert next_step == sample_plan.steps[1]

    def test_plan_to_dict(self, sample_plan):
        """Test plan serialization."""
        data = sample_plan.to_dict()
        assert data["task_description"] == "Test task"
        assert data["goal"] == "Complete the test"
        assert len(data["steps"]) == 3
        assert "context" in data


class TestTaskPlanner:
    """Test suite for TaskPlanner."""

    @pytest.fixture
    def task_planner(self):
        return TaskPlanner()

    @pytest.mark.asyncio
    async def test_create_plan(self, task_planner):
        """Test plan creation."""
        plan = await task_planner.create_plan("Open the calculator app")

        assert plan is not None
        assert plan.goal == "Open the calculator app"
        assert len(plan.steps) > 0

    @pytest.mark.asyncio
    async def test_create_plan_with_context(self, task_planner):
        """Test plan creation with screen context."""
        context = {
            "dimensions": {"width": 1920, "height": 1080},
            "elements": [],
        }

        plan = await task_planner.create_plan(
            "Click the start button",
            screen_context=context,
        )

        assert plan is not None
        assert len(plan.steps) > 0

    def test_fallback_plan(self, task_planner):
        """Test fallback plan creation."""
        plan = task_planner._create_fallback_plan("Open notepad")

        assert len(plan) > 0
        assert plan[0].action_type == "screenshot"

    def test_estimate_plan_duration(self, task_planner):
        """Test duration estimation."""
        plan = ActionPlan(goal="Test")
        plan.steps = [
            PlanStep(description="Screenshot", action_type="screenshot", order=0),
            PlanStep(description="Click", action_type="mouse_click", order=1),
            PlanStep(description="Type", action_type="keyboard_type", parameters={"text": "hello"}, order=2),
            PlanStep(description="Wait", action_type="wait", parameters={"duration": 2.0}, order=3),
        ]

        duration = task_planner.estimate_plan_duration(plan)
        assert duration > 0
        assert duration >= 2.0  # At least the wait time

    def test_optimize_plan(self, task_planner):
        """Test plan optimization."""
        plan = ActionPlan(goal="Test")
        plan.steps = [
            PlanStep(description="Screenshot 1", action_type="screenshot", order=0),
            PlanStep(description="Screenshot 2", action_type="screenshot", order=1),
            PlanStep(description="Type a", action_type="keyboard_type", parameters={"text": "a"}, order=2),
            PlanStep(description="Type b", action_type="keyboard_type", parameters={"text": "b"}, order=3),
        ]

        optimized = task_planner.optimize_plan(plan)

        # Should merge consecutive screenshots and keyboard types
        screenshot_count = sum(1 for s in optimized.steps if s.action_type == "screenshot")
        type_count = sum(1 for s in optimized.steps if s.action_type == "keyboard_type")

        assert screenshot_count == 1
        assert type_count == 1


class TestPlannerIntegration:
    """Integration tests for Task Planner."""

    @pytest.mark.asyncio
    async def test_full_planning_cycle(self):
        """Test complete planning cycle."""
        planner = TaskPlanner()

        # Create plan
        plan = await planner.create_plan("Open browser and navigate to example.com")

        assert plan is not None
        assert len(plan.steps) > 0

        # Optimize
        optimized = planner.optimize_plan(plan)
        assert len(optimized.steps) <= len(plan.steps)

        # Estimate duration
        duration = planner.estimate_plan_duration(optimized)
        assert duration > 0
