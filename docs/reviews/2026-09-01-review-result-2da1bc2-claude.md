# MACAO PRD v2.5 全文档体系定级复核（第三轮）评审结论

- **评审日期**：2026-09-01
- **评审人**：`claude`
- **评审对象**：[`docs/reviews/2026-09-01-review-request-PRD-v2.5-Design-Sync.md`](2026-09-01-review-request-PRD-v2.5-Design-Sync.md)（本轮再次重写，新增 §4 闭环表与 §5 自动化验证）
- **对应 commit**：`2da1bc2`（`docs: close Claude and Codex review findings on 2766c69, harden schemas and fixtures`），工作区 clean
- **前两轮**：`0bc6247`（本人 `NO_APPROVE`，P0×2 + P1×8）→ `2766c69`（本人 `NO_APPROVE`，P1×2 + P2×8 + P3×4）
- **评审基准**：`docs/MACAO_REVIEW_GUIDELINES.md` v1.0 §1–§6、§9、§11
- **事实锚点**：`docs/usercases/PRODUCT-FACTS.md` F-1～F-22
- **申请定级**：L1 DOC-ALIGNED / PG-0
- **机器票**：`NO_APPROVE`
- **结构化 issue**：`BLOCKING` × 3（P1），`ADVISORY` × 5（P2 × 4 / P3 × 1）

---

## 结论

**我上轮的 2 项阻断（N-1、N-2）已彻底闭环，另 7 项 P2/P3 一并关闭；Codex 的 P1-4 / P1-6 / P1-7 亦经我独立机验闭环。** 本轮 Schema 硬化是实打实的：fixtures 正例 8/8 通过、反例 6/6 全部按预期拦截、两份 Schema 镜像逐字节一致、86/86 测试通过、全 `docs/` 树控制字符归零、悬空引用归零。

**但仍不能授予 L1 DOC-ALIGNED / PG-0**，存在 3 项 P1，其中 2 项是**本轮修复动作自身引入或未兑现的**：

