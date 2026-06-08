"""Task Planner for creating and managing action plans."""
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from loguru import logger

from config import settings


class PlanStepStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class PlanStep:
    """A single step in an action plan."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    description: str = ""
    action_type: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    expected_result: str = ""
    status: PlanStepStatus = PlanStepStatus.PENDING
    order: int = 0
    depends_on: List[str] = field(default_factory=list)
    retry_count: int = 0
    max_retries: int = 3
    result: Optional[str] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "description": self.description,
            "action_type": self.action_type,
            "parameters": self.parameters,
            "expected_result": self.expected_result,
            "status": self.status.value,
            "order": self.order,
            "depends_on": self.depends_on,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "result": self.result,
            "error": self.error,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


@dataclass
class ActionPlan:
    """Complete action plan for a task."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    task_description: str = ""
    goal: str = ""
    steps: List[PlanStep] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    status: str = "pending"
    current_step_index: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "task_description": self.task_description,
            "goal": self.goal,
            "steps": [step.to_dict() for step in self.steps],
            "context": self.context,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "status": self.status,
            "current_step_index": self.current_step_index,
            "metadata": self.metadata,
        }

    @property
    def current_step(self) -> Optional[PlanStep]:
        """Get the current step."""
        if 0 <= self.current_step_index < len(self.steps):
            return self.steps[self.current_step_index]
        return None

    @property
    def is_complete(self) -> bool:
        """Check if all steps are completed."""
        return all(step.status == PlanStepStatus.COMPLETED for step in self.steps)

    @property
    def has_failed(self) -> bool:
        """Check if any step has failed beyond retries."""
        return any(
            step.status == PlanStepStatus.FAILED and step.retry_count >= step.max_retries
            for step in self.steps
        )

    def get_next_step(self) -> Optional[PlanStep]:
        """Get the next pending step."""
        for step in self.steps:
            if step.status == PlanStepStatus.PENDING:
                # Check dependencies
                if all(
                    self.get_step_by_id(dep_id).status == PlanStepStatus.COMPLETED
                    for dep_id in step.depends_on
                    if self.get_step_by_id(dep_id)
                ):
                    return step
        return None

    def get_step_by_id(self, step_id: str) -> Optional[PlanStep]:
        """Get a step by its ID."""
        for step in self.steps:
            if step.id == step_id:
                return step
        return None

    def mark_step_complete(self, step_id: str, result: str) -> None:
        """Mark a step as completed."""
        step = self.get_step_by_id(step_id)
        if step:
            step.status = PlanStepStatus.COMPLETED
            step.result = result
            step.completed_at = datetime.utcnow()
            self.updated_at = datetime.utcnow()

    def mark_step_failed(self, step_id: str, error: str) -> None:
        """Mark a step as failed."""
        step = self.get_step_by_id(step_id)
        if step:
            step.status = PlanStepStatus.FAILED
            step.error = error
            step.retry_count += 1
            self.updated_at = datetime.utcnow()

    def retry_step(self, step_id: str) -> bool:
        """Retry a failed step."""
        step = self.get_step_by_id(step_id)
        if step and step.retry_count < step.max_retries:
            step.status = PlanStepStatus.PENDING
            step.error = None
            self.updated_at = datetime.utcnow()
            return True
        return False


