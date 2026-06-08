"""Action Executor for executing planned actions."""
import asyncio
import json
import random
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from agents.vision.vision import vision_engine
from agents.ocr.ocr import ocr_engine
from config import settings
from security import AuditLogger, SecurityPolicy


@dataclass
class ActionResult:
    """Result of an action execution."""
    success: bool
    action_type: str
    parameters: Dict[str, Any]
    result: Optional[str] = None
    error: Optional[str] = None
    screenshot_before: Optional[str] = None
    screenshot_after: Optional[str] = None
    duration_ms: int = 0
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "action_type": self.action_type,
            "parameters": self.parameters,
            "result": self.result,
            "error": self.error,
            "screenshot_before": self.screenshot_before,
            "screenshot_after": self.screenshot_after,
            "duration_ms": self.duration_ms,
            "metadata": self.metadata,
        }


class ActionExecutor:
    """Executor for performing computer actions."""

    def __init__(self):
        self.playwright = None
        self.browser = None
        self.browser_context = None
        self.page = None
        self.session_screenshots: List[str] = []
        self.session_actions: List[Dict[str, Any]] = []
        logger.info("ActionExecutor initialized")

    async def execute_action(
        self,
        action_type: str,
        parameters: Dict[str, Any],
        session_id: Optional[str] = None,
        task_id: Optional[str] = None,
        require_approval: bool = False,
    ) -> ActionResult:
        """Execute a single action."""
        start_time = time.time()

        # Security validation
        valid, error = SecurityPolicy.validate_action(action_type, parameters)
        if not valid:
            return ActionResult(
                success=False,
                action_type=action_type,
                parameters=parameters,
                error=f"Security validation failed: {error}",
            )

        # Take screenshot before action
        screenshot_before = None
        try:
            _, screenshot_before = vision_engine.capture_screenshot()
        except Exception:
            pass

        result = None
        error = None

        try:
            # Execute based on action type
            if action_type.startswith("mouse_"):
                result = await self._execute_mouse_action(action_type, parameters)
            elif action_type.startswith("keyboard_"):
                result = await self._execute_keyboard_action(action_type, parameters)
            elif action_type == "scroll":
                result = await self._execute_scroll(parameters)
            elif action_type.startswith("open_app") or action_type == "close_app":
                result = await self._execute_app_action(action_type, parameters)
            elif action_type.startswith("switch_window") or action_type == "resize_window":
                result = await self._execute_window_action(action_type, parameters)
            elif action_type.startswith("browser_"):
                result = await self._execute_browser_action(action_type, parameters)
            elif action_type == "wait":
                result = await self._execute_wait(parameters)
            elif action_type == "screenshot":
                result = await self._execute_screenshot(parameters)
            elif action_type == "ocr":
                result = await self._execute_ocr(parameters)
            elif action_type == "vision_analyze":
                result = await self._execute_vision_analyze(parameters)
            else:
                error = f"Unknown action type: {action_type}"

        except Exception as e:
            error = str(e)
            logger.error(f"Action execution failed: {action_type} - {e}")

        # Take screenshot after action
        screenshot_after = None
        try:
            _, screenshot_after = vision_engine.capture_screenshot()
        except Exception:
            pass

        duration_ms = int((time.time() - start_time) * 1000)

        # Log action
        AuditLogger.log_action(
            action_type=action_type,
            parameters=parameters,
            result="success" if error is None else f"failed: {error}",
            session_id=session_id,
        )

        return ActionResult(
            success=error is None,
            action_type=action_type,
            parameters=parameters,
            result=result,
            error=error,
            screenshot_before=screenshot_before,
            screenshot_after=screenshot_after,
            duration_ms=duration_ms,
        )

    async def _execute_mouse_action(self, action_type: str, parameters: Dict[str, Any]) -> str:
        """Execute mouse actions."""
        import pyautogui

        # Configure pyautogui for safety
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.1

        x = parameters.get("x")
        y = parameters.get("y")

        if action_type == "mouse_move":
            if x is not None and y is not None:
                # Human-like movement with bezier curve
                await self._human_like_mouse_move(x, y)
                return f"Mouse moved to ({x}, {y})"
            else:
                raise ValueError("Coordinates required for mouse_move")

        elif action_type == "mouse_click":
            if x is not None and y is not None:
                await self._human_like_mouse_move(x, y)
            pyautogui.click()
            return "Mouse clicked"

        elif action_type == "mouse_double_click":
            if x is not None and y is not None:
                await self._human_like_mouse_move(x, y)
            pyautogui.doubleClick()
            return "Mouse double-clicked"

        elif action_type == "mouse_right_click":
            if x is not None and y is not None:
                await self._human_like_mouse_move(x, y)
            pyautogui.rightClick()
            return "Mouse right-clicked"

        elif action_type == "mouse_drag":
            x1 = parameters.get("x1")
            y1 = parameters.get("y1")
            x2 = parameters.get("x2")
            y2 = parameters.get("y2")
            if all(v is not None for v in [x1, y1, x2, y2]):
                pyautogui.moveTo(x1, y1)
                pyautogui.dragTo(x2, y2, duration=0.5)
                return f"Dragged from ({x1}, {y1}) to ({x2}, {y2})"
            else:
                raise ValueError("Start and end coordinates required for drag")

        return "Mouse action completed"

    async def _human_like_mouse_move(self, target_x: int, target_y: int) -> None:
        """Move mouse with human-like bezier curve movement."""
        import pyautogui

        current_x, current_y = pyautogui.position()

        # Generate bezier curve points
        steps = random.randint(15, 30)

        # Control points for curve
        mid_x = (current_x + target_x) / 2 + random.randint(-50, 50)
        mid_y = (current_y + target_y) / 2 + random.randint(-50, 50)

        for t in range(steps + 1):
            t_normalized = t / steps

            # Quadratic bezier curve
            x = (1 - t_normalized)**2 * current_x + 2 * (1 - t_normalized) * t_normalized * mid_x + t_normalized**2 * target_x
            y = (1 - t_normalized)**2 * current_y + 2 * (1 - t_normalized) * t_normalized * mid_y + t_normalized**2 * target_y

            # Add slight jitter
            x += random.randint(-2, 2)
            y += random.randint(-2, 2)

            pyautogui.moveTo(int(x), int(y), duration=0.01)
            await asyncio.sleep(0.01)

    async def _execute_keyboard_action(self, action_type: str, parameters: Dict[str, Any]) -> str:
        """Execute keyboard actions."""
        import pyautogui

        if action_type == "keyboard_type":
            text = parameters.get("text", "")
            interval = parameters.get("interval", 0.01)

            # Human-like typing with variable speed
            for char in text:
                pyautogui.typewrite(char, interval=interval)
                # Random pause between characters
                if random.random() < 0.1:
                    await asyncio.sleep(random.uniform(0.05, 0.2))

            return f"Typed: {text[:50]}{'...' if len(text) > 50 else ''}"

        elif action_type == "keyboard_shortcut":
            shortcut = parameters.get("shortcut", "")
            keys = shortcut.lower().split("+")

            # Map key names
            key_map = {
                "ctrl": "ctrl",
                "alt": "alt",
                "shift": "shift",
                "win": "win",
                "cmd": "command",
                "tab": "tab",
                "enter": "enter",
                "esc": "esc",
                "space": "space",
                "delete": "delete",
                "backspace": "backspace",
                "up": "up",
                "down": "down",
                "left": "left",
                "right": "right",
            }

            mapped_keys = [key_map.get(k, k) for k in keys]
            pyautogui.hotkey(*mapped_keys)
            return f"Pressed shortcut: {shortcut}"

        return "Keyboard action completed"

    async def _execute_scroll(self, parameters: Dict[str, Any]) -> str:
        """Execute scroll action."""
        import pyautogui

        direction = parameters.get("direction", "down")
        amount = parameters.get("amount", 3)
        x = parameters.get("x")
        y = parameters.get("y")

        if x is not None and y is not None:
            pyautogui.moveTo(x, y)

        if direction == "down":
            pyautogui.scroll(-amount * 100)
            return f"Scrolled down {amount} units"
        elif direction == "up":
            pyautogui.scroll(amount * 100)
            return f"Scrolled up {amount} units"
        elif direction == "left":
            pyautogui.hscroll(-amount * 100)
            return f"Scrolled left {amount} units"
        elif direction == "right":
            pyautogui.hscroll(amount * 100)
            return f"Scrolled right {amount} units"

        return "Scroll completed"

    async def _execute_app_action(self, action_type: str, parameters: Dict[str, Any]) -> str:
        """Execute application actions."""
        import subprocess
        import sys

        if action_type == "open_app":
            app_name = parameters.get("app_name", "")

            if sys.platform == "win32":
                # Windows
                subprocess.Popen(["start", app_name], shell=True)
            elif sys.platform == "darwin":
                # macOS
                subprocess.Popen(["open", "-a", app_name])
            else:
                # Linux
                subprocess.Popen([app_name])

            await asyncio.sleep(2)  # Wait for app to open
            return f"Opened application: {app_name}"

        elif action_type == "close_app":
            app_name = parameters.get("app_name", "")

            if sys.platform == "win32":
                subprocess.run(["taskkill", "/f", "/im", app_name], capture_output=True)
            elif sys.platform == "darwin":
                subprocess.run(["pkill", app_name], capture_output=True)
            else:
                subprocess.run(["pkill", app_name], capture_output=True)

            return f"Closed application: {app_name}"

        return "App action completed"

    async def _execute_window_action(self, action_type: str, parameters: Dict[str, Any]) -> str:
        """Execute window management actions."""
        if action_type == "switch_window":
            window_title = parameters.get("title", "")

            try:
                import pygetwindow as gw
                window = gw.getWindowsWithTitle(window_title)[0]
                window.activate()
                return f"Switched to window: {window_title}"
            except Exception as e:
                return f"Window switch failed: {e}"

        elif action_type == "resize_window":
            width = parameters.get("width", 800)
            height = parameters.get("height", 600)

            try:
                import pyautogui
                window = pyautogui.getActiveWindow()
                if window:
                    window.resizeTo(width, height)
                    return f"Resized window to {width}x{height}"
            except Exception as e:
                return f"Window resize failed: {e}"

        return "Window action completed"

    async def _execute_browser_action(self, action_type: str, parameters: Dict[str, Any]) -> str:
        """Execute browser automation actions using Playwright."""
        from playwright.async_api import async_playwright

        if action_type == "browser_open":
            if self.browser is None:
                self.playwright = await async_playwright().start()
                self.browser = await self.playwright.chromium.launch(headless=False)
                self.browser_context = await self.browser.new_context(
                    viewport={"width": 1920, "height": 1080},
                )
                self.page = await self.browser_context.new_page()
            return "Browser opened"

        if self.page is None:
            raise RuntimeError("Browser not initialized. Call browser_open first.")

        if action_type == "browser_navigate":
            url = parameters.get("url", "")
            SecurityPolicy.validate_url(url)
            await self.page.goto(url, wait_until="networkidle")
            return f"Navigated to: {url}"

        elif action_type == "browser_click":
            selector = parameters.get("selector", "")
            x = parameters.get("x")
            y = parameters.get("y")

            if selector:
                await self.page.click(selector)
                return f"Clicked element: {selector}"
            elif x is not None and y is not None:
                await self.page.mouse.click(x, y)
                return f"Clicked at ({x}, {y})"
            else:
                raise ValueError("Selector or coordinates required for browser_click")

        elif action_type == "browser_type":
            selector = parameters.get("selector", "")
            text = parameters.get("text", "")

            if selector:
                await self.page.fill(selector, text)
                return f"Typed '{text}' into {selector}"
            else:
                raise ValueError("Selector required for browser_type")

        elif action_type == "browser_upload":
            selector = parameters.get("selector", "")
            file_path = parameters.get("file_path", "")

            if selector and file_path:
                await self.page.set_input_files(selector, file_path)
                return f"Uploaded file: {file_path}"
            else:
                raise ValueError("Selector and file_path required for browser_upload")

        elif action_type == "browser_download":
            url = parameters.get("url", "")
            file_name = parameters.get("file_name", "")

            if url:
                async with self.page.expect_download() as download_info:
                    await self.page.goto(url)
                download = await download_info.value
                path = await download.path()
                return f"Downloaded file to: {path}"
            else:
                raise ValueError("URL required for browser_download")

        elif action_type == "browser_scroll":
            direction = parameters.get("direction", "down")
            amount = parameters.get("amount", 3)

            if direction == "down":
                await self.page.evaluate(f"window.scrollBy(0, {amount * 100})")
            elif direction == "up":
                await self.page.evaluate(f"window.scrollBy(0, -{amount * 100})")

            return f"Browser scrolled {direction}"

        return "Browser action completed"

    async def _execute_wait(self, parameters: Dict[str, Any]) -> str:
        """Execute wait action."""
        duration = parameters.get("duration", 1.0)
        await asyncio.sleep(duration)
        return f"Waited {duration} seconds"

    async def _execute_screenshot(self, parameters: Dict[str, Any]) -> str:
        """Execute screenshot action."""
        _, path = vision_engine.capture_screenshot()
        if path:
            return f"Screenshot saved: {path}"
        return "Screenshot captured"

    async def _execute_ocr(self, parameters: Dict[str, Any]) -> str:
        """Execute OCR action."""
        x = parameters.get("x")
        y = parameters.get("y")
        width = parameters.get("width")
        height = parameters.get("height")
        languages = parameters.get("languages", ["en"])

        # Capture screenshot
        img, _ = vision_engine.capture_screenshot(save=False)

        if all(v is not None for v in [x, y, width, height]):
            # OCR specific region
            roi = img[y:y+height, x:x+width]
            region = ocr_engine.read_text_at_region(img, x, y, width, height, languages)
            if region:
                return f"OCR Result: {region.text}"
        else:
            # OCR full screen
            text = ocr_engine.get_all_text(img, languages)
            return f"OCR Result: {text[:500]}{'...' if len(text) > 500 else ''}"

        return "OCR completed"

    async def _execute_vision_analyze(self, parameters: Dict[str, Any]) -> str:
        """Execute vision analysis action."""
        img, _ = vision_engine.capture_screenshot(save=False)
        analysis = vision_engine.analyze_image(img)
        return f"Vision Analysis: {json.dumps(analysis, indent=2)[:1000]}"

    async def close_browser(self) -> None:
        """Close browser and cleanup."""
        if self.browser:
            await self.browser.close()
            self.browser = None
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None
        self.page = None
        self.browser_context = None


# Global executor instance
executor = ActionExecutor()
