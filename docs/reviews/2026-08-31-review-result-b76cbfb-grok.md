# MACAO 独立复审报告 — Phase 3 / PG-3 / L4 终审验收申请 (commit `b76cbfb`)

> **评审人**：grok（独立复审；不采信申请粘贴输出，亦不采信其他专家票数）
> **评审日期**：2026-08-31
> **评审对象**：[`2026-08-31-review-request-Phase3-PG3-L4-Final.md`](2026-08-31-review-request-Phase3-PG3-L4-Final.md)
> **冻结代码提交**：HEAD `b76cbfb78301476c53bad59219475b84fd6f21ac`（短 SHA `b76cbfb`）
> **冻结差异范围**：申请钉 `15e8918..HEAD`；功能闭环主体 `ac32dbb`（其后 `b76cbfb` 为申请与 STATUS）
> **对齐基准**：`docs/MACAO_REVIEW_GUIDELINES.md` v1.0
> **前序**：grok 对 `15e8918` **REJECT L4**（P1：live-run 不调用 dispatcher、自动签字冒充操作员）。本轮按同一验收标准复验。
> **证据类型**：DOC / CODE / TEST / SIM / OPS

---

## 〇、Reviewer 自审

强制自检（指引 §9 B/C）：生产路径反例，而不是停在 81 测绿与 `live-run` 打印 DONE。

本轮反例：把 `dispatch_review_in_worktree` 换成必抛异常；计数 `create_isolated_worktree`；`auto_signoff=False`；末块/矛盾票/ABSTAIN/垃圾 YAML；gitignore 存量升级；`git diff --check 3c5ed32..HEAD`。

上轮 P1（dispatcher 零调用）在 boom 测试中已被证伪为**已闭环**（现会 `RuntimeError`）。不得因此把 L4 的 OPS/人工接管硬条件一并放过。

---

## 一、结论

**不授予 L4 RELEASE-READY，不通过 PG-3。维持既有 L3 SCENARIO-VERIFIED / PG-2。**

`ac32dbb` 已把上轮 grok P1-1 的核心证伪点修掉：`live-run` **真实调用** dispatcher，为 3 名 Reviewer 创建物理 Git Worktree，mock 适配器可构造，签字文案改为 `system-runner` / `--auto-signoff`。提取器末块优先、矛盾票拒绝、ABSTAIN Schema、gitignore 差量升级、`min_effective_votes=ceil(2n/3)`、diff-check 洁净、81/81 测试，本轮均独立 VERIFIED。

指引 §2.1 / §3.3：L4 仍要求 **用户可见的人工接管实机演练** 且 **OPS VERIFIED**。申请把该硬条件闭环到 `test_manual_override_resolution`：该测试在临时仓手写 `.review.yml`、直接调 `Orchestrator.resolve_override`、再由测试自己写入 `HUMAN_MERGE_APPROVED`（`signer: lead-architect`）。这是 **TEST/SIM**（L3 级路径本就应覆盖僵局/人裁），不是用户可见的 `macao override resolve` OPS。默认 `macao live-run` 仍 `--auto-signoff`，约 1s 走完 mock 全赞成，从不进入 HOLD。

申请「全部阻断项已物理闭环 / 具备生产级鲁棒性」对 dispatcher 接线为真，对 L4 OPS 判据为 **CONTRADICTED**。

---

## 二、申请声明逐条独立复核

