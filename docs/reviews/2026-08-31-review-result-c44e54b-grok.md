# MACAO 独立复审报告 — Phase 3 / PG-3 / L4 加固整改申请 (commit `c44e54b`)

> **评审人**：grok（独立复审；不采信申请粘贴输出，亦不采信其他专家票数）
> **评审日期**：2026-08-31
> **评审对象**：[`2026-08-31-review-request-Phase3-PG3-L4-Rectification.md`](2026-08-31-review-request-Phase3-PG3-L4-Rectification.md)
> **冻结代码提交**：HEAD `c44e54bfccee798b6be1d9c906e2db1861015ffb`（短 SHA `c44e54b`）
> **冻结差异范围**：`3c5ed32..c44e54b`；功能闭环主体为 `23bb07f`
> **对齐基准**：`docs/MACAO_REVIEW_GUIDELINES.md` v1.0（L1–L4 / PG-0–PG-3）
> **前序对象**：上轮 grok 对 `3c5ed32` **REJECT L4**，维持 L3/PG-2；本轮只核验申请声称已闭环的阻断项，以及 L4 硬条件是否新满足
> **证据类型**：DOC / CODE / TEST / SIM / OPS

---

## 〇、Reviewer 自审

上轮四项 P1 的验收标准写在 `2026-08-31-review-result-3c5ed32-grok.md` §四 / §八，本轮按**同一标准**复验，禁止把「单测绿 + live-run 打印 DONE」升格为 OPS VERIFIED（checklist **B** / **C**）。

强制自检仍走生产路径反例：向 `ReviewExtractor` 喂非评审 YAML；在临时仓调用 `dispatch_review_in_worktree`；在 `WAITING_REVIEW` 上跑 `OrchestratorDaemon.scan_once`；把 `dispatch_review_in_worktree` **替换为必抛异常**后再跑 `run_live_cycle`。

该自检确认上轮 P1-1 / P1-2 / P1-3（提取器默认赞成、dispatcher Git API、daemon 活任务崩溃）已物理闭环；**P1-4 / P1-NEW-15 / P1-Q4（live-run 合成协同 + 自动签字冒充人工接管）未闭环**，且签字文案比上轮更具误导性。

---

## 一、结论

**不授予 L4 RELEASE-READY，不通过 PG-3。维持既有 L3 SCENARIO-VERIFIED / PG-2（对象仍是 `4e38ed6` 的状态机与 Mock 场景）。**

指引 §2.1 / §3.3：L4 = L3 + **人工接管路径实机演练** + **回归无 P0/P1** + **用户手册齐备** + **OPS VERIFIED**。本轮增量把提取器、daemon、worktree API 三条代码阻断修掉了，但申请用来证明「生产级真实协同 / 真实操作员签字」的 `macao live-run` 仍由 runner 代写三张 `YES_APPROVE`、自动写入 `HUMAN_MERGE_APPROVED`，且 **从不调用** `LiveAgentDispatcher.dispatch_review_in_worktree`。把 dispatcher 打成必抛异常后，`run_live_cycle` 仍 `PASS` / `DONE`，`dispatcher_calls=0`，耗时 0.41s。

这不满足 L4 的 OPS 与人工接管硬条件；申请「所有阻断性问题已全部实测闭环」为 **CONTRADICTED**。

---

## 二、申请声明逐条独立复核

