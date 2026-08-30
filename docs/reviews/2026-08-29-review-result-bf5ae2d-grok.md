# MACAO 独立复审报告 — L3 / PG-2 终局封板认证申请 (commit `f41b9da..bf5ae2d`)

> **评审人**：grok（独立复审；不采信申请文档，亦不采信其他专家对 `f41b9da` / 本轮的结论；逐条重读源码 + 独立重跑命令 + 编写复现脚本）
> **评审日期**：2026-08-29
> **评审对象**：[`2026-08-29-review-request-L3-Final-Certification.md`](2026-08-29-review-request-L3-Final-Certification.md)
> **评审范围**：申请写 `f41b9da..bf5ae2d`（并称 `bf5ae2d` 为 HEAD）。代码闭环在 `a2dcc24` + `776693f`；`bf5ae2d` 起为文档。机验时工作区 HEAD 为 `99526aa`（仅追加本申请，`src/` 与 `bf5ae2d` 一致）。
> **对齐基准**：`docs/MACAO_PRD_v2.md` v2.3.1、`docs/MACAO_REVIEW_GUIDELINES.md` v1.0、`docs/schemas/*.schema.json`

---

## 〇、Reviewer 自审（连续漏审登记）

上轮 grok 对 `7935da3..f41b9da` **授予了 L3/PG-2**，但未把人工接管四分支（尤其 `RETRY_REVIEW`）走到「下一轮 collect 能否真正恢复」，也未核查合并签字是否绑定 `checkpoint_ref`。同轮 claude/codex/qwen 据此提出 P1-NEW-5/6/7。按指引 §9：同一 reviewer 对**同一类盲点**连续漏审，必须登记并激活对应 checklist。

- 本轮激活 checklist **A**（字段写入位置 vs 实际读取位置）与 **B**（「已完成」≠ 有完成证据）。
- 本轮强制自检：对每一个声称闭环的 override 出口，都推到**下一次** `collect_and_evaluate_consensus` / `execute_merge_pipeline`，而不是停在「发了消息 / 删了文件」。
- 该自检直接命中 **P1-NEW-8**（见 §三）：P1-NEW-6 的派发/清票已做，但超时场景下 E9 仍无法恢复。

---

## 一、结论

**不予授予 L3 SCENARIO-VERIFIED，亦不予授予 PG-1 / PG-2。维持 L2 SPEC-CODE-ALIGNED。**

申请清单中的 P1-NEW-5（签字绑定 checkpoint）、P1-NEW-7（迟到票不得自动合并）、P2-NEW-2（非法 override 不写孤儿产物）经独立复放 **均属实闭环**。P1-NEW-6 只完成了 PRD §3.3 E9 的前半段（清票 + 重新派发），**后半段失败**：超时 HOLD 后选择 `RETRY_REVIEW`，即便两位 Reviewer 均在新 deadline 内提交 YES，系统仍因历史 `REVIEWER_TIMEOUT_ABSTAIN` 把新票隔离为 `LATE_REVIEW_ISOLATED` 并再次 HOLD。这正是上轮 P1-NEW-6 的活锁在「已重派发」之后换皮再现。

GUIDELINES §2.1 要求超时场景的退出路径可复现；§2.2 PG-1 要求 P0/P1 为零。现存 P1-NEW-8，门禁不能放行。

---

## 二、申请清单逐条独立复核

