# MACAO 独立评审结果 — `3ea5256`（claude）

- **评审人**：claude
- **评审日期**：2026-08-30
- **评审对象**：`docs/reviews/2026-08-30-review-request-L3-PG2-Unanimous-Final.md`
- **实际评审范围**：`7973853..3ea5256`（申请书写作 `7973853..HEAD`；`HEAD` 是移动引用，本报告钉死为 `3ea5256`，见 P3-NEW-10）
- **依据基准**：`docs/MACAO_PRD_v2.md` v2.3.1、`docs/MACAO_REVIEW_GUIDELINES.md` v1.0、`docs/schemas/dev_manifest.schema.json`
- **申请定级**：L3 SCENARIO-VERIFIED / PG-2

## 结论

> **不予授予 L3 SCENARIO-VERIFIED / PG-2；PG-1 亦不予授予；维持 L2 SPEC-CODE-ALIGNED。**

申请清单 **2 项全部 VERIFIED**：我上一轮的 P1-NEW-11（`.dev.yml` 缺省字段 Fail-open）与 P2-NEW-5（E9 未限制源状态）都已彻底闭环，修复方式正确且无副作用。5 项机验声明加注册表对账，我全部独立重跑，**全部属实**；注册表 62/62 + 13/13 双向零差集，是历轮最干净的一次。这是我评审这个项目以来质量最高的一次提交。

阻断原因不在申请清单之内。本轮我把探测面从「评审/重试/合并回路」扩展到此前未系统覆盖的**返工回路**，发现 PRD §3.3 E6:839 规定的触发条件「新一轮 `.dev.yml` 有效（round+1、**新 commit**）」中的**新 commit 一半从未被实现**：Executor 只需把 `.dev.yml` 里的 `review_round` 从 1 改成 2、`latest_commit` 原样不动，就能把一次全员 `REWORK_REQUIRED` 裁决「交差」，仓库自始至终只有 1 个 commit。实测该无改动返工可一路走到 `MERGING`。记为 **P1-NEW-12（阻断）**。按 §2.2，PG-1 要求 P0/P1 为零，故不予授予。

**关于申请书的定级框架**：申请书以「Qwen 支持授予、Kimi 授予、Claude REJECT、Codex REJECT」的票型来组织本轮叙述。按 §8「真理不等于投票」，定级不由票数决定；且五人委员会中 Grok 本轮未出席，「沉默 ≠ 同意」。本报告只就证据本身作结论。

---

## §0 本次评审的自查与方法声明

1. 全部结论由我在 `7973853..3ea5256` 上独立重新推导，不采信申请书表述，也不采信目录中其他 reviewer 的结论。
2. 对 P1-NEW-11 我**不复用**仓库新增的 9 分支单测，而是把我上一轮的 7 分支反例脚本原样重跑，再自行补 7 个新分支（缺 `executor`、`tests_exempt` 豁免路径、`status` 非法、轮次不符、`tests_passed` 类型错误、`development` 非对象等），共 14 分支（§2.1）。
3. **P1-NEW-12 是我自己覆盖不足的暴露，不是本轮引入的回归。** 前七轮我把探测集中在评审、超时、E9 重试与合并回路，从未系统走过 E5→E6 返工回路；该缺陷自始存在，我到本轮才发现，予以登记。
4. 我另外做了两项**未发现问题**的反向核查，一并如实记录，以免读者误以为未查：
   - `validate_dev_manifest` 在 schema 缺失时是否 fail-open？`schema.py:67-68` 返回 `(False, "Schema '...' not found in registry")`，**fail-closed**，新门禁不存在「schema 加载失败即放行」的旁路；
   - 新的严格门禁是否会误杀合法清单？把 PRD §2.1:145-201 的权威示例 `.dev.yml` 原文抽出送检，**schema 校验通过**，文档与实现无冲突。

---

## §1 申请清单逐项核验

### 1.1 整改项