| 声明 | 独立复核 | 判定 |
|---|---|---|
| live-run 调用 `dispatch_review_in_worktree`，隔离 worktree 后原子清理 | boom：`calls=1` 后 `RuntimeError`，不再 PASS。正向：3 个路径 `.macao/worktrees/<id>/<task>/r1` 被创建且 `exists=True`，结束后 leftover=[]。`simulated_cli_output` 已删除。 | **VERIFIED**（上轮 P1 接线闭环） |
| `--auto-signoff` 诚实记录 `system-runner` | 独立：`signer=system-runner`，`note=Automated runner signoff (--auto-signoff)`。默认 CLI 仍自动签字。`auto_signoff=False` → `WAITING_SIGNOFF` / `MERGING`。 | **CODE VERIFIED**（不再冒充人类）；默认路径仍无人 |
| mock-cli 构造 + worktree 提取 | `MockAgentAdapter(cli_name="mock-cli")` 成功；未知 CLI `ValueError`；`test_live_dispatcher_worktree_mock_execution` 在 81 测中通过。 | **VERIFIED** |
| Extractor 末块优先、矛盾票拒绝、prompt 含 round/diff | 双块 → 末块 `NO_APPROVE`；`NO+APPROVED` → `ok=False`；opencode/claude/codex/agy/cursor/kimi `inject_task` 均读 `review_round`/`diff`。 | **VERIFIED** |
| Schema 三值 ABSTAIN / ABSTAINED | 独立提取 `vote=ABSTAIN` / `status=ABSTAINED`；`review_manifest.schema.json` enum + allOf 互锁；`OpinionStatus.ABSTAINED` 在 `types.py`。 | **VERIFIED** |
| gitignore 存量升级 9 条 | 仅有 worktrees 的旧文件升级后补齐 `.reviews/`/`*.db*`，worktrees 不重复，二次调用幂等。 | **VERIFIED** |
| `min_effective_votes = ceil(2n/3)` | 3 reviewer → `2`，规则仍 `2/3_majority`。 | **VERIFIED** |
| setup 覆写前备份 | `main.py:361-364`：存在配置且非 `--force` 时写 `macao.yaml.bak.<ts>`，随后仍覆写。无对应单测；`--force` 不备份。 | **CODE PARTIALLY_VERIFIED** |
| README L3 徽章、81/81、FAQ `live-run`、diff-check 0 | 徽章为 **L3 / PG-2**（不再预授 L4）。测试徽章仍是 **75/75**（申请写 81/81）。FAQ 无 `e2e-run`。`git diff --check 3c5ed32..HEAD` **rc=0**。README 仍写 live-run「生产级真实协同」。 | L3 徽章/FAQ/洁净度 **VERIFIED**；81 徽章 **CONTRADICTED** |
| 人工接管 OPS：1 赞成 + 1 反对 + 1 超时 → HOLD → `resolve_override` | `test_manual_override_resolution` 属实（81 测含之）：手写两张票 + `timed_out_reviewers=["agy-rev"]` → `CONSENSUS_CHECK`，Python API `resolve_override("APPROVED")` → `MERGING`，测试内再写 `HUMAN_MERGE_APPROVED`。未调用 CLI `macao override resolve` / `macao merge approve`。 | **TEST VERIFIED**；**OPS / 用户可见演练 CONTRADICTED** |
| 81 tests / compileall / 洁净 | `Ran 81 tests in 21.826s OK`；compileall 0；申请范围 diff-check 0。 | **VERIFIED** |
| `macao live-run` 7 步全绿、5/5 PERSISTED | CLI 退出 0，归档 PERSISTED，DONE。3 路均为 `cli: mock-cli`；开发仍是 runner 写 `math_lib.py`。 | 退出码 **VERIFIED**；「真实 CLI 协同」**PARTIALLY_VERIFIED**（真实 worktree + mock 票） |

独立反例摘要：

```text
boom(dispatch_review_in_worktree) -> RuntimeError calls=1  (no longer PASS)
create_isolated_worktree x6 (orchestrator E2 + dispatcher 各 3 次), leftover=[]
auto_signoff=True -> DONE signer=system-runner
auto_signoff=False -> WAITING_SIGNOFF MERGING
extractor last-block=NO_APPROVE; contradiction ok=False; ABSTAIN ok=True
garbage YAML ok=False
mock-cli constructs; unknown CLI ValueError
min_effective_votes=2 / 3 reviewers
gitignore upgrade missing rules, idempotent
81/81 OK; compileall 0; git diff --check 3c5ed32..HEAD rc=0
README badge tests-75/75 (not 81/81); Gate=L3/PG-2
```

---

## 三、P0

未发现需单列的 P0。

---

## 四、P1：进入 L4 / PG-3 前必须解决

### P1-1：L4 要求的「用户可见人工接管实机演练」仍未被满足；申请用单测外推 OPS

**验证状态**：CONTRADICTED（相对申请「OPS / 人工接管全流程实操」）

**证据**：

1. 指引 §2.1 L4、§3.3：L4 = L3 + **人工接管路径实机演练** + OPS VERIFIED。L3 已覆盖僵局/超时/人裁的 TEST/SIM；把同一条 Python API 再包一层单测，不能使 OPS 升格为 VERIFIED。
2. `tests/test_phase3.py:356-439`：`.reviews/*.review.yml` 由测试 **手写**（不经 dispatcher）；`orch.resolve_override(...)` 而非 `macao override resolve`；随后测试自己 `log_audit_event(..., HUMAN_MERGE_APPROVED, signer=lead-architect)`。这与上轮被否的「脚本代签」同构，只是场景换成了 DEADLOCK。
3. 默认 `macao live-run`（`main.py:402` `default=True`）自动签字后 DONE，约 1s，三票 mock `YES_APPROVE`，**从不进入** `CONSENSUS_CHECK` HOLD。
4. `--no-auto-signoff` 停在 `WAITING_SIGNOFF`/`MERGING`（独立复现），这是**合并签字门**，不是超时/僵局的 `override resolve` 接管。申请声称的 OPS 剧本未作为 CLI 演练出现。

**验收**：

