# 全量用例体系（UseCases）PRD v2.5 对齐独立评审结论（`caf3473`）

- **评审日期**：2026-09-01
- **评审人**：grok
- **评审对象**：[`docs/reviews/2026-09-01-review-request-UseCases-v2.5-Alignment.md`](2026-09-01-review-request-UseCases-v2.5-Alignment.md)
- **申请声称基线**：`2c40cd5`
- **实际评审对象**：`caf3473`（`origin/main` HEAD；含申请文件本身，以及「关闭 Claude/Grok `2da1bc2` 发现」的 Schema/PRD/UC-6 差量）
- **对齐基准**：`docs/MACAO_REVIEW_GUIDELINES.md` §1–§6、§9、§11；`docs/MACAO_PRD_v2.md`（PRD v2.5）；`docs/usercases/PRODUCT-FACTS.md` F-1～F-22；提案 D-1～D-9
- **定级申请**：L1 DOC-ALIGNED / PG-0（用例文档体系与 PRD v2.5 实施基线全面对齐）
- **机器票**：`NO_APPROVE`
- **证据**：`BLOCKING` × 3（P1），`ADVISORY` × 若干；**无 P0**

**结论：不授予 L1 DOC-ALIGNED / PG-0。** 主旅程（UC-5 计票 → UC-6 处置 → UC-8 合并）、D-1 不可变 `vote_result`、D-4 三值决策、D-5 五重门禁正文、D-8 拓扑前进、超时 ABSTAIN 计入 `accounted` 但不进 $E_N$/$E_W$，在 UC-4/5/9 主路径上已经能读出来，不是换标题。申请 §4 的控制字符清零、8 份 Schema 双副本、fixture 正例/反例、86/86 测试，本机独立复跑均成立。上轮 grok 在 `2da1bc2` 的 P1-1（`2/3_majority` 枚举）与 P1-2（UC-6 `executor_id`）在 **HEAD 上已闭环**。

但申请「全量 13 份用例与 D-1～D-9 **100% 机器语义级对齐**」不成立：处置产物路径在用例体系内部及相对权威 PRD 仍是两套；E7 `APPROVED` 有 issue 时谁写带 `EXEMPTED_BY_ADMIN` 的 FINAL 仍推不出唯一边（上轮 P1-3 未闭）；待审 YAML 示例未全部通过自称唯一的契约。按 F-17 / GUIDELINES §8，不能投有条件通过。在此之前不要把这套用例当作 Phase 1～5 的官方操作基准。

---

## 0. Reviewer 自审

- 不采信申请「100% 对齐」；对声称已落地的 D-9 用路径原文对账。
- 仪器：Draft-07（`jsonschema`）校验 fixture 与从用例围栏抽出的 YAML；Python 按字节值 `0x09/0x0b/0x0c/0x0d` 扫 `docs/usercases/*.md`；`diff` 比较 `docs/schemas` 与 `src/macao/schemas`；`PYTHONPATH=src python3 -m unittest discover tests`；`python3 -m compileall -q src tests`。
- 申请写 `2c40cd5`，工作区 HEAD 为 `caf3473`。本报告以 HEAD 为准（否则无法审到申请文件与 UC-6 信封修复），并登记 SHA 漂移为 P2。
- CODE 实现（加权引擎、E5a 守卫、override 命令）仍为各分册「待实现」项，**NOT_APPLICABLE**（本轮目标为 L1，不要求 L2）。
- 未把 STATUS 对 `2c40cd5` 的自述当作本轮证据。

强制自检：

| # | 项 | 本轮 |
|---|---|---|
| 1 | 字段名 vs 读取路径 | PRD §2.5 / Layer 1c 读 `.macao/.dispositions/r{rnd}/…`；UC-6 / README / 申请 D-9 写 `.macao/executor.disposition.yml`。UC-6 信封字段与 Schema 同构（`executor` 对象 / `disposition_status` / `dispositions[]`） |
| 2 | 「已完成 / 100%」是否有证据 | 申请 §4 四条机验 **VERIFIED**；申请标题「100% 机器语义级对齐」**CONTRADICTED**（见 P1-1～P1-3） |
| 3 | 确定性用语 | 各 UC 状态多为「设计稿（待实现）」✓；申请「100%」未标注目标 |
| 4 | YAML/JSON 可解析且过 Schema | UC-6 示例 **PASS**；UC-3 示例 **FAIL**（缺 `evidence_commit`）；UC-1-gemini 示例 **FAIL**（`consensus_strategy` / 无 `consensus_rule`） |
| 5 | P1 均附路径 | 是 |

