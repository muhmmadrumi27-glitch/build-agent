"""Security Agent for monitoring and enforcing security policies."""
import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger

from security import AuditLogger, SecurityPolicy


class SecurityAgent:
    """Security agent that monitors actions and enforces policies."""

    # Risk scores for different action types
    ACTION_RISK_SCORES = {
        "mouse_move": 1,
        "mouse_click": 2,
        "mouse_double_click": 2,
        "mouse_right_click": 2,
        "mouse_drag": 3,
        "keyboard_type": 2,
        "keyboard_shortcut": 3,
        "scroll": 1,
        "open_app": 3,
        "close_app": 5,
        "switch_window": 2,
        "resize_window": 2,
        "browser_open": 3,
        "browser_navigate": 4,
        "browser_click": 3,
        "browser_type": 3,
        "browser_upload": 6,
        "browser_download": 6,
        "browser_scroll": 2,
        "wait": 1,
        "screenshot": 1,
        "ocr": 1,
        "vision_analyze": 1,
    }

    # Thresholds
    HIGH_RISK_THRESHOLD = 5
    CRITICAL_RISK_THRESHOLD = 8

    def __init__(self):
        self.active_policies: List[Dict[str, Any]] = []
        self.blocked_patterns: List[str] = []
        self.approval_queue: List[Dict[str, Any]] = []
        self.session_risk_score = 0
        self.action_count = 0
        logger.info("SecurityAgent initialized")

    def evaluate_action(
        self,
        action_type: str,
        parameters: Dict[str, Any],
        user_level: str = "user",
        session_id: Optional[str] = None,
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """Evaluate an action for security compliance."""
        risk_score = self.ACTION_RISK_SCORES.get(action_type, 3)

        # Check for dangerous patterns in parameters
        param_str = json.dumps(parameters).lower()
        for pattern in SecurityPolicy.DANGEROUS_PATTERNS:
            import re
            if re.search(pattern, param_str, re.IGNORECASE):
                AuditLogger.log_security_event(
                    event_type="dangerous_pattern_detected",
                    details={"action": action_type, "pattern": pattern, "parameters": parameters},
                    severity="critical",
                    session_id=session_id,
                )
                return False, f"Dangerous pattern detected: {pattern}", {"risk_score": 10}

        # Check file access
        if "file_path" in parameters or "path" in parameters:
            file_path = parameters.get("file_path") or parameters.get("path", "")
            valid, error = SecurityPolicy.validate_file_access(file_path)
            if not valid:
                AuditLogger.log_security_event(
                    event_type="sensitive_file_access_blocked",
                    details={"file_path": file_path, "action": action_type},
                    severity="high",
                    session_id=session_id,
                )
                return False, error, {"risk_score": 8}

        # Check URL access
        if "url" in parameters:
            valid, error = SecurityPolicy.validate_url(parameters["url"])
            if not valid:
                AuditLogger.log_security_event(
                    event_type="blocked_url_access",
                    details={"url": parameters["url"], "action": action_type},
                    severity="high",
                    session_id=session_id,
                )
                return False, error, {"risk_score": 7}

        # Update session risk score
        self.session_risk_score += risk_score
        self.action_count += 1

        # Check if approval is required
        requires_approval = False
        if risk_score >= self.HIGH_RISK_THRESHOLD:
            requires_approval = True
        if self.session_risk_score > 20 and self.action_count > 5:
            requires_approval = True

        metadata = {
            "risk_score": risk_score,
            "session_risk_score": self.session_risk_score,
            "requires_approval": requires_approval,
            "action_count": self.action_count,
        }

        if requires_approval:
            return True, "Action requires approval", metadata

        return True, "Action approved", metadata

    def approve_action(self, action_id: str, approved_by: str) -> bool:
        """Approve a pending action."""
        for item in self.approval_queue:
            if item["action_id"] == action_id:
                item["approved"] = True
                item["approved_by"] = approved_by
                item["approved_at"] = datetime.utcnow().isoformat()

                AuditLogger.log_security_event(
                    event_type="action_approved",
                    details={"action_id": action_id, "approved_by": approved_by},
                    severity="medium",
                )
                return True
        return False

    def reject_action(self, action_id: str, rejected_by: str, reason: str) -> bool:
        """Reject a pending action."""
        for item in self.approval_queue:
            if item["action_id"] == action_id:
                item["approved"] = False
                item["rejected_by"] = rejected_by
                item["rejection_reason"] = reason

                AuditLogger.log_security_event(
                    event_type="action_rejected",
                    details={"action_id": action_id, "rejected_by": rejected_by, "reason": reason},
                    severity="high",
                )
                return True
        return False

    def add_policy(self, policy: Dict[str, Any]) -> None:
        """Add a security policy."""
        self.active_policies.append(policy)
        logger.info(f"Security policy added: {policy.get('name', 'unnamed')}")

    def remove_policy(self, policy_name: str) -> bool:
        """Remove a security policy."""
        for i, policy in enumerate(self.active_policies):
            if policy.get("name") == policy_name:
                self.active_policies.pop(i)
                logger.info(f"Security policy removed: {policy_name}")
                return True
        return False

    def get_session_summary(self) -> Dict[str, Any]:
        """Get security summary for current session."""
        return {
            "total_actions": self.action_count,
            "total_risk_score": self.session_risk_score,
            "average_risk": self.session_risk_score / max(self.action_count, 1),
            "pending_approvals": len([a for a in self.approval_queue if a.get("approved") is None]),
            "active_policies": len(self.active_policies),
        }

    def reset_session(self) -> None:
        """Reset session security state."""
        self.session_risk_score = 0
        self.action_count = 0
        self.approval_queue = []
        logger.info("Security session reset")


# Global security agent instance
security_agent = SecurityAgent()
