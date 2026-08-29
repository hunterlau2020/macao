# MACAO L3 / PG-2 终局封板独立评审结论 — claude

- **评审日期**：2026-08-29
- **评审对象**：`docs/reviews/2026-08-29-review-request-L3-Final-Seal.md`
- **评审范围（commit）**：`7935da3..f41b9da`
- **评审基准**：`docs/MACAO_REVIEW_GUIDELINES.md`（§2.1 分级判据、§2.2 门禁、§3 证据类型与验证状态、§8 仲裁原则、§9 自审 Checklist）、`docs/MACAO_PRD_v2.md` v2.3.1、`docs/schemas/*.schema.json`
- **评审方式**：全部结论由本人从一手代码、SQLite 实库与实机复现独立推导；不采信申请文档自述，亦不采信 codex / zcode / kimi / qwen / grok 既有结论
- **结论**：**不予授予 L3 SCENARIO-VERIFIED / PG-2；PG-1 亦不予授予（§2.2 要求 P0/P1 清零）；L2 SPEC-CODE-ALIGNED 维持**
  - 申请清单 5 项中 **4 项 VERIFIED**（P1-NEW-3 / P1-NEW-4 / P3-NEW-2 / P3-NEW-1），**GOV-1 描述不实（PARTIALLY_VERIFIED）**；
  - 机验清单 5 项全部本机复跑通过；
  - 独立发现 **3 项新 P1 + 3 项 P2**，3 项 P1 均位于本轮 P1-NEW-3 整改所依赖的**人工接管与合并签字路径**上，属 L3「超时/弃权场景可复现证据」的必要组成，故封板条件未达成。

> **本报告在 STATUS 全量对账阶段修订过一次**：GOV-1 由 VERIFIED 下修为 PARTIALLY_VERIFIED，并补入 P1-NEW-7（迟到票越过超时 HOLD）。两处均系首次提交时的漏检，修订依据见 §〇 自审与对应条目。

---

## 〇、reviewer 自审登记（GUIDELINES §9）

- 本轮激活 checklist **A**（"字段声明位置 vs 实际读取位置不一致"）。上两轮我审 `HUMAN_OVERRIDE_REQUEST` 与 `resolve_override` 时，只核到「HOLD 是否成立、票面是否正确落盘」，**未沿着人工接管的四个 choice 各自往下走一步**；本轮补齐后直接命中 P1-NEW-6（`RETRY_REVIEW` 死路）。同一盲点也解释了我此前从未核查 `merge/controller.py` 的签字取证逻辑，而 P1-NEW-5 正落在那里。
- **本轮漏检两项，在全量对账阶段自查补正**：(1) GOV-1 我只核到「文件是否以 `-qwen.md` 落盘、正文署名是否一致」，**未回溯 git 历史核对申请所述的「更名」是否真实发生**，也未把勘误范围扩到其他轮次——两处都有问题，见 §一 GOV-1 行与 §四；(2) 我在读 `collect_and_evaluate_consensus` 时已注意到「迟到票会使 `timed_out_reviewers` 变空」这一机制，**却未把它推到合并终点**，因而漏掉 P1-NEW-7。该项由 codex（其 P1-2）与 qwen（其 P1-Q2）各自独立提出；依 GUIDELINES §8「真理不等于投票」，我未采信其结论，而是自写脚本复现确认后才登记（§三 P1-NEW-7）。
- 本轮亦纠正一处自身潜在误判：`resolve_override(RETRY_REVIEW)` 写出 `decision: RETRY_REVIEW` 的 `vote_result.json`，经核 `docs/schemas/vote_result.schema.json` 的 `decision` 枚举含 `RETRY_REVIEW`，且 PRD §3.3 E7 明文要求「裁定结果落盘为终局 `vote_result.json`」，**该行为合规**，不计入发现。
- 本轮全部 P1/P2 结论均附可独立复跑的脚本与实测输出（§9 强制自检第 5 条）。

---

## 一、申请清单逐项独立复核

