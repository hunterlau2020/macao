# MACAO 文档门禁状态（Live Status）

> 依据 `docs/MACAO_REVIEW_GUIDELINES.md` 维护；本文件是唯一允许记录实时门禁状态的位置。

- 更新时间：2026-08-26
- 最近复审：`reviews/2026-08-26-review-result-47f54f2-codex.md`（结论 PARTIALLY_VERIFIED，未达 L1 DOC-ALIGNED / PG-0）
- 当前等级：**PG-0**（允许 PoC 探索；暂不可作为可直接实现的完整规格）

## 针对 47f54f2 复审发现的处理状态

| 编号 | 发现 | 状态 | 处理位置 |
|------|------|------|---------|
| P0-1 | 固定顺序读文件导致持久 `.dev.yml` 遮蔽后续产物 | 已修订，待复审确认 | PRD §3.2（状态作用域读取）、§3.3（命令+产物统一转移表）、§3.4（生命周期与场景推演） |
| P0-2 | `code_changes` 扁平/嵌套路径分叉 + 缺工作区定位契约 | 已修订，待复审确认 | PRD §2.4（`code_changes.refs.*` 唯一路径 + `repository` 块）、§5.3、第十三部分（macao.yaml 解析源） |
| P1-1 | §1.2 阶段表 CHECKPOINT 顺序倒置、"所有收集完毕"残留 | 已修订 | PRD §1.2 |
| P1-2 | 产物缺 `review_round` / SHA-256 / message_id 字段 | 已修订 | PRD §2.1/§2.2/§2.3 |
| P1-3 | Layer 3 图示与伪代码的接管触发条件不一致 | 已修订 | PRD §3.1 |
| P1-4 | 本文件缺失 + GUIDELINES 引用不可达路径 | 已修订 | `MACAO_REVIEW_GUIDELINES.md` 头部与本文件 |
| P1-5 | SRSv1 伪 JSON 示例不可解析 | 已修订（改为 text 标注） | `SRSv1.md` |

## 下一步

1. 四场景 SIM 复核（首次双批准 / 1:1 僵局 / 一人超时弃权 / 返工第二轮），每步须唯一命中 PRD §3.3 转移表；
2. 提交 `REVIEW_REQUEST` 可解析 fixture，验证 §5.3 jq 路径端到端可读出 refs 与仓库定位；
3. 以上通过后申请 L1 DOC-ALIGNED 复审。
