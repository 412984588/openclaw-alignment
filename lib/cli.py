#!/usr/bin/env python3
"""
OpenClaw Alignment command-line interface.

Provides one-command initialization and local memory configuration management.
"""

import argparse
import json
import shutil
from pathlib import Path
from typing import Optional


class OpenClawAlignmentCLI:
    """Main OpenClaw Alignment CLI class."""

    def __init__(self):
        self.memory_dir_name = ".openclaw_memory"
        self.config_file_name = "config.json"
        self.templates = {
            "USER.md": "USER_template.md",
            "SOUL.md": "SOUL_template.md",
            "AGENTS.md": "AGENTS_template.md",
        }

    def get_template_dir(self) -> Path:
        """Return the packaged template directory."""
        # Resolve templates from the installed package
        package_dir = Path(__file__).parent
        template_dir = package_dir.parent / "templates"
        return template_dir

    def get_memory_dir(self, cwd: Optional[Path] = None) -> Path:
        """Return the memory directory path."""
        if cwd is None:
            cwd = Path.cwd()
        return cwd / self.memory_dir_name

    def init(self, target_dir: Optional[str] = None, force: bool = False) -> bool:
        """
        Initialize OpenClaw Alignment memory files.

        Args:
            target_dir: Target directory (defaults to current working directory)
            force: Overwrite existing files when True

        Returns:
            True if initialization succeeds
        """
        if target_dir:
            cwd = Path(target_dir).resolve()
        else:
            cwd = Path.cwd()

        memory_dir = self.get_memory_dir(cwd)
        template_dir = self.get_template_dir()

        # Validate template directory
        if not template_dir.exists():
            print(f"❌ Error: template directory not found: {template_dir}")
            print("   Make sure openclaw-alignment is installed correctly")
            return False

        # Check whether the memory directory already exists
        if memory_dir.exists():
            if not force:
                print(f"⚠️  Memory directory already exists: {memory_dir}")
                print("   Use --force to re-initialize")
                return False
            print("🔄 Forcing re-initialization...")
        else:
            print("🚀 Initializing OpenClaw Alignment memory...")

        # Create memory directory
        memory_dir.mkdir(parents=True, exist_ok=True)

        # Create GEP subdirectory
        gep_dir = memory_dir / "gep"
        gep_dir.mkdir(parents=True, exist_ok=True)

        # Check for existing MD files and auto-migrate
        if not force:
            user_md = memory_dir / "USER.md"
            soul_md = memory_dir / "SOUL.md"
            agents_md = memory_dir / "AGENTS.md"

            if user_md.exists() or soul_md.exists() or agents_md.exists():
                print("🔄 Existing markdown files detected. Migrating to GEP format...")
                from .md_to_gep import MarkdownToGEPConverter
                from .gep_store import GEPStore

                gep_store = GEPStore(gep_dir)
                converter = MarkdownToGEPConverter()
                converter.migrate_all(memory_dir, gep_store)

        # Initialize empty genes.json and capsules.json if they don't exist
        from .gep_store import GEPStore
        gep_store = GEPStore(gep_dir)

        if not gep_store.genes_file.exists() or force:
            gep_store.save_genes({})
            print(f"✅ Created: {gep_store.genes_file}")

        if not gep_store.capsules_file.exists() or force:
            gep_store.save_capsules({})
            print(f"✅ Created: {gep_store.capsules_file}")

        # Create empty events.jsonl
        if not gep_store.events_file.exists() or force:
            gep_store.events_file.touch()
            print(f"✅ Created: {gep_store.events_file}")

        # Copy template files
        success_count = 0
        for target_name, template_name in self.templates.items():
            template_file = template_dir / template_name
            target_file = memory_dir / target_name

            if not template_file.exists():
                print(f"⚠️  Template file missing: {template_name}")
                continue

            if target_file.exists() and not force:
                print(f"⏭️  Skipped existing file: {target_name}")
                continue

            shutil.copy2(template_file, target_file)
            success_count += 1
            print(f"✅ Created: {target_file}")

        # Create config file
        config_file = memory_dir / self.config_file_name
        if not config_file.exists() or force:
            config = {
                "version": "1.0.0",
                "initialized_at": str(Path.cwd()),
                "memory_path": str(memory_dir),
                "features": {
                    "rl_enabled": True,
                    "auto_learning": True,
                    "safety_checks": True,
                },
            }
            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            print(f"✅ Created: {config_file}")

        # Create .gitignore
        gitignore_file = memory_dir / ".gitignore"
        if not gitignore_file.exists() or force:
            with open(gitignore_file, "w", encoding="utf-8") as f:
                f.write("# OpenClaw Alignment local files\n")
                f.write("# Do not commit these files\n")
                f.write("config.json\n")
                f.write("*.backup\n")
                f.write("*.cache\n")
            print(f"✅ Created: {gitignore_file}")

        # Print success summary
        print("")
        print("=" * 60)
        print("✨ Initialization complete!")
        print("=" * 60)
        print(f"📂 Memory directory: {memory_dir}")
        print("📄 Created files:")
        for target_name in self.templates.keys():
            print(f"   - {target_name}")
        print(f"   - {self.config_file_name}")
        print("   - .gitignore")
        print("")
        print("📝 Next steps:")
        print("   1. Edit USER.md to define your personal preferences")
        print("   2. Review SOUL.md to confirm system principles")
        print("   3. Check AGENTS.md to see available tools")
        print("   4. Run: openclaw-align analyze")
        print("")

        return True

    def status(self) -> None:
        """Show current local status."""
        cwd = Path.cwd()
        memory_dir = self.get_memory_dir(cwd)
        config_file = memory_dir / self.config_file_name
        gep_dir = memory_dir / "gep"

        print("📊 OpenClaw Alignment status")
        print("")
        print(f"📂 Memory directory: {memory_dir}")
        print(f"   Status: {'✅ Exists' if memory_dir.exists() else '❌ Missing'}")
        print("")

        if memory_dir.exists():
            print("📄 Configuration files:")

            # Check config file
            if config_file.exists():
                with open(config_file, "r", encoding="utf-8") as f:
                    config = json.load(f)
                print(f"   ✅ {self.config_file_name}")
                print(f"      Version: {config.get('version', 'unknown')}")
                print(f"      RL enabled: {config.get('features', {}).get('rl_enabled', False)}")
            else:
                print(f"   ❌ {self.config_file_name} (missing)")

            # Check template files
            for target_name in self.templates.keys():
                target_file = memory_dir / target_name
                status = "✅" if target_file.exists() else "❌"
                print(f"   {status} {target_name}")

            # Check GEP directory
            print("")
            print("🧬 GEP Assets:")
            if gep_dir.exists():
                from .gep_store import GEPStore
                gep_store = GEPStore(gep_dir)
                stats = gep_store.get_stats()
                print("   ✅ gep/ directory")
                print(f"      Genes: {stats['total_genes']}")
                print(f"      Capsules: {stats['total_capsules']}")
                print(f"      Events: {stats['total_events']}")
            else:
                print("   ❌ gep/ directory (missing)")
        else:
            print("💡 Tip: run 'openclaw-align init' to initialize memory files")
        print("")

    def version(self) -> None:
        """Show version info."""
        from . import __version__
        print(f"OpenClaw Alignment CLI v{__version__}")
        print("")
        print(f"Python: {__import__('sys').version}")
        print(f"Install path: {Path(__file__).parent.parent}")

    def gene_list(self) -> None:
        """List all genes."""
        cwd = Path.cwd()
        memory_dir = self.get_memory_dir(cwd)
        gep_dir = memory_dir / "gep"

        if not gep_dir.exists():
            print("❌ GEP directory not found. Run 'openclaw-align init' first.")
            return

        from .gep_store import GEPStore
        gep_store = GEPStore(gep_dir)
        genes = gep_store.load_genes()

        if not genes:
            print("📋 No genes found.")
            return

        print(f"📋 Genes ({len(genes)} total):")
        print("")
        for gene_id, gene in genes.items():
            print(f"   {gene}")

    def gene_show(self, gene_id: str) -> None:
        """Show gene details."""
        cwd = Path.cwd()
        memory_dir = self.get_memory_dir(cwd)
        gep_dir = memory_dir / "gep"

        if not gep_dir.exists():
            print("❌ GEP directory not found. Run 'openclaw-align init' first.")
            return

        from .gep_store import GEPStore
        gep_store = GEPStore(gep_dir)
        gene = gep_store.get_gene(gene_id)

        if not gene:
            print(f"❌ Gene not found: {gene_id}")
            return

        print(f"📄 Gene Details: {gene.id}")
        print("")
        print(f"Summary: {gene.summary}")
        print(f"Category: {gene.category}")
        print(f"Confidence: {gene.confidence:.2f}")
        print(f"Success Streak: {gene.success_streak}")
        print(f"Asset ID: {gene.asset_id}")
        print("")
        print("Strategy:")
        print(gene.strategy)
        if gene.trigger:
            print("")
            print(f"Triggers: {', '.join(gene.trigger)}")
        if gene.preconditions:
            print("")
            print("Preconditions:")
            for cond in gene.preconditions:
                print(f"  - {cond}")
        if gene.postconditions:
            print("")
            print("Postconditions:")
            for cond in gene.postconditions:
                print(f"  - {cond}")
        if gene.validation:
            print("")
            print("Validation:")
            for test in gene.validation:
                print(f"  - {test}")

    def capsule_list(self) -> None:
        """List all capsules."""
        cwd = Path.cwd()
        memory_dir = self.get_memory_dir(cwd)
        gep_dir = memory_dir / "gep"

        if not gep_dir.exists():
            print("❌ GEP directory not found. Run 'openclaw-align init' first.")
            return

        from .gep_store import GEPStore
        gep_store = GEPStore(gep_dir)
        capsules = gep_store.load_capsules()

        if not capsules:
            print("📋 No capsules found.")
            return

        print(f"📋 Capsules ({len(capsules)} total):")
        print("")
        for capsule_id, capsule in capsules.items():
            print(f"   {capsule}")

    def capsule_show(self, capsule_id: str) -> None:
        """Show capsule details."""
        cwd = Path.cwd()
        memory_dir = self.get_memory_dir(cwd)
        gep_dir = memory_dir / "gep"

        if not gep_dir.exists():
            print("❌ GEP directory not found. Run 'openclaw-align init' first.")
            return

        from .gep_store import GEPStore
        gep_store = GEPStore(gep_dir)
        capsule = gep_store.get_capsule(capsule_id)

        if not capsule:
            print(f"❌ Capsule not found: {capsule_id}")
            return

        print(f"📄 Capsule Details: {capsule.id}")
        print("")
        print(f"Summary: {capsule.summary}")
        print(f"Category: {capsule.category}")
        print(f"Confidence: {capsule.confidence:.2f}")
        print(f"Asset ID: {capsule.asset_id}")
        print("")
        if capsule.genes_used:
            print(f"Genes Used ({len(capsule.genes_used)}):")
            for gene_id in capsule.genes_used:
                print(f"  - {gene_id}")
        else:
            print("Genes Used: (none)")
        if capsule.trigger:
            print("")
            print(f"Triggers: {', '.join(capsule.trigger)}")

    def events_show(self, limit: int = 20) -> None:
        """Show recent evolution events."""
        cwd = Path.cwd()
        memory_dir = self.get_memory_dir(cwd)
        gep_dir = memory_dir / "gep"

        if not gep_dir.exists():
            print("❌ GEP directory not found. Run 'openclaw-align init' first.")
            return

        from .gep_store import GEPStore
        gep_store = GEPStore(gep_dir)
        events = gep_store.get_events(limit)

        if not events:
            print("📋 No events found.")
            return

        print(f"📋 Recent Evolution Events ({len(events)} shown):")
        print("")
        for event in events:
            print(f"   {event}")

    def export_md(self) -> None:
        """Export markdown files from Gene/Capsule assets."""
        cwd = Path.cwd()
        memory_dir = self.get_memory_dir(cwd)
        gep_dir = memory_dir / "gep"

        if not gep_dir.exists():
            print("❌ GEP directory not found. Run 'openclaw-align init' first.")
            return

        from .gep_to_md import GEPToMarkdownExporter
        exporter = GEPToMarkdownExporter()
        exporter.export_all(gep_dir, memory_dir)

        print("")
        print("✨ Markdown files exported successfully!")

    def confidence_history(self, task_type: Optional[str] = None) -> None:
        """Show confidence history."""
        cwd = Path.cwd()
        memory_dir = self.get_memory_dir(cwd)
        gep_dir = memory_dir / "gep"

        if not gep_dir.exists():
            print("❌ GEP directory not found. Run 'openclaw-align init' first.")
            return

        from .gep_store import GEPStore
        gep_store = GEPStore(gep_dir)
        genes = gep_store.load_genes()

        if not genes:
            print("📋 No genes found. Confidence history will be built as you execute tasks.")
            return

        # Filter genes
        if task_type:
            relevant_genes = [g for g in genes.values() if task_type in g.trigger]
        else:
            # Show all genes with confidence > 0.5
            relevant_genes = [g for g in genes.values() if g.confidence > 0.5]

        if not relevant_genes:
            if task_type:
                print(f"📋 No genes found for task type: {task_type}")
            else:
                print("📋 No high-confidence genes found yet (> 0.5)")
            return

        # Sort by confidence
        relevant_genes = sorted(relevant_genes, key=lambda g: -g.confidence)

        print(f"📊 Confidence History ({len(relevant_genes)} genes)")
        print("")
        print(f"{'Confidence':<12} {'Streak':<8} {'Gene Summary'}")
        print("-" * 60)
        for gene in relevant_genes:
            print(f"{gene.confidence:<12.2f} {gene.success_streak:<8} {gene.summary}")
        print("")

    def execute_demo(self, task_type: str = "T2", description: str = "run tests") -> None:
        """
        Demonstrate the intelligent confirmation flow.

        Args:
            task_type: Task type (T1/T2/T3/T4)
            description: Task description
        """
        cwd = Path.cwd()
        memory_dir = self.get_memory_dir(cwd)
        gep_dir = memory_dir / "gep"

        if not gep_dir.exists():
            print("❌ GEP directory not found. Run 'openclaw-align init' first.")
            return

        from .gep_store import GEPStore
        from .confirmation import IntelligentConfirmation

        gep_store = GEPStore(gep_dir)
        conf_engine = IntelligentConfirmation(gep_store)

        # Build task context
        task_context = {
            "task_type": task_type,
            "task_description": description,
            "command": f"npm run {description}",
            "files": []
        }

        print("🎯 Task execution demo")
        print(f"   Type: {task_type}")
        print(f"   Description: {description}")
        print("")

        # Decision: whether confirmation is required
        should_confirm, reason = conf_engine.should_confirm(task_context)

        if not should_confirm:
            # Auto-execute
            explanation = conf_engine.get_explanation(task_context, False, reason)
            print(explanation)

            # Simulate a successful execution
            print(f"⚡ Running command: {task_context['command']}")
            print("✅ Task completed")

            # Record feedback (auto execution success)
            conf_engine.record_feedback(
                task_context,
                was_confirmed=False,
                user_cancelled=False
            )
            print("📈 Confidence increased (+0.05)")

        else:
            # Confirmation required
            print(f"🤔 Confirmation required: {reason}")
            print("")
            response = input("Continue execution? [Y/n]: ").strip().lower()

            if response == 'n':
                print("❌ User cancelled execution")

                # Record feedback (user cancelled)
                conf_engine.record_feedback(
                    task_context,
                    was_confirmed=True,
                    user_cancelled=True
                )
                print("📉 Confidence decreased (-0.2)")
            else:
                print(f"⚡ Running command: {task_context['command']}")
                print("✅ Task completed")

                # Record feedback (user confirmed and succeeded)
                conf_engine.record_feedback(
                    task_context,
                    was_confirmed=True,
                    user_cancelled=False
                )

        print("")


