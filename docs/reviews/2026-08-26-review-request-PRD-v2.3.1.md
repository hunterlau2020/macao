# MACAO PRD v2.3.1 独立复审申请

> **申请日期**：2026-08-26
> **申请人**：文档维护方（ox-alpha 会话）
> **待审对象**：`docs/MACAO_PRD_v2.md` **v2.3.1** 及配套——`EXECUTIVE_SUMMARY.md`、`IMPROVEMENT_SUMMARY.md`、`docs/schemas/*`（6 Schema，$id 统一 v2.3；fixtures 11 个）、`docs/README.md`、`docs/reviews/STATUS.md`
> **对应 commit**：本申请与修订同批提交；评审以包含 "v2.3.1" 提交的 `main` HEAD 为准（`git log --oneline -1`）

## 一、性质与定级目标

- 性质：**L1 DOC-ALIGNED 定级复审（第四轮）**；上轮 `cc77a94` 五份独立评审（kimi/opencode/codex/claude/gemini）结论一致的 2 P0 + 3 P1 已全部按 STATUS 清单修订，本轮为闭环确认轮
- 目标等级：**L1 DOC-ALIGNED / PG-0**
- 前置声明：代码实现与厂商 CLI 兼容性验证仍不存在；P2-8（AEP per-type payload Schema）与 E2E 测试矩阵按约定随 PoC 前置工作回填

## 二、上轮发现的处理坐标（逐条复核）

完整清单见 `docs/reviews/STATUS.md` 的"v2.3.1 修订闭环清单"表；关键落点：

| 编号 | 修复落点 |
|------|---------|
| P0-1 rebase | PRD §14.5 步 1（豁免废除 + E4a push 对象硬校验 + v1.1 受控门禁三条件）、§13 `rebase_before_merge` 禁用、§3.3 E4a 行 |
| P0-2 worktree | PRD §16.3 三行 + 拓扑图、§12.2 准入硬条件、§2.4 Type B/§5.2 示例与三个 fixtures 的 workspace_path |
| P1-1 ABSTAIN | `review_manifest.schema.json` vote 枚举移出 ABSTAIN；PRD §2.2/§3.3 超时行注明"弃权仅由 Orchestrator 记票、终局落盘"；反例 fixture `review_abstain_invalid.yml` |
| P1-2 artifacts | PRD §11.4 DDL（artifact_id 自增 + 五元组唯一约束）、§11.5 追加归档语义 |
| P1-3 治理 | STATUS 全量对账完成 + 对账规则固化（STATUS 引言） |
| Deadlock 分歧项 | 并集方案 B 落文：§3.3 E3 伴随动作（确定性票数判定 → Deadlock 即发 Type G、HOLD、不写 vote_result）+ §3.4 场景三（1:1 + REWORK/RETRY/CANCEL/弃权变体） |
| P2-9 终局模型 | `vote_result.schema.json` decision 扩 RETRY_REVIEW/CANCELLED + human_override 强制 if/then；正例 fixture `vote_result_human_override.json` |

## 三、本轮重点核查（高风险区）

1. **P0-1 闭环唯一性**："target 领先、clean rebase"场景下，E4a 硬校验能否唯一证明无未评审内容进入 push；受控门禁三条件与 MVP 禁用表述无矛盾；
2. **P0-2 三处一致性**：§12.2（强制约束+准入条件）、§16.3（三行表格+拓扑图）、§2.4/§5.2/三个 fixture（注入后 worktree 路径）与正文不再有"可选/主工作区"表述残留；
3. **Deadlock 入口与终局**：E3 伴随动作 → E7 裁定 → E4/E5/E9/E10 四分支在 §3.4 场景三可逐步骤唯一推导；vote_result 四值 decision 与 Schema if/then 强制 human_override 的一致性；
4. **ABSTAIN/artifacts**：`.review.yml` 已无法表达弃权，弃权票只能终局落盘；artifacts 追加语义与 §3.4 生命周期表无 upsert 覆盖历史审计行。

## 四、机器校验复现指引（18 项）

```text
环境：python3 + jsonschema（draft-07）+ PyYAML
1. 6 个 docs/schemas/*.schema.json 经 Draft7Validator.check_schema 自检
2. fixtures/valid/ 7 例通过对应 Schema：
   aep_review_request / dev / review / review_context_full / review_context_minimal /
   vote_result / vote_result_human_override
3. fixtures/invalid/ 4 例必须被拒绝：
   aep_unknown_type（type 枚举）/ context_missing_refs（refs 必填）/
   review_abstain_invalid（ABSTAIN 死枚举）/ review_status_vote_conflict（if/then）
4. PRD 示例：§2.4 Type B payload.review_context 过 review_context.schema.json；
   §5.2 完整模型 YAML 过同一 Schema；§2.3 vote_result 示例过 vote_result.schema.json
5. EXEC 三产物示例、IMPROVEMENT_SUMMARY context 示例过对应 Schema
6. git diff --check 无空白错误
```

## 五、评审排班（依据 2026-08-26 四轮质量评估结论）

- **本轮阵容**：claude（语义/产品轴）+ codex（安全/审计轴）+ opencode（治理/法证轴）——三角色互不重叠；
- gemini 退出定级轮（两轮定级误判历史，且 P0 发现与 codex 角度重合）；kimi 与 opencode 角度同构，不同轮互替。

## 六、期望产出

按 `MACAO_REVIEW_GUIDELINES.md`，若复核仅余 P2/P3 → 宣告 **L1 DOC-ALIGNED / PG-0** 并更新 `docs/reviews/STATUS.md` 为 L1；输出 `docs/reviews/<date>-review-result-<commit>-<reviewer>.md`（逐条路径+行号证据）。