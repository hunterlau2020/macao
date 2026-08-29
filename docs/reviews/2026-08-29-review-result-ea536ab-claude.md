# MACAO 全量阻断项闭环与超时单测终局评审（L3 / PG-2）独立复审结论 — claude

- **评审日期**：2026-08-29
- **评审对象**：`docs/reviews/2026-08-29-review-request-L3-All-Items-Closed.md`
- **评审范围（commit）**：`4df059e..ea536ab`（HEAD）
- **评审基准**：`docs/MACAO_REVIEW_GUIDELINES.md`（§2.1 L3 判据、§3.3 证据最低要求、§4 声明验证矩阵、§6 反例场景库、§9 自审 Checklist）、`docs/MACAO_PRD_v2.md` v2.3.1、`docs/schemas/*.schema.json`
- **评审方式**：全部结论均由本人从一手代码 / 数据库 / 实机复现独立推导，不采信申请文档自述，亦不采信 codex / zcode / qwen 既有结论
- **结论**：**不予授予 L3 SCENARIO-VERIFIED / PG-2；维持 L2 / PG-1 待定**
  - 申请清单 8 项中 **6 项完全属实闭环（VERIFIED）**，**2 项为 PARTIALLY_VERIFIED**（REQ-TIMEOUT、P1-2）；
  - 独立发现 **2 项新 P1**（其中 1 项直接证伪申请文档 §机验结果 中的 "5 份物理产物与数据库记录完全匹配"）、**1 项 P2**、**1 项 P3**（证伪 §二 第 5 条 `git diff --check` 洁净度声明）。

---

## 〇、reviewer 自审登记（GUIDELINES §9）

- 本轮激活 checklist **B**（"`[x]` / 已完成 ≠ 已有完成证据"）与 **C**（确定性用语是否为已验证事实）。申请文档中 "100%"、"完全匹配"、"全量闭环" 等表述均被逐条还原为可机验断言核对，其中 2 条被证伪（见 §三）。
- 登记本人上轮（`4df059e` 轮）漏审：我在上轮提出 P1-2（`register_artifact` 无生产调用点）时，只核验了"是否有调用点 / 表是否非空"，**未核验产物追踪链的下半段（`consumed` / `archived_path` / `sha256` 是否正确落库）**。本轮该盲点直接命中新发现 P1-NEW-2 与 P2-NEW-1。

---

## 一、申请清单逐项独立复核

