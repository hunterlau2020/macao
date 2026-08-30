# MACAO L3 / PG-2 终局封板与深度自查认证 独立评审结论 — claude

- **评审日期**：2026-08-29
- **评审对象**：`docs/reviews/2026-08-29-review-request-L3-Final-Certification.md`
- **评审范围（commit）**：`f41b9da..bf5ae2d`（HEAD 为 `99526aa`，仅追加申请与 STATUS 文档）
- **评审基准**：`docs/MACAO_REVIEW_GUIDELINES.md`（§2.1 分级判据、§2.2 门禁、§3 证据与验证状态、§8 仲裁原则、§9 自审 Checklist）、`docs/MACAO_PRD_v2.md` v2.3.1、`docs/schemas/*.schema.json`
- **评审方式**：全部结论由本人从一手代码、SQLite 实库与实机复现独立推导；不采信申请文档自述，亦不采信 grok / zcode / codex / qwen / kimi 既有结论
- **结论**：**不予授予 L3 SCENARIO-VERIFIED / PG-2；PG-1 亦不予授予（§2.2 要求 P0/P1 清零）；L2 SPEC-CODE-ALIGNED 维持**
  - 申请清单 5 项中 **3 项 VERIFIED**（P1-NEW-5 / P1-NEW-7 / P2-NEW-2），**P1-NEW-6 与 GOV-1 为 PARTIALLY_VERIFIED**；
  - 六项深度加固中 **5 项 VERIFIED**（第 6 项为文档沉淀，非机验对象）；机验清单 5 项全部本机复跑通过；
  - 但独立发现 **1 项新 P1 + 2 项 P2**：**P1-NEW-6 与 P1-NEW-7 的两个修复互相抵消**，`RETRY_REVIEW` 由上轮的「活锁」变成本轮的「无限循环 + 如期票被丢弃」，仍不可能成功。

---

## 〇、reviewer 自审登记（GUIDELINES §9）

- 本轮激活 checklist **B**（「已完成 ≠ 已有完成证据」）。我上轮报告明确写过「P1-NEW-6 与 P1-NEW-7 **必须一起修**，否则唯一的合法出路仍是死的」——本轮两项确实一起改了。**若我只核「旧票是否清空、请求是否重发」这一层，会直接判为闭环**；只有把场景继续推到「三名 Reviewer 全部如期重新提交之后」，才暴露出两个修复在语义上互相抵消（§三 P1-NEW-8）。这提示我上轮的建议措辞本身不够精确：我说了「一起修」，却没说清「重试必须**解除**该轮已建立的超时处置」。
- 本轮亦纠正一处自身误判：我最初以 `MACAO_SCHEMAS_DIR=/tmp/nonexistent-schemas` 测试 Schema 寻址，得到「env 覆盖失效」的结论；复看 `core/schema.py:14` 发现该分支带 `Path(env_dir).is_dir()` 守卫，不存在的目录降级是**正确设计**。改用真实存在的目录重测后覆盖生效，该项判为 VERIFIED，未计入发现。
- 本轮全部 P1/P2 结论均附可独立复跑的脚本与实测输出（§9 强制自检第 5 条）。

---

## 一、申请清单逐项独立复核

| 编号 | 申请声明 | 独立复核结论 | 关键证据 |
|---|---|---|---|
| **P1-NEW-5** | 签字校验强绑定 `checkpoint_ref` | **VERIFIED** | 复现 C：仅持 r1 签字合并 r2 代码被 Fail-closed 拒绝；补授 r2 签字后放行 |
| **P1-NEW-7 / P1-Q2** | 持久化超时处置，迟到票隔离 | **VERIFIED** | 复现 A：HOLD 后迟到补交仍维持 `CONSENSUS_CHECK`，`LATE_REVIEW_ISOLATED` 落库，终局保持 `ABSTAIN` |
| **P1-NEW-6** | `RETRY_REVIEW` 清空旧票并重新派发 | **PARTIALLY_VERIFIED** | 复现 B：清票 ✅ / 3 条新 `REVIEW_REQUEST` ✅ / 新 dispatch 审计 ✅——**但重试轮仍不可能达成共识**，见 §三 P1-NEW-8 |
| **P2-NEW-2** | 先校验状态机再写盘 | **VERIFIED** | 复现 E：`CODING` 态非法裁定抛 `ValueError`，磁盘无孤儿产物、artifacts 表 0 行、`TRANSITION_REJECTED` 审计 1 条 |
| **GOV-1** | 两处更名 + STATUS 47 份全量对账 | **PARTIALLY_VERIFIED** | 更名属实（`git log` 显示 `R100 ea536ab-zcode.md → -qwen.md`）；**「47 份全量对账」被证伪**，且同一错标在本轮第四次重演，见 §四 |

