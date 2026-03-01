#!/usr/bin/env python3
"""
监控面板 - TensorBoard集成与训练可视化

实现完整的训练监控功能：
- TensorBoard日志记录
- 奖励曲线可视化
- 损失曲线追踪
- 超参数对比
- 模型性能分析

Phase 3.3 - 预计180行
"""

import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import json
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# 尝试导入TensorBoard
try:
    from torch.utils.tensorboard import SummaryWriter
    TENSORBOARD_AVAILABLE = True
except ImportError:
    TENSORBOARD_AVAILABLE = False
    SummaryWriter = None


class TrainingMonitor:
    """
    训练监控器

    功能：
    - TensorBoard日志记录
    - 指标追踪（奖励、损失、性能）
    - 检查点比较
    - 训练报告生成
    """

    def __init__(self,
                 log_dir: str = "./logs/tensorboard",
                 experiment_name: str = None):
        """
        初始化监控器

        Args:
            log_dir: 日志目录
            experiment_name: 实验名称
        """
        self.log_dir = Path(log_dir).expanduser()
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # 创建实验目录
        if experiment_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.experiment_dir = self.log_dir / f"{experiment_name}_{timestamp}"
        else:
            self.experiment_dir = self.log_dir / datetime.now().strftime("%Y%m%d_%H%M%S")

        self.experiment_dir.mkdir(parents=True, exist_ok=True)

        # 初始化TensorBoard writer
        self.tensorboard_enabled = TENSORBOARD_AVAILABLE
        if self.tensorboard_enabled:
            self.writer = SummaryWriter(log_dir=str(self.experiment_dir))
            logger.info(f"✅ TensorBoard已启用: {self.experiment_dir}")
        else:
            self.writer = None
            logger.warning("⚠️ TensorBoard不可用，使用降级模式（JSON日志）")

        # 指标记录
        self.metrics_history: Dict[str, List[Tuple[int, float]]] = {}
        self._closed = False

    def log_scalar(self, tag: str, value: float, step: int):
        """
        记录标量指标

        Args:
            tag: 指标标签（如"train/reward", "train/loss"）
            value: 指标值
            step: 步数
        """
        if self.tensorboard_enabled and self.writer:
            self.writer.add_scalar(tag, value, step)

        # 同时记录到内存（用于降级模式）
        if tag not in self.metrics_history:
            self.metrics_history[tag] = []
        self.metrics_history[tag].append((step, value))

    def log_scalars(self, main_tag: str, tag_scalar_dict: Dict[str, float], step: int):
        """
        批量记录标量指标

        Args:
            main_tag: 主标签
            tag_scalar_dict: 标签-值字典
            step: 步数
        """
        if self.tensorboard_enabled and self.writer:
            self.writer.add_scalars(main_tag, tag_scalar_dict, step)

        # 记录到内存
        for sub_tag, value in tag_scalar_dict.items():
            full_tag = f"{main_tag}/{sub_tag}"
            if full_tag not in self.metrics_history:
                self.metrics_history[full_tag] = []
            self.metrics_history[full_tag].append((step, value))

    def log_histogram(self, tag: str, values: np.ndarray, step: int):
        """
        记录直方图

        Args:
            tag: 标签
            values: 值数组
            step: 步数
        """
        if self.tensorboard_enabled and self.writer:
            self.writer.add_histogram(tag, values, step)

    def log_hyperparams(self, hparam_dict: Dict[str, Any], metric_dict: Dict[str, float]):
        """
        记录超参数和最终指标

        Args:
            hparam_dict: 超参数字典
            metric_dict: 指标字典
        """
        if self.tensorboard_enabled and self.writer:
            from torch.utils.tensorboard.summary import hparams
            self.writer.add_hparams(hparam_dict, metric_dict)

    def log_training_step(self,
                         episode: int,
                         reward: float,
                         actor_loss: float,
                         critic_loss: float,
                         extra_metrics: Dict[str, float] = None):
        """
        记录训练步骤（便捷方法）

        Args:
            episode: Episode数
            reward: 奖励
            actor_loss: Actor损失
            critic_loss: Critic损失
            extra_metrics: 额外指标
        """
        # 记录主要指标
        self.log_scalar("train/reward", reward, episode)
        self.log_scalar("train/actor_loss", actor_loss, episode)
        self.log_scalar("train/critic_loss", critic_loss, episode)

        # 记录额外指标
        if extra_metrics:
            for key, value in extra_metrics.items():
                self.log_scalar(f"train/{key}", value, episode)

    def log_evaluation(self,
                      episode: int,
                      eval_reward: float,
                      eval_success_rate: float,
                      eval_metrics: Dict[str, float] = None):
        """
        记录评估指标

        Args:
            episode: Episode数
            eval_reward: 评估奖励
            eval_success_rate: 成功率
            eval_metrics: 额外评估指标
        """
        self.log_scalar("eval/reward", eval_reward, episode)
        self.log_scalar("eval/success_rate", eval_success_rate, episode)

        if eval_metrics:
            for key, value in eval_metrics.items():
                self.log_scalar(f"eval/{key}", value, episode)

    def log_model_weights(self, tag: str, weights: np.ndarray, step: int):
        """
        记录模型权重分布

        Args:
            tag: 标签（如"policy_net/layer1"）
            weights: 权重数组
            step: 步数
        """
        self.log_histogram(tag, weights, step)

        # 记录统计量
        self.log_scalars(
            f"{tag}/stats",
            {
                "mean": float(np.mean(weights)),
                "std": float(np.std(weights)),
                "min": float(np.min(weights)),
                "max": float(np.max(weights))
            },
            step
        )

    def save_metrics_to_json(self, filename: str = None) -> str:
        """
        保存指标到JSON文件（降级模式）

        Args:
            filename: 文件名

        Returns:
            文件路径
        """
        if not filename:
            filename = f"metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        filepath = self.experiment_dir / filename

        with open(filepath, 'w') as f:
            json.dump(self.metrics_history, f, indent=2)

        logger.info(f"✅ 指标已保存: {filepath}")
        return str(filepath)

    def get_metrics_summary(self) -> Dict[str, Any]:
        """
        获取指标汇总

        Returns:
            指标汇总统计
        """
        summary = {}

        for tag, history in self.metrics_history.items():
            if not history:
                continue

            steps, values = zip(*history)

            summary[tag] = {
                "count": len(values),
                "mean": float(np.mean(values)),
                "std": float(np.std(values)),
                "min": float(np.min(values)),
                "max": float(np.max(values)),
                "latest": float(values[-1]),
                "first": float(values[0]),
                "improvement": float(values[-1] - values[0]) if len(values) > 1 else 0.0
            }

        return summary

    def plot_metrics(self, tags: List[str] = None, save_path: str = None):
        """
        绘制指标曲线（降级模式）

        Args:
            tags: 要绘制的指标标签（None=全部）
            save_path: 保存路径
        """
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            logger.warning("⚠️ matplotlib不可用，无法绘图")
            return

        if tags is None:
            tags = list(self.metrics_history.keys())

        # 创建子图
        n_plots = len(tags)
        n_cols = min(3, n_plots)
        n_rows = (n_plots + n_cols - 1) // n_cols

        fig, axes = plt.subplots(n_rows, n_cols, figsize=(15, 5 * n_rows))
        if n_plots == 1:
            axes = [axes]
        else:
            axes = axes.flatten()

        # 绘制每个指标
        for i, tag in enumerate(tags):
            if tag not in self.metrics_history:
                continue

            steps, values = zip(*self.metrics_history[tag])

            axes[i].plot(steps, values, 'b-', linewidth=2)
            axes[i].set_title(tag)
            axes[i].set_xlabel('Step')
            axes[i].set_ylabel('Value')
            axes[i].grid(True, alpha=0.3)

        # 隐藏多余的子图
        for i in range(n_plots, len(axes)):
            axes[i].set_visible(False)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            logger.info(f"✅ 图表已保存: {save_path}")
        else:
            save_path = self.experiment_dir / "metrics_plot.png"
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            logger.info(f"✅ 图表已保存: {save_path}")

        plt.close()

    def compare_experiments(self,
                          experiment_dirs: List[str],
                          metric_tags: List[str]) -> Dict[str, Any]:
        """
        比较多个实验

        Args:
            experiment_dirs: 实验目录列表
            metric_tags: 要比较的指标标签

        Returns:
            比较结果
        """
        comparison = {
            "experiments": [],
            "metrics": {}
        }

        for exp_dir in experiment_dirs:
            exp_path = Path(exp_dir)
            if not exp_path.exists():
                logger.warning(f"⚠️ 实验目录不存在: {exp_dir}")
                continue

            # 读取指标文件
            metrics_file = exp_path / "metrics_summary.json"
            if metrics_file.exists():
                with open(metrics_file, 'r') as f:
                    metrics = json.load(f)
                    comparison["experiments"].append({
                        "name": exp_path.name,
                        "metrics": metrics
                    })

        # 计算每个指标的最佳实验
        for tag in metric_tags:
            best_exp = None
            best_value = None

            for exp in comparison["experiments"]:
                if tag in exp["metrics"]:
                    value = exp["metrics"][tag].get("latest", 0)

                    if best_value is None or value > best_value:
                        best_value = value
                        best_exp = exp["name"]

            comparison["metrics"][tag] = {
                "best_experiment": best_exp,
                "best_value": best_value
            }

        return comparison

    def close(self):
        """关闭监控器"""
        if self._closed:
            return
        self._safe_close_writer()
        self._closed = True

        # 保存最终指标
        summary = self.get_metrics_summary()
        summary_file = self.experiment_dir / "metrics_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)

        logger.info(f"✅ 监控器已关闭，指标已保存")

    def _safe_close_writer(self):
        """安全关闭writer，避免线程异常"""
        if self.tensorboard_enabled and self.writer:
            try:
                self.writer.flush()
                self.writer.close()
                logger.info("✅ TensorBoard writer已关闭")
            except Exception as e:
                logger.warning(f"⚠️ 关闭TensorBoard writer失败: {e}")

    def __del__(self):
        """析构时尽量关闭writer，避免后台线程异常"""
        try:
            self.close()
        except Exception:
            # 避免析构过程中抛异常
            pass