| 编号 | 申请声明 | 独立复核方法与结果 | 判定 |
|---|---|---|---|
| **P1-NEW-5** | 签字必须 `detail.checkpoint_ref == task.checkpoint_ref`；第 1 轮签字不能放行第 2 轮代码 | 读 `merge/controller.py:49-61`：已改用 `get_audit_events_by_type`，并逐条比对 `checkpoint_ref`。独立脚本：仅持 `ref_r1` 签字合并 `ref_r2` → `ok=False`，消息含 round-2 SHA；补发 `ref_r2` 签字后 `ok=True` 且 `HEAD==ref_r2`。80 条无关审计之后签字仍可见（上轮 P2-NEW-1 的 `limit=50` 截断已不成立）。`cli/main.py:308-311` 写入的字段与消费端一致。 | **✅ VERIFIED** |
| **P1-NEW-7 / P1-Q2** | 一旦记录超时弃权，迟到文件隔离为 `LATE_REVIEW_ISOLATED`，不得 automatic 合并；终局保持 ABSTAIN | 读 `orchestrator.py:454-463, 490-540`：`historical_timed_out_ids` 与当次检测取并集；命中者记 `LATE_REVIEW_ISOLATED` 且不进入 `valid_reviews`。独立脚本：1 YES + 1 超时 → HOLD、无 `vote_result.json`；迟到者补交 YES 后仍 `CONSENSUS_CHECK`，`LATE_REVIEW_ISOLATED=1`；`resolve_override("APPROVED")` 后 `resolution=human_override`，票面 `codex/YES + opencode/ABSTAIN`。2 YES happy-path 仍为 `automatic` + `MERGING`，未误伤。 | **✅ VERIFIED** |
| **P1-NEW-6** | `RETRY_REVIEW` 清空 `.reviews/`、重发带新 deadline 的 `REVIEW_REQUEST` | **前半段属实**：`orchestrator.py:779-789` 在 E9 后 `unlink` 活跃票并调用 `dispatch_review_requests`。独立脚本：状态 `WAITING_REVIEW`、活跃 `.review.yml` 为 `[]`、`REVIEW_REQUESTS_DISPATCHED` 1→2、新 `REVIEW_REQUEST` AEP ≥2。配套单测只断言到这一步。**后半段失败**见 §三 P1-NEW-8：同 round 的历史超时处置不被作废，重试后准时 YES 仍被当迟到票。对照实验：无超时历史时 `RETRY_REVIEW` 后两张 YES 可 `automatic` 进入 `MERGING`——说明活锁绑定的是超时处置，不是 E9 本身。 | **⚠️ PARTIALLY_VERIFIED**（派发/清票 ✅；超时恢复出口 ❌） |
| **P2-NEW-2** | `resolve_override` 先校验 `can_transition`，非法转移不写盘 | 读 `orchestrator.py:720-730`：校验失败立刻 `TRANSITION_REJECTED` 并 `raise`，位于 `generate_vote_result` 之前。独立脚本：`CODING` 下 `APPROVED` → `ValueError: Illegal state transition from CODING to MERGING via trigger E7`；磁盘无 `vote_result.json`；artifacts 无 `vote_result` 行。 | **✅ VERIFIED** |
| **GOV-1** | `ea536ab-zcode` 与 `f41b9da-zcode` 更名为 `-qwen.md` | `git show a2dcc24`：`ea536ab-zcode.md → ea536ab-qwen.md` 为 **R100 更名**（属实）。`f41b9da-qwen.md` 为 **A 新增**，仓库中从未存在过 `f41b9da-zcode.md`。工作区无错标文件；STATUS 登记的 51 份 result 与磁盘 1:1。净状态正确，但「两份都完成更名」过宽。 | **⚠️ PARTIALLY_VERIFIED**（净状态 ✅；「更名」表述对 f41b9da 不成立） |

### 深度加固项（申请 §二）

| 声明 | 独立复核 | 判定 |
|---|---|---|
| Adapter `cancel` / `get_logs` 抽象 + Mock 实现 | `base.py:48-55` 为 `@abstractmethod`；6 个适配器均实现；`get_logs` 返回 `str`。`test_adapter_interface_and_log_consistency` PASS。 | **✅ VERIFIED** |
| `PTYSession.get_clean_logs(tail_lines=...)` | `pty_session.py:115-119` 支持切片；返回 `List[str]`，与 Adapter 的 `str` 仍是两层类型，但 Adapter 侧已自行 `join`。 | **✅ VERIFIED**（契约在 Adapter 层对齐） |
| Schema 四级寻址含 `MACAO_SCHEMAS_DIR` | `schema.py:11-30` 四级顺序属实。独立设置环境变量后 `get_schemas_dir()` 指向该目录。**但** `test_schemas_dir_lookup_and_env_override` **并未设置该环境变量**，只检查了默认发现路径。 | **CODE VERIFIED**；测试名相对声明为 CLAIM_ONLY |
| `parse_duration` 非法串抛错 | `"invalid_string"` → `ValueError`；`10m`→600。空串仍回落 600s（申请写的是非空非法串）。 | **✅ VERIFIED** |
| Task ID 32-bit + 5 次重试 | `orchestrator.py:140-158`：`uuid4().hex[:8]`，`IntegrityError` 路径重试 5 次。本次 `e2e-run` 得到 `task-20260829124306-31f4c090`（8 位后缀）。 | **✅ VERIFIED** |
| `mark_artifact_consumed` 补齐 sha256 | `store.py:111-140`：归档后若原 `sha256` 为空则读盘回填。`test_artifacts_registered_and_tracked_in_database` PASS。 | **✅ VERIFIED** |
| `docs/EXPERT_QUALITY.md` 重构 | 文件存在且本轮 `bf5ae2d` 有实质增补。属文档沉淀，不构成场景证据。 | **DOC VERIFIED**；与 L3 判据无关 |