| 声明 | 独立复核 | 判定 |
|---|---|---|
| P1-1 / P1-NEW-13 / P1-Q6：`ReviewExtractor` Fail-Closed，缺票不再默认赞成 | 独立 7 款垃圾/回声 YAML 全部 `ok=False`。`status: APPROVED` 显式映射 `YES_APPROVE`；`status: REJECTED` 映射 `NO_APPROVE`。错 `checkpoint_ref` / `reviewer.id` 拒绝。`vote.py:97-99` 与 `orchestrator.py:564-566` 空 vote 为 `continue`，不再补 `YES_APPROVE`。 | **VERIFIED**（上轮 P1-1 闭环） |
| P1-2 / P1-NEW-14 / P1-Q5：daemon 活任务超时降级 | 独立构造 `per_reviewer: 0s` 的 `WAITING_REVIEW`：`scan_once` → `TIMEOUT_DEGRADATION`，2 条 `REVIEWER_TIMEOUT_ABSTAIN`，`DEADLOCK_DETECTED.reason=TIMEOUT_ESCALATION`，状态停在 `CONSENSUS_CHECK`（不自动 MERGING），二次扫描不崩溃。`run_loop` 异常写 stderr。申请写「进入 HOLD」——仓库 **无 `HOLD` 枚举**，实际是 CONSENSUS_CHECK 等待人裁，语义对、用词不准。仓库根目录 `daemon --once` 仍是空转（`active_task=None`），不能单独当 OPS。 | **CODE/SIM VERIFIED**（上轮 P1-3 闭环） |
| P1-3 / P1-NEW-15 / P1-Q4：`live-run` 真实协同、Extractor 强校验、真实操作员签字 | 见 §四 P1-1。`feature/calc-live` 与 Extractor 调用、归档 5 份 PERSISTED、真实 `time.time()` 耗时均属实，但开发/评审/签字仍由 runner 合成。 | **CONTRADICTED**（「真实协同 / 真实签字」） |
| P1-4：dispatcher 接 `create_isolated_worktree`；未知 CLI Fail-Closed | `hasattr(GitManager,"create_isolated_worktree")=True`；`create_worktree` 仍不存在且已不再调用。未知 CLI → `ValueError`。独立对 opencode 派发 3s：返回 `TIMEOUT`，worktree 在 `finally` 中删除（`git worktree list` 仅主仓）。注册表含 `mock-cli`，但 `MockAgentAdapter.__init__` 需要 `cli_name`，`get_adapter_for_reviewer({"cli":"mock-cli"})` → `TypeError`。`src/` / `tests/` 中 **`dispatch_review_in_worktree` 零调用方**。申请把准入写在 `live_dispatcher.py:215`，实际 `ValueError` 在 `:140`。 | **CODE 接线 VERIFIED**；mock 准入与 OPS 演练 **未闭环** |
| P2-NEW-8：向导单测不依赖 PATH | `test_wizard_probes_and_smart_config` 改为 `assertIsInstance(clis, list)`。 | **VERIFIED** |
| `.gitignore` 六项隔离 | 独立调用 `ensure_gitignore_isolation`：worktrees / `.reviews/` / `.dev.yml` / `vote_result.json` / `archive/` / `*.db*` 全部写入且二次调用幂等。单测只断言前两项，申请「验证 6 项」过宽。 | **CODE VERIFIED**；测试覆盖 **PARTIALLY_VERIFIED** |
| 75 tests / compileall / diff-check 100% Clean | 独立：`Ran 75 tests in 21.316s OK`；`compileall` rc=0；`git diff --check` 工作树与 `3c5ed32..HEAD` 均为 rc=0。上轮 trailing whitespace 已不在本范围。 | **VERIFIED** |
| `live-run` 7 步全绿、5/5 PERSISTED、DONE | 独立 CLI：退出 0，7 步 OK，归档 5 份 PERSISTED，终态 DONE。证明力止于「合成路径的 FSM 仍绿」。 | 退出码 **VERIFIED**；「真实协同」**CONTRADICTED** |
| `daemon --once` 正常扫描 | 本仓库空闲扫描 exit 0。活跃路径见上行独立 SIM，不由这条命令证明。 | **PARTIALLY_VERIFIED** |
| `preflight` 6 款 CLI 全绿 | Git/SQLite + claude-code/codex/opencode/agy/cursor/kimi + mock-cli 均 OK。 | **VERIFIED** |
| `test-clis` PTY / ANSI / 0 僵尸 | 本机仍 **4/4**（claude/codex/opencode/agy），0 zombie。申请未再写 6/6，此项与表述一致。 | **VERIFIED**（4 路 `--version` 冒烟，非真实评审会话） |
| Schema `team.name` / `agmsg_member_id` | `src/macao/schemas/macao_config.schema.json:28,35,47` 与 `docs/schemas/` 对应字段存在。 | **CODE VERIFIED** |
| README / FAQ 齐备且与定级一致 | README 徽章写 **L4 RELEASE-READY** 与 **72/72**（实际 75，且 L4 未授予）；`live-run` 被写成「生产级多 Agent 真实协同」。 | 手册存在；定级/协同表述 **CONTRADICTED** |

独立反例摘要：

```text
extractor garbage/echo YAML -> ok=False (7/7)
status-only APPROVED -> YES_APPROVE; REJECTED -> NO_APPROVE
mismatch ref/id -> rejected
create_isolated_worktree=True; unknown CLI -> ValueError
mock-cli construct -> TypeError missing cli_name
opencode dispatch 3s -> TIMEOUT, worktree cleaned
boom(dispatch_review_in_worktree) + run_live_cycle -> PASS DONE dispatcher_calls=0 duration=0.41s
HUMAN_MERGE_APPROVED note="Human operator verified consensus and approved merge" (auto)
live_runner.py contains simulated_cli_output, math_lib.py; NOT dispatch_review_in_worktree
daemon active 0s timeout -> CONSENSUS_CHECK + 2 ABSTAIN + TIMEOUT_ESCALATION
gitignore 9 entries present; min_effective_votes=3 with consensus_rule=2/3_majority
75/75 OK; compileall 0; git diff --check 0
test-clis 4/4; preflight 6 CLI + mock OK
```