| 编号 | 申请书主张 | 我的独立核验 | 状态 |
|---|---|---|---|
| **P1-NEW-11**（Claude）/ **P1-1**（Codex）/ **P3-1**（Kimi） | 先调用 `validate_dev_manifest` 做 Draft-07 全量校验，再以无宽容默认值的方式校验不变式 | 落点属实：`orchestrator.py:222-225`（schema 前置，不通过即 `return None`）、`:228-234`（`data.get("review_round")` / `data.get("signal")` 去掉放行默认值，`quality.get("tests_passed") is True or quality.get("tests_exempt") is True` 与 PRD §2.1:222-223 逐字对齐）、`:236-240`。**14 分支实测全部符合预期**（§2.1），我上一轮的三个失败分支 E/F/G 现已全部正确拒绝。`version` 与 `executor` 现由 schema 的 `required` 覆盖，PRD §2.1:217 的 `manifest.get('version')` 一项也随之满足。 | **VERIFIED** |
| **P2-NEW-5**（Claude） | `transitions.py` 增加 `E9` 守卫，仅允许 `CONSENSUS_CHECK` / `UNKNOWN` → `WAITING_REVIEW` | 落点属实：`transitions.py:48-51`，与 E7 的 `:43-46` 同口径，`valid_transitions` 中的 `E9: (None, …)` 条目已删除（原注释与代码矛盾的问题一并消除）。八状态矩阵实测只有 `CONSENSUS_CHECK` 与 `UNKNOWN` 为 `True`，其余六态全部 `False`；活路径实测 `resolve_override(RETRY_REVIEW)` 从 `WAITING_REVIEW` 被拒并写入 `TRANSITION_REJECTED` 审计，状态未变、无孤儿 `vote_result.json`（P2-NEW-2 的守卫仍然生效）。 | **VERIFIED** |

### 1.2 机验声明（全部由我独立重跑）

| 申请书声明 | 我的实测 | 状态 |
|---|---|---|
| 全量单测 64 项 | `Ran 64 tests in 15.103s / OK`，RC=0 | **VERIFIED** |
| 5 轮连续回归 320 次，0 flake | `Run 1..5 PASS`（5 × 64 = 320） | **VERIFIED** |
| `macao test-clis` 4/4，0 僵尸 | claude 2.1.251 / codex 2.1.0 / opencode 1.18.25 / agy 1.1.22 全 `PASS`、全 `✓ DEAD (0 Zombie)`，RC=0。ANSI 列的证据强度见 P2-CARRY-1 | **VERIFIED（ANSI 列除外）** |
| `macao e2e-run` 7/7、DONE、5 份产物哈希一致 | `final_state=DONE`、`decision=APPROVED`、`merge_exact_match=True`。另以固定工作目录重跑并直查 SQLite：`artifacts` 恰 5 行，**违反 `consumed=1` / `sha256` 64 位 / 归档文件物理存在 三不变式的行数 = 0**；`ARTIFACT_ARCHIVED` 审计 6 行 | **VERIFIED** |
| `compileall -q src && git diff --check` → RC 0 | `compileall` RC=0；`git diff --check 7973853..3ea5256` RC=0；工作区 RC=0 | **VERIFIED** |
| 注册表 62 份结果 + 13 份申请，与目录 100% 对账 | `git ls-tree -r HEAD docs/reviews` 计得 **62** / **13**；STATUS 注册表引用的文件名与 HEAD 受控文件**双向零差集**（`comm` 两向皆空）；`git status --short docs/reviews` 为空，无未受控残留 | **VERIFIED** |

---

## §2 已闭环项的证据

### 2.1 P1-NEW-11：14 分支反例矩阵

`schema` 列为 `validate_dev_manifest` 的独立判定，`accepted` 指是否转入 `READY_FOR_REVIEW`：

