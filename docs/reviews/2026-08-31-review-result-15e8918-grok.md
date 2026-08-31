# MACAO 独立复审报告 — Phase 3 / PG-3 / L4 加固整改申请 (commit `15e8918`)

> **评审人**：grok（独立复审；不采信申请粘贴输出，亦不采信工作区未跟踪的其他专家结论）
> **评审日期**：2026-08-31
> **评审对象**：[`2026-08-31-review-request-Phase3-PG3-L4-Rectification.md`](2026-08-31-review-request-Phase3-PG3-L4-Rectification.md)
> **冻结代码提交**：HEAD `15e89187f122cd0889f849e32d9ade61a76a299d`（短 SHA `15e8918`）
> **冻结差异范围**：申请钉 `3c5ed32..HEAD`；功能闭环主体仍为 `23bb07f`（`23bb07f..HEAD -- src tests` 为空）。`15e8918` 仅新增 `docs/usecases/UC1-init-gemini.md`。
> **对齐基准**：`docs/MACAO_REVIEW_GUIDELINES.md` v1.0（L1–L4 / PG-0–PG-3）
> **证据类型**：DOC / CODE / TEST / SIM / OPS

---

## 〇、Reviewer 自审

本轮强制自检（指引 §9 checklist B/C）：对每一个「真实协同 / 真实签字 / 100% Clean / 已全部闭环」声明，走生产路径反例，而不是停在 CLI 退出码 0。

反例集合：向 `ReviewExtractor` 喂非评审 YAML；未知 CLI / `mock-cli` 构造；临时仓调用 `dispatch_review_in_worktree`；把该方法替换为必抛异常后再跑 `run_live_cycle`；在 `WAITING_REVIEW` + `per_reviewer: 0s` 上跑 `scan_once`；`git diff --check 3c5ed32..HEAD`（申请声明的范围，而非空工作树）。

---

## 一、结论

**不授予 L4 RELEASE-READY，不通过 PG-3。维持既有 L3 SCENARIO-VERIFIED / PG-2（对象仍是 `4e38ed6` 的状态机与 Mock 场景）。**

指引 §2.1 / §3.3：L4 = L3 + **人工接管路径实机演练** + **回归无 P0/P1** + **用户手册齐备** + **OPS VERIFIED**。

`23bb07f` 已物理修掉提取器默认赞成、daemon 活任务崩溃、dispatcher Git API 错名。这些本轮独立复现为 **VERIFIED**。申请用来证明「生产级真实协同 / 真实操作员签字」的 `macao live-run` **仍由 runner 代写三张 YES、自动写入 `HUMAN_MERGE_APPROVED`，且从不调用 `dispatch_review_in_worktree`**。把 dispatcher 打成必抛异常后，`run_live_cycle` 仍 `PASS` / `DONE`，`calls=0`，耗时 0.65s。申请「所有阻断性问题已全部实测闭环」为 **CONTRADICTED**。

另：申请范围 `3c5ed32..HEAD` 的 `git diff --check` **rc=2**（`15e8918` 引入 `UC1-init-gemini.md` 尾随空白），「100% Clean」不成立。

---

## 二、申请声明逐条独立复核

