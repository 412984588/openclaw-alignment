#!/usr/bin/env python3
"""
智能确认决策引擎

基于 GEP confidence 和任务风险评估，动态决定是否需要用户确认。
核心目标：减少不必要的确认，同时保持安全。
"""

import re
from typing import Dict, List, Optional, Tuple
from enum import Enum

from .gep import Gene
from .gep_store import GEPStore


class RiskLevel(Enum):
    """风险等级"""
    LOW = "low"          # 低风险：本地文件修改、代码格式化
    MEDIUM = "medium"    # 中风险：数据库修改、网络请求
    HIGH = "high"        # 高风险：删除文件、系统配置修改
    CRITICAL = "critical" # 危险：rm -rf、破坏性操作


class IntelligentConfirmation:
    """
    智能确认决策引擎

    基于 GEP confidence 和任务风险评估，动态决定是否需要用户确认。

    核心逻辑：
    - 高 confidence + 低风险 = 自动执行
    - 高 confidence + 高风险 = 仍需确认（安全优先）
    - 低 confidence + 任何风险 = 需要确认
    """

    def __init__(self, gep_store: Optional[GEPStore] = None):
        """
        初始化智能确认引擎

        Args:
            gep_store: GEP Store 实例（可选）
        """
        self.gep_store = gep_store

        # 高风险关键词（必须确认）
        self.high_risk_keywords = [
            "rm", "remove", "delete", "unlink", "rmdir",
            "format", "fdisk", "mkfs",
            "chmod", "chown", "iptables",
            "docker", "podman", "kubectl",
            "git push --force", "git reset --hard"
        ]

        # 中风险关键词（可选确认）
        self.medium_risk_keywords = [
            "database", "migrate", "schema",
            "api", "fetch", "request",
            "install", "uninstall", "update"
        ]

        # 低风险关键词（可自动执行）
        self.low_risk_keywords = [
            "test", "tests", "format", "lint", "check",
            "log", "status", "info", "list",
            "validate", "verify",
            # 扩展：文档和查看类操作
            "docs", "read", "view", "show", "display",
            "inspect", "describe", "explain",
            # 扩展：分析类操作
            "analyze", "measure", "benchmark", "profile",
            # 扩展：构建类操作（如果成功多次）
            "build", "compile", "bundle"
        ]

    def should_confirm(self, task_context: Dict[str, any]) -> Tuple[bool, str]:
        """
        决定是否需要用户确认

        Args:
            task_context: 任务上下文
                - task_type: 任务类型（T1/T2/T3/T4）
                - task_description: 任务描述
                - command: 执行的命令（如果有）
                - files: 涉及的文件列表（如果有）

        Returns:
            (需要确认, 原因说明)
        """
        # 1. 评估风险等级
        risk_level = self.assess_risk(task_context)

        # 2. 获取相关 Gene 的 confidence
        confidence_info = self.get_confidence_info(task_context)

        # 3. 决策逻辑
        should_confirm, reason = self._decide(risk_level, confidence_info, task_context)

        return should_confirm, reason

    def assess_risk(self, task_context: Dict[str, any]) -> RiskLevel:
        """
        评估任务风险等级

        Args:
            task_context: 任务上下文

        Returns:
            风险等级
        """
        task_desc = task_context.get("task_description", "").lower()
        command = task_context.get("command", "").lower()
        files = task_context.get("files", [])

        # 组合检查文本
        combined_text = f"{task_desc} {command}"

        # 1. 基于命令完整上下文评估（上下文感知）
        context_risk = self._assess_command_context(command, task_desc)
        if context_risk != RiskLevel.MEDIUM:
            return context_risk

        # 2. 检查高风险关键词（使用词边界匹配）
        for keyword in self.high_risk_keywords:
            # 特殊处理 "format" - 只有在特定上下文才算高风险
            if keyword == "format":
                # 检查是否有磁盘格式化的上下文
                if any(ctx in combined_text for ctx in ["mkfs", "fdisk", "format disk", "format /dev"]):
                    return RiskLevel.CRITICAL
                # 否则跳过，让低风险检查处理
                continue

            # 其他高风险关键词使用词边界匹配
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, combined_text):
                return RiskLevel.CRITICAL

        # 3. 检查中风险关键词
        for keyword in self.medium_risk_keywords:
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, combined_text):
                return RiskLevel.MEDIUM

        # 4. 检查低风险关键词
        for keyword in self.low_risk_keywords:
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, combined_text):
                return RiskLevel.LOW

        # 5. 基于文件路径历史评估
        file_risk = self.assess_file_operation_risk(files)
        if file_risk != RiskLevel.MEDIUM:
            return file_risk

        # 默认中等风险
        return RiskLevel.MEDIUM

    def _assess_command_context(self, command: str, task_desc: str) -> RiskLevel:
        """
        基于命令完整上下文评估风险

        示例：
        - "npm run test" → LOW
        - "npm run build" → LOW（如果成功5次以上）
        - "git status" → LOW
        - "git push" → MEDIUM（首次）→ LOW（成功10次）

        Args:
            command: 执行的命令
            task_desc: 任务描述

        Returns:
            风险等级（如果不是特殊命令，返回 MEDIUM 让后续逻辑处理）
        """
        # Git 操作的上下文评估
        if "git" in command:
            if any(cmd in command for cmd in ["git status", "git log", "git diff", "git show"]):
                return RiskLevel.LOW  # 只读操作
            elif "git push" in command and "--force" not in command:
                return RiskLevel.MEDIUM  # 正常推送，中等风险
            elif any(cmd in command for cmd in ["git commit", "git add"]):
                return RiskLevel.LOW  # 本地提交，低风险

        # npm/pnpm/yarn 操作的上下文评估
        if any(pkg in command for pkg in ["npm run", "pnpm run", "yarn"]):
            if any(cmd in command for cmd in ["test", "lint", "format", "check"]):
                return RiskLevel.LOW
            elif "build" in command:
                return RiskLevel.LOW  # 构建通常是安全的

        # Python 操作的上下文评估
        if "python" in command or "pytest" in command:
            if any(cmd in command for cmd in ["-m pytest", "test", "mypy", "black", "ruff"]):
                return RiskLevel.LOW

        # 如果没有匹配特殊模式，返回 MEDIUM 让后续逻辑继续处理
        return RiskLevel.MEDIUM

    def assess_file_operation_risk(self, files: List[str]) -> RiskLevel:
        """
        基于文件路径历史评估风险

        示例逻辑：
        - 修改 `.py`, `.js`, `.md` → 通常 LOW
        - 修改 `package.json`, `requirements.txt` → MEDIUM（依赖变更）
        - 修改 `.env`, `config.py` → HIGH（配置变更）
        - 删除任何文件 → CRITICAL（必须确认）

        Args:
            files: 文件路径列表

        Returns:
            风险等级
        """
        if not files:
            return RiskLevel.MEDIUM

        for file_path in files:
            file_path_lower = str(file_path).lower()

            # 检查系统目录
            if any(keyword in file_path_lower for keyword in ["home", "etc", "system", "root"]):
                return RiskLevel.HIGH

            # 检查敏感文件
            if any(keyword in file_path_lower for keyword in [".env", "config.py", "config.json", "secrets"]):
                return RiskLevel.HIGH

            # 检查依赖文件
            if any(keyword in file_path_lower for keyword in ["package.json", "requirements.txt", "pom.xml", "build.gradle"]):
                return RiskLevel.MEDIUM

            # 检查删除操作
            if any(keyword in file_path_lower for keyword in ["delete", "remove", "unlink"]):
                return RiskLevel.CRITICAL

            # 检查代码文件（通常是低风险）
            if any(file_path_lower.endswith(ext) for ext in [".py", ".js", ".ts", ".tsx", ".md", ".txt"]):
                return RiskLevel.LOW

        return RiskLevel.MEDIUM

    def get_confidence_info(self, task_context: Dict[str, any]) -> Dict[str, float]:
        """
        获取相关 Gene 的 confidence 信息

        Args:
            task_context: 任务上下文

        Returns:
            confidence 信息字典
        """
        if not self.gep_store:
            return {"max_confidence": 0.0, "avg_confidence": 0.0, "count": 0}

        # 加载所有 Gene
        genes = self.gep_store.load_genes()

        # 找到相关的 Gene（基于任务类型和触发信号）
        task_type = task_context.get("task_type", "T2")
        task_desc = task_context.get("task_description", "").lower()

        relevant_genes = []
        for gene in genes.values():
            # 检查任务类型匹配
            if task_type in gene.trigger:
                relevant_genes.append(gene)
            # 检查描述中的关键词匹配
            elif any(trigger in task_desc for trigger in gene.trigger):
                relevant_genes.append(gene)

        if not relevant_genes:
            return {"max_confidence": 0.0, "avg_confidence": 0.0, "count": 0}

        confidences = [g.confidence for g in relevant_genes]

        return {
            "max_confidence": max(confidences),
            "avg_confidence": sum(confidences) / len(confidences),
            "min_success_streak": min(g.success_streak for g in relevant_genes),
            "count": len(relevant_genes),
            "genes": relevant_genes
        }

    def _decide(self, risk_level: RiskLevel, confidence_info: Dict[str, float],
                 task_context: Dict[str, any]) -> Tuple[bool, str]:
        """
        决策逻辑：是否需要确认

        Args:
            risk_level: 风险等级
            confidence_info: confidence 信息
            task_context: 任务上下文

        Returns:
            (需要确认, 原因说明)
        """
        confidence = confidence_info["max_confidence"]
        success_streak = confidence_info.get("min_success_streak", 0)
        count = confidence_info["count"]

        # 规则 1: 无历史经验 → 必须确认
        if count == 0:
            return True, "🤔 首次执行此类任务，需要确认"

        # 规则 2: 危险操作 → 必须确认（无论 confidence 多高）
        if risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            return True, f"⚠️  {risk_level.value.upper()} 风险操作，必须确认"

        # 规则 3: 高信心 + 低风险 → 自动执行
        if confidence >= 0.9 and risk_level == RiskLevel.LOW:
            if success_streak >= 5:
                return False, f"✅ 高信心（{confidence:.2f}）+ {success_streak} 次连续成功，自动执行"
            else:
                return False, f"✅ 高信心（{confidence:.2f}），自动执行"

        # 规则 4: 中等信心 + 低风险 → 自动执行
        if confidence >= 0.8 and risk_level == RiskLevel.LOW:
            return False, f"✅ 中等信心（{confidence:.2f}）+ 低风险，自动执行"

        # 规则 5: 中等信心 + 中风险 + 连续成功 → 自动执行
        if confidence >= 0.8 and risk_level == RiskLevel.MEDIUM and success_streak >= 10:
            return False, f"✅ 中等信心（{confidence:.2f}）+ {success_streak} 次连续成功，自动执行"

        # 规则 6: 其他情况 → 需要确认
        return True, f"🤔 信心度不足（{confidence:.2f}），需要确认"

    def record_feedback(self, task_context: Dict[str, any],
                        was_confirmed: bool, user_cancelled: bool) -> None:
        """
        记录用户反馈，更新 Gene confidence

        Args:
            task_context: 任务上下文
            was_confirmed: 是否需要确认
            user_cancelled: 用户是否撤销了执行
        """
        if not self.gep_store:
            return

        from .gep import Event, Gene
        from datetime import datetime

        genes = self.gep_store.load_genes()

        # 找到相关 Gene
        task_type = task_context.get("task_type", "T2")
        task_desc = task_context.get("task_description", "")
        relevant_genes = [
            g for g in genes.values()
            if task_type in g.trigger
        ]

        # 如果没有相关 Gene，创建一个
        if not relevant_genes:
            gene_id = f"gene_{task_type}_confirmation"
            if gene_id not in genes:
                # 创建新 Gene
                new_gene = Gene(
                    id=gene_id,
                    summary=f"任务类型 {task_type} 的确认偏好",
                    category="confirmation",
                    strategy=f"对于 {task_type} 类型的任务，根据历史执行情况决定是否需要确认",
                    trigger=[task_type],
                    confidence=0.0,
                    success_streak=0
                )
                new_gene.calculate_asset_id()
                genes[gene_id] = new_gene
                relevant_genes = [new_gene]

        updated = False
        for gene in relevant_genes:
            original_confidence = gene.confidence

            if user_cancelled:
                # 用户撤销 → 降低 confidence
                gene.success_streak = 0
                gene.confidence = max(0.0, gene.confidence - 0.2)
                updated = True

                # 记录 Event
                event = Event(
                    timestamp=datetime.now().isoformat(),
                    event_type="gene_updated",
                    asset_id=gene.asset_id,
                    rl_reward=-0.2,  # 负奖励
                    changes=f"用户撤销执行，confidence: {original_confidence:.2f} → {gene.confidence:.2f}",
                    source_node_id="user_feedback"
                )
                self.gep_store.append_event(event)

            elif not was_confirmed:
                # 自动执行成功 → 提升 confidence
                gene.success_streak += 1
                gene.confidence = min(1.0, gene.confidence + 0.05)
                updated = True

                # 记录 Event
                event = Event(
                    timestamp=datetime.now().isoformat(),
                    event_type="gene_updated",
                    asset_id=gene.asset_id,
                    rl_reward=0.05,  # 正奖励
                    changes=f"自动执行成功，confidence: {original_confidence:.2f} → {gene.confidence:.2f}",
                    source_node_id="auto_execution"
                )
                self.gep_store.append_event(event)

            elif was_confirmed and not user_cancelled:
                # 用户确认并执行成功 → 小幅提升 confidence
                gene.success_streak += 1
                gene.confidence = min(1.0, gene.confidence + 0.03)  # 比自动执行提升得少
                updated = True

                # 记录 Event
                event = Event(
                    timestamp=datetime.now().isoformat(),
                    event_type="gene_updated",
                    asset_id=gene.asset_id,
                    rl_reward=0.03,  # 正奖励（较小）
                    changes=f"用户确认执行成功，confidence: {original_confidence:.2f} → {gene.confidence:.2f}",
                    source_node_id="user_confirmed"
                )
                self.gep_store.append_event(event)

        if updated:
            self.gep_store.save_genes(genes)

    def get_explanation(self, task_context: Dict[str, any],
                         should_confirm: bool, reason: str) -> str:
        """
        生成可执行的决策说明

        Args:
            task_context: 任务上下文
            should_confirm: 是否需要确认
            reason: 原因说明

        Returns:
            格式化的说明文本
        """
        if not should_confirm:
            # 自动执行：显示理由
            confidence_info = self.get_confidence_info(task_context)
            relevant_genes = confidence_info.get("genes", [])

            explanation = f"🤖 自动执行：{reason}\n"

            if relevant_genes:
                top_gene = max(relevant_genes, key=lambda g: g.confidence)
                explanation += f"   主要依据：{top_gene.summary}\n"
                explanation += f"   信心度：{top_gene.confidence:.2f} | 连续成功：{top_gene.success_streak} 次\n"

            return explanation
        else:
            # 需要确认：显示理由
            return f"🤔 需要确认：{reason}"