### 机验清单复核（申请文档 §三）

| 命令 | 声明 | 本机实测 | 状态 |
|---|---|---|---|
| `unittest discover tests` | 58 ran / 58 PASS | `Ran 58 tests ... OK` | **VERIFIED** |
| 5 轮连续回归（290 次） | 0 flake | 5 轮均 OK（13.1s–14.2s） | **VERIFIED** |
| `macao test-clis` | 4/4 PASS，0 孤儿/僵尸 | claude 2.1.251 / codex 2.1.0 / opencode 1.18.25 / agy 1.1.22 全 PASS | **PARTIALLY_VERIFIED**，见 P2-CARRY-1 |
| `macao e2e-run` | 7/7 全绿，5 产物与账本双向一致 | 7/7 OK，`final_state=DONE`；artifacts 表 5 行全 `consumed=1`、`sha256` 均 64 位、`archived_path` 与 `.macao/archive/` 下 5 个物理文件 1:1 吻合 | **VERIFIED** |
| `git diff --check f41b9da..HEAD` | rc=0 | rc=0（工作区亦 rc=0） | **VERIFIED** |

### 六项深度加固独立复核（申请文档 §二）

| 维度 | 独立复核结论 | 证据 |
|---|---|---|
| Adapter 契约一致性 | **VERIFIED** | `AgentAdapter.__abstractmethods__` 含 `cancel` / `get_logs`；Claude / Codex / OpenCode / Antigravity / Kimi / Mock **6 个实现全部就位且 `get_logs` 返回标注为 `str`** |
| Schema 四级寻址 | **VERIFIED** | `MACAO_SCHEMAS_DIR` 指向真实目录时覆盖生效；目录不存在时按 `schema.py:14` 的 `is_dir()` 守卫正确降级。附注：第 2 级 `src/macao/schemas` 当前**不存在**，属为 pip 分发预留的空分支，非缺陷 |
| `parse_duration` 显式校验 | **VERIFIED** | `abc` / `10x` → `ValueError`；`""` 与 `None` → 600.0。申请措辞「**非空**非法字符串显式抛出」与实现精确一致 |
| Task ID 高熵防碰 | **VERIFIED** | `uuid.uuid4().hex[:8]`（32-bit）+ `range(5)` 有界重试 |
| 产物 SHA256 归档自愈 | **VERIFIED** | `store.py:112-119` 归档时读物理文件补齐；E2E 后 5 行 `sha256` 均 64 位 |
| EXPERT_QUALITY.md | **NOT_APPLICABLE** | 文档沉淀，非机验对象，本轮不作定级依据 |

---

## 二、已确认的正向闭环

### P1-NEW-5 —— 真实闭环

`merge/controller.py:48-61` 现同时做了两件事：改用无 `LIMIT` 的 `get_audit_events_by_type`，并逐条比对 `s.get("detail", {}).get("checkpoint_ref") == checkpoint_ref`。我上轮的 P1-NEW-5（过度放行）与 P2-NEW-1（`limit=50` 挤出签字）**由同一处改动一并闭环**：

```
[C] 仅持 r1 签字合并 r2 代码 -> ok=False  msg='Human signoff required for checkpoint 95397e0f... before merge'
[C] 补授 r2 签字后          -> ok=True sha=95397e0f
[D] 签字后灌 200 条审计     -> ok=True  ('Merge pipeline completed successfully')
```

与我上轮实测（r1 签字放行 r2 未评审代码 `ok=True`、60 次轮询后签字被挤出窗口 `ok=False`）双向反转。落地了 PRD §14.5-1:1537「评审对象 = 合并对象」与 §3.3 E4a:836。

### P1-NEW-7 / P1-Q2 —— 真实闭环

`orchestrator.py:454-456` 把该轮已落库的 `REVIEWER_TIMEOUT_ABSTAIN` 读出为 `historical_timed_out_ids` 并与当次检测结果取并集，`:490-499` 将已超时者的迟到 manifest 隔离出自动共识，`vote.py:87-93` 在票面生成侧同步排除：