---

## 一、申请 §4 机验（独立复跑）

| 声明 | 本机 | 判定 |
|---|---|---|
| 13 份 `docs/usercases/*.md` 控制字符 0 | 13/13 计数为 0 | **VERIFIED** |
| valid fixture 8/8 | 8/8 PASS | **VERIFIED** |
| invalid 全部拦截 | 6/6 REJECTED | **VERIFIED** |
| `docs/schemas` vs `src/macao/schemas` 0 diff | 8 份 SAME | **VERIFIED** |
| 86/86 PASS；compileall 0 | Ran 86，OK，30.2s；compile rc=0 | **VERIFIED** |
| `docs/usecases` → `usercases` 软链接 | `docs/usecases -> usercases` | **VERIFIED** |

附加探针（申请未列，本轮为核验上轮闭环与本轮示例）：

| 探针 | 结果 |
|---|---|
| `macao_config.consensus_rule = "2/3_majority"` | **REJECT**（枚举仅 `weighted_2/3_v1`）——上轮 grok P1-1 **闭环** |
| UC-6 抽出 YAML vs `review_disposition.schema.json` | **PASS**——上轮 grok P1-2 示例层 **闭环** |
| UC-6 基底 + `EXEMPTED_BY_ADMIN` 且无 `override_id` | **REJECT**（契约守卫有效） |
| UC-3 抽出 YAML vs `dev_manifest.schema.json` | **FAIL**：`full_document.evidence_commit` 为 required |
| UC-1-gemini 抽出 YAML vs `macao_config.schema.json` | **FAIL**：`policy.consensus_rule` 为 required；示例写的是 `consensus_strategy: "majority"` |

---

## 二、上轮 grok（`2da1bc2`）阻断在本对象上的状态

| 上轮项 | 本轮判定 | 证据 |
|---|---|---|
| **P1-1** `macao_config` 仍接受 `2/3_majority` | **VERIFIED 闭环**（HEAD） | `docs/schemas/macao_config.schema.json:66` 枚举 `["weighted_2/3_v1"]`；探针 REJECT 旧值。闭环提交是 `caf3473`，不在申请所写的 `2c40cd5` |
| **P1-2** UC-6 示例 `executor_id` 无法过 Schema | **VERIFIED 闭环**（示例层） | UC-6 L31–34 为 `executor: { id, role, cli }`；抽出 YAML **PASS**。A2 写者含混 **未闭**，并入本轮 P1-2 |
| **P1-3** E7 `APPROVED` 有 issue 时 FINAL 写者不能唯一推出 | **未闭环** | 见本轮 P1-2。UC-6 补了 `EXEMPTED_BY_ADMIN ⟹ override_id` 规则句，但 A2 仍写「管理员将 issue 标记为 `EXEMPTED_BY_ADMIN`……放行至 `MERGING`」 |

---

## 三、D-1～D-9 落地对照（独立，不采信申请 §3 表）

