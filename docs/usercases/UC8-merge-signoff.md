# UC-8 合并与签字（`MERGING` 流水线 → `DONE`）

- **设计日期**：2026-09-01
- **设计人**：glm
- **状态**：用例设计稿（待实现；实现前须过 Schema/测试对账）
- **关联**：PRD v2.5 §3.3（E4/E4a/E4b）、§14.5（Merge Policy）、§15.1；`execute_merge`（orchestrator.py:700）、Merge Controller 五道关卡；FAQ Q12/Q16。
- **边界声明**：`MERGING` 合的是 **git**（ff/CI/签字/push），不是"合并评审意见"（那是 UC-5 计票 + UC-6 采纳已完成的）。**评审对象 = 合并对象**：`checkpoint_ref` 硬绑定，任何产生新 commit 的操作（rebase/amend/cherry-pick/解冲突改动）都判为未评审新对象 → E4b。

---

## 1. 前置条件

| # | 条件 | 不满足时的行为 |
|---|---|---|
| P1 | 任务 `MERGING`（E4：decision=APPROVED 或 E7 裁定 APPROVED） | E1 |
| P2 | `vote_result.json.checkpoint_ref` == 待合并分支 HEAD（期间无新 commit） | E4b（硬校验） |
| P3 | target 分支检出成功且与远端不冲突（或纯本地） | A3 |

## 2. 主成功场景（五道关卡顺序执行，任一失败 → E4b）

### 关卡 1：检出与上游同步

检出 `target_branch`；确认 `source` 仍可对 target ff（或按 `merge.strategy: no_ff`）。**E4a 硬校验前置**：自 E4 起至 push，工作区不得产生任何新 commit——rebase/amend 一律判 E4b（`rebase_before_merge` MVP 禁用，v1.1 受控门禁三条件见 PRD §14.5）。

### 关卡 2：技术合并

`ff_only`（默认）合并；**Git Conflict** → 不自动解冲突（解冲突产生的改动=新变更=未评审），转 UC-7 P6 管理员裁定：人工解冲突后按新 commit 走 E4b 增量复审，或 CANCEL。

### 关卡 3：CI gate

`merge.ci_gate_command` 非空则执行；失败 → E4b（`REWORK_REQUEST` 注明 CI 失败原因）；命令为空则跳过（可选关卡）。

### 关卡 4：人工签字（默认强制）

`require_human_signoff: true`（保守默认）→ 推送前 `macao merge approve [--note]`。签字是**发布放行**语义，与 `override resolve`（异常裁定）不同（PRD §14.2）。拒绝 → E4b。自动化演练场景用 `--auto-signoff` 时必须诚实标注 `signer: system-runner`（Phase 3 已实现的诚实机制，禁止伪装人类）。

### 关卡 5：推送与通告（E4a）

push 前**最终硬校验**：待推对象 == `vote_result.checkpoint_ref`（字节级）；push 成功 → E4a → `DONE`：发 `MERGE_COMPLETED`（含 merge_commit）；本轮全部产物提升至 canonical evidence ref（`refs/macao/evidence/<task_id>/r<round>`）并归档至 `.macao/archive/<ref>/r<round>/`，不污染 source 分支 HEAD；agmsg 通告全员（结果 + 归档路径）。

### 完成提示

`next_action=PROMPT_TASK_CREATE`（下一单）；`agent_registry` 全员 `AWAIT_TASK`。

## 3. 备选流

| # | 场景 | 行为 |
|---|---|---|
| A1 | 签字人同时是 executor 席位 | 允许（管理员身份）；审计区分 `signer` 身份来源；`require_human_signoff` 语义是"人类放行"而非"第三方放行" |
| A2 | CI gate 可选且未配置 | 跳过关卡 3，其余不变 |
| A3 | 远端不可达（本地/个人仓库场景） | push 关卡降级为本地 merge 完成 + 审计 `PUSH_SKIPPED_LOCAL`；共享仓库场景（分支保护）不在 MVP（PRD §14.5） |
| A4 | 已 push 后发现事故 | git revert 回滚；事件入审计（PRD §14.5 第 6 步）；不撤销 DONE |

## 4. 异常流

| # | 场景 | 行为 |
|---|---|---|
| E1 | 状态非 `MERGING` | 拒绝合并命令 |
| E2 | push 前发现 ref 漂移（P2 破坏） | **不合并**；E4b 增量复审（round+1）；审计 `CHECKPOINT_DRIFT` |
| E3 | CI/push 失败可重试性判断 | 可自动重试的瞬时错误重试一次（指数退避）；其余 → E4b |
| E4b | 任一关卡失败 | → `REWORK`（round+1）；`REWORK_REQUEST` 注明失败关卡与原因；本轮产物归档 |
| E4c | 签字被拒 | 同 E4b；审计 `MERGE_SIGNOFF_REJECTED`（含 note） |

## 5. 后置条件

- **成功（E4a）**：target 含合并结果；merge_commit 入审计；归档目录完整（含 sha256 清单）；`DONE` 终态。
- **失败（E4b）**：target 不变（合并未 push 即回滚工作区）；任务 `REWORK`；归档本轮现场；无半合并状态残留。

## 6. 验收标准（可测）

1. 五关卡顺序 + 单关卡注入失败（fixture：CI 非零退出、签字拒绝、冲突仓库、ref 漂移）各自 → E4b 且 target HEAD 不变
2. ref 漂移检测：E4 后注入新 commit → push 前硬校验拦截（E2）
3. 签字：默认无 `merge approve` 不 push；`--auto-signoff` 审计 `signer=system-runner`（诚实性断言）
4. 归档完整性：E4a 后归档目录文件清单与 sha256 对账零差集
5. `MERGING` 与 `DONE` 区分：push 完成才 DONE；中断停在 `MERGING` 可重入（幂等续跑）

## 7. 实现落点

| 位置 | 变更 |
|---|---|
| `src/macao/merge/controller.py` + `orchestrator.py:execute_merge` | 关卡顺序化、E2 漂移硬校验、A3 本地降级、E3 重试策略 |
| `src/macao/cli/main.py:merge approve` | 签字审计细化（身份来源、note） |
| `tests/` | 第 6 节 |

## 8. 设计自审

- "MERGING 合的是 git 不是意见"贯穿：任何试图在流水线内"再消化评审意见"的实现都是越界
- 评审对象=合并对象（哈希级）是审计链不可断裂的根约束，关卡 1 与关卡 5 双重把守
- 遗留决策点：①`no_ff` 策略下的 merge_commit 与 checkpoint_ref 关系表述；②v1.1 受控 rebase 门禁的 `range-diff` 集成；③push 重试上限
