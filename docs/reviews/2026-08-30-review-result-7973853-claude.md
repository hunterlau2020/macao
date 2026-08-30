# MACAO 独立评审结果 — `7973853`（claude）

- **评审人**：claude
- **评审日期**：2026-08-30
- **评审对象**：`docs/reviews/2026-08-30-review-request-L3-PG2-Final.md`
- **实际评审范围**：`3e1a991..7973853`（申请书写作 `3e1a991..HEAD`；`HEAD` 是移动引用，本报告钉死为 `7973853`，见 P3-NEW-10）
- **依据基准**：`docs/MACAO_PRD_v2.md` v2.3.1、`docs/MACAO_REVIEW_GUIDELINES.md` v1.0、`docs/schemas/dev_manifest.schema.json`
- **申请定级**：L3 SCENARIO-VERIFIED / PG-2

## 结论

> **不予授予 L3 SCENARIO-VERIFIED / PG-2；PG-1 亦不予授予；维持 L2 SPEC-CODE-ALIGNED。**

申请清单 4 项中 **3 项 VERIFIED**：我上一轮提出的 P1-NEW-9（E9 代际归档覆写）、P2-NEW-4（活跃 `vote_result.json` 驱动崩溃回退）、P3-NEW-7（`LATE_REVIEW_ISOLATED` 非幂等）**全部真正闭环**，且修复质量高于申请书的描述——我用三代际、生产超时路径、崩溃重建三组独立场景验证，均通过。5 项机验声明我全部独立重跑，**全部属实**；注册表 58/58 + 12/12 双向零差集。

第 4 项（Kimi 的 **P1-2**，`check_development_checkpoint` 先验校验）**未闭环，且申请书与 STATUS.md 的表述被证伪**。修复只覆盖了「字段存在但取值非法」，没有覆盖「字段缺失」：实现用 `data.get("signal", "EXPLICIT")` 与 `quality.get("tests_passed", True)` 两个**默认放行**取值，与 PRD §2.1:218/222-223 参考实现的语义正好相反；`version` 根本未校验，而 STATUS.md 明文声称「强校验 …、`version` …」。实测：**缺 `quality_metrics`、缺 `signal`、乃至只有 4 行的最小清单，全部被接受并驱动 FSM 进入 `READY_FOR_REVIEW`**。这是 Fail-open，不是申请书所称的 Fail-closed，记为 **P1-NEW-11（阻断）**。按 §2.2，PG-1 要求 P0/P1 为零，故不予授予。

---

## §0 本次评审的自查与方法声明

1. 全部结论由我在 `3e1a991..7973853` 上独立重新推导；不采信申请书表述，也不采信目录中其他 reviewer 的结论。
2. 三项闭环项我**不复用**仓库新增单测判定，全部改用生产路径重跑：`timeouts.per_reviewer` 真实过期触发 `detect_timed_out_reviewers()`（仓库测试用 `timed_out_reviewers=[...]` 显式传参绕过该分支），并把归档验证扩展到**三个代际**（仓库测试只到两代）。
3. 对 P1-2 我采用**反例驱动**：不复现「合规清单能通过」，而是穷举「不合规清单应被拒绝」的 7 个分支，其中 3 个是仓库测试未覆盖的字段缺失分支——问题正出在这 3 个上（§3.1）。
4. `git diff --check`、`compileall`、`e2e-run` 的账本一致性我均自行复算，不采信输出中的自证文字（§1.2）。

---

## §1 申请清单逐项核验

### 1.1 整改项

