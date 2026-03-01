#!/usr/bin/env python3
"""
核心维度与枚举顺序契约

集中维护状态/动作空间维度，避免多文件硬编码漂移。
"""

from typing import Final


TASK_TYPE_ORDER: Final[tuple[str, ...]] = ("T1", "T2", "T3", "T4")
TECH_STACK_ORDER: Final[tuple[str, ...]] = (
    "react",
    "vue",
    "fastapi",
    "express",
    "python",
    "javascript",
    "typescript",
    "go",
)
USER_MOOD_ORDER: Final[tuple[str, ...]] = ("focused", "relaxed", "stressed")

AGENT_ORDER: Final[tuple[str, ...]] = ("claude", "codex", "gemini")
AUTOMATION_ORDER: Final[tuple[str, ...]] = ("low", "medium", "high")
STYLE_ORDER: Final[tuple[str, ...]] = ("brief", "detailed", "interactive")
CONFIRM_ORDER: Final[tuple[bool, ...]] = (False, True)

STATE_DIMENSIONS: Final[dict[str, int]] = {
    "task_type": len(TASK_TYPE_ORDER),
    "tech_stack": len(TECH_STACK_ORDER),
    "user_mood": len(USER_MOOD_ORDER),
    "time_of_day": 1,
    "recent_performance": 1,
}
STATE_VECTOR_DIM: Final[int] = sum(STATE_DIMENSIONS.values())

ACTION_HEAD_DIMS: Final[dict[str, int]] = {
    "agent": len(AGENT_ORDER),
    "automation": len(AUTOMATION_ORDER),
    "style": len(STYLE_ORDER),
    "confirm": len(CONFIRM_ORDER),
}
ACTION_VECTOR_DIM: Final[int] = sum(ACTION_HEAD_DIMS.values())
