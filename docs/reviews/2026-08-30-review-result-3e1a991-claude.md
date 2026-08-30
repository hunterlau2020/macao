# MACAO 独立评审结果 — `3e1a991`（claude）

- **评审人**：claude
- **评审日期**：2026-08-30
- **评审对象**：`docs/reviews/2026-08-30-review-request-L3-Final-Seal.md`
- **实际评审范围**：`99526aa..3e1a991`（申请书写作 `99526aa..HEAD`；`HEAD` 是移动引用，本报告钉死为 `3e1a991`，见 P3-NEW-10）
- **依据基准**：`docs/MACAO_PRD_v2.md` v2.3.1、`docs/MACAO_REVIEW_GUIDELINES.md`
- **申请定级**：L3 SCENARIO-VERIFIED / PG-2

## 结论

> **不予授予 L3 SCENARIO-VERIFIED / PG-2；PG-1 亦不予授予；维持 L2 SPEC-CODE-ALIGNED。**

理由：申请书列出的 4 项闭环中 3 项 VERIFIED、1 项 PARTIALLY_VERIFIED；5 项机验声明我全部独立复现且**全部属实**。本轮是五轮以来代码质量最高的一轮——上轮我提的唯一阻断项 P1-NEW-8 已被**真正**修复（且经生产路径而非仅测试路径验证）。

但本轮修复使一条此前**不可达**的路径变为可达：E9 重试真正跑通之后，第二代际的评审产物会在归档目录与 `artifacts` 台账中**原地覆盖**第一代际的产物，被作废的评审意见（含 `critical` 反对票）与 E7/E9 人工终局裁定记录**被物理销毁且无任何其他留痕**。这与 PRD §3.3 E9:841「本轮已收意见作废归档」与 §14.5-1:1537「审计链在哈希层面不得断裂」直接冲突，记为 **P1-NEW-9（阻断）**。按 §2.2，PG-1 要求 P0/P1 为零，故不予授予。

---

## §0 本次评审的自查与方法声明

1. 本报告全部结论由我在 `99526aa..3e1a991` 上**独立重新推导**，不采信申请书表述，也不采信目录中其他 reviewer 的结论。评审期间 `docs/reviews/` 下并发出现了 `2026-08-30-review-result-3e1a991-codex.md`（13:12）与 `2026-08-30-review-result-3e1a991-kimi.md`（13:14）两份他方报告，我**未读取其内容**，仅在 §4 记录其存在以供治理对账。
2. 上轮（`bf5ae2d`）核心整改项 P1-NEW-8，我刻意**不复用**仓库新增的两个单测。仓库测试通过 `timed_out_reviewers=[...]` **显式传参**绕开了生产侧的自动检测分支；我用 `timeouts.per_reviewer` 真实过期触发 `detect_timed_out_reviewers()` 的生产路径重跑，结论一致（§2）。
3. 我在本轮**修正了自己上一轮的一处判断遗漏**：上轮我只测到 E9 重试无法达成共识（活锁）就停下了，没有继续追问「若重试真的跑通，第二代际产物落到哪里」。该问题在 `bf5ae2d` 上因活锁而不可达，我因此未发现；本轮活锁解除后它立刻暴露。这是我上一轮的覆盖不足，予以登记。
4. 单测/申请书里的自证不作为证据：`test-clis` 的 ANSI 列、`e2e-run` 的账本一致性、`git diff --check` 我均自行复算（§1 机验表）。

---

## §1 申请清单逐项核验

### 1.1 整改项

