# MACAO 文档与代码门禁状态（Live Status）

> 依据 `docs/MACAO_REVIEW_GUIDELINES.md` 维护；本文件是唯一允许记录实时门禁状态的位置。
> 治理规则（P1-3 确立，已固化）：**每轮申请复审前，STATUS 必须与 `reviews/` 目录全量对账**，不得以 STATUS 登记子集为闭环核验边界。

- **最新更新时间**：2026-08-29（四方独立专家 claude / qwen / zcode / codex 针对 `e7ba2d2` 评审报告全部同步就位，完成 100% 全量对账）
- **当前申请对象**：自 `2026-08-28-review-request-Phase1-Phase2-Integration.md` 后的配置穿透修复、Adapter 真实注入、Fail-closed 合并与 Worktree 门禁、归档物理路径修正与全量自动化测试
- **当前定级状态**：**维持 L2 SPEC-CODE-ALIGNED / PG-1（未获 L3 / PG-2 准入）**
  - **正面进展**：四方专家一致确认上一轮（`906b17e`）的 11 项 P0/P1/P2 整改**全部真实闭环**（配置展平穿透、Fail-closed 守卫、归档 5 份合法产物、4 款 CLI PTY 探针）；
  - **阻断问题**：多位专家独立发现本轮新增/残留阻断问题（`message_id` 随机碰撞致 SQLite 主键冲突、AEP 类型与 Schema/PRD 偏移致人工裁定断裂、MergeController 缺少 CI 失败前置原子性、Mock Adapter 消息消费闭环）。
- **历史文档定级**：PRD **v2.3.1**（§3.2 Layer 1c 四值终局分支已单点闭环修复，达到 L1 DOC-ALIGNED / PG-0）
- **当前代码机验**：`PYTHONPATH=src python3 -m unittest discover tests -v`（38 测试在 `message_id` 碰撞修复前存在约 20%~25% 偶发主键冲突失败率）；`test-clis` / `e2e-run` 路径属实。

---

## 评审申请记录全量对账表 (Review Registry - 35 份历史与当前评审报告 + 5 份申请全量对账)

