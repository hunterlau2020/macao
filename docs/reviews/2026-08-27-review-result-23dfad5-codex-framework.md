# MACAO 整体技术框架评审

- **评审日期**：2026-08-27
- **评审对象**：`23dfad5`（全项目技术方案、目录/依赖结构及当前实现）
- **评审维度**：技术选型、代码组织、实现质量
- **结论**：**当前框架适合作为“纯 Mock 的概念验证”，不具备真实三 CLI 编排或安全合并的可用基础。** Python、SQLite、JSON Schema 与增强型 CLI 的主选型本身合理；阻断点在于把元数据和 Mock 行为当作运行时安全边界，以及协议、配置和 Adapter 契约存在多套不兼容的真相源。

## 1. 技术选型

### 可保留的选择

- **Python + Click/Rich**适合本地单机 PoC：易于脚本化、调试和编写流程测试；没有必要在当前阶段引入 Web 前端或全屏 TUI。
- **SQLite + WAL**适合单控制进程的状态快照与轻量队列；**JSON Schema**适合把磁盘产物和 AEP 信封变为可验证契约。
- **Git worktree**适合作为评审 checkout 的便利机制，PTY 也可作为厂商 CLI 尚无稳定 API 时的短期兼容层。

### P0：把 worktree 当安全沙箱是错误的技术边界

`execution_mode=SANDBOXED` 只存在于 Capability Manifest（`src/macao/adapter/codex.py:19-28`、`src/macao/adapter/kimi.py:18-27`），实际启动仅以同一用户权限运行 CLI（`:48-52`），没有容器、用户/挂载命名空间、网络策略、命令白名单或凭据隔离。`git worktree` 仅分离 checkout，不限制进程读取父目录、改动其他路径或联网；因此不能兑现技术总览所称的“物理隔离沙箱”（`docs/TECH_INTRUDUCE.md:78,195-196`）。

**要求**：将 Reviewer 定位降为“隔离 checkout、非安全 sandbox”，或在真实联调前接入可验证的 OS 级边界（例如 rootless container/bubblewrap、只读挂载、临时凭据、网络默认拒绝），并将该边界作为 preflight 的硬失败条件。

### P1：SQLite 消息表的 Pub/Sub 语义不成立

`message_queue` 对多个接收者只保存一行及一个 `status`（`src/macao/storage/db.py:72-84`）；任一接收者 ACK 会使所有接收者都看不到消息（`src/macao/msg/bus.py:47-83`）。已复现：向 `r1,r2` 广播后，`r1` ACK，`r2` 的待收列表变为空。这也意味着声明的 TTL、重试和 DLQ 没有消费方粒度的状态，且代码中没有 deadline 扫描/退避重投实现（`src/macao/msg/bus.py:21-100`）。

**要求**：若需要 fan-out，发布时拆成每接收者一条投递，或引入 `message_deliveries(message_id, recipient, status, attempts, lease_until)`；ACK/DLQ/重试以 delivery 为键。若只需要 point-to-point，则从协议和接口移除数组 `to` / `all`，避免错误承诺。

## 2. 项目代码组织结构

### P0：核心协议类型出现重复且不兼容的定义

- `PreflightCheckResult` 在 `src/macao/core/types.py:122-133` 的字段为 `agent_id/error`，而三个 Adapter 仍以旧的 `cli_name/auth_valid/in_matrix/details` 构造它（如 `src/macao/adapter/codex.py:30-45`）。实际调用 `CodexAdapter/KimiAdapter/ClaudeCodeAdapter.preflight()` 均复现为 `TypeError: unexpected keyword argument 'cli_name'`。
- 当前 `PTYSession` 提供 `send_input()`，没有 `write_input()` 或 `get_clean_logs()`（`src/macao/adapter/pty_session.py:100-156`）；三个真实 Adapter 却调用后两者（如 `src/macao/adapter/codex.py:62-76`）。即使启动成功，任务注入/日志读取也会在运行时失败。
- `AEPEnvelope` 同时作为 `core.types` dataclass（`src/macao/core/types.py:80-90`）与 `msg.envelope` dict helper（`src/macao/msg/envelope.py:11-50`）存在；`CapabilityManifest` 也重复定义于 `core.types` 和 `adapter.base`。这让模块间的接口无法通过类型或测试保障。

**要求**：建立唯一的 `domain/protocol`（枚举、dataclass、Schema 映射）和唯一的 `ports`（Adapter、MessageBus、Git、StateStore）层；删除重复类型，令实现只依赖接口。为每个真实 Adapter 建立 contract test，至少覆盖 preflight、start、inject、logs、cancel，不以 Mock 代替。

### P1：配置不是单一事实源，CLI 初始化产物无法加载

运行 `macao init --path <temp>` 后交给 `ConfigManager.load_config()`，已复现失败：`'team' is a required property`。原因是 CLI 生成 `project/agents/consensus/orchestration`（`src/macao/cli/main.py:50-82`），而 Schema/现有配置要求 `project.repository/team`（`docs/schemas/macao_config.schema.json:6-49`、`macao.yaml:1-25`）。同时 Orchestrator 使用另一份扁平 dict（`src/macao/workflow/orchestrator.py:44-49,215,339-340`），绕开 `ConfigManager`。

