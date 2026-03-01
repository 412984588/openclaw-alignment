#!/usr/bin/env python3
"""
Markdown → GEP 转换器

将现有的 Markdown 配置文件（USER.md/SOUL.md/AGENTS.md）转换为 GEP 格式。
支持自动迁移和增量更新。
"""

import re
import time
from pathlib import Path
from typing import Dict, List, Optional

from .gep import Gene, Capsule, Event
from .gep_store import GEPStore


class MarkdownToGEPConverter:
    """
    Markdown → GEP 转换器

    负责将现有的 Markdown 配置文件转换为 GEP 格式。
    """

    def convert_user_md_to_genes(self, user_md_path: Path) -> Dict[str, Gene]:
        """
        将 USER.md 转换为多个 Gene

        映射关系：
        - 基本信息 → gene_basic_info
        - 工作偏好 → gene_work_habits
        - 沟通风格 → gene_communication_style

        Args:
            user_md_path: USER.md 文件路径

        Returns:
            Gene 字典
        """
        if not user_md_path.exists():
            print(f"⚠️  USER.md 不存在: {user_md_path}")
            return {}

        with open(user_md_path, 'r', encoding='utf-8') as f:
            content = f.read()

        genes = {}

        # 提取基本信息
        basic_info = self._extract_section(content, "Basic Information")
        if basic_info:
            genes["gene_basic_info"] = Gene(
                id=f"gene_basic_info_{int(time.time())}",
                summary="用户基本信息",
                category="optimize",
                strategy=basic_info,
                trigger=["task_start", "user_query"],
                confidence=0.8
            )

        # 提取工作偏好
        work_prefs = self._extract_section(content, "Working Preferences")
        if work_prefs:
            genes["gene_work_habits"] = Gene(
                id=f"gene_work_habits_{int(time.time())}",
                summary="工作习惯偏好",
                category="optimize",
                strategy=work_prefs,
                trigger=["task_execution", "workflow_decision"],
                confidence=0.8
            )

        # 提取备注信息
        notes = self._extract_section(content, "Notes")
        if notes:
            genes["gene_project_constraints"] = Gene(
                id=f"gene_project_constraints_{int(time.time())}",
                summary="项目特定约束",
                category="harden",
                strategy=notes,
                trigger=["constraint_check", "validation"],
                confidence=0.7
            )

        # 为所有 Gene 计算 asset_id
        for gene in genes.values():
            gene.calculate_asset_id()

        return genes

    def convert_soul_md_to_capsule(self, soul_md_path: Path) -> Optional[Capsule]:
        """
        将 SOUL.md 转换为一个 Capsule

        映射关系：SOUL.md → capsule 安全边界

        Args:
            soul_md_path: SOUL.md 文件路径

        Returns:
            Capsule 对象，如果文件不存在则返回 None
        """
        if not soul_md_path.exists():
            print(f"⚠️  SOUL.md 不存在: {soul_md_path}")
            return None

        with open(soul_md_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 提取核心原则
        core_principles = self._extract_section(content, "Core Principles")

        # 提取禁止行为
        prohibited = self._extract_section(content, "Prohibited Actions")

        # 提取奖励信号
        rewards = self._extract_section(content, "Reward Signals")

        # 组合为策略描述
        strategy_parts = []
        if core_principles:
            strategy_parts.append(f"核心原则:\n{core_principles}")
        if prohibited:
            strategy_parts.append(f"禁止行为:\n{prohibited}")
        if rewards:
            strategy_parts.append(f"奖励信号:\n{rewards}")

        strategy = "\n\n".join(strategy_parts)

        # 创建 Capsule
        capsule = Capsule(
            id=f"capsule_safety_{int(time.time())}",
            summary="安全边界和核心原则",
            genes_used=[],  # 初始为空，后续可通过学习填充
            trigger=["high_risk_operation", "safety_check", "boundary_validation"],
            category="harden",
            confidence=0.9
        )
        capsule.calculate_asset_id()

        return capsule

    def convert_agents_md_to_genes(self, agents_md_path: Path) -> Dict[str, Gene]:
        """
        将 AGENTS.md 转换为多个 Gene

        映射关系：每个 agent 配置 → 一个 Gene

        Args:
            agents_md_path: AGENTS.md 文件路径

        Returns:
            Gene 字典
        """
        if not agents_md_path.exists():
            print(f"⚠️  AGENTS.md 不存在: {agents_md_path}")
            return {}

        with open(agents_md_path, 'r', encoding='utf-8') as f:
            content = f.read()

        genes = {}

        # 提取工具调度配置
        tool_dispatch = self._extract_section(content, "Tool Dispatch")
        if tool_dispatch:
            genes["gene_tool_dispatch"] = Gene(
                id=f"gene_tool_dispatch_{int(time.time())}",
                summary="Agent 工具调度策略",
                category="optimize",
                strategy=tool_dispatch,
                trigger=["agent_selection", "task_dispatch"],
                confidence=0.8
            )

        # 提取操作规则
        operation_rules = self._extract_section(content, "Operation Rules")
        if operation_rules:
            genes["gene_operation_rules"] = Gene(
                id=f"gene_operation_rules_{int(time.time())}",
                summary="Agent 操作规则",
                category="harden",
                strategy=operation_rules,
                trigger=["operation_check", "validation"],
                confidence=0.8
            )

        # 提取升级策略
        escalation = self._extract_section(content, "Escalation")
        if escalation:
            genes["gene_escalation"] = Gene(
                id=f"gene_escalation_{int(time.time())}",
                summary="不确定时升级策略",
                category="harden",
                strategy=escalation,
                trigger=["high_uncertainty", "escalation_request"],
                confidence=0.8
            )

        # 为所有 Gene 计算 asset_id
        for gene in genes.values():
            gene.calculate_asset_id()

        return genes

    def migrate_all(self, memory_dir: Path, gep_store: GEPStore) -> None:
        """
        自动迁移所有 MD 文件到 GEP 格式

        1. 读取 USER.md/SOUL.md/AGENTS.md
        2. 转换为 Gene/Capsule
        3. 保存到 GEP Store
        4. 记录迁移 Event

        Args:
            memory_dir: 内存目录（包含 MD 文件）
            gep_store: GEP Store 实例
        """
        print("🔄 开始迁移 Markdown 文件到 GEP 格式...")

        user_md = memory_dir / "USER.md"
        soul_md = memory_dir / "SOUL.md"
        agents_md = memory_dir / "AGENTS.md"

        # 转换 USER.md → Genes
        if user_md.exists():
            print(f"📄 处理 USER.md...")
            user_genes = self.convert_user_md_to_genes(user_md)
            existing_genes = gep_store.load_genes()
            existing_genes.update(user_genes)
            gep_store.save_genes(existing_genes)
            print(f"✅ 导入 {len(user_genes)} 个 Gene（来自 USER.md）")

            # 记录 Event
            for gene in user_genes.values():
                event = Event(
                    timestamp=self._current_timestamp(),
                    event_type="gene_created",
                    asset_id=gene.asset_id,
                    changes=f"从 USER.md 迁移: {gene.summary}",
                    source_node_id="md_migration"
                )
                gep_store.append_event(event)

        # 转换 SOUL.md → Capsule
        if soul_md.exists():
            print(f"📄 处理 SOUL.md...")
            soul_capsule = self.convert_soul_md_to_capsule(soul_md)
            if soul_capsule:
                existing_capsules = gep_store.load_capsules()
                existing_capsules[soul_capsule.id] = soul_capsule
                gep_store.save_capsules(existing_capsules)
                print(f"✅ 导入 1 个 Capsule（来自 SOUL.md）")

                # 记录 Event
                event = Event(
                    timestamp=self._current_timestamp(),
                    event_type="capsule_created",
                    asset_id=soul_capsule.asset_id,
                    changes=f"从 SOUL.md 迁移: {soul_capsule.summary}",
                    source_node_id="md_migration"
                )
                gep_store.append_event(event)

        # 转换 AGENTS.md → Genes
        if agents_md.exists():
            print(f"📄 处理 AGENTS.md...")
            agent_genes = self.convert_agents_md_to_genes(agents_md)
            existing_genes = gep_store.load_genes()
            existing_genes.update(agent_genes)
            gep_store.save_genes(existing_genes)
            print(f"✅ 导入 {len(agent_genes)} 个 Gene（来自 AGENTS.md）")

            # 记录 Event
            for gene in agent_genes.values():
                event = Event(
                    timestamp=self._current_timestamp(),
                    event_type="gene_created",
                    asset_id=gene.asset_id,
                    changes=f"从 AGENTS.md 迁移: {gene.summary}",
                    source_node_id="md_migration"
                )
                gep_store.append_event(event)

        print("✨ 迁移完成！")

    def _extract_section(self, content: str, section_name: str) -> str:
        """
        从 Markdown 内容中提取指定章节

        Args:
            content: Markdown 内容
            section_name: 章节名称

        Returns:
            章节内容（去除标题）
        """
        # 匹配章节标题（## 或 ###）
        pattern = rf'##\s+{re.escape(section_name)}\s*\n+(.*?)(?=\n##\s+|\Z)'
        match = re.search(pattern, content, re.DOTALL)

        if match:
            return match.group(1).strip()

        return ""

    def _current_timestamp(self) -> str:
        """获取当前 ISO 8601 时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()
