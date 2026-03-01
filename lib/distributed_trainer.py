#!/usr/bin/env python3
"""
分布式训练支持 - Redis + Celery

实现多项目并行训练功能：
- Redis作为消息队列和状态存储
- Celery进行分布式任务调度
- 支持多worker并行训练
- 智能检测依赖（不可用时降级到单机模式）

Phase 3.1 - 预计200行
"""

import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import json
from datetime import datetime
import logging

# 尝试导入Redis和Celery
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

try:
    from celery import Celery, current_task
    from celery.result import AsyncResult
    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False
    Celery = None
    current_task = None
    AsyncResult = None

from .trainer import RLTrainer
from .environment import InteractionEnvironment


logger = logging.getLogger(__name__)


class DistributedTrainingConfig:
    """分布式训练配置"""

    def __init__(self,
                 redis_host: str = "localhost",
                 redis_port: int = 6379,
                 redis_db: int = 0,
                 broker_url: str = None,
                 result_backend: str = None,
                 require_worker: bool = True,
                 connection_timeout: float = 1.0):
        """
        初始化配置

        Args:
            redis_host: Redis主机
            redis_port: Redis端口
            redis_db: Redis数据库
            broker_url: Celery broker URL
            result_backend: Celery结果后端URL
            require_worker: 是否要求至少一个Celery worker在线
            connection_timeout: 连接探测超时时间（秒）
        """
        self.redis_host = redis_host
        self.redis_port = redis_port
        self.redis_db = redis_db
        self.require_worker = require_worker
        self.connection_timeout = connection_timeout

        # 默认使用Redis作为broker和backend
        self.broker_url = broker_url or f"redis://{redis_host}:{redis_port}/{redis_db}"
        self.result_backend = result_backend or f"redis://{redis_host}:{redis_port}/{redis_db}"

        # 检查可用性
        self.redis_available = REDIS_AVAILABLE
        self.celery_available = CELERY_AVAILABLE