| 声明 | 独立复核 | 判定 |
|---|---|---|
| P1-1 / P1-NEW-13 / P1-Q6：Extractor Fail-Closed | 5 款垃圾/回声 YAML 全部 `ok=False`；错 `checkpoint_ref` 拒绝。`live_dispatcher.py:72-85,100-107`。 | **VERIFIED** |
| P1-2 / P1-NEW-14 / P1-Q5：daemon 活任务超时降级 | 独立：`WAITING_REVIEW` → `scan_once` `TIMEOUT_DEGRADATION`，2×`REVIEWER_TIMEOUT_ABSTAIN`，状态 `CONSENSUS_CHECK`（无 `HOLD` 枚举）。仓库根 `daemon --once` 仍是 `active_task=None` 空转。 | **CODE/SIM VERIFIED**；CLI 空转证据 **PARTIALLY_VERIFIED** |
| P1-3 / P1-NEW-15 / P1-Q4：live-run 真实协同与真实操作员签字 | 见 §四 P1-1。`feature/calc-live`、Extractor 调用、归档 5 份 PERSISTED、真实计时属实；开发/票/签字仍合成。 | **CONTRADICTED**（「真实」） |
| P1-4：`create_isolated_worktree` + 未知 CLI Fail-Closed | `create_isolated_worktree=True`；未知 CLI → `ValueError`（`:140`，申请误钉 `:215`）。opencode 2s 派发 `TIMEOUT`，worktree 已删。`mock-cli` 构造 `TypeError`（缺 `cli_name`）。`src/` 与 `tests/` **零调用** `dispatch_review_in_worktree`。 | **接线 VERIFIED**；OPS 演练 **未闭环** |
| P2-NEW-8：向导单测不依赖 PATH | `assertIsInstance(clis, list)`。 | **VERIFIED** |
| gitignore 六项隔离 | 独立 6 项均写入且幂等。单测只断言 worktrees / `.reviews/`（`test_phase3.py:135-136`）。 | **CODE VERIFIED**；测试覆盖 **PARTIALLY_VERIFIED** |
| 75 tests 100% PASS | `Ran 75 tests in 22.271s OK`。 | **VERIFIED** |
| compileall + `git diff --check` 100% Clean | `compileall` rc=0。工作树 `git diff --check` rc=0（无未提交 diff）。申请范围 `git diff --check 3c5ed32..HEAD` **rc=2**：`docs/usecases/UC1-init-gemini.md:3-5` trailing whitespace。 | compileall ✅；洁净度 **CONTRADICTED** |
| live-run 7 步全绿、5/5 PERSISTED、DONE | CLI 退出 0，报告 7 步 OK、归档 PERSISTED、DONE。故障注入证明 dispatcher 未被调用。 | 退出码 **VERIFIED**；真实协同 **CONTRADICTED** |
| `daemon --once` 正常扫描 | `{'active_task': None, 'action_taken': 'NONE'}` exit 0。 | 空转 **PARTIALLY_VERIFIED** |
| Schema `team.name` / `agmsg_member_id` | `src/macao/schemas/macao_config.schema.json` 字段存在。 | **CODE VERIFIED** |
| 手册齐备且与定级一致 | README 徽章写 **L4 RELEASE-READY** 与 **72/72**（实测 75，L4 未授予）；`live-run` 写成生产级真实协同；`main.py:394` docstring 写 `L4 Ready`。 | 手册存在；定级表述 **CONTRADICTED** |

独立反例摘要：

```text
extractor garbage/echo -> ok=False
create_isolated_worktree=True; unknown CLI -> ValueError
mock-cli -> TypeError missing cli_name
opencode dispatch 2s -> TIMEOUT, worktree leftover=False
boom(dispatch_review_in_worktree)+run_live_cycle -> PASS DONE calls=0 dur=0.65 archived=5 signoffs=1
note="Human operator verified consensus and approved merge" (auto)
live_runner.py: dispatch_review_in_worktree=False simulated_cli_output=True
daemon 0s timeout -> CONSENSUS_CHECK TIMEOUT_DEGRADATION abstain=2
gitignore 6 entries present; min_effective_votes=3 vs 2/3_majority
75/75 OK; compileall 0; git diff --check 3c5ed32..HEAD rc=2
```

---

## 三、P0

未发现需单列的 P0。

---

## 四、P1：进入 L4 / PG-3 前必须解决

### P1-1：`live-run` 仍是合成协同；自动签字被写成「操作员已核实」，不满足 L4 人工接管 / OPS

**验证状态**：CONTRADICTED

**证据**：

1. `src/macao/workflow/live_runner.py:94-119`：runner 自写 `math_lib.py`、自提交、自写 `.dev.yml`，无 Executor CLI。
2. 同文件 `:140-164`：内嵌 `simulated_cli_output`（三张合法 `YES_APPROVE`）再交给 `ReviewExtractor`——校验的是自己刚写的 YAML。
3. `grep`：`dispatch_review_in_worktree` 仅定义于 `live_dispatcher.py:144`；`tests/` 零匹配。步骤 4 标题「Worktree Dispatch」实际调用 `orchestrator.dispatch_review_requests`。
4. 独立故障注入：替换 `dispatch_review_in_worktree` 为必抛异常后 `run_live_cycle()` → `status=PASS`、`final_state=DONE`、`calls=0`、`archived=5`、`dur=0.65`、`signoffs=1`。
5. `:174-180` 自动 `HUMAN_MERGE_APPROVED`，`signer=operator`，`note="Human operator verified consensus and approved merge"`。无人参与。`main.py:406` 仍打印「100% success」。
6. 指引 §2.1 L4、§3.3 OPS：无 `macao override resolve` 实机记录。`live-run` 约 3s 结束，与三路真实 CLI 评审物理不相容。

**验收**（与上轮对 `3c5ed32` 的 P1-4 同一标准）：

- 每个 Reviewer 必须经 `dispatch_review_in_worktree`（或等价生产 dispatcher）建隔离 worktree、拉起 Adapter；runner 禁止代写 `.review.yml`、禁止自动 `HUMAN_MERGE_APPROVED`。
- 合成路径须改名（如 `mock-run`），并去掉 README / STATUS / CLI 的 L4 / 真实 / 操作员签字表述。
- 另附一次超时或僵局 → `CONSENSUS_CHECK` → `macao override resolve` 的用户可见 OPS 记录。若用 `mock-cli` 自证，须先修构造契约（P2-1）。

