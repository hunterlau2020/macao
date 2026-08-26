# MACAO PRD v2.3 独立复审申请

> **申请日期**：2026-08-26
> **申请人**：文档维护方（ox-alpha 会话）
> **待审对象**：`docs/MACAO_PRD_v2.md` **v2.3** 及配套变更——`EXECUTIVE_SUMMARY.md`、`IMPROVEMENT_SUMMARY.md`、`docs/schemas/*`（含新增 `review_context.schema.json` 与 9 个 fixtures）、`docs/README.md`
> **对应 commit**：本申请与修订同批提交；评审以包含 "PRD v2.3" 提交后的 `main` HEAD 为准（hash 以 `git log --oneline -1` 输出为准）

## 一、复审性质与定级目标

- 性质：**L1 DOC-ALIGNED 定级复审**（上一轮 `8ab9be7` 的两份评审结论均为 PENDING_REVIEW，本轮为其闭环轮）
- 目标等级：**L1 DOC-ALIGNED / PG-0**（允许开始编码与 PoC；不外推 L2+）
- 前置声明：代码实现、厂商 CLI 兼容性验证尚不存在，不在本轮评审范围内

## 二、上轮发现的处理情况（应逐条复核关闭）

| 来源 | 应复核项 | 修复位置 |
|------|---------|---------|
| kimi P0-1 / opencode P1-3 | review_context 唯一权威结构 | §5.2 完整模型（两传输块+六语义块）；§2.4 最小子集；新增 `schemas/review_context.schema.json` |
| opencode P1-4 | Deadlock 终局表达 / Layer 1c 静默 else / override 枚举三处不一致 / CANCEL 无终态 | 终局 vote_result（`resolution` 字段）；Layer 1c 显式两分支；枚举统一 APPROVED/REWORK/RETRY_REVIEW/CANCEL；新增 E9/E10 与 `CANCELLED` 终态（FSM 10 态） |
| opencode P1-1 | §6.1 触发条件 1 残留 "Layer 2 confidence < 0.7" | 改为 Layer 3/E8 口径 + 人工接管超时总则 |
| opencode P1-2 | §1.1 图缺 MERGING、回环标注不符；§1.2 行不同步 | 图重绘 + 简化视图说明；§1.2 行同步；README 导航行修正 |
| kimi P1-1/2/3 | EXEC 三处产物示例未通过 Schema | 三示例已重写并通过对应 Schema（见第四节机验清单） |
| kimi P1-4/P1-5 | 计划类 ✅ 无证据；字段类型不合法 | 全部改为【计划】/[ ] 待验证；整数化 |
| 双方 P2/P3 | Type D round 语义、Type F attachments、KPI 分母、timeouts 注释、占位符、标题版本、架构速写对齐、"↑500%" 等 | 均已落文，逐条位置见 `reviews/STATUS.md` 本节表格 |

## 三、请复审方重点核查（高风险区）

1. **review_context 单一结构**：§2.4 最小子集与 §5.2 完整模型的顶层键名/嵌套路径是否完全一致；`review_context.schema.json` 是否同时接受两者；
2. **Deadlock 流程唯一性**：从 E3 到终局的每一步（含人工裁定落盘 `resolution=human_override` 后的转移）能否唯一推导；
3. **10 态 FSM 一致性**：§1.1（简化视图）、§1.2、§3.3、§11.4 State Store、执行摘要之间的状态清单与边引用无矛盾；
4. **摘要文档示例**：EXEC 三示例、IMPROVEMENT_SUMMARY context 示例是否通过对应 Schema。

## 四、机器校验复现指引

评审方可重放以下检查（环境需 python3 + jsonschema + PyYAML）：

```text
1. schemas 自身合法：json.load(docs/schemas/*.schema.json)
2. fixtures 行为：valid/ 6 例通过对应 Schema；invalid/ 3 例被正确拒绝
   （含 status↔vote if/then 冲突例、context 缺 refs 例、AEP 未知 type 例）
3. PRD 内嵌示例：8 个 JSON 块解析；7 个 AEP 信封过 aep_envelope.schema.json；
   §2.4 Type B 的 payload.review_context 过 review_context.schema.json；
   5 个 YAML 块解析；§2.1/§2.2/§13 示例过对应 Schema
4. EXEC 三产物示例过对应 Schema；IMPROVEMENT_SUMMARY context 过 Schema
5. git diff --check（空白错误）
```

## 五、已知未覆盖项（不构成否决项，登记在案）

- E2E 测试用例矩阵、LLD 模块设计、错误码枚举表：按计划由 Week 1-2 PoC 产出后回填
- 两个技术假设（Hook API 稳定性、Codex/Kimi PTY 合规产出率）：属实验验证范畴
- IMPROVEMENT_SUMMARY 中历史叙事数字（如投票通过概率 33%/89%/75%）出处核查：历史记录性质

## 六、期望产出

按 `MACAO_REVIEW_GUIDELINES.md` 出具 `docs/reviews/<date>-review-result-<commit>-<reviewer>.md`：
逐条给出 文件+行号 证据；若仅余 P2/P3，请宣告 **L1 DOC-ALIGNED / PG-0** 并更新 `reviews/STATUS.md`。
