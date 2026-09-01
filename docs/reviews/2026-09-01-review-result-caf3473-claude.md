# MACAO 全量用例体系（UseCases）PRD v2.5 对齐 评审结论

- **评审日期**：2026-09-01
- **评审人**：`claude`
- **评审对象**：[`docs/reviews/2026-09-01-review-request-UseCases-v2.5-Alignment.md`](2026-09-01-review-request-UseCases-v2.5-Alignment.md)
- **实际评审 commit**：**`caf3473`**（工作区 clean）。申请 §基线声明为 `2c40cd5`，但 `caf3473` 又修改了在审交付物 `UC6-issue-triage-rework.md`，故以 HEAD 为准（见 U-12）
- **评审基准**：`docs/MACAO_REVIEW_GUIDELINES.md` v1.0 §1–§6、§9、§11
- **对齐基准**：`docs/MACAO_PRD_v2.md`（PRD v2.5 权威基准）、`docs/schemas/*.schema.json`（机器契约）、`docs/usercases/PRODUCT-FACTS.md` F-1～F-22
- **申请定级**：L1 DOC-ALIGNED / PG-0
- **机器票**：`NO_APPROVE`
- **结构化 issue**：`BLOCKING` × 5（P1），`ADVISORY` × 8（P2 × 5 / P3 × 3）

---

## 结论

**不予授予 L1 DOC-ALIGNED / PG-0。**

用例体系的**主干确实已经对齐 v2.5**，而且有几处是我这几轮反复要求、这次真正做到了的：UC-5 的三态决策表与纯整数五重门禁、UC-7 的五选项闭合与「DEADLOCK 已即时落盘、裁定写独立 `admin_override.json`、严禁二次回写」、UC-9 对 `accounted` 与非弃权有效集合 $E_N/E_W$ 的严格切分、UC-4 的产物层去重（f4/A5/E5）、UC-6 的 100% 穷尽与 `FINAL` 严禁遗留 `NEEDS_ADMIN`。申请 §4 的四组自动化结论我逐条重跑，**全部属实**（13 份文档控制字符 0、fixtures 8/8 + 反例全拦截、镜像 0 diff、86/86 PASS）。用例集内全部 YAML/JSON 围栏可解析，UC-6 的处置示例对 `review_disposition.schema.json` 校验 **PASS**。

**但用例作为「Phase 1~5 研发实施与测试验收的官方操作基准」尚不成立**，存在 5 项 P1，全部是「照用例实现会得到与 PRD / 契约不同的结果」：

1. **U-1 处置产物路径分裂**：UC-6（处置用例本身）与 README 单写者表写 `.macao/executor.disposition.yml`，而 PRD §2.5、FAQ Q14/Q15、UC-1 写 `.macao/.dispositions/r<round>/executor.disposition.yml`。PRD §3.2 Layer 1c **按后者路径读取**——照 UC-6 实现，编排器永远读不到处置产物，任务在 `CONSENSUS_CHECK` 永久 HOLD。
2. **U-2 AEP Type 字母整体错位一位**：UC-2 与 UC-4 / README 把 `DEVELOPMENT_STARTED` 记为 Type B、`REVIEW_REQUEST` 记为 Type C，而 PRD §2.4 的权威表是 Type A / Type B（Type C 是 `REVIEW_RESPONSE`）。UC-7 的 Type H 又是对的，用例集**内部也不自洽**。
3. **U-3 `.review.yml` 的 issue 列表字段名错**：用例用 `issues[]`，PRD §2.2 与 `review_manifest.schema.json` 用 `items[]`（Schema **不存在** `issues` 属性）。UC-4 §6 验收第 5 条直接把 `issues[]` 当断言对象。
4. **U-4 UC-8 丢掉了 Pre-merge Evidence Push 校验，并把两阶段封存的顺序做反了**：PRD §14.5 第 1 步与 §3.3 E4 伴随动作要求**合并前**用 `ls-remote` 校验 evidence ref 已推送；UC-8 五道关卡从「检出」起步，evidence 提升被放到关卡 5 **push 成功之后**。这正是两阶段封存要防的失败模式。
5. **U-13 两份用例的产物示例通不过其权威契约**：`UC3-dev-checkpoint.md:33` 的 `.dev.yml` 示例缺 `full_document.evidence_commit`；`UC1-init-gemini.md:126` 的「生成的 `macao.yaml` 规格示例」整体停留在 **v2.4**（`version: "2.4"`、`policy.consensus_strategy` 而非 `consensus_rule`、无任何加权字段）。后者是 `macao init` 被文档规定要**生成**的产物。

五项都是逐字修订即可闭环，无设计变更。按 **F-17**，需要修复后才能作为基准的「有条件通过」在机器语义上属阻断性不通过，故机器票为 `NO_APPROVE`。

---

## 0. Reviewer 自审记录（GUIDELINES §9）

### 0.1 本轮撤回的一项拟议判定

我一度准备就「`.macao/state.db`」提 P2——理由是 UC-1/UC-2/UC-10/README 都写死了该路径，而 PRD 未定义。逐条核对后确认 **PRD 通篇只写「SQLite State Store」（L1272、L1537），从未给出文件名**。用例给出比权威基准更具体的落地路径，属于**细化**而非**冲突**，不构成 L1 的交叉引用矛盾。该项**不予提出**。

（对照：U-8 之所以成立，是因为 UC-3 对 **E6 转移守卫**加严——守卫语义是 PRD §3.3 明确定义过的东西，用例改写守卫与用例细化路径不是一回事。）

### 0.2 一处需要先证伪自己再下结论的地方

发现 UC-8 只有五道关卡、而 PRD §14.5 有六步时，我没有直接判「缺一步」——先把 UC-8 关卡 1 与关卡 5 的正文完整读完，确认 `ls-remote` / evidence 预推送**确实没有出现在任何一关**（关卡 1 只做 target 检出与 ff 可行性 + E4a 硬校验前置；关卡 5 是 push 后才提升 evidence）。确认为真实缺失且顺序相反后才登记 U-4。

### 0.2b 一项本可自查而未查到的遗漏（由同行报告触发后复核确认）

