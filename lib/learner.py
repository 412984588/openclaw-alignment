#!/usr/bin/env python3
"""
Learning modules for lightweight preference signals and optional RL adaptation.

Supports two learning modes：
1. PreferenceLearner: derive weak hints from local history signals
2. RLLearner: optional reinforcement-learning optimization
"""

import json
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path
from collections import defaultdict
from datetime import datetime, timezone

from .agent import AlignmentAgent, Trajectory
from .environment import InteractionEnvironment
from .policy_models import Rule
from .paths import resolve_config_path, resolve_model_dir


class PreferenceLearner:
    """Derive weak preference hints from observed local history."""

    def __init__(self, config_path: str | Path | None = None):
        self.config_path = str(resolve_config_path(config_path))
        self.learned_preferences: Dict[str, Any] = {}

    def learn_from_git_history(self, git_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert Git-derived signals into weak preference hints."""
        print("\n🧠 Deriving weak hints from local history...")

        # Learn technology stack preferences
        tech_preferences = self._learn_tech_stack(git_data["tech_stack"])

        # Learn lightweight workflow signals
        workflow_preferences = self._learn_workflow(git_data["workflow"])

        # Combine observations into a weak-hint profile
        self.learned_preferences = {
            "tech_stack": tech_preferences,
            "workflow": workflow_preferences,
            "metadata": {
                "last_updated": git_data.get("metadata", {}).get("collected_at", "unknown"),
                "confidence": git_data.get("metadata", {}).get("confidence", 0.5),
                "data_source": "git_history",
                "strength": "weak_hint",
            }
        }

        print(f"✅ Weak hints updated. Confidence: {self.learned_preferences['metadata']['confidence']*100}%")
        return self.learned_preferences

    def _learn_tech_stack(self, tech_stack: Dict[str, int]) -> Dict[str, Any]:
        """Learn technology stack preferences"""
        total = sum(tech_stack.values())

        if total == 0:
            return {"primary": "unknown", "stats": {}}

        # Find out which technologies are most commonly used
        sorted_tech = sorted(tech_stack.items(), key=lambda x: x[1], reverse=True)

        # Main technology stack（forward3name）
        primary = sorted_tech[0][0] if sorted_tech else "unknown"
        secondary = sorted_tech[1][0] if len(sorted_tech) > 1 else None
        tertiary = sorted_tech[2][0] if len(sorted_tech) > 2 else None

        # Calculate proportion
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
        """Extract coarse workflow signals from observed activity."""
        preferences = {
            "test_driven": workflow.get("test_first", False),
            "test_ratio": workflow.get("test_ratio", 0),
            "automation_level": "balanced",
            "signal_strength": "weak_hint",
        }

        # Infer only a coarse automation signal from test proportions
        if preferences["test_ratio"] > 0.5:
            preferences["automation_level"] = "quality_focused"
        elif preferences["test_ratio"] < 0.2:
            preferences["automation_level"] = "speed_focused"

        return preferences

    def save_preferences(self, output_path: str | Path | None = None) -> None:
        """Save derived hint data to the configuration file."""
        output_file = Path(output_path or self.config_path).expanduser()

        # Make sure the directory exists
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Read existing configuration
        if output_file.exists():
            with open(output_file, 'r') as f:
                config = json.load(f)
        else:
            config = {"version": "2.0.0"}

        # Update configuration
        config.update({
            "learned_preferences": self.learned_preferences,
            "last_updated": self.learned_preferences["metadata"]["last_updated"]
        })

        # Save configuration
        with open(output_file, 'w') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

        print(f"✅ Weak hints saved to: {output_file}")

    def generate_report(self) -> str:
        """Generate a report of weak hints derived from observed history."""
        if not self.learned_preferences:
            return "❌ No history hints have been derived yet"

        tech = self.learned_preferences.get("tech_stack", {})
        workflow = self.learned_preferences.get("workflow", {})
        metadata = self.learned_preferences.get("metadata", {})

        report = f"""
# Intent Alignment Hint Report

## 📊 Observed technology patterns

Observed primary stack: **{tech.get('primary', 'unknown')}** ({tech.get('stats', {}).get(tech.get('primary', ''), {}).get('percentage', 0)}%)
Secondary signal: {tech.get('secondary', 'none')}
Third signal: {tech.get('tertiary', 'none')}

Observed sample breakdown:
"""

        for tech_name, stats in tech.get("stats", {}).items():
            report += f"- {tech_name}: observed {stats['count']} times ({stats['percentage']}%)\n"

        report += f"""
## 🔄 Weak workflow hints

Observed test-first tendency: {'✅ yes' if workflow.get('test_driven') else '❌ no'}
Weak hint profile: {workflow.get('automation_level', 'balanced')}
Observed test proportion: {workflow.get('test_ratio', 0)*100:.0f}%

## 📈 metadata

Confidence: {metadata.get('confidence', 0)*100:.0f}%
Data source: {metadata.get('data_source', 'unknown')}
Hint strength: {metadata.get('strength', 'weak_hint')}
Update time: {metadata.get('last_updated', 'unknown')}

---

💡 **Interpretation**:
- Treat these observations as weak hints, not durable workflow policy
- Observed primary stack: {tech.get('primary', 'unknown')}
- {'Observed test-first behavior in history' if workflow.get('test_driven') else 'History does not strongly indicate test-first behavior'}
- Current hint suggests {'quality-focused verification habits' if workflow.get('automation_level') == 'quality_focused' else 'balanced or speed-oriented execution habits'}
"""

        return report

    def build_hint_rules(self, scope_key: str) -> List[Rule]:
        """Convert learned Git-derived preferences into weak hint rules only."""
        if not self.learned_preferences:
            return []

        workflow = self.learned_preferences.get("workflow", {})
        metadata = self.learned_preferences.get("metadata", {})
        timestamp = datetime.now(timezone.utc).isoformat()

        workflow_hint = Rule(
            id=f"hint_git_history_workflow_{abs(hash(scope_key)) % 10_000}",
            summary="Git history weakly hints that verification tasks may be automation-friendly",
            category="optimize",
            trigger=["task_type:T1", "keyword:test", "keyword:lint", "keyword:build"],
            strategy="Treat verification-heavy tasks as weak automation hints only.",
            confidence=min(0.5, float(metadata.get("confidence", 0.3))),
            status="hint",
            scope="project" if scope_key else "global",
            scope_key=scope_key,
            evidence_count=1,
            source_type="git_history",
            last_seen_at=timestamp,
            policy_decision="auto_execute" if workflow.get("test_ratio", 0) >= 0.3 else "",
        )
        workflow_hint.calculate_asset_id()
        return [workflow_hint]

    def collect_runtime_policy_signals(self, policy_store: Any) -> Dict[str, Any]:
        """Summarize strong runtime signals from decision history without mutating policy state."""
        outcome_events = [
            event
            for event in policy_store.get_decision_events(limit=2_000)
            if event.event_type == "decision_outcome"
        ]

        strong_signals = {
            "explicit_user_corrections": 0,
            "accepted_auto_executes": 0,
            "rollback_failures": 0,
            "repeated_failures": 0,
            "override_against_rule": 0,
        }

        for event in outcome_events:
            override = event.payload.get("user_override", "")
            result = event.payload.get("execution_result", "")
            final_decision = event.payload.get("final_decision", "")

            if override in {"confirmed_after_prompt", "prefer_auto_execute", "prefer_confirmation"}:
                strong_signals["explicit_user_corrections"] += 1
            if result == "success" and final_decision == "auto_execute":
                strong_signals["accepted_auto_executes"] += 1
            if result == "rollback":
                strong_signals["rollback_failures"] += 1
            if result == "failure":
                strong_signals["repeated_failures"] += 1
            if override in {"blocked_auto_execute", "prefer_confirmation"}:
                strong_signals["override_against_rule"] += 1

        return {
            "strong_signals": strong_signals,
            "sample_size": len(outcome_events),
            "source": "policy_events",
        }


class RLLearner:
    """
    reinforcement learning learner - online learning

    Learn in real time from task execution，useActor-CriticAlgorithm optimization strategy
    """

    def __init__(self, model_path: str | Path | None = None, config_path: str | Path | None = None):
        """
        initializationRLlearner

        Args:
            model_path: Model save path
            config_path: Configuration file path
        """
        self.model_path = str(resolve_model_dir(model_path))
        self.config_path = str(resolve_config_path(config_path))

        # Initialize environment and agent
        self.env = InteractionEnvironment(config_path=self.config_path)

        self.agent = AlignmentAgent(
            state_dim=self.env.get_state_space_size(),
            action_dim=self.env.get_action_space_size()
        )

        # Try loading an existing model
        self._load_model()

        # current trajectory
        self.current_trajectory: Optional[Trajectory] = None

        # Historical preference statistics (task_type + selection dimensions)
        self._agent_reward_history: Dict[Tuple[str, str], List[float]] = defaultdict(list)
        self._workflow_reward_history: Dict[Tuple[str, str], List[float]] = defaultdict(list)

        # contract：Reward system prioritizes reading learner history
        self.env.reward_calculator.set_history_provider(self)

        # Initialize local policy store if available
        from .policy_store import PolicyStore
        memory_dir = Path(self.config_path).parent
        self.policy_store = PolicyStore.bootstrap(memory_dir, ensure_files=True)

    def _load_model(self) -> None:
        """Load existing model"""
        model_dir = Path(self.model_path).expanduser()
        if model_dir.exists():
            try:
                self.agent.load_model(str(model_dir))
                print(f"✅ Model loaded: {model_dir}")
            except Exception as e:
                print(f"⚠️  Failed to load model: {e}，Use new model")

    def learn_from_task(self, task_context: Dict[str, Any],
                       task_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Learn from a single task（online learning）

        Args:
            task_context: task context
            task_result: Task execution results

        Returns:
            Learn statistics
        """
        # 1. Reset environment
        state = self.env.reset(task_context)

        # 2. Select action（Use current strategy）
        action = self.agent.select_action(state, explore=False)

        # 3. perform action，Get feedback
        next_state, reward, done, info = self.env.step(action, task_result)

        # 4. Build a single step trajectory
        trajectory = Trajectory(
            states=[state.to_vector()],
            actions=[self.agent.encode_action_indices(action)],
            rewards=[reward],
            dones=[done],
            next_states=[next_state.to_vector()]
        )

        # 4.1 Record preference history（Used for subsequent reward calculations）
        self.record_preference_result(
            task_type=task_context.get("task_type", "T2"),
            agent=action.agent_selection.value,
            workflow=task_result.get("workflow", "standard"),
            reward=reward,
        )

        # 5. update strategy
        stats = self.agent.update_policy(trajectory)

        # 6. Save models regularly
        if self.agent.episode_count % 10 == 0:
            self.save_model()

        # 7. Auto-create or update policy rules (if available)
        if self.policy_store:
            self._update_policy_rules(task_context, task_result, reward, action)

        return {
            "reward": reward,
            "action_taken": str(action),
            "agent_used": action.agent_selection.value,
            **stats
        }

    def get_recommended_action(self, task_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get recommended actions（Do not update policy）

        Integrate intelligent confirmation decisions based on policy confidence and risk.

        Args:
            task_context: task context

        Returns:
            Recommended actions
        """
        # Reset environment
        state = self.env.reset(task_context)

        # Select action（Not exploring）
        action = self.agent.select_action(state, explore=False)

        # Intelligent confirmation decision
        from .confirmation import IntelligentConfirmation
        confirmation_engine = IntelligentConfirmation(self.policy_store)

        should_confirm, reason = confirmation_engine.should_confirm(task_context)

        return {
            "agent": action.agent_selection.value,
            "automation_level": action.automation_level.value,
            "communication_style": action.communication_style.value,
            "confirmation_needed": should_confirm,  # Derived by intelligent decision policy
            "confirmation_reason": reason,  # Human-readable decision reason
            "confidence": 0.7 + self.env.recent_performance * 0.3  # Performance-based confidence
        }

    def save_model(self) -> None:
        """Save model"""
        self.agent.save_model(self.model_path)
        self.env.save_history(f"{self.model_path}/env_history.json")
        print(f"✅ Model saved: {self.model_path}")

    def get_training_stats(self) -> Dict[str, Any]:
        """Get training statistics"""
        return {
            "episode_count": self.agent.episode_count,
            "total_steps": self.agent.total_steps,
            "recent_performance": self.env.recent_performance,
            "agent_usage": self.env.agent_usage_history
        }

    def record_preference_result(self, task_type: str, agent: str, workflow: str, reward: float) -> None:
        """Record task results to preference history"""
        reward_clipped = max(0.0, min(1.0, float(reward)))
        self._agent_reward_history[(task_type, agent)].append(reward_clipped)
        self._workflow_reward_history[(task_type, workflow)].append(reward_clipped)

    def get_agent_success_rate(self, task_type: str, agent: str) -> Optional[float]:
        """supplyAgentHistorical success rate（Reward mean）"""
        rewards = self._agent_reward_history.get((task_type, agent))
        if not rewards:
            return None
        return float(sum(rewards) / len(rewards))

    def get_workflow_success_rate(self, task_type: str, workflow: str) -> Optional[float]:
        """Provide workflow historical success rate（Reward mean）"""
        rewards = self._workflow_reward_history.get((task_type, workflow))
        if not rewards:
            return None
        return float(sum(rewards) / len(rewards))

    def _update_policy_rules(
        self,
        task_context: Dict[str, Any],
        task_result: Dict[str, Any],
        reward: float,
        action,
    ) -> None:
        """
        Auto-create or update policy rules (internal helper).

        Called after each task to update relevant rules using task outcome.

        Args:
            task_context: Task context
            task_result: Task result
            reward: RL reward
            action: Chosen action
        """
        if not self.policy_store:
            return

        from .policy_models import PolicyEvent, Rule
        from datetime import datetime

        # 1. Create or update the agent selection preference rule
        agent_rule_id = f"rule_agent_selection_{action.agent_selection.value}"
        rules = self.policy_store.load_rules()
        rule_exists = agent_rule_id in rules

        if rule_exists:
            # Update existing rule
            rule = rules[agent_rule_id]
            rule.increment_confidence(reward)
            rule.status = "hint"
            rule.source_type = "rl_feedback"
            rule.policy_decision = ""
            rule.last_seen_at = datetime.now(timezone.utc).isoformat()
        else:
            # Create a new rule
            rule = Rule(
                id=agent_rule_id,
                summary=f"Agent selection preference: {action.agent_selection.value}",
                category="optimize",
                strategy=f"Use {action.agent_selection.value} to process matching tasks",
                trigger=["task_start", "agent_selection"],
                confidence=min(1.0, max(0.0, reward)),
                success_streak=1 if reward > 0.7 else 0,
                status="hint",
                scope="project",
                scope_key=str(Path(self.config_path).expanduser().parent),
                evidence_count=1,
                source_type="rl_feedback",
                last_seen_at=datetime.now(timezone.utc).isoformat(),
                policy_decision="",
            )
            rule.calculate_asset_id()

        rules[agent_rule_id] = rule
        self.policy_store.save_rules(rules)

        # 2. Record event
        event = PolicyEvent(
            timestamp=datetime.now().isoformat(),
            event_type="rule_updated" if rule_exists else "rule_created",
            asset_id=rule.asset_id,
            trigger_signals=[task_context.get("task_type", "unknown")],
            rl_reward=float(reward),
            changes=f"Task completed, reward={reward:.2f}",
            source_node_id="rl_learner"
        )
        self.policy_store.append_event(event)


def main():
    """Test learning algorithms"""
    # simulationGitdata
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

    # learning preferences
    learner = PreferenceLearner()
    learner.learn_from_git_history(git_data)

    # Generate report
    report = learner.generate_report()
    print(report)

    # Save to configuration
    # learner.save_preferences()


if __name__ == "__main__":
    main()
