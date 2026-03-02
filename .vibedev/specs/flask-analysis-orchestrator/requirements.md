# Requirements Document

## Introduction
本功能将提供一个基于 Flask 的统一分析服务接口。调用方提交开始时间、结束时间、集群名称后，服务并发调用 `tools/` 下的分析能力（network、code、cpu、metadata、qps、tp），聚合后一次性返回结果。系统需明确并发能力约束为 `10`（并发=10），并保证在部分工具失败时仍可返回可解释的结果。

## Requirements
wqaq  QAaqqa          qq  
1. API 输入与协议
   - User Story: As a 调用方, I want to 通过一个 HTTP 接口提交时间范围和集群名称, so that 我可以一次触发全量诊断分析。
   - Acceptance Criteria:
     1. When 调用方以 `POST` 请求分析接口时, the system shall 接收 `start_time`、`end_time`、`cluster_name` 三个必填字段。
     2. If 任一必填字段缺失或为空, then the system shall 返回 `400 Bad Request` 与明确字段级错误信息。
     3. If `start_time` 或 `end_time` 不满足 `YYYY-MM-DD HH:MM:SS` 格式, then the system shall 返回 `400` 并说明格式要求。
     4. If `start_time >= end_time`, then the system shall 返回 `400` 并说明时间范围非法。

2. 分析工具编排范围
   - User Story: As a 调用方, I want to 一次调用覆盖全部关键分析工具, so that 我无需逐个调用多个接口。
   - Acceptance Criteria:
     1. When 输入参数校验通过时, the system shall 触发以下六类分析：network、code、cpu、metadata、qps、tp。
     2. Where 现有工具模块可用, the system shall 分别调用 `get_cluster_network_analysis`、`get_cluster_status_code_analysis`、`get_cluster_cpu_analysis`、`get_cluster_metadata`、`get_cluster_qps_analysis`、`get_cluster_connect_delay_analysis`。
     3. If 任一工具调用抛出异常, then the system shall 记录失败原因且不阻断其他工具执行。

3. 并发执行策略
   - User Story: As a 平台运维, I want to 控制服务并发, so that 服务在负载下保持稳定并避免下游过载。
   - Acceptance Criteria:
     1. While 服务处理分析请求时, the system shall 使用并发执行机制并行触发六个工具调用。
     2. The system shall 将服务并发上限设置为 `10`（并发=10）。
     3. The system shall 将工具调用线程池（或等效执行池）最大并发设置为 `10`。
     4. If 并发请求数超过 `10`, then the system shall 采用可配置限流或排队策略，并返回可观测的限流信号（如 429 或排队等待）。

4. 聚合结果输出
   - User Story: As a 调用方, I want to 获得结构化聚合结果, so that 我能直接展示或继续自动化处理。
   - Acceptance Criteria:
     1. When 六类分析执行完成或达到超时条件时, the system shall 返回统一 JSON 结构。
     2. The system shall 在响应中包含 `request_id`、输入参数回显、每个工具的 `status`、`data`、`error`、`latency_ms`。
     3. If 某工具无数据返回, then the system shall 将该工具标记为 `empty` 并提供说明文本。

5. 超时与失败处理
   - User Story: As a 调用方, I want to 在异常情况下仍及时收到响应, so that 我可以快速重试或降级。
   - Acceptance Criteria:
     1. The system shall 为每个工具调用配置超时时间（默认 30 秒，可配置）。
     2. If 工具调用超时, then the system shall 将该工具状态标记为 `timeout` 并继续聚合其他结果。
     3. When 所有工具均失败时, the system shall 返回 `502` 或 `500` 并附带各工具失败原因摘要。

6. 可观测性与运维
   - User Story: As a 运维工程师, I want to 追踪一次请求的全链路状态, so that 我能快速定位性能瓶颈与失败根因。
   - Acceptance Criteria:
     1. When 接收到分析请求时, the system shall 生成唯一 `request_id` 并写入全链路日志。
     2. The system shall 记录接口总耗时和各工具耗时。
     3. If 请求命中限流或并发保护, then the system shall 记录限流事件与当前并发计数。

7. 安全与配置
   - User Story: As a 平台管理员, I want to 通过配置管理并发与超时参数, so that 我可以在不同环境安全发布。
   - Acceptance Criteria:
     1. The system shall 支持通过环境变量或配置文件设置并发上限、工具超时、日志级别。
     2. If 未提供配置项, then the system shall 使用默认值：`MAX_CONCURRENCY=10`、`TOOL_TIMEOUT_SECONDS=30`。