```text
A. fully schema-conforming manifest            schema=True  accepted=True  expect=True  OK
B. tests_passed: false                         schema=True  accepted=False expect=False OK
C. signal: INFERRED                            schema=False accepted=False expect=False OK
D. fabricated commit sha                       schema=True  accepted=False expect=False OK
E. NO quality_metrics block                    schema=False accepted=False expect=False OK   <- 上轮为 True
F. NO signal field                             schema=False accepted=False expect=False OK   <- 上轮为 True
G. bare minimum 4-line manifest                schema=False accepted=False expect=False OK   <- 上轮为 True
H. NO version field                            schema=False accepted=False expect=False OK
I. NO executor block                           schema=False accepted=False expect=False OK
J. tests_passed:false + tests_exempt:true      schema=True  accepted=True  expect=True  OK
K. status: in_progress                         schema=False accepted=False expect=False OK
L. review_round: 2 (task is round 1)           schema=True  accepted=False expect=False OK
M. tests_passed as string 'true'               schema=False accepted=False expect=False OK
N. development: not an object                  schema=False accepted=False expect=False OK
```

J 分支确认 PRD §2.1:222-223 的 `tests_exempt` 豁免路径被正确保留，没有为了收紧而误伤合法清单；N 分支确认 schema 前置也顺带堵住了 `development` 非对象时 `.get()` 抛 `AttributeError` 的隐患。

### 2.2 P2-NEW-5：源状态矩阵与活路径

```text
E9 from IDLE / CODING / READY_FOR_REVIEW / WAITING_REVIEW / MERGING / REWORK -> False
E9 from CONSENSUS_CHECK -> True      E9 from UNKNOWN -> True
```

```text
state: WAITING_REVIEW
RETRY_REVIEW from WAITING_REVIEW: rejected -> Illegal state transition from WAITING_REVIEW to WAITING_REVIEW via trigger E9
TRANSITION_REJECTED audit rows: 1 {'from_state':'WAITING_REVIEW','to_state':'WAITING_REVIEW','trigger_id':'E9','choice':'RETRY_REVIEW'}
state unchanged: WAITING_REVIEW      no vote_result.json written: True
```

仓库同步把两处依赖旧行为的测试入口改回了 `CONSENSUS_CHECK`（`tests/test_p0_p1_rectification.py:1196`、`:1278`，均先经共识评估进入僵局再发起 E9），这一点做得正确——上一轮我指出的「测试依赖 PRD 不认可的路径」随之消除。

---

## §3 本轮发现

### P1-NEW-12（阻断，新增）：E6 不校验「新 commit」，无改动返工可讨销 `REWORK_REQUIRED` 裁决

**规范依据**：

- PRD §3.3 **E6:839**：`REWORK` → `READY_FOR_REVIEW` 的触发条件是「新一轮 `.dev.yml` 有效（**round+1、新 commit**）」；
- PRD §2.1:**216**（`.dev.yml` 最小有效性规则）：「`latest_commit` 非空、存在于本地 git 历史且**未被消费过**」。

**实现**：`orchestrator.py:236` 的判据是 `dev_rnd == rnd and status == "ready_for_review" and signal == "EXPLICIT" and latest_commit and tests_passed`，`:238-240` 只校验 `commit_exists(latest_commit)`。**全函数从未把 `latest_commit` 与 `task["checkpoint_ref"]`（上一轮已评审对象）比较，也没有任何「该 commit 是否已被本任务消费过」的判定。** 两条 PRD 规则的「新 / 未被消费」语义都没有对应实现。

**实测（三 Reviewer 全员反对 → 返工 → 原样重交）**：

```text
round1 -> REWORK_REQUIRED | state: REWORK | round: 2
E6 with the IDENTICAL commit accepted: True | state = READY_FOR_REVIEW | round = 2 | checkpoint_ref = b92624432624
checkpoint unchanged across the rework: True
```

继续走完第二轮：

```text
round2 -> APPROVED | state: MERGING | checkpoint_ref: 431774443470
commits in repo the whole time: 1
REWORK_REQUIRED verdict discharged with an unchanged object: True
```

Executor 全程没有产生任何新 commit（仓库自始至终 `git rev-list --count HEAD` = 1），仅把 `.dev.yml` 的 `review_round: 1` 改成 `2` 重写一次，任务就从 `REWORK` 走回 `READY_FOR_REVIEW`，再走到 `MERGING`。

**危害**：