```
[A] 超时 HOLD 后            state=CONSENSUS_CHECK
[A] 迟到补交后              state=CONSENSUS_CHECK  vote_result=False  LATE_REVIEW_ISOLATED=1 条
[A] 人工裁定 -> MERGING     decision=APPROVED resolution=human_override
                            breakdown={'approve': 2, 'reject': 0, 'abstain': 1}
                            votes=[('antigravity','YES_APPROVE'),('codex','YES_APPROVE'),('opencode','ABSTAIN')]
```

上轮同场景实测为 `state=MERGING / resolution=automatic / HUMAN_OVERRIDE 审计 0 条`，本轮完全反转。**超时人工接管边现在是持久化的，这是本轮最有价值的修复。**

### P2-NEW-2 —— 真实闭环

`orchestrator.py:721` 把 `TransitionTable.can_transition` 前置到任何写盘与 `register_artifact` 之前，与 `collect_and_evaluate_consensus` 中已有的 P0-3 纪律对齐：

```
[E] 抛出 ValueError: Illegal state transition from CODING to MERGING via trigger E7
[E] 磁盘孤儿 vote_result.json=False  artifacts 表残留=0 行  TRANSITION_REJECTED 审计=1 条
```

### P3-NEW-3（上轮）—— 部分闭环

`DEADLOCK_DETECTED`（`:542-543`）与 `MAX_REWORK_ROUNDS_REACHED`（`:570-571`）均已加按轮幂等守卫，100 次轮询各只写 1 行、`HUMAN_OVERRIDE_REQUEST` 只发 1 条。但同一模式在本轮新代码中第三次引入，见 P3-NEW-7。

---

## 三、本轮独立新发现

### P1-NEW-8（阻断）：P1-NEW-6 与 P1-NEW-7 的两个修复互相抵消，`RETRY_REVIEW` 成为无限循环，且如期重交的票被丢弃

**根因（CODE）**：两处改动各自成立，但共用同一把键：

- P1-NEW-7 把超时处置持久化，键为 **(task_id, review_round)**——`orchestrator.py:454`：
  `existing_timeouts = self.store.get_audit_events_by_type(task_id, "REVIEWER_TIMEOUT_ABSTAIN", review_round=rnd)`；
- PRD §3.3 E9:841 规定 `RETRY_REVIEW` 是「**重试当前轮**评审，**round 不变**」，`choice_map` 亦如此实现（`:712-718`，`review_round` 不递增）。

因此重试轮沿用同一个 `rnd`，上一轮写下的 `REVIEWER_TIMEOUT_ABSTAIN` 依然命中，该 Reviewer 被**永久**标记为超时；其在重试轮**如期提交**的新 manifest 随即被 `:490-499` 当作「迟到票」隔离。**为让 P1-NEW-7 安全而建立的持久化处置，恰好是让 P1-NEW-6 的重试永远无法成功的原因。**

**实机复现（TEST，确定性）**：连续三次 `RETRY_REVIEW`，每次三名 Reviewer 全部如期重新提交赞成票：

```
初始超时 HOLD: state=CONSENSUS_CHECK
  第 1 次 RETRY_REVIEW + 三人全部重交 -> state=CONSENSUS_CHECK round=1
  第 2 次 RETRY_REVIEW + 三人全部重交 -> state=CONSENSUS_CHECK round=1
  第 3 次 RETRY_REVIEW + 三人全部重交 -> state=CONSENSUS_CHECK round=1
人工 APPROVED 后终局票面: responded=3 breakdown={'approve': 2, 'reject': 0, 'abstain': 1}
  votes=[('antigravity','YES_APPROVE'),('codex','YES_APPROVE'),('opencode','ABSTAIN')]
```

两重后果：