我对 13 份用例做的围栏检查只做到**可解析**（`yaml.safe_load` / `json.loads` 全部成功），**没有把可对应到既有契约的示例逐一送去 Draft-07 校验**——只单独校验了 UC-6 的处置示例。同行 grok 在同一 commit 的报告指出 UC-3 与 UC-1-gemini 两处示例不过契约；我据此补做全量校验，**独立复现并确认为真**（见 U-13），且发现 UC-1-gemini 的问题比「缺字段」更重（整份示例是 v2.4 规格）。

登记：**「能解析」不等于「合契约」**，此后凡用例/文档中可映射到 `docs/schemas/` 的产物示例，必须逐份跑 validator，而不是只跑解析器。该检查已补入 §五脚本 D。

### 0.3 强制自检 5 项

| # | 检查项 | 本轮结果 |
|---|---|---|
| 1 | 字段名 vs 实际读取路径 | **CONTRADICTED ×3**：U-1（处置路径 vs Layer 1c 读取路径）、U-2（Type 字母）、U-3（`issues[]` vs 契约 `items[]`）。三项均为 GUIDELINES §9 模式 A |
| 2 | 每处「已完成」是否有证据 | 申请 §4 四组自动化结论**全部属实**；§2/§3 有 3 处与交付物或权威基准不符（U-5、U-7 及 U-4 的关卡描述） |
| 3 | 确定性用语是否标注 | 申请称「100% 机器语义级对齐」「高度一致」——被 4 项 P1 证伪；用例正文未见未标注的确定性断言 |
| 4 | 代码块是否真能解析 | **解析层全部 PASS**（13 份文档全部围栏解析成功，0 失败）；**契约层 2 处 FAIL** → U-13（UC-3 `.dev.yml` 缺 `evidence_commit`；UC-1-gemini `macao.yaml` 为 v2.4 规格）。我首轮只做了解析检查，见 §0.2b |
| 5 | 每个 P1 是否给出可复现证据 | 是；四项均附文件 + 行号，并给出可重跑脚本（§五） |

### 0.4 连续漏审模式登记

前两轮登记的两条纪律本轮均生效并复用：①验证脚本按语义锚点定位（本轮直接复用于 UC 代码块提取）；②反例/差异结论必须确认成因（§0.2）。本轮新增一条：**「用例比 PRD 更具体」与「用例与 PRD 冲突」必须分开判**，前者不是缺陷（§0.1）。

### 0.5 证据类型适用性

DOC / SPEC 为主；对用例内嵌产物示例做了 Draft-07 实测（**TEST**）；对 FSM 场景做了手工重放（**SIM**）。申请目标为 L1 / PG-0，**CODE / OPS 判为 NOT_APPLICABLE**；仅在 U-6 中引用 CLI 实际子命令作为旁证，不作为定级依据。

---

## 一、已对齐 / 已确认项（独立复现，非采信自述）

1. **UC-5 计票主干完全对齐 D-1**：决策表三态（`APPROVED` / `REWORK_REQUIRED` / `DEADLOCK`）与 PRD §2.3 规则 6 逐字同构；五重门禁公式（$3w_i<2W$、$E_N \ge \lceil 2N/3 \rceil$、$E_W \ge \lceil 2W/3 \rceil$、$3W_{win} \ge 2E_W$、胜方席位 $\ge 2$）与 PRD §2.3、FAQ Q15 三处一致；「DEADLOCK 即时写盘不可变 `vote_result`」在 UC-5 决策表与 §2.d 两处明写。
2. **UC-7 是对齐质量最高的一份**：`--choice APPROVED|REWORK|RETRY_REVIEW|CANCEL|EXTEND` **五选项闭合**（与 PRD §3.3 E7、§6.1、§14.1 一致）；`admin_override.json` 字段清单（`override_id`/`trigger`/`choice`/`admin_identity`/`exempt_issue_ids`）与 `admin_override.schema.json` 的 `required` 对得上；验收标准第 2 条明写「DEADLOCK HOLD 期间 `vote_result.json` 已经存在且 `decision=DEADLOCK`；裁定后…内容与哈希无任何改写」。
3. **UC-9 的超时集合边界正确且唯一**：「超时席位记 `ABSTAIN` 计入 `accounted` 以触发 E3 判定，但**严格排除在有效选票集 $E_N, E_W$ 之外**」；迟到票在计票前可替换 pending 标记、落盘后隔离为 `LATE_REVIEW_ISOLATED` 审计。这条正是 Codex 上一轮 P1-7 要求的三集合统一，已落实。
4. **UC-4 的产物层去重完备**：P4 去重前置、f4 去重取最新合法票、A5「同 reviewer_id 两份同轮票 → 不双计」、E5「崩溃重启后重复提交 → f4 幂等」。GUIDELINES §6 第 5、6 条由此可唯一推出。
5. **UC-6 处置契约对齐**：100% 精确穷尽、`FINAL` 严禁遗留 `NEEDS_ADMIN`、`requires_new_checkpoint` 必填布尔分流 E4/E5a、E1 遗漏或未知 id 拒收。**实测其 YAML 示例对 `review_disposition.schema.json` 校验 PASS**（`caf3473` 把 `executor_id` 改为 `executor{}` 对象正是这项的最后一环）。
6. **UC-3 的信封与信号规范对齐**：`.dev.yml` 仅摘要 + 指针 + sha256 + `signal: EXPLICIT`；A1 明确 `signal: IMPLICIT` 不转移、只产 Layer 2 预警——与 `dev_manifest.schema.json` 现行 `signal: {"enum":["EXPLICIT","IMPLICIT"]}` 同构。
7. **README 单写者垄断表方向正确**：五大产物的写者归属（Executor / Reviewer / Orchestrator / Executor / Admin）与 PRD §16.1、F-13、F-20 一致（**路径写法有误，见 U-1**）。
8. **申请 §4 自动化结论全部属实**：`docs/usercases/*.md` 共 **13 份**、控制字符 **0**；`fixtures/valid` **8/8 PASS**、`fixtures/invalid` **全部按预期拦截**；`docs/schemas/` ↔ `src/macao/schemas/` **8 份逐字节一致**；`PYTHONPATH=src python3 -m unittest discover tests` → **Ran 86 tests, OK**；`compileall` rc=0。（注：§4 声明的是控制字符与测试，未声称用例示例全部通过 Schema——后者的实测结果见 U-13）

---

## 二、P1：必须先解决（4 项）

### U-1　处置产物路径三方分裂，照 UC-6 实现会导致任务永久 HOLD