class DistributedTrainer:
    """
    分布式训练器

    功能：
    - 多项目并行训练
    - 任务状态跟踪
    - 训练结果聚合
    - 智能降级（依赖不可用时使用单机模式）
    """

    def __init__(self, config: DistributedTrainingConfig = None,
                 model_dir: str = None):
        """
        初始化分布式训练器

        Args:
            config: 分布式配置
            model_dir: 模型保存目录
        """
        self.config = config or DistributedTrainingConfig()
        self.model_dir = Path(model_dir).expanduser() if model_dir else Path("./models/distributed")
        self.model_dir.mkdir(parents=True, exist_ok=True)

        # 检查分布式功能是否可用
        self.distributed_enabled = (
            self.config.redis_available and
            self.config.celery_available
        )

        if self.distributed_enabled and not self._distributed_runtime_ready():
            logger.warning("⚠️ 未检测到可用的分布式运行时，降级到单机模式")
            self.distributed_enabled = False

        if self.distributed_enabled:
            logger.info("✅ 分布式训练已启用（Redis + Celery）")
            self._initialize_distributed()
        else:
            logger.warning("⚠️ 分布式模式不可用，降级到单机模式")
            self._initialize_fallback()

        # 训练任务记录
        self.training_tasks: Dict[str, Dict[str, Any]] = {}

    def _distributed_runtime_ready(self) -> bool:
        """检查分布式运行时是否可用（Redis连通 + 可选worker在线）"""
        try:
            redis_client = redis.Redis(
                host=self.config.redis_host,
                port=self.config.redis_port,
                db=self.config.redis_db,
                decode_responses=True,
                socket_connect_timeout=self.config.connection_timeout,
                socket_timeout=self.config.connection_timeout,
            )
            redis_client.ping()
        except Exception as exc:
            logger.warning(f"⚠️ Redis连接不可用: {exc}")
            return False

        if not self.config.require_worker:
            return True

        try:
            probe_app = Celery(
                'openclaw_alignment_probe',
                broker=self.config.broker_url,
                backend=self.config.result_backend
            )
            replies = probe_app.control.ping(timeout=self.config.connection_timeout)
            if not replies:
                logger.warning("⚠️ 未检测到在线Celery worker")
                return False
        except Exception as exc:
            logger.warning(f"⚠️ Celery worker探测失败: {exc}")
            return False

        return True

    def _initialize_distributed(self):
        """初始化分布式组件"""
        # 初始化Redis连接
        self.redis_client = redis.Redis(
            host=self.config.redis_host,
            port=self.config.redis_port,
            db=self.config.redis_db,
            decode_responses=True,
            socket_connect_timeout=self.config.connection_timeout,
            socket_timeout=self.config.connection_timeout,
        )

        # 初始化Celery应用
        self.celery_app = Celery(
            'openclaw_alignment',
            broker=self.config.broker_url,
            backend=self.config.result_backend
        )

        # 配置Celery
        self.celery_app.conf.update(
            task_serializer='json',
            accept_content=['json'],
            result_serializer='json',
            timezone='UTC',
            enable_utc=True,
        )

        # 注册训练任务
        self.celery_app.task(self._train_task, name='train_episode')

    def _initialize_fallback(self):
        """初始化降级模式（单机）"""
        self.local_trainer = RLTrainer(model_dir=str(self.model_dir))

    def train_distributed(self,
                        project_configs: List[Dict[str, Any]],
                        num_episodes_per_project: int = 100,
                        save_interval: int = 10) -> Dict[str, Any]:
        """
        分布式训练多个项目

        Args:
            project_configs: 项目配置列表（每个项目独立训练）
                [{"project_id": "proj1", "task_types": ["T1", "T2"]}, ...]
            num_episodes_per_project: 每个项目训练episode数
            save_interval: 保存间隔

        Returns:
            训练统计汇总
        """
        logger.info(f"🚀 开始分布式训练（{len(project_configs)} 个项目）...")

        if not self.distributed_enabled:
            # 降级到单机顺序训练
            return self._train_sequential(project_configs, num_episodes_per_project)

        # 并行训练
        task_ids = []
        try:
            for config in project_configs:
                project_id = config.get("project_id", f"project_{len(task_ids)}")

                # 提交异步任务
                result = self.celery_app.send_task(
                    'train_episode',
                    args=[config, num_episodes_per_project, save_interval],
                    kwargs={}
                )

                task_ids.append({
                    "project_id": project_id,
                    "task_id": result.id
                })

                # 记录任务
                self.training_tasks[project_id] = {
                    "task_id": result.id,
                    "status": "PENDING",
                    "config": config,
                    "started_at": datetime.now().isoformat()
                }
        except Exception as exc:
            logger.error(f"❌ 分布式任务提交失败，降级到单机模式: {exc}")
            return self._train_sequential(project_configs, num_episodes_per_project)

        # 等待所有任务完成
        results = self._wait_for_tasks(task_ids)

        # 聚合结果
        return self._aggregate_results(results)

    def _train_sequential(self,
                         project_configs: List[Dict[str, Any]],
                         num_episodes_per_project: int) -> Dict[str, Any]:
        """
        顺序训练（降级模式）

        Args:
            project_configs: 项目配置列表
            num_episodes_per_project: 每个项目训练episode数

        Returns:
            训练统计汇总
        """
        logger.info("⚠️ 使用单机顺序训练模式")

        all_results = []

        for config in project_configs:
            project_id = config.get("project_id", "unknown")

            logger.info(f"🔄 训练项目: {project_id}")

            # 创建独立训练器
            trainer = RLTrainer(model_dir=str(self.model_dir / project_id))

            # 训练
            stats = trainer.train(
                num_episodes=num_episodes_per_project,
                max_steps_per_episode=100,
                save_interval=10
            )

            all_results.append({
                "project_id": project_id,
                "stats": stats
            })

        return self._aggregate_results(all_results)

    def _train_task(self,
                   project_config: Dict[str, Any],
                   num_episodes: int,
                   save_interval: int) -> Dict[str, Any]:
        """
        Celery训练任务（在worker上执行）

        Args:
            project_config: 项目配置
            num_episodes: 训练episode数
            save_interval: 保存间隔

        Returns:
            训练统计
        """
        project_id = project_config.get("project_id", "unknown")

        # 更新任务状态
        if CELERY_AVAILABLE and current_task:
            current_task.update_state(
                state='PROGRESS',
                meta={'project_id': project_id, 'progress': 0}
            )

        # 创建训练器
        model_dir = Path("./models/distributed") / project_id
        model_dir.mkdir(parents=True, exist_ok=True)

        trainer = RLTrainer(model_dir=str(model_dir))

        # 训练
        stats = trainer.train(
            num_episodes=num_episodes,
            max_steps_per_episode=100,
            save_interval=save_interval
        )

        return {
            "project_id": project_id,
            "stats": stats
        }

    def _wait_for_tasks(self,
                       task_ids: List[Dict[str, str]],
                       timeout: int = 3600) -> List[Dict[str, Any]]:
        """
        等待所有任务完成

        Args:
            task_ids: 任务ID列表
            timeout: 超时时间（秒）

        Returns:
            任务结果列表
        """
        import time
        start_time = time.time()

        results = []
        completed_count = 0

        while completed_count < len(task_ids):
            # 检查超时
            if time.time() - start_time > timeout:
                logger.error(f"❌ 训练超时（{timeout}秒）")
                break

            # 检查每个任务状态
            for task_info in task_ids:
                project_id = task_info["project_id"]
                task_id = task_info["task_id"]

                if project_id in [r["project_id"] for r in results]:
                    continue  # 已完成

                # 查询任务状态
                result = AsyncResult(task_id, app=self.celery_app)

                if result.ready():
                    # 任务完成
                    task_result = result.get()
                    results.append(task_result)

                    # 更新记录
                    self.training_tasks[project_id]["status"] = "COMPLETED"
                    self.training_tasks[project_id]["completed_at"] = datetime.now().isoformat()

                    completed_count += 1
                    logger.info(f"✅ 项目 {project_id} 完成（{completed_count}/{len(task_ids)}）")

                elif result.status == 'FAILED':
                    # 任务失败
                    logger.error(f"❌ 项目 {project_id} 训练失败: {result.info}")

                    self.training_tasks[project_id]["status"] = "FAILED"
                    self.training_tasks[project_id]["error"] = str(result.info)

                    completed_count += 1

            # 等待一段时间再检查
            time.sleep(5)

        return results

    def _aggregate_results(self,
                          results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        聚合训练结果

        Args:
            results: 训练结果列表

        Returns:
            聚合统计
        """
        if not results:
            return {}

        # 聚合指标
        total_rewards = [r["stats"].get("average_reward", 0) for r in results]
        total_episodes = sum(r["stats"].get("total_episodes", 0) for r in results)

        return {
            "total_projects": len(results),
            "total_episodes": total_episodes,
            "average_reward_per_project": {
                r["project_id"]: r["stats"].get("average_reward", 0)
                for r in results
            },
            "overall_average_reward": float(np.mean(total_rewards)),
            "reward_std": float(np.std(total_rewards)),
            "best_project": max(results, key=lambda x: x["stats"].get("average_reward", 0))["project_id"],
            "training_tasks": self.training_tasks
        }

    def get_task_status(self, project_id: str) -> Optional[Dict[str, Any]]:
        """
        获取任务状态

        Args:
            project_id: 项目ID

        Returns:
            任务状态信息
        """
        return self.training_tasks.get(project_id)

    def get_all_statuses(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有任务状态

        Returns:
            所有任务状态
        """
        return self.training_tasks

    def cancel_task(self, project_id: str) -> bool:
        """
        取消任务

        Args:
            project_id: 项目ID

        Returns:
            是否成功取消
        """
        if not self.distributed_enabled:
            logger.warning("⚠️ 单机模式不支持取消任务")
            return False

        task_info = self.training_tasks.get(project_id)
        if not task_info:
            logger.warning(f"⚠️ 任务不存在: {project_id}")
            return False

        task_id = task_info["task_id"]

        # 撤销Celery任务
        self.celery_app.control.revoke(task_id, terminate=True)

        # 更新状态
        self.training_tasks[project_id]["status"] = "CANCELLED"
        self.training_tasks[project_id]["cancelled_at"] = datetime.now().isoformat()

        logger.info(f"✅ 任务已取消: {project_id}")
        return True

    def save_training_report(self, results: Dict[str, Any], filename: str = None) -> str:
        """
        保存训练报告

        Args:
            results: 训练结果
            filename: 文件名

        Returns:
            报告文件路径
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"distributed_training_report_{timestamp}.json"

        report_path = self.model_dir / filename

        with open(report_path, 'w') as f:
            json.dump(results, f, indent=2)

        logger.info(f"✅ 训练报告已保存: {report_path}")
        return str(report_path)


def main():
    """测试分布式训练器"""
    config = DistributedTrainingConfig()
    trainer = DistributedTrainer(config)

    print(f"✅ 分布式训练器已创建")
    print(f"   分布式功能: {'✅ 启用' if trainer.distributed_enabled else '❌ 禁用（降级）'}")

    # 测试项目配置
    project_configs = [
        {"project_id": "test_project_1", "task_types": ["T1", "T2"]},
        {"project_id": "test_project_2", "task_types": ["T3", "T4"]},
    ]

    # 训练（少量episode测试）
    results = trainer.train_distributed(
        project_configs=project_configs,
        num_episodes_per_project=3,
        save_interval=1
    )

    print(f"\n📊 分布式训练结果:")
    print(f"   总项目数: {results.get('total_projects', 0)}")
    print(f"   总episode数: {results.get('total_episodes', 0)}")
    print(f"   平均奖励: {results.get('overall_average_reward', 0):.3f}")

    # 保存报告
    report_path = trainer.save_training_report(results)
    print(f"   训练报告: {report_path}")


if __name__ == "__main__":
    main()