| 编号 | 申请声明 | 独立复核结论 | 关键证据 |
|---|---|---|---|
| **P1-NEW-3** | 存在超时 Reviewer 即强制 HOLD 于 `CONSENSUS_CHECK`，绝不 `resolution: automatic` 自动合并 | **VERIFIED** | 复现 A（走**生产自动检测路径**，非测试显式传参路径） |
| **P1-NEW-4** | 定向查询摆脱 `limit` 窗口截断；`REVIEWER_TIMEOUT_ABSTAIN` 幂等写入 | **VERIFIED**（限 orchestrator 两处调用点，见 P2-NEW-1） | 复现 B（125 次轮询，检出 100% 稳定，审计行恒为 1） |
| **P3-NEW-2** | `effective_votes` 由 `approve+reject` 精确计算 | **VERIFIED** | `e2e-run` 实测 `effective_votes=3`，与 `approve=3, reject=0` 一致 |
| **GOV-1** | 注册表归属勘误 | **PARTIALLY_VERIFIED（描述不实）** | 净结果对：`...-7935da3-qwen.md` 正文署名 `qwen`，该轮登记一致。但申请所述「将 `-7935da3-zcode.md` **更名**」并未发生——`git log --all --diff-filter=A -- 'docs/reviews/*7935da3*'` 显示该文件名**从未进入过版本库**，`f41b9da` 是直接以正确文件名新增。且真正错标的 `...-ea536ab-zcode.md`（正文第 4 行署名 `qwen`，且无对应 `-ea536ab-qwen.md`）**原样保留至今**。详见 §四 |
| **P3-NEW-1** | `git diff --check 7935da3..HEAD` 返回码 0 | **VERIFIED** | 本机复跑 rc=0（上轮同一声明 rc=2，本轮已真实修正） |

### 机验清单复核（申请文档 §二）

| 命令 | 声明 | 本机实测 | 状态 |
|---|---|---|---|
| `unittest discover tests` | 51 ran / 51 PASS | `Ran 51 tests ... OK` | **VERIFIED** |
| 5 轮连续回归（255 次） | 0 flake | 5 轮均 `Ran 51 tests ... OK`（12.7s–14.2s） | **VERIFIED** |
| `macao test-clis` | 4/4 真实 CLI PTY PASS，0 孤儿/僵尸 | claude 2.1.251 / codex 2.1.0 / opencode 1.18.25 / agy 1.1.22 全 PASS | **PARTIALLY_VERIFIED**，见 P2-CARRY-1 |
| `macao e2e-run` | 7/7 全绿，终态 DONE；5 产物与账本双向 100% 一致 | 7/7 OK，`final_state=DONE`；artifacts 表 5 行，全 `consumed=1`、`sha256` 长度 64、`archived_path` 与 `.macao/archive/<ref>/r1/` 下 5 个物理文件 1:1 吻合 | **VERIFIED** |
| `git diff --check 7935da3..HEAD` | rc=0 无告警 | rc=0（工作区 `git diff --check` 亦 rc=0） | **VERIFIED** |

---

## 二、已确认的正向闭环（本轮实质进展）

### P1-NEW-3 —— 真实闭环，且优于测试所证明的范围

`src/macao/workflow/orchestrator.py:501` 的守卫条件为
`if decision == Decision.DEADLOCK or (timed_out_reviewers and len(timed_out_reviewers) > 0)`，
即**任何超时都无条件 HOLD**，与 PRD §6.1「系统在任何情况下都不得因超时而静默推进或自动选择结果」（第 1152 行）及 §6.2 降级路径完全一致。

需要指出的是：新增单测 `test_three_reviewer_timeout_must_hold_and_require_human_override` 是**显式传入** `timed_out_reviewers=detected_timeouts` 的，并未覆盖 `orchestrator.py:437-438` 的生产自动检测分支。我因此另行以 `per_reviewer: "0s"` 构造真实墙钟条件，直接走 `timed_out_reviewers=None` 的生产路径复核：

```
[A] change=None vdata=None
[A] state=CONSENSUS_CHECK  vote_result.json exists=False
[A] audit types=['DEADLOCK_DETECTED', 'REVIEWER_TIMEOUT_ABSTAIN', 'REVIEW_REQUESTS_DISPATCHED', ...]
[A] HUMAN_OVERRIDE_REQUEST published = True
[A] override -> AgentState.MERGING
[A] decision=APPROVED resolution=human_override responded=3 breakdown={'approve': 2, 'reject': 0, 'abstain': 1}
[A] votes=[('antigravity','YES_APPROVE'), ('codex','YES_APPROVE'), ('opencode','ABSTAIN')]
```