### 机验清单（不采信申请粘贴输出）

| # | 声明 | 本机实测 | 状态 |
|---|---|---|---|
| 1 | 58/58 PASS | `Ran 58 tests in 14.822s OK` | ✅ |
| 2 | 5 轮连续回归 0 flake | 另跑 ×2，均为 58/58 OK（共 3 轮、174 次执行，0 flake）。未凑满申请的 5 轮。 | ✅ 属实方向；轮数未按 5 复放 |
| 3 | `macao test-clis` 4/4 | claude 2.1.251 / codex 2.1.0 / opencode 1.18.25 / agy 1.1.22 均 PASS，0 orphan | ✅（ANSI 列仍为橡皮图章，见 P2） |
| 4 | `e2e-run` 7 步 DONE | 7/7 OK，终态 DONE；步骤 4 `votes_yes=3, effective_votes=3` | ✅ |
| 5 | `git diff --check f41b9da..HEAD` 返回 0 | 返回码 0 | ✅ |

---

## 三、本轮独立新发现

### P1-NEW-8（阻断）：E9 `RETRY_REVIEW` 不清空/换代超时处置，重试后准时票被当成迟到票，超时场景仍然活锁

**这不是对 P1-NEW-6 前半段或 P1-NEW-7 的否定。** 清票 + 重派发是真的；迟到票在**同一次**超时尝试内不得 automatic 合并也是真的。问题出在二者的接合：P1-NEW-7 把超时处置持久化到 `(task_id, review_round)`，而 E9 **故意不增加 round**（PRD §3.3 E9：「round 不变」），又没有任何 `dispatch_generation` / 作废标记。

**证据（CODE）**

`collect_and_evaluate_consensus` 无条件并入本 round 全部历史超时：

```454:463:src/macao/workflow/orchestrator.py
        existing_timeouts = self.store.get_audit_events_by_type(task_id, "REVIEWER_TIMEOUT_ABSTAIN", review_round=rnd)
        historical_timed_out_ids = {a.get("detail", {}).get("reviewer_id") for a in existing_timeouts if "reviewer_id" in a.get("detail", {})}
        ...
            timed_out_reviewers = sorted(list(set(detected) | historical_timed_out_ids))
```

`resolve_override` 的 E9 分支（`:779-789`）只删除 `.review.yml` 并 `dispatch_review_requests`；**不**写入作废事件，也**不**把后续 collect 限制在「最新一次 `REVIEW_REQUESTS_DISPATCHED` 之后」的超时记录。

配套测试 `test_retry_review_override_clears_reviews_and_redispatches_fresh_requests` 从 `CONSENSUS_CHECK` 起步，**从未写入** `REVIEWER_TIMEOUT_ABSTAIN`，也不断言重试后的下一次 collect。这是 checklist **B**：用「清了文件」代替「超时出口可用」。

**违反的规范**

- PRD §3.3 E9（第 841 行）：「本轮已收意见作废归档；重新发送 `REVIEW_REQUEST`（全新 message_id 与 deadline）」。新 deadline 的语义是给未完成者一次新的准时窗口，而不是把上一窗口的弃权判决永久钉在同一 round。
- PRD §3.3 注释：「超时不是独立的状态来源：超时降级的结果最终仍通过 E3、E7 或 **E9** 生效」。E9 若不能让新窗口的有效票进入自动共识，则超时的合法保守出口只剩强制 `APPROVED` / `REWORK` / `CANCEL`。
- 上轮 P1-NEW-6 原判据原文：「`RETRY_REVIEW` 在超时场景下永远不可能成功」。派发修好后，成功条件仍然不成立。