| 编号 | 申请书主张 | 我的独立核验 | 状态 |
|---|---|---|---|
| **P1-NEW-9**（Claude）/ **P1-1**（Codex） | `fsm.py` 引入 `_get_generation`，哈希不一致时以 `g{gen}_{name}` 另存；每次归档写不可变 `ARTIFACT_ARCHIVED` 审计 | 落点属实：`fsm.py:83-88`（`_get_generation` = 本轮 `REVIEW_REQUESTS_DISPATCHED` 计数）、`:96-102` 与 `:135-141`（哈希比对后另存）、`:107-121` 与 `:146-160`（`ARTIFACT_ARCHIVED` 含 `generation` / `archived_path` / `sha256`）。**三代际实测全部可独立取回**（§2.1）。我上一轮的原始复现（Gen1 `critical` 反对票 + E9 人工裁定）现已完全保全：文件 sha 与 Gen1 归档时**逐位相同**，`vote_result.json` 仍可读出 `RETRY_REVIEW / human_override`。代际锚点时序也正确——`dispatch_review_requests` 在 `fsm.transition(E2)` **之后**才写派发审计，故 E9 归档时计到的是「当前代」而非「下一代」。 | **VERIFIED** |
| **P2-NEW-4**（Claude） | `resolve_override("RETRY_REVIEW")` 归档后主动清理活跃 `.macao/vote_result.json` | 落点属实：`orchestrator.py:815-821`。实测：E9 后活跃 `.macao/` 仅剩 `.dev.yml` 与 `state.db`；Gen2 僵局 HOLD 后触发崩溃重建，状态**保持 `CONSENSUS_CHECK` 不动**，`CRASH_RECONCILE` 无任何动作（上一轮此处会被静默回退为 `WAITING_REVIEW`）。 | **VERIFIED** |
| **P3-NEW-7**（Claude） | `already_logged` 代际内幂等守卫 | 落点属实：`orchestrator.py:513-525`。实测优于申请书主张：不仅**同代际 50 次轮询只写 1 行**（上一轮 100 次写 100 行），而且**跨代际仍会各记 1 行**（Gen1 + Gen2 = 2 行），没有退化成全局压制而丢失新一代的隔离事实。 | **VERIFIED** |
| **P1-2**（Kimi） | 强校验 `signal == "EXPLICIT"`、`tests_passed`（或 `tests_exempt`）、git commit 物理存在性，「不合规清单 Fail-closed 拒绝转移」 | **部分成立**。取值非法的三类确已拒绝（`tests_passed: false` / `signal: INFERRED` / 伪造 commit，实测均返回 `None` 且状态停在 `CODING`）。但**字段缺失一律放行**：`orchestrator.py:224` 的 `data.get("signal", "EXPLICIT")` 与 `:228` 的 `quality.get("tests_passed", True)` 使缺省即通过；`version` 从未被读取（该函数全文无 `version` 字样）。见 P1-NEW-11。 | **CONTRADICTED** |

### 1.2 机验声明（全部由我独立重跑）

| 申请书声明 | 我的实测 | 状态 |
|---|---|---|
| 全量单测 64 项 → `Ran 64 tests OK` | `Ran 64 tests in 14.960s / OK`，RC=0 | **VERIFIED** |
| 5 轮连续回归 320 次，0 flake | `Run 1..5 PASS`（5 × 64 = 320） | **VERIFIED** |
| `macao test-clis` 4/4 PASS，0 僵尸 | claude 2.1.251 / codex 2.1.0 / opencode 1.18.25 / agy 1.1.22 全 `PASS`、全 `✓ DEAD (0 Zombie)`，RC=0。ANSI 列的证据强度见 P2-CARRY-1 | **VERIFIED（ANSI 列除外）** |
| `macao e2e-run` 7/7、DONE、5 份产物哈希一致 | `final_state=DONE`、`decision=APPROVED`、`merge_exact_match=True`。我另以固定工作目录重跑并直查 SQLite：`artifacts` 恰 5 行，**违反 `consumed=1` / `sha256` 64 位 / 归档文件物理存在 三不变式的行数 = 0**；新增 `ARTIFACT_ARCHIVED` 审计 6 行 | **VERIFIED** |
| `compileall -q src && git diff --check` → RC 0 | `compileall` RC=0；`git diff --check 3e1a991..7973853` RC=0；工作区 `git diff --check` RC=0 | **VERIFIED** |
| 注册表 58 份结果 + 12 份申请，与目录 100% 对账 | `git ls-tree -r HEAD docs/reviews` 计得 **58** / **12**；STATUS 注册表引用的文件名与 HEAD 受控文件**双向零差集**（`comm` 两向皆空），无未受控残留 | **VERIFIED** |