与我上轮同场景实测（`decision=APPROVED, resolution=automatic` → `MERGING` → `DONE`）完全反转。**该项属实闭环，`resolution` 由 `automatic` 变为 `human_override` 是本轮最有价值的修复。**

### P1-NEW-4 —— 真实闭环

以我上轮的**原始有机场景**（重复调用 `collect_and_evaluate_consensus`，而非申请文档新测所用的 `POLL_HEARTBEAT` 人造事件）复核 125 次：

```
[B] poll#1/#25/#55/#80/#120: detect=['opencode']   (上轮：第 25 次起即返回 [])
[B] total audit events=131  REVIEWER_TIMEOUT_ABSTAIN rows=1
[B] FINAL responded=3 breakdown={'approve': 2, 'reject': 0, 'abstain': 1}   (上轮：responded=1, abstain=0)
```

`store.py:167-192` 的 `get_audit_events_by_type` 无 `LIMIT`，配合 `orchestrator.py:476,486` 的幂等守卫，检出稳定性与终局回填均已恢复。

### P1-2（跨轮）—— 仍保持完全闭环

```
[F] artifact rows = 5
    dev_manifest    consumed=1 sha256_len=64 archived_path='.macao/archive/<ref>/r1/.dev.yml'
    review_manifest rev=antigravity/codex/opencode  consumed=1 sha256_len=64 …（3 行）
    vote_result     consumed=1 sha256_len=64 archived_path='.macao/archive/<ref>/r1/vote_result.json'
[F] physical archive files (5) = 与上述 archived_path 1:1 吻合
```

---

## 三、本轮独立新发现

### P1-NEW-5（阻断）：合并签字未与 `checkpoint_ref` / `review_round` 绑定，第 1 轮的人工签字可放行第 2 轮**未经评审**的代码

**证据（CODE）**：`src/macao/merge/controller.py:49-53`

```python
if require_signoff:
    audits = self.store.list_audit_events(task_id, limit=50)
    signoffs = [a for a in audits if a.get("type") in ("HUMAN_MERGE_APPROVED", "MERGE_SIGNOFF_APPROVED")]
    if not signoffs:
        return False, "Human signoff required before merge (macao merge approve)", None
```

判据**仅匹配事件 type**，不比对 `checkpoint_ref`，也不比对 `review_round`。而 `src/macao/cli/main.py:308-311` 写入签字事件时**已经把 `checkpoint_ref` 存进了 detail**：

```python
store.log_audit_event(task_id, "HUMAN_MERGE_APPROVED", {
    "note": note,
    "checkpoint_ref": task_data.get("checkpoint_ref")
})
```

即所需数据已持久化、消费端从不读取——GUIDELINES §9 checklist **A** 的典型形态。

**违反的规范**：
- PRD §3.3 E4a（第 836 行）：「最终 push 对象 == `vote_result.json.checkpoint_ref` **硬校验通过**（……CI gate 通过、push 完成、**签字按策略收集**）」；
- PRD §14.5 第 1 步（第 1537 行）：「**"评审对象 = 合并对象"是本流水线的不可变前提**」，任何产生新 commit 的操作一律判为**未评审的新对象 → E4b 增量复审**；
- PRD §16 变更记录第 1734 行更把该约束登记为**已闭环的 P0-1**：「评审对象 = 合并对象硬绑定……E4a 增加 push 对象 == checkpoint_ref 硬校验」——即 PRD 侧认定此项已完成，代码侧的签字环节实际未落地。

**实机复现（TEST，确定性）**：

```
[E] signoff granted for round=1 ref=97ccc956
[E] round=2 checkpoint_ref=136da521 (NO new signoff granted)
[E] merge round-2 code with only a round-1 signoff -> ok=True msg='Merge pipeline completed successfully' sha=136da521
[E] main now contains unreviewed evil.txt: True
```

**影响方向为「过度放行」**：`require_human_signoff` 默认 `true`（PRD 第 1474 行称之为「刻意的保守安全默认值——正常路径下人类对自己代码被合并保留否决权」），但该否决权在返工轮次上**一次授予、永久复用**。本轮 P1-NEW-3 的整改把所有超时都收敛到人工接管，恰恰使「人工放行凭证」成为系统唯一的安全边界，因此该缺陷在本轮之后**危害等级上升而非下降**。

---