class MetricsAnalyzer:
    """
    指标分析器

    分析训练指标并提供洞察
    """

    def __init__(self, metrics_history: Dict[str, List[Tuple[int, float]]]):
        """
        初始化分析器

        Args:
            metrics_history: 指标历史
        """
        self.metrics = metrics_history

    def detect_convergence(self,
                          metric_tag: str,
                          window: int = 10,
                          threshold: float = 0.01) -> Tuple[bool, int]:
        """
        检测指标是否收敛

        Args:
            metric_tag: 指标标签
            window: 滑动窗口大小
            threshold: 收敛阈值（方差）

        Returns:
            (是否收敛, 收敛步数)
        """
        if metric_tag not in self.metrics:
            return False, -1

        steps, values = zip(*self.metrics[metric_tag])

        # 滑动窗口检测
        for i in range(window, len(values)):
            window_values = values[i-window:i]
            variance = np.var(window_values)

            if variance < threshold:
                return True, steps[i]

        return False, -1

    def detect_plateau(self,
                      metric_tag: str,
                      window: int = 20,
                      threshold: float = 0.001) -> Tuple[bool, int]:
        """
        检测指标是否进入平台期

        Args:
            metric_tag: 指标标签
            window: 滑动窗口大小
            threshold: 平台期阈值（平均变化率）

        Returns:
            (是否平台期, 开始步数)
        """
        if metric_tag not in self.metrics:
            return False, -1

        steps, values = zip(*self.metrics[metric_tag])

        # 计算变化率
        for i in range(window, len(values)):
            recent_values = values[i-window:i]
            avg_change = np.mean(np.diff(recent_values))

            if abs(avg_change) < threshold:
                return True, steps[i-window]

        return False, -1

    def analyze_learning_curve(self, metric_tag: str) -> Dict[str, Any]:
        """
        分析学习曲线

        Args:
            metric_tag: 指标标签

        Returns:
            分析结果
        """
        if metric_tag not in self.metrics:
            return {}

        steps, values = zip(*self.metrics[metric_tag])

        # 拟合学习曲线（指数饱和模型）
        def model(x, a, b, c):
            return a * (1 - np.exp(-b * x)) + c

        try:
            from scipy.optimize import curve_fit

            # 归一化步数
            x_normalized = np.array(steps) / max(steps)
            y = np.array(values)

            # 初始参数猜测
            p0 = [max(y) - min(y), 1.0, min(y)]

            # 拟合
            popt, _ = curve_fit(model, x_normalized, y, p0=p0, maxfev=5000)

            # 计算拟合质量
            y_pred = model(x_normalized, *popt)
            r_squared = 1 - np.sum((y - y_pred)**2) / np.sum((y - np.mean(y))**2)

            # 预测渐近值
            asymptote = popt[0] + popt[2]

            return {
                "convergence_value": float(asymptote),
                "current_value": float(values[-1]),
                "progress_to_convergence": float(values[-1] / asymptote) if asymptote != 0 else 0,
                "r_squared": float(r_squared),
                "fit_params": {
                    "amplitude": float(popt[0]),
                    "rate": float(popt[1]),
                    "offset": float(popt[2])
                }
            }

        except (ImportError, RuntimeError):
            # scipy不可用或拟合失败，返回简单统计
            return {
                "current_value": float(values[-1]),
                "mean": float(np.mean(values)),
                "std": float(np.std(values)),
                "trend": "increasing" if values[-1] > values[0] else "decreasing"
            }