---

## §2 已闭环项的证据

### 2.1 P1-NEW-9：三代际归档完整性

连续三次「Gen N 提交带唯一标记的 `critical` 反对票 → 超时 → HOLD → `RETRY_REVIEW`」：

```text
after gen1 retry, archive: ['.dev.yml', 'codex.review.yml', 'vote_result.json']
after gen2 retry, archive: [..., 'codex.review.yml', 'g2_codex.review.yml', 'g2_vote_result.json', 'vote_result.json']
after gen3 retry, archive: [..., 'codex.review.yml', 'g2_codex.review.yml', 'g3_codex.review.yml', ...]
marks per archived file: {'codex.review.yml': ['GEN1-MARK'], 'g2_codex.review.yml': ['GEN2-MARK'], 'g3_codex.review.yml': ['GEN3-MARK']}
all three generations retrievable: True
ARTIFACT_ARCHIVED review_manifest rows: [(1,'codex.review.yml','0d2b4691'), (2,'g2_codex.review.yml','e077bc69'), (3,'g3_codex.review.yml','2b14a11e')]
```

我上一轮 P1-NEW-9 的原始复现脚本在本 commit 上的结果：

```text
GEN1 dissent file survived: True | sha unchanged: True
vote_result.json     -> RETRY_REVIEW human_override {'approve': 0, 'reject': 1, 'abstain': 2}
g2_vote_result.json  -> APPROVED     automatic      {'approve': 3, 'reject': 0, 'abstain': 0}
```

哈希相同则复用同名文件（内容一致，无证据损失），哈希不同才另存，设计是正确的。

### 2.2 P2-NEW-4：僵局 HOLD 不再被陈旧产物解除

```text
active vote_result.json after RETRY exists: False
Gen2 decision: None  state: CONSENSUS_CHECK
active vote_result.json during Gen2 deadlock exists: False
state before reconcile: CONSENSUS_CHECK -> after reconcile: CONSENSUS_CHECK
CRASH_RECONCILE notes: []
```

### 2.3 P3-NEW-7：代际内幂等且代际间不压制

```text
gen1 after 50 polls: 1
gen1+gen2 after 50 more polls: 2   (每代各 1 行，符合预期)
```

---

## §3 本轮发现

### P1-NEW-11（阻断）：`check_development_checkpoint` 对字段**缺失**一律放行，与 PRD §2.1 参考实现语义相反

PRD §2.1:206-229 给出了该函数的参考实现，明确列出「.dev.yml 最小有效性规则」并以 `return None  # 无效或缺省 → 不产生状态转移` 收尾。逐条对照 `orchestrator.py:221-234`：

| PRD §2.1 参考实现 | 行号 | 本次实现 | 行号 | 差异 |
|---|---|---|---|---|
| `manifest.get('version')` | 217 | 未读取 | — | **完全缺失** |
| `manifest.get('signal') == 'EXPLICIT'` | 218 | `data.get("signal", "EXPLICIT") == "EXPLICIT"` | 224 | 缺省即放行 |
| `qm = manifest['development']['quality_metrics']`（缺失即 KeyError → 无效） | 220 | `data.get("development", {}).get("quality_metrics", {})` | 227 | 缺失退化为 `{}` |
| `qm.get('tests_passed') is True or qm.get('tests_exempt') is True` | 222-223 | `quality.get("tests_passed", True) or quality.get("tests_exempt", False)` | 228 | 缺省即放行 |
| `commit_exists(commit)` | 224 | `self.git.commit_exists(latest_commit)` | 233 | 一致 ✅ |
| `commit … 未被消费过`（规则注释） | 216 | 未实现 | — | 由 `review_round` 一致性间接部分覆盖 |