class TaskPlanner:
    """Task planner that creates action plans using LLM reasoning."""

    PLANNING_PROMPT = """You are an expert computer automation planner. Your task is to break down a high-level goal into a sequence of specific, actionable steps.

You have access to the following action types:
- mouse_move: Move mouse to coordinates (x, y)
- mouse_click: Click at current position or coordinates (x, y)
- mouse_double_click: Double click at coordinates
- mouse_right_click: Right click at coordinates
- mouse_drag: Drag from (x1, y1) to (x2, y2)
- keyboard_type: Type text at current focus
- keyboard_shortcut: Press keyboard shortcuts (e.g., ctrl+c, alt+tab)
- scroll: Scroll up or down at position
- open_app: Open an application by name
- close_app: Close an application
- switch_window: Switch to a window by title
- resize_window: Resize window to dimensions
- browser_open: Open a browser
- browser_navigate: Navigate to URL
- browser_click: Click on element in browser
- browser_type: Type in browser element
- browser_upload: Upload file in browser
- browser_download: Download file from browser
- browser_scroll: Scroll in browser
- wait: Wait for a specified duration
- screenshot: Take a screenshot
- ocr: Read text from screen
- vision_analyze: Analyze screen content

Current screen context:
{screen_context}

Task history:
{task_history}

Create a detailed step-by-step plan to accomplish this goal:
Goal: {goal}

Return your response as a JSON object with the following structure:
{{
    "goal": "restated goal",
    "context": {{
        "assumptions": ["list of assumptions"],
        "constraints": ["list of constraints"],
        "required_info": ["information needed"]
    }},
    "steps": [
        {{
            "description": "clear description of what this step does",
            "action_type": "one of the action types above",
            "parameters": {{"key": "value"}},
            "expected_result": "what should happen after this step",
            "depends_on": ["ids of steps that must complete before this"]
        }}
    ]
}}

Rules:
1. Each step must be specific and actionable
2. Include verification steps (screenshots, OCR) after critical actions
3. Add wait steps after actions that may take time
4. Consider error cases and add recovery steps
5. Steps should be ordered logically with dependencies
6. Be conservative - prefer safe actions over risky ones
"""

    def __init__(self):
        self.llm = None
        self._init_llm()
        logger.info("TaskPlanner initialized")

    def _init_llm(self):
        """Initialize LLM client."""
        try:
            from langchain_openai import ChatOpenAI
            self.llm = ChatOpenAI(
                model=settings.openai_model,
                api_key=settings.openai_api_key,
                temperature=0.2,
            )
        except Exception as e:
            logger.warning(f"OpenAI LLM init failed: {e}")
            try:
                from langchain_anthropic import ChatAnthropic
                self.llm = ChatAnthropic(
                    model=settings.anthropic_model,
                    api_key=settings.anthropic_api_key,
                    temperature=0.2,
                )
            except Exception as e2:
                logger.warning(f"Anthropic LLM init failed: {e2}")
                self.llm = None

    async def create_plan(
        self,
        goal: str,
        screen_context: Optional[Dict[str, Any]] = None,
        task_history: Optional[List[Dict[str, Any]]] = None,
    ) -> ActionPlan:
        """Create an action plan for a given goal."""
        plan = ActionPlan(
            task_description=goal,
            goal=goal,
        )

        if self.llm is None:
            # Fallback: create a simple manual plan
            plan.steps = self._create_fallback_plan(goal)
            return plan

        try:
            # Prepare context
            screen_ctx = json.dumps(screen_context or {}, indent=2)
            history = json.dumps(task_history or [], indent=2)

            # Create prompt
            prompt = ChatPromptTemplate.from_messages([
                SystemMessage(content="You are an expert computer automation planner."),
                HumanMessage(content=self.PLANNING_PROMPT.format(
                    goal=goal,
                    screen_context=screen_ctx,
                    task_history=history,
                )),
            ])

            # Get plan from LLM
            response = await self.llm.ainvoke(prompt.format_messages())
            plan_data = JsonOutputParser().parse(response.content)

            # Parse steps
            for i, step_data in enumerate(plan_data.get("steps", [])):
                step = PlanStep(
                    description=step_data.get("description", ""),
                    action_type=step_data.get("action_type", ""),
                    parameters=step_data.get("parameters", {}),
                    expected_result=step_data.get("expected_result", ""),
                    depends_on=step_data.get("depends_on", []),
                    order=i,
                )
                plan.steps.append(step)

            # Update plan context
            plan.context = plan_data.get("context", {})
            plan.goal = plan_data.get("goal", goal)

            logger.info(f"Plan created with {len(plan.steps)} steps")

        except Exception as e:
            logger.error(f"Plan creation failed: {e}")
            plan.steps = self._create_fallback_plan(goal)

        return plan

    def _create_fallback_plan(self, goal: str) -> List[PlanStep]:
        """Create a simple fallback plan when LLM is unavailable."""
        steps = []

        # Always start with observation
        steps.append(PlanStep(
            description="Take screenshot to observe current state",
            action_type="screenshot",
            parameters={},
            expected_result="Screenshot captured for analysis",
            order=0,
        ))

        # Add a generic action based on goal keywords
        goal_lower = goal.lower()

        if "browser" in goal_lower or "website" in goal_lower or "url" in goal_lower:
            steps.append(PlanStep(
                description="Open browser",
                action_type="browser_open",
                parameters={},
                expected_result="Browser opened",
                order=1,
            ))
        elif "open" in goal_lower and "app" in goal_lower:
            app_name = goal_lower.replace("open", "").replace("app", "").strip()
            steps.append(PlanStep(
                description=f"Open application: {app_name}",
                action_type="open_app",
                parameters={"app_name": app_name or "notepad"},
                expected_result="Application opened",
                order=1,
            ))
        elif "type" in goal_lower or "enter" in goal_lower:
            steps.append(PlanStep(
                description="Type text at current focus",
                action_type="keyboard_type",
                parameters={"text": "Sample text"},
                expected_result="Text typed successfully",
                order=1,
            ))
        elif "click" in goal_lower:
            steps.append(PlanStep(
                description="Click at specified location",
                action_type="mouse_click",
                parameters={"x": 500, "y": 500},
                expected_result="Click executed",
                order=1,
            ))
        else:
            steps.append(PlanStep(
                description="Perform basic interaction",
                action_type="screenshot",
                parameters={},
                expected_result="Current state observed",
                order=1,
            ))

        # Always end with verification
        steps.append(PlanStep(
            description="Verify final state with screenshot",
            action_type="screenshot",
            parameters={},
            expected_result="Final state captured",
            order=len(steps),
        ))

        return steps

    async def replan(
        self,
        plan: ActionPlan,
        failed_step: PlanStep,
        error_message: str,
        current_state: Optional[Dict[str, Any]] = None,
    ) -> ActionPlan:
        """Create a revised plan after a step failure."""
        logger.info(f"Replanning after failure: {error_message}")

        # Mark current step as failed
        plan.mark_step_failed(failed_step.id, error_message)

        if self.llm is None:
            # Simple fallback: add retry step
            if plan.retry_step(failed_step.id):
                return plan

            # Add alternative step
            alt_step = PlanStep(
                description=f"Alternative approach for: {failed_step.description}",
                action_type="screenshot",
                parameters={},
                expected_result="Alternative path explored",
                order=failed_step.order + 1,
            )
            plan.steps.insert(failed_step.order + 1, alt_step)
            return plan

        try:
            # Create replanning prompt
            replan_prompt = f"""The following step failed:
Step: {failed_step.description}
Action: {failed_step.action_type}
Parameters: {json.dumps(failed_step.parameters)}
Error: {error_message}

Current plan progress:
{json.dumps([s.to_dict() for s in plan.steps], indent=2)}

Current state:
{json.dumps(current_state or {}, indent=2)}

Create a revised plan to recover from this failure and continue toward the goal.
Return JSON with additional recovery steps."""

            response = await self.llm.ainvoke(replan_prompt)
            recovery_data = JsonOutputParser().parse(response.content)

            # Add recovery steps
            for step_data in recovery_data.get("steps", []):
                step = PlanStep(
                    description=step_data.get("description", ""),
                    action_type=step_data.get("action_type", ""),
                    parameters=step_data.get("parameters", {}),
                    expected_result=step_data.get("expected_result", ""),
                    order=failed_step.order + 1,
                )
                plan.steps.insert(failed_step.order + 1, step)

            # Retry the failed step
            plan.retry_step(failed_step.id)

        except Exception as e:
            logger.error(f"Replanning failed: {e}")
            # Simple fallback
            plan.retry_step(failed_step.id)

        return plan

    def optimize_plan(self, plan: ActionPlan) -> ActionPlan:
        """Optimize a plan by removing redundant steps and merging similar actions."""
        optimized_steps = []

        for step in plan.steps:
            # Skip redundant screenshots
            if step.action_type == "screenshot" and optimized_steps:
                last_step = optimized_steps[-1]
                if last_step.action_type == "screenshot":
                    continue

            # Merge consecutive keyboard types
            if step.action_type == "keyboard_type" and optimized_steps:
                last_step = optimized_steps[-1]
                if last_step.action_type == "keyboard_type":
                    last_step.parameters["text"] += step.parameters.get("text", "")
                    last_step.description += " + " + step.description
                    continue

            optimized_steps.append(step)

        # Reorder
        for i, step in enumerate(optimized_steps):
            step.order = i

        plan.steps = optimized_steps
        return plan

    def estimate_plan_duration(self, plan: ActionPlan) -> float:
        """Estimate the total duration of a plan in seconds."""
        duration = 0.0

        action_durations = {
            "mouse_move": 0.5,
            "mouse_click": 0.3,
            "mouse_double_click": 0.4,
            "mouse_right_click": 0.3,
            "mouse_drag": 1.0,
            "keyboard_type": 0.1,  # per character
            "keyboard_shortcut": 0.5,
            "scroll": 0.5,
            "open_app": 3.0,
            "close_app": 1.0,
            "switch_window": 1.0,
            "resize_window": 1.0,
            "browser_open": 3.0,
            "browser_navigate": 2.0,
            "browser_click": 0.5,
            "browser_type": 0.1,
            "browser_upload": 2.0,
            "browser_download": 5.0,
            "browser_scroll": 0.5,
            "wait": 1.0,
            "screenshot": 0.5,
            "ocr": 1.0,
            "vision_analyze": 2.0,
        }

        for step in plan.steps:
            base_duration = action_durations.get(step.action_type, 1.0)

            # Adjust for typing length
            if step.action_type in ["keyboard_type", "browser_type"]:
                text_length = len(step.parameters.get("text", ""))
                base_duration *= max(1, text_length)

            # Adjust for wait duration
            if step.action_type == "wait":
                base_duration = step.parameters.get("duration", 1.0)

            duration += base_duration

        return duration


# Global planner instance
planner = TaskPlanner()
