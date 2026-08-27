# MACAO PRD v2.3.1 独立复审结论（L1 闭环确认轮）

- **评审日期**：2026-08-27
- **评审人**：zcode（独立评审，GLM）
- **评审对象**：`docs/MACAO_PRD_v2.md` v2.3.1 及配套（commit `403ddc7`，含 EXECUTIVE_SUMMARY / IMPROVEMENT_SUMMARY / docs/schemas 6 Schema + 11 fixtures / docs/README / STATUS）
- **对齐基准**：`docs/MACAO_PRD_v2.md`（权威基准）+ `docs/MACAO_REVIEW_GUIDELINES.md` v1.0
- **申请文件**：`docs/reviews/2026-08-26-review-request-PRD-v2.3.1.md`
- **结论**：**未达 L1 DOC-ALIGNED / PG-0（本轮）**——上轮 cc77a94 的 2 P0 + 3 P1 + 分歧项 + P2-9 修复全部核验通过，但 P2-9 的 Schema 四值化未同步修订 §3.2 Layer 1c，引入 **1 项新的 P1 文档内矛盾**；另登记 2 P2 + 3 P3。修订面极小（单点），修后可直复核该点宣告 L1。

---

## 一、机验复现（申请 §四，18 项）

评审人独立重跑（Python 3.11.9 + jsonschema 4.24.0 + PyYAML，Windows/Git Bash）：**23 项检查全部 PASS**（覆盖申请全部 18 项：6 Schema 自检、7 正例、4 反例被拒、PRD §2.4 Type B / §5.2 / §2.3 示例、EXEC 三产物、IMPROVEMENT context、git diff --check clean）。关键反例拒绝原因确认：`review_abstain_invalid.yml` 同时命中 "'ABSTAIN' is not one of ['YES_APPROVE','NO_APPROVE']"（枚举反例）与 status=APPROVED 期望 YES_APPROVE（映射反例）。**机验声明与事实一致。**

## 二、上轮发现闭环核验（逐条，VERIFIED）

| 编号 | 核验结论 | 证据（路径:行号） |
|------|---------|------------------|
| P0-1 rebase 豁免废除 | **VERIFIED** | PRD §14.5 步 1（`MACAO_PRD_v2.md:1533`：任何新 hash 含 clean rebase/cherry-pick/amend → E4b；豁免"明确废除"；v1.1 受控门禁三重条件）；§13（`:1471` `rebase_before_merge: false` MVP 禁用 + 三重条件指引）；§3.3 E4a 行（`:832` "最终 push 对象 == `vote_result.json.checkpoint_ref` 硬校验…期间未产生任何新 commit"）。三处口径一致，无矛盾 |
| P0-2 worktree 强制化 | **VERIFIED** | §16.3 拓扑图（`:1619-1620` "每 Reviewer 独立 worktree"）与隔离行（`:1629` "**强制**…准入硬条件…绝不进入 Executor 主工作区"）；§12.2（`:1406` 准入硬条件）；§2.4 Type B（`:499`）与 §5.2（`:985`）workspace_path 均为 `~/work/macao-demo/.macao/worktrees/...` 注入路径；三个 fixture（`schemas/fixtures/valid/{aep_review_request.json, review_context_full.json, review_context_minimal.json}` repository.workspace_path 均为 worktree 路径）。grep 全文无 worktree"可选"残留；"主工作区"仅出现于禁令/说明性否定语境（`:985` `:1629`） |
| P1-1 ABSTAIN 死枚举移除 | **VERIFIED** | `review_manifest.schema.json:59` vote 枚举仅 `YES_APPROVE/NO_APPROVE`；§2.2（`:305` "ABSTAIN 不在此枚举…弃权票仅由 Orchestrator…写入 vote_result.json"）；`:318` 弃权口径；§3.3 超时行（`:830` "随 E7 终局 vote_result 一并落盘，不提前写"）；反例 fixture 机验被拒 ✓ |
| P1-2 artifacts 复合主键+追加语义 | **VERIFIED（文档）** | §11.4 DDL（`:1325` `artifact_id INTEGER PRIMARY KEY AUTOINCREMENT`；`:1332` `UNIQUE(task_id, kind, checkpoint_ref, review_round, reviewer_id)`）；§11.5（`:1353` "新增行而非同路径 upsert…不用覆盖式写入抹掉历史审计行"）。注：**代码实现回退了本项**，见同日代码评审报告 P1-4 |
| P1-3 治理对账 | **PARTIALLY_VERIFIED** | 引言规则已固化（`STATUS.md:4`）；但当前 STATUS 对账表为子集（见新发现 P2-1） |
| Deadlock 分歧项（并集方案 B） | **VERIFIED** | §3.3 E3 行（`:829` "票数判定是确定性函数…发送 HUMAN_OVERRIDE_REQUEST…**HOLD，不写 vote_result.json**，等待 E7"）；§3.4 场景三（`:888-902`）步骤 5 + 6a/6b/6c/6d + 7 可逐步骤唯一推导，四选项与 E4/E5/E9/E10 落位一一对应；弃权变体经超时降级入链 ✓；Type G options 含 CANCEL（`:686`）与 §6.1 trigger 3（`:1124`）一致 |
| P2-9 四值终局模型 | **PARTIALLY_VERIFIED** | `vote_result.schema.json:51` decision = `APPROVED/REWORK_REQUIRED/RETRY_REVIEW/CANCELLED`；`:86-90` if/then 强制 RETRY_REVIEW/CANCELLED ⇒ resolution=human_override；正例 fixture `vote_result_human_override.json` 机验通过。**但 §3.2 未同步**（见新发现 P1-1） |