**实机复现（独立脚本，不跑仓库单测）**

```text
[1] 2 reviewer，codex YES，opencode 超时
    → state=CONSENSUS_CHECK，REVIEWER_TIMEOUT_ABSTAIN=['opencode']，无 vote_result.json
[2] resolve_override(RETRY_REVIEW)
    → state=WAITING_REVIEW
    → 活跃 .review.yml = []
    → REVIEW_REQUESTS_DISPATCHED 1→2，新 REVIEW_REQUEST AEP=2
    → REVIEWER_TIMEOUT_ABSTAIN 仍为 ['opencode']   ← 处置未被作废
[3] 将 per_reviewer 设回 10m（避免 0s 立刻再超时），codex + opencode 均提交 YES
    → collect_and_evaluate_consensus → change=None，state=CONSENSUS_CHECK
    → LATE_REVIEW_ISOLATED=1（opencode 的新准时 YES 被隔离）
    → 磁盘仍是上一步留下的 decision=RETRY_REVIEW / opencode=ABSTAIN
```

对照：同一套 RETRY，但**没有**事先写入超时审计 → 两张 YES → `state=MERGING, decision=APPROVED, resolution=automatic`。

因此：E9 在非超时路径可用；**作为超时四选一里最保守的那一选，仍然死**。P1-NEW-3 之后所有超时都必须经人工出口，四个 choice 里 `RETRY_REVIEW` 再次无法完成超时恢复。

**建议修复（最小）**：历史超时只对「当前这一次派发」生效。例如只并入 `sequence_id` 大于本 round 最新 `REVIEW_REQUESTS_DISPATCHED` 的 `REVIEWER_TIMEOUT_ABSTAIN`；E9 重派发后旧处置自动失效，新窗口里的新超时仍能 HOLD。不要物理删除审计行。配套测试必须是：超时 HOLD → `RETRY_REVIEW` → 原超时者准时 YES → `automatic` 进入 `MERGING`，且该票计为 YES 而非 ABSTAIN/LATE。

---

## 四、P2 / P3（不构成本轮主阻断，必须登记）

### P2-CARRY-1：`test-clis` 的 ANSI Strip 列仍是字面量 `True`

`integ_harness.py:108-109`：`clean_logs = session.get_clean_logs()` 之后 `ansi_stripped_ok = True`。本次 4/4 报告中的「ANSI Strip ✓ YES」不是验证证据。已连续多轮提出，本轮申请未提及。

### P2-CARRY-2：脏树守卫仍不覆盖 untracked

`merge/controller.py:69-72` 只检查 `git diff` / `diff --cached`。未跟踪文件仍可在 `reset --hard` 路径上丢失。跨轮已知项。

### P3-1：超时时钟读审计插入 `ts`，忽略已写入的 `deadline`

`dispatch_review_requests` 把 `deadline` 写入审计 detail 与 AEP payload（`orchestrator.py:325-363`），`detect_timed_out_reviewers`（`:397-421`）却只用审计行 `ts` + `timeouts.per_reviewer`。默认路径下两者近似相等；但回填「过去的 deadline」不能触发超时，Reviewer 看到的 deadline 也不是引擎真正执行的那条。属 checklist **A**。

### P3-2：`timeouts.review_request`（30m）与 ping 仍未实现

`src/` 无消费方读取 `review_request`；无 ping。申请本轮未再写「完全对齐 §1.2」，故不再升格。行为仍是 `per_reviewer` 到期 → HOLD + E7。

### P3-3：`LATE_REVIEW_ISOLATED` 未幂等

HOLD 后每次 collect 都会再插一行。`DEADLOCK_DETECTED` 本轮已改为按 round 只写一次（`orchestrator.py:542-565`），同类纪律未覆盖迟到隔离。

### P3-4：STATUS 表头「47 份报告」与磁盘不符

`docs/reviews/` 现有 **51** 份 `review-result*` + **10** 份申请；STATUS 正文列出的 result 与磁盘一致（51 unique），仅标题数字过期。

### P3-5：签字未绑定 `review_round`