### P1-NEW-6（阻断）：`RETRY_REVIEW` 人工裁定为死路——不重发 `REVIEW_REQUEST`、不刷新 deadline，导致超时 HOLD 后立即再次超时（活锁）

**证据（CODE）**：`src/macao/workflow/orchestrator.py:677-682` 的 `choice_map` 将 `RETRY_REVIEW` 映射为 `(WAITING_REVIEW, "E9", "RETRY_REVIEW")`，其后 `:693-728` 只做了「写 `vote_result.json` → `register_artifact` → `fsm.transition` → 广播 `STATE_CHANGED`」，**没有任何重新派发逻辑**；`src/macao/cli/main.py:285` 亦只是调用后打印。`fsm.py:74` 对 E9 只触发归档。

**违反的规范**：PRD §3.3 E9（第 841 行）：
「`CONSENSUS_CHECK` → `WAITING_REVIEW`｜伴随动作：**本轮已收意见作废归档；重新发送 `REVIEW_REQUEST`（全新 message_id 与 deadline）**」

**实机复现（TEST，确定性）**：超时 HOLD 后执行 `resolve_override(RETRY_REVIEW)`：

```
[H] after timeout HOLD, state = CONSENSUS_CHECK
[H] resolve_override(RETRY_REVIEW) -> state=WAITING_REVIEW round=1
[H] new REVIEW_REQUEST AEPs re-sent : 0            (PRD E9 要求 3)
[H] REVIEW_REQUESTS_DISPATCHED rows : 1            (新 deadline 应新增 1 行)
[H] prior-round .review.yml still live on disk     : ['antigravity.review.yml', 'codex.review.yml']
[H] detect_timed_out_reviewers now  : ['opencode']  <- 沿用**原始** dispatch 时间戳
```

三项后果，逐条独立成立：

1. **活锁**：因为没有新的 `REVIEW_REQUESTS_DISPATCHED` 记录，`detect_timed_out_reviewers`（`orchestrator.py:371-382`）取到的仍是**上一次**派发时间，重试后 `opencode` **瞬间**再次判定超时 → 下一次 `collect_and_evaluate_consensus` 立即再度 HOLD。**`RETRY_REVIEW` 在超时场景下永远不可能成功**——而它正是 PRD §6.1/§6.2 为超时准备的四选一恢复路径之一。
2. **意见未作废**：`fsm.py:97-113` 的 `_archive_reviews`（由 `fsm.py:76` 调用）使用 `shutil.copy2`（复制而非移动），`.macao/.reviews/` 下的原件保留。重试轮 `collect_reviews(ref, rnd)` 会原样重新采信旧票，「重试」实为「重放」。
3. Reviewer 侧收不到任何重试通知（0 条新 `REVIEW_REQUEST`）。

**与本轮的耦合**：P1-NEW-3 之后，所有超时都必须经人工接管出口。四个 choice 中 `APPROVED` 与 `CANCEL` 可用、`REWORK` 正常，唯独语义上最保守、最应被推荐的 `RETRY_REVIEW` 不可用。GUIDELINES §2.1 要求 L3 的「超时/弃权场景均有可复现推演或测试证据」，该出口的证据链在此断裂。

---

### P1-NEW-7（阻断）：迟到 review 可越过**已经建立**的超时人工接管边，`resolution: automatic` 自动合并

> 该项由 codex（其 P1-2）与 qwen（其 P1-Q2）各自独立提出，我首轮漏检。以下判定基于我自己的复现输出，不采信其报告结论（GUIDELINES §8）。

**证据（CODE）**：超时守卫（`orchestrator.py:501`）的条件是**当次调用**的 `timed_out_reviewers` 是否非空，而该名单来自 `detect_timed_out_reviewers`（`orchestrator.py:437-438` 自动注入），其算法为 `expected - submitted`（`:405-407`）。因此**迟到者一旦补交 `.review.yml`，就不再出现在名单里，守卫随即失效**——已落盘的 `REVIEWER_TIMEOUT_ABSTAIN` 审计事件在此路径上完全不被读取，人工接管边没有任何持久化表示。

**实机复现（TEST，确定性）**：