| 编号 | 申请声明 | 独立复核结论 | 证据 |
|---|---|---|---|
| **REQ-TIMEOUT** | 超时 Reviewer 标记弃权 → 死锁 → 人工接管全链路测试证据 | **PARTIALLY_VERIFIED** | 降级逻辑属实（`orchestrator.py:374-388` 合成 `ABSTAIN` + `REVIEWER_TIMEOUT_ABSTAIN` 审计事件；`engine.py:42-56` 有效票 1 < quorum 2 → `DEADLOCK`；`orchestrator.py:395-417` HOLD 且不写盘 + 发布 `HUMAN_OVERRIDE_REQUEST`），`test_reviewer_timeout_degradation_scenario` 断言实质（不写盘 / 状态保持 / 消息类型 / E7 裁定后写盘）。**但"超时判定"本身在生产链路中不存在** → 见 §三 P1-NEW-1 |
| **P0-1** | `task_id` 引入高熵后缀防同秒并发碰撞 | **VERIFIED** | `orchestrator.py:110-113`：`f"task-{date_str}-{uuid.uuid4().hex[:6]}"`（16.7M 熵空间）；`test_task_id_concurrency_no_collision_in_100_tasks` 实测 100/100 唯一。Schema 无 `task_id` pattern 约束（`grep task_id docs/schemas/*.json` 空），格式变更无兼容性破坏 |
| **P0-2** | 达到 max-round 时 HOLD 且绝不提前写盘 | **VERIFIED** | `orchestrator.py:421-441` 的 max-round 守卫位置严格早于 `generate_vote_result(...)`（`:444`），与 DEADLOCK 分支同构，返回 `(None, None)`；`test_max_rework_rounds_reached_holds_without_writing_disk_vote_result` 额外断言崩溃恢复（`StateReconciler.reconcile()`）后状态仍稳固为 `CONSENSUS_CHECK`，非浅断言 |
| **P0-3** | MergeController 拒绝脏工作区（Fail-closed） | **VERIFIED** | `merge/controller.py:60-64`：`git diff --name-only` + `git diff --cached --name-only` 双检，且位置早于 `checkout`（`:67`），故用户未提交改动不会先被 checkout 破坏；`test_merge_controller_refuses_dirty_worktree_fail_closed` 断言拒绝**且**文件内容原样保留 |
| **P1-1** | 补齐 `remove_isolated_worktree` 并物理清理 | **VERIFIED**（本人上轮 P1-NEW-A 已闭环） | `utils/git_utils.py:109-112` 新增方法，委派 `remove_worktree`（`worktree remove --force` + `prune` + `rmtree` 兜底）；`orchestrator.py:259-265` 异常清理路径不再 `AttributeError`；`test_worktree_dispatch_exception_physically_cleans_created_worktrees` 已按我上轮建议**新增磁盘目录不存在断言**（`assertFalse(rev1_wt_path.exists())`），补齐了上轮的覆盖盲点 |
| **P1-2** | 恢复 `register_artifact` 生产调用点 | **PARTIALLY_VERIFIED** | 调用点确已恢复于 3 处 4 个位点（`orchestrator.py:199`/`355`/`455`/`591`）；实机 `e2e-run` 后 `artifacts` 表确有 5 行（dev_manifest×1 / review_manifest×3 / vote_result×1）。**但追踪链下半段被证伪** → 见 §三 P1-NEW-2、P2-NEW-1 |
| **P2-1** | `validate_vote_result` 移至写盘之前 | **VERIFIED** | `consensus/vote.py:174-183`：校验在 `if write_to_disk:` 之前，非法产物不再先污染磁盘 |
| **P2-2** | `human_resolution` 非法输入 Fail-fast | **VERIFIED** | `consensus/vote.py:129-132`：`else: raise ValueError(...)`，静默降级为 `APPROVED` 的安全缺陷已消除；`test_vote_result_validation_before_write_and_fail_fast_on_invalid_resolution` 同时断言异常文案与磁盘无残留 |

### 机验清单复核（申请文档 §二）

| # | 声明 | 实测 | 状态 |
|---|---|---|---|
| 1 | `unittest discover tests -v` 49 ran / 49 PASS | 实测 `Ran 49 tests ... OK` | ✅ 属实 |
| 2 | 5 轮连续全量回归 0 flake | 实测 run1..run5 全部 `OK` | ✅ 属实 |
| 3 | `macao test-clis` 4/4 PASS | 实测 claude-code / codex / opencode / agy 四款全部 `PASS`，0 Zombie / 0 orphan | ✅ 属实 |
| 4 | `macao e2e-run` "7 步 OK，5 份物理产物**与数据库记录完全匹配**" | 实测 7 步 OK、归档 5 份、`artifacts` 表 5 行属实；但**数据库记录与物理产物并不匹配**（3/5 行 `consumed=0`、`archived_path=NULL`，5/5 行 `sha256=''`） | ❌ **部分证伪** → P1-NEW-2 / P2-NEW-1 |
| 5 | `git diff --check` 洁净 | `git diff --check 4df059e..HEAD` 返回码 2，报 `docs/POC_VERIFICATION_REPORT.md:25: trailing whitespace` | ❌ **证伪** → P3-NEW-1 |

---

## 二、已确认的正向结论