1. **M-1（回归）**：为闭环 Codex P1-3 而给 `review_context.schema.json` 加上 `additionalProperties: false`，但没有把 PRD §5.2 自己声明的 `required_blocks` 块加进 `properties`——于是**§5.2 这份「唯一权威完整模型」现在无法通过它自己指定的机器契约**。该实例在上一轮 `2766c69` 是 PASS，本轮变为 FAIL。这与申请 §3 「`review_context` … Draft-07 Schema 校验测试 100% PASS」直接矛盾。
2. **M-2（闭环声明不实）**：申请 §4 称 `macao_config.schema.json` 已「严格收敛 `policy.consensus_rule` 枚举为 `["weighted_2/3_v1"]`」。实测枚举为 **`["weighted_2/3_v1", "2/3_majority"]`**，旧规则仍被接受，且 `2/3_majority` 在 PRD、README、清单中**没有任何迁移或兼容说明**。Codex P1-5 的要求是「保留则须定义明确的版本迁移/兼容模式，否则从 v2.5 Schema 移除」——两条路都没走。
3. **M-3（新的文档—契约倒置）**：本轮为闭环 Codex P1-4 给 `review_disposition.schema.json` 加了条件约束，`EXEMPTED_BY_ADMIN` 现**强制要求非空 `override_id` 且 `requires_new_checkpoint == false``。但权威基准 PRD **§2.5 全节没有出现过 `override_id`**，三条「处置规则与守卫」也未提及该约束；正例 fixture 同样未覆盖该路径。按 §2.5 编码的实现产出的豁免处置会被契约拒收。

三项合计约 15 行改动，仍无设计风险。按 **F-17**，需要修复后才能作为基线的「有条件通过」在机器语义上属阻断性不通过，故机器票为 `NO_APPROVE`。**这是连续第三轮：每轮都真实闭环了上一轮的全部阻断，又在修复动作里带出新的同类缺陷。** 建议在第 4 轮把「回归检查」本身固化为交付前的自动化门禁（见 §六）。

---

## 0. Reviewer 自审记录（GUIDELINES §9）

### 0.1 本轮我自己的两次测量错误（均在下结论前自查出并纠正）

- **假阴性，差点误判为「已闭环」**：我构造 AEP 反例「`AEP/1.0` 信封 + `DISPOSITION_REQUIRED` + 60 KB payload」，validator 报错，脚本打印「拒绝 OK」。**但拒因不是我要测的任何一项**——是我随手写的 `message_id: "m1"` 不匹配 `^msg-[0-9]{8}-[0-9A-Za-z_-]+$`。若就此收笔，会把一项未闭环项误记为闭环。改为**逐维度隔离**（以合法 fixture 为基底，一次只改一个字段）后，真实结论是三项均**被接受**（见 M-4）。教训登记：反例测试必须打印拒因并确认拒因就是被测约束，否则「拒绝」不构成证据。
- **映射器缺陷，未当成被审对象的问题**：我回放 `fixtures/` 时用文件名前缀推断对应 Schema，`context_missing_refs.json` 未能映射（前缀是 `context` 而非 `review_context`），脚本打印「无法映射」。这是**我的映射器不完备**，不是 fixture 缺陷。已单独对该文件跑 `review_context.schema.json`，结果为 REJECT(18)，符合反例预期。

### 0.2 强制自检 5 项

| # | 检查项 | 本轮结果 |
|---|---|---|
| 1 | 字段名 vs 实际读取路径 | **部分 CONTRADICTED**：§5.2 ↔ §5.3 ↔ Schema 在 `code_changes.refs.*` 上三者同构 ✓；但 §5.2 整体已无法通过自身契约（M-1），且 §2.5 缺 `override_id`（M-3） |
| 2 | 每处「已完成」是否有证据 | 申请 §5 三组自动化结论我逐条重跑，**全部属实**（控制字符 0、fixtures 8/8 + 反例全拦截、86/86、镜像 0 diff）；申请 §4 有 2 处不实（M-2、M-4） |
| 3 | 确定性用语是否标注 | PRD 21 个复选框仍全为 `[ ]` ✓；申请标题「100% 物理闭环」被 M-2 / M-4 证伪 |
| 4 | 代码块是否真能解析 | **全部 PASS**：§2.1 / §2.2 / §2.3 / §2.5 / §13 五份示例对各自 Schema 通过；**唯 §5.2 FAIL**（M-1）；LaTeX 公式已恢复（N-1 闭环） |
| 5 | 每个 P1 是否给出可复现证据 | 是；三项均附可直接重跑的脚本（§五） |

### 0.3 连续漏审模式登记

上轮我登记的是「跨轮复用的验证脚本必须按语义锚点定位，禁止硬编码行偏移」。本轮该纪律**生效**：我上轮报告内嵌的脚本在 PRD 再改 27 行后仍能正确定位并直接跑出 N-1/N-2 的闭环结论。本轮新增登记：**反例测试必须校验拒因**（见 §0.1 第一条），已写入 §五脚本 B 的实现方式（逐维度隔离 + 打印拒因）。

### 0.4 证据类型适用性

DOC / SPEC 为主；对 `docs/schemas/` 的 7 份契约与 14 份 fixture 做了 Draft-07 实测（**TEST**）；状态机场景手工重放（**SIM**）。本轮 commit 同时改动了 `consensus/vote.py`、`workflow/orchestrator.py`、`utils/context_builder.py`、`adapter/mock.py`、`core/schema.py` 等实现文件，但申请目标为 L1 / PG-0，按 GUIDELINES §1.2 与申请自身的证据边界，**CODE / OPS 判为 NOT_APPLICABLE**；仅记录回归结果：86/86 PASS、`compileall` rc=0。

---

## 一、上轮阻断与登记项的闭环核验（逐项独立机验）

### 1.1 我上轮的 2 项 P1 —— 全部闭环

| 上轮 issue | 判定 | 决定性证据 |
|---|---|---|
| **N-1** §2.3 五重门禁公式被控制字符损坏 | **VERIFIED** | 按字节扫描 `docs/**/*.md` 全树（`0x09`/`0x0b`/`0x0c`/`0x0d`）：**总计 0**（上轮 9，全部集中于 PRD L332–335）。公式已还原为 `$\forall i, 3 \times w_i < 2 \times W$` 与 `\lceil 2N/3 \rceil`，与 FAQ L306–309、UC-5、清单三处完好复述一致 |
| **N-2** `vote_result` decision 枚举放行 `RETRY_REVIEW`/`CANCELLED` | **VERIFIED（超出要求）** | 逐值 falsify：`APPROVED`/`REWORK_REQUIRED`/`DEADLOCK` 接受、`RETRY_REVIEW`/`CANCELLED` **拒绝**；另（我未要求而申请自行加固）`resolution` 移除 `human_override`，`required` 由 7 项扩至 **15 项**，含 `policy_snapshot`/`issues_index`/`issues_index_sha256`/`requires_disposition`/`reviewers_accounted`；旧正例 `vote_result_human_override.json` 已移出并新增反例 `vote_result_cancelled_decision.json` |

### 1.2 我上轮的 P2 / P3 —— 7 项闭环，4 项存续

| 上轮 issue | 判定 | 证据 |
|---|---|---|
| **N-4** §16.1 垄断权表无 `admin_override.json` / 无管理员角色 | **VERIFIED** | §16.1 首行改为「**编排者/管理员** \| 用户 (Admin) + MACAO Orchestrator」，职责含「人工接管处理与豁免裁决」，垄断权列含 `admin_override.json` |
| **N-6** §5.2「9 大必需块」vs 实列 10；Schema 仅 required 5 | **VERIFIED** | L948 / L950 / L952 三处统一改为「**10 大必需块**」「两个传输定位块 + 八个语义块」；Schema `required` 由 5 项扩至 **10 项**，缺 `evidence`/`review_guidelines` 的反例现被拒绝 |
| **N-7** `dev_manifest.signal` 的 `const` 使 UC-3 d2 / A1 不可达 | **VERIFIED** | `signal` 由 `{"const":"EXPLICIT"}` 改为 `{"enum":["EXPLICIT","IMPLICIT"]}`，UC-3 A1 的 `signal: IMPLICIT` 现为合法产物且不触发转移，d1 / d2 两道门禁独立可达 |
| **N-8** §17.1 worktree 路径层级与实现相反 | **VERIFIED** | §17.1 改为 `.macao/worktrees/<reviewer_id>/<task_id>/r<round>`，与 §5.2、FAQ、UC-4 及 `src/macao/utils/git_utils.py:104` 一致；PRD 内 worktree 写法收敛为单一方案 |
| **N-9** STATUS 未随轮更新、缺登记 | **VERIFIED（本轮已提交）** | 我上一轮所做的 STATUS 全量对账与双轨改写已随 `2da1bc2` 提交入库（123 行）。**但本轮再度滞后** → 降级登记为 M-8 |
| **N-11** §4.1 标题工期与 §4.2 冲突 | **VERIFIED** | 标题改为「严格的 MVP 范围（第一期）」，「6-8 周」已删除，与 §4.2 Phase 1–5 / Day 1–7 不再冲突 |
| **N-12** §19 声明的 `model:` 未进 §13 | **VERIFIED** | §13 executor 与 3 个 reviewer 条目均补 `model` 字段（L1355、L1357–1359） |
| **N-3** `resolution` 同义值 + UC-5 A3 行标 | **部分闭环** | `human_override` 已移除 ✓；但同义对 `automatic` / `AUTO_WEIGHTED_CONSENSUS` 仍并存，且 UC-5 L66 的 A3 行标仍写 `resolution: human_override`——现已是**契约拒绝的取值** → M-6 |
| **N-5** `dictator_cap_enabled` 开关 vs §2.3 无条件 / F-22 | **未闭环** | 仍为 `{"type":"boolean"}`，§2.3 门禁 1 仍是无条件表述，校验落点仍未在文档中指明 → M-7 |
| **N-10** AEP `type` 未绑定 `protocol` 版本、字节预算无契约表达 | **未闭环** | 见 M-4（且本轮闭环表未列该项） |
| **N-13 / N-14** PRD 未指向 UC-4 去重、`signal` 语义未在 PRD 正文定义 | **未闭环（P3，本轮不再单列）** | 维持登记，不影响定级 |

### 1.3 Codex 上轮 7 项 P1 —— 我独立复核的结论

| Codex issue | 我的判定 | 证据 |
|---|---|---|
| **P1-1** 公式控制字符 | **VERIFIED** | 同 N-1 |
| **P1-2** `vote_result` 契约仍允许人工终局 | **VERIFIED** | 同 N-2；另 Codex 要求的 `policy_snapshot`/`issues_index_sha256`/`requires_disposition` 设为 required **已落实**；旧 fixture 已移出正例集 |
| **P1-3** `review_context` 与 AEP 三项 fail-open | **PARTIALLY_VERIFIED** | `review_context` 半边**已闭环且超出要求**（10 项 required、`content_base64` 属性彻底移除、`additionalProperties: false`）——但正是这次加固引入 M-1；**AEP 半边完全未动**，且闭环表未提及 → M-4 |
| **P1-4** disposition 三套契约、非法 FINAL 被接受 | **VERIFIED** | 5 组 falsify 全部正确拒绝：`FINAL + NEEDS_ADMIN`、`EXEMPTED_BY_ADMIN` 缺 `override_id`、`EXEMPTED_BY_ADMIN + requires_new_checkpoint=true`、缺 `requires_new_checkpoint`、未知 `disposition_type`；新增反例 fixture `disposition_final_with_needs_admin.yml` 并被正确拦截。**但契约变严后 PRD §2.5 未同步** → M-3 |
| **P1-5** 配置 Schema 未封闭加权策略与独裁帽 | **CONTRADICTED（相对申请声明）** | 枚举实为两值，`2/3_majority` 仍被接受且无迁移说明 → M-2；独裁帽仍为可关开关 → M-7 |
| **P1-6** `schemas/README.md` 与 `dev_manifest` 停留 v2.3 | **PARTIALLY_VERIFIED** | README 已重写为 v2.5、8 份 Schema、8 类 AEP、三值票与互锁 ✓；`dev_manifest.$id` 升至 v2.5 ✓；但 Codex 点名的 `task_id`/`checkpoint_ref`/`full_document` **只进了 `properties`，未进 `required`** → M-5 |
| **P1-7** UC-9 超时 ABSTAIN 口径自相矛盾 | **VERIFIED** | UC-9 现明确「超时弃权票计入 `accounted` 以满足 E3 门禁，但**绝不计入非弃权有效席位 $E_N$ 与有效权重 $E_W$**」；迟到票改记 `LATE_REVIEW_ISOLATED` 审计、严禁修改不可变 `vote_result.json`；全体弃权 $\implies E_N=0 \implies$ 必然 DEADLOCK。三个集合的定义已唯一 |

### 1.4 申请 §5「自动化验证结果」独立重跑 —— 全部属实

| 申请声明 | 我的实测 |
|---|---|
| 全文档集控制字符 0 | **0**（`docs/**/*.md` 按字节扫 `0x09/0x0b/0x0c/0x0d`） ✓ |
| `fixtures/valid/` 8/8 PASS | **8/8 PASS** ✓ |
| `fixtures/invalid/` 100% FAIL-CLOSED | **6/6 全部按预期拒绝** ✓（含我单独补测的 `context_missing_refs.json` → REJECT(18)） |
| `docs/schemas/` ↔ `src/macao/schemas/` 0 diff | **8 份逐字节一致** ✓ |
| 86/86 PASS、compileall 0 Errors | **Ran 86 tests, OK（34.1s）**；rc=0 ✓ |

另我自行加测：PRD `§x.y` 与「第 X 部分」交叉引用**悬空计数均为 0**；`review_manifest` 五重互锁 falsify **5/5 全部正确拒绝**。

---

## 二、P1：必须先解决（3 项）

### M-1　§5.2「唯一权威完整模型」无法通过它自己指定的机器契约（本轮引入的回归）

**实测**（§五脚本 C）：

```
§5.2 context   vs review_context.schema.json  -> FAIL(1)
     - (root) Additional properties are not allowed ('required_blocks' was unexpected)