def main():
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(
        description="OpenClaw Alignment - reinforcement-learning driven alignment system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  openclaw-align init                  Initialize memory files
  openclaw-align init --force          Force re-initialization
  openclaw-align init ~/projects       Initialize under a target directory
  openclaw-align status                Show current status
  openclaw-align version               Show version
  openclaw-align gene list             List all genes
  openclaw-align gene show <id>        Show gene details
  openclaw-align capsule list          List all capsules
  openclaw-align events                Show recent evolution events
  openclaw-align export-md             Export GEP to Markdown format
  openclaw-align confidence-history    Show confidence history
  openclaw-align execute-demo          Demo intelligent confirmation workflow
        """
    )

    parser.add_argument(
        "--version",
        action="store_true",
        help="Show version information"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # init command
    init_parser = subparsers.add_parser(
        "init",
        help="Initialize memory files"
    )
    init_parser.add_argument(
        "target_dir",
        nargs="?",
        help="Target directory (defaults to current directory)"
    )
    init_parser.add_argument(
        "--force",
        action="store_true",
        help="Force overwrite existing files"
    )

    # status command
    subparsers.add_parser(
        "status",
        help="Show current status"
    )

    # analyze command (keeps original behavior)
    analyze_parser = subparsers.add_parser(
        "analyze",
        help="Analyze Git history and learn preferences"
    )
    analyze_parser.add_argument(
        "--repo",
        default=".",
        help="Git repository path"
    )
    analyze_parser.add_argument(
        "--commits",
        type=int,
        default=100,
        help="Number of commits to analyze"
    )

    # gene command
    gene_parser = subparsers.add_parser(
        "gene",
        help="Gene management commands"
    )
    gene_subparsers = gene_parser.add_subparsers(dest="gene_command", help="Gene actions")

    gene_subparsers.add_parser("list", help="List all genes")
    gene_show_parser = gene_subparsers.add_parser("show", help="Show gene details")
    gene_show_parser.add_argument("gene_id", help="Gene ID")

    # capsule command
    capsule_parser = subparsers.add_parser(
        "capsule",
        help="Capsule management commands"
    )
    capsule_subparsers = capsule_parser.add_subparsers(dest="capsule_command", help="Capsule actions")

    capsule_subparsers.add_parser("list", help="List all capsules")
    capsule_show_parser = capsule_subparsers.add_parser("show", help="Show capsule details")
    capsule_show_parser.add_argument("capsule_id", help="Capsule ID")

    # events command
    events_parser = subparsers.add_parser(
        "events",
        help="Show evolution events"
    )
    events_parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Number of events to show (default: 20)"
    )

    # export-md command
    subparsers.add_parser(
        "export-md",
        help="Export GEP assets to Markdown format"
    )

    # confidence-history command
    conf_history_parser = subparsers.add_parser(
        "confidence-history",
        help="Show confidence history for learned preferences"
    )
    conf_history_parser.add_argument(
        "--task-type",
        help="Filter by task type (e.g., T1, T2, T3, T4)"
    )

    # execute-demo command
    execute_parser = subparsers.add_parser(
        "execute-demo",
        help="Demonstrate intelligent confirmation workflow"
    )
    execute_parser.add_argument(
        "--task-type",
        default="T2",
        help="Task type (default: T2)"
    )
    execute_parser.add_argument(
        "--description",
        default="run tests",
        help="Task description (default: 'run tests')"
    )

    args = parser.parse_args()
    cli = OpenClawAlignmentCLI()

    # Show version
    if args.version:
        cli.version()
        return

    # Execute command
    if args.command == "init":
        success = cli.init(
            target_dir=args.target_dir,
            force=args.force
        )
        exit(0 if success else 1)

    elif args.command == "status":
        cli.status()

    elif args.command == "analyze":
        # Call the existing analysis flow
        from .integration import IntentAlignmentEngine
        engine = IntentAlignmentEngine(args.repo)
        engine.run_analysis(args.commits)

    elif args.command == "gene":
        if args.gene_command == "list":
            cli.gene_list()
        elif args.gene_command == "show":
            cli.gene_show(args.gene_id)
        else:
            gene_parser.print_help()

    elif args.command == "capsule":
        if args.capsule_command == "list":
            cli.capsule_list()
        elif args.capsule_command == "show":
            cli.capsule_show(args.capsule_id)
        else:
            capsule_parser.print_help()

    elif args.command == "events":
        cli.events_show(args.limit)

    elif args.command == "export-md":
        cli.export_md()

    elif args.command == "confidence-history":
        cli.confidence_history(args.task_type)

    elif args.command == "execute-demo":
        cli.execute_demo(args.task_type, args.description)

    else:
        # Default behavior: print help
        parser.print_help()


if __name__ == "__main__":
    main()
