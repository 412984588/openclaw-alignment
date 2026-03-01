#!/usr/bin/env python3
"""
OpenClaw Alignment API

供外部系统（如 OpenClaw Gateway）调用的 API 接口。
提供智能确认决策和反馈记录功能。
"""

from typing import Dict, Any, Tuple, Optional
from pathlib import Path


class ConfirmationAPI:
    """
    确认 API 类

    供外部系统调用的 API，提供智能确认决策功能。
    """

    def __init__(self, memory_dir: Optional[Path] = None):
        """
        初始化 API

        Args:
            memory_dir: 内存目录路径（默认为当前目录的 .openclaw_memory）
        """
        if memory_dir is None:
            memory_dir = Path.cwd() / ".openclaw_memory"

        self.memory_dir = Path(memory_dir)
        gep_dir = self.memory_dir / "gep"

        # 初始化 GEP Store 和智能确认引擎
        from .gep_store import GEPStore
        from .confirmation import IntelligentConfirmation

        self.gep_store = GEPStore(gep_dir) if gep_dir.exists() else None
        self.conf_engine = IntelligentConfirmation(self.gep_store)

    def should_auto_execute(self, task: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        """
        判断是否应该自动执行

        Args:
            task: 任务上下文，包含：
                - task_type: 任务类型（T1/T2/T3/T4）
                - task_description: 任务描述
                - command: 执行的命令（如果有）
                - files: 涉及的文件列表（如果有）

        Returns:
            (是否自动执行, 原因, 详细信息)

            详细信息包含：
            - confidence: 最大信心度
            - success_streak: 最小连续成功次数
            - relevant_genes_count: 相关 Gene 数量
        """
        should_confirm, reason = self.conf_engine.should_confirm(task)
        confidence_info = self.conf_engine.get_confidence_info(task)

        details = {
            "confidence": confidence_info.get("max_confidence", 0.0),
            "success_streak": confidence_info.get("min_success_streak", 0),
            "relevant_genes_count": confidence_info.get("count", 0)
        }

        return (not should_confirm, reason, details)

    def record_execution_result(self, task: Dict[str, Any], success: bool, auto_executed: bool) -> None:
        """
        记录执行结果

        Args:
            task: 任务上下文
            success: 任务是否成功
            auto_executed: 是否自动执行（无需用户确认）
        """
        self.conf_engine.record_feedback(
            task,
            was_confirmed=not auto_executed,
            user_cancelled=not success
        )

    def get_confidence_history(self, task_type: Optional[str] = None) -> Dict[str, Any]:
        """
        获取 confidence 历史

        Args:
            task_type: 任务类型过滤（可选）

        Returns:
            confidence 历史字典
        """
        if not self.gep_store:
            return {"genes": []}

        genes = self.gep_store.load_genes()

        if task_type:
            relevant_genes = [g for g in genes.values() if task_type in g.trigger]
        else:
            relevant_genes = [g for g in genes.values() if g.confidence > 0.5]

        return {
            "genes": [
                {
                    "id": g.id,
                    "summary": g.summary,
                    "confidence": g.confidence,
                    "success_streak": g.success_streak
                }
                for g in sorted(relevant_genes, key=lambda x: -x.confidence)
            ]
        }

    def get_explanation(self, task: Dict[str, Any], should_confirm: bool, reason: str) -> str:
        """
        生成决策说明

        Args:
            task: 任务上下文
            should_confirm: 是否需要确认
            reason: 原因说明

        Returns:
            格式化的说明文本
        """
        return self.conf_engine.get_explanation(task, should_confirm, reason)


# 便捷函数：快速创建 API 实例
def create_api(memory_dir: Optional[Path] = None) -> ConfirmationAPI:
    """
    创建 ConfirmationAPI 实例

    Args:
        memory_dir: 内存目录路径（默认为当前目录的 .openclaw_memory）

    Returns:
        ConfirmationAPI 实例
    """
    return ConfirmationAPI(memory_dir)