`docs/schemas/dev_manifest.schema.json` 把 `version` / `signal` / `development` / `status` / `review_round` 列为 `required`，`development.required = ["quality_metrics","git"]`，`quality_metrics.required = ["tests_passed"]`，`signal` 更是 `{"const": "EXPLICIT"}`。而 `check_development_checkpoint` **从头到尾没有调用过 `validate_dev_manifest`**（全仓库该函数只在 `reconcile.py:67` 被调用）——**崩溃恢复路径比主检查点路径更严格**，这本身就是一处一致性缺陷。

**实测七分支**（`schema_valid` 由 `validate_dev_manifest` 给出，`accepted` 指是否转入 `READY_FOR_REVIEW`）：

```text
A. fully conforming manifest              schema_valid=False accepted=True  expect=True  OK
B. tests_passed: false                    schema_valid=False accepted=False expect=False OK
C. signal: INFERRED                       schema_valid=False accepted=False expect=False OK
D. fabricated commit sha                  schema_valid=False accepted=False expect=False OK
E. NO quality_metrics block at all        schema_valid=False accepted=True  expect=False *** MISMATCH ***
F. NO signal field at all                 schema_valid=False accepted=True  expect=False *** MISMATCH ***
G. bare minimum, no schema fields         schema_valid=False accepted=True  expect=False *** MISMATCH ***
```

分支 G 的清单只有四行（`status` / `review_round` / `development.git.latest_commit`），无 `version`、无 `signal`、无 `quality_metrics`，仍被接受为一次「显式信号、测试通过」的检查点。分支 A 自身也是 schema 非法的（缺 `executor.cli`），却照样通过——这一条即可单独证明主路径不做任何 schema 校验。

**危害**：`.dev.yml` 是**不受信的 Executor CLI** 写出的产物，`check_development_checkpoint` 是它进入 FSM 的唯一信任边界。缺 `signal` 被当作 `EXPLICIT`，直接架空 PRD §2.1「显式信号优先，MACAO 强制认可」的前提；缺 `quality_metrics` 被当作 `tests_passed`，等于在**零测试证据**下把未验证的 commit 送入评审流水线，正是 §9 清单 B「『已完成』≠ 完成证据」。

**测试为何全绿**：`tests/test_p0_p1_rectification.py:1340` 的 docstring 写的是「fails closed on **missing** EXPLICIT signal or failed quality metrics」，但三个用例（`tests_passed: false`、伪造 commit、合法清单）**全部显式带有 `signal: EXPLICIT`**，没有任何一个 case 省略字段。断言的是机制在良构输入下的行为，不是 fail-closed 性质本身——§9 清单 B。

**建议**：在 `check_development_checkpoint` 读取字段前先调用 `validate_dev_manifest(data)`，不通过即 `return None`；把 `.get("signal", "EXPLICIT")` 改为 `.get("signal")`、`.get("tests_passed", True)` 改为 `.get("tests_passed") is True`；补 `version` 存在性与「commit 未被消费」两项；测试补齐字段缺失分支（至少 E/F/G 三例）。

### P2-NEW-5（规范）：E9 在转换表中被建模为「任意活动态可达」，与 PRD §3.3:841 不符

`transitions.py:39` 写作 `"E9": (None, AgentState.WAITING_REVIEW)`，`None` 表示不限制源状态；同一行的注释却写「from CONSENSUS_CHECK or UNKNOWN」——**注释与代码自相矛盾**。而 PRD §3.3:841 的 E9 行明确限定 `CONSENSUS_CHECK`。对比之下 E7 在 `:43-47` 被正确限制为 `CONSENSUS_CHECK / UNKNOWN`，E8/E10 用 `None` 则符合 PRD 的 `*`（任意活动态）。实测：

