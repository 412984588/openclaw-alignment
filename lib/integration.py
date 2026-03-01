#!/usr/bin/env python3
"""
OpenClaw集成模块 - 连接数据收集、学习和配置更新
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, Any

from .collector import GitPreferenceCollector
from .learner import PreferenceLearner, RLLearner


class IntentAlignmentEngine:
    """意图对齐引擎 - 协调数据收集、学习和优化"""

    def __init__(self, repo_path: str = ".", config_path: str = None):
        self.repo_path = Path(repo_path).resolve()
        self.config_path = config_path or "~/.openclaw/extensions/intent-alignment/config/config.json"
        self.config_path = Path(self.config_path).expanduser()

        # 初始化组件
        self.collector = GitPreferenceCollector(str(self.repo_path))
        self.learner = PreferenceLearner(str(self.config_path))

    def run_analysis(self, max_commits: int = 100) -> Dict[str, Any]:
        """运行完整的分析流程"""
        print("🚀 启动意图对齐分析...")
        print(f"📂 仓库路径: {self.repo_path}")
        print("")

        # 步骤1: 收集数据
        git_data = self.collector.collect(max_commits)

        if not git_data.get("tech_stack"):
            print("❌ 没有收集到任何数据")
            return {}

        # 步骤2: 学习偏好
        preferences = self.learner.learn_from_git_history(git_data)

        # 步骤3: 保存配置
        self.learner.save_preferences()

        # 步骤4: 生成报告
        report = self.learner.generate_report()

        # 步骤5: 显示总结
        print("\n" + "="*50)
        print("✅ 分析完成！")
        print("="*50)
        print(f"主要发现:")
        print(f"  - 最常用技术: {preferences['tech_stack']['primary']}")
        print(f"  - 自动化偏好: {preferences['workflow']['automation_level']}")
        print(f"  - 置信度: {preferences['metadata']['confidence']*100:.0f}%")
        print("")
        print(f"详细报告已保存到: {self.config_path}")
        print("")

        return preferences

    def get_current_preferences(self) -> Dict[str, Any]:
        """获取当前学习到的偏好"""
        if not self.config_path.exists():
            return {}

        with open(self.config_path, 'r') as f:
            config = json.load(f)

        return config.get("learned_preferences", {})

    def update_preferences(self, new_data: Dict[str, Any]) -> None:
        """增量更新偏好"""
        current = self.get_current_preferences()

        # 合并新数据
        current.update(new_data)

        # 保存
        with open(self.config_path, 'w') as f:
            json.dump(current, f, indent=2, ensure_ascii=False)

        print("✅ 偏好已更新")

    def reset_preferences(self) -> None:
        """重置所有学习数据"""
        if self.config_path.exists():
            backup = self.config_path.with_suffix('.backup.json')
            self.config_path.rename(backup)
            print(f"✅ 偏好已重置，备份保存在: {backup}")


class RLAlignmentEngine(IntentAlignmentEngine):
    """
    强化学习对齐引擎 - 扩展IntentAlignmentEngine

    新增RL在线学习接口：
    - on_task_start(): 任务开始时获取推荐策略
    - on_task_complete(): 任务完成时更新模型
    """

    def __init__(self, repo_path: str = ".", config_path: str = None, use_rl: bool = True):
        """
        初始化RL对齐引擎

        Args:
            repo_path: Git仓库路径
            config_path: 配置文件路径
            use_rl: 是否使用强化学习
        """
        # 初始化父类
        super().__init__(repo_path, config_path)

        # 初始化RL学习器
        self.use_rl = use_rl
        if use_rl:
            self.rl_learner = RLLearner(
                model_path=f"{self.config_path.parent}/models/rl",
                config_path=str(self.config_path)
            )

    def on_task_start(self, task_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        任务开始时调用 - 获取推荐策略

        Args:
            task_context: 任务上下文，包含：
                - task_type: 任务类型
                - tech_stack: 技术栈
                - description: 任务描述

        Returns:
            推荐的策略
        """
        if not self.use_rl:
            return {}

        # 获取推荐动作
        recommendation = self.rl_learner.get_recommended_action(task_context)

        print(f"🤖 RL推荐: {recommendation['agent']} | "
              f"自动化: {recommendation['automation_level']} | "
              f"风格: {recommendation['communication_style']}")

        return recommendation

    def on_task_complete(self, task_context: Dict[str, Any],
                         task_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        任务完成时调用 - 更新模型

        Args:
            task_context: 任务上下文
            task_result: 任务执行结果

        Returns:
            学习统计
        """
        if not self.use_rl:
            return {}

        print(f"📊 正在从任务中学习...")

        # 从任务中学习
        stats = self.rl_learner.learn_from_task(task_context, task_result)

        print(f"✅ 学习完成: 奖励={stats['reward']:.3f}")

        return stats

    def get_training_progress(self) -> Dict[str, Any]:
        """获取训练进度"""
        if not self.use_rl:
            return {"mode": "statistical"}

        stats = self.rl_learner.get_training_stats()

        return {
            "mode": "reinforcement_learning",
            "episodes": stats["episode_count"],
            "steps": stats["total_steps"],
            "performance": stats["recent_performance"],
            "agent_usage": stats["agent_usage"]
        }


def main():
    """命令行接口"""
    import argparse

    parser = argparse.ArgumentParser(description="意图对齐分析工具")
    parser.add_argument("--repo", ".", help="Git仓库路径")
    parser.add_argument("--commits", type=int, default=100, help="分析的提交数量")
    parser.add_argument("--reset", action="store_true", help="重置偏好")
    parser.add_argument("--show", action="store_true", help="显示当前偏好")

    args = parser.parse_args()

    engine = IntentAlignmentEngine(args.repo)

    if args.reset:
        engine.reset_preferences()
    elif args.show:
        prefs = engine.get_current_preferences()
        print(json.dumps(prefs, indent=2, ensure_ascii=False))
    else:
        engine.run_analysis(args.commits)


if __name__ == "__main__":
    main()