- 用户可见记录一份：活跃任务进入 `CONSENSUS_CHECK`（超时或 1:1+弃权）→ 终端执行 `macao override resolve --choice ...` → 状态/票面/审计可核对；合入若仍要求签字则走 `macao merge approve`，禁止测试或 runner 代写 `HUMAN_MERGE_APPROVED` 冒充操作员。
- 申请与 STATUS 不得把 `test_manual_override_resolution` 标成 OPS 闭环。

---

## 五、上轮 grok 项闭环登记

| 上轮 ID | 本轮状态 | 证据 |
|---|---|---|
| 15E8918-P1-1 dispatcher 零调用 / 合成 YAML | **CLOSED** @ `ac32dbb` | boom 必失败；3 个物理 worktree |
| 15E8918-P1-1 冒充 Human operator 签字 | **CLOSED**（诚实 auto-signoff） | `system-runner`；L4 接管另见本轮 P1-1 |
| 15E8918-P2-1 mock-cli `cli_name` | **CLOSED** | 独立构造成功 |
| 15E8918-P2-2 gitignore 测试覆盖 | **CLOSED** | 存量升级单测 + 独立复现 |
| 15E8918-P2-3 `min_effective_votes=n` | **CLOSED** | 现为 2 |
| 15E8918-P2-4 README L4 预授 | **CLOSED** | 徽章改 L3/PG-2；测试数徽章仍错 |
| 15E8918-P2-6 UC1 尾随空白 | **CLOSED** | 申请范围 diff-check rc=0 |

---

## 六、P2 / P3

| ID | 说明 |
|---|---|
| P2-1 | README 测试徽章仍为 `75/75`，申请/STATUS 写 81/81。`live-run` 行仍写「生产级多 Agent **真实**协同」，实际 Reviewer 全是 `mock-cli`，Executor 仍是 runner 写 `math_lib.py`。 |
| P2-2 | `orchestrator.dispatch_review_requests` 与 `LiveAgentDispatcher` **各**调用一次 `create_isolated_worktree`（独立计数 6 次 / 3 人）。路径相同则先删再建，浪费且掩盖「谁拥有 worktree」的职责。 |
| P2-3 | `setup --force` 覆写不备份；备份路径无单测。备份后仍无条件覆写（有 bak 即算防护，但「防护」≠ 拒绝覆盖）。 |
| P2-4 | `generate_smart_config` 的 `security.allowed_clis` 不含 `mock-cli`，而 `live-run` 默认三位 Reviewer 全是 mock-cli（当前 dispatcher 不读该列表，配置与演练分裂）。 |
| P2-5 | `live_runner` 仍读顶层 `require_signoff`，向导写入 `merge.require_human_signoff`。缺省 True 导致永远走签字分支。 |
| P2-6 | CLI 成功文案仍是「100% success」（`main.py:416`）；确定性用语未标目标。 |
| P3-1 | 申请钉 `15e8918..HEAD` 又写完整范围到 `ac32dbb`，实际 HEAD 是 `b76cbfb`。 |

---

## 七、L4 / 场景对账

| L4 条件 | 状态 |
|---|---|
| 继承 L3 | **维持**（81/81 含历轮状态机测试） |
| 人工接管实机演练 | **CONTRADICTED**（仅有 Python API 单测；无 CLI OPS） |
| 回归无 P0/P1 | **不成立**（本轮 1×P1） |
| 用户手册齐备 | PARTIALLY_VERIFIED（FAQ/README 在；75 vs 81、真实协同过宽） |
| OPS VERIFIED | **PARTIALLY_VERIFIED**（mock dispatcher + 真实 worktree 已演练；接管/真实 CLI 评审会话未作为发布证据） |

---

## 八、门禁判定

| 级别/门禁 | 判定 |
|---|---|
| L3 / PG-2 | **维持** |
| L4 RELEASE-READY | **不通过** |
| PG-3 | **不通过**（绑定 L4） |

---

## 九、建议闭环顺序

1. 用临时仓或文档化剧本跑通：`WAITING_REVIEW` 超时或僵局 → `CONSENSUS_CHECK` → **CLI** `macao override resolve`（必要时再 `macao merge approve`），把命令、状态、审计贴进申请或 `docs/` 演练记录。禁止用单测代签冒充 OPS。
2. 默认可将 `live-run` 改为 `--no-auto-signoff`，或明确文档：该命令是 mock worktree 冒烟，不是 L4 人工接管证据。
3. 修 README 75→81、去掉「真实协同」过宽表述、合并 worktree 双创建、补 setup 备份单测。

---

## 十、Known issues

| issue_id | 严重度 | resolution_commit | status |
|---|---|---|---|
| 15E8918-P1-1 dispatcher 零调用 | P1 | `ac32dbb` | **CLOSED** |
| B76CBFB-P1-1 人工接管 OPS 用单测外推 | P1 | 待补 | **OPEN** |
| B76CBFB-P2-1 … P2-6 | P2 | 待补 | OPEN |
| B76CBFB-P3-1 | P3 | 待补 | OPEN |
