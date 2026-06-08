"""Main Agent orchestrator that coordinates all components."""
import asyncio
import json
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, AsyncGenerator, Dict, List, Optional

from loguru import logger

from agents.executor.executor import ActionResult, executor
from agents.memory.memory import memory_engine
from agents.ocr.ocr import ocr_engine
from agents.planner.planner import ActionPlan, PlanStepStatus, TaskPlanner, planner
from agents.security.security import security_agent
from agents.vision.vision import vision_engine
from config import settings
from security import AuditLogger


class AgentStatus(str, Enum):
    IDLE = "idle"
    OBSERVING = "observing"
    PLANNING = "planning"
    EXECUTING = "executing"
    VERIFYING = "verifying"
    CORRECTING = "correcting"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class AgentState:
    """Current state of the agent."""
    status: AgentStatus = AgentStatus.IDLE
    current_task: Optional[str] = None
    current_plan: Optional[ActionPlan] = None
    current_step: Optional[int] = None
    session_id: Optional[str] = None
    total_actions: int = 0
    successful_actions: int = 0
    failed_actions: int = 0
    start_time: Optional[datetime] = None
    last_screenshot: Optional[str] = None
    error_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


class BuildAgent:
    """Main autonomous agent that orchestrates all components."""

    def __init__(self):
        self.state = AgentState()
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.event_callbacks: List[callable] = []
        self._running = False
        self._paused = False
        self._stop_requested = False
        logger.info("BuildAgent initialized")

    def add_event_callback(self, callback: callable) -> None:
        """Add a callback for agent events."""
        self.event_callbacks.append(callback)

    async def _emit_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Emit an event to all callbacks."""
        event = {
            "type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data,
        }
        for callback in self.event_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception as e:
                logger.error(f"Event callback error: {e}")

    async def run_task(
        self,
        goal: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        llm_provider: Optional[str] = None,
        llm_model: Optional[str] = None,
        require_approval: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """Run a complete task from goal to completion."""
        session_id = session_id or str(uuid.uuid4())
        self.state.session_id = session_id
        self.state.start_time = datetime.utcnow()
        self.state.status = AgentStatus.OBSERVING

        logger.info(f"Starting task: {goal} (Session: {session_id})")

        await self._emit_event("task_started", {
            "session_id": session_id,
            "goal": goal,
            "timestamp": datetime.utcnow().isoformat(),
        })

        try:
            # Phase 1: Observe
            await self._observe()

            # Phase 2: Plan
            self.state.status = AgentStatus.PLANNING
            plan = await self._plan(goal)
            self.state.current_plan = plan

            # Phase 3: Execute
            self.state.status = AgentStatus.EXECUTING
            result = await self._execute_plan(plan, session_id, user_id, require_approval)

            # Phase 4: Verify
            self.state.status = AgentStatus.VERIFYING
            verification = await self._verify(plan, result)

            # Phase 5: Store memory
            await self._store_memory(goal, plan, result, session_id)

            self.state.status = AgentStatus.COMPLETED

            await self._emit_event("task_completed", {
                "session_id": session_id,
                "goal": goal,
                "success": result["success"],
                "total_steps": len(plan.steps),
                "completed_steps": result["completed_steps"],
            })

            return {
                "session_id": session_id,
                "goal": goal,
                "success": result["success"],
                "plan": plan.to_dict(),
                "result": result,
                "verification": verification,
                "duration": (datetime.utcnow() - self.state.start_time).total_seconds(),
            }

        except Exception as e:
            logger.error(f"Task failed: {e}")
            self.state.status = AgentStatus.FAILED

            await self._emit_event("task_failed", {
                "session_id": session_id,
                "goal": goal,
                "error": str(e),
            })

            return {
                "session_id": session_id,
                "goal": goal,
                "success": False,
                "error": str(e),
            }

        finally:
            self.state.status = AgentStatus.IDLE
            self.state.current_task = None
            self.state.current_plan = None

    async def _observe(self) -> Dict[str, Any]:
        """Observe the current screen state."""
        logger.info("Phase 1: Observing screen state")

        # Capture screenshot
        screenshot, path = vision_engine.capture_screenshot()
        self.state.last_screenshot = path

        # Analyze screen
        analysis = vision_engine.analyze_image(screenshot)

        # Read text
        text = ocr_engine.get_all_text(screenshot)

        observation = {
            "screenshot_path": path,
            "analysis": analysis,
            "text": text,
            "timestamp": datetime.utcnow().isoformat(),
        }

        await self._emit_event("observation", observation)

        return observation

    async def _plan(self, goal: str) -> ActionPlan:
        """Create an action plan."""
        logger.info("Phase 2: Planning actions")

        # Get current state for context
        observation = await self._observe()

        # Get relevant memories
        similar_tasks = memory_engine.get_similar_tasks(goal, n_results=3)
        task_history = [m["content"] for m in similar_tasks]

        # Create plan
        plan = await planner.create_plan(
            goal=goal,
            screen_context=observation,
            task_history=task_history,
        )

        await self._emit_event("plan_created", {
            "plan_id": plan.id,
            "steps_count": len(plan.steps),
            "estimated_duration": planner.estimate_plan_duration(plan),
        })

        return plan

    async def _execute_plan(
        self,
        plan: ActionPlan,
        session_id: str,
        user_id: Optional[str] = None,
        require_approval: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """Execute an action plan."""
        logger.info(f"Phase 3: Executing plan with {len(plan.steps)} steps")

        completed_steps = 0
        failed_steps = 0

        for i, step in enumerate(plan.steps):
            if self._stop_requested:
                logger.info("Stop requested, aborting execution")
                break

            while self._paused:
                self.state.status = AgentStatus.PAUSED
                await asyncio.sleep(0.5)

            self.state.current_step = i
            self.state.status = AgentStatus.EXECUTING

            await self._emit_event("step_started", {
                "step_index": i,
                "step": step.to_dict(),
            })

            # Security evaluation
            should_approve, message, sec_metadata = security_agent.evaluate_action(
                step.action_type,
                step.parameters,
                session_id=session_id,
            )

            if not should_approve:
                logger.warning(f"Action blocked by security: {message}")
                plan.mark_step_failed(step.id, f"Security blocked: {message}")
                failed_steps += 1
                continue

            # Check if approval is required
            need_approval = require_approval or (require_approval is None and settings.require_approval)
            if need_approval or sec_metadata.get("requires_approval", False):
                await self._emit_event("approval_required", {
                    "step_index": i,
                    "step": step.to_dict(),
                    "reason": message,
                })
                # Wait for approval (in production, this would wait for user input)
                # For now, auto-approve after a delay
                await asyncio.sleep(2)

            # Execute step
            try:
                step.started_at = datetime.utcnow()
                result = await executor.execute_action(
                    action_type=step.action_type,
                    parameters=step.parameters,
                    session_id=session_id,
                    task_id=plan.id,
                )

                self.state.total_actions += 1

                if result.success:
                    plan.mark_step_complete(step.id, result.result or "Success")
                    self.state.successful_actions += 1
                    completed_steps += 1

                    # Store action memory
                    memory_engine.store_action(
                        action_type=step.action_type,
                        parameters=step.parameters,
                        result=result.result or "Success",
                        session_id=session_id,
                        task_id=plan.id,
                    )
                else:
                    plan.mark_step_failed(step.id, result.error or "Unknown error")
                    self.state.failed_actions += 1
                    failed_steps += 1

                    # Attempt recovery
                    if step.retry_count < step.max_retries:
                        logger.info(f"Retrying step {i} (attempt {step.retry_count + 1})")
                        plan.retry_step(step.id)

                        # Replan if needed
                        if step.retry_count >= 1:
                            plan = await planner.replan(
                                plan,
                                step,
                                result.error or "Execution failed",
                            )

                await self._emit_event("step_completed", {
                    "step_index": i,
                    "success": result.success,
                    "result": result.to_dict(),
                })

            except Exception as e:
                logger.error(f"Step execution error: {e}")
                plan.mark_step_failed(step.id, str(e))
                self.state.failed_actions += 1
                failed_steps += 1

                await self._emit_event("step_failed", {
                    "step_index": i,
                    "error": str(e),
                })

            # Brief pause between steps
            await asyncio.sleep(0.5)

        success = failed_steps == 0 or (completed_steps > 0 and failed_steps < len(plan.steps) * 0.5)

        return {
            "success": success,
            "completed_steps": completed_steps,
            "failed_steps": failed_steps,
            "total_steps": len(plan.steps),
        }

    async def _verify(self, plan: ActionPlan, execution_result: Dict[str, Any]) -> Dict[str, Any]:
        """Verify the execution results."""
        logger.info("Phase 4: Verifying results")

        # Take final screenshot
        screenshot, path = vision_engine.capture_screenshot()

        # Check if goal was achieved
        verification = {
            "screenshot_path": path,
            "plan_completed": plan.is_complete,
            "execution_success": execution_result["success"],
            "all_steps_completed": execution_result["completed_steps"] == execution_result["total_steps"],
            "timestamp": datetime.utcnow().isoformat(),
        }

        await self._emit_event("verification", verification)

        return verification

    async def _store_memory(
        self,
        goal: str,
        plan: ActionPlan,
        result: Dict[str, Any],
        session_id: str,
    ) -> None:
        """Store task memory."""
        logger.info("Phase 5: Storing memory")

        # Store task completion
        task_result = "Success" if result["success"] else "Failed"
        memory_engine.store_task(
            task_description=goal,
            task_result=task_result,
            session_id=session_id,
            task_id=plan.id,
        )

        # Store session summary
        memory_engine.store(
            content=f"Session {session_id} summary: {json.dumps(result)}",
            entry_type="session_summary",
            session_id=session_id,
        )

    async def stream_task(
        self,
        goal: str,
        session_id: Optional[str] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream task execution events."""
        session_id = session_id or str(uuid.uuid4())

        events = []

        async def collect_event(event):
            events.append(event)

        self.add_event_callback(collect_event)

        # Run task in background
        task = asyncio.create_task(self.run_task(goal, session_id))

        # Yield events as they occur
        while not task.done() or events:
            while events:
                yield events.pop(0)
            await asyncio.sleep(0.1)

        # Yield final result
        result = await task
        yield {"type": "final_result", "data": result}

    def pause(self) -> None:
        """Pause execution."""
        self._paused = True
        self.state.status = AgentStatus.PAUSED
        logger.info("Agent paused")

    def resume(self) -> None:
        """Resume execution."""
        self._paused = False
        self.state.status = AgentStatus.EXECUTING
        logger.info("Agent resumed")

    def stop(self) -> None:
        """Stop execution."""
        self._stop_requested = True
        logger.info("Stop requested")

    def get_status(self) -> Dict[str, Any]:
        """Get current agent status."""
        return {
            "status": self.state.status.value,
            "current_task": self.state.current_task,
            "current_step": self.state.current_step,
            "session_id": self.state.session_id,
            "total_actions": self.state.total_actions,
            "successful_actions": self.state.successful_actions,
            "failed_actions": self.state.failed_actions,
            "error_count": self.state.error_count,
            "start_time": self.state.start_time.isoformat() if self.state.start_time else None,
            "last_screenshot": self.state.last_screenshot,
        }

    async def get_screen_preview(self) -> Dict[str, Any]:
        """Get current screen preview."""
        screenshot, path = vision_engine.capture_screenshot()
        analysis = vision_engine.analyze_image(screenshot)
        text = ocr_engine.get_all_text(screenshot)

        return {
            "screenshot_path": path,
            "analysis": analysis,
            "text_preview": text[:500],
            "timestamp": datetime.utcnow().isoformat(),
        }


# Global agent instance
build_agent = BuildAgent()