| 出处 | 路径 |
|---|---|
| **PRD §2.5（权威基准）L638** | `.macao/.dispositions/r<round>/executor.disposition.yml` |
| **PRD §3.2 Layer 1c（读取方）** | `f'.macao/.dispositions/r{rnd}/executor.disposition.yml'` |
| `FAQ.md` Q14 L284 / Q15 L301 | `.macao/.dispositions/r<round>/executor.disposition.yml` |
| `UC1-init-glm.md:112` | `.macao/.dispositions/r<round>/executor.disposition.yml` |
| **`UC6-issue-triage-rework.md:24`** | **`.macao/executor.disposition.yml`** ✗ |
| **`README.md:97`（单写者垄断表）** | **`.macao/executor.disposition.yml`** ✗ |
| 申请 §2 item 8 / §3 D-9 | `.macao/executor.disposition.yml` ✗ |

**失败路径是确定的**：PRD §3.2 Layer 1c 在 `CONSENSUS_CHECK` 且 `requires_disposition == true` 时，从 `.macao/.dispositions/r{rnd}/executor.disposition.yml` 读取并要求 `disposition_status == 'FINAL'`；读不到就 `return AgentState.CONSENSUS_CHECK`（保持 HOLD）。执行者若按 UC-6 写到 `.macao/executor.disposition.yml`，编排器永远读不到，E4 与 E5a 都不会触发——任务在 `CONSENSUS_CHECK` 无限 HOLD，且没有任何报错。

**为什么判 P1**：UC-6 是处置流程的**操作基准**，README 单写者表是全体 UC 的**横切规范**，两者同时错在同一处。GUIDELINES §5 明文禁止同一产物多套路径；这里还叠加了 §9 模式 A（写入位置 ≠ 读取位置 → 运行时静默失败）。

**验收标准**：UC-6 §2.b 与 README 单写者表统一为 `.macao/.dispositions/r<round>/executor.disposition.yml`；`grep -rn 'executor\.disposition\.yml' docs/` 的每一处路径前缀一致。

### U-2　AEP Type 字母在用例集中整体错位一位，且用例集内部不自洽

PRD §2.4 权威对照表：

| # | 消息类型 | 标识 |
|---|---|---|
| 1 | `DEVELOPMENT_STARTED` | **Type A** |
| 2 | `REVIEW_REQUEST` | **Type B** |
| 3 | `REVIEW_RESPONSE` | **Type C** |
| … | … | … |
| 8 | `HUMAN_OVERRIDE_REQUEST` | Type H |

用例集实际写法：

| 位置 | 写法 | 应为 |
|---|---|---|
| `UC2-task-create.md:51` | 「AEP 消息（**Type B**）只含：`task_id`、`title`、`success_criteria`、`source_branch`…」——这是 `DEVELOPMENT_STARTED` 的 payload | Type A |
| `README.md:43` | UC-2「下发 **Type B** 信封」 | Type A |
| `UC4-review-dispatch.md:7` | 「原样放入 AEP/1.1 `REVIEW_REQUEST`（**Type C**，零 base64 内联）」 | Type B |
| `README.md:45` / `README.md:67` | UC-4「下发 **Type C**」/「`REVIEW_REQUEST`（**Type C**…）」 | Type B |
| `UC7-human-override.md:25` | 「`HUMAN_OVERRIDE_REQUEST`（**Type H**…）」 | **正确** ✓ |

即：A/B/C 段整体后移一位，而 H 段正确——用例集**自身**对同一套字母编号给出了两种口径。申请 §2 item 4/item 6 沿用了错误写法。

**影响**：Type 字母是 PRD §2.4 为 8 类消息建立的**唯一标识**，用例是编写测试套件的操作基准；按 UC-2 写「Type B 只含 task_id/title/success_criteria」的测试会与 `REVIEW_REQUEST` 的 payload 断言直接冲突。

**验收标准**：UC-2、UC-4、README 三处改为 Type A / Type B；`grep -rn 'Type [A-H]' docs/usercases/` 的每一处与 PRD §2.4 表逐行对齐。

### U-3　`.review.yml` 的 issue 列表字段名与机器契约不符

- **契约**：`docs/schemas/review_manifest.schema.json` 的 `properties` 为 `[version, timestamp, task_id, reviewer, checkpoint_ref, review_round, full_document, opinion, **items**, vote, abstain_reason]`——**没有 `issues` 属性**；
- **PRD §2.2** 的示例与互锁约束全部使用 `items:`；
- **用例集**：`README.md:95`（单写者表「专家票面与问题索引信封（三值 `vote`、`opinion`、**`issues[]`**）」）、`UC1-init-glm.md:100`、**`UC4-review-dispatch.md:81`（§6 验收第 5 条：「**`issues[]`** 的 id 均带 reviewer 前缀且未被改写」）**。

UC-4 §6 是「可测验收标准」，把一个契约中不存在的字段名写成断言对象，测试要么断言不到、要么按 UC 命名产出无法通过 Schema 的 `.review.yml`。属 §9 模式 A + §5 字段命名一致性。

**验收标准**：三处 `issues[]` 改为 `items[]`；`grep -rn 'issues\[\]' docs/` 归零（`issues_index` 是 `vote_result` 的字段，与此无关，不要误改）。

### U-4　UC-8 缺失 Pre-merge Evidence Push 校验，两阶段封存顺序被倒置

**PRD 侧（三处一致）**：
- §14.5 第 **1** 步：「**Pre-merge Evidence Push 校验**：Orchestrator 校验 `refs/macao/evidence/<task_id>/r<round>` 已成功推送到远端（经 `ls-remote` 校验）」；
- §3.3 E4 伴随动作：「§14.5：检出 → **pre-merge evidence push 校验** → merge → CI gate → 人工签字 → push」；
- §5.4 第 2 条「两阶段验证」：Pre-merge Seal 在**进入源码合并前**完成，Post-merge Seal 在合并推送成功后生成。

**UC-8 侧**：§2 标题为「主成功场景（**五道关卡**顺序执行）」，五关卡为 **① 检出与上游同步 → ② 技术合并 → ③ CI gate → ④ 人工签字 → ⑤ 推送与通告**。我逐关卡读完正文确认：

- 关卡 1 只做 target 检出、ff 可行性确认与「自 E4 起至 push 不得产生新 commit」的 E4a 硬校验前置——**无 evidence ref、无 `ls-remote`**；
- 关卡 5 才写「push 成功 → E4a → `DONE` … 本轮全部产物**提升至 canonical evidence ref**」——evidence 提升发生在源码 push **之后**。

