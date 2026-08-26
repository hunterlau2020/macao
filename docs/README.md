# MACAO 文档索引

> 权威基准：[`MACAO_PRD_v2.md`](MACAO_PRD_v2.md)（当前 v2.3）。文档间不一致时以 PRD 为准。

## 核心文档（建议阅读顺序）

| # | 文档 | 定位 |
|---|------|------|
| 1 | [`EXECUTIVE_SUMMARY.md`](EXECUTIVE_SUMMARY.md) | 执行摘要与快速参考，最快了解全貌 |
| 2 | [`MACAO_PRD_v2.md`](MACAO_PRD_v2.md) | **权威基准**：流程/产物协议/状态机/架构/配置/用户旅程/边界（第一～十六部分） |
| 3 | [`TECH_INTRUDUCE.md`](TECH_INTRUDUCE.md) | **技术架构与实现说明**：技术选型、组件落地矩阵、CLI 交互设计与模块全景 |
| 4 | [`PLAN.md`](PLAN.md) | **技术开发计划**：8 周 MVP 迭代任务分解、里程碑（M0~M3）与交付验收标准 |
| 5 | [`ROADMAP.md`](ROADMAP.md) | **技术路线图**：8 周 MVP 与未来演进路线（v1.1 ~ v2.0） |
| 6 | [`IMPROVEMENT_SUMMARY.md`](IMPROVEMENT_SUMMARY.md) | v1.0 → v2.x 改进对比与版本演进说明 |
| 7 | [`SRSv1.md`](SRSv1.md) | v1.0 历史基线（暂定名 "A"），**仅供追溯，不得用于实现** |

## 规范与治理

| 路径 | 内容 |
|------|------|
| [`schemas/`](schemas/) | 版本化 JSON Schema（三类产物 / AEP 信封 / review_context / macao.yaml）+ 正反 fixtures，Adapter Conformance 的校验输入 |
| [`reviews/`](reviews/) | 各 commit 的独立评审结论；[`reviews/STATUS.md`](reviews/STATUS.md) 为唯一实时门禁状态 |
| [`MACAO_REVIEW_GUIDELINES.md`](MACAO_REVIEW_GUIDELINES.md) | 评审方法论（L1~L4 / PG-0~PG-3 门禁、证据规则） |
| [`EXPERT_QUALITY.md`](EXPERT_QUALITY.md) | 评审专家质量评估报告（评分卡 / 角度重合度 / 排班建议），用于后续评审排班 |

## 快速导航（PRD 常用章节）

- 工作流 FSM 与统一转移表：§3.3（权威，10 态含 MERGING/CANCELLED；§1.1/§1.2 为简化视图，以 §3.3 为准）
- 三类产物契约与共识规则：第二部分 / §2.3 决策表
- 状态识别作用域读取与场景推演：§3.2 / §3.4
- Reviewer Context 与工作流：第五部分
- 系统架构 / State Store DDL / 恢复算法：第十一部分
- Adapter Contract 与执行权限边界：第十二部分
- 配置规范 `macao.yaml`：第十三部分
- 用户旅程 / 运维 / Merge Policy：第十四部分
- 边界声明（串行、安全、成本、评审质量评测）：第十五部分
- 部署形态（单机同置 / 跨机分布）：第十六部分