```

**成因**：本轮为闭环 Codex P1-3，给 `review_context.schema.json` 加了 `"additionalProperties": false`，`properties` 列 10 个块、`required` 列同样 10 个块——这部分是对的，也确实把「5 块 + base64」的 fail-open 关掉了。但 PRD §5.2 的 YAML 首块是：

```yaml
review_context:
  # 0. 必需块声明
  required_blocks:
    - repository
    - dev_checkpoint
    ...（共 10 项）
```

`required_blocks` 是 §5.2 自己定义的「# 0. 必需块声明」，却不在 Schema 的 `properties` 里，于是被 `additionalProperties: false` 判为非法。

**为什么判 P1**：
1. 这是我最初 P0-2 的**同类复发**——权威模型与其自称的机器契约互斥。上一轮 `2766c69` 该实例是 **PASS**，本轮变 **FAIL**，属回归；
2. 直接证伪申请 §3「`review_context` … Draft-07 Schema 校验测试 100% PASS」；
3. 落在 GUIDELINES §9 模式 A：实现者照 §5.2 生成 context → 被契约拒收。

**减轻情节**：`fixtures/valid/review_context_{full,minimal}.json` 两份正例均不含 `required_blocks`，因此**通过**——申请 §5 的「8/8 PASS」本身没有说谎，缺口只在 PRD 正文示例与 fixture 之间。这也说明 fixture 集尚未覆盖「权威文档正文示例」这一来源。

**验收标准**：二选一——(a) 把 `required_blocks` 加入 Schema `properties`（建议同时约束为与 `required` 同集合的字符串数组）；或 (b) 从 §5.2 删除 `required_blocks` 块（该信息现已由 Schema `required` 承载，属冗余）。改完后 §五脚本 C 的 `§5.2 context` 行须为 PASS。**并把 PRD 各节示例纳入 fixture 回放范围**，否则同类回归会再次发生。

### M-2　`consensus_rule` 枚举未按声明收敛，`2/3_majority` 仍被接受且无迁移说明

申请 §4 对 Codex P1-5 的闭环描述为：「**严格收敛 `policy.consensus_rule` 枚举为 `["weighted_2/3_v1"]`**（并兼容默认配置推导）」。

**实测**：

```
docs/schemas/macao_config.schema.json → policy.consensus_rule:
  {"enum": ["weighted_2/3_v1", "2/3_majority"]}