**要求**：用一个版本化 config model 生成、校验、加载并注入全部服务；CLI 不得硬编码与 Schema 不同的模板或默认 Agent/版本。把 config 解析放在 composition root，禁止业务模块自行解释原始 dict。

### P1：应用层职责过度集中，难以做可靠性测试

`Orchestrator` 同时负责文件解析、Git 差异、worktree 生命周期、AEP 发布、共识、状态转移、归档和 merge（`src/macao/workflow/orchestrator.py:90-396`）。该结构使 Mock 测试绕过了真实 Git、Adapter、消息投递和配置装配，测试 S1 甚至在非 Git 临时目录以虚构 commit 走“模拟 merge 成功”（`tests/test_orchestrator_sim.py:16-85`；`src/macao/merge/controller.py:55-59`）。

**建议结构**：

```text
cli (composition root)
  -> application services (task / review / consensus / merge)
      -> ports (AgentRuntime, MessageBus, GitRepository, ArtifactStore)
          -> adapters (PTY CLI, SQLite, Git, filesystem)
domain (state machine, vote rules, immutable protocol types)
```

状态转移、审计事件和 outbox 投递应在同一 SQLite 事务中形成一个应用服务操作；磁盘产物/Git 归档通过可重放 job 处理，而不是由一个调用链隐式双写。

## 3. 代码实现质量

### P0：真实适配器与环境预检不可用，且 CLI 报告了虚假就绪

真实 Adapter 的 preflight 已如上复现为异常；CLI `preflight` 没有调用任何 Adapter 或探测环境，而是输出固定版本、固定“System ready”结果（`src/macao/cli/main.py:22-38`）。这会让操作者在 CLI 缺失、版本不兼容、认证无效或 Adapter 已断裂时得到通过结论。

**要求**：`preflight` 必须实例化由 config 选择的 Adapter，执行真实但无副作用的二进制/version/auth/capability 探测，并按失败退出码返回；把各 CLI 参数与支持版本置于被测的 manifest，绝不写死在 UI。

### P1：审计/恢复与产物声明仍非可验证实现

- `StateReconciler` 只扫描两个固定活跃路径，未从 git 历史恢复，且直接 `update_task_state`，绕开 FSM 合法性校验（`src/macao/storage/reconcile.py:34-77`）。
- `artifacts` 虽已加 `artifact_id`，但登记和消费依旧更新同一行（`src/macao/storage/store.py:80-119`），不能实现 PRD 所称“归档新增行、原行只读”的 append-only 审计模型。
- `SchemaValidator` 运行时向上搜索源码树中的 `docs/schemas`（`src/macao/core/schema.py:10-19`）；`pyproject.toml` 未将 schemas 作为 package data（`:1-39`）。源码目录内有效不代表安装后的 wheel/二进制环境可验证协议。

**要求**：将版本化 schema 打包进 Python package（或显式外置并在启动时必须提供路径/版本），将恢复逻辑改为使用事件和幂等 job，并为“已安装包”“真实临时 Git repo”“崩溃于每个双写阶段”增加测试。

### P2：工程声明与实际 Phase/测试范围漂移

`docs/PLAN.md` 明确把合并、沙箱、DLQ、脱敏及完整 CLI 交互放在 Phase 2/3 待开展（`:25-36,96-120`），但 `TECH_INTRUDUCE.md` 称“全量组件均已实现”、并把 agmsg、TTL/DLQ、签字、prompt_toolkit 写成已落地（`:69-82`）。实际依赖中 `prompt_toolkit` 仅是 dev extra 且源码未使用（`pyproject.toml:29-33`），`usage` 只是占位输出（`src/macao/cli/main.py:206-213`）。

**要求**：将技术说明改为“已实现 / Mock 验证 / 待实现 / 待实机验证”四种状态；将门禁从“测试总数”改为能力矩阵和反例覆盖清单。

## 建议的重建顺序

1. 先冻结一个可运行的协议/配置/Adapter Contract，并修复真实 Adapter 的 API 断裂；补 contract tests。
2. 建立真正的 Reviewer 安全边界和可验证的 preflight；未完成前禁止任何真实 CLI 自动执行。
3. 重构消息投递为每接收者状态，并以 transactional outbox 连接 FSM/audit。
4. 拆分 Orchestrator 为应用服务和基础设施 port；补真实 Git、安装包、并发/崩溃与 CLI 的集成测试。
5. 最后再扩展 TUI、用量统计、第三 Reviewer 或分布式能力；它们不应掩盖当前执行路径的可靠性缺口。

## 验证记录

- `PYTHONPATH=src python3 -m unittest discover tests -v`：24/24 通过。
- `PYTHONPATH=src python3 -m compileall -q src`：通过。
- 额外反例已执行：三 Adapter `preflight()` 的类型错误、PTY 方法缺失、`macao init` 生成配置无法被 loader 验证、广播消息被单一 ACK 吞掉。