1. **无虚假闭环声明**：8 项整改的代码落点与申请文档描述逐条一致，无"改了别处充数"或"改测试不改代码"的情况；新增 5 个回归测试均为实质断言（驱动真实 `Orchestrator` / `MergeController` / `VoteAggregator`，断言状态机终态、磁盘副作用、消息类型与异常文案），非浅层 smoke。
2. **安全不变量未回退**：Worktree 派发事务性（先建全部 worktree 再推进 FSM）、DEADLOCK 不写盘、Merge 全失败分支 `reset --hard pre_merge_head` 原子回滚、`ls-remote` 校验由"能查到才校验"收紧为"查不到即 Fail-closed"（`controller.py:121-127`）——本轮均为**增强**而非放松。
3. **上轮我方两项 P1 已真实闭环**：P1-NEW-A（worktree 物理清理）完全闭环并补齐断言；P1-NEW-B（`register_artifact` 无调用点）主干闭环，剩余问题为其下游链路（见 §三）。

---

## 三、本轮独立新发现

### P1-NEW-1（阻断 L3）：Reviewer 超时在生产链路中**无任何检测机制**，超时场景的真实默认行为是"静默无限挂起"

- **证据 1（参数无生产调用方）**：`grep -rn "timed_out_reviewers" src/ tests/` 结果显示，该参数仅在 `orchestrator.py`（定义/使用）与 `tests/test_p0_p1_rectification.py:97-100`（测试传入）出现。`src/macao/cli/main.py` 与 `src/macao/workflow/e2e_runner.py:232` 的生产调用**均未传入**，且系统中不存在任何计算该列表的代码。
- **证据 2（超时配置为死配置）**：`cli/main.py:61-66` 生成的默认 `macao.yaml` 声明了 `timeouts.per_reviewer: "10m"` / `review_request: "30m"` 等 5 项；`core/config.py:76` 将其原样透出到 runtime config；但 `grep -rn '"timeouts"' src/macao/` 显示**全仓库零消费方**。
- **证据 3（消息 deadline 恒为 NULL）**：`msg/bus.py:20-44` 的 `publish(..., deadline=None)` 支持写入 `message_queue.deadline`，但 `grep -rn "deadline=" src/macao/` 显示 orchestrator 的全部 `publish` 调用**均未传 deadline**，故派发 REVIEW_REQUEST 时不落任何截止时间，事后也无从判定超时。
- **证据 4（实机复现：静默挂起）**：临时 git repo，3 名 reviewer 全部不响应，连续 3 次调用 `collect_and_evaluate_consensus(tid, configured_reviewers=3)`：

  ```text
  call 0 change= None vote= None state= WAITING_REVIEW
  call 1 change= None vote= None state= WAITING_REVIEW
  call 2 change= None vote= None state= WAITING_REVIEW
  audit events: ['STATE_TRANSITION_E1']
  messages: ['DEVELOPMENT_STARTED']
  ```

  任务永久停留 `WAITING_REVIEW`，**无超时审计事件、无 `HUMAN_OVERRIDE_REQUEST`、无任何可观测告警**。
- **判据冲突**：GUIDELINES §2.1 L3 要求"**超时**/弃权/崩溃恢复……均有可复现推演或测试证据"；§6 反例库明列"2-reviewer 1 超时 + 1 批准"与"**人工接管超时后系统的默认动作（是否静默按高置信度状态继续）**"。本轮补齐的是**超时发生之后的降级分支**，而该分支在生产中不可达——测试通过手工投喂 `timed_out_reviewers` 绕过了缺失的触发器。按 §3.3，REQ-TIMEOUT 的 TEST 证据只能判为 `PARTIALLY_VERIFIED`，不足以支撑 L3。
- **建议修复**：(1) `dispatch_review_requests` 落库派发时刻并按 `timeouts.per_reviewer` 计算 deadline（写入 `message_queue.deadline`）；(2) 新增 `Orchestrator.detect_timed_out_reviewers(task_id)` 由 deadline 与 `message_deliveries` ACK 状态推导超时列表，并在 `collect_and_evaluate_consensus` 内部默认调用（参数保留为可选覆盖）；(3) 补一条端到端测试：deadline 已过 → 自动判超时 → ABSTAIN → DEADLOCK → 人工接管，全程不手工传入超时列表。

