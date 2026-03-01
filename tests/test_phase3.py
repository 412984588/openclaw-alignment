#!/usr/bin/env python3
"""
Phase 3高级功能测试

测试分布式训练、自动调参、监控面板和性能优化
"""

import pytest
import numpy as np
from pathlib import Path
import tempfile
import shutil


class TestDistributedTrainer:
    """分布式训练器测试"""

    def test_initialization(self):
        """测试初始化"""
        from lib.distributed_trainer import DistributedTrainer, DistributedTrainingConfig

        config = DistributedTrainingConfig()
        trainer = DistributedTrainer(config)

        assert trainer is not None
        assert trainer.config is not None

    def test_fallback_mode(self):
        """测试降级模式"""
        from lib.distributed_trainer import DistributedTrainer, DistributedTrainingConfig

        config = DistributedTrainingConfig()
        trainer = DistributedTrainer(config)

        # 分布式功能应该检测到依赖
        assert hasattr(trainer, 'distributed_enabled')

        # 应该有本地训练器作为降级
        assert hasattr(trainer, 'local_trainer') or trainer.distributed_enabled

    def test_train_sequential(self):
        """测试顺序训练（降级模式）"""
        from lib.distributed_trainer import DistributedTrainer, DistributedTrainingConfig

        config = DistributedTrainingConfig()
        trainer = DistributedTrainer(config)

        project_configs = [
            {"project_id": "test_proj_1", "task_types": ["T1"]},
        ]

        # 训练1个episode
        results = trainer.train_distributed(
            project_configs=project_configs,
            num_episodes_per_project=1,
            save_interval=1
        )

        assert results is not None
        assert "total_projects" in results
        assert results["total_projects"] == 1

    def test_fallback_when_runtime_unreachable(self):
        """测试依赖存在但分布式运行时不可达时自动降级"""
        from lib.distributed_trainer import (
            DistributedTrainer,
            DistributedTrainingConfig,
            REDIS_AVAILABLE,
            CELERY_AVAILABLE,
        )

        if not (REDIS_AVAILABLE and CELERY_AVAILABLE):
            pytest.skip("Redis/Celery not installed in this environment")

        config = DistributedTrainingConfig(
            redis_host="127.0.0.1",
            redis_port=1,  # deliberately unreachable
            require_worker=True,
            connection_timeout=0.2,
        )
        trainer = DistributedTrainer(config)
        assert trainer.distributed_enabled is False


class TestHyperparameterTuner:
    """超参数调优器测试"""

    def test_scheduler_creation(self):
        """测试调度器创建"""
        from lib.hyperparameter_tuner import LearningRateScheduler

        scheduler = LearningRateScheduler(
            initial_lr=0.001,
            scheduler_type="exponential"
        )

        assert scheduler is not None
        assert scheduler.initial_lr == 0.001

    def test_lr_schedule(self):
        """测试学习率调度"""
        from lib.hyperparameter_tuner import LearningRateScheduler

        scheduler = LearningRateScheduler(
            initial_lr=0.001,
            scheduler_type="exponential",
            decay_rate=0.96,
            decay_steps=100
        )

        # 测试前10步的学习率
        lrs = [scheduler.get_lr(i) for i in range(10)]

        # 学习率应该逐渐下降
        assert lrs[0] == 0.001  # 初始学习率
        assert lrs[-1] < lrs[0]  # 应该下降

    def test_cosine_schedule(self):
        """测试余弦退火调度"""
        from lib.hyperparameter_tuner import LearningRateScheduler

        scheduler = LearningRateScheduler(
            initial_lr=0.001,
            scheduler_type="cosine",
            decay_steps=100
        )

        lr = scheduler.get_lr(50)
        assert lr > 0
        assert lr <= 0.001

    def test_hyperparameter_search(self):
        """测试超参数搜索"""
        from lib.hyperparameter_tuner import HyperparameterSearch

        search_space = {
            "learning_rate": (0.0001, 0.01),
            "batch_size": [32, 64, 128]
        }

        search = HyperparameterSearch(search_space, search_type="random", n_trials=5)

        # 测试建议配置
        config1 = search.suggest(0)
        config2 = search.suggest(1)

        assert config1 is not None
        assert config2 is not None
        assert "learning_rate" in config1
        assert "batch_size" in config1

        # 两个配置应该不同（随机）
        assert config1 != config2

    def test_record_trial(self):
        """测试记录试验"""
        from lib.hyperparameter_tuner import HyperparameterSearch

        search_space = {
            "learning_rate": (0.0001, 0.01)
        }

        search = HyperparameterSearch(search_space, n_trials=5)

        # 记录试验
        config = search.suggest(0)
        search.record_trial(config, score=0.85)

        assert len(search.trials) == 1
        assert search.best_trial is not None
        assert search.best_trial["score"] == 0.85

    def test_early_stopping(self):
        """测试早停机制"""
        from lib.hyperparameter_tuner import EarlyStopping

        early_stop = EarlyStopping(patience=3, min_delta=0.01)

        # 前几次评分改善
        assert not early_stop.check(0.5)
        assert not early_stop.check(0.55)
        assert not early_stop.check(0.60)

        # 后续评分不再改善
        assert not early_stop.check(0.60)  # counter=1
        assert not early_stop.check(0.60)  # counter=2
        assert early_stop.check(0.60)  # counter=3 -> 早停