```

枚举是**两值**，不是声明的一值。且 `grep -rn '2/3_majority'` 在 `docs/` 全树只有这一处命中——**PRD 正文、`schemas/README.md`、`v2.5_CODE_CHANGE_INVENTORY.md` 均未出现该值**，既没有「legacy / 仅用于读取存量配置」的标注，也没有版本绑定的 `if/then`。

**影响**：一份 `consensus_rule: "2/3_majority"` 的配置在 v2.5 契约下合法，而 PRD §2.3 与 §13 只定义 `weighted_2/3_v1`。这正是 Codex P1-5 陈述的后果——同一份 v2.5 配置可能在不同实现中按等权旧算法运行。按 GUIDELINES §8，投票规则属「审计相关的结构性变更」，不可含糊。

**验收标准**：或从枚举移除 `2/3_majority`；或保留并在 §13 与 `schemas/README.md` 显式标注为「仅用于读取 v2.3.1 存量配置，v2.5 新配置禁止使用」，并用 `if/then` 绑定 `version` 字段。同时修正申请 §4 的表述。

### M-3　`review_disposition` 契约新增的必填约束未进入权威基准 §2.5

本轮为闭环 Codex P1-4，`review_disposition.schema.json` 新增条件约束。我逐条 falsify 确认其**生效且正确**：

| 反例 | 结果 |
|---|---|
| `FINAL` + 任一 `disposition_type: NEEDS_ADMIN` | 拒绝 ✓ |
| `EXEMPTED_BY_ADMIN` 缺 `override_id` | **拒绝** ✓ |
| `EXEMPTED_BY_ADMIN` + `requires_new_checkpoint: true` | **拒绝** ✓ |
| 缺 `requires_new_checkpoint` | 拒绝 ✓ |
| 未知 `disposition_type` | 拒绝 ✓ |

**问题**：后两条新语义在权威基准里**不存在**。PRD §2.5 全节（格式块 + 三条「处置规则与守卫」）**从未出现 `override_id`**，也未说明 `EXEMPTED_BY_ADMIN` 必须 `requires_new_checkpoint == false`；`EXEMPTED_BY_ADMIN` 仅作为格式块里一行注释的枚举值出现。正例 fixture `docs/schemas/fixtures/valid/disposition.yml` 同样**不含 `override_id`**，即该路径无任何正例覆盖。

**影响**：这是「契约比权威规范更严」的倒置。实现者按 §2.5 写出的管理员豁免处置（`disposition_type: EXEMPTED_BY_ADMIN`）会被 Schema 拒收，且看不出原因；同时 §2.5 的守卫规则 2（「全部 `requires_new_checkpoint == false` ⟹ E4」）与新约束的关系也未说明。属 GUIDELINES §9 模式 A。

**验收标准**：§2.5 格式块补 `override_id` 字段（并说明其与 `admin_override.json` 的 `override_id` 的引用关系），「处置规则与守卫」增加第 4 条写明 `EXEMPTED_BY_ADMIN` 的两项强制约束；新增覆盖 `EXEMPTED_BY_ADMIN` 的正例 fixture。

---

## 三、P2：登记，Phase 1 前处理（4 项）

| ID | 问题 | 证据 |
|---|---|---|
| **M-4** | **Codex P1-3 的 AEP 半边未闭环，且未出现在申请 §4 闭环表中**。逐维度隔离实测（以合法 fixture 为基底，一次只改一个字段）：①`protocol` 降为 `AEP/1.0` → **接受**；②`AEP/1.0` + `type: DISPOSITION_REQUIRED`（AEP/1.1 才引入的第 8 类）→ **接受**；③payload 置 60 KB（超 16 KiB 预算）→ **接受**。`aep_envelope.schema.json` 的 `payload` 仍只约束为 `{"type":"object"}`，无按 `type` 的条件 Schema、无 `allOf`。Codex 原文要求「为 8 类 AEP 建立按 `type` 选择的 payload 条件 Schema；明确字节预算属于 envelope Schema 之外的序列化后 validator，并在清单中给出其唯一实现位置和边界负例」——三项均未做。申请 §1 却称「对全部 9 项阻断完成 100% 物理闭环」 | `aep_envelope.schema.json`；PRD L360 |
| **M-5** | `dev_manifest` 的 `task_id` / `checkpoint_ref` / `full_document` **只加入 `properties`，未加入 `required`**（`required` 仍为 `version`/`executor`/`development`/`status`/`signal`/`review_round`）。而 PRD §1.2 的 DEVELOPMENT 离开条件是「当前轮 `.dev.yml` **与评审申请全文**通过最小有效性校验」，F-15 亦要求信封承载全文引用——`full_document` 可缺省意味着一份不指向任何评审申请全文的 `.dev.yml` 仍是合法产物。申请 §4 称已「统一 `task_id`、`checkpoint_ref`、`full_document`、`signal` 等字段」，就 `signal` 而言属实，就前三项而言只做了一半 | `dev_manifest.schema.json`；PRD §1.2 |
| **M-6** | `vote_result.resolution` 枚举为 `["automatic","AUTO_WEIGHTED_CONSENSUS"]`——`human_override` 已正确移除，但**同义对仍并存**且无使用规则（GUIDELINES §5 禁止同一决策结果多名）。更硬的一点：`UC5-consensus-tally.md:66` 的 A3 行标仍写 `resolution: human_override`，该取值**现已被契约拒绝**，即用例引用了一个不可能合法的值（上轮此项为「指向永远写不出的取值」，本轮升级为「指向枚举外的值」） | `vote_result.schema.json`；UC-5 L66 |
| **M-7** | `dictator_cap_enabled` 仍是 `{"type":"boolean"}` 开关，而 §2.3 门禁 1 为无条件表述（「单席位权重达 2/3 **拒绝启动系统**」）、F-22 为强制事实。一个可置 `false` 的开关等于给事实源规定为强制的门禁留了合法关闭路径。另：Draft-07 无法表达 $\forall i, 3w_i < 2W$ 这类跨条目求和约束，这本身合理，但 PRD / README / 清单仍未区分「结构 Schema 负责什么」与「运行期 validator 负责什么」（Codex 同轮建议 2 亦未落实） | `macao_config.schema.json`；PRD L332 / L1361 |

---

## 四、P3：可延期（1 项）

| ID | 问题 | 证据 |
|---|---|---|
| **M-8** | 交付物 #13 称 STATUS.md「完整如实记录」。上一轮的全量对账与双轨改写已随本 commit 提交入库 ✓，但 STATUS 文首仍停在 `2766c69` 轮（「当前定级状态：票型 2 授予 + 2 拒绝」），登记表也无 `2766c69 .. 2da1bc2` 行。此为每轮固有的滞后，按其自身治理规则应在**下一轮申请复审前**补齐 | `docs/reviews/STATUS.md` L6–L13、L101 |

上轮登记的 N-13（PRD 未指向 UC-4 的产物层去重规则）与 N-14（`signal` 语义仅定义于 UC-3，PRD 正文无条文）本轮未处理，维持 P3 登记，不影响定级。

---

## 五、反例与边界场景推演（GUIDELINES §6 全量重放）

| # | 场景 | 上轮 | 本轮 | 依据 |
|---|---|---|---|---|
| 1 | 2-reviewer 全部弃权 | 是 | **是** ✓ | UC-9 c3 + §2.3 门禁 6；UC-9 现明确「全体弃权 $\implies E_N=0 \implies$ 必然 DEADLOCK $\implies$ UC-7」 |
| 2 | 1 超时 + 1 批准 | 是 | **是（更强）** ✓ | UC-9 新增「集合定义」：超时弃权计入 `accounted` 触发 E3，但绝不计入 $E_N/E_W$；$E_N=1 < \lceil 4/3 \rceil = 2$ → DEADLOCK。Codex P1-7 指出的双重口径已消除 |
| 3 | 1:1 僵局 | 是 | **是** ✓ | 门禁 4 双向不满足 → DEADLOCK 即时落盘 → HOLD → E7 写独立 `admin_override.json` |
| 4 | 3-reviewer 1:1:1 | 是 | **是** ✓ | §3.4 场景三即以此为例，6a–6e 五选项齐备 |
| 5 | 崩溃重启后重复提交投票 | 是 | **是** ✓ | UC-4 E5 f4 去重幂等；UC-9 f 补「同一席位同轮只记一次 ABSTAIN，重扫描不重复注入」 |
| 6 | 同 reviewer_id 两份同轮票 | 是 | **是** ✓ | UC-4 P4 / A5 |
| 7 | `.dev.yml` 缺字段但 `signal=EXPLICIT` | 是 | **是（机制更正确）** ✓ | `signal` 由 `const` 改 `enum`，`IMPLICIT` 现为合法产物但不触发转移（UC-3 A1），Schema 校验与信号判定成为两道独立可达的门禁 |
| 8 | 第二轮返工覆盖第一轮 | 是 | **是** ✓ | §3.4 生命周期表；场景二 Step 7 |
| 9 | 人工接管超时默认动作 | 是 | **是** ✓ | §6.1 八条触发器 + 总则 HOLD |
| 10 | Git 冲突致 checkpoint 不一致 | 是 | **是** ✓ | E4a `ff_only` / `no_ff` 双模 OID 硬校验 |
| 11 | `review_context` 载体不一致 | 是 | **是（但见 M-1）** ⚠ | §5.2 ↔ §5.3 ↔ Schema 在 `code_changes.refs.*` 上仍三者同构，diff 载体本身无歧义；**但 §5.2 整份实例已无法通过契约**（M-1），故该节作为「唯一权威完整模型」不再可直接引用 |

**11 / 11 仍可唯一推出**，其中场景 2、5、7 因本轮修改而**判据更强**。

### 复现脚本

```bash
cd /path/to/macao && python3 - <<'PY'
import json, glob, os, copy, yaml, jsonschema, re

