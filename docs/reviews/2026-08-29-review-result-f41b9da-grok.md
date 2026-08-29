# MACAO 独立复审报告 — L3 / PG-2 终局封板申请 (commit `7935da3..f41b9da`)

> **评审人**：grok（独立复审；不采信申请文档，亦不采信其他专家对 `f41b9da` 或前轮的结论；逐条重读源码 + 独立重跑命令 + 编写复现脚本）
> **评审日期**：2026-08-29
> **评审对象**：[`2026-08-29-review-request-L3-Final-Seal.md`](2026-08-29-review-request-L3-Final-Seal.md)
> **评审范围**：申请写 `7935da3..f41b9da`。代码闭环在 `f41b9da`；当前 HEAD 为 `176df60`（仅追加本申请与 STATUS）。本报告对代码行为以 `f41b9da` 为准，机验在 `176df60` 工作区执行（`src/` 与 `f41b9da` 一致）。
> **对齐基准**：`docs/MACAO_PRD_v2.md` v2.3.1、`docs/MACAO_REVIEW_GUIDELINES.md` v1.0、`docs/schemas/*.schema.json`

---

## 一、结论

**支持授予 L3 SCENARIO-VERIFIED / Process Gate 2 (PG-2)。**

申请清单中的两项阻断（P1-NEW-3 超时强制人工接管、P1-NEW-4 定向审计查询）经独立复放 **均属实闭环**，且专项测试能约束所声称行为（去掉 HOLD 守卫或改回 `limit` 窗口后，对应测试应失败）。上轮 grok 在 `ea536ab` 指出的「终局 `vote_result.json` 不含超时 ABSTAIN」在本轮路径上已不成立：3 Reviewer（2 赞成 + 1 超时）经 `resolve_override("APPROVED")` 后票面为 `approve=2, abstain=1, resolution=human_override`。

GUIDELINES §2.1 L3 要求的全同意 / 僵局 / 超时 / 弃权 / 崩溃恢复 / 返工，现均有可复现 TEST；§2.2 PG-1 要求的 P0/P1 在本轮复核范围内归零。申请把实现写成「完全对齐 PRD §1.2 第 128 行（30m + ping）」**过宽**，记为 P2，不构成安全阻断。

---

## 二、申请清单逐条独立复核

| 编号 | 申请声明 | 独立复核方法与结果 | 判定 |
|---|---|---|---|
| **P1-NEW-3** | 3 Reviewer、2 赞成 + 1 超时不得自动批准；一律 HOLD 于 `CONSENSUS_CHECK` 并走人工接管 | 读 `orchestrator.py:498-524`：`DEADLOCK or timed_out_reviewers` 时不调用 `generate_vote_result(write_to_disk=True)`，发布 `HUMAN_OVERRIDE_REQUEST` 后 `return None, None`。独立脚本：`detected=['opencode']`，`change is None`，状态 `CONSENSUS_CHECK`，磁盘无 `vote_result.json`；此时 `execute_merge` 返回 `expected MERGING`（无法合入）。`resolve_override("APPROVED")` 后：`decision=APPROVED`，`resolution=human_override`（**不是 automatic**），`responded=3`，`abstain=1`，票面含 `opencode/ABSTAIN`。3 张 YES 的 happy-path 仍为 `automatic` + `MERGING`，守卫未误伤全同意。 | **✅ VERIFIED** |
| **P1-NEW-4** | `get_audit_events_by_type` 摆脱 `limit=50`；超时审计幂等；100+ 轮询后仍能回填 | 读 `store.py:167-192`：按 `task_id + type` 全量查询，无 `LIMIT`；`review_round` 在 Python 侧过滤。读 `orchestrator.py:475-491, 685-703`：超时检测与 `resolve_override` 回填均走定向查询；`REVIEWER_TIMEOUT_ABSTAIN` 按已有 `reviewer_id` 跳过重复写入。独立脚本对 **真实 `collect_and_evaluate_consensus` 连调 80 次**（强于测试里的 `POLL_HEARTBEAT` 填充）：poll 1/25/80 的 `detect_timed_out` 始终为 `['opencode']`；`REVIEWER_TIMEOUT_ABSTAIN` 行数恒为 **1**；终局票面仍为 `codex/YES + opencode/ABSTAIN`，`abstain=1`。 | **✅ VERIFIED** |
| **P3-NEW-2** | `effective_votes = approve + reject` | 读 `e2e_runner.py:236-239`。独立 E2E 步骤 4：`votes_yes=3, effective_votes=3`。全同意场景两值本就相等，此项只确认不再读已删除的 `breakdown.effective_votes` 键。 | **✅ VERIFIED** |
| **GOV-1** | `7935da3-zcode.md` 更名为 `…-qwen.md` | 工作区不存在 `2026-08-29-review-result-7935da3-zcode.md`；存在 `…-qwen.md` 且正文署名 qwen。STATUS 登记与之一致。 | **✅ VERIFIED** |
| **P3-NEW-1** | `git diff --check 7935da3..HEAD` 返回码 0 | 实测 `check_exit=0`，无告警。 | **✅ VERIFIED** |