```
[I] 超时 HOLD 后 state=CONSENSUS_CHECK  vote_result=False
[I] 已落盘 REVIEWER_TIMEOUT_ABSTAIN: ['opencode']
[I] opencode 迟到补交 review.yml
[I] 再次评估 -> state=MERGING change=AgentState.MERGING
[I] vote_result.json 已自动写盘: True
[I]   decision=APPROVED resolution=automatic responded=3 breakdown={'approve': 3, 'reject': 0, 'abstain': 0}
[I] 是否经过任何人工裁定(HUMAN_OVERRIDE 审计): 0 条
```

**违反的规范**：PRD §6.1 第 1152 行「系统在任何情况下都不得因超时而静默推进或自动选择结果」。系统已经判定进入超时降级、已写下 `REVIEWER_TIMEOUT_ABSTAIN` 审计、已向 admin 发出 `HUMAN_OVERRIDE_REQUEST`，随后**未经任何人工裁定**（`HUMAN_OVERRIDE` 审计 0 条）就把该轮自动推进到 `MERGING` 并落盘 `resolution: automatic`。

**与 P1-NEW-3 的关系**：这不是对 P1-NEW-3 修复的否定——§二 已证实超时**进入** HOLD 的路径真实有效。问题在于该 HOLD 是**无状态的、每次重新计算的**，因而不是一条边界，只是一个瞬时快照。修复方向应是：本轮一旦写下 `REVIEWER_TIMEOUT_ABSTAIN`，该轮即被标记为「已进入降级」，此后只能经 `resolve_override` 出场；迟到票按 PRD §3.3 E9 走 `RETRY_REVIEW` 重开一轮（而 `RETRY_REVIEW` 目前是死路，见 P1-NEW-6——两项必须一起修）。

---

### P2-NEW-1：`merge/controller.py:50` 仍停留在 `list_audit_events(limit=50)`，签字记录被挤出窗口后合并被永久拒绝

申请文档 §一 称 P1-NEW-4 已「**彻底摆脱** `limit` 窗口截断」。实际全仓仅剩的另一处审计消费点未改：

```
$ grep -rn "list_audit_events" src/
  src/macao/storage/store.py:143:    def list_audit_events(...)
  src/macao/merge/controller.py:50:            audits = self.store.list_audit_events(task_id, limit=50)
```

且触发条件由 P3-NEW-3（见下）现成提供——超时 HOLD 期间每轮询一次即写一行 `DEADLOCK_DETECTED`。实测：

```
[D] right after signoff  -> 'Merge pipeline completed successfully'
[D] after 60 polls: total audit events=67
[D] after polling      -> ok=False msg='Human signoff required before merge (macao merge approve)'
[D] signoff present in limit=50 window: False
[D] signoff present in full log       : True
```

方向为 fail-closed（拒绝合并，不产生不安全合并），且重新签字可恢复，故定 P2 而非 P1；但**申请文档的「彻底」表述作为系统级声明被证伪（CONTRADICTED）**，且该行与 P1-NEW-5 是同一行代码的两个缺陷，应一并整改。

---

### P2-NEW-2：`resolve_override` 先写权威 `vote_result.json`、后校验 FSM 转移，非法转移会遗留孤儿终局产物

`orchestrator.py` 中步骤 4（`generate_vote_result(..., write_to_disk=True)`，`:696-705`）与 `register_artifact`（`:708-714`）**都在** 步骤 5 的 `fsm.transition`（`:717`）**之前**执行。实测从非法源状态发起裁定：

```
[G] state before: CODING
[G] resolve_override raised: ValueError: Illegal state transition from CODING to MERGING via trigger E7
[G] state after : CODING
[G] orphan authoritative vote_result.json on disk: True
[G]   decision=APPROVED resolution=human_override responded=0 breakdown={'approve': 0, 'reject': 0, 'abstain': 0}
```

状态机本身 fail-closed（正确拒绝），但 `.macao/vote_result.json` 这一权威消费路径上留下了一份「人工批准、0 票、approve=0」的终局产物，同时 artifacts 表已登记该行。PRD §3.3 E7 明确 E7 只能从 `CONSENSUS_CHECK` 发起，而 `resolve_override` 无任何前置状态校验，CLI `macao override resolve` 也不做拦截。

这与 codex 此前提出、团队已在 `collect_and_evaluate_consensus` 中专门加固的 P0-3（「max-round 达到时不得写盘」——守卫置于 `generate_vote_result` 之前）**属同一缺陷类**，同样的纪律未施加到 `resolve_override`。

---

### P2-CARRY-1（跨轮遗留，本轮申请未提及）：`test-clis` 的 ANSI Strip 列是硬编码 `True`