| 裁定 | 判定 | 摘要 |
|---|---|---|
| **D-1** 机器决策与人工接管物理分离 | **主体 VERIFIED** | UC-5 §2.c/d、UC-7 边界声明：DEADLOCK 即时落盘，E7 只写 `admin_override.json` |
| **D-2** 独立 Admin Override | **主体 VERIFIED** | UC-7 §2.d 字段清单含 `override_id` / `choice` / `exempt_issue_ids`；Schema 五值 `choice`（含 `EXTEND`）与 UC-7 命令行一致。申请 §3 写「4 大闭合选项」与正文 **不一致**（P2-2） |
| **D-3** 独立 Review Disposition | **PARTIALLY_VERIFIED** | UC-6 信封与 PRD §2.5 / Schema 字段同构；三态、精确覆盖、`FINAL` 禁 `NEEDS_ADMIN` 均有文字。**路径未收敛**（P1-1） |
| **D-4** `decision` 三态 | **VERIFIED** | UC-5 决策表仅 `APPROVED` / `REWORK_REQUIRED` / `DEADLOCK`；无机器 `RETRY_REVIEW`/`CANCELLED` |
| **D-5** 纯整数五重门禁 | **主体 VERIFIED** | UC-5 §2.b 五条与 PRD §2.3 同构；UC-9 明确超时票进 `accounted`、不进 $E_N$/$E_W$。UC-1 h0(3) 决策句仍写「赞成加权占比 ≥ 2/3」（P2-5） |
| **D-6** FSM 三投影 / E3 全席位 accounted | **主体 VERIFIED** | UC-4 §2.g：`reviewers_accounted == reviewers_configured`；UC-6 §2.c 按 `requires_new_checkpoint` 分流 E4/E5a。E7 与 Layer 1c 接力 **未唯一**（P1-2） |
| **D-7** 零语义 / AEP/1.1 | **主体 VERIFIED** | UC-2/UC-4 禁止编排器自拟正文、Type C 零 base64、ping 极短。用例正文几乎不出现 `evidence_commit`（仅 UC-6 示例有）；16 KiB 只在 README 共享表出现，未进入信封 Schema（沿用上轮 P2，本轮不升 P1） |
| **D-8** Checkpoint 拓扑单调前进 | **VERIFIED** | UC-3 P2/E2：必须为上轮 `checkpoint_ref` 子孙且未被消费；UC-8 P2 硬绑定合并对象 |
| **D-9** 产物命名与单写者全库一致 | **CONTRADICTED** | 见 P1-1。写者表（README）方向正确；**路径字面量未全库一致** |

---

## 四、GUIDELINES §6 反例库（用例能否唯一推出）

| 场景 | 能否从用例唯一推出 | 落点 |
|---|---|---|
| 2-reviewer 全部弃权 | **能** | UC-9 §2.d 全体弃权 → $E_N=0$ → DEADLOCK；UC-5 A2 |
| 2-reviewer 1 超时 + 1 批准 | **能** | UC-9：超时进 `accounted` 不进 $E_N$；$E_N=1 < \lceil 4/3 \rceil=2$ → DEADLOCK |
| 2-reviewer 1:1 僵局 | **能** | UC-5 决策表「其余一切」→ DEADLOCK + 即时落盘 |
| 3-reviewer 1:1:1 | **能** | 同上 |
| Reviewer 崩溃后重复提交 | **能** | UC-4 E5 / f4 去重幂等 |
| 同 `reviewer_id` 两份同轮票 | **能** | UC-4 A5 |
| `.dev.yml` 缺字段但 `signal=EXPLICIT` | **能（拒收）** | UC-3 d1/E4 Schema fail-closed；但**正例本身过不了 Schema**（P1-3） |
| 第二轮 `.review.yml` 是否覆盖第一轮全文 | **能** | UC-4 A1：去重取最新票，旧全文保留在 `docs/reviews/` |
| 人工接管超时后默认动作 | **能** | UC-7 §2.f：保持 HOLD，不静默继续 |
| Git 冲突 / checkpoint 漂移 | **能** | UC-8 关卡 2 / E4b / E2 |
| `review_context` 载体 vs 工作流 | **能（方向）** | UC-4 §2.b：worktree 内 `git diff`，严禁 base64。无完整 Type C JSON 示例（P2） |
| 遗漏 issue 的 disposition / `FINAL`+`NEEDS_ADMIN` / 非法 `choice` | **文字能** | UC-6 E1 与规则句；UC-7 E2。**E7 豁免后谁写 FINAL 不能唯一推出**（P1-2） |

主路径反例库 11/11 中，10 项可唯一推出；「豁免放行」不是 §6 原表项，但是申请 §5 点名的 fail-closed 项，**不能**唯一推出。

---

## 五、已对齐 / 已确认项

1. F-20 已写明 D-1/D-2 落实；`vote_result` 与 disposition 写者边界在 PRODUCT-FACTS、UC-5、UC-6 边界声明同向。
2. UC-4 收敛条件已改为全席位 `accounted == configured`，不再用 `minimum_quorum` 提前返回。
3. UC-5 决策三值、DEADLOCK 即时落盘、A3 不再写 `resolution: human_override`。
4. UC-9 超时 ABSTAIN 计入 `accounted`、排除于 $E_N$/$E_W$；迟到票在 `vote_result` 落盘后 `LATE_REVIEW_ISOLATED`。
5. UC-7 验收与 v2.3.1 相反：DEADLOCK 期间文件已存在，裁定不改哈希。
6. UC-8 五关卡与「评审对象 = 合并对象」与 PRD §14.5 同向。
7. UC-10 doctor 只读、不自动转移状态。
8. 软链接 `docs/usecases` → `usercases` 存在。
9. 上轮配置枚举与 UC-6 `executor` 对象在 HEAD 上已修好。