1. **`RETRY_REVIEW` 是无限循环**。上轮它因「沿用旧 dispatch 时间戳 → 瞬间再超时」而活锁；本轮 dispatch 时间戳确已刷新（复现 B 实测 `REVIEW_REQUESTS_DISPATCHED` 累计 2 条、3 条新 `REVIEW_REQUEST` AEP、`.reviews/` 旧票清空），**但持久化处置接管了同一个死结**。故障形态改变，可达状态未变——`RETRY_REVIEW` 仍是四个人工裁定选项中唯一不可用的一个，而它正是 PRD §6.1/§6.2 为超时准备的、语义上最保守的恢复路径。
2. **数据丢失**：`opencode` 三轮如期提交的赞成票全部被丢弃，终局票面仍记 `ABSTAIN`。这不再只是「卡住」，而是**把真实存在的评审意见从审计链上抹掉**，与 PRD §2.2:318「弃权……由 Orchestrator 记入本轮票面」的语义相悖——系统记录了一个该 Reviewer 从未表达过的弃权。

**测试为何未拦住**：新增的 `test_retry_review_override_clears_reviews_and_redispatches_fresh_requests` 只断言「旧票清除 + 生成新 deadline 派发审计与消息」，**不断言重试轮能否达成共识**。断言的是机制发生，不是目的达成——GUIDELINES §9 checklist **B** 的典型形态。58/58 全绿与本缺陷并不矛盾。

**修复方向**：E9 必须**解除**本轮的超时处置——例如落一条 `TIMEOUT_DISPOSITION_CLEARED` 审计并让 `historical_timed_out_ids` 只统计其后的记录，或把处置键从 `(task, round)` 改为 `(task, round, dispatch_generation)`。配套断言必须是「HOLD → RETRY_REVIEW → 三人如期重交 → **自动达成共识并进入 MERGING，票面 3 approve / 0 abstain**」。

---

### P2-CARRY-1（跨三轮遗留，本轮申请再次未提及）：`test-clis` 的 ANSI Strip 列是硬编码 `True`

`src/macao/adapter/integ_harness.py:108-109` 一字未动：

```python
clean_logs = session.get_clean_logs()
ansi_stripped_ok = True
```

`clean_logs` 取出后即被丢弃，判定值是字面量。本轮「Adapter 契约一致性」加固恰好改到**紧邻的** `PTYSession.get_clean_logs(tail_lines=...)` 签名，却未顺手把这一行改成真实断言。该项已在我 `ea536ab`、`f41b9da` 两轮报告中提出，**本轮是第三轮未修、且申请中未作任何说明**，而申请 §机验结果继续把「4/4 真实 CLI PTY 验证 PASS」整体作为**认证**证据引用。PTY Spawn 与 Clean Kill 两列是真实判定，唯 ANSI 一列不构成验证。

### P2-NEW-3（治理）：STATUS 注册表「47 份全量对账」被证伪，三处计数互不相符

治理规则 P1-3 要求「每轮申请复审前，STATUS 必须与 `reviews/` 目录**全量**对账」。实测：

| 口径 | 数量 |
|---|---|
| `ls docs/reviews/*review-result*.md \| wc -l` | **53** |
| STATUS 注册表**表内实际登记**的报告文件名（去重） | **51** |
| STATUS 注册表**标题声明** | **47** |

标题的 47 既不等于目录的 53，**也不等于它自己表内的 51**。申请文档 §一 GOV-1 行同样复述「完成 47 份报告全量对账」。未登记的 2 份为本轮 `bf5ae2d-grok.md` / `bf5ae2d-zcode.md`（晚于 STATUS 写就，时序可解释），但标题与表体自相矛盾的 4 份差额不可解释。**「全量对账 100% 一致」判为 CONTRADICTED。**

### P3-NEW-7：`LATE_REVIEW_ISOLATED` 未做幂等，同类缺陷第三次引入

HOLD 建立 + 迟到票在位时轮询 100 次：

```
audit DEADLOCK_DETECTED        = 1     ✅（上轮为 100，本轮已修）
audit REVIEWER_TIMEOUT_ABSTAIN = 1     ✅
audit LATE_REVIEW_ISOLATED     = 100   ❌（orchestrator.py:496，本轮新引入）
msg   HUMAN_OVERRIDE_REQUEST   = 1     ✅（上轮为 100，本轮已修）
审计总行数 = 107
```

本轮在两处修好了无界审计增长，却在新写的 P1-NEW-7 修复里第三次引入同一模式。因 P2-NEW-1（`limit=50` 消费方）已闭环，后果已从「功能中断」降为「日志无界增长」，故定 P3。

### P3-NEW-4（跨轮遗留）：`per_reviewer` 仍作弃权判定线，ping 与 30m 轮窗口仍未实现