### P1-NEW-2（阻断）：`reviewer_id` 键不一致，review_manifest 产物**永远无法标记为已消费/已归档**，证伪"数据库记录完全匹配"

- **根因**：注册端 `orchestrator.py:355-362` 写入 `reviewer_id=r["reviewer_id"]`（如 `"codex"`）；归档端 `workflow/fsm.py:105-112` 调用 `mark_artifact_consumed(..., reviewer_id=rev_file.stem)`，而 `rev_file` 为 `codex.review.yml`，**`Path("codex.review.yml").stem == "codex.review"`**（实测确认，`Path.stem` 只剥离最后一个后缀）。`store.py:95-104` 的 `UPDATE ... WHERE ... AND reviewer_id = ?` 因此永不命中。
- **实机复现（完整 `e2e-run` 成功后直查 SQLite）**：

  ```text
  status PASS  tracked 5  archived 5
  {'kind':'dev_manifest',    'reviewer_id':'',            'sha256':'', 'consumed':1, 'archived_path':'.macao/archive/<ref>/r1/.dev.yml'}
  {'kind':'review_manifest', 'reviewer_id':'antigravity', 'sha256':'', 'consumed':0, 'archived_path':None}
  {'kind':'review_manifest', 'reviewer_id':'codex',       'sha256':'', 'consumed':0, 'archived_path':None}
  {'kind':'review_manifest', 'reviewer_id':'opencode',    'sha256':'', 'consumed':0, 'archived_path':None}
  {'kind':'vote_result',     'reviewer_id':'',            'sha256':'', 'consumed':1, 'archived_path':'.macao/archive/<ref>/r1/vote_result.json'}
  ```

  3 份 review manifest 物理上**确已归档**（归档目录 5 份文件），数据库却全部记为未消费、无归档路径 —— 与申请文档"5 份物理产物与数据库记录完全匹配"的声明直接矛盾。
- **影响**：(1) `macao status` 经 `cli/ui.py:80` 对全部 reviewer 产物恒显示 `Consumed: NO`，运维读到的是错误的实时状态；(2) PRD §11.4 的产物审计闭环（注册 → 消费 → 归档）在 reviewer 侧断链，`consumed` 位失去语义；(3) 100% 确定性复现，非概率性问题。
- **测试盲点**：`test_artifacts_registered_and_tracked_in_database` 仅断言 `len(artifacts) >= 4` 与 `kind` 集合，**未断言 `consumed` / `archived_path`**，故该缺陷完整绕过本轮 49 项测试。
- **建议修复**：`fsm.py:111` 改为 `reviewer_id=rev_file.name.split(".")[0]`（或统一由 `.review.yml` 后缀剥离的公共函数产出），并在上述测试中补充 `assertTrue(all(a["consumed"] for a in artifacts))` 与 `archived_path is not None` 断言。

### P2-NEW-1：`artifacts.sha256` 恒为空串，产物完整性审计列已失效

- **根因**：`store.py:82` `sha256 = hashlib.sha256(content).hexdigest() if content else ""`；orchestrator 的 4 个注册点（`:199` / `:355` / `:455` / `:591`）**均未传 `content`**。对照 `git show e7ba2d2:src/macao/storage/store.py`，旧实现会在 `sha256 is None and Path(path).exists()` 时自动读盘计算——该能力在 `4df059e` 的重构中被移除且本轮未补偿。
- **证据**：上节 SQLite 实测，5/5 行 `sha256=''`。
- **影响**：`vote_result.json` 内的 `input_artifacts[].sha256`（`vote.py:52-53` 正常计算）与数据库审计表不一致，无法据库校验归档产物是否被篡改；属 GUIDELINES §4"所有状态转换可审计"声明的实质性弱化。定为 P2（审计弱化，不破坏状态机正确性），但应与 P1-NEW-2 一并修复。
- **建议修复**：在 `register_artifact` 内恢复"`content is None` 且 `path` 存在时读盘计算 sha256"的兜底，或由 orchestrator 各注册点显式传入文件字节。