class TestMonitoring:
    """监控面板测试"""

    def test_monitor_creation(self):
        """测试监控器创建"""
        from lib.monitoring import TrainingMonitor

        with tempfile.TemporaryDirectory() as tmpdir:
            monitor = TrainingMonitor(log_dir=tmpdir, experiment_name="test")

            assert monitor is not None
            assert monitor.experiment_dir.exists()
            monitor.close()

    def test_log_scalar(self):
        """测试记录标量"""
        from lib.monitoring import TrainingMonitor

        with tempfile.TemporaryDirectory() as tmpdir:
            monitor = TrainingMonitor(log_dir=tmpdir)

            monitor.log_scalar("test/metric", 0.5, step=0)
            monitor.log_scalar("test/metric", 0.6, step=1)

            assert "test/metric" in monitor.metrics_history
            assert len(monitor.metrics_history["test/metric"]) == 2
            monitor.close()

    def test_log_training_step(self):
        """测试记录训练步骤"""
        from lib.monitoring import TrainingMonitor

        with tempfile.TemporaryDirectory() as tmpdir:
            monitor = TrainingMonitor(log_dir=tmpdir)

            monitor.log_training_step(
                episode=0,
                reward=0.75,
                actor_loss=0.1,
                critic_loss=0.2
            )

            assert "train/reward" in monitor.metrics_history
            assert monitor.metrics_history["train/reward"][0][1] == 0.75
            monitor.close()

    def test_metrics_summary(self):
        """测试指标汇总"""
        from lib.monitoring import TrainingMonitor

        with tempfile.TemporaryDirectory() as tmpdir:
            monitor = TrainingMonitor(log_dir=tmpdir)

            # 记录一些指标
            for i in range(10):
                monitor.log_scalar("test/value", i * 0.1, step=i)

            summary = monitor.get_metrics_summary()

            assert "test/value" in summary
            assert summary["test/value"]["count"] == 10
            assert summary["test/value"]["mean"] > 0
            monitor.close()

    def test_save_metrics(self):
        """测试保存指标"""
        from lib.monitoring import TrainingMonitor
        import json

        with tempfile.TemporaryDirectory() as tmpdir:
            monitor = TrainingMonitor(log_dir=tmpdir)

            monitor.log_scalar("test/metric", 0.5, step=0)

            filepath = monitor.save_metrics_to_json("test_metrics.json")

            assert Path(filepath).exists()

            # 验证内容
            with open(filepath, 'r') as f:
                data = json.load(f)

            assert "test/metric" in data
            monitor.close()