---

## 三、P0

未发现需单列的 P0。

---

## 四、P1：进入 L4 / PG-3 前必须解决

### P1-1：`live-run` 仍是合成协同；自动签字被改写成「操作员已核实」，不满足 L4 人工接管 / OPS

**验证状态**：CONTRADICTED

**证据**：

1. `src/macao/workflow/live_runner.py:94-119`：runner 自己写 `src/math_lib.py`、自己提交、自己写 `.dev.yml`，无 Executor CLI。
2. 同文件 `:140-164`：为每个 reviewer **内嵌** `simulated_cli_output`（三张合法 `YES_APPROVE`），再交给 `ReviewExtractor`。这只证明提取器能解析**自己刚写的合法 YAML**，不是 CLI 产出。
3. 全仓 `grep dispatch_review_in_worktree`：定义仅在 `live_dispatcher.py:144`；`live_runner.py` 源码不含该调用。步骤 4 标题为「Worktree Dispatch」，实际走的是 `orchestrator.dispatch_review_requests`（消息总线），不是隔离 worktree + PTY。
4. 独立故障注入：将 `LiveAgentDispatcher.dispatch_review_in_worktree` 替换为必抛异常后 `run_live_cycle()` → `status=PASS`、`final_state=DONE`、`dispatcher_calls=0`、`archived_count=5`、`duration=0.41`。
5. `:174-180` 在 `require_signoff` 缺省为 True 时自动 `log_audit_event(..., "HUMAN_MERGE_APPROVED", {signer: "operator", note: "Human operator verified consensus and approved merge"})`。上轮文案是 `Live runner auto-signoff`；本轮改成看起来像真人签字，**没有人参与**。CLI 成功文案仍是「100% success」（`main.py:406`）。
6. 指引 §2.1 L4、§3.3 OPS：要求用户可见的人工接管演练。本轮无 `macao override resolve` 实机记录；超时 HOLD 路径（daemon 已能到达 `CONSENSUS_CHECK`）从未接到人裁。`macao live-run` 约 1.5s 结束，与三路真实 CLI 评审物理不相容。

申请表把本项写成「真实协同流程重塑 / 真实操作员签字 / 7 步全绿实机演练」——命令通过，证明力与上轮相同：旧 FSM 在自产三张赞成票后可以 DONE。

**验收**（与上轮 P1-4 同一标准，不得用 Extractor 自测代替）：

- 每个 Reviewer 必须经 `dispatch_review_in_worktree`（或等价生产 dispatcher）创建隔离 worktree、拉起 Adapter、消费上下文；runner 禁止代写 `.review.yml` / 禁止自动 `HUMAN_MERGE_APPROVED`。
- 合成 runner 须改名（如 `mock-run`），并改掉 README / STATUS / CLI「Live / L4 / 100% 真实 / 操作员签字」表述。
- 另附一次用户可见的 `WAITING_REVIEW` 超时或僵局 → `CONSENSUS_CHECK` → `macao override resolve` 实机记录（命令、状态、票面、审计）。`mock-cli` 若继续作为免额度自证路径，必须先修构造契约（见 P2-1）。

---

## 五、上轮 P1 闭环登记（本轮独立确认，不作为本轮否决理由）

| 上轮 ID | 本轮状态 | 证据 |
|---|---|---|
| 3C5ED32-P1-1 提取器默认赞成 | **CLOSED** @ `23bb07f` | 独立 7 反例全拒绝；显式 status 仍可映射 |
| 3C5ED32-P1-2 dispatcher `create_worktree` | **CLOSED** @ `23bb07f` | 改为 `create_isolated_worktree`；opencode 短超时路径可建/删 worktree；未知 CLI `ValueError` |
| 3C5ED32-P1-3 daemon 活任务崩溃 | **CLOSED** @ `23bb07f` | 复用 `detect_timed_out_reviewers`；独立活跃超时 → ABSTAIN + TIMEOUT_ESCALATION + CONSENSUS_CHECK |
| 3C5ED32-P1-4 live-run 合成 / 自动签字 | **OPEN**（本轮 P1-1） | 见 §四 |
| 3C5ED32-P2-1 gitignore 产物 | **CLOSED**（代码） | 独立 9 条规则均在；测试只查 2 条 → 本轮 P2-2 |
| 3C5ED32-P2-2 `git diff --check` | **CLOSED**（本范围） | `3c5ed32..HEAD` rc=0 |
| 3C5ED32-P2-3 test-clis 6/6 | 申请不再声称 6/6 | 实测 4/4，与本次申请一致 |
| 3C5ED32-P2-4 `min_effective_votes=len(reviewers)` | **OPEN** → 本轮 P2-3 | 独立 `min_effective_votes=3` 且 `consensus_rule=2/3_majority` |
| 3C5ED32-P2-5 README L4 徽章 / 归档 EMPTY | 归档已绿；徽章仍写 L4 / 72/72 | → 本轮 P2-4 |

