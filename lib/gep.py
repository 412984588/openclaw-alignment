#!/usr/bin/env python3
"""
GEP (Genome Evolution Protocol) 数据模型

支持 Gene（基因）、Capsule（胶囊）、Event（事件）三种核心数据类型。
用于 OpenClaw agent 能力共享和进化追踪。
"""

import json
import hashlib
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
from datetime import datetime


@dataclass
class Gene:
    """
    GEP Gene 数据模型 - 单一能力/策略

    映射关系：USER.md 的单个配置项 → Gene

    Attributes:
        id: Gene 唯一标识符
        type: 固定为 "Gene"
        summary: 能力描述（中文）
        category: 类别（repair|optimize|innovate|harden）
        trigger: 触发信号列表
        strategy: 执行策略描述
        preconditions: 前置条件列表
        postconditions: 后置条件列表
        validation: 验证测试列表
        confidence: 信心度（0.0-1.0）
        success_streak: 连续成功次数
        asset_id: SHA256 资产 ID
    """
    id: str
    type: str = "Gene"
    summary: str = ""
    category: str = "innovate"  # repair|optimize|innovate|harden
    trigger: List[str] = field(default_factory=list)
    strategy: str = ""
    preconditions: List[str] = field(default_factory=list)
    postconditions: List[str] = field(default_factory=list)
    validation: List[str] = field(default_factory=list)
    confidence: float = 0.0
    success_streak: int = 0
    asset_id: str = ""

    def calculate_asset_id(self) -> str:
        """
        计算 SHA256 asset_id

        基于 Gene 的核心内容计算 SHA256 哈希值，用于资产追踪和去重。

        Returns:
            SHA256 哈希值（十六进制字符串）
        """
        # 创建规范化的内容字符串（排除 asset_id 本身）
        content_dict = asdict(self)
        content_dict.pop('asset_id', None)

        # 序列化为 JSON 并排序键（确保一致性）
        content_str = json.dumps(content_dict, sort_keys=True, ensure_ascii=False)

        # 计算 SHA256
        sha256_hash = hashlib.sha256(content_str.encode('utf-8')).hexdigest()
        self.asset_id = f"sha256:{sha256_hash}"

        return self.asset_id

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Gene':
        """从字典创建 Gene 实例"""
        return cls(**data)

    def increment_confidence(self, reward: float) -> None:
        """
        基于 RL reward 更新信心度和连续成功次数

        Args:
            reward: RL reward (0.0-1.0)
        """
        if reward > 0.7:
            # 高奖励：增加信心度和成功次数
            self.success_streak += 1
            self.confidence = min(1.0, self.confidence + 0.05)
        elif reward < 0.3:
            # 低奖励：减少信心度和成功次数
            self.success_streak = 0
            self.confidence = max(0.0, self.confidence - 0.1)

    def __str__(self) -> str:
        """字符串表示（用于 CLI 显示）"""
        return f"[{self.id}] {self.summary} (信心度: {self.confidence:.2f})"


@dataclass
class Capsule:
    """
    GEP Capsule 数据模型 - 完整解决方案

    映射关系：SOUL.md + AGENTS.md 组合 → Capsule

    Attributes:
        id: Capsule 唯一标识符
        type: 固定为 "Capsule"
        summary: 完整解决方案描述
        genes_used: 使用的 Gene ID 列表
        trigger: 触发信号列表
        category: 类别（默认为 innovate）
        confidence: 信心度（0.0-1.0）
        asset_id: SHA256 资产 ID
    """
    id: str
    type: str = "Capsule"
    summary: str = ""
    genes_used: List[str] = field(default_factory=list)
    trigger: List[str] = field(default_factory=list)
    category: str = "innovate"
    confidence: float = 0.0
    asset_id: str = ""

    def calculate_asset_id(self) -> str:
        """
        计算 SHA256 asset_id

        基于 Capsule 的核心内容计算 SHA256 哈希值。

        Returns:
            SHA256 哈希值（十六进制字符串）
        """
        # 创建规范化的内容字符串
        content_dict = asdict(self)
        content_dict.pop('asset_id', None)

        # 序列化为 JSON 并排序键
        content_str = json.dumps(content_dict, sort_keys=True, ensure_ascii=False)

        # 计算 SHA256
        sha256_hash = hashlib.sha256(content_str.encode('utf-8')).hexdigest()
        self.asset_id = f"sha256:{sha256_hash}"

        return self.asset_id

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Capsule':
        """从字典创建 Capsule 实例"""
        return cls(**data)

    def __str__(self) -> str:
        """字符串表示（用于 CLI 显示）"""
        return f"[{self.id}] {self.summary} (使用 {len(self.genes_used)} 个 Gene, 信心度: {self.confidence:.2f})"


@dataclass
class Event:
    """
    GEP Event 数据模型 - 进化审计记录

    存储格式：events.jsonl（每行一个 JSON，追加模式）

    Attributes:
        timestamp: ISO 8601 时间戳
        event_type: 事件类型（gene_created|gene_updated|capsule_created|capsule_updated）
        asset_id: 关联的资产 ID
        trigger_signals: 触发信号列表
        rl_reward: RL reward（0.0-1.0）
        changes: 变更描述
        source_node_id: 来源节点 ID
    """
    timestamp: str
    event_type: str  # gene_created|gene_updated|capsule_created|capsule_updated
    asset_id: str
    trigger_signals: List[str] = field(default_factory=list)
    rl_reward: float = 0.0
    changes: str = ""
    source_node_id: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Event':
        """从字典创建 Event 实例"""
        return cls(**data)

    def to_jsonl(self) -> str:
        """转换为 JSONL 格式（单行 JSON）"""
        return json.dumps(asdict(self), ensure_ascii=False)

    @classmethod
    def from_jsonl(cls, jsonl_str: str) -> 'Event':
        """从 JSONL 格式解析"""
        data = json.loads(jsonl_str)
        return cls(**data)

    def __str__(self) -> str:
        """字符串表示（用于 CLI 显示）"""
        return f"[{self.timestamp}] {self.event_type}: {self.changes} (reward: {self.rl_reward:.2f})"
