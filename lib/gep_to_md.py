#!/usr/bin/env python3
"""
GEP → Markdown 导出器

将 GEP 格式（Gene/Capsule）导出为 Markdown 配置文件（USER.md/SOUL.md/AGENTS.md）。
用于向后兼容和手动编辑。
"""

from pathlib import Path
from typing import Dict, List, Optional

from .gep import Gene, Capsule
from .gep_store import GEPStore


class GEPToMarkdownExporter:
    """
    GEP → Markdown 导出器

    负责将 GEP 资产导出为 Markdown 配置文件。
    """

    def export_genes_to_user_md(self, genes: Dict[str, Gene], output_path: Path) -> None:
        """
        将 Gene 导出为 USER.md

        映射关系：
        - 基本信息 Gene → 基本信息
        - 工作习惯 Gene → 工作偏好
        - 沟通风格 Gene → 沟通风格

        Args:
            genes: Gene 字典
            output_path: 输出文件路径
        """
        # 提取相关 Gene
        basic_info_gene = self._find_gene_by_summary(genes, "基本信息")
        work_habits_gene = self._find_gene_by_summary(genes, "工作习惯")
        constraints_gene = self._find_gene_by_summary(genes, "项目特定约束")

        # 构建 Markdown 内容
        content = "# USER\n\n"

        # 基本信息
        content += "## Basic Information\n\n"
        if basic_info_gene:
            content += self._format_gene_strategy(basic_info_gene)
        else:
            content += "- Name: [Your Name]\n"
            content += "- Role: [Developer | Data Scientist | DevOps | Manager]\n"
            content += "- Primary Stack: [Python | JavaScript | Go | Rust | Other]\n"

        # 工作偏好
        content += "\n## Working Preferences\n\n"
        if work_habits_gene:
            content += self._format_gene_strategy(work_habits_gene)
        else:
            content += "- Communication style: [concise | detailed | interactive]\n"
            content += "- Automation preference: [low | medium | high]\n"
            content += "- Review depth: [light | standard | strict]\n"

        # 备注
        content += "\n## Notes\n\n"
        if constraints_gene:
            content += self._format_gene_strategy(constraints_gene)
        else:
            content += "- Add project-specific constraints and personal preferences here.\n"

        # 写入文件
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"✅ 导出 USER.md: {output_path}")

    def export_capsule_to_soul_md(self, capsule: Optional[Capsule], output_path: Path) -> None:
        """
        将 Capsule 导出为 SOUL.md

        映射关系：安全边界 Capsule → SOUL.md

        Args:
            capsule: Capsule 对象（可选）
            output_path: 输出文件路径
        """
        content = "# SOUL\n\n"

        # Capsule 没有 strategy 属性，始终使用默认模板
        # 如果需要自定义内容，应该从 Gene 中获取
        # TODO: 未来可以从 capsule.genes_used 关联的 Gene 中提取内容
        # 现在先使用默认模板
        content += "## Core Principles\n\n"
        content += "1. Safety First\n\n"
        content += "- Protect user data\n"
        content += "- Require explicit confirmation for high-risk actions\n"
        content += "- Respect task boundaries\n\n"

        content += "2. Transparency and Control\n\n"
        content += "- Explain recommendations\n"
        content += "- Keep user as final decision-maker\n"
        content += "- Keep auditable logs\n\n"

        content += "3. Continuous Learning\n\n"
        content += "- Improve incrementally from feedback\n"
        content += "- Avoid overfitting to short-term patterns\n\n"

        content += "4. Quality Assurance\n\n"
        content += "- Prefer test-first workflows\n"
        content += "- Keep documentation in sync with behavior\n"
        content += "- Monitor performance and regressions\n\n"

        content += "## Prohibited Actions\n\n"
        content += "- Destructive file operations without confirmation\n"
        content += "- Unauthorized external network or data export\n"
        content += "- Secret disclosure\n\n"

        content += "## Reward Signals\n\n"
        content += "- Positive: task completion, quality improvement, user acceptance\n"
        content += "- Negative: regressions, boundary violations, repeated failures\n"

        # 写入文件
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"✅ 导出 SOUL.md: {output_path}")

    def export_agent_genes_to_agents_md(self, genes: Dict[str, Gene], output_path: Path) -> None:
        """
        将 Agent 相关 Gene 导出为 AGENTS.md

        映射关系：Agent Gene → AGENTS.md

        Args:
            genes: Gene 字典
            output_path: 输出文件路径
        """
        # 提取相关 Gene
        tool_dispatch_gene = self._find_gene_by_summary(genes, "Agent 工具调度策略")
        operation_rules_gene = self._find_gene_by_summary(genes, "Agent 操作规则")
        escalation_gene = self._find_gene_by_summary(genes, "不确定时升级策略")

        # 构建 Markdown 内容
        content = "# AGENTS\n\n"

        # 工具调度
        content += "## Tool Dispatch\n\n"
        if tool_dispatch_gene:
            content += self._format_gene_strategy(tool_dispatch_gene)
        else:
            content += "- Codex: backend logic, APIs, data processing\n"
            content += "- Claude Code: UI and interaction-heavy tasks\n"
            content += "- Gemini: research and external references\n"

        # 操作规则
        content += "\n## Operation Rules\n\n"
        if operation_rules_gene:
            content += self._format_gene_strategy(operation_rules_gene)
        else:
            content += "- Behavior changes require tests\n"
            content += "- Keep changes atomic and reviewable\n"
            content += "- Run full validation before release\n"

        # 升级策略
        content += "\n## Escalation\n\n"
        if escalation_gene:
            content += self._format_gene_strategy(escalation_gene)
        else:
            content += "- If uncertainty is high, request explicit confirmation before proceeding\n"

        # 写入文件
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"✅ 导出 AGENTS.md: {output_path}")

    def export_all(self, gep_dir: Path, output_dir: Path) -> None:
        """
        导出所有 GEP 资产为 Markdown 格式

        用于 `openclaw-align export-md` 命令。

        Args:
            gep_dir: GEP 目录
            output_dir: 输出目录（通常是 .openclaw_memory/）
        """
        gep_store = GEPStore(gep_dir)

        # 加载所有资产
        genes = gep_store.load_genes()
        capsules = gep_store.load_capsules()

        # 查找安全边界 Capsule
        safety_capsule = self._find_capsule_by_summary(capsules, "安全边界")

        # 导出 USER.md
        user_md_path = output_dir / "USER.md"
        self.export_genes_to_user_md(genes, user_md_path)

        # 导出 SOUL.md
        soul_md_path = output_dir / "SOUL.md"
        self.export_capsule_to_soul_md(safety_capsule, soul_md_path)

        # 导出 AGENTS.md
        agents_md_path = output_dir / "AGENTS.md"
        self.export_agent_genes_to_agents_md(genes, agents_md_path)

        print("\n✨ 所有 Markdown 文件导出完成！")

    def _find_gene_by_summary(self, genes: Dict[str, Gene], keyword: str) -> Optional[Gene]:
        """
        根据摘要关键词查找 Gene

        Args:
            genes: Gene 字典
            keyword: 关键词

        Returns:
            匹配的 Gene，如果找不到则返回 None
        """
        for gene in genes.values():
            if keyword in gene.summary:
                return gene
        return None

    def _find_capsule_by_summary(self, capsules: Dict[str, Capsule], keyword: str) -> Optional[Capsule]:
        """
        根据摘要关键词查找 Capsule

        Args:
            capsules: Capsule 字典
            keyword: 关键词

        Returns:
            匹配的 Capsule，如果找不到则返回 None
        """
        for capsule in capsules.values():
            if keyword in capsule.summary:
                return capsule
        return None

    def _format_gene_strategy(self, gene: Gene) -> str:
        """
        格式化 Gene 策略为 Markdown 列表

        Args:
            gene: Gene 对象

        Returns:
            格式化的 Markdown 字符串
        """
        strategy = gene.strategy.strip()

        # 如果策略已经包含 Markdown 格式，直接返回
        if strategy.startswith('-') or '\n-' in strategy:
            return strategy

        # 否则，将每一行转换为列表项
        lines = strategy.split('\n')
        formatted_lines = []
        for line in lines:
            line = line.strip()
            if line and not line.startswith('-'):
                line = f"- {line}"
            formatted_lines.append(line)

        return '\n'.join(formatted_lines) + '\n'