| 编号 | 申请书主张 | 我的独立核验 | 状态 |
|---|---|---|---|
| **P1-NEW-8 / P1-Q3 / P1-1** | 超时处置绑定当前轮最新派发代际（`sequence_id >= latest_dispatch_seq`），E9 重试后如期票正常参与共识 | 落点属实：`orchestrator.py:457-465`（`collect_and_evaluate_consensus`）与 `:755-763`（`resolve_override`）。`store.py:196` 的 `ORDER BY sequence_id DESC` 保证 `dispatches[0]` 确为最新派发，`dispatch_review_requests` 在 `:325-331` 每次派发都写入带 `review_round` 的 `REVIEW_REQUESTS_DISPATCHED`，代际锚点成立。生产自动检测路径实测：Gen1 两人超时 → HOLD → `RETRY_REVIEW` → Gen2 三人如期提交 → `state=MERGING`、`decision=APPROVED`、`resolution=automatic`、票面 `approve=3 / abstain=0`、`LATE_REVIEW_ISOLATED=0`、`review_round` 保持 1。无派发记录时 `latest_dispatch_seq=0`，全部历史超时仍计入，fail-closed 方向正确。 | **VERIFIED** |
| **P2-CARRY-1** | `integ_harness.py:108` 引入 `ANSI_ESCAPE_RE`，逐行真实扫描 `clean_logs`，断言 0 残留 | 硬编码 `True` 确已移除，实际落点为 `integ_harness.py:110`（申请书写 `:108`）。但被扫描的 `clean_logs` 来自 `pty_session.py:115-119`，其内容早在 `:89` 与 `:96` 处已被**同一个** `ANSI_ESCAPE_RE`（`strip_ansi`）清洗过。因此该断言检验的是「同一正则的幂等性」，而非「原始 PTY 流中确有 ANSI 且被正确清除」，对任何常规 ANSI 输入结构性地不可能失败；`if clean_logs else True` 使空捕获也真空通过。申请书「ANSI Escape 序列真实无残留检测通过」的措辞强于证据所能支撑的范围（§9 清单 B）。 | **PARTIALLY_VERIFIED** |
| **Schema 单测覆盖** | `tests/test_config.py:116-128` 用 `TemporaryDirectory()` 真实注入 `MACAO_SCHEMAS_DIR` | 落点精确（实为 `:116-127`）。确实真实 `os.environ` 注入并在 `finally` 中复原，`assertEqual(custom_path, Path(custom_dir).resolve())` 成立。上轮 Grok/Qwen 提出的「未真实设置环境变量」已解决。残留弱点见 P3-NEW-9。 | **VERIFIED** |
| **GOV-1 注册表勘误** | `bf5ae2d-zcode.md` 更名为 `-qwen.md`；台账修正为 55 份结果 + 11 份申请 | 逐一对账通过：`git ls-tree -r HEAD docs/reviews` 计得 **55** 份 `review-result` + **11** 份 `review-request`；STATUS 注册表内引用的 55 个结果文件名与磁盘 55 个受版本控制的文件**双向完全一致**（`comm` 无差集，唯一「差异」是 STATUS:13 行内叙述改名过程时提及的旧文件名，属正常行文）。更名后的 `bf5ae2d-qwen.md` 签名确为 qwen，与内容自洽。 | **VERIFIED** |

### 1.2 机验声明（全部由我独立重跑）

| 申请书声明 | 我的实测 | 状态 |
|---|---|---|
| `unittest discover tests -v` → 60 ran / 60 PASS | `Ran 60 tests in 13.112s / OK`，RC=0 | **VERIFIED** |
| 5 轮连续全量回归 300 次执行，0 flake | `Run 1..5 PASS`，RC=0（5 × 60 = 300） | **VERIFIED** |
| `macao test-clis` 4/4 PASS，0 孤儿/僵尸 | claude 2.1.251 / codex 2.1.0 / opencode 1.18.25 / agy 1.1.22 全 `PASS`，全 `✓ DEAD (0 Zombie)`，RC=0。ANSI 列的证据强度见 P2-CARRY-1 | **VERIFIED（ANSI 列除外）** |
| `macao e2e-run` 7/7 全绿、终态 DONE、5 份产物与账本双向一致 | 7 步全 OK、`final_state=DONE`、`merge_exact_match=True`。我另以固定工作目录重跑并直接查 SQLite：`artifacts` 恰 5 行，全部 `consumed=1`、`sha256` 长度 64、`archived_path` 非空且物理文件**逐个 `os.path.exists()` 为真** | **VERIFIED** |
| `git diff --check 99526aa..HEAD` 返回码 0 | RC=0，无输出 | **VERIFIED** |

---

## §2 已确认闭环（P1-NEW-8）的证据

生产路径（`timeouts.per_reviewer: "2s"` 真实过期，**不传** `timed_out_reviewers`）：