`src/macao/adapter/integ_harness.py:108-109`：

```python
clean_logs = session.get_clean_logs()
ansi_stripped_ok = True
```

`clean_logs` 取出后即被丢弃，判定值为字面量。本次 `macao test-clis` 报告中 4 行「ANSI Strip ✓ YES」**不构成验证证据**，而申请文档 §机验结果将「4/4 真实 CLI PTY 验证 PASS」整体作为封板证据引用。PTY Spawn 与 Clean Kill 两列是真实判定（`pty_spawn_ok` 由 pid 推出、`clean_kill_ok` 由 `os.kill(pid, 0)` 推出），唯 ANSI 一列为橡皮图章。该项已在我 `ea536ab` 轮报告中提出，本轮既未修复也未在申请中说明。

---

### P3-NEW-3：`DEADLOCK_DETECTED` 审计与 `HUMAN_OVERRIDE_REQUEST` AEP 未做幂等，轮询即无界膨胀

100 次 `collect_and_evaluate_consensus` 轮询后：

```
[C] audit DEADLOCK_DETECTED        = 100      msg HUMAN_OVERRIDE_REQUEST = 100
    audit REVIEWER_TIMEOUT_ABSTAIN = 1        msg REVIEW_REQUEST         = 3
```

本轮只把 `REVIEWER_TIMEOUT_ABSTAIN` 改成了幂等，紧邻其下的升级分支未做。需公平指出：PRD §6.1「HOLD 当前状态 + **持续告警（升级通知）**」本就要求持续告警，故重复发 AEP 本身尚可辩护；问题在于 (a) 审计行无界增长，正是 P2-NEW-1 的触发机制；(b) 无去重键/升级层级，谈不上「升级」通知。另：`reason` 字段虽已区分 `TIMEOUT_ESCALATION`，事件 `type` 仍写死 `DEADLOCK_DETECTED`，按 type 统计僵局的消费方会把超时误计为僵局。

### P3-NEW-4：`per_reviewer` 仍被当作弃权判定线，PRD §1.2 的 ping 语义与 30m 轮窗口仍未实现

`orchestrator.py:392-393`（检测）与 `:301-302`（派发）均取 `timeouts.per_reviewer`（默认 `10m`）作为超时阈值。PRD §1.2 第 128 行 `WAITING_REVIEW` 超时列为 **`30m（10m/reviewer 触发 ping）`**——`per_reviewer` 是 **ping 触发器**，轮窗口是 `review_request`(30m)；全仓无任何 ping 实现。

申请文档称本轮「完全对齐 PRD §1.2:128」——该表述 **CONTRADICTED**。但因 P1-NEW-3 已使后果变为 fail-safe 的 HOLD（而非上轮的自动合并），实际危害仅为「Reviewer 慢 10 分钟即过早升级为人工接管」，故本轮由 P1 降级为 **P3**。

### P3-NEW-5：「定向 SQL **索引**查询」表述无据

`src/macao/storage/db.py:43-49` 的 `audit_events` 表定义中无任何索引，全仓 `grep -n "INDEX" src/macao/storage/db.py` 返回空。`get_audit_events_by_type` 是带 `WHERE` 的全表扫描。功能正确，但「索引查询」属 §9 checklist **C**（确定性用语未标注）类表述，建议改为「定向条件查询」或补上 `CREATE INDEX idx_audit_task_type ON audit_events(task_id, type)`。

### P3-NEW-6：两项新增单测均绕过生产自动检测分支

`test_three_reviewer_timeout_must_hold_and_require_human_override:202-206`（`tests/test_p0_p1_rectification.py:205`） 与 `test_audit_polling_over_50_does_not_lose_timeout_reviewers`（同文件 `:282`） 均显式传入 `timed_out_reviewers=detected`，`orchestrator.py:437-438` 的 `if timed_out_reviewers is None: ... detect_timed_out_reviewers(task_id)` 这一生产入口无用例覆盖。我已用 `per_reviewer: "0s"` 自行覆盖并确认其正确（复现 A/B/C），建议将该构造收编进测试集以固化。

---

## 四、治理事项：署名错标已连续三轮，GOV-1 未真正闭环

全量对账后核实（全部为我本人执行的命令输出）：