### 机验清单（不采信申请粘贴输出）

| # | 声明 | 本机实测 | 状态 |
|---|---|---|---|
| 1 | 51/51 PASS | `Ran 51 tests in 12.329s OK` | ✅ |
| 2 | 5 轮连续回归 0 flake | 本评审人另跑 ×2，均为 51/51 OK（共 3 轮，未凑满申请的 5 轮；3 轮 0 flake） | ✅ 属实方向；轮数未按 5 复放 |
| 3 | `macao test-clis` 4/4 | claude 2.1.251 / codex 2.1.0 / opencode 1.18.25 / agy 1.1.22 均 PASS，0 orphan | ✅（ANSI 列仍为橡皮图章，见 P2） |
| 4 | `e2e-run` 7 步、账本 consumed/sha256 | 7 步 OK，DONE；独立查 SQLite：5 行全部 `consumed=1`、`sha256` 长度 64、`archived_path` 非空 | ✅ |
| 5 | `git diff --check 7935da3..HEAD` 返回 0 | 返回码 0 | ✅ |

---

## 三、P2 / 残留（不阻断本轮定级，必须登记）

### P2-1：申请「完全对齐 PRD §1.2:128 / §6.1 ping」过宽

P1-NEW-3 关闭的是 **超时后自动 `resolution: automatic` 合并**（claude/kimi/codex 在 `7935da3` 复现的安全回归）。当前语义是：一旦检出超时 reviewer，共识评估 HOLD 并要求 E7。这与 PRD「不得因超时静默推进」一致。

下列 §1.2 / §6.1 条文 **仍未实现**，不能写「完全对齐」：

- `WAITING_REVIEW` 超时列原文为 **30m（10m/reviewer 触发 ping）**；实现 `orchestrator.py:301-302, 392-393` 仍把 `timeouts.per_reviewer`（默认 10m）当作弃权判定线；`timeouts.review_request`（30m）在 `src/` 零消费方。
- `grep` 生产代码无 ping / 自愈；§6.1 的「ping → 再等 2 分钟 → 问用户是否标记弃权」未做。超时后直接进入整单 `HUMAN_OVERRIDE_REQUEST`（四选一裁定），而不是单独的「Mark as abstain?」。

建议：STATUS 将超时契约明确为「`per_reviewer` 到期 → HOLD + E7」，或后续实现 ping/30m 窗口。此项不影响「超时场景有 TEST 证据」，故不升 P1。

### P2-2：HOLD 轮询仍每轮追加 `DEADLOCK_DETECTED` / `HUMAN_OVERRIDE_REQUEST`