1. **返工回路的定义性前提失效**。§2.1 的 L3 门槛要求「全同意 / 1:1 僵局 / 超时 / 弃权 / 崩溃恢复 / **返工循环** 等场景均有可复现推演或测试证据」；返工循环当前无法从系统唯一推出 PRD 规定的结果——同一份输入既可能是「已修复」也可能是「原样重交」，系统不作区分、不留任何标记。
2. **共识裁决可被无声讨销**。`REWORK_REQUIRED` 是 Reviewer 集体意见的产物，PRD 用「新 commit」把它锚定为「必须产生新对象」。缺了这一校验，一次全员反对可以在零代码改动下推进到下一轮，`max_rework_rounds` 也可被空转耗尽。
3. **审计链缺口**。`vote_result.json` 与 `artifacts` 台账里，round 1 与 round 2 的 `checkpoint_ref` 完全相同，事后无法从产物层看出这一轮返工到底做了什么。这与 §14.5-1:1537「『评审对象 = 合并对象』是本流水线的不可变前提 …… 审计链在哈希层面不得断裂」的精神一致地要求哈希必须推进。

**为何定 P1**：这是**正常路径**（不需要管理员误操作、不需要构造畸形产物），发生在与 P1-NEW-11 同一个信任边界（不受信 Executor 写出的 `.dev.yml`）上，且直接使一条 PRD 明文规定的 E-trigger 触发条件失效，属 §3.2 的 **CONTRADICTED**。与本项目既往口径一致：历轮正常路径上的状态机正确性缺陷（P1-NEW-3 超时自动合并、P1-NEW-7 迟到票参与共识、P1-NEW-8 重试活锁）均按 P1 处置。

需要如实说明的边界：它**不会**造成「未经评审即合并」——第二轮 Reviewer 确实会收到 `REVIEW_REQUEST` 并看到该对象。只重合并安全性的读者可能主张 P2。但即便按 P2 计，返工循环场景仍无法满足 §3.3「L3：SIM/TEST 覆盖所有适用 P0/P1 场景且为 VERIFIED」，L3 一样不能授予。

**建议修复**：在 `check_development_checkpoint` 中，当 `current_st == AgentState.REWORK` 时增加 `latest_commit != task["checkpoint_ref"]` 硬校验（不满足即 `return None` 并写审计）；进一步可查 `artifacts` 中是否已存在同 `checkpoint_ref` 的 `dev_manifest` 且 `consumed=1`，实现 PRD §2.1:216 的「未被消费过」。测试需补一个用例：round 1 判 `REWORK_REQUIRED` 后以相同 commit 提交 round 2 清单，断言 `check_development_checkpoint` 返回 `None` 且状态停留 `REWORK`。

### P2-CARRY-1（连续第六轮）：`test-clis` 的 ANSI 校验仍非独立证据

`integ_harness.py:110` 本轮未改动。被扫描的 `clean_logs` 来自 `pty_session.py:115-119`，其内容早在 `:89`、`:96` 处被**同一个** `ANSI_ESCAPE_RE`（`strip_ansi`）清洗过，该断言检验的是正则幂等性而非清洗有效性，对任何常规 ANSI 输入结构性地不可能失败；`if clean_logs else True` 使空捕获真空通过。申请书与 STATUS.md 仍写「ANSI Strip True / ANSI 真实检测」。**建议**：保留一份未清洗的原始缓冲，双向断言（原始含 ANSI ∧ 清洗后不含）才置 `True`，或如实标注为「清洗器幂等性检查」。连续六轮未实质解决，不宜再作为认证证据引用。

### 已闭环的历史 P3

- **P3-NEW-12 → 已闭环**：上一轮我指出 STATUS.md 声称强校验 `version` 而实现未校验。本轮 `version` 由 schema 的 `required` 覆盖（分支 H 实测拒绝），STATUS.md:10 的表述现已属实。

### 跨轮遗留（P3，不阻断）