```text
Gen1 state: CONSENSUS_CHECK   vote_result on disk: False
Gen1 REVIEWER_TIMEOUT_ABSTAIN: ['antigravity', 'opencode']
After RETRY state: WAITING_REVIEW   .reviews left: []
Gen2 state: MERGING
Gen2 LATE_REVIEW_ISOLATED count: 0
Gen2 decision: APPROVED   resolution: automatic   breakdown: {'approve': 3, 'reject': 0, 'abstain': 0}
round still: 1
```

补充验证：

- **不会误放行**：Gen2 无人提交且新 deadline 再次到期时，`REVIEWER_TIMEOUT_ABSTAIN` 以新 `sequence_id` 落盘，系统稳定 HOLD 在 `CONSENSUS_CHECK`，不写 `vote_result.json`，符合 §6.1:1152。
- **不会误隔离**：Gen1 超时者在 Gen2 如期提交时不再被判迟到（`LATE_REVIEW_ISOLATED=0`），PRD §2.2:318 要求的「弃权须经人工确认」不再被系统自行代劳。
- **P1-NEW-7 未被削弱**：未执行 `RETRY_REVIEW` 时，`latest_dispatch_seq` 仍指向本代际派发，历史超时照常生效，迟到票仍被隔离（下方 P3-NEW-7 的 100 次轮询实测即建立在该行为仍生效之上）。

上轮我提的 **P2-NEW-3**（STATUS 三处计数 47/51/53 互不相符）本轮一并闭环，见 §1.1 GOV-1。

---

## §3 本轮发现

### P1-NEW-9（阻断，新增/由本轮修复转为可达）：E9 重试的第二代际产物原地覆盖第一代际归档，作废意见与人工终局裁定被物理销毁

**根因**：归档路径在 `fsm.py:85-88`（`_archive_file`）与 `fsm.py:100-104`（`_archive_reviews`）中固定为 `.macao/archive/<checkpoint_ref>/r<review_round>/<原文件名>`，且用 `shutil.copy2` 写入；`artifacts` 台账在 `store.py:101-107` 以 `ON CONFLICT(task_id, kind, checkpoint_ref, review_round, reviewer_id) DO UPDATE SET path=..., sha256=...` 原地更新。而 PRD §3.3 E9:841 明确规定 `RETRY_REVIEW` **round 不变**。于是同一 `(ref, round, reviewer)` 的两个代际共用同一条归档路径与同一行台账，后者无条件覆盖前者，**归档目录与数据库中都不保留任何代际维度**。

**实测（第一代际为一票 `critical` 反对，第二代际全票赞成）**：

```text
GEN1 archived codex.review.yml sha: 44fc8b594cfa36fd | contains GEN1-DISSENT: True
GEN1 ledger rows for codex: [('44fc8b594cfa36fd', '.macao/archive/<ref>/r1/codex.review.yml')]
GEN2 archived codex.review.yml sha: 78fd3a0c9c6fabfe | still contains GEN1-DISSENT: False
OVERWRITTEN (gen1 evidence destroyed): True
GEN2 ledger rows for codex: [('78fd3a0c9c6fabfe', '.macao/archive/<ref>/r1/codex.review.yml')]
```

E7/E9 人工终局裁定同样被覆盖：

```text
archived E7/E9 record -> RETRY_REVIEW human_override | votes: {'approve': 0, 'reject': 0, 'abstain': 3}
same path after gen2 -> APPROVED  automatic          | votes: {'approve': 3, 'reject': 0, 'abstain': 0}
human RETRY_REVIEW ruling still retrievable from archive: False
```

**为何是 P1 而非 P2**：