| 轮次 | 文件名 | 正文第 4 行署名 | 是否存在对应的 `-qwen.md` | 状态 |
|---|---|---|---|---|
| `ea536ab` | `...-ea536ab-zcode.md` | **qwen** | 否 | ❌ **错标未修** |
| `7935da3` | `...-7935da3-qwen.md` | qwen | — | ✅ 该轮登记正确 |
| `f41b9da` | `...-f41b9da-zcode.md` | **qwen** | 否 | ❌ **本轮再次错标** |

三点结论：

1. **GOV-1 所述的「更名」是不存在的操作。** `git log --all --oneline --name-status --diff-filter=A -- 'docs/reviews/*7935da3*'` 显示 `f41b9da` 新增的四个文件是 `-claude` / `-codex` / `-kimi` / `-qwen`，`...-7935da3-zcode.md` **从未进入过版本库**（它此前只是工作区未跟踪文件）。净结果虽然正确，但申请把「以正确文件名新增」写成「完成更名勘误」，属 §9 checklist **B**（「已完成」≠ 有完成证据）。
2. **真正需要勘误的 `...-ea536ab-zcode.md` 至今未动。** 该轮注册表仍把 qwen 的工作登记在 zcode 名下，`ea536ab` 轮 zcode 的独立意见实际缺失。
3. **同一错误在本轮重演**：`...-f41b9da-zcode.md` 正文同样署名 qwen。

> **补记（本报告提交后、STATUS 对账期间的状态变化）**：上表第 1、3 行所述的两处错标已在工作区被实际勘误——`...-ea536ab-zcode.md` → `...-ea536ab-qwen.md`（git 状态显示为 ` D` + 未跟踪新文件）、`...-f41b9da-zcode.md` → `...-f41b9da-qwen.md`，两轮文件名与正文署名现已一致。该动作发生在受审范围 `7935da3..f41b9da` 之外，**不改变本报告对 GOV-1 声明本身的判定**（申请所述的「更名」在当时确未发生），但注册表的净状态已修好。
>
> **未因此改变的部分**：**zcode 的独立意见在 `ea536ab` / `7935da3` / `f41b9da` 连续三轮实际缺席**，kimi 本轮亦未出具意见。改名解决的是归属错标，不是意见缺席。按 GUIDELINES §8「沉默 ≠ 同意」，两者的缺席均不得计入任何多数，STATUS 亦不得以「已完成勘误」表述掩盖为「专家意见已齐备」。

---

## 五、定级建议

| 项 | 结论 | 依据 |
|---|---|---|
| **L1 DOC-ALIGNED** | **达成** | 文档/Schema/PRD 对照一致；本轮 `git diff --check` 洁净度声明属实 |
| **L2 SPEC-CODE-ALIGNED** | **达成（维持）** | 51/51 单测通过、5 轮 255 次执行 0 flake、字段与 `vote_result.schema.json` 逐字段对应 |
| **L3 SCENARIO-VERIFIED** | **不予授予** | §2.1 要求「超时/弃权……场景均有可复现推演或测试证据」。超时**进入**路径证据已完备（P1-NEW-3 属实闭环），但**退出**路径 `RETRY_REVIEW` 经实机复现为活锁（P1-NEW-6），且 HOLD 边界可被迟到票消解（P1-NEW-7），场景闭环不成立 |
| **PG-1** | **不予授予** | §2.2 要求「L2；**P0/P1 为零**」。现存 P1-NEW-5、P1-NEW-6、P1-NEW-7 三项 |
| **PG-2** | **不予授予** | §2.2 要求「PG-1 + 接口稳定 + 消费方场景测试」。PG-1 未达成；且合并签字（消费方最关键的对外契约）存在跨轮复用缺陷 |

### 建议的最小放行条件