80 次真实 `collect` 后 `DEADLOCK_DETECTED` = 80 行（超时弃权审计已幂等为 1 行）。检测不再被挤出窗口，但审计链与消息队列会被轮询放大。建议对 `DEADLOCK_DETECTED` 按 `(task, round, reason)` 幂等，或对已 HOLD 的任务短路径返回。

### P2-3：`MergeController` 签字查询仍 `list_audit_events(..., limit=50)`

`merge/controller.py:50` 未改用定向查询。与本轮超时检测不是同一条路径；高频审计后存在签字被挤出窗口的理论风险。建议与 P1-NEW-4 同一修法。

### 跨轮已知限制（本轮 diff 未触及，不计入虚报）

- `integ_harness.py` 仍无条件 `ansi_stripped_ok = True`；`test-clis` 的 ANSI 列不能当 OPS 证据（L4 前必修）。
- 合并签字未绑定 `checkpoint_ref`（旧签字可授权新 checkpoint）。
- 脏树守卫仍不覆盖 untracked；CI 失败仍在用户工作区 `reset --hard`（已跟踪脏文件路径已 Fail-closed）。

---

## 四、L3 场景对账（GUIDELINES §2.1 / §6）

| 场景 | 证据 | 状态 |
|---|---|---|
| 全同意 | `e2e-run` / `test_e2e_runner_truthful_evidence_and_archive`：3 YES，DONE | VERIFIED |
| 1:1 / 有效票不足死锁 | 超时 1 YES+1 ABSTAIN 与 3 人超时 HOLD 均不写自动票、发接管请求 | VERIFIED |
| 超时 | 时钟推进 11m → `detect_timed_out_reviewers`；存在超时则禁止 automatic 合并 | VERIFIED |
| 弃权 | 终局 JSON 含 `ABSTAIN` 且计入 `reviewers_responded` / `vote_breakdown.abstain` | VERIFIED |
| 崩溃恢复 | `test_reconcile_*`；max-round 不写盘后 reconcile 仍 `CONSENSUS_CHECK` | VERIFIED |
| 返工循环 | 既有 S2 / max-round 测试（本轮未回退） | VERIFIED |

观察（非阻断）：在 **尚未超时** 时，3 人配置下 2 张 YES 已达法定人数，`collect` 会 `automatic` 批准而不等待第三人。这与 PRD「有效票达到法定人数即可离开 `WAITING_REVIEW`」一致，与「超时后用合成 ABSTAIN 凑满 2/3 并自动合并」不是同一条缺陷。

---

## 五、准入建议

**批准 L3 SCENARIO-VERIFIED / PG-2。**

闭环质量：P1-NEW-3/4 的修复落在状态机与查询层，测试断言了「无自动票 / 人工后票面含 ABSTAIN / 定向查询在大量轮询后仍稳定」，不是只断言 `status==PASS`。

**STATUS 修订建议（非否决条件）**：

1. 删掉「完全对齐 §1.2 ping/30m」表述，改为「超时检出后强制 E7，禁止 automatic 合并」。
2. 登记 P2-1～P2-3 为已知限制。
3. 申请范围请写实际 HEAD（当前为 `176df60`），或固定为代码提交 `f41b9da` 并注明其后仅有文档提交。

---

## Reviewer 自审记录

- 本轮先读 `7935da3..f41b9da` 的 `orchestrator.py` / `store.py` / 新增测试，再写独立脚本；未把其他专家的 `f41b9da` 报告当作证据。
- 针对 P1-NEW-4，未停留在测试使用的 `POLL_HEARTBEAT` 填充，而是连调 80 次真实 `collect_and_evaluate_consensus`，以覆盖「自我加速写审计」原复现形态。
- 上轮 grok（`ea536ab`）漏审/阻断点对照：终局票面 ABSTAIN 已在本轮独立脚本中出现；本轮额外检查了 HOLD 期间 `execute_merge` 被拒绝、以及 3 YES happy-path 未被守卫误伤。
- 未覆盖：真实远端 push、Windows、真实 LLM 评审质量；`test-clis` 的 ANSI 断言不可信。