`orchestrator.py:319`（派发）与 `:410`（检测）仍取 `timeouts.per_reviewer`（默认 `10m`）作为超时阈值。PRD §1.2:128 中 `WAITING_REVIEW` 超时列为 **`30m（10m/reviewer 触发 ping）`**——`per_reviewer` 是 **ping 触发器**，轮窗口是 `review_request`(30m)；全仓无任何 ping 实现。因后果为 fail-safe 的 HOLD，维持 P3。

### P3-NEW-5（跨轮遗留）：`audit_events` 仍无任何索引

`grep -c "INDEX" src/macao/storage/db.py` = **0**。本轮 `get_audit_events_by_type` 的调用点由 2 处增至 6 处以上（含每次共识评估 3 次定向查询），全表扫描频次显著上升。功能正确，建议补 `CREATE INDEX idx_audit_task_type ON audit_events(task_id, type)`。

---

## 四、治理事项：zcode 独立意见连续四轮缺席

GOV-1 的两处更名**属实**（`git log --name-status a2dcc24` 显示 `R100 ...-ea536ab-zcode.md → ...-ea536ab-qwen.md`，并新增 `...-f41b9da-qwen.md`、`...-7935da3-qwen.md`）。但同一错误在本轮**立即重演**：

| 轮次 | 文件名 | 正文第 4 行署名 | 状态 |
|---|---|---|---|
| `ea536ab` | `...-ea536ab-qwen.md` | qwen | ✅ 已勘误 |
| `7935da3` | `...-7935da3-qwen.md` | qwen | ✅ 正确 |
| `f41b9da` | `...-f41b9da-qwen.md` | qwen | ✅ 已勘误 |
| **`bf5ae2d`** | **`...-bf5ae2d-zcode.md`** | **qwen** | ❌ **本轮第四次错标** |

其余 6 份历史 zcode 报告署名均为 zcode，正确。

**zcode 的独立意见因此在 `ea536ab` / `7935da3` / `f41b9da` / `bf5ae2d` 连续四轮实际缺席；kimi 自 `7935da3` 后亦未再出具。** 按 GUIDELINES §8「沉默 ≠ 同意」，两者的缺席不得计入任何多数，STATUS 亦不得以「已完成 GOV-1 勘误」表述掩盖为「专家意见已齐备」。建议在文件落库前加一道 `评审人` 字段与文件名一致性校验，否则改名只是逐轮追赶。

---

## 五、定级建议

| 项 | 结论 | 依据 |
|---|---|---|
| **L1 DOC-ALIGNED** | **达成** | 文档/Schema/PRD 对照一致；`git diff --check` 洁净度声明属实 |
| **L2 SPEC-CODE-ALIGNED** | **达成（维持）** | 58/58 单测通过、5 轮 290 次执行 0 flake、Adapter 契约与 Schema 寻址静态检查通过、字段与 `vote_result.schema.json` 逐字段对应 |
| **L3 SCENARIO-VERIFIED** | **不予授予** | §2.1 要求「超时/弃权……场景均有可复现推演或测试证据」。超时**进入**与**迟到票隔离**证据现已完备（P1-NEW-7 属实闭环），但**退出**路径 `RETRY_REVIEW` 经实机复现为无限循环且丢弃如期票（P1-NEW-8），场景闭环仍不成立 |
| **PG-1** | **不予授予** | §2.2 要求「L2；**P0/P1 为零**」。现存 P1-NEW-8 一项 |
| **PG-2** | **不予授予** | §2.2 要求「PG-1 + 接口稳定 + 消费方场景测试」。PG-1 未达成 |

**须公平指出**：本轮是我跟踪的五轮中实质进展最大的一轮——上轮我提的 3 项 P1 中 2 项（P1-NEW-5、P1-NEW-7）**完全无保留闭环**，2 项 P2（P2-NEW-1、P2-NEW-2）亦闭环，P3-NEW-3 部分闭环，六项主动加固 5 项属实。阻断只剩 **1 项 P1**，且它不是新缺陷，而是两个正确修复未做语义调和的产物。

### 建议的最小放行条件