---

## 六、P2 / P3

| ID | 说明 |
|---|---|
| P2-1 | 注册表广告 `mock-cli`，但 `get_adapter_for_reviewer` 以 `adapter_cls(agent_id=, config=)` 构造，`MockAgentAdapter` 缺 `cli_name` → `TypeError`。免额度 dispatcher 自证路径不可用。 |
| P2-2 | `test_wizard_probes_and_smart_config` 只 `assertIn` worktrees 与 `.reviews/`，申请「6 项规则注入」无对应断言。 |
| P2-3 | `generate_smart_config` 把 `min_effective_votes` 设为 reviewer 人数（3=全票），与同文件 `2/3_majority` 冲突（上轮 P2-4 未闭）。 |
| P2-4 | README 徽章 `L4 RELEASE-READY` 与 `72/72`；`live-run` 行写成生产级真实协同；`main.py:394` docstring 仍写 `L4 Ready`。评审未结束即预授徽章。 |
| P2-5 | `live_runner` 读 `config["require_signoff"]`，向导写入的是 `merge.require_human_signoff`，键名分裂；缺省 True 导致永远自动签字。 |
| P2-6 | `run_loop` 捕获异常只写 stderr 后继续转；未以非零健康状态退出。dispatcher 读 worktree 文件时 `except Exception: pass`（`live_dispatcher.py:225-226`）。 |
| P2-7 | 显式 `vote: ABSTAIN` + `status: CHANGES_REQUESTED` 被提取成 `NO_APPROVE`（status 分支优先），弃权变成反对，可翻转 2/3。纯 ABSTAIN 则可能过不了 review_manifest 枚举。 |
| P2-8 | `src/` + `tests/` 无任何 `dispatch_review_in_worktree` 调用，worktree+PTY 生产路径零自动化覆盖。 |
| P3-1 | 申请把 CLI 准入钉在 `live_dispatcher.py:215`（实为提取调用）；daemon「进入 HOLD」无对应枚举。 |
| P3-2 | `docs/reference/` 仍混有非 MACAO 评审指南；`STATUS.md:7` 当前申请对象仍指向旧文件 `Phase3-PG3-L4.md`（表内已登记整改申请）。 |

---

## 七、L4 / 场景对账

| L4 条件 | 状态 |
|---|---|
| 继承 L3 | **维持**（75/75 含历轮整改；本轮未击穿既有状态机） |
| 人工接管实机演练 | **CONTRADICTED**（自动 `HUMAN_MERGE_APPROVED`，无 `override resolve` OPS） |
| 回归无 P0/P1 | **不成立**（本轮 1×P1：合成 live-run） |
| 用户手册齐备 | PARTIALLY_VERIFIED（FAQ/README 在；L4/真实协同/72 测过宽） |
| OPS VERIFIED | **CONTRADICTED**（dispatcher 生产派发未被 live-run 或测试执行；daemon 活跃路径仅有 SIM/单测，仓库 `daemon --once` 仍为空转） |

---

## 八、门禁判定

| 级别/门禁 | 判定 |
|---|---|
| L3 / PG-2 | **维持** |
| L4 RELEASE-READY | **不通过** |
| PG-3 | **不通过**（绑定 L4） |

---

## 九、建议闭环顺序

1. **二选一，且必须改文档**：把 `live-run` 接到真实 `dispatch_review_in_worktree`（允许 `mock-cli`，但须先修 P2-1 构造），**删除** runner 内嵌 YAML 与自动签字；**或**将命令改名为 mock/demo，去掉 README/STATUS/CLI 的 L4/真实/操作员签字表述。
2. 补一条超时或僵局 → `macao override resolve` 的用户可见 OPS 记录后再申请 L4。
3. 修 mock-cli 构造、`min_effective_votes`、README 徽章与测试数、live-run 配置键名。
4. 给 `dispatch_review_in_worktree` 加一条临时 git 仓上的真实 `worktree add` / 失败 Fail-closed / `finally` 删除测试。

---

## 十、Known issues

| issue_id | 严重度 | resolution_commit | status |
|---|---|---|---|
| 3C5ED32-P1-1 | P1 | `23bb07f` | **CLOSED** |
| 3C5ED32-P1-2 | P1 | `23bb07f` | **CLOSED** |
| 3C5ED32-P1-3 | P1 | `23bb07f` | **CLOSED** |
| 3C5ED32-P1-4 / C44E54B-P1-1 | P1 | 待补 | **OPEN** |
| C44E54B-P2-1 … P2-8 | P2 | 待补 | OPEN |
| C44E54B-P3-1 … P3-2 | P3 | 待补 | OPEN |
