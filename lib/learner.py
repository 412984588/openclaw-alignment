#!/usr/bin/env python3
"""
学习模块 - 从收集的数据中学习用户偏好
"""

import json
from typing import Dict, List, Any, Tuple
from pathlib import Path


class PreferenceLearner:
    """偏好学习算法"""

    def __init__(self, config_path: str = None):
        self.config_path = config_path or "~/.openclaw/extensions/intent-alignment/config/config.json"
        self.learned_preferences = {}

    def learn_from_git_history(self, git_data: Dict[str, Any]) -> Dict[str, Any]:
        """从Git历史学习偏好"""
        print("\n🧠 正在学习偏好...")

        # 学习技术栈偏好
        tech_preferences = self._learn_tech_stack(git_data["tech_stack"])

        # 学习工作流偏好
        workflow_preferences = self._learn_workflow(git_data["workflow"])

        # 组合学习结果
        self.learned_preferences = {
            "tech_stack": tech_preferences,
            "workflow": workflow_preferences,
            "metadata": {
                "last_updated": git_data.get("metadata", {}).get("collected_at", "unknown"),
                "confidence": git_data.get("metadata", {}).get("confidence", 0.5),
                "data_source": "git_history"
            }
        }

        print(f"✅ 学习完成！置信度: {self.learned_preferences['metadata']['confidence']*100}%")
        return self.learned_preferences

    def _learn_tech_stack(self, tech_stack: Dict[str, int]) -> Dict[str, Any]:
        """学习技术栈偏好"""
        total = sum(tech_stack.values())

        if total == 0:
            return {"primary": "unknown", "stats": {}}

        # 找出最常用的技术
        sorted_tech = sorted(tech_stack.items(), key=lambda x: x[1], reverse=True)

        # 主要技术栈（前3名）
        primary = sorted_tech[0][0] if sorted_tech else "unknown"
        secondary = sorted_tech[1][0] if len(sorted_tech) > 1 else None
        tertiary = sorted_tech[2][0] if len(sorted_tech) > 2 else None

        # 计算占比
        stats = {
            tech: {
                "count": count,
                "percentage": round(count / total * 100, 1)
            }
            for tech, count in sorted_tech[:5] if count > 0
        }

        return {
            "primary": primary,
            "secondary": secondary,
            "tertiary": tertiary,
            "stats": stats,
            "total_samples": total
        }

    def _learn_workflow(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """学习工作流偏好"""
        preferences = {
            "test_driven": workflow.get("test_first", False),
            "test_ratio": workflow.get("test_ratio", 0),
            "automation_level": "balanced"
        }

        # 根据测试比例推断自动化偏好
        if preferences["test_ratio"] > 0.5:
            preferences["automation_level"] = "quality_focused"
        elif preferences["test_ratio"] < 0.2:
            preferences["automation_level"] = "speed_focused"

        return preferences

    def save_preferences(self, output_path: str = None) -> None:
        """保存学习结果到配置文件"""
        output_path = output_path or self.config_path
        output_path = Path(output_path).expanduser()

        # 确保目录存在
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 读取现有配置
        if output_path.exists():
            with open(output_path, 'r') as f:
                config = json.load(f)
        else:
            config = {"version": "1.0.0"}

        # 更新配置
        config.update({
            "learned_preferences": self.learned_preferences,
            "last_updated": self.learned_preferences["metadata"]["last_updated"]
        })

        # 保存配置
        with open(output_path, 'w') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

        print(f"✅ 偏好已保存到: {output_path}")

    def generate_report(self) -> str:
        """生成学习报告"""
        if not self.learned_preferences:
            return "❌ 还没有学习任何偏好"

        tech = self.learned_preferences.get("tech_stack", {})
        workflow = self.learned_preferences.get("workflow", {})
        metadata = self.learned_preferences.get("metadata", {})

        report = f"""
# 意图对齐学习报告

## 📊 技术栈偏好

主要技术: **{tech.get('primary', 'unknown')}** (占比{tech.get('stats', {}).get(tech.get('primary', ''), {}).get('percentage', 0)}%)
次要技术: {tech.get('secondary', '无')}
第三选择: {tech.get('tertiary', '无')}

详细统计:
"""

        for tech_name, stats in tech.get("stats", {}).items():
            report += f"- {tech_name}: {stats['count']}次 ({stats['percentage']}%)\n"

        report += f"""
## 🔄 工作流偏好

测试驱动: {'✅ 是' if workflow.get('test_driven') else '❌ 否'}
自动化偏好: {workflow.get('automation_level', 'balanced')}
测试占比: {workflow.get('test_ratio', 0)*100:.0f}%

## 📈 元数据

置信度: {metadata.get('confidence', 0)*100:.0f}%
数据来源: {metadata.get('data_source', 'unknown')}
更新时间: {metadata.get('last_updated', 'unknown')}

---

💡 **建议**:
- 主要使用 {tech.get('primary', 'unknown')} 进行开发
- {'采用测试驱动开发' if workflow.get('test_driven') else '考虑增加测试覆盖率'}
- 保持当前{'的质量优先' if workflow.get('automation_level') == 'quality_focused' else '速度优先'}风格
"""

        return report


def main():
    """测试学习算法"""
    # 模拟Git数据
    git_data = {
        "tech_stack": {
            "python": 45,
            "javascript": 12,
            "react": 38,
            "vue": 3,
            "fastapi": 25
        },
        "file_types": {
            ".py": 45,
            ".js": 8,
            ".jsx": 12,
            ".ts": 4
        },
        "workflow": {
            "test_first": True,
            "test_ratio": 0.35
        },
        "metadata": {
            "collected_at": "2026-02-28T18:30:00Z",
            "confidence": 0.85
        }
    }

    # 学习偏好
    learner = PreferenceLearner()
    preferences = learner.learn_from_git_history(git_data)

    # 生成报告
    report = learner.generate_report()
    print(report)

    # 保存到配置
    # learner.save_preferences()


if __name__ == "__main__":
    main()