class TestPerformanceOptimizer:
    """性能优化器测试"""

    def test_quantization(self):
        """测试模型量化"""
        from lib.performance_optimizer import ModelQuantization

        quantizer = ModelQuantization()

        # 创建测试权重
        weights = np.random.randn(128, 64).astype(np.float32)

        # 量化
        quantized, params = quantizer.quantize_weights(weights, bits=8)

        assert quantized.dtype == np.int8
        assert "scale" in params
        assert "zero_point" in params

        # 反量化
        dequantized = quantizer.dequantize_weights(quantized, params)

        # 验证误差较小
        error = np.mean(np.abs(weights - dequantized))
        assert error < 0.1  # 误差应该小于0.1

    def test_inference_cache(self):
        """测试推理缓存"""
        from lib.performance_optimizer import InferenceCache

        # 创建模拟模型
        class DummyModel:
            def forward(self, state):
                return float(np.sum(state))

        model = DummyModel()
        cache = InferenceCache(model, cache_size=100)

        # 第一次调用（缓存未命中）
        state = np.array([1.0, 2.0, 3.0])
        result1 = cache.predict(state)

        # 第二次调用相同状态（缓存命中）
        result2 = cache.predict(state)

        assert result1 == result2

        # 检查缓存统计（使用LRU缓存的cache_info）
        stats = cache.get_cache_stats()
        # 第一次调用：miss（建立缓存），第二次调用：hit
        # 但由于第一次在建立缓存时也算miss，所以应该是1 miss, 1 hit
        assert stats["cache_misses"] >= 1  # 至少一次miss
        assert stats["cache_hits"] >= 1  # 至少一次hit
        assert stats["total_requests"] == 2

    def test_cache_stats(self):
        """测试缓存统计"""
        from lib.performance_optimizer import InferenceCache

        class DummyModel:
            def forward(self, state):
                return float(np.sum(state))

        model = DummyModel()
        cache = InferenceCache(model, cache_size=100)

        # 多次预测
        state = np.array([1.0, 2.0, 3.0])
        for _ in range(5):
            cache.predict(state)

        stats = cache.get_cache_stats()

        assert stats["total_requests"] == 5
        assert stats["hit_rate"] > 0  # 应该有缓存命中

    def test_batch_inference(self):
        """测试批量推理"""
        from lib.performance_optimizer import BatchInference

        class DummyModel:
            def forward(self, state):
                return float(np.random.random())

        model = DummyModel()
        batch_infer = BatchInference(model, batch_size=5)

        # 添加2个请求（小于batch_size）
        for _ in range(2):
            state = np.random.randn(10)
            request_id = batch_infer.predict(state, sync=False)
            assert isinstance(request_id, int)

        # 队列应该有2个请求
        assert batch_infer.get_queue_size() == 2

        # 刷新批量
        results = batch_infer.flush()
        assert len(results) == 2
        assert all(isinstance(item, tuple) and len(item) == 2 for item in results)

        # 队列应该为空
        assert batch_infer.get_queue_size() == 0

        # 测试自动批量触发
        for _ in range(5):
            state = np.random.randn(10)
            batch_infer.predict(state, sync=False)

        # 队列应该为空（自动触发批量推理后清空）
        assert batch_infer.get_queue_size() == 0


class TestIntegration:
    """集成测试"""

    def test_phase3_integration(self):
        """测试Phase 3集成"""
        from lib.distributed_trainer import DistributedTrainer
        from lib.hyperparameter_tuner import HyperparameterTuner
        from lib.monitoring import TrainingMonitor
        from lib.performance_optimizer import PerformanceOptimizer

        # 所有模块应该可以导入
        assert DistributedTrainer is not None
        assert HyperparameterTuner is not None
        assert TrainingMonitor is not None
        assert PerformanceOptimizer is not None

    def test_full_pipeline(self):
        """测试完整流程"""
        from lib.monitoring import TrainingMonitor
        from lib.hyperparameter_tuner import LearningRateScheduler

        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建监控器
            monitor = TrainingMonitor(log_dir=tmpdir, experiment_name="full_pipeline")

            # 创建学习率调度器
            scheduler = LearningRateScheduler(initial_lr=0.001, scheduler_type="exponential")

            # 模拟训练循环
            for episode in range(10):
                lr = scheduler.get_lr()
                reward = 0.5 + 0.1 * (episode / 10)

                monitor.log_training_step(
                    episode=episode,
                    reward=reward,
                    actor_loss=0.1 / (episode + 1),
                    critic_loss=0.05 / (episode + 1)
                )

            # 验证记录
            summary = monitor.get_metrics_summary()
            assert "train/reward" in summary
            assert summary["train/reward"]["count"] == 10
            monitor.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
