# MACAO 文档与代码门禁状态（Live Status）

> 依据 `docs/MACAO_REVIEW_GUIDELINES.md` 维护；本文件是唯一允许记录实时门禁状态的位置。
> 治理规则（P1-3 确立，已固化）：**每轮申请复审前，STATUS 必须与 `reviews/` 目录全量对账**，不得以 STATUS 登记子集为闭环核验边界。

- **最新更新时间**：2026-08-29（claude / zcode / codex 针对 `4df059e` 的 3 份独立复审报告已同步就位，完成 100% 全量对账）
- **当前申请对象**：自 `2026-08-29-review-request-L3-Final-Rectification.md` 后的 `message_id` 16 位高熵防碰撞、AEP Schema 与 PRD 10 状态/7 类型对齐、人工裁定 4 选项连通、MergeController CI 失败原子回滚与配置远端 Fail-closed、Mock Adapter 契约消费全生命周期驱动与 43 项自动化测试
- **当前定级状态**：**维持 L2 SPEC-CODE-ALIGNED / PG-1（未获 L3 / PG-2 准入）**
  - **整改复验共识**：三方专家一致确认上一轮（`e7ba2d2`）的 4 项 P0-NEW（`message_id` 碰撞、协议枚举/人工裁定断裂、MergeController CI 原子性、Adapter 契约驱动+Worktree 事务性）**全部真实闭环**；43/43 单元测试与 500 次并发写入 100% 稳定通过；
  - **当前残余阻断项**：
    1. **L3 判据超时场景覆盖缺口**（zcode, codex 共同指出：L3 定级标准必须包含超时降级推演或 fake-clock 单测证据）；
    2. **CI 失败使用 `git reset --hard` 对用户未提交代码的保护**（codex：工作区未提交修改安全）；
    3. **默认 `task_id` 秒级时间戳防并发冲突**（codex：`task_id` 增加高熵后缀）；
    4. **最大返工轮次到达时 vote_result 写盘时机与崩溃恢复一致性**（codex：达到上限 HOLD 时不提前写盘）；
    5. **Worktree 异常清理与 Artifact 注册链路**（claude：`remove_worktree` 调用参数与 `register_artifact` 生产调用链路）。
- **历史文档定级**：PRD **v2.3.1**（§3.2 Layer 1c 四值终局分支已单点闭环修复，达到 L1 DOC-ALIGNED / PG-0）
- **当前代码机验**：`PYTHONPATH=src python3 -m unittest discover tests -v` **43 ran / 43 PASS (100%)**；`test-clis` / `e2e-run` 路径属实。

---

## 评审申请记录全量对账表 (Review Registry - 38 份历史与当前评审报告 + 6 份申请全量对账)

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
| 2026-08-28 | `2026-08-28-review-request-Phase1-Phase2-Integration.md` | `aa173d8` .. `906b17e` | L3 / PG-2 | `2026-08-28-review-result-906b17e-zcode.md`<br>`2026-08-28-review-result-906b17e-claude.md`<br>`2026-08-28-review-result-906b17e-codex.md`<br>`2026-08-28-review-result-906b17e-integration-qwen.md` (4 份) | 四方专家一致判定：未达 L3，维持 L2/PG-1；提出 11 项整改项；已在 e7ba2d2 中闭环修复。 |
| 2026-08-29 | `2026-08-29-review-request-Phase1-Phase2-Rectification.md` | `906b17e` .. `e7ba2d2` | L3 / PG-2 | `2026-08-29-review-result-e7ba2d2-claude.md`<br>`2026-08-29-review-result-e7ba2d2-rectification-qwen.md`<br>`2026-08-29-review-result-e7ba2d2-zcode.md`<br>`2026-08-29-review-result-e7ba2d2-codex.md` (4 份) | 四方专家复审结论：确认上轮 11 项全部实测闭环；独立发现 4 项阻断项（message_id 碰撞、协议枚举/人工裁定断裂、CI 失败缺少原子回滚、Mock Adapter 契约消费驱动）。 |
| **2026-08-29** | **`2026-08-29-review-request-L3-Final-Rectification.md`** | **`e7ba2d2` .. `4df059e`** | **L3 / PG-2** | `2026-08-29-review-result-4df059e-claude.md`<br>`2026-08-29-review-result-4df059e-zcode.md`<br>`2026-08-29-review-result-4df059e-codex.md` (3 份已就位) | **维持 L2 / PG-1（未获 L3/PG-2 准入）**<br>1. 申请 4 项 P0 全部独立复验真实关闭；<br>2. 专家指出残余阻断项：补齐超时场景测试证据、task_id 增加高熵防并发冲突、max-round 达到上限时 HOLD 不提前写盘、Merge 工作区未提交修改安全防护、Worktree 异常清理补齐方法。 |

---

## 本轮（4df059e 复审）待整改与补齐清单

| 编号 | 严重度 | 问题描述与整改要求 | 涉及专家 |
|---|---|---|---|
| **REQ-TIMEOUT** | 阻断 | **L3 判据超时场景测试证据**：提供基于时钟机制或 fake-clock 的单元测试，覆盖 Reviewer 超时未响应 → 标记弃权 → 仲裁死锁/人工接管的全链路。 | zcode, codex |
| **P0-1** | 阻断 | **`task_id` 秒级时间戳防同秒并发冲突**：`start_task` 生成的 `task_id` 应增加 UUID/高熵随机后缀，防止并发调用触发 SQLite 主键唯一约束冲突。 | codex |
| **P0-2** | 阻断 | **最大返工轮次达到上限时 HOLD 且不提前写盘**：达到 `max_rework_rounds` 时不应生成并落盘 `REWORK_REQUIRED` 的 `vote_result.json`，防止崩溃恢复时直接判定返工而绕过人工裁定。 | codex |
| **P1-1** | 重要 | **Worktree 异常清理调用与路径匹配**：在 `GitManager` 中提供 `remove_isolated_worktree` 或按 Path 正确调用 `remove_worktree`，避免异常时遗留孤儿 worktree。 | claude |
| **P1-2** | 重要 | **恢复 `register_artifact` 在生产流程中的调用点**：在 `check_development_checkpoint` 中恢复产物追踪注册，确保 `artifacts` 数据库表正常记录。 | claude |
| **P2-1** | 建议 | **`consensus/vote.py` 恢复先校验后写盘顺序**：Schema 校验应在落盘前执行，确保无效数据绝不落盘。 | zcode |
| **P2-2** | 建议 | **`human_resolution` 非法输入 Fail-fast 校验**：未知输入不应静默降级为 APPROVED，应抛出异常。 | zcode |

---

## 下一步行动

1. 提交更新后的 `STATUS.md` 与已同步的复审报告；
2. 针对上述清单开展单点整改与超时测试补齐。
