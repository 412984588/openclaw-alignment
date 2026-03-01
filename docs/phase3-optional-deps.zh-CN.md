# Phase3 可选依赖

安装方式：

```bash
pip install "openclaw-alignment[phase3]"
```

功能映射：

- `redis`、`celery`：分布式训练
- `torch`、`tensorboard`：神经网络与监控
- `numba`：JIT 优化
- `scipy`：指标分析中的高级拟合

缺少依赖时，系统会自动降级。