---

## 五、申请清单中其余阻断项（本轮独立确认，不作为本轮否决理由）

| 申请闭环项 | 本轮状态 | 证据 |
|---|---|---|
| Extractor 缺票默认赞成 | **CLOSED** @ `23bb07f` | 独立垃圾 YAML 全拒绝 |
| daemon 活任务崩溃 / 契约错配 | **CLOSED** @ `23bb07f` | 独立活跃超时 → ABSTAIN + CONSENSUS_CHECK |
| dispatcher `create_worktree` API | **CLOSED** @ `23bb07f` | 已接 `create_isolated_worktree`；未知 CLI `ValueError` |
| live-run 合成 / 自动签字 | **OPEN**（本轮 P1-1） | 见 §四 |
| 向导 PATH 解耦 | **CLOSED** | `assertIsInstance` |
| gitignore 产物隔离 | **CLOSED**（代码） | 独立 6 项在；测试只查 2 条 → P2-2 |

---

## 六、P2 / P3

| ID | 说明 |
|---|---|
| P2-1 | 注册表含 `mock-cli`，构造缺 `cli_name` → `TypeError`。免额度 dispatcher 自证路径不可用。 |
| P2-2 | gitignore 单测只断言 2/6 项，申请「验证 6 项」过宽。 |
| P2-3 | `generate_smart_config`：`min_effective_votes=len(reviewers)`（3=全票）与 `2/3_majority` 冲突。 |
| P2-4 | README 徽章 `L4 RELEASE-READY` 与 `72/72`；`main.py:394` 写 `L4 Ready`。评审未结束即预授。 |
| P2-5 | `live_runner` 读 `require_signoff`，向导写入 `merge.require_human_signoff`，键名分裂；缺省 True 导致永远自动签字。 |
| P2-6 | 申请范围 `git diff --check 3c5ed32..HEAD` rc=2（`UC1-init-gemini.md:3-5` 尾随空白）。「100% Clean」被证伪。 |
| P2-7 | `run_loop` 异常只写 stderr 后继续转；dispatcher 读文件 `except Exception: pass`（`live_dispatcher.py:225-226`）。 |
| P2-8 | `src/` + `tests/` 无任何 `dispatch_review_in_worktree` 调用。 |
| P3-1 | 申请把 CLI 准入钉在 `live_dispatcher.py:215`（实为 `:140`）；「进入 HOLD」无对应枚举（实际 `CONSENSUS_CHECK`）。 |
| P3-2 | `STATUS.md:7` 当前申请对象仍指向旧文件 `Phase3-PG3-L4.md`。 |

---

## 七、L4 / 场景对账

| L4 条件 | 状态 |
|---|---|
| 继承 L3 | **维持**（75/75；`src/tests` 自 `23bb07f` 无再变） |
| 人工接管实机演练 | **CONTRADICTED**（自动 `HUMAN_MERGE_APPROVED`，无 `override resolve` OPS） |
| 回归无 P0/P1 | **不成立**（本轮 1×P1） |
| 用户手册齐备 | PARTIALLY_VERIFIED（FAQ/README 在；L4/72 测/真实协同过宽） |
| OPS VERIFIED | **CONTRADICTED**（dispatcher 生产派发未被 live-run 或测试执行） |

---

## 八、门禁判定

| 级别/门禁 | 判定 |
|---|---|
| L3 / PG-2 | **维持** |
| L4 RELEASE-READY | **不通过** |
| PG-3 | **不通过**（绑定 L4） |

---

## 九、建议闭环顺序

1. 把 `live-run` 接到真实 `dispatch_review_in_worktree`（或改名为 mock 并改文档）；删除内嵌 YAML 与自动签字。
2. 补超时/僵局 → `macao override resolve` 的用户可见 OPS 记录后再申请 L4。
3. 修 mock-cli 构造、`min_effective_votes`、README 徽章、`UC1-init-gemini.md` 尾随空白。
4. 给 dispatcher 加一条临时 git 仓上的 `worktree add` / Fail-closed / `finally` 删除测试。

---

## 十、Known issues

| issue_id | 严重度 | resolution_commit | status |
|---|---|---|---|
| 3C5ED32-P1-1 Extractor 默认赞成 | P1 | `23bb07f` | **CLOSED** |
| 3C5ED32-P1-2 dispatcher Git API | P1 | `23bb07f` | **CLOSED** |
| 3C5ED32-P1-3 daemon 活任务崩溃 | P1 | `23bb07f` | **CLOSED** |
| 15E8918-P1-1 live-run 合成 / 自动签字 | P1 | 待补 | **OPEN** |
| 15E8918-P2-1 … P2-8 | P2 | 待补 | OPEN |
| 15E8918-P3-1 … P3-2 | P3 | 待补 | OPEN |