---

## 六、P1：进入实施基线前应修正

### P1-1　处置产物路径未收敛（申请 D-9「全库一致」不成立）

申请 §3 D-9 与 README 共享产物表写活动路径为 **`.macao/executor.disposition.yml`**。权威 PRD 与同一用例集的另一分册写的是另一条路径。

**证据**：

| 来源 | 路径 |
|---|---|
| 申请 D-9、D-3；`docs/usercases/README.md:97`；UC-6 L24 | `.macao/executor.disposition.yml` |
| PRD §2.5 L638；Layer 1c L780；`docs/schemas/README.md:10`；FAQ 产物表；**UC-1 h0(2) L112** | `.macao/.dispositions/r<round>/executor.disposition.yml` |

UC-1 是申请列明的 D-3 落地位置之一，与 UC-6 对同一文件给出两个绝对路径。Layer 1c 伪代码只 load 带 round 的目录。按 README 实现的执行者把文件写在 `.macao/` 根下，按 PRD 实现的编排器永远读不到 FINAL，E4/E5a 不会发生。

**影响**：GUIDELINES §5「产物路径」属审计相关结构性变更；两个按「已对齐用例」编码的系统不能互换产物。

**验收**：全库（PRD §2.5、Layer 1c、FAQ、Schema README、UC-1 h0(2)、UC-6、用例 README、申请 D-9）收敛为**同一条**活动路径 + **同一条**归档路径；用一条 Draft-07 + 路径断言的单测锁死。推荐与权威 PRD 一致：活动文件 `.macao/.dispositions/r<round>/executor.disposition.yml`，归档 `.macao/archive/<ref>/r<round>/`。

### P1-2　E7 `APPROVED` 有 issue 时，FINAL / `EXEMPTED_BY_ADMIN` 写者仍不能唯一推出（上轮 grok P1-3 未闭）

申请 §5 要求核验单写者垄断「严禁任何二次回写或状态伪造」。本轮把契约守卫写进了 UC-6 规则句，但**主备选流仍互相打架**。

**证据**：

1. UC-6 §2.b：执行者是 `executor.disposition.yml` 唯一写者；`EXEMPTED_BY_ADMIN` 必须带 `override_id`。
2. UC-6 A2 L74：「**管理员**通过 `macao override resolve --choice APPROVED --exempt-issue-ids [...]` **将 BLOCKING issue 标记为 `EXEMPTED_BY_ADMIN`**，生成 `override_id` **并放行至 `MERGING`**。」主语是管理员；未出现执行者再交 FINAL。
3. UC-7 §2.c：`APPROVED` → **立即** E4 → `MERGING`，「必须提供 FINAL disposition」——**未写提供者、未写等待点**。
4. UC-1 h2：`CONSENSUS_CHECK`（HOLD: DEADLOCK）时 Executor `role_view = AWAIT_HUMAN`，**不是** `SHOULD_DISPOSE`。override 之后哪一行生效，用例无表。
5. PRD 场景三 6a（权威基准，用例应对齐）：步骤 5 只有 DEADLOCK 的 `vote_result`；6a 写「**存在** FINAL disposition → `MERGING`」。表中没有任何人写出该 FINAL。
6. 提案 §4.2（申请「关联变更提案」）现在是**第三套**：DEADLOCK 覆盖要 **Executor** 写 `EXEMPTED_BY_ADMIN`；处置超时覆盖「**可由管理员一并签署替代 FINAL**」——直接打穿 D-9 执行者垄断。

**推演**（GUIDELINES §6 风格，1:1 僵局 + 管理员批准 + 非空 `issues_index`）：