P1-NEW-5 按 checkpoint 绑定已足够覆盖「返工产生新 commit」的攻击。RETRY 保持同一 `checkpoint_ref`，此时 round 绑定不是安全必需。可作后续加固，不升 P1。

---

## 五、L3 场景对账（GUIDELINES §2.1 / §6）

| 场景 | 证据 | 状态 |
|---|---|---|
| 全同意 | `e2e-run` / 独立 2 YES → `automatic` + `MERGING` | VERIFIED |
| 1:1 / 有效票不足死锁 | 既有 deadlock 单测；HOLD 不写自动票 | VERIFIED |
| 超时进入 HOLD | P1-NEW-3 路径 + 本轮独立 1 YES+1 超时 | VERIFIED |
| 超时后迟到票 | P1-NEW-7 独立复放：仍 HOLD，终局 ABSTAIN | VERIFIED |
| 超时后 E9 重试再达成共识 | 独立复放：仍 HOLD，准时 YES 被 LATE 隔离 | **CONTRADICTED（P1-NEW-8）** |
| 弃权票面 | `resolve_override("APPROVED")` 含 ABSTAIN | VERIFIED |
| 崩溃恢复 | `test_reconcile_*` 仍 PASS | VERIFIED |
| 返工循环 | S2 / max-round 仍 PASS；REWORK 会 `round+1`，旧超时审计不会串到新 round | VERIFIED |
| 第 1 轮签字放行第 2 轮代码 | 独立复放已拒绝 | VERIFIED（P1-NEW-5） |

---

## 六、定级建议

| 项 | 结论 | 依据 |
|---|---|---|
| **L1 DOC-ALIGNED** | **达成** | Schema/PRD 对照；本轮 diff 洁净 |
| **L2 SPEC-CODE-ALIGNED** | **达成（维持）** | 58/58、3 轮 0 flake、字段与 schema 对应；本轮加固未破坏 happy-path |
| **L3 SCENARIO-VERIFIED** | **不予授予** | 超时退出路径中 E9 经实机复现仍无法让新窗口达成共识 |
| **PG-1** | **不予授予** | P1-NEW-8 未归零 |
| **PG-2** | **不予授予** | 依赖 PG-1 |

### 建议的最小放行条件

1. **P1-NEW-8（唯一新阻断）**：超时处置按「当前派发代次」作用域化（推荐：只认最新 `REVIEW_REQUESTS_DISPATCHED` 之后的 `REVIEWER_TIMEOUT_ABSTAIN`）。测试：超时 HOLD → `RETRY_REVIEW` → 原超时者准时 YES → `automatic` MERGING，票面为 YES 而非 ABSTAIN。
2. 修订申请/STATUS：P1-NEW-6 标为「派发已修、超时恢复未修」；GOV-1 改为「ea536ab 已更名，f41b9da 以正确文件名新增」；申请 HEAD 写成 `99526aa` 或明确 `bf5ae2d` 之后仅有申请文档。
3. P2/P3 可后续处理，不阻断下一轮（在 P1-NEW-8 关闭的前提下）。

---

## 七、附：本轮复现要点

```bash
PYTHONPATH=src python3 -m unittest discover tests -v   # 58/58 OK
PYTHONPATH=src python3 -m macao.cli.main e2e-run       # 7/7 DONE
PYTHONPATH=src python3 -m macao.cli.main test-clis     # 4/4 PASS（ANSI 列不可信）
git diff --check f41b9da..HEAD                         # exit 0
```

超时 × E9 接合（核心反例，须在临时 git 仓库中调用生产 `Orchestrator`，不要只跑现有单测）：

1. 配置 2 reviewer，制造 1 YES + 1 超时，确认 `CONSENSUS_CHECK` 且已有 `REVIEWER_TIMEOUT_ABSTAIN`。
2. `resolve_override("RETRY_REVIEW")`，确认活跃票清空且新 `REVIEW_REQUEST` 已发出。
3. 两位都提交 YES（新窗口未超时）。
4. 再 `collect_and_evaluate_consensus`：当前实现得到 `CONSENSUS_CHECK` + `LATE_REVIEW_ISOLATED`；修复后应得到 `MERGING` + `resolution=automatic`。