# 脚本 A：全 docs 树控制字符按字节扫描（N-1 验收）
tot = 0
for f in glob.glob('docs/**/*.md', recursive=True):
    c = sum(1 for x in open(f, 'rb').read() if x in (9, 11, 12, 13))
    if c: print("  %s: %d" % (f, c)); tot += c
print("脚本A 控制字符总数:", tot, " (期望 0)")

# 脚本 B：反例测试 —— 必须打印拒因并确认拒因就是被测约束（本轮自审教训）
print("\n脚本B AEP 逐维度隔离（以合法 fixture 为基底，一次只改一个字段）")
A = json.load(open('docs/schemas/aep_envelope.schema.json'))
VA = jsonschema.Draft7Validator(A)
base = json.load(open('docs/schemas/fixtures/valid/aep_review_request.json'))
assert not list(VA.iter_errors(base)), "基底 fixture 应合法"
for name, mut in [
        ("protocol 降为 AEP/1.0",               lambda x: x.update(protocol='AEP/1.0')),
        ("AEP/1.0 + 1.1 专有类型 DISPOSITION_REQUIRED",
         lambda x: (x.update(protocol='AEP/1.0'), x.update(type='DISPOSITION_REQUIRED'))),
        ("payload 60KB（超 16 KiB 预算）",       lambda x: x.update(payload={'x': 'y' * 60000}))]:
    t = copy.deepcopy(base); mut(t); e = list(VA.iter_errors(t))
    print("  %s %s%s" % ("**接受**" if not e else "拒绝  ", name,
                         "" if not e else "  拒因: " + e[0].message[:80]))