1. 若无 FINAL：E4 不得进 `MERGING`（PRD §3.3 E4）；UC-6 A2 / UC-7 c 却写成已进。
2. 若管理员或编排器代写 disposition：破 D-9 / §16.1。
3. 若仍要执行者再写 FINAL：应投影 `SHOULD_DISPOSE`，而 DEADLOCK HOLD 行是 `AWAIT_HUMAN`；用例没有「override 之后」的一行。

**验收**：UC-6 A2、UC-7 §2.c、UC-1 h1/h2 写成**同一条边**，例如：E7 `APPROVED` 且仍有未覆盖 issue → 只落盘 `admin_override.json`、解除 DEADLOCK HOLD、投影 `SHOULD_DISPOSE`；Executor 提交含 `EXEMPTED_BY_ADMIN`+`override_id` 的 FINAL 后再 E4；**禁止**无 FINAL 直跳 `MERGING`；**禁止**管理员代写 `executor.disposition.yml`。用「1:1 僵局 + `--choice APPROVED --exempt-issue-ids`」逐步推演只能命中这一行。

### P1-3　待审用例 YAML 示例未全部通过自称唯一的契约（L1 硬条件）

GUIDELINES §2.1 L1：「所有 YAML/JSON 示例是合法可解析格式」；§9 模式 D：声称是 YAML 的代码块字段须与正式 Schema 一致。申请将 13 份用例列为实施基准，并声明与 Draft-07 契约「100% 互锁」。

**证据 A — UC-3（检查点主信封，申请 D-8 落地文件）**

`docs/usercases/UC3-dev-checkpoint.md` L33–48 的 `.dev.yml` 含 `full_document.path` / `sha256`，**没有** `evidence_commit`。`dev_manifest.schema.json` 规定：一旦出现 `full_document`，`required` 为 `path` + `evidence_commit` + `sha256`。本机抽出校验：

```text
FAIL  UC-3 .dev.yml example
      path=['full_document']: 'evidence_commit' is a required property
```

同目录正例 `docs/schemas/fixtures/valid/dev.yml` L10–13 含 `evidence_commit`。实现者按 UC-3 照抄会得到 **Schema 拒收、不触发 E1/E6** 的信封。UC-3 d5 还把 sha256 对账写成 fail-closed，与「正例非法」并列，属于模式 A+D。

**证据 B — UC-1-gemini（申请 §2 第 3 项交付物，与 glm 主稿并列承担 `macao init --agteam`）**

文件仍标 `版本：v1.0 (2026-08-31)`、`macao.yaml` 示例 `version: "2.4"`、`policy.consensus_strategy: "majority"`（L161–164）。抽出校验：

```text
FAIL  UC-1-gemini macao.yaml example
      path=['policy']: 'consensus_rule' is a required property
```

该示例还会让实现者写出已被 HEAD 契约拒绝的旧仲裁字段。步骤 3 仍把 agmsg 历史「文本语义特征」当作角色与进展研判输入，与申请 D-7 / F-12「编排器无模型、不读业务语义」同页冲突。README 虽标注「对照稿」，申请 §1～§2 仍将其计入「全量 13 份」「彻底梳理、更新」，并赋予与 glm 主稿相同的 v2.5 规格声明。

**验收**：

1. UC-3 示例补 `evidence_commit`（及与 fixture/PRD §2.1 同名的 git 字段），抽出 YAML 对 `dev_manifest.schema.json` **PASS**。
2. 要么把 `UC1-init-gemini.md` 从本轮交付物与「13 份对齐」声明中明确降级为「历史对照、不作实施基准」并在文首加 fail-closed 横幅；要么改到与 glm 主稿 / `macao_config.schema.json` 同一套字段（`consensus_rule: weighted_2/3_v1`），抽出 YAML **PASS**。
3. 增加一条「从 `docs/usercases/*.md` 抽出 fenced YAML/JSON 并对对应 Schema 校验」的门禁，避免下一轮再靠人工抽查。

---

## 七、P2 / P3