```text
E9 from IDLE / CODING / READY_FOR_REVIEW / WAITING_REVIEW / CONSENSUS_CHECK / MERGING / REWORK / UNKNOWN -> True（八种全部放行）
E7 from CODING / WAITING_REVIEW / MERGING -> False（正确拒绝）
```

后果：管理员在 `MERGING`（已批准、合并流水线执行中）下执行 `RETRY_REVIEW`，会被 `resolve_override` 的 P2-NEW-2 前置守卫放行，随即删除活跃评审与 `vote_result.json` 并重新派发。定为 P2 而非 P1：需要管理员主动误操作，且不会导致错误合并。

顺带指出：新增的 `test_multi_generation_archiving_preserves_gen1_evidence_immutable`（`:1141`）正是**从 `WAITING_REVIEW` 直接调用 `resolve_override(RETRY_REVIEW)`**——它依赖的恰是这条 PRD 不认可的路径。该测试因此没有覆盖真实的 `CONSENSUS_CHECK` 入口。我在 §2.1 的复现走的是「超时 → HOLD → E9」的 PRD 路径，结论仍成立，故不影响 P1-NEW-9 的 VERIFIED 判定，仅记为测试覆盖面提示。

### P2-CARRY-1（连续第五轮）：`test-clis` 的 ANSI 校验仍非独立证据

`integ_harness.py:110` 本轮未改动。被扫描的 `clean_logs` 来自 `pty_session.py:115-119`，其内容早在 `:89`、`:96` 处被**同一个** `ANSI_ESCAPE_RE`（`strip_ansi`）清洗过，因此该断言检验的是正则幂等性而非清洗有效性，对任何常规 ANSI 输入结构性地不可能失败；`if clean_logs else True` 使空捕获真空通过。申请书与 STATUS.md 仍写「ANSI Strip True / ANSI 真实检测」。**建议**：保留一份未清洗的原始缓冲，双向断言（原始含 ANSI ∧ 清洗后不含）才置 `True`，或如实标注为「清洗器幂等性检查」。

### P3-NEW-11（新增，P1-NEW-9 的残留）：`artifacts` 台账仍只保留最新代际视图

`store.py:101-107` 的 `ON CONFLICT(task_id, kind, checkpoint_ref, review_round, reviewer_id) DO UPDATE` 未变，`mark_artifact_consumed` 同样原地更新。实测三代际后，`artifacts` 中 codex 仍只有 1 行，`archived_path`/`sha256` 指向最新代际。历史代际的可追溯性现在**完全依赖** `ARTIFACT_ARCHIVED` 审计表。这是可接受的设计（审计表是仅追加的），但两处台账口径不同，建议在文档中明确「`artifacts` = 当前代际视图，跨代际追溯走 `ARTIFACT_ARCHIVED`」，或在唯一键中加入 `generation`。

### P3-NEW-12（治理）：STATUS.md 关于 `version` 强校验的表述被证伪

`docs/reviews/STATUS.md:13` 写「`check_development_checkpoint` 强校验 `signal == "EXPLICIT"`、`tests_passed`、**`version`** 及 git commit 物理存在性，Fail-closed 拒绝非法转移」。实现中 `version` 从未被读取（§3.1 表格），`signal`/`tests_passed` 在缺失时放行。该句在 `version` 一项上是**无对应实现的声明**，应予更正。

### P3-NEW-4 / P3-NEW-5 / P3-NEW-9 / P3-NEW-10（跨轮遗留）