1. 与 PRD 明文规定直接冲突，属 §3.2 的 **CONTRADICTED**，而非「未实现」。E9:841 要求「作废归档」，实现做了归档随即又销毁；§14.5-1:1537 把「审计链在哈希层面不得断裂」列为不可变前提，台账 `sha256` 被原地改写正是哈希层断裂。
2. **无任何替代留痕**。`orchestrator.py` 全量审计事件类型仅 `DEADLOCK_DETECTED` / `LATE_REVIEW_ISOLATED` / `MAX_REWORK_ROUNDS_REACHED` / `REVIEWER_TIMEOUT_ABSTAIN` / `REVIEW_REQUESTS_DISPATCHED` / `TRANSITION_REJECTED` / `WORKTREE_CREATION_FAILED`，**没有任何一项承载评审意见的内容或哈希**。第一代际 reviewer 意见的唯一记录就是被覆盖的归档文件与被改写的台账行，损失是**完全**的。（人工裁定尚存 `HUMAN_OVERRIDE` 审计行，损失是部分的。）
3. 与本轮定级申请直接相关：L3 要求「返工循环」场景有**可复现证据**，而重试循环恰恰是唯一会销毁自身证据的路径。
4. 与项目既往定级口径一致：P1-1（超时票面落盘）、P1-NEW-7（迟到票据持久化隔离）同属「审计留痕」类且历轮均按 P1 处置。

**建议修复方向**：归档路径引入代际维度（如 `r{round}/g{dispatch_seq}/`），或在 `artifacts` 唯一键中加入 `sequence_id`/`generation`，使覆盖变为追加；`_archive_file` / `_archive_reviews` 在目标已存在且哈希不同时必须拒绝静默覆盖。

### P2-NEW-4（规范）：`RETRY_REVIEW` 遗留的 `vote_result.json` 使崩溃重建把 §6.1 的 HOLD 静默回退

`resolve_override` 在第 5 步无差别地以 `write_to_disk=True` 落盘 `vote_result.json`（`decision=RETRY_REVIEW`），第 6 步的归档用 `shutil.copy2`（复制而非移动），因此 `.macao/vote_result.json` 在整个第二代际期间**持续留在盘上**，且 `review_round` 与当前轮相同。

若第二代际以 `DEADLOCK` 收场，`collect_and_evaluate_consensus` 按设计**不写**新的 `vote_result.json` 并 HOLD 在 `CONSENSUS_CHECK`（这部分行为正确）。此时发生崩溃，`reconcile.py:34-57` 读到那份陈旧的 `RETRY_REVIEW` 文件（schema 合法、轮次匹配），经 `store.update_task_state` **绕过 `TransitionTable`** 把状态从 `CONSENSUS_CHECK` 改回 `WAITING_REVIEW`：

```text
Gen2 decision: None  state: CONSENSUS_CHECK
on-disk vote_result.json now: RETRY_REVIEW | round 1
state before reconcile: CONSENSUS_CHECK -> after reconcile: WAITING_REVIEW
CRASH_RECONCILE notes: ['Reconciled state to WAITING_REVIEW from physical vote_result.json (RETRY_REVIEW)']
```

一次僵局 HOLD 在无任何人工裁定的情况下被陈旧产物解除，与 §6.1:1152「任何情况下都不得静默推进或自动选择结果」的精神冲突。定为 P2 而非 P1，因为下一次轮询会重新判定僵局并回到 HOLD，不会导致错误合并；`get_active_task`（`store.py:48-54`）排除 `DONE`/`CANCELLED`，也堵住了「已完成任务被回退到 MERGING」的更严重变体。

**建议**：`RETRY_REVIEW`/`CANCEL` 分支不落盘业务性 `vote_result.json`（裁定本身已由 `HUMAN_OVERRIDE` 审计承载），或归档改为移动语义；`reconcile` 只接受未被消费（`consumed=0`）的产物。

### P2-CARRY-1（连续第四轮）：`test-clis` 的 ANSI 校验仍非独立证据

见 §1.1。相比硬编码 `True` 是实质改进，但因扫描对象已被同一正则清洗过，仍不构成独立证据。**建议**：在 `pty_session` 上保留一份未清洗的原始缓冲，断言「原始流含 ANSI」且「清洗后不含」，双向成立才置 `ansi_stripped_ok=True`；或把该列如实标注为「清洗器幂等性检查」。

### P3-NEW-7（连续第二轮遗留）：`LATE_REVIEW_ISOLATED` 仍未做幂等

`orchestrator.py:505` 的写入无按轮去重守卫。实测（1 人超时、其后补交、100 次常规轮询，无任何管理员动作）：

```text
state: CONSENSUS_CHECK
LATE_REVIEW_ISOLATED rows: 100
REVIEWER_TIMEOUT_ABSTAIN rows: 1
total audit rows: 107
```

