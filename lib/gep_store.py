#!/usr/bin/env python3
"""Persistence layer for GEP assets (genes, capsules, events)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .gep import Capsule, Event, Gene


class GEPStore:
    """Storage manager for Gene/Capsule/Event assets."""

    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)
        self.genes_file = self.base_dir / "genes.json"
        self.capsules_file = self.base_dir / "capsules.json"
        self.events_file = self.base_dir / "events.jsonl"
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def load_genes(self) -> dict[str, Gene]:
        """Load all genes from `genes.json`."""
        if not self.genes_file.exists():
            return {}

        try:
            data = json.loads(self.genes_file.read_text(encoding="utf-8"))
            return {gene_id: Gene.from_dict(gene_data) for gene_id, gene_data in data.items()}
        except Exception as exc:
            print(f"⚠️  Failed to load genes: {exc}")
            return {}

    def save_genes(self, genes: dict[str, Gene]) -> None:
        """Persist genes to disk atomically."""
        data = {gene_id: gene.to_dict() for gene_id, gene in genes.items()}
        self._atomic_write_json(self.genes_file, data)

    def load_capsules(self) -> dict[str, Capsule]:
        """Load all capsules from `capsules.json`."""
        if not self.capsules_file.exists():
            return {}

        try:
            data = json.loads(self.capsules_file.read_text(encoding="utf-8"))
            return {
                capsule_id: Capsule.from_dict(capsule_data)
                for capsule_id, capsule_data in data.items()
            }
        except Exception as exc:
            print(f"⚠️  Failed to load capsules: {exc}")
            return {}

    def save_capsules(self, capsules: dict[str, Capsule]) -> None:
        """Persist capsules to disk atomically."""
        data = {capsule_id: capsule.to_dict() for capsule_id, capsule in capsules.items()}
        self._atomic_write_json(self.capsules_file, data)

    @staticmethod
    def _atomic_write_json(path: Path, data: dict[str, Any]) -> None:
        temp_file = path.with_suffix(".tmp")
        temp_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        temp_file.replace(path)

    def append_event(self, event: Event) -> None:
        """Append one event to `events.jsonl`."""
        if not self.events_file.exists():
            self.events_file.touch()
        with open(self.events_file, "a", encoding="utf-8") as handle:
            handle.write(event.to_jsonl() + "\n")

    def get_events(self, limit: int = 100) -> list[Event]:
        """Return latest events in reverse chronological order."""
        if not self.events_file.exists():
            return []

        events: list[Event] = []
        try:
            lines = self.events_file.read_text(encoding="utf-8").splitlines()
            for line in reversed(lines[-limit:]):
                payload = line.strip()
                if not payload:
                    continue
                try:
                    events.append(Event.from_jsonl(payload))
                except Exception:
                    continue
            return events
        except Exception as exc:
            print(f"⚠️  Failed to read events: {exc}")
            return []

    def get_gene(self, gene_id: str) -> Gene | None:
        """Return one gene by id."""
        return self.load_genes().get(gene_id)

    def save_gene(self, gene: Gene) -> None:
        """Insert or update one gene."""
        genes = self.load_genes()
        genes[gene.id] = gene
        self.save_genes(genes)

    def get_capsule(self, capsule_id: str) -> Capsule | None:
        """Return one capsule by id."""
        return self.load_capsules().get(capsule_id)

    def save_capsule(self, capsule: Capsule) -> None:
        """Insert or update one capsule."""
        capsules = self.load_capsules()
        capsules[capsule.id] = capsule
        self.save_capsules(capsules)

    def delete_gene(self, gene_id: str) -> bool:
        """Delete one gene if it exists."""
        genes = self.load_genes()
        if gene_id not in genes:
            return False
        del genes[gene_id]
        self.save_genes(genes)
        return True

    def delete_capsule(self, capsule_id: str) -> bool:
        """Delete one capsule if it exists."""
        capsules = self.load_capsules()
        if capsule_id not in capsules:
            return False
        del capsules[capsule_id]
        self.save_capsules(capsules)
        return True

    def get_stats(self) -> dict[str, Any]:
        """Return aggregated storage statistics."""
        genes = self.load_genes()
        capsules = self.load_capsules()
        events = self.get_events(limit=1_000_000)

        return {
            "total_genes": len(genes),
            "total_capsules": len(capsules),
            "total_events": len(events),
            "genes_file_size": self.genes_file.stat().st_size if self.genes_file.exists() else 0,
            "capsules_file_size": self.capsules_file.stat().st_size if self.capsules_file.exists() else 0,
            "events_file_size": self.events_file.stat().st_size if self.events_file.exists() else 0,
        }