1. **P1-NEW-8**：E9 解除本轮超时处置（落 `TIMEOUT_DISPOSITION_CLEARED` 审计并让 `historical_timed_out_ids` 只统计其后记录，或把处置键扩为 `(task, round, dispatch_generation)`）。**验收断言必须是**「HOLD → `RETRY_REVIEW` → 三人如期重交 → 自动进入 `MERGING`，票面 3 approve / 0 abstain」，而非仅断言清票与重派发。
2. **P2-CARRY-1**：`integ_harness.py:109` 用 `clean_logs` 实际断言无 ANSI 序列（如 `re.search(r"\x1b\[", clean_logs) is None`），或在报告中把该列标注为「未验证」；连续三轮未修，不宜再随认证申请一并引用为证据。
3. **P2-NEW-3**：STATUS 注册表标题、表体与 `reviews/` 目录三者对齐（当前 47 / 51 / 53），并把本轮 2 份报告登记入表。
4. **P3 类**：`LATE_REVIEW_ISOLATED` 幂等（P3-NEW-7）、ping 与 30m 轮窗口（P3-NEW-4）、审计索引（P3-NEW-5）可随后续轮次处理，不阻断。
5. **治理**：修正 `...-bf5ae2d-zcode.md` 文件名，并在落库流程中加入「`评审人` 字段与文件名一致」的校验；补齐 zcode（四轮）与 kimi（三轮）的独立意见，补不齐则在 STATUS 中标注「缺席、不计入多数」。

---

## 六、附：本轮复现命令

```bash
# 机验清单 1/2/5
PYTHONPATH=src python3 -m unittest discover tests
for i in 1 2 3 4 5; do PYTHONPATH=src python3 -m unittest discover tests 2>&1 | tail -3; done
git diff --check f41b9da..HEAD; echo "rc=$?"

# 机验清单 3/4
PYTHONPATH=src python3 -m macao.cli.main test-clis
PYTHONPATH=src python3 -m macao.cli.main e2e-run

# 复现 A（P1-NEW-7）：3 Reviewer / per_reviewer="0s" / 2 赞成 + 1 超时 -> HOLD；
#   迟到者补交后再次 collect_and_evaluate_consensus -> 仍 CONSENSUS_CHECK、LATE_REVIEW_ISOLATED 落库
# 复现 B（P1-NEW-6）：HOLD 后 resolve_override("RETRY_REVIEW")
#   -> 3 条新 REVIEW_REQUEST、REVIEW_REQUESTS_DISPATCHED 累计 2 条、.reviews/ 清空（机制属实）
# 复现 F（P1-NEW-8）：在复现 B 之后三人全部如期重交 -> 仍 CONSENSUS_CHECK；
#   连续 3 次 RETRY_REVIEW 循环不变；人工 APPROVED 后 opencode 三轮如期票全部丢弃、终局记 ABSTAIN
# 复现 C（P1-NEW-5）：r1 签字 -> 新 commit c2 / round 2 -> execute_merge_pipeline(require_signoff=True) 拒绝；
#   补授 c2 签字后放行
# 复现 D（P2-NEW-1）：签字后灌 200 条审计 -> 合并仍成功（limit 窗口截断已消除）
# 复现 E（P2-NEW-2）：CODING 态 resolve_override("APPROVED") -> ValueError，磁盘/DB 均无残留

# 六项加固静态与动态核查
PYTHONPATH=src python3 -c "from macao.adapter.base import AgentAdapter; print(sorted(AgentAdapter.__abstractmethods__))"
PYTHONPATH=src python3 -c "
import os; from macao.core.schema import get_schemas_dir
print(get_schemas_dir()); os.environ['MACAO_SCHEMAS_DIR']='<真实存在的目录>'; print(get_schemas_dir())"
PYTHONPATH=src python3 -c "
from macao.workflow.orchestrator import parse_duration
for v in ['10m','30s','1h','2d','600','','abc','10x',None]:
    try: print(v, parse_duration(v))
    except Exception as e: print(v, type(e).__name__, e)"

# 遗留项与治理核查
grep -c "INDEX" src/macao/storage/db.py
sed -n '108,110p' src/macao/adapter/integ_harness.py
grep -n "LATE_REVIEW_ISOLATED" src/macao/workflow/orchestrator.py
ls docs/reviews/*review-result*.md | wc -l
grep -o '2026-[0-9-]*-review-result-[A-Za-z0-9.-]*\.md' docs/reviews/STATUS.md | sort -u | wc -l
for f in docs/reviews/*zcode*.md; do echo "$f: $(grep -m1 '评审人' $f)"; done
```
