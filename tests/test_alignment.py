#!/usr/bin/env python3
"""
测试意图对齐功能
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.integration import IntentAlignmentEngine


def test_collector():
    """测试数据收集"""
    print("="*50)
    print("测试1: 数据收集")
    print("="*50)

    engine = IntentAlignmentEngine(".")
    git_data = engine.collector.collect(50)

    assert git_data is not None, "数据收集失败"
    assert "tech_stack" in git_data, "缺少技术栈数据"
    assert "metadata" in git_data, "缺少元数据"

    print("✅ 数据收集测试通过")
    print()


def test_learner():
    """测试学习算法"""
    print("="*50)
    print("测试2: 学习算法")
    print("="*50)

    # 创建engine
    from lib.learner import PreferenceLearner
    learner = PreferenceLearner()

    # 模拟数据
    mock_data = {
        "tech_stack": {
            "python": 10,
            "javascript": 5,
            "react": 8
        },
        "workflow": {
            "test_first": True,
            "test_ratio": 0.4
        },
        "metadata": {
            "confidence": 0.8
        }
    }

    preferences = learner.learn_from_git_history(mock_data)

    assert preferences is not None, "学习失败"
    assert "tech_stack" in preferences, "缺少技术栈偏好"
    assert preferences["tech_stack"]["primary"] == "python", "主要技术识别错误"

    print("✅ 学习算法测试通过")
    print()


def test_integration():
    """测试完整集成"""
    print("="*50)
    print("测试3: 完整集成")
    print("="*50)

    engine = IntentAlignmentEngine(".")

    # 运行分析
    result = engine.run_analysis(10)

    assert result is not None, "分析失败"
    assert "tech_stack" in result, "缺少技术栈结果"

    print("✅ 集成测试通过")
    print()


def main():
    """运行所有测试"""
    print("\n🧪 开始测试意图对齐功能...\n")

    try:
        test_collector()
        test_learner()
        # test_integration()  # 需要Git仓库，暂时跳过

        print("="*50)
        print("✅ 所有测试通过！")
        print("="*50)

    except AssertionError as e:
        print(f"❌ 测试失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