| ID | 级 | 问题 |
|---|---|---|
| P2-1 | P2 | 申请钉死 `2c40cd5`，`origin/main` 实为 `caf3473`（申请文件 + Schema/UC-6 差量）。上轮 Codex 已要求申请写死短 SHA。 |
| P2-2 | P2 | 申请 D-2 / README UC-7 要点写「4 大选项」；UC-7 命令行、验收与 `admin_override.schema.json` 为 **5** 值（含 `EXTEND`），与 PRD §3.3 E7 一致。漏掉 `EXTEND` 的实现会把合法裁定当非法 `choice` 拒绝。 |
| P2-3 | P2 | UC-1-glm 是拼接稿：L21「主成功场景（细化 a–i）」未完成即在 L61–62 插入另一套 P2/P3 表，L66 再开「## 2. 主成功场景（M1…）」。前置条件表出现两次且编号冲突。 |
| P2-4 | P2 | gitignore 条数：UC-1 f4 写「8 规则」，UC-10 / 申请写「9 规则」；`wizard.py:83-93` 实为 **9** 条。 |
| P2-5 | P2 | UC-1 h0(3) 决策句「赞成加权占比 ≥ 2/3」；UC-5 §2.b 同时保留「赞成加权占比 = Σ/有效权重」。与「严禁浮点」并列，数学上可等价于 $3W_{win}\ge 2E_W$，但会诱使实现走除法。以 UC-5 五条整数门禁为准删掉占比句。 |
| P2-6 | P2 | UC-3 §8 遗留决策③仍问「采纳清单是否独立 `adoption.yml`」；UC-1 §8 遗留⑤已写「已裁定为 `executor.disposition.yml`」。D-3 不得再标未决。 |
| P2-7 | P2 | UC-5 决策表把 `APPROVED` 直接画成 E4/E5a，§2.d 才写 `requires_disposition` 时 HOLD。压缩表会让实现者跳过 Type E 等待。 |
| P2-8 | P2 | AEP 16 KiB / 禁 base64 仍未进入 `aep_envelope.schema.json`（沿用 Design-Sync 轮 P2）；用例侧也没有一份完整 Type C/E JSON 可抽验。 |
| P3-1 | P3 | UC-3 示例 `development.git.source_branch` 与 Schema 属性名 `branch`、fixture `branch` 不一致（额外字段当前能过，因未 `additionalProperties: false`）。 |

---

## 八、建议闭环顺序

1. **P1-1**：路径收敛到 PRD §2.5 那一条；改 UC-6、README、申请 D-9；UC-1 h0(2) 保持与 PRD 同句。
2. **P1-2**：UC-6 A2 删掉「管理员标记并放行 MERGING」；UC-7 `APPROVED` 行改为「override 落盘 → `SHOULD_DISPOSE` → Executor FINAL → E4」；禁止管理员代写 disposition。提案超时「替代 FINAL」一并删掉或改成与 D-9 相容的唯一边。
3. **P1-3**：修 UC-3 示例；处理 gemini 对照稿（降级或改到 v2.5 契约）；把「抽出围栏 YAML 校验」做成可复现脚本。
4. P2-1～P2-4 可同一差量：申请 SHA 钉死 HEAD、选项写成五值、UC-1 去拼接、gitignore 统一 9。
5. 更新 `STATUS.md` 登记本报告；不要把 86/86 或「fixture 8/8」写成用例对齐的充分条件。

闭合后可再评 **L1 / PG-0**。现行代码轨仍按既有 L3/PG-2 行为，在用例边写死之前不要按 UC-6 A2 实现 `override.py` 直跳 `MERGING`。

**不建议**：以申请 §3 对照表代替路径/写者对账；不建议在 gemini 对照稿仍含 `consensus_strategy: majority` 时声称 13 份全部 v2.5。

---

## 九、机器票与 issue 索引

| issue_id | severity | disposition_class | 摘要 |
|---|---|---|---|
| `grok/P1-1` | major | `BLOCKING` | 处置活动路径双真源：`.macao/executor.disposition.yml` vs `.macao/.dispositions/r<round>/…`（D-9 / UC-1 vs UC-6） |
| `grok/P1-2` | major | `BLOCKING` | E7 `APPROVED` 有 issue 时 FINAL/`EXEMPTED_BY_ADMIN` 写者与 UC-6 A2 / UC-7 c / `role_view` 不能唯一推出（上轮 P1-3 未闭） |
| `grok/P1-3` | major | `BLOCKING` | UC-3 `.dev.yml` 示例缺 `evidence_commit` 无法过 Schema；UC-1-gemini 示例仍为 v2.4 `consensus_strategy: majority` |

`vote`: `NO_APPROVE`