- **P3-NEW-4**：`per_reviewer` 仍是唯一弃权判定线，PRD §1.2:128 的 `30m（10m/reviewer 触发 ping）` 两级语义仍未实现；`orchestrator.py` 全文无 `ping`。
- **P3-NEW-5**：`db.py` 仍无任何 `CREATE INDEX`（`grep -c` = 0）。本轮 P3-NEW-7 的幂等守卫把一次 `get_audit_events_by_type("LATE_REVIEW_ISOLATED")` 全表扫描放进了 `for r in collected_reviews` 循环体内（`:514`），每轮询每被隔离 reviewer 各一次，查询压力方向进一步恶化。当前规模无影响，建议顺手把该查询提到循环外。
- **P3-NEW-9**：`tests/test_config.py` 的 `MACAO_SCHEMAS_DIR` 单测仍只断言路径解析、注入的是空目录，未断言「覆盖后仍能取到 schema」。
- **P3-NEW-10**：申请书**再次**使用移动引用 `3e1a991..HEAD` 界定范围（应钉死为 `3e1a991..7973853`，PRD §14.5-1:1537「评审对象 = 合并对象」）；行号引用继续存在漂移：`fsm.py:80-135` 实为 `:83-166`；`orchestrator.py:811-820` 实为 `:806-821`；测试四处 `1141-1224` / `1226-1268` / `1270-1317` / `1319-1372` 实为 `1141-1239` / `1241-1281` / `1283-1338` / `1340-1408`。`orchestrator.py:510-525` 与 `:221-236` 基本准确。

---

## §4 治理观察

1. **P1-3 全量对账连续第二轮机验通过**：STATUS 注册表与 HEAD 受控文件 58/58、12/12 双向零差集，且工作区无未受控评审残留（`git status --short docs/reviews` 为空）。这是该规则确立以来最干净的一次，应予肯定。
2. **本轮闭环质量**：这是五轮以来最扎实的一轮。P1-NEW-9 的修复不仅解决了我提出的问题，还超出申请书描述——新增的 `ARTIFACT_ARCHIVED` 事件为整条归档链补上了此前完全缺失的内容级审计（此前 `orchestrator.py` 的七种审计事件无一承载产物哈希）。P3-NEW-7 的修复也正确保留了代际间的区分度，没有为了让计数变成 1 而牺牲语义。
3. **仍需注意的模式**：连续三轮出现「新增测试的名称/文档字符串声明了一项性质，但用例只覆盖良构输入」（本轮为 `test_check_development_checkpoint_validation_fail_closed`）。这是 §9 清单 B 的典型形态，也是本轮唯一阻断项能在 64/64 全绿下存活的原因。建议把「反例分支」纳入自查十项铁律的固定检查项。
4. **reviewer 出席**：截至本报告写作，`docs/reviews/` 下尚无其他 reviewer 对 `7973853` 的结果文件。上一轮（`3e1a991`）codex 与 kimi 均已出席；zcode 最近一份真实署名报告仍停留在 `2026-08-29-review-result-4df059e-zcode.md`，此后连续五轮缺席，按 §8「沉默 ≠ 同意」不得计入任何多数。
5. **STATUS 待更新**：STATUS.md 尚未登记本轮（`7973853`）的任何结果报告，需在下一轮申请前按 P1-3 补齐；同时应更正 P3-NEW-12 指出的 `version` 表述。

---

## §5 定级判定

| 门禁 | 判定 | 依据 |
|---|---|---|
| L1 DOC-ALIGNED / PG-0 | **维持** | PRD v2.3.1 无回归 |
| L2 SPEC-CODE-ALIGNED | **维持** | 64/64 单测、5 轮 320 次零 flake、`test-clis` 4/4、`e2e-run` 7/7 与账本零违规、`compileall` 与 `git diff --check` 皆 RC=0，均经我独立复现 |
| PG-1 | **不予授予** | §2.2 要求 P0/P1 为零；存在 P1-NEW-11（未决） |
| L3 SCENARIO-VERIFIED / PG-2 | **不予授予** | L3 要求关键场景可从系统唯一推出预期结果；进入评审流水线的**入口校验**当前对缺省字段 fail-open，检查点场景无法唯一推出「已通过测试的显式信号」这一前提；且 PG-2 以 PG-1 为前提 |

### 授予 L3/PG-2 的最小条件

