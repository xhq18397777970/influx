# Flask Analysis Orchestrator

基于 Flask 的分析聚合服务。  
接口输入 `start_time`、`end_time`、`cluster_name`，并行调用 `tools/` 下 6 类分析能力（`network/code/cpu/metadata/qps/tp`），统一返回结果。

## 1. 环境准备

```bash
source /opt/homebrew/anaconda3/etc/profile.d/conda.sh
conda activate agent
```

安装依赖（如已安装可跳过）：

```bash
pip install flask requests numpy
```

## 2. 启动项目

在项目根目录执行：

```bash
export FLASK_APP=app:create_app
export FLASK_ENV=development
flask run --host 0.0.0.0 --port 5000
```

默认配置（可通过环境变量覆盖）：
- `MAX_CONCURRENCY=10`
- `TOOL_TIMEOUT_SECONDS=30`
- `LOG_LEVEL=INFO`

## 3. 接口说明

- Method: `POST`
- Path: `/api/v1/cluster/analyze`
- Content-Type: `application/json`

请求体：

```json
{
  "start_time": "2026-01-13 09:00:00",
  "end_time": "2026-01-13 09:30:00",
  "cluster_name": "ga-lan-jdns1"
}
```

## 4. 调用示例

调用示例已从 README 分离为独立 Python 文件：

- 单次调用：`examples/simple_call.py`
- 并发调用（并发=10）：`examples/concurrent_call.py`

运行方式：

```bash
# 单次调用
python examples/simple_call.py

# 并发调用（默认并发=10）
python examples/concurrent_call.py --concurrency 10 --total-requests 10
```

示例响应（节选）：

```json
{
  "request_id": "9f1e6d09f8624d5da3186fb8f64f6ea2",
  "input": {
    "start_time": "2026-01-13 09:00:00",
    "end_time": "2026-01-13 09:30:00",
    "cluster_name": "ga-lan-jdns1"
  },
  "summary": {
    "success_count": 5,
    "empty_count": 0,
    "failure_count": 1,
    "timeout_count": 0,
    "total_count": 6
  },
  "results": {
    "network": {"status": "success"},
    "code": {"status": "success"},
    "cpu": {"status": "success"},
    "metadata": {"status": "success"},
    "qps": {"status": "success"},
    "tp": {"status": "error"}
  }
}
```

## 5. 运行测试

```bash
python -m unittest
```