# 脚本 C：PRD 正文示例对各自 Schema 校验（按章节标题定位）
L = open('docs/MACAO_PRD_v2.md').read().split('\n')
def sec(pat):
    st = None
    for i, l in enumerate(L):
        if re.match(r'^#{2,4} ', l):
            if st is not None: return st, i
            if re.search(pat, l): st = i
    return st, len(L)
def blk(a, b, lang):
    for i in range(a, b):
        if L[i].strip() == '```' + lang:
            j = i + 1
            while L[j].strip() != '```': j += 1
            return '\n'.join(L[i + 1:j])
print("\n脚本C PRD 示例 vs docs/schemas/")
for name, pat, lang, sf, load, key in [
        ('§2.1 .dev.yml',    r'### 2\.1 ', 'yaml', 'dev_manifest',       yaml.safe_load, None),
        ('§2.2 .review.yml', r'### 2\.2 ', 'yaml', 'review_manifest',    yaml.safe_load, None),
        ('§2.3 vote_result', r'### 2\.3 ', 'json', 'vote_result',        json.loads,     None),
        ('§2.5 disposition', r'### 2\.5 ', 'yaml', 'review_disposition', yaml.safe_load, None),
        ('§5.2 context',     r'### 5\.2 ', 'yaml', 'review_context',     yaml.safe_load, 'review_context'),
        ('§13 macao.yaml',   r'^## 第十三部分', 'yaml', 'macao_config',  yaml.safe_load, None)]:
    a, b = sec(pat); inst = load(blk(a, b, lang))
    if key: inst = inst[key]
    errs = sorted(jsonschema.Draft7Validator(json.load(open('docs/schemas/%s.schema.json' % sf))).iter_errors(inst),
                  key=lambda x: list(x.path))
    print("  %-18s vs %-30s -> %s" % (name, sf + '.schema.json', "PASS" if not errs else "FAIL(%d)" % len(errs)))
    for x in errs[:4]: print("       -", list(x.path) or "(root)", x.message[:120])