即 UC-8 把 PRD 的「先封存证据、再合并源码」倒置为「先合并源码、再提升证据」，并整体删除了 `ls-remote` 预校验这一关。

**为什么判 P1**：这不是措辞差异，而是审计完整性保证的**方向被反转**。两阶段封存存在的意义就是防止「源码已合入、证据未落地」这一状态；按 UC-8 执行，push 成功后、evidence 提升前的任何中断都会产生一个**有合并、无证据**的不可追溯 checkpoint。UC-8 被申请 §2 item 10 明确列为 `MERGING → DONE` 的操作基准，Phase 3 的测试套件将据此编写。

**验收标准**：UC-8 §2 改为**六道关卡**，新增「关卡 0/1：Pre-merge Evidence Seal（`ls-remote` 校验 `refs/macao/evidence/<task_id>/r<round>` 已推送，未推送 → 不得进入技术合并）」；关卡 5 拆为「push 源码」与「Post-merge Seal」；同步修正申请 §2 item 10 与 §3 D-7 的关卡描述；UC-8 §6 验收补一条「evidence 未推送时不得进入关卡 2」的 fail-closed 断言。

### U-13　两份用例的产物示例通不过其权威机器契约，其中一份整体停留在 v2.4

把 13 份用例中**可映射到 `docs/schemas/` 的产物示例**逐份送 Draft-07 校验（§五脚本 D），结果：

| 示例 | 契约 | 结果 |
|---|---|---|
| `UC6-issue-triage-rework.md:26` | `review_disposition.schema.json` | **PASS** ✓ |
| `UC3-dev-checkpoint.md:33` | `dev_manifest.schema.json` | **FAIL(1)** — `['full_document'] 'evidence_commit' is a required property` |
| `UC1-init-gemini.md:126` | `macao_config.schema.json` | **FAIL(1)** — `['policy'] 'consensus_rule' is a required property` |

**UC-3** 的 `.dev.yml` 示例自身标 `version: "v2.5"`，`full_document` 却只给了 `path` 与 `sha256`，缺 v2.5 契约必填的 `evidence_commit`——而 evidence commit 正是 D-8「证据进入独立 evidence ref」的引用锚点，缺了它，全文引用就退回成一个无法定位到具体 evidence 版本的路径。

**UC-1-gemini** 的问题更重。该节标题是「**5. 产物规格定义（Generated Artifacts）→ 生成的 `macao.yaml` 规格示例**」——即 `macao init` 被文档规定要**生成**的东西，其内容却整体是 v2.4：

```yaml
version: "2.4"                          # ← 自我声明为 v2.4
policy:
  consensus_strategy: "majority"        # ← v2.5 契约的字段名是 consensus_rule
  max_rework_rounds: 3
  min_effective_votes: 3
```

对照 PRD §13 与 `macao_config.schema.json`：字段名应为 `policy.consensus_rule`（`required`），取值应为 `weighted_2/3_v1`；且**完全没有** `vote_weight`、`dictator_cap_enabled`、`minimum_winning_seats`、`seat_quorum_required`、`weight_quorum_required`、`timeouts.review_disposition`、`aep.max_message_bytes` 等 v2.5 加权共识与预算字段。`consensus_strategy` 这个键在全库 v2.5 文档与契约中**不存在**。

**为什么判 P1**：申请把 UC-1 两份并列为 deliverable #3，并称用例体系已达成「100% 机器语义级对齐」。一份规定初始化产物形态的用例若照此生成配置，产出的 `macao.yaml` 会被 Config Loader 直接拒绝启动（PRD §13「失败则拒绝启动并列出错误项」）；即使侥幸加载，也会按等权旧算法而非 `weighted_2/3_v1` 运行——正是 D-5/D-6 要消除的分歧。

**验收标准**：UC-3 示例的 `full_document` 补 `evidence_commit`；UC-1-gemini §5 的 `macao.yaml` 示例整体按 PRD §13 重写（`version` 与 `consensus_rule` 起，补齐加权与预算字段）；§五脚本 D 全部行为 PASS。

---

## 三、P2：登记，Phase 1 前处理（5 项）