| 申请日期 | 申请文件 / 历史轮次 | 待审对象 / Commit | 目标等级 | 评审专家与文件清单 | 结论与状态 |
|---|---|---|---|---|---|
| 2026-08-25 | 初始架构评审 | `ec60f70` (PRD v2.1) | L1 | `2026-08-25-review-result-ec60f70-claude.md`<br>`2026-08-25-review-result-ec60f70-codex.md`<br>`2026-08-25-review-result-ec60f70-gemini.md` (3 份) | 未通过（发现状态机与共识分歧） |
| 2026-08-26 | 历史迭代轮 1 | `47f54f2` (PRD v2.2) | L1 | `2026-08-26-review-result-47f54f2-codex.md` (1 份) | 历史追踪（指出沙箱与存储边界） |
| 2026-08-26 | 历史迭代轮 2 | `684a012` (PRD v2.2.1) | L1 | `2026-08-26-review-result-684a012-claude.md`<br>`2026-08-26-review-result-684a012-codex.md`<br>`2026-08-26-review-result-684a012-gemini.md` (3 份) | 历史追踪（收敛 AEP 信封与 Schema） |
| 2026-08-26 | 历史迭代轮 3 | `8ab9be7` (PRD v2.2.2) | L1 | `2026-08-26-review-result-8ab9be7-claude.md`<br>`2026-08-26-review-result-8ab9be7-codex.md`<br>`2026-08-26-review-result-8ab9be7-gemini.md`<br>`2026-08-26-review-result-8ab9be7-kimi.md`<br>`2026-08-26-review-result-8ab9be7-opencode.md` (5 份) | 历史追踪（确立并集方案 B 与死锁 HOLD） |
| 2026-08-26 | `2026-08-26-review-request-PRD-v2.3.md` | `cc77a94` (PRD v2.3) | L1 | `2026-08-26-review-result-cc77a94-claude.md`<br>`2026-08-26-review-result-cc77a94-codex.md`<br>`2026-08-26-review-result-cc77a94-gemini.md`<br>`2026-08-26-review-result-cc77a94-kimi.md`<br>`2026-08-26-review-result-PRD-v2.3-opencode.md` (5 份) | 未通过（提出 2 P0 + 3 P1 修订项） |
| 2026-08-26 | `2026-08-26-review-request-PRD-v2.3.1.md` | `403ddc7` (PRD v2.3.1) | L1 / PG-0 | `2026-08-26-review-result-403ddc7-claude.md`<br>`2026-08-27-review-result-403ddc7-codex.md`<br>`2026-08-27-review-result-403ddc7-zcode.md` (3 份) | 上轮 2 P0 + 3 P1 全部 VERIFIED；新增 P1（§3.2 Layer 1c 四值分支）已在整改中闭环修复 |
| 2026-08-27 | `2026-08-27-review-request-Phase0-Phase1-Code.md` | `d137a05` .. `435eeea` | L2 / PG-1 | `2026-08-27-review-result-435eeea-claude.md`<br>`2026-08-27-review-result-435eeea-codex.md`<br>`2026-08-27-review-result-435eeea-zcode.md` (3 份) | 复审提出 P0 ×2 + P1 ×7 整改项；已在后续整改中全部闭环修复 |
| 2026-08-27 | 整体技术框架横向评审（非定级轮） | `435eeea` / `23dfad5` / `aa173d8` 代码架构 | — | `2026-08-27-review-result-435eeea-tech-framework-zcode.md`<br>`2026-08-27-review-result-23dfad5-tech-framework-claude.md`<br>`2026-08-27-review-result-23dfad5-codex-framework.md`<br>`2026-08-27-review-result-aa173d8-tech-framework-qwen.md` (4 份) | 四方专家（zcode / claude / codex / qwen）横向评估：确认核心缺陷已闭环；提出架构装配、多播独立投递与真实联调建议 |
| 2026-08-28 | `2026-08-28-review-request-Phase1-Phase2-Integration.md` | `aa173d8` .. `906b17e` | L3 / PG-2 | `2026-08-28-review-result-906b17e-zcode.md`<br>`2026-08-28-review-result-906b17e-claude.md`<br>`2026-08-28-review-result-906b17e-codex.md`<br>`2026-08-28-review-result-906b17e-integration-qwen.md` (4 份) | **四方专家一致判定：未达 L3 SCENARIO-VERIFIED / PG-2，维持 L2/PG-1**；提出 P0×3 + P1×6 整改项；已在 e7ba2d2 中闭环修复。 |
| **2026-08-29** | **`2026-08-29-review-request-Phase1-Phase2-Rectification.md`** | **`906b17e` .. `e7ba2d2`** | **L3 / PG-2** | `2026-08-29-review-result-e7ba2d2-claude.md`<br>`2026-08-29-review-result-e7ba2d2-rectification-qwen.md`<br>`2026-08-29-review-result-e7ba2d2-zcode.md`<br>`2026-08-29-review-result-e7ba2d2-codex.md` (4 份全部提交) | **四方专家复审结论：维持 L2 SPEC-CODE-ALIGNED / PG-1，未批准 L3/PG-2**<br>1. 上轮 11 项整改全部实测闭环；<br>2. 新增阻断项：`message_id` 短 uuid 碰撞崩溃、AEP 类型/枚举与 PRD/Schema 错配致人工裁定断裂、MergeController CI 失败缺少前置隔离与配置远端检查、Mock Adapter 契约消费闭环。待新一轮单点闭环整改。 |

---

## 本轮（e7ba2d2 四方专家复审）新增待整改问题汇总清单

| 编号 | 严重度 | 问题描述与整改要求 | 涉及专家 |
|---|---|---|---|
| **P0-NEW-1** | 阻断 | **`AEPEnvelope.generate_message_id()` 短 UUID 高频碰撞**：仅取 4 位十进制后缀导致同日仅 ~10,000 空间，连续生成极易触发 SQLite 主键冲突崩溃。要求使用完整 UUID4 或高熵十六进制字符串，并增加高频发布无碰撞测试。 | claude, zcode, codex |
| **P0-NEW-2** | 阻断 | **协议枚举/Schema/PRD 错配与人工裁定不可用**：`types.py` 状态机与 AEP 类型未对齐 PRD/Schema；`OverrideChoice` 枚举值变更导致 CLI `resolve_override()` 抛出 `ValueError`。要求以 PRD/Schema 为权威单一真理源对齐，并增加 4 种人工裁定端到端测试。 | codex |
| **P0-NEW-3** | 阻断 | **MergeController CI 门禁失败未隔离与远端检查**：`MergeController` 先合并目标分支再运行 CI，CI 失败时目标分支已污染前移；配置了 `remote_name` 但远端不存在时静默跳过。要求 CI 前置于隔离环境运行、配置 remote 必严格校验、失败时原子恢复。 | codex |
| **P0-NEW-4** | 阻断 | **Mock Adapter 契约消费驱动与超时场景**：Phase 2 协同需通过 Adapter 的 `start/inject/produce/ack/stop` 契约方法驱动，补齐超时检测。 | codex, zcode |

---

## 下一步行动

1. 完成 `docs/reviews/STATUS.md` 与 35 份评审报告 + 5 份申请的全量对账提交；
2. 针对 `P0-NEW-1` ~ `P0-NEW-4` 开展精准单点整改与自动化测试验证。