同一函数内的 `REVIEWER_TIMEOUT_ABSTAIN`、`DEADLOCK_DETECTED`、`MAX_REWORK_ROUNDS_REACHED` 都已加幂等守卫，唯独此处未加。本轮申请书未提及。

### P3-NEW-4（跨轮遗留）：`per_reviewer` 仍是唯一弃权判定线

`detect_timed_out_reviewers` 仍以 `timeouts.per_reviewer` 单一阈值直接判定弃权，PRD §1.2:128 规定的 `WAITING_REVIEW` 总窗口 30m、每 reviewer 10m 触发 **ping** 的两级语义仍未实现。本轮未触及。

### P3-NEW-5（跨轮遗留）：`audit_events` 仍无任何索引

`db.py` 全文无 `CREATE INDEX`。`get_audit_events_by_type`（`store.py:196`）对每个类型做全表扫描后在 Python 侧过滤 `review_round`；本轮新增的代际锚定使该函数在 `collect_and_evaluate_consensus` 与 `resolve_override` 中的调用次数**翻倍**（各多一次 `REVIEW_REQUESTS_DISPATCHED` 查询）。当前规模无影响，长任务下会线性劣化。

### P3-NEW-9：Schema 环境变量单测只断言路径，未断言 schema 真能从该目录加载

`tests/test_config.py:117` 注入的是**空**临时目录，断言止于 `get_schemas_dir() == Path(custom_dir).resolve()`。上轮提出的「未真实设置环境变量」已解决，但「多级寻址与环境变量覆盖**行为**」中「覆盖后仍能取到 schema」这一半仍未覆盖。建议向该目录写入一份最小 schema 并断言 `ValidatorRegistry.get_schema()` 取到的是它。

### P3-NEW-10（文档/治理）：申请书用移动引用 `HEAD` 界定评审范围，且三处行号引用有漂移

- 范围写作 `99526aa..HEAD`。`HEAD` 随后续提交移动，与 §14.5-1:1537「评审对象 = 合并对象」的钉死要求不符；应写死为 `99526aa..3e1a991`。
- 行号漂移：`orchestrator.py:750-762` 实为 `:754-763`；`integ_harness.py:108` 实为 `:110`；`orchestrator.py:454-464` 实为 `:454-465`。`tests/test_config.py:116-128` 准确。均为定位偏差，不影响修复本身。
- 新增的 `test_retry_review_override_full_recovery_and_consensus` 通过 `timed_out_reviewers=["opencode"]` **显式传参**触发超时，未覆盖生产侧 `detect_timed_out_reviewers()` 自动检测分支；`change1 = orch.collect_and_evaluate_consensus(...)` 把二元组赋给单一变量后从未使用。功能结论我已用生产路径独立确认成立，此处仅为测试覆盖面提示。

---

## §4 治理观察

1. **reviewer 出席**：本轮（`3e1a991`）截至 13:14，`docs/reviews/` 下已出现 codex 与 kimi 两份未纳入版本控制的结果文件（`?? 2026-08-30-review-result-3e1a991-codex.md`、`?? ...-kimi.md`）；我未读取其内容。kimi 最近一份报告为 `2026-08-29-review-result-7935da3-kimi.md`，其后缺席 `f41b9da`、`bf5ae2d` 两轮，本轮回归。
2. **zcode 连续缺席**：`bf5ae2d` 轮以 zcode 命名提交、实际签名为 qwen 的报告，本轮已按 GOV-1 更名为 `-qwen.md`（该文件从未进入版本控制，`git log --all --diff-filter=A` 对旧文件名无任何记录，属工作区内改名）。zcode 最近一份真实署名报告停留在 `2026-08-29-review-result-4df059e-zcode.md`，此后 `ea536ab` / `7935da3` / `f41b9da` / `bf5ae2d` 连续四轮无出席。按 §8「沉默 ≠ 同意」，zcode 不得计入本轮及前四轮的任何多数。
3. **P1-3 治理规则执行情况**：本轮 STATUS 与 `reviews/` 目录**首次达成完全对账**（55/55、11/11 双向无差集），是该规则确立以来第一次机验通过，应予肯定。
4. **STATUS 待更新**：STATUS.md 尚未登记本轮（`3e1a991`）的任何结果报告，需在下一轮申请前按 P1-3 补齐。

