#!/usr/bin/env python3
"""
数据收集模块 - 从Git历史和用户操作中收集偏好数据
"""

import os
import subprocess
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any


class GitPreferenceCollector:
    """从Git历史收集技术偏好"""

    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path).resolve()
        self.preferences = {
            "tech_stack": {},
            "file_types": {},
            "commit_patterns": {},
            "workflow": {}
        }

    def collect(self, max_commits: int = 100) -> Dict[str, Any]:
        """收集Git历史中的偏好数据"""
        print(f"📊 正在分析Git历史（最近{max_commits}次提交）...")

        # 获取提交历史
        commits = self._get_commits(max_commits)
        print(f"✅ 分析了 {len(commits)} 次提交")

        # 分析技术栈
        self.preferences["tech_stack"] = self._analyze_tech_stack(commits)

        # 分析文件类型
        self.preferences["file_types"] = self._analyze_file_types(commits)

        # 分析工作流模式
        self.preferences["workflow"] = self._analyze_workflow(commits)

        # 添加元数据
        self.preferences["metadata"] = {
            "collected_at": datetime.now().isoformat(),
            "repo_path": str(self.repo_path),
            "commits_analyzed": len(commits),
            "confidence": self._calculate_confidence()
        }

        return self.preferences

    def _get_commits(self, max_count: int) -> List[Dict[str, Any]]:
        """获取Git提交历史"""
        try:
            result = subprocess.run(
                ["git", "log", f"-{max_count}", "--pretty=format:%H|%s|%an", "--name-only"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                print("⚠️  无法获取Git历史")
                return []

            commits = []
            lines = result.stdout.strip().split('\n')

            current_commit = None
            for line in lines:
                if '|' in line:  # 提交信息行
                    parts = line.split('|')
                    current_commit = {
                        "hash": parts[0],
                        "subject": parts[1],
                        "author": parts[2],
                        "files": []
                    }
                    commits.append(current_commit)
                elif current_commit and line:  # 文件行
                    current_commit["files"].append(line)

            return commits

        except subprocess.TimeoutExpired:
            print("⚠️  Git命令超时")
            return []
        except Exception as e:
            print(f"⚠️  获取Git历史失败: {e}")
            return []

    def _analyze_tech_stack(self, commits: List[Dict]) -> Dict[str, int]:
        """分析技术栈偏好"""
        tech_stack = {
            "python": 0,
            "javascript": 0,
            "typescript": 0,
            "react": 0,
            "vue": 0,
            "fastapi": 0,
            "node": 0
        }

        for commit in commits:
            for file_path in commit.get("files", []):
                file_lower = file_path.lower()

                # 检测Python
                if file_path.endswith('.py'):
                    tech_stack["python"] += 1

                # 检测JavaScript/TypeScript
                if file_path.endswith('.js'):
                    tech_stack["javascript"] += 1
                if file_path.endswith('.ts') or file_path.endswith('.tsx'):
                    tech_stack["typescript"] += 1

                # 检测React
                if "react" in file_lower or file_path.endswith('.jsx'):
                    tech_stack["react"] += 1

                # 检测Vue
                if "vue" in file_lower:
                    tech_stack["vue"] += 1

                # 检测FastAPI
                if "fastapi" in file_lower:
                    tech_stack["fastapi"] += 1

                # 检测Node
                if "package.json" in file_path:
                    tech_stack["node"] += 1

        return tech_stack

    def _analyze_file_types(self, commits: List[Dict]) -> Dict[str, int]:
        """分析文件类型偏好"""
        file_types = {}

        for commit in commits:
            for file_path in commit.get("files", []):
                ext = Path(file_path).suffix or "(无后缀)"
                file_types[ext] = file_types.get(ext, 0) + 1

        return file_types

    def _analyze_workflow(self, commits: List[Dict]) -> Dict[str, Any]:
        """分析工作流模式"""
        workflow = {
            "test_first": False,
            "commit_frequency": {},
            "pair_programming": False
        }

        # 检查是否有测试驱动开发模式
        test_commits = [c for c in commits if any(
            "test" in f.lower() for f in c.get("files", [])
        )]

        if len(test_commits) > len(commits) * 0.3:
            workflow["test_first"] = True
            workflow["test_ratio"] = len(test_commits) / len(commits)

        return workflow

    def _calculate_confidence(self) -> float:
        """计算置信度"""
        total_commits = sum(self.preferences["tech_stack"].values())
        if total_commits < 10:
            return 0.3  # 数据不足，低置信度
        elif total_commits < 50:
            return 0.7  # 中等置信度
        else:
            return 0.95  # 高置信度


def main():
    """测试数据收集"""
    collector = GitPreferenceCollector()
    preferences = collector.collect()

    print("\n📊 学习结果：")
    print(f"技术栈偏好：")
    for tech, count in sorted(preferences["tech_stack"].items(), key=lambda x: x[1], reverse=True):
        if count > 0:
            print(f"  - {tech}: {count}次")

    print(f"\n文件类型偏好：")
    for ext, count in sorted(preferences["file_types"].items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"  - {ext}: {count}次")

    print(f"\n置信度: {preferences['metadata']['confidence']*100}%")


if __name__ == "__main__":
    main()
