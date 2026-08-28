# Phase 1 / Phase 2 闭环整改独立复审（Codex）

- 评审日期：2026-08-29
- 评审范围：`906b17e..e7ba2d2`，申请文档提交 `afc85e0`
- 基准：`docs/MACAO_PRD_v2.md` v2.3.1、`docs/MACAO_REVIEW_GUIDELINES.md`
- 结论：**REJECT；不准予 L3 SCENARIO-VERIFIED / PG-2**

## 1. 总结

本轮已确认以下整改有效：配置已展平并传入合并控制器；non-git merge 和 non-git worktree 已改为 fail-closed；E2E 展示的票数与归档路径已修正，并通过本地 bare remote 验证了 happy path push；PTY 异常分支增加了 session 回收。

但本提交引入了新的协议/FSM P0 回归，合并流水线仍存在远端缺失假成功和 CI 失败后目标分支已前移的问题；所谓“真实 Adapter 驱动”仍是 Runner 直接生成产物的 Mock 场景。38/38 测试通过不能覆盖这些反例，也未达到 L3 明定的超时、人工裁定和消费方接口稳定性要求。

## 2. P0 阻断项

### P0-1：协议枚举与 PRD/Schema 被改坏，人工裁定路径不可用

`src/macao/core/types.py:8-32` 将权威 10 状态中的 `UNKNOWN` 替换成了 `HUMAN_OVERRIDE`，并将 7 种 AEP 消息中的 `REVIEW_RESPONSE`、`STATE_CHANGED` 替换/扩展成 `REVIEW_SUBMITTED`、`CONSENSUS_REACHED`、`OVERRIDE_RESOLVED`、`TASK_CANCELLED`。这与 PRD §2.4、§3.3 以及 `docs/schemas/aep_envelope.schema.json` 不一致，属于 PG-2 接口破坏性变更。

人工裁定存在两个可复现的直接故障：

1. CLI 仍只接受 `APPROVED|REWORK|RETRY_REVIEW|CANCEL`（`src/macao/cli/main.py:270-285`），但 `OverrideChoice` 已改成 `FORCE_MERGE|FORCE_REWORK|...`（`src/macao/core/types.py:64-69`）。实测 `OverrideChoice("APPROVED")` 和 `OverrideChoice("REWORK")` 均抛出 `ValueError`。
2. `resolve_override()` 最后发布 `AEPType.OVERRIDE_RESOLVED`（`src/macao/workflow/orchestrator.py:452-463`），但 AEP Schema 不允许该类型。实测 `AEPEnvelope.create(AEPType.OVERRIDE_RESOLVED, ...)` 被 Schema 拒绝。

因此 Deadlock 后最关键的 E7 人工处置不能可靠完成；现有 38 项测试没有调用 `resolve_override()`，所以全绿是覆盖缺口，不是路径有效证据。

修复要求：以 PRD/Schema 为唯一协议源恢复 `UNKNOWN`、7 种 AEP 类型和 CLI 规定的四种 choice；若确需升级协议，先同步 PRD、Schema、兼容策略与消费方契约测试。增加 APPROVED、REWORK、RETRY_REVIEW、CANCEL 四分支的端到端测试，断言产物、状态和通知要么全部成功，要么不发生部分提交。

### P0-2：MergeController 在配置远端不存在时仍返回成功；CI 失败后本地目标分支已经被合并

`MergeController` 先执行 `git merge --ff-only`，之后才运行 CI（`src/macao/merge/controller.py:59-83`）。专项反例中 CI 命令 `false` 返回失败，但 `main` HEAD 已等于 checkpoint；Orchestrator 随后把任务转入 REWORK（`src/macao/workflow/orchestrator.py:402-405`），造成“状态说返工、目标分支已包含待返工代码”的双账本冲突。

远端处理同样不是 fail-closed：当配置了 `remote_name` 但 `git remote` 中不存在该名称时，`src/macao/merge/controller.py:91-99` 直接跳过 push 并返回成功。专项反例以 `remote_name="missing-origin"` 调用，结果为 `True, Merge pipeline completed successfully`。代码也没有在 push 后读取远端 ref 并验证其 SHA。

影响：E4a/DONE 不能证明 PRD 要求的“最终 push 对象 == checkpoint_ref”；CI 失败可能已经污染目标分支。

修复要求：CI 应在隔离 checkpoint/worktree 上先运行，或失败时以经过验证的原子恢复策略保证目标分支未改变；配置了 remote 时，remote 不存在、push 失败或 push 后远端 SHA 不等于完整 checkpoint 均必须失败且不得进入 DONE。增加 missing remote、push rejection、CI failure、远端 SHA 不匹配四个真实 Git 反例。

### P0-3：Phase 2 仍不是 Adapter 驱动场景，无法证明接口消费方已接通

Runner 虽注入了三个 `MockAgentAdapter`（`src/macao/workflow/e2e_runner.py:105-122`），但未调用它们的 `start()`、`inject_task()`、`ack()`、`simulate_produce_*()` 或 `stop()`。源码、测试、`.dev.yml` 以及三份 `.review.yml` 仍由 Runner 直接写入主仓库（`e2e_runner.py:135-195,221-240`），并非由对应 Adapter 在各自 worktree 中生成。

Composition Root `get_orchestrator()` 也只注入配置字典，没有按 `team` 构造真实 Adapter；Orchestrator 仅发布 SQLite 消息，没有消费循环将消息送入 Adapter。故申请所称“真实 Adapter 注入/驱动”仍未成立。将本路径明确称为 Mock simulation 是合理的，但它不能证明 PG-2 所要求的稳定接口与消费方场景。