---

## §5 定级判定

| 门禁 | 判定 | 依据 |
|---|---|---|
| L1 DOC-ALIGNED / PG-0 | **维持** | PRD v2.3.1 无回归 |
| L2 SPEC-CODE-ALIGNED | **维持** | 60/60 单测、5 轮 300 次零 flake、`test-clis` 4/4、`e2e-run` 7/7 与账本双向一致，均经我独立复现 |
| PG-1 | **不予授予** | §2.2 要求 P0/P1 为零；存在 P1-NEW-9（未决） |
| L3 SCENARIO-VERIFIED / PG-2 | **不予授予** | L3 要求返工/重试循环有**可复现证据**，而该循环当前会销毁自身证据（P1-NEW-9）；且 PG-2 以 PG-1 为前提 |

### 授予 L3/PG-2 的最小条件

1. **P1-NEW-9**：归档路径与 `artifacts` 唯一键引入代际维度，使 E9 重试的每一代际产物可独立取回；补一个测试，断言重试后第一代际的 `.review.yml` 与 E7/E9 `vote_result.json` 仍能按原哈希取回。
2. **P2-NEW-4**：`RETRY_REVIEW` 不再遗留业务性 `vote_result.json`，或 `reconcile` 拒绝已消费产物；补一个「重试后第二代际僵局 + 崩溃重建」测试，断言状态仍停在 `CONSENSUS_CHECK`。
3. **P2-CARRY-1**：ANSI 校验改为原始流/清洗流双向断言，或在报告中如实降级标注；连续四轮未实质解决，不宜再作为认证证据引用。
4. **P3 类**（`LATE_REVIEW_ISOLATED` 幂等、ping/30m 两级窗口、审计索引、Schema 单测加载断言、申请书钉死 commit 与行号勘误）可随后续轮次处理，不阻断定级。

---

## §6 复现命令

```bash
cd /home/debian/macao

# 机验（申请书 5 项，全部可复现）
PYTHONPATH=src python3 -m unittest discover tests -v
for i in 1 2 3 4 5; do PYTHONPATH=src python3 -m unittest discover tests >/dev/null 2>&1 && echo "Run $i PASS"; done
PYTHONPATH=src python3 -m macao.cli.main test-clis
PYTHONPATH=src python3 -m macao.cli.main e2e-run
git diff --check 99526aa..3e1a991; echo "RC=$?"

# 代码落点
sed -n '454,465p;505,509p;754,763p;792,802p' src/macao/workflow/orchestrator.py
sed -n '82,112p'  src/macao/workflow/fsm.py          # 归档路径无代际维度（P1-NEW-9）
sed -n '99,110p'  src/macao/storage/store.py         # artifacts ON CONFLICT DO UPDATE（P1-NEW-9）
sed -n '34,57p'   src/macao/storage/reconcile.py     # 陈旧 vote_result 驱动状态回退（P2-NEW-4）
sed -n '106,111p' src/macao/adapter/integ_harness.py # ANSI 断言（P2-CARRY-1）
sed -n '85,100p'  src/macao/adapter/pty_session.py   # clean_logs 已在此处被同一正则清洗
grep -n "CREATE INDEX" src/macao/storage/db.py       # 无输出（P3-NEW-5）

# PRD 锚点
sed -n '128p;318p;840,841p;1152p;1537p' docs/MACAO_PRD_v2.md

# 注册表对账（55/55、11/11）
git ls-tree -r --name-only HEAD docs/reviews | grep -c review-result
git ls-tree -r --name-only HEAD docs/reviews | grep -c review-request
```

P1-NEW-9 / P2-NEW-4 / P3-NEW-7 的场景复现脚本（生产自动检测路径，非仓库单测路径）保存于本次评审的临时目录，核心步骤已在 §2、§3 中以完整输出给出，可按上述配置（`reviewer_ids=["codex","opencode","antigravity"]`、`timeouts.per_reviewer="2s"`、`require_signoff=False`）逐步重放。
