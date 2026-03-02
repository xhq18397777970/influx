1. [x] 建立 Flask 服务骨架与配置模块（先落地可测试的最小框架）
   - LLM Prompt: 创建 `app` 包的最小可运行结构（`app/__init__.py`, `app/config.py`），提供 `create_app()` 与配置读取逻辑；实现 `MAX_CONCURRENCY=10`、`TOOL_TIMEOUT_SECONDS=30` 默认值与环境变量覆盖能力。
   - Files: `app/__init__.py`, `app/config.py`, `tests/test_config.py`
   - Tests: 先写 `tests/test_config.py`，覆盖默认值与环境变量覆盖。
   - Requirements: 7.1, 7.2, 3.2, 3.3

2. [x] 以测试先行实现请求参数校验器
   - LLM Prompt: 先编写 `tests/test_validator.py`，覆盖字段缺失、空值、时间格式错误、`start_time >= end_time`；再实现 `app/validators.py` 使测试通过。
   - Files: `app/validators.py`, `tests/test_validator.py`
   - Tests: 参数校验单元测试必须先失败再通过。
   - Requirements: 1.1, 1.2, 1.3, 1.4

3. [x] 实现工具适配层并统一六类工具调用接口
   - LLM Prompt: 创建 `app/tool_adapters.py`，为 network/code/cpu/metadata/qps/tp 提供统一调用函数，分别映射到 `tools/bps.py`, `tools/code.py`, `tools/cpu.py`, `tools/get_cluster_metadata.py`, `tools/qps.py`, `tools/tp.py` 的入口函数。
   - Files: `app/tool_adapters.py`, `tests/test_tool_adapters.py`
   - Tests: 使用 monkeypatch/mock 验证函数映射正确、异常会被捕获并返回标准错误对象。
   - Requirements: 2.1, 2.2, 2.3

4. [x] 实现分析编排器（线程池并发 + 单工具超时 + 部分失败容错）
   - LLM Prompt: 先写 `tests/test_orchestrator.py` 覆盖“全成功、部分失败、单工具超时”三类场景；再实现 `app/orchestrator.py`，使用 `ThreadPoolExecutor(max_workers=10)` 并输出每工具 `status/data/error/latency_ms`。
   - Files: `app/orchestrator.py`, `tests/test_orchestrator.py`
   - Tests: 必须断言六个工具在同一请求中被并行启动（非串行）、超时映射为 `timeout`、异常映射为 `error`，且不影响其他工具执行。
   - Requirements: 3.1, 3.3, 5.1, 5.2

5. [x] 实现请求级并发闸门与超限保护
   - LLM Prompt: 在 `app/concurrency.py` 实现全局 `BoundedSemaphore(10)` 的获取/释放封装；在路由层接入并发闸门，超限时返回 `429` 标准错误体。
   - Files: `app/concurrency.py`, `app/routes.py`, `tests/test_concurrency_guard.py`
   - Tests: 并发测试中模拟超过 10 请求时出现 `429`；验证 semaphore 在异常路径下也会释放。
   - Requirements: 3.2, 3.4

6. [x] 实现统一响应构建器与状态码决策逻辑
   - LLM Prompt: 在 `app/response_builder.py` 实现标准响应 envelope（`request_id/input/summary/results`），并实现 HTTP 状态码策略：至少一个成功返回 `200`，全部失败返回 `502/500`。
   - Files: `app/response_builder.py`, `tests/test_response_builder.py`
   - Tests: 覆盖 `success/error/timeout/empty` 组合下的 summary 统计和状态码决策。
   - Requirements: 4.1, 4.2, 4.3, 5.3

7. [x] 实现可观测性（request_id、总耗时、工具耗时、限流日志）
   - LLM Prompt: 在 `app/logging_utils.py` 与路由/编排层中接入结构化日志；每次请求生成 `request_id`，记录总耗时与各工具耗时，并记录并发超限事件。
   - Files: `app/logging_utils.py`, `app/routes.py`, `app/orchestrator.py`, `tests/test_observability.py`
   - Tests: 通过 log capture 断言关键字段存在：`request_id`、`total_latency_ms`、`tool_latency_ms`、`rate_limit_hit`。
   - Requirements: 6.1, 6.2, 6.3

8. [x] 接线并完成端到端自动化集成测试（以代码收口）
   - LLM Prompt: 完成 `POST /api/v1/cluster/analyze` 端点接线（validator + concurrency guard + orchestrator + response builder）；补齐 `tests/test_api_integration.py`，覆盖全成功、部分失败、全部失败、参数错误、并发超限。
   - Files: `app/routes.py`, `app/__init__.py`, `tests/test_api_integration.py`
   - Tests: 集成测试中 mock 六个工具调用，验证返回结构、状态码、错误体与输入回显。
   - Requirements: 1.1, 1.2, 1.3, 1.4, 2.1, 2.2, 2.3, 3.2, 4.1, 4.2, 4.3, 5.3, 7.1