- **P3-NEW-11**：`store.py:104-105` 的 `ON CONFLICT … DO UPDATE` 未变，`artifacts` 仍只保留最新代际的 `archived_path`/`sha256`；跨代际追溯依赖 `ARTIFACT_ARCHIVED` 审计表。建议在文档中明确两者口径差异，或在唯一键中加入 `generation`。
- **P3-NEW-4**：`per_reviewer` 仍是唯一弃权判定线，PRD §1.2:128 的 `30m（10m/reviewer 触发 ping）` 两级语义仍未实现，`orchestrator.py` 全文无 `ping`。
- **P3-NEW-5**：`db.py` 仍无任何 `CREATE INDEX`（`grep -c` = 0）。上一轮我指出的「幂等守卫把全表扫描放进了 `for r in collected_reviews` 循环体」本轮亦未调整。
- **P3-NEW-9**：`tests/test_config.py` 的 `MACAO_SCHEMAS_DIR` 单测仍只断言路径解析、注入空目录，未断言「覆盖后仍能取到 schema」。补充一点本轮新观察：`SchemaValidator` 是类级缓存的单例（`schema.py:36-42`），`_schemas` 只在首次实例化时加载，进程内改环境变量不再生效——单测若将来扩展到「覆盖后取 schema」，需要一并处理该缓存。
- **P3-NEW-10**：申请书**第三次**使用移动引用（`7973853..HEAD`，应钉死为 `7973853..3ea5256`，PRD §14.5-1:1537）；行号引用继续漂移：`orchestrator.py:221-236` 实为 `:222-240`；`transitions.py:47-50` 实为 `:48-51`；`tests:1340-1430` 实为 `:1348-1512`；`tests:1193,1270` 实为 `:1196,1278`。均为定位偏差，不影响修复本身。

---

## §4 治理观察

1. **P1-3 全量对账连续第三轮机验通过**，且本轮是历轮最干净的一次：62/62、13/13 双向零差集，工作区无任何未受控评审残留。
2. **本轮闭环质量**：两项申请项都是**彻底**闭环而非打补丁——P1-NEW-11 选择了「schema 前置 + 去掉全部宽容默认值」的正确修法（而不是逐个补 `if`），P2-NEW-5 连同原有的注释/代码矛盾一并消除，并主动把依赖旧行为的两处测试入口改回 PRD 认可的 `CONSENSUS_CHECK`。这三点都超出了申请书自述的范围。
3. **测试质量本轮明显改善**：`test_check_development_checkpoint_validation_fail_closed` 从 3 个良构分支扩到 9 个分支且真正包含字段缺失反例，是我连续三轮指出的 §9 清单 B 模式第一次被正面解决。唯一小退步：新版本在多数分支里去掉了「状态仍停留 `CODING`」的二次断言，只留 `assertIsNone`；建议补回，因为「返回 None」与「未发生状态转移」并不等价。
4. **委员会出席**：`7973853` 一轮 Claude / Codex / Kimi / Qwen 四方出席，Grok 缺席；zcode 最近一份真实署名报告仍停留在 `2026-08-29-review-result-4df059e-zcode.md`，此后连续六轮缺席。按 §8「沉默 ≠ 同意」，缺席方不得计入任何多数。
5. **STATUS 待更新**：STATUS.md 尚未登记本轮（`3ea5256`）的任何结果报告，需在下一轮申请前按 P1-3 补齐。

---

## §5 定级判定

| 门禁 | 判定 | 依据 |
|---|---|---|
| L1 DOC-ALIGNED / PG-0 | **维持** | PRD v2.3.1 无回归；其 §2.1 权威 `.dev.yml` 示例经实测通过新门禁的 schema 校验 |
| L2 SPEC-CODE-ALIGNED | **维持** | 64/64 单测、5 轮 320 次零 flake、`test-clis` 4/4、`e2e-run` 7/7 与账本零违规、`compileall` 与 `git diff --check` 皆 RC=0，均经我独立复现 |
| PG-1 | **不予授予** | §2.2 要求 P0/P1 为零；存在 P1-NEW-12（未决） |
| L3 SCENARIO-VERIFIED / PG-2 | **不予授予** | §2.1 要求返工循环等场景「可从文档或系统唯一推出预期结果」；E6 的「新 commit」前提未实现，返工循环无法与「原样重交」区分（P1-NEW-12）；且 PG-2 以 PG-1 为前提 |

