#!/usr/bin/env python3
"""
GEP 存储管理器

管理 Gene、Capsule、Event 的持久化存储。
支持 JSON 和 JSONL 格式。
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any

from .gep import Gene, Capsule, Event


class GEPStore:
    """
    GEP 资产存储管理器

    负责管理 Gene、Capsule、Event 的持久化存储。

    Attributes:
        base_dir: GEP 存储目录
        genes_file: Gene 库文件路径（genes.json）
        capsules_file: Capsule 库文件路径（capsules.json）
        events_file: Event 审计日志路径（events.jsonl）
    """

    def __init__(self, base_dir: Path):
        """
        初始化 GEP Store

        Args:
            base_dir: GEP 存储基础目录
        """
        self.base_dir = Path(base_dir)
        self.genes_file = self.base_dir / "genes.json"
        self.capsules_file = self.base_dir / "capsules.json"
        self.events_file = self.base_dir / "events.jsonl"

        # 确保目录存在
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def load_genes(self) -> Dict[str, Gene]:
        """
        加载所有 Gene

        Returns:
            Gene 字典（key: gene_id, value: Gene 对象）
        """
        if not self.genes_file.exists():
            return {}

        try:
            with open(self.genes_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            return {
                gene_id: Gene.from_dict(gene_data)
                for gene_id, gene_data in data.items()
            }
        except Exception as e:
            print(f"⚠️  加载 Gene 失败: {e}")
            return {}

    def save_genes(self, genes: Dict[str, Gene]) -> None:
        """
        保存 Gene 到 genes.json

        Args:
            genes: Gene 字典
        """
        try:
            # 转换为可序列化的字典
            data = {
                gene_id: gene.to_dict()
                for gene_id, gene in genes.items()
            }

            # 写入文件（原子操作：先写临时文件再重命名）
            temp_file = self.genes_file.with_suffix('.tmp')
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            # 原子重命名
            temp_file.replace(self.genes_file)

        except Exception as e:
            print(f"❌ 保存 Gene 失败: {e}")
            raise

    def load_capsules(self) -> Dict[str, Capsule]:
        """
        加载所有 Capsule

        Returns:
            Capsule 字典（key: capsule_id, value: Capsule 对象）
        """
        if not self.capsules_file.exists():
            return {}

        try:
            with open(self.capsules_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            return {
                capsule_id: Capsule.from_dict(capsule_data)
                for capsule_id, capsule_data in data.items()
            }
        except Exception as e:
            print(f"⚠️  加载 Capsule 失败: {e}")
            return {}

    def save_capsules(self, capsules: Dict[str, Capsule]) -> None:
        """
        保存 Capsule 到 capsules.json

        Args:
            capsules: Capsule 字典
        """
        try:
            # 转换为可序列化的字典
            data = {
                capsule_id: capsule.to_dict()
                for capsule_id, capsule in capsules.items()
            }

            # 写入文件（原子操作）
            temp_file = self.capsules_file.with_suffix('.tmp')
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            # 原子重命名
            temp_file.replace(self.capsules_file)

        except Exception as e:
            print(f"❌ 保存 Capsule 失败: {e}")
            raise

    def append_event(self, event: Event) -> None:
        """
        追加 Event 到 events.jsonl（追加模式）

        Args:
            event: Event 对象
        """
        try:
            # 确保文件存在
            if not self.events_file.exists():
                self.events_file.touch()

            # 追加一行 JSON
            with open(self.events_file, 'a', encoding='utf-8') as f:
                f.write(event.to_jsonl() + '\n')

        except Exception as e:
            print(f"❌ 追加 Event 失败: {e}")
            raise

    def get_events(self, limit: int = 100) -> List[Event]:
        """
        读取最近的 N 个 Event（从末尾向前读取）

        Args:
            limit: 读取的最大数量

        Returns:
            Event 列表（按时间倒序）
        """
        if not self.events_file.exists():
            return []

        try:
            events = []
            with open(self.events_file, 'r', encoding='utf-8') as f:
                # 读取所有行
                lines = f.readlines()

                # 从末尾向前读取
                for line in reversed(lines[-limit:]):
                    line = line.strip()
                    if line:
                        try:
                            event = Event.from_jsonl(line)
                            events.append(event)
                        except Exception:
                            # 跳过无效行
                            continue

            return events

        except Exception as e:
            print(f"⚠️  读取 Event 失败: {e}")
            return []

    def get_gene(self, gene_id: str) -> Optional[Gene]:
        """
        获取单个 Gene

        Args:
            gene_id: Gene ID

        Returns:
            Gene 对象，如果不存在则返回 None
        """
        genes = self.load_genes()
        return genes.get(gene_id)

    def save_gene(self, gene: Gene) -> None:
        """
        保存单个 Gene（更新或新增）

        Args:
            gene: Gene 对象
        """
        genes = self.load_genes()
        genes[gene.id] = gene
        self.save_genes(genes)

    def get_capsule(self, capsule_id: str) -> Optional[Capsule]:
        """
        获取单个 Capsule

        Args:
            capsule_id: Capsule ID

        Returns:
            Capsule 对象，如果不存在则返回 None
        """
        capsules = self.load_capsules()
        return capsules.get(capsule_id)

    def save_capsule(self, capsule: Capsule) -> None:
        """
        保存单个 Capsule（更新或新增）

        Args:
            capsule: Capsule 对象
        """
        capsules = self.load_capsules()
        capsules[capsule.id] = capsule
        self.save_capsules(capsules)

    def delete_gene(self, gene_id: str) -> bool:
        """
        删除单个 Gene

        Args:
            gene_id: Gene ID

        Returns:
            是否成功删除
        """
        genes = self.load_genes()
        if gene_id in genes:
            del genes[gene_id]
            self.save_genes(genes)
            return True
        return False

    def delete_capsule(self, capsule_id: str) -> bool:
        """
        删除单个 Capsule

        Args:
            capsule_id: Capsule ID

        Returns:
            是否成功删除
        """
        capsules = self.load_capsules()
        if capsule_id in capsules:
            del capsules[capsule_id]
            self.save_capsules(capsules)
            return True
        return False

    def get_stats(self) -> Dict[str, Any]:
        """
        获取存储统计信息

        Returns:
            统计信息字典
        """
        genes = self.load_genes()
        capsules = self.load_capsules()
        events = self.get_events(limit=1000000)  # 获取所有事件

        return {
            "total_genes": len(genes),
            "total_capsules": len(capsules),
            "total_events": len(events),
            "genes_file_size": self.genes_file.stat().st_size if self.genes_file.exists() else 0,
            "capsules_file_size": self.capsules_file.stat().st_size if self.capsules_file.exists() else 0,
            "events_file_size": self.events_file.stat().st_size if self.events_file.exists() else 0,
        }
