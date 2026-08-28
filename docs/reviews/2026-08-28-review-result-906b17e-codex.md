# MACAO Phase 1 / Phase 2 集成评审（Codex）

评审对象：`aa173d8..906b17e`，工作区当前提交 `82ffe99`（申请文档）。

## 结论

**不准予 L3 INTEGRATED / PG-2 准入。**

本次整改修复了 DTO 构造错误，也为消息扇出增加了按接收者投递记录；34 个现有测试可通过。但 Phase 2 并未让真实 Executor/Reviewer 执行协同，合并安全配置没有真正接入，而且 Phase 1 的“真实 CLI 生命周期”只测量 `--version` 子进程。因此现有证据最多证明了**受控模拟流程和短命令 PTY 基础能力**，不能证明申请所述的真实多 Agent 闭环或生产级安全门禁。

## 阻断项（P0）

### P0-1：Phase 2 Runner 伪造 Executor 与 Reviewer 产物，未运行任何真实 Adapter

- `ControlledE2ERunner` 构造 `Orchestrator` 时未注入 executor 或 reviewer adapters（`src/macao/workflow/e2e_runner.py:95`）。因此分发阶段实际采用 Orchestrator 的默认 `cc-glm`、`kimi` 两人列表（`src/macao/workflow/orchestrator.py:155`），并非报告显示的 Codex/OpenCode/AGY 三人。
- Runner 自行写入算术源码、测试和 `.dev.yml`（`e2e_runner.py:108-168`），随后又在主工作区自行生成三份全赞成 `.review.yml`（`e2e_runner.py:194-213`）。这些写入没有调用 Adapter 的 `start()`、`inject_task()`、`ack()` 或任何真实 CLI。
- 所以工作树分发、三方评审、仲裁三者不属于同一参与者集合；测试只验证了人为预置的 YAML 能被聚合。实际运行 `macao e2e-run` 也显示 `votes_yes=0, effective_votes=0`，但仍显示 APPROVED，原因是报告读取了不存在的 `yes_approve` / `effective_votes` 键（`e2e_runner.py:220-227`）。

影响：申请的“实机端到端协同闭环”和“三方 Worktree 物理隔离审查”没有成立，不能作为 PG-2 证据。

修复要求：Composition Root 按 `macao.yaml.team` 构造并注入全部 Adapter；E2E 必须由 Executor 真实产出 checkpoint 与 dev manifest、由每个已创建 worktree 内对应 Reviewer 产出 review manifest，并对每个 Adapter 的启动、输入、退出、消息 ACK 与产物路径做断言。模拟路径应单独命名为 simulation，不可作为实机证据。

### P0-2：合并安全配置未被消费，默认人工签字可被静默绕过，且从未推送远端

- `ConfigManager.load_config()` 返回的是 Schema 顶层嵌套结构（`policy`、`merge`），但 Orchestrator 读取扁平的 `self.config["ci_gate_command"]` / `self.config["require_signoff"]`（`orchestrator.py:343-351`）。以仓库 `macao.yaml` 实测：`merge.require_human_signoff=True`，而 Orchestrator 得到 `require_signoff=False`。
- `execute_merge()` 没有将 `remote_name` 传给 `MergeController`（`orchestrator.py:347-351`）；故控制器中仅在 `remote_name` 非空时执行的 `git push` 永远不会发生（`merge/controller.py:92-96`）。Phase 2 临时仓库本身也没有远端。
- `get_orchestrator()` 吞掉配置校验异常并退回缺省值（`cli/main.py:86-99`），该缺省值也为 `require_signoff=False`（`orchestrator.py:49-54`），形成安全配置 fail-open。

影响：生产配置要求人工签字时仍可能本地合并并进入 DONE；没有远端 HEAD 校验，和 PRD 的推送后硬校验不一致。

修复要求：将 `ConfigManager` 显式映射为一个已验证的运行时策略 DTO（含 quorum、CI、signoff、remote）；配置错误必须拒绝 mutating 命令。合并前强制传入已配置 remote，push 成功后以 `remote/target_branch` 的 SHA 精确校验 checkpoint；对“无签字拒绝”和“push/CI 失败不进入 DONE”增加真实 git fixture 测试。

