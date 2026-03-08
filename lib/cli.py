#!/usr/bin/env python3
"""OpenClaw Alignment command-line interface."""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .api import ConfirmationAPI
from .confirmation import IntelligentConfirmation
from .md_to_policy import MarkdownToPolicyConverter
from .policy_store import PolicyStore
from .policy_to_md import PolicyToMarkdownExporter


class OpenClawAlignmentCLI:
    """Main OpenClaw Alignment CLI class."""

    def __init__(self) -> None:
        self.memory_dir_name = ".openclaw_memory"
        self.config_file_name = "config.json"
        self.templates = {
            "USER.md": "USER_template.md",
            "SOUL.md": "SOUL_template.md",
            "AGENTS.md": "AGENTS_template.md",
        }

    def get_template_dir(self) -> Path:
        package_dir = Path(__file__).parent
        return package_dir.parent / "templates"

    def get_memory_dir(self, cwd: Optional[Path] = None) -> Path:
        return (cwd or Path.cwd()) / self.memory_dir_name

    def get_policy_dir(self, cwd: Optional[Path] = None) -> Path:
        return self.get_memory_dir(cwd) / "policy"

    def _open_policy_store(
        self,
        cwd: Optional[Path] = None,
        *,
        ensure_files: bool = False,
    ) -> PolicyStore:
        return PolicyStore.bootstrap(self.get_memory_dir(cwd), ensure_files=ensure_files)

    def init(self, target_dir: Optional[str] = None, force: bool = False) -> bool:
        cwd = Path(target_dir).resolve() if target_dir else Path.cwd()
        memory_dir = self.get_memory_dir(cwd)
        template_dir = self.get_template_dir()

        if not template_dir.exists():
            print(f"Error: template directory not found: {template_dir}")
            return False

        memory_dir.mkdir(parents=True, exist_ok=True)
        store = self._open_policy_store(cwd)
        policy_dir = store.base_dir

        if not force and self._has_markdown_seed(memory_dir) and not store.load_rules() and not store.load_playbooks():
            MarkdownToPolicyConverter().migrate_all(memory_dir, store)

        if force or not store.rules_file.exists():
            store.save_rules({})
            print(f"Created: {store.rules_file}")
        if force or not store.playbooks_file.exists():
            store.save_playbooks({})
            print(f"Created: {store.playbooks_file}")
        if force or not store.policy_events_file.exists():
            store.policy_events_file.touch()
            print(f"Created: {store.policy_events_file}")

        for target_name, template_name in self.templates.items():
            template_file = template_dir / template_name
            target_file = memory_dir / target_name
            if not template_file.exists():
                continue
            if target_file.exists() and not force:
                continue
            shutil.copy2(template_file, target_file)
            print(f"Created: {target_file}")

        config_file = memory_dir / self.config_file_name
        if force or not config_file.exists():
            config = {
                "version": "2.0.0",
                "initialized_at": datetime.now(timezone.utc).isoformat(),
                "initialized_in": str(cwd),
                "memory_path": str(memory_dir),
                "features": {
                    "auto_learning": True,
                    "safety_checks": True,
                    "policy_engine": "autonomous_execution",
                },
            }
            config_file.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")
            print(f"Created: {config_file}")

        gitignore_file = memory_dir / ".gitignore"
        if force or not gitignore_file.exists():
            gitignore_file.write_text(
                "# OpenClaw Alignment local files\n"
                "# Do not commit these files\n"
                "config.json\n"
                "*.backup\n"
                "*.cache\n",
                encoding="utf-8",
            )
            print(f"Created: {gitignore_file}")

        print("")
        print("Initialization complete.")
        print(f"Policy memory: {memory_dir}")
        print(f"Policy assets: {policy_dir}")
        return True

    def _has_markdown_seed(self, memory_dir: Path) -> bool:
        return any((memory_dir / name).exists() for name in self.templates)

    def status(self) -> None:
        memory_dir = self.get_memory_dir()
        store = self._open_policy_store()
        policy_dir = store.base_dir
        config_file = memory_dir / self.config_file_name

        print("OpenClaw Alignment status")
        print("")
        print(f"Policy memory: {memory_dir}")
        print(f"Status: {'present' if memory_dir.exists() else 'missing'}")
        print("")

        if config_file.exists():
            config = json.loads(config_file.read_text(encoding="utf-8"))
            print(f"Config version: {config.get('version', 'unknown')}")
        else:
            print("Config version: missing")

        stats = store.get_stats()
        print(f"Rules: {stats['total_rules']}")
        print(f"Playbooks: {stats['total_playbooks']}")
        print(f"Policy events: {stats['total_policy_events']}")
        print(f"Policy directory: {policy_dir}")

    def version(self) -> None:
        from . import __version__

        print(f"OpenClaw Alignment CLI v{__version__}")

    def rule_list(self) -> None:
        store = self._open_policy_store()
        rules = store.load_rules()
        if not rules:
            print("No rules found.")
            return
        print(f"Rules ({len(rules)} total):")
        for rule in rules.values():
            print(f"  {rule}")

    def rule_show(self, rule_id: str) -> None:
        store = self._open_policy_store()
        rule = store.get_rule(rule_id)
        if rule is None:
            print(f"Rule not found: {rule_id}")
            return

        print(f"Rule Details: {rule.id}")
        print(f"Summary: {rule.summary}")
        print(f"Status: {rule.status}")
        print(f"Scope: {rule.scope}")
        if rule.scope_key:
            print(f"Scope Key: {rule.scope_key}")
        print(f"Policy Decision: {rule.policy_decision or '(none)'}")
        print(f"Evidence Count: {rule.evidence_count}")
        print(f"Risk Level: {rule.risk_level or '(unset)'}")
        if rule.validation:
            print("Validation:")
            for test in rule.validation:
                print(f"  - {test}")

    def playbook_list(self) -> None:
        store = self._open_policy_store()
        playbooks = store.load_playbooks()
        if not playbooks:
            print("No playbooks found.")
            return
        print(f"Playbooks ({len(playbooks)} total):")
        for playbook in playbooks.values():
            print(f"  {playbook}")

    def playbook_show(self, playbook_id: str) -> None:
        store = self._open_policy_store()
        playbook = store.get_playbook(playbook_id)
        if playbook is None:
            print(f"Playbook not found: {playbook_id}")
            return
        print(f"Playbook Details: {playbook.id}")
        print(f"Summary: {playbook.summary}")
        print(f"Category: {playbook.category}")
        print(f"Confidence: {playbook.confidence:.2f}")
        print(f"Rules Used: {', '.join(playbook.rules_used) if playbook.rules_used else '(none)'}")

    def events_show(self, limit: int = 20) -> None:
        store = self._open_policy_store()
        events = store.get_events(limit)
        if not events:
            print("No policy events found.")
            return
        print(f"Recent policy events ({len(events)} shown):")
        for event in events:
            print(f"  {event}")

    def export_md(self) -> None:
        memory_dir = self.get_memory_dir()
        PolicyToMarkdownExporter().export_all(self._open_policy_store().base_dir, memory_dir)
        print("Markdown export completed.")

    def confidence_history(self, task_type: Optional[str] = None) -> None:
        rules = ConfirmationAPI(memory_dir=self.get_memory_dir()).get_confidence_history(task_type)["rules"]
        if not rules:
            print("No rules found.")
            return
        print(f"Confidence History ({len(rules)} rules)")
        print("")
        print(f"{'Confidence':<12} {'Streak':<8} {'Status':<12} {'Scope':<10} {'Rule Summary'}")
        print("-" * 88)
        for rule in rules:
            print(
                f"{rule['confidence']:<12.2f} {rule['success_streak']:<8} "
                f"{rule['status']:<12} {rule['scope']:<10} {rule['summary']}"
            )

    def decision_history(self, limit: int = 10) -> None:
        decisions = ConfirmationAPI(memory_dir=self.get_memory_dir()).get_recent_decisions(limit)["decisions"]
        if not decisions:
            print("No decision history found.")
            return
        print(f"Recent Decisions ({len(decisions)} shown)")
        print("")
        for decision in decisions:
            outcome = decision.get("execution_result") or "pending"
            print(
                f"- {decision['decision_id']} | {decision['final_decision']} | "
                f"risk={decision['risk_level']} | outcome={outcome}"
            )
            print(f"  summary: {decision['task_summary']}")
            print(f"  reason: {decision['reason']}")
            print(f"  resolution: {decision['resolution']}")

    def policy_status(self) -> None:
        snapshot = self._open_policy_store().get_policy_status_snapshot()
        print("Policy lifecycle status")
        print("")
        for status, count in snapshot["status_counts"].items():
            print(f"  {status}: {count}")
        print("")
        print(f"Recent promotions: {len(snapshot['recent_promotions'])}")
        print(f"Recent suspensions: {len(snapshot['recent_suspensions'])}")
        print(f"High-risk confirmed: {len(snapshot['risky_confirmed_rules'])}")
        print(f"Special scopes: {len(snapshot['special_scopes'])}")

    def policy_recent(self, limit: int = 10) -> None:
        events = self._open_policy_store().get_recent_lifecycle_events(limit=limit)
        if not events:
            print("No lifecycle events found.")
            return
        print(f"Recent policy lifecycle events ({len(events)} shown)")
        for event in events:
            payload = event.payload
            print(
                f"- {event.event_type} | {payload.get('rule_id', 'unknown')} | "
                f"{payload.get('trigger', 'n/a')}"
            )

    def policy_risky(self) -> None:
        rules = self._open_policy_store().get_risky_confirmed_rules()
        if not rules:
            print("No high-risk confirmed auto-execute rules.")
            return
        print("High-risk confirmed auto-execute rules")
        for rule in rules:
            print(f"- {rule.id} | {rule.risk_level} | {rule.scope}:{rule.scope_key or '*'}")
            print(f"  {rule.summary}")

    def policy_suspended(self, limit: int = 20) -> None:
        rules = self._open_policy_store().get_rules_by_status("suspended")[:limit]
        if not rules:
            print("No suspended rules.")
            return
        print(f"Suspended rules ({len(rules)} shown)")
        for rule in rules:
            print(
                f"- {rule.id} | {rule.scope}:{rule.scope_key or '*'} | "
                f"{rule.suspension_reason or 'unknown'}"
            )
            print(f"  {rule.summary}")

    def execute_demo(self, task_type: str = "T2", description: str = "run tests") -> None:
        store = self._open_policy_store()
        engine = IntelligentConfirmation(store)
        task_context = {
            "task_type": task_type,
            "task_description": description,
            "command": f"npm run {description}",
            "files": [],
        }
        should_confirm, reason = engine.should_confirm(task_context)
        print(engine.get_explanation(task_context, should_confirm, reason))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="OpenClaw Alignment - explainable autonomous execution policy engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--version", action="store_true", help="Show version information")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    init_parser = subparsers.add_parser("init", help="Initialize memory files")
    init_parser.add_argument("target_dir", nargs="?", help="Target directory")
    init_parser.add_argument("--force", action="store_true", help="Force overwrite existing files")

    subparsers.add_parser("status", help="Show current status")

    analyze_parser = subparsers.add_parser("analyze", help="Analyze Git history and learn preferences")
    analyze_parser.add_argument("--repo", default=".", help="Git repository path")
    analyze_parser.add_argument("--commits", type=int, default=100, help="Number of commits to analyze")

    rule_parser = subparsers.add_parser("rule", help="Rule management commands")
    rule_subparsers = rule_parser.add_subparsers(dest="rule_command", help="Rule actions")
    rule_subparsers.add_parser("list", help="List all rules")
    rule_show_parser = rule_subparsers.add_parser("show", help="Show rule details")
    rule_show_parser.add_argument("rule_id", help="Rule ID")

    playbook_parser = subparsers.add_parser("playbook", help="Playbook management commands")
    playbook_subparsers = playbook_parser.add_subparsers(dest="playbook_command", help="Playbook actions")
    playbook_subparsers.add_parser("list", help="List all playbooks")
    playbook_show_parser = playbook_subparsers.add_parser("show", help="Show playbook details")
    playbook_show_parser.add_argument("playbook_id", help="Playbook ID")

    events_parser = subparsers.add_parser("events", help="Show policy events")
    events_parser.add_argument("--limit", type=int, default=20, help="Number of events to show")

    subparsers.add_parser("export-md", help="Export policy memory to Markdown format")

    confidence_parser = subparsers.add_parser("confidence-history", help="Show confidence history")
    confidence_parser.add_argument("--task-type", help="Filter by task type")

    decision_parser = subparsers.add_parser("decision-history", help="Show recent confirmation decisions")
    decision_parser.add_argument("--limit", type=int, default=10, help="Number of recent decisions to show")

    policy_parser = subparsers.add_parser("policy", help="Read-only policy lifecycle operations")
    policy_subparsers = policy_parser.add_subparsers(dest="policy_command", help="Policy actions")
    policy_subparsers.add_parser("status", help="Show policy lifecycle status")
    policy_recent_parser = policy_subparsers.add_parser("recent", help="Show recent lifecycle events")
    policy_recent_parser.add_argument("--limit", type=int, default=10, help="Number of events to show")
    policy_subparsers.add_parser("risky", help="Show risky confirmed rules")
    policy_suspended_parser = policy_subparsers.add_parser("suspended", help="Show suspended rules")
    policy_suspended_parser.add_argument("--limit", type=int, default=20, help="Number of rules to show")

    execute_parser = subparsers.add_parser("execute-demo", help="Demonstrate confirmation workflow")
    execute_parser.add_argument("--task-type", default="T2", help="Task type")
    execute_parser.add_argument("--description", default="run tests", help="Task description")

    args = parser.parse_args()
    cli = OpenClawAlignmentCLI()

    if args.version:
        cli.version()
        return
    if args.command == "init":
        raise SystemExit(0 if cli.init(args.target_dir, args.force) else 1)
    if args.command == "status":
        cli.status()
        return
    if args.command == "analyze":
        from .integration import IntentAlignmentEngine

        IntentAlignmentEngine(args.repo).run_analysis(args.commits)
        return
    if args.command == "rule":
        if args.rule_command == "list":
            cli.rule_list()
        elif args.rule_command == "show":
            cli.rule_show(args.rule_id)
        else:
            rule_parser.print_help()
        return
    if args.command == "playbook":
        if args.playbook_command == "list":
            cli.playbook_list()
        elif args.playbook_command == "show":
            cli.playbook_show(args.playbook_id)
        else:
            playbook_parser.print_help()
        return
    if args.command == "events":
        cli.events_show(args.limit)
        return
    if args.command == "export-md":
        cli.export_md()
        return
    if args.command == "confidence-history":
        cli.confidence_history(args.task_type)
        return
    if args.command == "decision-history":
        cli.decision_history(args.limit)
        return
    if args.command == "policy":
        if args.policy_command == "status":
            cli.policy_status()
        elif args.policy_command == "recent":
            cli.policy_recent(args.limit)
        elif args.policy_command == "risky":
            cli.policy_risky()
        elif args.policy_command == "suspended":
            cli.policy_suspended(args.limit)
        else:
            policy_parser.print_help()
        return
    if args.command == "execute-demo":
        cli.execute_demo(args.task_type, args.description)
        return

    parser.print_help()


if __name__ == "__main__":
    main()