### P3-NEW-1：`git diff --check` 未洁净，证伪申请文档 §二 第 5 条

- `git diff --check 4df059e..HEAD` 退出码 2，报 `docs/POC_VERIFICATION_REPORT.md:25: trailing whitespace`（E2E 报告表格输出块内的行尾空格）。`src/` 与 `tests/` 洁净。

### 遗留未闭环项（历轮已登记，本轮未触及，非本轮虚假声明）

- `adapter/integ_harness.py:109` `ansi_stripped_ok = True` 仍为无条件常量赋值：第 108 行取到 `clean_logs` 后**从未检查其内容是否残留 ANSI 序列**，`test-clis` 报告中的 `ansi_stripped` 列为橡皮图章。该文件本轮未修改，属跨轮遗留 P2，建议在 L4/OPS 前闭环。

---

## 四、定级建议

| 判据 | 结论 |
|---|---|
| L2 SPEC-CODE-ALIGNED | 满足（枚举/Schema/字段与 PRD v2.3.1 一致，49/49 通过） |
| **PG-1**（L2 + P0/P1 归零） | **暂不满足**：存在 P1-NEW-1、P1-NEW-2 |
| **L3 SCENARIO-VERIFIED** | **不满足**：§2.1 明列的"超时"场景在生产链路不可达（P1-NEW-1），TEST 证据判为 PARTIALLY_VERIFIED |
| **PG-2** | **不予授予**（依赖 PG-1 + 消费方场景测试） |

**授予条件（均为单点小改，预计一轮可闭环）**：

1. 闭环 **P1-NEW-1**：实现基于 `timeouts.per_reviewer` + 派发 deadline 的**真实超时判定**，并补一条不手工传入 `timed_out_reviewers` 的端到端超时测试；
2. 闭环 **P1-NEW-2**：修正 `fsm.py:111` 的 `reviewer_id` 取值，并在产物追踪测试中补 `consumed` / `archived_path` 断言；
3. （建议同轮）闭环 **P2-NEW-1** sha256 兜底与 **P3-NEW-1** 行尾空格；申请文档中"完全匹配""洁净"等确定性表述需按 GUIDELINES §9-C 以实测重新校准后再提交。

以上 1、2 两项闭环并经实机复验后，本人支持授予 **L3 SCENARIO-VERIFIED / PG-2**。

---

## 五、附：本轮复现命令

```bash
# 全量与 5 轮回归
PYTHONPATH=src python3 -m unittest discover tests -v
for i in 1 2 3 4 5; do PYTHONPATH=src python3 -m unittest discover tests | tail -1; done

# 真实 CLI PTY 生命周期
PYTHONPATH=src python3 -m macao.cli.main test-clis

# P1-NEW-2 / P2-NEW-1：E2E 后直查 artifacts 表
PYTHONPATH=src python3 -c "
import sqlite3
from macao.workflow.e2e_runner import ControlledE2ERunner
r = ControlledE2ERunner(); res = r.run_e2e_cycle()
c = sqlite3.connect(str(r.repo_dir/'.macao'/'state.db')); c.row_factory = sqlite3.Row
for row in c.execute('SELECT kind,reviewer_id,sha256,consumed,archived_path FROM artifacts'): print(dict(row))
r.cleanup()"

# P1-NEW-1：无响应 reviewer 导致静默挂起
#   见 §三 P1-NEW-1 证据 4（临时 repo + 连续三次 collect_and_evaluate_consensus）

# P3-NEW-1
git diff --check 4df059e..HEAD
```