def main():
    """测试监控器"""
    monitor = TrainingMonitor(experiment_name="test_monitor")

    print(f"✅ 监控器已创建")
    print(f"   TensorBoard: {'✅ 启用' if monitor.tensorboard_enabled else '❌ 禁用'}")

    # 模拟训练过程
    for episode in range(100):
        reward = 0.5 + 0.3 * (1 - np.exp(-episode / 50)) + np.random.normal(0, 0.02)
        actor_loss = 0.5 * np.exp(-episode / 30) + np.random.normal(0, 0.01)
        critic_loss = 0.3 * np.exp(-episode / 40) + np.random.normal(0, 0.01)

        monitor.log_training_step(
            episode=episode,
            reward=reward,
            actor_loss=actor_loss,
            critic_loss=critic_loss
        )

    # 保存指标
    monitor.save_metrics_to_json()

    # 绘制曲线
    monitor.plot_metrics()

    # 获取汇总
    summary = monitor.get_metrics_summary()
    print(f"\n📊 训练汇总:")
    print(f"   最终奖励: {summary['train/reward']['latest']:.4f}")
    print(f"   奖励改善: {summary['train/reward']['improvement']:.4f}")
    print(f"   最终Actor损失: {summary['train/actor_loss']['latest']:.4f}")

    # 分析学习曲线
    analyzer = MetricsAnalyzer(monitor.metrics_history)
    curve_analysis = analyzer.analyze_learning_curve("train/reward")
    print(f"\n📈 学习曲线分析:")
    print(f"   收敛值预测: {curve_analysis.get('convergence_value', 0):.4f}")
    print(f"   当前进度: {curve_analysis.get('progress_to_convergence', 0)*100:.1f}%")

    monitor.close()


if __name__ == "__main__":
    main()