# 脚本 D：decision 枚举 / disposition 条件约束 falsify
print("\n脚本D 枚举与条件约束")
VV = jsonschema.Draft7Validator(json.load(open('docs/schemas/vote_result.schema.json')))
vr = json.loads(blk(*sec(r'### 2\.3 '), 'json'))
for dv in ['APPROVED', 'REWORK_REQUIRED', 'DEADLOCK', 'RETRY_REVIEW', 'CANCELLED']:
    x = copy.deepcopy(vr); x['decision'] = dv
    print("  decision=%-16s -> %s" % (dv, "接受" if not list(VV.iter_errors(x)) else "拒绝"))
print("  consensus_rule enum:",
      json.load(open('docs/schemas/macao_config.schema.json'))['properties']['policy']['properties']['consensus_rule'])
VD = jsonschema.Draft7Validator(json.load(open('docs/schemas/review_disposition.schema.json')))
d0 = yaml.safe_load(open('docs/schemas/fixtures/valid/disposition.yml').read())
def dt(name, mut):
    x = copy.deepcopy(d0); mut(x); e = list(VD.iter_errors(x))
    print("  %s %s" % ("拒绝OK " if e else "**接受✗**", name))
dt("FINAL + NEEDS_ADMIN",          lambda x: (x.update(disposition_status='FINAL'),
                                              x['dispositions'][0].update(disposition_type='NEEDS_ADMIN')))
dt("EXEMPTED_BY_ADMIN 缺 override_id",
                                   lambda x: x['dispositions'][0].update(disposition_type='EXEMPTED_BY_ADMIN'))
print("  §2.5 是否记载 override_id:",
      'override_id' in '\n'.join(L[sec(r'### 2\.5 ')[0]:sec(r'### 2\.5 ')[1]]))

# 脚本 E：fixtures 全量回放（映射不到 Schema 时必须单独补测，勿记为缺陷）
print("\n脚本E fixtures 回放")
M = {'review_context': 'review_context', 'context': 'review_context', 'vote_result': 'vote_result',
     'review': 'review_manifest', 'dev': 'dev_manifest', 'aep': 'aep_envelope',
     'disposition': 'review_disposition', 'admin_override': 'admin_override', 'macao': 'macao_config'}
for kind in ['valid', 'invalid']:
    for f in sorted(glob.glob('docs/schemas/fixtures/%s/*' % kind)):
        n = os.path.basename(f)
        sf = next((v for k, v in sorted(M.items(), key=lambda x: -len(x[0])) if n.startswith(k)), None)
        inst = json.loads(open(f).read()) if f.endswith('.json') else yaml.safe_load(open(f).read())
        errs = list(jsonschema.Draft7Validator(json.load(open('docs/schemas/%s.schema.json' % sf))).iter_errors(inst))
        ok = (not errs) if kind == 'valid' else bool(errs)
        print("  %s %-8s %-44s %s" % ("OK " if ok else "**✗**", kind, n,
                                      "PASS" if not errs else "REJECT(%d)" % len(errs)))
PY

