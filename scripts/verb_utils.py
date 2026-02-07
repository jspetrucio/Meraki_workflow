"""
Shared verb classification utilities for CNL.

Provides ACTION_VERBS and ANALYSIS_VERBS sets used by:
- task_registry.py — verb-aware find_matching_task()
- agent_router.py — verb-aware _quick_classify() (Story 7.7)

Created: Story 7.2 (HIGH-1 amendment — shared verb utility)
"""

# Action verbs: signal intent to MODIFY configuration
# Includes undo/revert verbs since they still change state.
ACTION_VERBS: frozenset[str] = frozenset({
    "configure",
    "create",
    "change",
    "set",
    "add",
    "remove",
    "delete",
    "enable",
    "disable",
    "update",
    "apply",
    "modify",
    "assign",
    "block",
    "unblock",
    "allow",
    "deny",
    "revert",
    "restore",
    "rollback",
    "undo",
})

# Analysis verbs: signal intent to READ/INSPECT (not modify)
# Includes common noun forms (e.g., "discovery" for "discover") to handle
# natural phrasing like "do a full discovery" or "run a health check".
ANALYSIS_VERBS: frozenset[str] = frozenset({
    "analyze",
    "analysis",
    "check",
    "verify",
    "show",
    "list",
    "why",
    "what",
    "how",
    "status",
    "health",
    "scan",
    "inspect",
    "review",
    "report",
    "discover",
    "discovery",
    "diagnose",
    "compare",
    "find",
    "display",
    "describe",
    "audit",
    "investigate",
})


def detect_verb_type(message: str) -> tuple[bool, bool]:
    """Detect whether a message contains action and/or analysis verbs.

    Args:
        message: User message text

    Returns:
        Tuple of (has_action_verb, has_analysis_verb)
    """
    words = set(message.lower().split())
    has_action = bool(words & ACTION_VERBS)
    has_analysis = bool(words & ANALYSIS_VERBS)
    return has_action, has_analysis