| ID | 问题 | 证据 |
|---|---|---|
| **U-5** | **README 与 UC-7 对 override 选项数互斥**。`README.md` §UC-7：「选项闭合：`APPROVED` / `REWORK` / `RETRY_REVIEW` / `CANCEL`（支持 `--exempt-issue-ids`）」——**漏 `EXTEND`**；而 `UC7-human-override.md:29` 与 §2.c 表、PRD §3.3 E7、§6.1、§14.1、`admin_override.schema.json` 的 `choice` 枚举均为**五值**。申请 §2 item 9 与 §3 D-2 同样写「4 大闭合选项」。README 是用例目录的总览页，其口径与分册相反 | `README.md` §UC-7 vs `UC7-human-override.md:29` |
| **U-6** | **入口命令在权威基准中不存在**。`UC1-init-glm.md`（标题、§b、§2 主流程）、`UC1-init-gemini.md`（触发条件、时序图、示例）与 `README.md:42` 均以 **`macao init --agteam <team>`** 为唯一入口；PRD §14.1 第 2 步定义的是 `macao init --new` / `macao init --adopt-existing`，§14.2 另有 `macao adopt` 别名，**全文无 `--agteam`**。旁证（不作为定级依据）：实际 CLI `src/macao/cli/main.py:177` 的 `init` 只有 `--path` 一个选项，`--agteam` / `--new` / `--adopt-existing` 均不存在。UC-1 同时**未覆盖** PRD 定义的既有项目接管路径（`--adopt-existing`），而 F-6 明确要求 `macao init` 必须同时覆盖静态初始化与既有项目动态接管 | `UC1-init-glm.md:1/27/68`、`UC1-init-gemini.md:16/39/58`、`README.md:42` vs PRD L1416/L1429 |
| **U-7** | **申请 §3 的 D-1～D-9 与唯一定义该编号的文档六项不符，且 PRD 零处 D-x**。`PRD_CHANGE_PROPOSAL_v2.5.md` L34–42 是全库唯一定义 D-1～D-9 的地方：D-2=独立 `review_disposition`、D-3=Reviewer 显式 `ABSTAIN`、D-4=`BACKLOG`→`DEFERRED` 更名、D-5=`requires_new_checkpoint` 必填、D-6=加权三重 quorum、D-8=evidence ref、D-9=`init/doctor/reconcile/adopt` 边界。申请 §3 把这些编号重新指派为：D-2=独立 Admin Override、D-3=独立 Review Disposition、D-4=vote_result 三态、D-5=五重门禁、D-6=FSM 三投影、D-8=Checkpoint 拓扑单调、D-9=产物命名单写者——**七项语义被换掉，且提案的 D-3（ABSTAIN）与 D-4（DEFERRED 更名）在申请中整体消失**。同时 `grep -n 'D-[1-9]' docs/MACAO_PRD_v2.md` 结果为**空**，而 `README.md:89` 与 `:109` 两次写「PRD v2.5 D-1～D-9」——指向权威基准里不存在的编号体系。整份申请的对齐论证以此编号为索引 | 提案 L34–42 vs 申请 §3；PRD 全文 D-x 计数 = 0；`README.md:89/109` |
| **U-8** | **UC-3 对 E6 守卫加严而权威基准未同步**。`UC3-dev-checkpoint.md:16` P2：「本轮业务工作已产生**拓扑前进的新 commit**（**严格为上轮 `checkpoint_ref` 之子孙**且未被消费）」；PRD §3.3 E6 的守卫只写「新 source commit **!= 上一轮**」。「不等于」与「必须是子孙」是两个不同的判定（例如从上轮 checkpoint 的兄弟分支提交，满足前者、不满足后者）。申请 §3 把它列为「D-8: Checkpoint 拓扑单调前进约束」，但提案的 D-8 是 evidence ref（见 U-7），PRD 也只在版本历史行提到过 v2.3.1 的 `is_ancestor 拓扑校验`。用例可以比 PRD 更具体（如 `state.db` 路径，见 §0.1），但**不应单方面改写 PRD 已明确定义的转移守卫** | `UC3-dev-checkpoint.md:16` vs PRD §3.3 E6 |
| **U-9** | **UC-3 §2.g 保留 D-2 之前的双写模型残留**：「返工轮…差异：申请全文须含**采纳清单**（按 UC-6，引用上轮 `issues_index` 的 `id`：采纳哪些、不采纳哪些及理由——内容由执行者写）」。v2.5 下逐项处置是**独立不可变产物** `executor.disposition.yml`，且按 PRD §3.3 E6 必须在进入 E6 **之前**就已存在 FINAL 版本；把采纳清单再写进下一轮申请全文，等于同一决定存在两个载体，正是 D-2 要消除的双真源。UC-3 §2.g 应改为「申请全文**引用**上轮 FINAL disposition 的 `path + evidence_commit + sha256`」 | `UC3-dev-checkpoint.md` §2.g |

---

## 四、P3：可延期（3 项）

| ID | 问题 | 证据 |
|---|---|---|
| **U-10** | **gitignore 规则数四方分歧，且用例集内部就不一致**：`UC1-init-glm.md:58` f4 写「**8 规则**」；`UC10-existing-project-doctor.md:32` 与申请 §2 item 12 写「**9 条规则**」；PRD §20 只写「追加 `.macao/worktrees/` 与 `*.db`」（**2 条**）。逐条数实现 `src/macao/cli/wizard.py:83–92` 的 `required_rules` 为 **9 条**——即 **UC-10 是对的那一方，UC-1 与 PRD 都不对**。修订方向应是把 UC-1 与 PRD §20 对齐到 9，而非改 UC-10 | `UC1:58` / `UC10:32` / PRD L1582 / `wizard.py:83-92` |
| **U-11** | `UC3-dev-checkpoint.md:72` A3 引用命令 `macao checkpoint create --file`，并标注出处「PRD §14.2」。PRD §14.2 的运维命令表无此条目，全文亦无该命令（CLI 中同样不存在）。属悬空命令引用 | `UC3:72` vs PRD §14.2 |
| **U-12** | **申请钉死的基线不是实际评审对象**。申请写「当前代码与文档基线：`commit 2c40cd5`（`origin/main`）」，但 HEAD 为 `caf3473`，且 `caf3473` **又修改了在审交付物** `UC6-issue-triage-rework.md`（把 `executor_id: "cc-ds4"` 改为 `executor: {id, role, cli}` 对象以匹配 Schema）。按申请声明的 `2c40cd5` 复核，会把一个已修复的 Schema 不符项记为缺陷。这与 Codex 在 `2766c69` 轮登记的 P2-1 是同一问题，尚未形成纪律 | 申请文首 vs `git show caf3473 -- docs/usercases/UC6-issue-triage-rework.md` |

---

## 五、反例与边界场景推演（GUIDELINES §6 全量，按申请 §5.1 要求逐条核验）

| # | 场景 | 可唯一推出 | 依据（用例侧） |
|---|---|---|---|
| 1 | 2-reviewer 全部弃权 | **是** ✓ | UC-5 决策表第 3 行「其余一切（未达法定人数、1:1、全弃权）→ DEADLOCK 即时写盘」；UC-9「全体弃权 $\implies E_N=0 \implies$ 必然 DEADLOCK」 |
| 2 | 1 超时 + 1 批准 | **是** ✓ | UC-9 c3 记 ABSTAIN 计入 `accounted` 触发 E3，但排除于 $E_N/E_W$ → $E_N=1<\lceil4/3\rceil=2$ → DEADLOCK |
| 3 | 1:1 僵局 | **是** ✓ | UC-5 决策表；UC-7 §2.d 独立 `admin_override.json` |
| 4 | 3-reviewer 1:1:1 | **是** ✓ | UC-5 五重门禁：门禁 4 与门禁 5 均不满足 → DEADLOCK |
| 5 | 崩溃重启后重复提交投票 | **是** ✓ | UC-4 E5「f4 去重幂等；崩溃前已消费票不重复计数」 |
| 6 | 同 checkpoint 两份同 reviewer_id 票 | **是** ✓ | UC-4 P4 去重前置 + A5「不双计」 |
| 7 | `.dev.yml` 缺字段但 `signal=EXPLICIT` | **是** ✓ | UC-3 d1（Schema）与 d2（signal）两道独立门禁；A1 `IMPLICIT` 不转移 |
| 8 | 第二轮返工是否覆盖第一轮 | **是** ✓ | UC-3 A2 窗口内取最新、旧信封标 `STALE`；UC-8 关卡 5 归档至 `r<round>` |
| 9 | 人工接管超时后默认动作 | **是** ✓ | UC-7 适用场景含「处置超时」；PRD §6.1 总则 HOLD + 持续告警 |
| 10 | Git 冲突致 checkpoint 与工作区不一致 | **是** ✓ | UC-8 关卡 2「不自动解冲突（解冲突产生的改动=新变更=未评审）→ 转 UC-7 P6」；关卡 5 字节级硬校验 |
| 11 | `review_context` 载体与 Reviewer 工作流不一致 | **是（但见 U-2）** ⚠ | UC-4 明确「10 个必需与语义块、零 base64、worktree 内取 diff」，与 PRD §5.2/§5.3 同构；**但消息类型字母写错**（U-2） |