### P0-3：所谓 `sandboxed` 仅是临时 cwd / Git worktree，不满足 PRD 的安全边界

Phase 1 Harness 仅以 `tempfile.mkdtemp()` 创建目录、在其中运行各 CLI 的 `--version`（`src/macao/adapter/integ_harness.py:52-74`）。PTYSession 用同一 OS 用户直接 `Popen`，没有容器、用户/挂载命名空间、网络限制或凭据隔离（`src/macao/adapter/pty_session.py:25-58`）。但 PRD §12.2 明确要求 sandboxed 模式处于独立 worktree **加容器/受限环境**，默认禁止网络和包安装。

影响：将 reviewer 标为 `SANDBOXED` 不构成安全承诺；遭受提示注入的 CLI 仍能以宿主用户权限访问可见文件、凭据和网络。

修复要求：在可审计的 OS 级隔离器中执行（例如 rootless container / bubblewrap，最小挂载、无网络默认、显式凭据注入），并在 preflight 与集成测试中验证隔离失败即拒绝接入。

## 重要问题（P1）

1. **Phase 1 验收并未覆盖所宣称的行为。** Harness 的成功条件只要求 PTY 成功启动且原始 PID 消失（`integ_harness.py:119-120`）；ANSI 结果不参与 verdict，且“进程已自然以 0 退出”即可视为 ANSI 成功（`87-92`）。它既不写入标准输入，也不验证 PGID、子孙进程或 SIGKILL 路径；异常分支仅删除临时目录，不会对已启动的 `session` 执行 terminate（`103-117`）。应使用受控的长运行、带 ANSI、会派生子进程的 fixture 覆盖 TERM、KILL、异常清理与全 PGID 扫描。

2. **归档验收为假阳性。** FSM 按 PRD 写入 `.macao/archive/<checkpoint_ref>/r1/`，而 Runner 检查的是 `<task_id>/r1`（`e2e_runner.py:248-250`）。实测 `macao e2e-run` 输出 “Archived 0 files”，UI 仍无条件显示 `PERSISTED`。`status` 也不检查归档列表（`252-261`）。应检查正确目录、内容集合和哈希，并将 0 归档视为失败。

3. **独立 ACK API 仍可被一次无 recipient 的 ACK 全部确认。** `MessageBus.ack(message_id)` 的默认分支更新该消息的所有 deliveries（`src/macao/msg/bus.py:91-106`）。此外 deadline 没有调度、重试或自动 DLQ，分发请求也未设置 deadline；这不满足 PRD §11.6 的阶段 TTL 与三次退避。应将 recipient 设为必填或由经过认证的消费者上下文推导，并实现/测试到期、重投和 DLQ。

4. **质量自检结论不实。** `git diff --check aa173d8..HEAD` 实际报告多处新增行尾空格，包括两份集成方案、POC 验证报告和本申请；并非“0 errors”。将该检查纳入 CI 门禁。

5. **真实 Adapter 路径缺少覆盖。** Adapter 的 `get_logs(tail_lines)` 调用 `PTYSession.get_clean_logs(tail_lines)`，但后者不接收参数（例如 `src/macao/adapter/codex.py:66-67` 对 `pty_session.py:115-117`），真实日志读取会抛出 `TypeError`。现有测试只运行 preflight 和 Harness，未覆盖 start/inject/log/stop 契约。

## 已验证的正向项

- `PYTHONPATH=src python3 -m unittest discover tests -v`：34/34 PASS。
- `PYTHONPATH=src python3 -m compileall -q src`：通过。
- 消息总线针对 `ack(message_id, recipient=...)` 的两接收者独立 ACK 回归测试通过。
- `macao e2e-run` 可在临时 Git 仓库中完成本地 fast-forward 模拟；该运行同时暴露了归档 0 文件和错误的投票展示，不能被解释为真实协同成功。

## 准入建议

在上述 P0 全部关闭前，定级应为 **L2（受控模拟 / 组件已接线）**，不应进入 PG-2。复审时至少提交：真实 Adapter 驱动的三方证据、OS 级隔离证据、签字/CI/push 负向测试、正确的归档与消息 TTL/ACK 回归测试，以及干净的 `git diff --check`。