1. **P1-NEW-11（唯一阻断项）**：`check_development_checkpoint` 先调用 `validate_dev_manifest` 再取字段；去掉两处放行默认值；补 `version` 与「commit 未被消费」；测试补齐「缺 `signal`」「缺 `quality_metrics`」「最小残缺清单」三个反例分支，断言 `return None` 且状态停留 `CODING`。
2. **P2-NEW-5**：`transitions.py:39` 的 E9 改为 `(CONSENSUS_CHECK, WAITING_REVIEW)` 并允许 `UNKNOWN`（与 E7 同口径），修正与注释的矛盾；把 P1-NEW-9 的测试入口改回 `CONSENSUS_CHECK`。
3. **P2-CARRY-1**：ANSI 校验改为原始流/清洗流双向断言，或在申请书与 STATUS 中如实降级标注；连续五轮未实质解决，不宜再作为认证证据引用。
4. **P3 类**（台账代际口径说明、STATUS `version` 表述勘误、ping/30m 两级窗口、审计索引与循环内查询、Schema 单测加载断言、申请书钉死 commit 与行号勘误）可随后续轮次处理，不阻断定级。

---

## §6 复现命令

```bash
cd /home/debian/macao

# 机验（申请书 5 项 + 注册表，全部可复现）
PYTHONPATH=src python3 -m unittest discover tests -v
for i in 1 2 3 4 5; do PYTHONPATH=src python3 -m unittest discover tests >/dev/null 2>&1 && echo "Run $i PASS"; done
PYTHONPATH=src python3 -m macao.cli.main test-clis
PYTHONPATH=src python3 -m macao.cli.main e2e-run
python3 -m compileall -q src && echo OK; git diff --check 3e1a991..7973853; echo "RC=$?"
git ls-tree -r --name-only HEAD docs/reviews | grep -c review-result   # 58
git ls-tree -r --name-only HEAD docs/reviews | grep -c review-request  # 12

# 代码落点
sed -n '221,234p'  src/macao/workflow/orchestrator.py   # P1-NEW-11：两处放行默认值、无 version
sed -n '507,527p'  src/macao/workflow/orchestrator.py   # P3-NEW-7 幂等守卫（已闭环）
sed -n '806,821p'  src/macao/workflow/orchestrator.py   # P2-NEW-4 活跃 vote_result 清理（已闭环）
sed -n '83,121p;128,160p' src/macao/workflow/fsm.py     # P1-NEW-9 代际归档 + ARTIFACT_ARCHIVED（已闭环）
sed -n '39p'       src/macao/workflow/transitions.py    # P2-NEW-5：E9 源状态为 None
sed -n '101,107p'  src/macao/storage/store.py           # P3-NEW-11：台账仍原地覆盖
sed -n '67p'       src/macao/storage/reconcile.py       # 仅此处调用 validate_dev_manifest
grep -n "validate_dev_manifest" src/macao/workflow/orchestrator.py   # 无输出 → 主路径不做 schema 校验
sed -n '109,110p'  src/macao/adapter/integ_harness.py   # P2-CARRY-1
sed -n '89p;96p'   src/macao/adapter/pty_session.py     # 同一正则已在采集时清洗
grep -c "CREATE INDEX" src/macao/storage/db.py          # 0（P3-NEW-5）

# 基准锚点
sed -n '128p;206,229p;841p;1537p' docs/MACAO_PRD_v2.md
python3 -c "import json;d=json.load(open('docs/schemas/dev_manifest.schema.json'));print(d['required']);print(d['properties']['signal']);print(d['properties']['development']['required'])"
```

P1-NEW-11 的七分支反例脚本、P1-NEW-9 的三代际脚本、P2-NEW-4 的崩溃重建脚本与 P3-NEW-7 的跨代际轮询脚本保存于本次评审的临时目录；核心配置为 `reviewer_ids=["codex","opencode","antigravity"]`、`timeouts.per_reviewer="2s"`、`require_signoff=False`，完整输出已在 §2、§3 中逐条给出，可按上述参数重放。