### 授予 L3/PG-2 的最小条件

1. **P1-NEW-12（唯一阻断项）**：`check_development_checkpoint` 在 `REWORK` 态下增加 `latest_commit != task["checkpoint_ref"]` 硬校验并写审计；补充 PRD §2.1:216 的「未被消费过」判定；补一个返工回路反例测试（相同 commit 重交 → `None` 且状态停留 `REWORK`）。
2. **P2-CARRY-1**：ANSI 校验改为原始流/清洗流双向断言，或在申请书与 STATUS 中如实降级标注。
3. **P3 类**（台账代际口径说明、Schema 单例缓存与单测加载断言、ping/30m 两级窗口、审计索引与循环内查询、`assertIsNone` 之外补状态断言、申请书钉死 commit 与行号勘误）可随后续轮次处理，不阻断定级。

我需要指出：本轮之后，评审流水线在「评审 / 超时 / 弃权 / 僵局 / 重试 / 崩溃恢复 / 合并」七类场景上的证据已相当扎实。只要 P1-NEW-12 按上述方式闭环并补上返工回路的反例测试，我这一侧不再有阻断项。

---

## §6 复现命令

```bash
cd /home/debian/macao

# 机验（申请书 5 项 + 注册表，全部可复现）
PYTHONPATH=src python3 -m unittest discover tests -v
for i in 1 2 3 4 5; do PYTHONPATH=src python3 -m unittest discover tests >/dev/null 2>&1 && echo "Run $i PASS"; done
PYTHONPATH=src python3 -m macao.cli.main test-clis
PYTHONPATH=src python3 -m macao.cli.main e2e-run
python3 -m compileall -q src && echo OK; git diff --check 7973853..3ea5256; echo "RC=$?"
git ls-tree -r --name-only HEAD docs/reviews | grep -c review-result   # 62
git ls-tree -r --name-only HEAD docs/reviews | grep -c review-request  # 13

# 代码落点
sed -n '222,240p' src/macao/workflow/orchestrator.py   # P1-NEW-11 已闭环 / P1-NEW-12：无 checkpoint_ref 比较
sed -n '42,51p'   src/macao/workflow/transitions.py    # P2-NEW-5 已闭环
sed -n '65,68p'   src/macao/core/schema.py             # schema 缺失时 fail-closed（反向核查，无问题）
sed -n '36,42p'   src/macao/core/schema.py             # 类级单例缓存（P3-NEW-9 补充观察）
sed -n '101,107p' src/macao/storage/store.py           # P3-NEW-11：台账仍原地覆盖
sed -n '109,110p' src/macao/adapter/integ_harness.py   # P2-CARRY-1
sed -n '89p;96p'  src/macao/adapter/pty_session.py     # 同一正则已在采集时清洗
grep -c "CREATE INDEX" src/macao/storage/db.py         # 0（P3-NEW-5）

# 基准锚点
sed -n '128p;216p;217,224p;839p;841p;1537p' docs/MACAO_PRD_v2.md

# PRD 权威 .dev.yml 示例送检（反向核查：通过）
sed -n '145,201p' docs/MACAO_PRD_v2.md > /tmp/prd_dev.yml
PYTHONPATH=src python3 -c "import yaml;from macao.core.schema import validate_dev_manifest;print(validate_dev_manifest(yaml.safe_load(open('/tmp/prd_dev.yml'))))"
```

P1-NEW-12 的返工回路脚本、P1-NEW-11 的 14 分支反例脚本与 P2-NEW-5 的状态矩阵脚本保存于本次评审的临时目录；核心配置为 `reviewer_ids=["codex","opencode","antigravity"]`、`min_effective_votes=3`、`max_rework_rounds=3`、`require_signoff=False`，完整输出已在 §2、§3 中逐条给出，可按上述参数重放。