修复要求：至少建立一个完全由 Mock Adapter 契约驱动的 deterministic E2E（消息消费 → start/inject → worktree 内产物 → ACK → stop），并断言每个方法的调用与路径；真实 CLI 可另设受控、人工监督的 OPS 测试，不必消耗在单元测试中。申请文案应区分 Mock scenario、真实 PTY 探针和真实 CLI 协同。

### P0-4：AEP message_id 日内碰撞会使消息总线直接写入失败

`AEPEnvelope.generate_message_id()` 只取 `uuid.uuid4().int` 十进制文本的前 4 位（`src/macao/msg/envelope.py:16-20`），而 `message_queue.message_id` 是主键（`src/macao/storage/db.py:72-95`）。现场连续生成 1000 个 ID，仅 863 个唯一，出现 137 次碰撞；重复 ID 发布时会触发 SQLite 唯一约束错误，消息和 deliveries 均无法建立。

这会直接影响任务启动、评审分发和合并通知，不满足 PG-2 的接口稳定要求。应使用完整 UUID/ULID，或保留 Schema 前缀后使用至少 128 bit 随机量；同时增加固定随机源碰撞反例、并发发布和数据库幂等语义测试。

## 3. P1 重要问题

1. **Worktree 失败不是事务性 fail-closed。** `dispatch_review_requests()` 在创建任何 worktree 之前先将 FSM 推进到 `WAITING_REVIEW` 并归档 `.dev.yml`（`src/macao/workflow/orchestrator.py:188-205`）。任一 worktree 创建失败后虽然抛错，但状态与产物已消费，任务会卡在没有完整投递的 WAITING_REVIEW。应先完成全部准备，或实现补偿/事务状态。

2. **Phase 1 的 ANSI/进程树结论仍是假阳性。** Harness 只执行四个 CLI 的 `--version`（`src/macao/adapter/integ_harness.py:78-89`），随后无条件设置 `ansi_stripped_ok = True`（`108-110`）；PASS 不包含 ANSI 断言，也只检查原始 PID，不检查 PGID/子孙进程（`114-130`）。它能证明短命令 PTY 可启动，不能证明输入管道、ANSI 清洗或真实交互会话的进程树强杀。

3. **消息 ACK/TTL 上轮问题未关闭。** `MessageBus.ack(message_id)` 不传 recipient 时仍会一次 ACK 全部 deliveries（`src/macao/msg/bus.py:91-106`）；deadline 没有扫描、退避重试和自动 DLQ，review dispatch 也没有写 deadline。L3 要求的超时场景没有工作流级测试。

4. **归档只复制，不满足 PRD 生命周期。** `WorkflowFSM` 使用 `copy2` 后不删除源文件，也没有执行“git 提交 → 复制 → 删除原位置”（`src/macao/workflow/fsm.py:71-111`）。E2E 只断言 archive 中存在文件，没有断言源产物已消费清除、SQLite 双账本与哈希一致。

5. **真实 Adapter 合同仍未回归。** Codex/Claude 的 `get_logs(tail_lines)` 仍向不接受参数的 `PTYSession.get_clean_logs()` 传参；现有测试未覆盖真实 Adapter 的 start/inject/log/stop。`macao test-clis` 使用独立的 `--version` 命令，无法发现该类问题。

6. **增量洁净度仍不通过。** `git diff --check 906b17e..e7ba2d2` 报告 POC 报告和集成申请中的多处 trailing whitespace。申请声称全部 P1 闭环，但上轮明确指出的这一项未关闭。

7. **L3 场景矩阵不完整。** 当前有全同意、返工、1:1 Deadlock、部分弃权函数测试和两种恢复测试，但没有 deadline/超时降级、E7 四分支、worktree 中途失败、push 失败、CI 失败后恢复、重复消息/ACK 的系统场景。按评审指南 §2.1、§3.3，不能仅凭 happy-path E2E 授予 L3。

## 4. 已验证的正向整改

- `PYTHONPATH=src python3 -m unittest discover tests -v`：38/38 PASS。
- `PYTHONPATH=src python3 -m compileall -q src`：通过。
- `macao e2e-run`：Mock happy path 报告 3 票、5 份归档并完成本地 bare remote push；显示字段已与实际聚合结果一致。
- `ConfigManager.to_runtime_config()` 能将 `require_signoff`、CI、remote、quorum 和 reviewer IDs 贯穿到 Orchestrator。
- non-git merge、non-git worktree 和 git diff 假文件回退已经改为 fail-closed/空结果。
- PTY 不支持平台可返回 SKIPPED，异常路径会尝试终止已创建 session。

## 5. 门禁判定与闭环顺序

当前快照存在 P0/P1，且协议接口不稳定，**PG-1 的“P0/P1 为零”和 PG-2 的“接口稳定 + 消费方场景测试”均不满足**；L2 的 SPEC-CODE-ALIGNED 也应在恢复 PRD 枚举后重新确认。

建议闭环顺序：

1. 恢复 PRD/Schema/CLI/FSM/AEP 的单一协议，并补齐 E7 四分支测试。
2. 修复 merge 的 CI 前置/原子性、missing remote fail-closed 和 push 后远端 SHA 校验。
3. 让 E2E 真正通过 Adapter 合同驱动，补齐 worktree 失败补偿与消息 ACK/timeout 场景。
4. 完成真实 Adapter 合同测试、归档生命周期测试和 `git diff --check`。

完成上述 P0/P1 后再申请 L3 / PG-2。

## 6. Reviewer 自审

本轮除复测申请列出的整改点外，额外交叉核对了协议枚举、CLI 消费方、失败后的 Git 物理状态以及 Schema 对消息类型的约束，避免仅依据 38/38 happy-path 结论外推门禁等级。
