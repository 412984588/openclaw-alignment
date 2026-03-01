#!/usr/bin/env python3
"""
OpenClaw integration module.

Connects data collection, learning, and config updates.
"""

import json
from pathlib import Path
from typing import Dict, Any

from .collector import GitPreferenceCollector
from .learner import PreferenceLearner, RLLearner
from .paths import resolve_config_path, resolve_model_dir


class IntentAlignmentEngine:
    """Intent alignment engine for collection, learning, and optimization."""

    def __init__(self, repo_path: str = ".", config_path: str | Path | None = None):
        self.repo_path = Path(repo_path).resolve()
        self.config_path = resolve_config_path(config_path)

        # Initialize components
        self.collector = GitPreferenceCollector(str(self.repo_path))
        self.learner = PreferenceLearner(str(self.config_path))

    def run_analysis(self, max_commits: int = 100) -> Dict[str, Any]:
        """Run the full analysis pipeline."""
        print("🚀 Starting intent alignment analysis...")
        print(f"📂 Repository path: {self.repo_path}")
        print("")

        # Step 1: Collect data
        git_data = self.collector.collect(max_commits)

        if not git_data.get("tech_stack"):
            print("❌ No data was collected")
            return {}

        # Step 2: Learn preferences
        preferences = self.learner.learn_from_git_history(git_data)

        # Step 3: Save config
        self.learner.save_preferences()

        # Step 4: Generate report
        self.learner.generate_report()

        # Step 5: Print summary
        print("\n" + "="*50)
        print("✅ Analysis complete!")
        print("="*50)
        print("Highlights:")
        print(f"  - Primary technology: {preferences['tech_stack']['primary']}")
        print(f"  - Automation preference: {preferences['workflow']['automation_level']}")
        print(f"  - Confidence: {preferences['metadata']['confidence']*100:.0f}%")
        print("")
        print(f"Detailed report saved to: {self.config_path}")
        print("")

        return preferences

    def get_current_preferences(self) -> Dict[str, Any]:
        """Return currently learned preferences."""
        if not self.config_path.exists():
            return {}

        with open(self.config_path, 'r') as f:
            config = json.load(f)

        return config.get("learned_preferences", {})

    def update_preferences(self, new_data: Dict[str, Any]) -> None:
        """Incrementally update preferences."""
        current = self.get_current_preferences()
        current.update(new_data)

        # Keep config structure stable to avoid overriding top-level fields
        config: Dict[str, Any]
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                config = json.load(f)
        else:
            config = {"version": "1.0.1"}

        config["learned_preferences"] = current

        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

        print("✅ Preferences updated")

    def reset_preferences(self) -> None:
        """Reset all learned data."""
        if self.config_path.exists():
            backup = self.config_path.with_suffix('.backup.json')
            self.config_path.rename(backup)
            print(f"✅ Preferences reset, backup saved at: {backup}")


class RLAlignmentEngine(IntentAlignmentEngine):
    """
    RL alignment engine extending IntentAlignmentEngine.

    Adds online RL hooks:
    - on_task_start(): get recommended strategy
    - on_task_complete(): update model with task outcome
    """

    def __init__(
        self,
        repo_path: str = ".",
        config_path: str | Path | None = None,
        use_rl: bool = True,
    ):
        """
        Initialize RL alignment engine.

        Args:
            repo_path: Git repository path
            config_path: Config file path
            use_rl: Whether to enable reinforcement learning
        """
        # Initialize base class
        super().__init__(repo_path, config_path)

        # Initialize RL learner
        self.use_rl = use_rl
        if use_rl:
            self.rl_learner = RLLearner(
                model_path=str(resolve_model_dir()),
                config_path=str(self.config_path)
            )

    def on_task_start(self, task_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Called when a task starts to get a recommended strategy.

        Args:
            task_context: Task context, including:
                - task_type
                - tech_stack
                - description

        Returns:
            Recommended strategy
        """
        if not self.use_rl:
            return {}

        # Get recommended action
        recommendation = self.rl_learner.get_recommended_action(task_context)

        print(
            f"🤖 RL recommendation: {recommendation['agent']} | "
            f"automation: {recommendation['automation_level']} | "
            f"style: {recommendation['communication_style']}"
        )

        return recommendation

    def on_task_complete(self, task_context: Dict[str, Any],
                         task_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Called when a task finishes to update the model.

        Args:
            task_context: Task context
            task_result: Task execution result

        Returns:
            Learning stats
        """
        if not self.use_rl:
            return {}

        print("📊 Learning from task outcome...")

        # Learn from task outcome
        stats = self.rl_learner.learn_from_task(task_context, task_result)

        print(f"✅ Learning done: reward={stats['reward']:.3f}")

        return stats

    def get_training_progress(self) -> Dict[str, Any]:
        """Return training progress."""
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
    """Command-line interface."""
    import argparse

    parser = argparse.ArgumentParser(description="Intent alignment analysis tool")
    parser.add_argument("--repo", default=".", help="Git repository path")
    parser.add_argument("--commits", type=int, default=100, help="Number of commits to analyze")
    parser.add_argument("--reset", action="store_true", help="Reset learned preferences")
    parser.add_argument("--show", action="store_true", help="Show current preferences")

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