# 脚本 F：Schema 镜像一致性 + 回归门禁建议
for f in docs/schemas/*.json; do b=$(basename "$f")
  diff -q "$f" "src/macao/schemas/$b" >/dev/null 2>&1 || echo "DRIFT $b"; done
PYTHONPATH=src python3 -m unittest discover tests 2>&1 | tail -3
```

---

## 六、建议的闭环顺序与验收标准

| 序 | 事项 | 验收标准 |
|---|---|---|
| 1 | **M-1** §5.2 与契约对齐 | §五脚本 C 的 `§5.2 context` 行为 PASS；二选一：`required_blocks` 进 Schema `properties`，或从 §5.2 删除该冗余块 |
| 2 | **M-2** `consensus_rule` | 移除 `2/3_majority`，或保留并在 §13 + `schemas/README.md` 标注为存量兼容值并用 `if/then` 绑定 `version`；同步修正申请 §4 表述 |
| 3 | **M-3** §2.5 补全 | §2.5 格式块含 `override_id`，守卫增加 `EXEMPTED_BY_ADMIN` 的两项强制约束；新增覆盖该路径的正例 fixture |
| 4 | **把回归检查固化为交付前门禁**（针对连续三轮的同一模式） | 建议最小三条，全部可脚本化：①**PRD 正文各节示例纳入 fixture 回放范围**（M-1 正是因为只回放 `fixtures/` 而漏检）；②反例测试断言拒因关键字/路径，而非只断言「被拒」（§0.1 第一条）；③全 `docs/` 树控制字符扫描 + 交叉引用悬空扫描。三条均已在 §五脚本中给出实现 |
| 5 | **M-4～M-7（P2）** | AEP 建立按 `type` 的 payload 条件 Schema 并指明字节预算的唯一强制落点；`dev_manifest` 的 `full_document` 等按 §1.2 / F-15 进 `required`；`resolution` 去同义值并修正 UC-5 L66；裁定 `dictator_cap_enabled` 语义（建议直接删除开关）并在文档区分 Schema 与运行期 validator 的职责边界 |
| 6 | 复评 L1 / PG-0 | 第 1～3 项闭合即可授予；建议最小差量快速复评 |

**不建议**：把 M-1 当作「只是示例里多一个键」放行——它使 §5.2 这份被三处正文称为「唯一权威完整模型」的节区不可直接引用，且是同一缺陷类别的第三次出现。**同样不建议**：因本轮仍为 `NO_APPROVE` 而低估进展——我上轮 2 项阻断 + 7 项 P2/P3、Codex 3 项 P1 均为可验证的实质闭环，反例库 11/11 维持全通过且其中 3 条判据更强。

---

## 七、与其他 Reviewer 的交叉核对（GUIDELINES §8）

截至本报告完成，`2da1bc2` 轮**尚无其他 reviewer 出具报告**（`docs/reviews/` 下本轮仅本文件）。按 §8「沉默 ≠ 同意」，Codex / GLM / Grok / Kimi / Qwen / ZCode 均不计入任何一方。

对上一轮（`2766c69`）的分歧走向，据实记录：我与 Codex 判 `NO_APPROVE`、GLM 与 Qwen 判授予（2:2）。**本轮结果支持了 2 项阻断的实质性**——申请方接受并修复了我与 Codex 独立收敛的两项，且两项均为 GLM 与 Qwen 未覆盖的检测面。这不构成对 GLM / Qwen 结论的否定（其复核的 11～13 项闭环我亦独立确认为真），但佐证了 GUIDELINES §8「真理不等于投票」在本项目上的适用性：多数票未必覆盖全部检测面。

本轮我对 Codex 上轮 7 项 P1 全部做了独立复核（§1.3），其中 P1-3 与 P1-6 我判为**部分闭环**（申请判为全闭环），P1-5 我判为 **CONTRADICTED**。若 Codex 本轮出具报告，这三项预计是主要重合点。

---

## 附：机器票与结构化 issue 清单

| issue_id | severity | disposition_class | 摘要 |
|---|---|---|---|
| `claude/M-1` | major | `BLOCKING` | §5.2「唯一权威完整模型」被自身契约拒绝（`additionalProperties: false` 与 `required_blocks` 冲突）；上轮 PASS、本轮 FAIL，属回归，并证伪申请 §3「100% PASS」 |
| `claude/M-2` | major | `BLOCKING` | `consensus_rule` 枚举实为 `["weighted_2/3_v1","2/3_majority"]`，与申请 §4「严格收敛为单值」矛盾；`2/3_majority` 全库无迁移或兼容说明 |
| `claude/M-3` | major | `BLOCKING` | `review_disposition` 契约新增的 `EXEMPTED_BY_ADMIN ⟹ override_id 必填 + requires_new_checkpoint=false` 未进入权威基准 §2.5，正例 fixture 亦未覆盖 |
| `claude/M-4` | minor | `ADVISORY` | Codex P1-3 的 AEP 半边未闭环且未列入闭环表：`AEP/1.0` 可载 1.1 专有类型、60 KB payload 被接受、无按 `type` 的 payload 条件 Schema、字节预算无强制落点 |
| `claude/M-5` | minor | `ADVISORY` | `dev_manifest` 的 `task_id`/`checkpoint_ref`/`full_document` 只进 `properties` 未进 `required`，与 §1.2 离开条件及 F-15 不符 |
| `claude/M-6` | minor | `ADVISORY` | `resolution` 同义对 `automatic` / `AUTO_WEIGHTED_CONSENSUS` 并存；UC-5 L66 仍引用已被枚举拒绝的 `human_override` |
| `claude/M-7` | minor | `ADVISORY` | `dictator_cap_enabled` 仍为可关开关，与 §2.3 无条件表述及 F-22 冲突；Schema 与运行期 validator 的职责边界仍未在文档中划分 |
| `claude/M-8` | trivial | `ADVISORY` | STATUS.md 未登记本轮（`2766c69 .. 2da1bc2`），文首仍停在上一轮票型 |

```
vote: NO_APPROVE
requires_new_checkpoint: true   # 需产生新的文档 checkpoint；预计改动约 15 行，建议最小差量快速复评
```
