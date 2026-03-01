#!/usr/bin/env python3
"""
性能优化器 - 批量推理与模型量化

实现推理性能优化：
- 批量推理（Batch Inference）
- 模型量化（Quantization）
- 缓存机制（Memoization）
- JIT编译（可选）

Phase 3.4 - 预计150行
"""

import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Callable
from pathlib import Path
import json
from datetime import datetime
import logging
from functools import lru_cache

logger = logging.getLogger(__name__)

# 尝试导入JIT编译
try:
    import numba
    from numba import jit, njit
    NUMBA_AVAILABLE = True
except ImportError:
    NUMBA_AVAILABLE = False
    jit = None
    njit = None


class BatchInference:
    """
    批量推理器

    将多个推理请求合并为批量处理，提升吞吐量
    """

    def __init__(self,
                 model: Any,
                 batch_size: int = 32,
                 timeout_ms: int = 10):
        """
        初始化批量推理器

        Args:
            model: 模型（policy_net或value_net）
            batch_size: 批量大小
            timeout_ms: 批量超时（毫秒）
        """
        self.model = model
        self.batch_size = batch_size
        self.timeout_ms = timeout_ms

        self.pending_requests: List[Dict[str, Any]] = []
        self.request_counter = 0
        self.last_batch_results: List[Tuple[int, float]] = []

    def predict(self, state: np.ndarray, sync: bool = True) -> float:
        """
        预测（支持批量）

        Args:
            state: 输入状态
            sync: 是否同步（不等待批量）

        Returns:
            预测结果
        """
        if sync:
            # 同步模式：直接推理
            return self._infer_single(state)

        # 异步模式：加入批量队列
        request_id = self._add_request(state)

        # 如果队列满，执行批量推理
        if len(self.pending_requests) >= self.batch_size:
            self.last_batch_results = self._flush_batch()

        return request_id

    def _add_request(self, state: np.ndarray) -> int:
        """添加请求到队列"""
        request_id = self.request_counter
        self.request_counter += 1

        request = {
            "id": request_id,
            "state": state,
            "result": None
        }

        self.pending_requests.append(request)

        return request_id

    def _infer_single(self, state: np.ndarray) -> float:
        """单个推理"""
        if hasattr(self.model, 'forward'):
            return self.model.forward(state)
        elif hasattr(self.model, 'get_action_probs'):
            probs = self.model.get_action_probs(state)
            return float(np.argmax(probs))
        else:
            raise ValueError(f"未知的模型类型: {type(self.model)}")

    def _infer_batch(self, states: np.ndarray) -> np.ndarray:
        """批量推理"""
        results = []

        for state in states:
            result = self._infer_single(state)
            results.append(result)

        return np.array(results)

    def _flush_batch(self) -> List[Tuple[int, float]]:
        """执行批量推理"""
        if not self.pending_requests:
            return []

        # 提取所有状态
        states = np.array([req["state"] for req in self.pending_requests])

        # 批量推理
        results = self._infer_batch(states)

        # 更新请求结果
        for i, req in enumerate(self.pending_requests):
            req["result"] = results[i]

        # 返回结果
        output = [(req["id"], req["result"]) for req in self.pending_requests]

        # 清空队列
        self.pending_requests = []

        return output

    def flush(self) -> List[Tuple[int, float]]:
        """手动刷新队列"""
        return self._flush_batch()

    def get_queue_size(self) -> int:
        """获取队列大小"""
        return len(self.pending_requests)