1. **P1-NEW-5**：`merge/controller.py:49-53` 的签字判据增加 `detail.checkpoint_ref == task.checkpoint_ref`（并建议同时比对 `review_round`），落地 PRD §14.5-1「评审对象 = 合并对象」；配套「第 1 轮签字 + 第 2 轮新 commit → 必须拒绝」的场景单测。
2. **P1-NEW-6**：`resolve_override` 的 `RETRY_REVIEW` 分支按 PRD §3.3 E9 补齐——作废（移出或标记）本轮 `.review.yml`、重发 `REVIEW_REQUEST`（全新 `message_id`）、写入新的 `REVIEW_REQUESTS_DISPATCHED`/deadline；配套「HOLD → RETRY_REVIEW → Reviewer 补交 → 正常达成共识」的端到端场景单测。
3. **P1-NEW-7**：把「本轮已进入超时降级」持久化为轮次状态（如以 `REVIEWER_TIMEOUT_ABSTAIN` 审计存在与否为准），一旦建立则该轮只能经 `resolve_override` 出场；迟到票走 E9 重开一轮。**须与第 2 项一起修**，否则唯一的合法出路仍是死的。配套「HOLD 建立 → 迟到票补交 → 仍须人工裁定」的场景单测。
4. **P2-NEW-1**：`controller.py:50` 改用 `get_audit_events_by_type`（与第 1 项同一处改动）。
5. **P2-NEW-2**：`resolve_override` 将 `fsm.transition` 的合法性校验前置于 `generate_vote_result(write_to_disk=True)`，与 `collect_and_evaluate_consensus` 中已有的 P0-3 纪律对齐。
6. **P2-CARRY-1**：`integ_harness.py:109` 用 `clean_logs` 实际断言无 ANSI 转义序列（如 `re.search(r"\x1b\[", clean_logs) is None`），或在报告中把该列标注为「未验证」。
7. **P3 类**：ping 与 30m 轮窗口（P3-NEW-4）、审计幂等与事件类型（P3-NEW-3）、索引表述（P3-NEW-5）、生产分支覆盖（P3-NEW-6）可随后续轮次处理，不阻断。
8. **治理**：真正执行 `...-ea536ab-zcode.md` → `-qwen.md` 的勘误、修正本轮 `...-f41b9da-zcode.md` 的文件名，并补齐 zcode 对这三轮的独立意见；补不齐则在 STATUS 中明确标注为「缺席、不计入多数」。

---

## 六、附：本轮复现命令

```bash
# 机验清单 1/2/5
PYTHONPATH=src python3 -m unittest discover tests
for i in 1 2 3 4 5; do PYTHONPATH=src python3 -m unittest discover tests 2>&1 | tail -3; done
git diff --check 7935da3..HEAD; echo "rc=$?"

# 机验清单 3/4
PYTHONPATH=src python3 -m macao.cli.main test-clis
PYTHONPATH=src python3 -m macao.cli.main e2e-run

# 复现 A / B / C：以 config timeouts.per_reviewer="0s" 构造真实墙钟超时，
#   3 Reviewer（codex/opencode/antigravity），codex+antigravity 交 YES_APPROVE，
#   A: collect_and_evaluate_consensus(tid, configured_reviewers=3)  # 不传 timed_out_reviewers，走生产自动检测
#   B: 上式重复 120 次后再 resolve_override("APPROVED")，检查终局票面
#   C: 上式重复 100 次后统计 audit_events / message 各 type 计数

# 复现 D：签字 → 轮询 60 次 → 再次 execute_merge_pipeline(require_signoff=True)
#   期望：'Human signoff required before merge'，而全量审计日志中签字事件确实存在

# 复现 E：store.update_task_state(tid, MERGING, checkpoint_ref=c1, review_round=1)
#   → log_audit_event("HUMAN_MERGE_APPROVED", {checkpoint_ref: c1, review_round: 1})
#   → 新建 commit c2、update_task_state(..., checkpoint_ref=c2, review_round=2)
#   → execute_merge_pipeline(require_signoff=True) 返回 ok=True

# 复现 G：CODING 状态下 resolve_override(tid, "APPROVED")
#   → 抛 ValueError，但 .macao/vote_result.json 已落盘且 approve=0

# 复现 I：超时 HOLD 建立后，迟到的 opencode 补交 review.yml，再次 collect_and_evaluate_consensus
#   → state=MERGING、resolution=automatic、HUMAN_OVERRIDE 审计 0 条

# 复现 H：超时 HOLD 后 resolve_override(tid, "RETRY_REVIEW")
#   → 新增 REVIEW_REQUEST AEP 数 = 0；detect_timed_out_reviewers 立即再次返回 ['opencode']

# 静态核查
grep -rn "list_audit_events" src/
grep -n "INDEX" src/macao/storage/db.py
sed -n '108,110p' src/macao/adapter/integ_harness.py
sed -n '49,53p' src/macao/merge/controller.py
sed -n '308,311p' src/macao/cli/main.py
```
