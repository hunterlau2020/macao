# MACAO 文档门禁状态（Live Status）

> 依据 `docs/MACAO_REVIEW_GUIDELINES.md` 维护；本文件是唯一允许记录实时门禁状态的位置。
> 治理规则（P1-3 确立，已固化）：**每轮申请复审前，STATUS 必须与 `reviews/` 目录全量对账**，不得以 STATUS 登记子集为闭环核验边界。

- 更新时间：2026-08-26（v2.3.1 修订完成，待第四轮独立复审）
- 最近复审对象：commit `cc77a94`（PRD v2.3），**五份独立评审结论一致：未达 L1**（2 P0 + 3 P1 + 9 P2 + 11 P3 + 1 分歧项），均已按下方清单在 **PRD v2.3.1** 修订闭环。
- 当前等级：**PENDING_REVIEW**（v2.3.1 待独立复审定级；目标 L1 DOC-ALIGNED / PG-0）
- 当前版本：PRD **v2.3.1**；schemas 6 个（$id 统一 v2.3）+ fixtures 11 个（正 7 反 4）；本轮机验 **18/18 PASS**。

## v2.3.1 修订闭环清单（对应 cc77a94 五份评审全部交付项）

| 编号 | 级别 | 修订内容 | 落点 |
|------|------|---------|------|
| P0-1 | P0 | "评审对象=合并对象"硬绑定：rebase 豁免**废除**（MVP 任何新 hash 含 clean rebase/cherry-pick/amend → E4b）；E4a 增加 push 对象==checkpoint_ref 硬校验；受控 range-diff 门禁（三重条件）规划 v1.1；`rebase_before_merge` MVP 禁用 | PRD §14.5 步 1、§13 配置、§3.3 E4a |
| P0-2 | P0 | worktree **强制化**：§16.3 三行改强制 + 拓扑图改"主工作区+每 Reviewer 独立 worktree"；Type B/§5.2/三个 fixture 的 workspace_path 改注入后 worktree 路径；§12.2 增加 `supports_worktree=true` 准入硬条件（preflight/Conformance） | PRD §16.3/§12.2/§2.4/§5.2、schemas fixtures |
| P1-1 | P1 | 弃权口径裁决（方案②）：`.review.yml` vote 枚举**移出 ABSTAIN**；§2.2 注明"弃权仅由 Orchestrator 超时降级写入 vote_result"；新增反例 fixture | review_manifest.schema.json、PRD §2.2、fixtures/invalid/review_abstain_invalid.yml |
| P1-2 | P1 | artifacts 改 `artifact_id` 自增主键 + `(task_id,kind,ref,round,reviewer_id)` 唯一约束；§11.5 增加"追加归档语义"（新插行非 upsert、历史行只读） | PRD §11.4 DDL、§11.5 |
| P1-3 | P1 | 治理对账：STATUS 与 reviews/ 全量对账完成（8ab9be7 五份 + cc77a94 五份全部登记）；对账规则固化于本文档引言 | STATUS.md（本文件） |
| 分歧项 | — | Deadlock 入口边按**并集方案 B** 落文：E3 伴随动作内联确定性票数判定（Deadlock→发 Type G + HOLD + 不写 vote_result）；§3.4 补场景三（1:1 平票 + REWORK/RETRY/CANCEL/弃权变体） | PRD §3.3 E3 行、§3.4 |
| P2-1 | P2 | E7 CANCEL→E10、E10 触发补 override 路径；Type G options/§6.1 trigger 3/§2.3 枚举补 CANCEL | PRD §3.3/§2.4/§6.1/§2.3 |
| P2-2 | P2 | Layer 1c 补 max_rework_rounds 守卫（达上限不落盘自动 decision，发 Type G → E7） | PRD §3.2 伪代码 |
| P2-3 | P2 | §11.4 DDL 注释改"10 态之一（含 CANCELLED）" | PRD §11.4 |
| P2-4 | P2 | IMPROVEMENT_SUMMARY L160 `quality_metrics`→`quality_snapshot` | IMPROVEMENT_SUMMARY |
| P2-5 | P2 | PRD §10 成功标志 ✅ → `[ ]` 验收标准（未达成前不得勾选） | PRD §10 |
| P2-6 | P2 | `macao merge approve` 补入 §14.2 命令表（注明与 override resolve 区别） | PRD §14.2 |
| P2-7 | P2 | §16.3"其余全自动"→"…`merge approve` 签字放行，其余自动" | PRD §16.3 |
| P2-8 | P2 | AEP per-type payload Schema：维持登记为 PoC 前置工作（schemas/README 如实表述覆盖面） | schemas/README |
| P2-9 | P2 | §3.4 场景三落文；新增终局 fixture（decision=APPROVED+resolution=human_override）；vote_result decision 枚举扩 RETRY_REVIEW/CANCELLED + 两值强制 human_override 的 if/then | PRD §3.4、vote_result.schema.json、fixtures/valid/vote_result_human_override.json |
| P3-1~P3-11 | P3 | 版本指针统一 v2.3.1（EXEC/README/IMPROVEMENT 标题）；§1.1 REVIEWING→WAITING_REVIEW、REJECTED→REWORK_REQUIRED；§2.4"4 个"→"7 个"；§16.1 E1~E10；Schema $id 全部 v2.3；§12.4/README 清单补 review_context；§14.1"14.6"勘误；README"L0~L4"→"L1~L4"；EXEC"100% 可靠"加设计目标标注；IMPROVEMENT 叙事数字豁免登记 | 各文档及 Schema |

**机验结果（本轮修订后独立重跑）**：6 Schema 自检 PASS；fixtures 7 正例 VALID + 4 反例被正确拒绝（含新增 human_override 正例、ABSTAIN 反例）；PRD §2.4 Type B/§5.2 完整模型/§2.3 vote_result 示例、EXEC 三示例、IMPROVEMENT context 示例全部 PASS；合计 **18/18**。

## 评审专家分工评估结论（2026-08-26，供下一轮排班参考）

依据对全部 16 份评审报告的四轮质量评估：保留核心三人组 **claude（语义/产品轴）+ codex（安全/审计轴）+ opencode（治理/法证轴）**；**gemini 退出定级轮**（两次定级误判史 + 与 codex 角度重合）；kimi 与 opencode 角度同构，同轮不同时出场。详见评审申请时的排班说明。

## 下一步

1. 对 **PRD v2.3.1** 提出新一轮独立复审申请（随本次修订一并提交），重点核查：P0-1 rebase 硬校验闭环、P0-2 worktree 三处一致性、Deadlock 入口边（E3 伴随动作）+ §3.4 场景三的转移唯一性、ABSTAIN 口径与 artifacts 追加语义、vote_result 四值终局模型的 Schema 强制性；
2. 若无新 P0/P1，仅余 P2/P3 → 宣告 **L1 DOC-ALIGNED / PG-0**，正式启动 Week 1-2 PoC；
3. P2-8（AEP per-type Schema）与 E2E 测试矩阵随 PoC 前置工作产出并回填。