class ModelQuantization:
    """
    模型量化

    将模型权重从float32转换为int8，减少模型大小和提升推理速度
    """

    @staticmethod
    def quantize_weights(weights: np.ndarray,
                        bits: int = 8) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        量化权重

        Args:
            weights: 原始权重（float32）
            bits: 量化位数（8或16）

        Returns:
            (量化后权重, 量化参数)
        """
        if bits == 8:
            # INT8量化
            qmin, qmax = -128, 127
            dtype = np.int8
        elif bits == 16:
            # INT16量化
            qmin, qmax = -32768, 32767
            dtype = np.int16
        else:
            raise ValueError(f"不支持的量化位数: {bits}")

        # 计算缩放因子和零点
        wmin, wmax = weights.min(), weights.max()
        scale = (wmax - wmin) / (qmax - qmin)
        zero_point = qmin - wmin / scale

        # 量化
        quantized = np.clip(
            np.round(weights / scale + zero_point),
            qmin, qmax
        ).astype(dtype)

        # 量化参数
        params = {
            "scale": float(scale),
            "zero_point": int(zero_point),
            "qmin": qmin,
            "qmax": qmax,
            "bits": bits
        }

        return quantized, params

    @staticmethod
    def dequantize_weights(quantized: np.ndarray,
                          params: Dict[str, Any]) -> np.ndarray:
        """
        反量化权重

        Args:
            quantized: 量化后权重
            params: 量化参数

        Returns:
            反量化后的权重（float32）
        """
        scale = params["scale"]
        zero_point = params["zero_point"]

        return (quantized.astype(np.float32) - zero_point) * scale

    def quantize_model(self, model: Any) -> Dict[str, Any]:
        """
        量化整个模型

        Args:
            model: 模型（需要有权重矩阵）

        Returns:
            量化后的模型和参数
        """
        quantized_model = {}
        quantization_params = {}

        # 提取模型权重（假设有get_weights方法）
        if hasattr(model, 'get_weights'):
            weights = model.get_weights()

            for layer_name, weight_matrix in weights.items():
                q_weight, q_params = self.quantize_weights(weight_matrix, bits=8)

                quantized_model[layer_name] = q_weight
                quantization_params[layer_name] = q_params
        else:
            logger.warning("⚠️ 模型不支持get_weights方法，无法量化")
            return {"original_model": model}

        return {
            "quantized_model": quantized_model,
            "quantization_params": quantization_params,
            "original_model": model
        }

    def estimate_size_reduction(self,
                               original_model: Any,
                               quantized_model: Dict[str, Any]) -> Dict[str, float]:
        """
        估算模型大小减少

        Args:
            original_model: 原始模型
            quantized_model: 量化后模型

        Returns:
            大小对比统计
        """
        # 计算原始大小（假设float32）
        original_size = 0
        if hasattr(original_model, 'get_weights'):
            weights = original_model.get_weights()
            for weight_matrix in weights.values():
                original_size += weight_matrix.nbytes

        # 计算量化后大小（int8）
        quantized_size = 0
        for q_weight in quantized_model["quantized_model"].values():
            quantized_size += q_weight.nbytes

        reduction_ratio = quantized_size / original_size
        size_saved = original_size - quantized_size

        return {
            "original_size_mb": original_size / (1024 * 1024),
            "quantized_size_mb": quantized_size / (1024 * 1024),
            "size_saved_mb": size_saved / (1024 * 1024),
            "reduction_ratio": reduction_ratio,
            "compression_rate": (1 - reduction_ratio) * 100
        }


class InferenceCache:
    """
    推理缓存

    缓存常见状态的结果，避免重复计算
    """

    def __init__(self,
                 model: Any,
                 cache_size: int = 10000):
        """
        初始化缓存

        Args:
            model: 模型
            cache_size: 缓存大小
        """
        self.model = model
        self.cache_size = cache_size

        # 使用LRU缓存
        self._cached_predict = lru_cache(maxsize=cache_size)(self._predict_uncached)

        # 缓存统计（使用LRU缓存的内部统计）
        self.total_requests = 0

    def _predict_uncached(self, state_bytes: bytes) -> float:
        """未缓存的预测（内部方法）"""
        # 从bytes恢复状态（简化：默认float32一维向量）
        state = np.frombuffer(state_bytes, dtype=np.float32)

        if hasattr(self.model, 'forward'):
            return self.model.forward(state)
        elif hasattr(self.model, 'get_action_probs'):
            probs = self.model.get_action_probs(state)
            return float(np.argmax(probs))
        else:
            raise ValueError(f"未知的模型类型: {type(self.model)}")

    def predict(self, state: np.ndarray) -> float:
        """
        预测（带缓存）

        Args:
            state: 输入状态

        Returns:
            预测结果
        """
        self.total_requests += 1

        # 计算状态hash
        state_bytes = np.asarray(state, dtype=np.float32).tobytes()

        # 使用LRU缓存
        return self._cached_predict(state_bytes)

    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        cache_info = self._cached_predict.cache_info()

        total = cache_info.hits + cache_info.misses
        hit_rate = cache_info.hits / total if total > 0 else 0

        return {
            "cache_hits": cache_info.hits,
            "cache_misses": cache_info.misses,
            "hit_rate": hit_rate,
            "total_requests": self.total_requests,
            "cache_size": cache_info.currsize
        }

    def clear_cache(self):
        """清空缓存"""
        self._cached_predict.cache_clear()
        self.total_requests = 0


class JITOptimizer:
    """
    JIT编译优化器

    使用Numba JIT编译加速数值计算
    """

    def __init__(self):
        """初始化JIT优化器"""
        self.jit_enabled = NUMBA_AVAILABLE

        if self.jit_enabled:
            logger.info("✅ Numba JIT已启用")
        else:
            logger.warning("⚠️ Numba不可用，JIT优化禁用")

    def optimize_function(self, func: Callable) -> Callable:
        """
        优化函数

        Args:
            func: 要优化的函数

        Returns:
            优化后的函数
        """
        if not self.jit_enabled:
            return func

        # 尝试JIT编译
        try:
            optimized = njit(func)
            return optimized
        except Exception as e:
            logger.warning(f"⚠️ JIT编译失败: {e}")
            return func

    def benchmark(self,
                 func: Callable,
                 *args,
                 n_iterations: int = 100) -> Dict[str, float]:
        """
        性能基准测试

        Args:
            func: 要测试的函数
            *args: 函数参数
            n_iterations: 迭代次数

        Returns:
            性能统计
        """
        import time

        # 预热
        for _ in range(10):
            func(*args)

        # 测试
        start_time = time.time()
        for _ in range(n_iterations):
            result = func(*args)
        end_time = time.time()

        total_time = end_time - start_time
        avg_time = total_time / n_iterations

        return {
            "total_time_s": total_time,
            "avg_time_ms": avg_time * 1000,
            "throughput": n_iterations / total_time
        }


class PerformanceOptimizer:
    """
    性能优化器（集成所有优化技术）

    完整的性能优化流程：
    1. 批量推理
    2. 模型量化
    3. 推理缓存
    4. JIT编译
    """

    def __init__(self,
                 model: Any,
                 enable_batch: bool = True,
                 enable_quantization: bool = False,
                 enable_cache: bool = True,
                 enable_jit: bool = False):
        """
        初始化性能优化器

        Args:
            model: 模型
            enable_batch: 启用批量推理
            enable_quantization: 启用量化
            enable_cache: 启用缓存
            enable_jit: 启用JIT
        """
        self.model = model
        self.enable_batch = enable_batch
        self.enable_quantization = enable_quantization
        self.enable_cache = enable_cache
        self.enable_jit = enable_jit

        # 初始化优化组件
        if enable_batch:
            self.batch_inference = BatchInference(model, batch_size=32)

        if enable_quantization:
            self.quantization = ModelQuantization()
            quantized = self.quantization.quantize_model(model)
            self.quantized_model = quantized.get("quantized_model")

        if enable_cache:
            self.cache = InferenceCache(model, cache_size=10000)

        if enable_jit:
            self.jit_optimizer = JITOptimizer()

        # 性能统计
        self.optimization_stats = {
            "batch_inference": {"calls": 0, "total_batched": 0},
            "cache": self.cache.get_cache_stats() if enable_cache else {},
            "quantization": self.quantization.estimate_size_reduction(
                model, self.quantized_model
            ) if enable_quantization else {}
        }

    def predict(self, state: np.ndarray) -> float:
        """
        优化后的预测

        Args:
            state: 输入状态

        Returns:
            预测结果
        """
        # 批量推理
        if self.enable_batch:
            result = self.batch_inference.predict(state)
            self.optimization_stats["batch_inference"]["calls"] += 1
            return result

        # 缓存推理
        elif self.enable_cache:
            return self.cache.predict(state)

        # 量化推理
        elif self.enable_quantization:
            # （简化：实际需要完整的量化推理逻辑）
            if hasattr(self.model, 'forward'):
                return self.model.forward(state)

        # 默认推理
        return self.model.forward(state)

    def flush(self):
        """刷新所有队列"""
        if self.enable_batch:
            return self.batch_inference.flush()

    def get_stats(self) -> Dict[str, Any]:
        """获取优化统计"""
        stats = {
            "batch_inference": self.optimization_stats["batch_inference"],
            "cache": self.cache.get_cache_stats() if self.enable_cache else {},
            "quantization": self.optimization_stats["quantization"]
        }

        if self.enable_batch:
            stats["batch_inference"]["queue_size"] = self.batch_inference.get_queue_size()

        return stats

    def save_stats(self, filepath: str):
        """保存统计信息"""
        with open(filepath, 'w') as f:
            json.dump(self.get_stats(), f, indent=2)

        logger.info(f"✅ 性能统计已保存: {filepath}")


def main():
    """测试性能优化器"""
    # 创建模拟模型
    class DummyModel:
        def __init__(self):
            self.weights = {
                "layer1": np.random.randn(128, 64),
                "layer2": np.random.randn(64, 10)
            }

        def forward(self, state):
            return float(np.random.random())

        def get_weights(self):
            return self.weights

    model = DummyModel()

    # 创建优化器
    optimizer = PerformanceOptimizer(
        model,
        enable_batch=True,
        enable_quantization=True,
        enable_cache=True,
        enable_jit=False
    )

    print(f"✅ 性能优化器已创建")

    # 测试预测
    for i in range(100):
        state = np.random.randn(17)
        result = optimizer.predict(state)

    # 获取统计
    stats = optimizer.get_stats()
    print(f"\n📊 性能统计:")
    print(f"   批量推理调用: {stats['batch_inference']['calls']}")
    print(f"   缓存命中率: {stats['cache'].get('hit_rate', 0):.2%}")
    if stats['quantization']:
        print(f"   模型压缩率: {stats['quantization'].get('compression_rate', 0):.1f}%")


if __name__ == "__main__":
    main()
