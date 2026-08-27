# Phase 0 / Phase 1 核心代码与测试套件独立审批评审结论

- **评审日期**：2026-08-27
- **评审对象**：commit `d137a05`..`435eeea` 的架构文档、`src/macao/` 与 `tests/`；申请见 `docs/reviews/2026-08-27-review-request-Phase0-Phase1-Code.md`
- **评审基准**：`docs/MACAO_PRD_v2.md` v2.3.1、`docs/schemas/`、`docs/MACAO_REVIEW_GUIDELINES.md`
- **结论**：**未达到 L2 SPEC-CODE-ALIGNED / PG-1；不得准入。** 现有 22 项测试可复现通过，但未覆盖共识身份去重、Deadlock 终局、状态表实际强制、Reviewer fail-closed 隔离和 Merge Policy。以下 P0 允许伪造法定人数、绕过状态/审计约束或让 Reviewer 回退到主工作区。

## 已确认项

- `PYTHONPATH=src python3 -m unittest discover tests -v`：22/22 通过。
- `PYTHONPATH=src python3 -m macao.cli.main doctor`：配置 Schema 与 SQLite 健康检查通过。
- 以上结果仅证明当前测试断言，不能覆盖下述反例。

## P0：必须先解决

| 编号 | 可复现证据 | 风险与修正要求 |
|---|---|---|
| P0-1 共识可由一个 Reviewer 伪造法定人数，Deadlock 还会预写错误终局 | `VoteAggregator.collect_reviews()` 按文件枚举收集，不按 `reviewer.id` 去重（`src/macao/consensus/vote.py:22-52`）；`StateRecognitionEngine` 也仅累加文件数（`src/macao/workflow/state_engine.py:60-83`）。复现：把同一 `r1.review.yml` 复制为 `r1-copy.review.yml`，仅一名 Reviewer 的两个 YES 票即被计作 2 票并转入 `MERGING`。此外，编排器在判定前无条件生成并写入 vote_result（`src/macao/workflow/orchestrator.py:204-221`），而生成器把 `DEADLOCK` 静默编码为 `REWORK_REQUIRED`（`src/macao/consensus/vote.py:102-145`）；1:1 时磁盘上已有该文件，违反 PRD 的“Deadlock 不写 vote_result、HOLD 等 E7”（`docs/MACAO_PRD_v2.md:829,893-902`）。 | 以已配置 reviewer 的唯一 ID 为准入集合，拒绝未知 ID、重复 ID、重复投递，计票前校验 `reviewers_responded` 与票面一致；每个 `message_id` 必须来自实际 AEP 回执。对 Deadlock 禁止写自动终局文件；只允许 E7 生成 `resolution=human_override` 的四值终局。为复制文件、未知 reviewer、1:1、超时弃权和四种 override 分支增加测试。 |
| P0-2 FSM 状态表未被实际执行，CLI 可绕过终局审计 | `WorkflowFSM.transition()` 从不调用 `TransitionTable.can_transition()`，而是无条件写库（`src/macao/workflow/fsm.py:21-63`）。可复现：`fsm.transition(task, DONE, "E1")` 后数据库状态为 `DONE`，但 `TransitionTable.can_transition(IDLE, DONE, "E1")` 返回 `False`。`macao override resolve` 也直接记录 override 后调用 FSM，不生成 PRD 所要求的终局 vote_result、未验证当前必须为 `CONSENSUS_CHECK`，见 `src/macao/cli/main.py:163-188`。 | 在唯一 transition 入口先强制验证 source、target、trigger 和前置产物；为开发产物转换定义正式 trigger，而非绕过状态表的 `E1_PRODUCED` / `EXPLICIT_SIGNAL`。CLI 必须委托 `Orchestrator.resolve_override()`，并在 E7 前校验 Deadlock/轮次，原子写终局 vote_result、审计和状态。补非法转换、终态不可转出、四个 override 的负向测试。 |
| P0-3 Reviewer 隔离 fail-open，真实 Adapter 未接收 worktree 路径 | 分发阶段工作树创建失败或 checkpoint 不存在时吞掉异常，并把 `isolated_worktree_path` 回退成主工作区（`src/macao/workflow/orchestrator.py:141-163`），违反 PRD 对 Reviewer“强制 sandboxed + 独立 worktree”的准入硬条件（`docs/MACAO_PRD_v2.md:1401-1406,1624-1629`）。即使创建成功，向 Adapter 注入的 payload 也没有该路径（`src/macao/workflow/orchestrator.py:165-171`）；Codex/Kimi 只在 `start()` 时从自身 config 取路径（`src/macao/adapter/codex.py:48-52`、`src/macao/adapter/kimi.py:47-51`），因此会继续在默认工作区运行。测试 S1 使用不存在的 `commit-oauth-001`（`tests/test_orchestrator_sim.py:49`）却仍通过，正是在验证该不安全回退。 | reviewer capability/preflight、commit 校验、worktree 创建和路径注入任一失败都必须拒绝 E2、记录审计且保持 `READY_FOR_REVIEW`；把每个已创建路径显式绑定到 Adapter 生命周期并在结束/失败后回收。测试必须断言 Reviewer 实际 cwd 是其专属 worktree，且失败时没有 `REVIEW_REQUEST` 和没有主工作区回退。 |
| P0-4 Merge Policy 的签字、push、E4a 硬校验及失败回退均未实现 | `MergeController.execute_merge_pipeline()` 在本地 `checkout` / `merge --ff-only` 后可选执行任意 shell CI 命令并直接返回成功（`src/macao/merge/controller.py:37-73`）。它没有实现或调用人工签字、`git push`、最终 push 对象等于 `vote_result.checkpoint_ref` 的硬校验、E4a `DONE` / E4b `REWORK` 状态转换或归档；参数 `require_signoff` 未被使用。PRD 要求这些为顺序强制步骤，见 `docs/MACAO_PRD_v2.md:1529-1538`。 | 在不修改目标分支前检查 checkpoint、当前 HEAD、策略和人工签字；将 CI/signoff/push 全部成功后才执行 E4a，任一失败走 E4b 和审计/归档。禁止 `shell=True` 的自由配置命令，至少改为受控 argv/白名单接口。为 checkpoint 漂移、CI 失败、拒签、push 失败与成功 E4a 分别建立临时 Git repo 测试。 |