## 三、新发现

### P1：必须先解决

**P1-1 §3.2 Layer 1c 与 vote_result 四值 Schema 直接矛盾（CONTRADICTED，影响状态机行为）**

- `MACAO_PRD_v2.md:779-780`：注释声明 "显式两分支：**decision 枚举仅 APPROVED | REWORK_REQUIRED（Schema 强制）**"——与 `vote_result.schema.json:51` 的四值枚举事实相反（"Schema 强制"为虚假陈述）。
- 同段伪代码（`:781-787`）无 RETRY_REVIEW/CANCELLED 分支：`decision == 'APPROVED'` 不成立时 fall-through 到 `if rnd < max_rework_rounds: return REWORK`。若 Layer 1c 读到合法的 `decision=RETRY_REVIEW`（E7 落盘后、E9 命令转移前发生崩溃/重启，§11.5 以物理产物为第一真理源重放），将**误路由到 E5 REWORK**，与 E7 行（`:836` "RETRY_REVIEW→E9；CANCEL→E10"）冲突，破坏 §3.3 验收标准"任意时刻每一步最多命中一个合法转移"。
- 按 GUIDELINES §8"可能影响状态机行为…按 P0/P1 处理"：主路径 E7 为命令驱动且无歧义、影响窗口为崩溃重放场景、无审计链/安全边界破坏，定级 **P1**。
- 修复建议：§3.2 注释改为四值表述；伪代码补显式分支（RETRY_REVIEW→E9、CANCELLED→E10，或声明这两值仅由 E7 命令驱动消费、Layer 1c 遇之即 HOLD 并告警）。

### P2：应修正

**P2-1 STATUS"全量对账"实为子集对账**：`reviews/` 目录共 17 份结果文件，当前 `STATUS.md:16-21` 对账表仅覆盖 8 份（ec60f70×3 + cc77a94 轮×5）；`47f54f2-codex`（1）、`684a012-*`（3）、`8ab9be7-*`（5）共 **9 份**未出现在任何行。403ddc7 时点 STATUS 的 P1-3 声明（"8ab9be7 五份 + cc77a94 五份全部登记"）亦未覆盖前两轮。因历史轮 P0/P1 均已经后续 PRD 版本闭环（版本历史 `:1704-1728` 可证）、无隐藏未决项，定级 P2：补三行历史轮登记或在表后附全量文件清单。

**P2-2 `strategy: no_ff` 与 E4a 硬校验不相容**：§13（`:1468`）提供 `ff_only | no_ff`，§14.5 步 2（`:1534`）允许 no_ff 合并；但 no_ff 必产生 merge commit，违反 E4a（`:832`）"期间未产生任何新 commit…push 对象 == checkpoint_ref"硬校验 → no_ff 配置下 E4a 结构上恒失败 → 恒 E4b。两处未调和（应标注 no_ff 仅 v1.1 受控门禁后可用，或定义 push 对象校验为祖先包含语义）。

### P3：可延期但需登记

- **P3-1** §1.1 简图 MERGING 框仍含 "merge / rebase" 步骤字样（`:104-105`）——MVP 已禁 rebase 且豁免废除，P0-1 修订未同步该图（有 `:117` "以 §3.3 为准"兜底，`§3.4:869` "rebase 检查"措辞可自洽，定 P3）。
- **P3-2** `input_artifacts.kind` 术语三分支：§2.3 示例 `"review"`（`:358`）vs fixture `"review_manifest"` vs §11.4 DDL 注释 `review_manifest`（`:1327`）。违反 GUIDELINES §5 唯一权威表原则（Schema 仅要求 string 故均可通过校验）。
- **P3-3** `vote_result.schema.json:91-94` 第二个 if/then 的 then 子句未含 `"required": ["next_step"]`——decision∈{APPROVED,REWORK_REQUIRED} 且 resolution=human_override 时缺 next_step 仍可通过校验，"human_override 须带 next_step"强制力弱化。

## 四、交叉文档文字修订

1. `docs/schemas/vote_result.schema.json`（P3-3）或 PRD §2.3（P3-2，kind 统一为 review_manifest）二选一处收敛术语。
2. STATUS.md 补历史轮登记（P2-1）。

## 五、建议闭环顺序与验收标准

1. 修 P1-1（§3.2 注释 + 伪代码分支，预计 <10 行改动）→ 复核该单点（可由任一已排班 reviewer 书面确认）→ 宣告 **L1 DOC-ALIGNED / PG-0**；
2. P2-1/P2-2 随下一次文档批量修订提交（可与代码轮修订合并出 v2.3.2）；
3. 验收标准：`grep -n "仅 APPROVED | REWORK_REQUIRED" docs/MACAO_PRD_v2.md` 无输出；对 `decision=RETRY_REVIEW` 的 Layer 1c 行为在 §3.2 有显式、唯一的规定。

## 六、Reviewer 自审记录

- 无连续漏审史，首次参与 MACAO 评审，无激活 checklist 项。
- 自检（GUIDELINES §9 强制 5 项）：字段名 vs 读取路径已逐处核对（§2.1/§2.2/§3.2 伪代码路径一致）；本轮发现的"[x]≠证据"类问题在代码评审报告（PLAN/ROADMAP 虚假完成声明）；确定性用语无新增违规；全部 YAML/JSON 代码块经机验可解析；本报告每项 REJECT 均附路径+行号。