**申请 §5.1 点名的 5 类 fail-closed 拦截，逐条核验结果**：缺 `signal: EXPLICIT` → UC-3 A1 ✓；未拓扑前进的 commit → UC-3 P2 / E2 ✓（**但该约束强于 PRD，见 U-8**）；遗漏 issue 的 disposition → UC-6 E1 拒收 ✓；`FINAL` 含 `NEEDS_ADMIN` → UC-6 §规则「严禁遗留」+ Schema 实测拒绝 ✓；非法 `choice` → UC-7 E2 拒绝 ✓。**五类全部具备明确的 fail-closed 行为。**

**11 / 11 可唯一推出**——这一点用例体系做得好，本轮 4 项 P1 都不是「推不出结果」，而是「推出的结果与 PRD 不同」。

### 复现脚本

```bash
cd /path/to/macao && bash -s <<'SH'
echo "=== U-1 处置路径分裂（只看规范类文档，排除 reviews/ 历史报告）==="
for f in docs/MACAO_PRD_v2.md docs/FAQ.md docs/usercases/*.md; do
  grep -oE '\.macao/[A-Za-z0-9_./<>-]*executor\.disposition\.yml' "$f" | sort -u | sed "s#^#  $(basename $f): #"
done

echo; echo "=== U-2 Type 字母 vs PRD §2.4 权威表 ==="
sed -n "/^AEP v1.1 共定义/,/^$/p" docs/MACAO_PRD_v2.md | grep -E '^\| [0-9]' | cut -c1-70
grep -rn 'Type [A-H]' docs/usercases/*.md | cut -c1-120

echo; echo "=== U-3 issues[] vs 契约 items[] ==="
python3 -c "import json;d=json.load(open('docs/schemas/review_manifest.schema.json'));p=list(d['properties']);print(' schema properties:',p);print(' items:', 'items' in p,'| issues:', 'issues' in p)"
grep -rn 'issues\[\]' docs/usercases/*.md | cut -c1-120

echo; echo "=== U-4 UC-8 关卡 vs PRD §14.5 ==="
grep -n '^### 关卡' docs/usercases/UC8-merge-signoff.md
echo "--- PRD §14.5 步骤 ---"
sed -n "/^### 14.5/,/^---/p" docs/MACAO_PRD_v2.md | grep -E '^[0-9]+\.' | cut -c1-90
echo "--- UC-8 是否出现 ls-remote / pre-merge / evidence 预推送 ---"
grep -c 'ls-remote\|Pre-merge\|pre-merge' docs/usercases/UC8-merge-signoff.md

echo; echo "=== U-6 入口命令 ==="
grep -rn 'macao init --' docs/usercases/*.md docs/MACAO_PRD_v2.md | cut -c1-110

echo; echo "=== U-7 D 编号 ==="
echo "提案定义（唯一来源）:"; grep -c '^| D-[1-9]' docs/PRD_CHANGE_PROPOSAL_v2.5.md
echo "PRD 中 D-x 出现次数:"; grep -c 'D-[1-9]' docs/MACAO_PRD_v2.md || echo 0
SH

python3 - <<'PY'
import glob, json, re, yaml, jsonschema
# 用例集控制字符 + 围栏可解析性 + UC-6 示例对 Schema 校验
n = 0
for f in sorted(glob.glob('docs/usercases/*.md')):
    n += sum(1 for x in open(f, 'rb').read() if x in (9, 11, 12, 13))
print("用例文档数:", len(glob.glob('docs/usercases/*.md')), " 控制字符总数:", n)
bad = 0
for f in sorted(glob.glob('docs/usercases/*.md')):
    T = open(f).read().split('\n'); i = 0
    while i < len(T):
        m = re.match(r'^```(yaml|json)\s*$', T[i].strip())
        if m:
            j = i + 1
            while j < len(T) and T[j].strip() != '```': j += 1
            try:
                (json.loads if m.group(1) == 'json' else yaml.safe_load)('\n'.join(T[i+1:j]))
            except Exception as e:
                print("  解析失败", f, i + 1, str(e)[:60]); bad += 1
            i = j
        i += 1
print("围栏解析失败数:", bad)
# 脚本 D：把可映射到 docs/schemas/ 的用例示例逐份送 Draft-07 校验
#          —— 「能解析」不等于「合契约」，勿只跑解析器（本轮自审教训）
SCH = {k: json.load(open('docs/schemas/%s.schema.json' % k)) for k in
       ['dev_manifest', 'review_manifest', 'vote_result', 'review_disposition',
        'admin_override', 'macao_config', 'review_context', 'aep_envelope']}
def guess(d):
    if not isinstance(d, dict): return None
    k = set(d)
    if {'signal', 'development'} & k: return 'dev_manifest'
    if {'dispositions', 'disposition_status'} & k: return 'review_disposition'
    if 'override_id' in k: return 'admin_override'
    if {'vote', 'opinion'} <= k: return 'review_manifest'
    if {'decision', 'vote_breakdown'} <= k: return 'vote_result'
    if {'policy', 'team'} <= k: return 'macao_config'
    if {'protocol', 'payload'} <= k: return 'aep_envelope'
    if 'review_context' in k: return 'review_context'
    return None