## P1：进入下一阶段前应修正

| 编号 | 证据 | 修正要求 |
|---|---|---|
| P1-1 artifacts DDL 和写入语义破坏历史审计 | PRD 要求 `artifact_id AUTOINCREMENT`、五元组 `UNIQUE` 和追加归档（`docs/MACAO_PRD_v2.md:1324-1333,1351-1355`）；实现却以五元组为复合主键（`src/macao/storage/db.py:25-38`）并使用 `INSERT OR REPLACE`（`src/macao/storage/store.py:81-90`）。复现：登记→消费→用相同五元组再登记后仅剩一行，且 `consumed=0`、`archived_path=NULL`，历史已被覆盖。 | 按 PRD 迁移为自增 `artifact_id`，禁止 REPLACE；消费和归档分别追加记录并保留原行。Reconciler 还应按 git > 磁盘 > SQLite 的完整优先级恢复，而非只扫描两个固定路径（`src/macao/storage/reconcile.py:32-63`）。 |
| P1-2 申请的格式校验结论不成立 | 申请称 `git diff --check` 为“0 errors”（`docs/reviews/2026-08-27-review-request-Phase0-Phase1-Code.md:110-124`），但 `git diff --check 403ddc7..HEAD` 实际报告多处尾随空白，例如 `src/macao/adapter/pty_session.py:95`、`src/macao/workflow/orchestrator.py:105`、`tests/test_orchestrator_sim.py:110`。 | 清理空白并在提交范围上重跑命令；不要把未通过的格式检查记录为 100% 可复现。 |

## 建议闭环顺序与验收标准

1. 先修 P0-1、P0-2，使“唯一 reviewer、唯一合法转移、唯一终局记录”成为不可绕过的原子流程。
2. 再修 P0-3、P0-4；所有隔离/签字/checkpoint/push 失败必须 fail closed，且目标分支不得发生未批准变更。
3. 完成 artifacts 迁移与恢复测试，清理 `git diff --check`。
4. 重新评审前，至少新增上述 P0 反例测试；仅 22 个既有测试全绿不足以支持 L2/PG-1。

## Reviewer 自审记录

- 按本轮安全/沙箱/存储职责，静态追踪了 worktree、PTY/Adapter、SQLite、Reconcile 与 Merge 路径，并用临时目录复现了非法 FSM 转换、重复 reviewer 计票、Deadlock 预写和 artifacts 覆盖。未执行真实三方 CLI 或联网交互。