print("--- 用例示例 vs 机器契约 ---")
for f in sorted(glob.glob('docs/usercases/*.md')):
    T = open(f).read().split('\n'); i = 0
    while i < len(T):
        m = re.match(r'^```(yaml|json)\s*$', T[i].strip())
        if m:
            j = i + 1
            while j < len(T) and T[j].strip() != '```': j += 1
            try: inst = (json.loads if m.group(1) == 'json' else yaml.safe_load)('\n'.join(T[i+1:j]))
            except Exception: i = j; continue
            g = guess(inst)
            if g:
                if g == 'review_context': inst = inst['review_context']
                errs = sorted(jsonschema.Draft7Validator(SCH[g]).iter_errors(inst), key=lambda x: list(x.path))
                print("  %-34s L%-4d %-20s %s" % (f.split('/')[-1], i + 1, g,
                      "PASS" if not errs else "FAIL(%d)" % len(errs)))
                for x in errs[:4]: print("        -", list(x.path) or "(root)", x.message[:110])
            i = j
        i += 1
PY
```

---

## 六、交叉文档需做的文字修订（最小闭环）

1. **U-1**：UC-6 §2.b 与 README 单写者表统一处置路径为 `.macao/.dispositions/r<round>/executor.disposition.yml`；同步修正申请 §2 item 8 与 §3 D-9。
2. **U-2**：UC-2、UC-4、README 的 Type 字母按 PRD §2.4 表改正（A = `DEVELOPMENT_STARTED`、B = `REVIEW_REQUEST`）；同步修正申请 §2 item 4/item 6。
3. **U-3**：README、UC-1、UC-4 的 `issues[]` 改为 `items[]`（注意勿误改 `vote_result` 的 `issues_index`）。
4. **U-4**：UC-8 补 Pre-merge Evidence Seal 关卡并调整两阶段封存顺序；补一条 fail-closed 验收断言。
5. **U-5**：README §UC-7 补 `EXTEND`；申请 §2/§3 同步改为五选项。
6. **U-6**：UC-1（两份）与 README 的入口命令改为 PRD §14.1 的 `--new` / `--adopt-existing`，或先在 PRD 中正式定义 `--agteam` 再由 UC 引用；补齐 F-6 要求的既有项目接管路径。
7. **U-7**：**统一 D 编号的唯一来源**——建议把提案 L34–42 的 D-1～D-9 表整体并入 PRD 附录，此后所有文档只引用 PRD 版本；修正申请 §3 的编号映射；README 两处「PRD v2.5 D-1～D-9」改为指向确定位置。
8. **U-8 / U-9**：UC-3 P2 的子孙约束或写入 PRD §3.3 E6，或放宽为与 E6 一致；§2.g 的采纳清单改为对上轮 FINAL disposition 的引用。
9. **U-10 ~ U-12**：gitignore 规则数取齐单一来源；删除或补定义 `macao checkpoint create`；今后每轮申请**钉死短 SHA** 而非 `origin/main`。

---

## 七、建议的闭环顺序与验收标准

| 序 | 事项 | 验收标准 |
|---|---|---|
| 1 | **U-1 / U-2 / U-3**（三项纯文本改名） | §五脚本对应段落：处置路径全库单一写法；`grep -rn 'Type [A-H]' docs/usercases/` 每处与 PRD §2.4 表一致；`grep -rn 'issues\[\]' docs/` 归零 |
| 1b | **U-13**（两处示例修订） | §五脚本 D 三行全 PASS；UC-1-gemini §5 的 `macao.yaml` 与 PRD §13 逐字段可对照 |
| 2 | **U-4**（UC-8 关卡重排） | UC-8 出现 `ls-remote` / Pre-merge Seal 且位于技术合并之前；关卡数与 PRD §14.5 步骤可一一对应；§6 验收含「evidence 未推送不得进入合并」断言 |
| 3 | 复评 L1 / PG-0 | 第 1～2 项（含 1b）闭合即可授予；建议最小差量快速复评，不要求重跑全量交付物核验 |
| 4 | **U-5 ~ U-9（P2）** | Phase 1 启动前处理；其中 U-7（D 编号唯一来源）建议优先，因为它是后续所有对齐论证的索引 |
| 5 | **把跨文档一致性检查固化为交付前门禁** | 本轮 4 项 P1 全部是「同一实体在不同文档中写法不同」，全部可脚本化检出：产物路径、消息类型字母、契约字段名、关卡/步骤序列。建议将 §五脚本的前四段纳入 CI，与前一轮建议的「PRD 正文示例纳入 fixture 回放」合并为同一道门禁 |

**不建议**：把 U-1 与 U-4 降级为 P2 放行。U-1 有确定的静默失败路径（永久 HOLD 且无报错），U-4 反转的是审计完整性保证的方向；两者都会在 Phase 1~5 按用例编写测试时被固化进测试断言，届时修复成本远高于现在。**同样不建议**：因本轮为 `NO_APPROVE` 而低估用例体系的质量——UC-5 / UC-7 / UC-9 / UC-4 四份的对齐是本项目文档轨迄今最扎实的，GUIDELINES §6 反例库 11/11 可唯一推出，申请 §4 的自动化结论无一夸大。

---

## 八、与其他 Reviewer 的交叉核对（GUIDELINES §8）

本报告完成前，同一 commit 的 [`2026-09-01-review-result-caf3473-grok.md`](2026-09-01-review-result-caf3473-grok.md) 已落地（机器票同为 `NO_APPROVE`，P1 × 3、无 P0）。逐项对照如下，凡采纳者均先自行复现：

**独立收敛（结论一致，证据各自取得）**
- **grok P1-1 = 本报告 U-1**（处置产物路径未收敛）。两份报告独立指向同一组文件与同一失败面。
- **grok P2-1 = U-12**（申请钉死 `2c40cd5`、HEAD 为 `caf3473`）；**grok P2-2 = U-5**（4 vs 5 选项）；**grok P2-6** 与 U-9 同源（UC-3 的采纳清单/`adoption.yml` 残留）。
- 申请 §4 的四组自动化结论，两份报告独立复跑结果一致，均判 VERIFIED。

**我据其提示复核后确认并采纳（记为本报告 U-13）**
- **grok P1-3**「待审用例 YAML 示例未全部通过自称唯一的契约」。我首轮只做了围栏**可解析**检查，未逐份送 Draft-07（见 §0.2b）。补做后独立确认两处 FAIL，并进一步查明 `UC1-init-gemini.md` 的问题不止缺字段——该「生成的 `macao.yaml` 规格示例」自我声明 `version: "2.4"`、使用 v2.5 不存在的 `consensus_strategy` 键、且完全没有加权与预算字段。

**据其提示复核后，修正了我自己的一项表述（U-10）**
- **grok P2-4** 指出 UC-1 f4 写「8 规则」、UC-10 写「9 规则」、`wizard.py` 实为 9 条。我原先只对比了 UC-10（9）与 PRD §20（2），据此把 UC-10 列为分歧一方。复核实现后确认 **UC-10 与实现一致，问题在 UC-1 与 PRD**，已按此改写 U-10 的修订方向。

**grok 报告的、我未独立取得证据因而不计入本报告结论的**
- grok P1-2（E7 `APPROVED` 且仍有未覆盖 issue 时，带 `EXEMPTED_BY_ADMIN` 的 FINAL 由谁写、能否无 FINAL 直跳 `MERGING`，UC-6 A2 / UC-7 §2.c / §16.1 单一写者三处推不出唯一边）。这一项与我在上一轮 PRD 文档轨登记的 M-3（§2.5 未记载 `override_id` 与 `EXEMPTED_BY_ADMIN` 的强制约束）指向同一处规范空洞，方向上我认为成立；但本轮我未对其做独立推演，故**不计入本报告的 issue 清单**，仅在此登记以供申请方一并处理。
- grok P2-3（UC-1-glm 拼接稿结构断裂）、P2-5（加权占比表述与纯整数原则的张力）、P2-7（UC-5 决策表压缩掉 `requires_disposition` HOLD 一步）、P2-8（AEP 预算未进 `aep_envelope.schema.json`）、P3-1（`source_branch` vs Schema `branch`）——同上，未独立复核，不计入。其中 P2-8 与我在 `2da1bc2` 轮登记的 M-4 同源。

**本报告独有、grok 未登记的**：U-2（AEP Type 字母整体错位，且 UC-7 的 Type H 正确导致用例集自身不自洽）、U-3（`issues[]` vs 契约 `items[]`）、U-4（UC-8 缺 Pre-merge Evidence Seal 且两阶段封存顺序倒置）、U-6（`macao init --agteam` 在 PRD 与 CLI 均不存在，且未覆盖 F-6 要求的接管路径）、U-7（申请 §3 的 D 编号与唯一定义源七项不符、PRD 零处 D-x）、U-8（UC-3 对 E6 守卫单方面加严）。

**票型**：`claude` = `NO_APPROVE`，`grok` = `NO_APPROVE`。两份报告在 U-1 / P1-1 上独立收敛。按 §8「沉默 ≠ 同意」，Codex / GLM / Kimi / Qwen / ZCode 本轮尚未出具，不计入任何一方。

需要说明与前一轮（`2da1bc2`，PRD 文档轨）的关系：那一轮我登记的 M-1 / M-2 / M-3 属**另一份申请**的范围，本轮不重复计入；`caf3473` 的提交信息称已关闭 Claude/Grok 在 `2da1bc2` 的发现（grok 报告确认其自身两项已闭环），该闭环应在 PRD 文档轨的下一次申请中由我复核，不影响本轮用例体系的定级。

---

## 附：机器票与结构化 issue 清单

| issue_id | severity | disposition_class | 摘要 |
|---|---|---|---|
| `claude/U-1` | critical | `BLOCKING` | 处置产物路径分裂：UC-6 与 README 写 `.macao/executor.disposition.yml`，PRD §2.5 / Layer 1c 读取方 / FAQ / UC-1 写 `.macao/.dispositions/r<round>/…`，照 UC-6 实现导致 `CONSENSUS_CHECK` 永久静默 HOLD |
| `claude/U-2` | major | `BLOCKING` | AEP Type 字母整体错位一位：UC-2/UC-4/README 的 Type B/C 应为 Type A/B；UC-7 的 Type H 正确，用例集内部不自洽 |
| `claude/U-3` | major | `BLOCKING` | `.review.yml` issue 列表字段名用 `issues[]`，契约与 PRD §2.2 为 `items[]`（Schema 无 `issues` 属性），UC-4 §6 验收断言直接引用错误字段 |
| `claude/U-4` | major | `BLOCKING` | UC-8 五道关卡缺 Pre-merge Evidence Push 校验，evidence 提升被置于源码 push 之后，与 PRD §14.5 / §3.3 E4 / §5.4 两阶段封存顺序相反 |
| `claude/U-13` | major | `BLOCKING` | UC-3 `.dev.yml` 示例缺 `full_document.evidence_commit`；UC-1-gemini「生成的 macao.yaml 规格示例」整体为 v2.4（`version: "2.4"`、`consensus_strategy` 而非 `consensus_rule`、无加权与预算字段），照此生成的配置会被 Config Loader 拒绝启动 |
| `claude/U-5` | minor | `ADVISORY` | README §UC-7 写「4 大选项」漏 `EXTEND`，与同集合的 UC-7 正文及 PRD 五选项互斥 |
| `claude/U-6` | minor | `ADVISORY` | UC-1 与 README 的入口命令 `macao init --agteam` 在 PRD §14.1 与实际 CLI 中均不存在，且未覆盖 PRD 的 `--adopt-existing` 接管路径（F-6） |
| `claude/U-7` | minor | `ADVISORY` | 申请 §3 的 D-1～D-9 与唯一定义源（提案 L34–42）七项语义不符，提案的 D-3/D-4 整体消失；PRD 全文零处 D-x，README 两处为悬空引用 |
| `claude/U-8` | minor | `ADVISORY` | UC-3 P2「严格为上轮 checkpoint 之子孙」强于 PRD §3.3 E6 的「!= 上一轮」，用例单方面改写 FSM 转移守卫 |
| `claude/U-9` | minor | `ADVISORY` | UC-3 §2.g 仍要求返工申请全文内含采纳清单，为 D-2 之前的双写模型残留 |
| `claude/U-10` | trivial | `ADVISORY` | UC-10「gitignore 9 条规则」与 PRD §20 的 2 条无共同来源 |
| `claude/U-11` | trivial | `ADVISORY` | UC-3 A3 引用的 `macao checkpoint create --file`（标注 PRD §14.2）在 PRD 与 CLI 中均不存在 |
| `claude/U-12` | trivial | `ADVISORY` | 申请钉死基线 `2c40cd5`，而 HEAD `caf3473` 又修改了在审交付物 UC-6；今后每轮须钉死短 SHA |

```
vote: NO_APPROVE
requires_new_checkpoint: true   # 需产生新的文档 checkpoint；U-1~U-3 为纯文本改名，U-4 为关卡重排，建议最小差量快速复评
```
