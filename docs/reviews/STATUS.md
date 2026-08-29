# MACAO 文档与代码门禁状态（Live Status）

> 依据 `docs/MACAO_REVIEW_GUIDELINES.md` 维护；本文件是唯一允许记录实时门禁状态的位置。
> 治理规则（P1-3 确立，已固化）：**每轮申请复审前，STATUS 必须与 `reviews/` 目录全量对账**，不得以 STATUS 登记子集为闭环核验边界。

- **最新更新时间**：2026-08-29（四方独立专家 claude / codex / grok / zcode (qwen) 针对 `ea536ab` 的 4 份独立复审报告全部就位，完成 100% 全量对账）
- **当前申请对象**：[`docs/reviews/2026-08-29-review-request-L3-All-Items-Closed.md`](2026-08-29-review-request-L3-All-Items-Closed.md)
- **当前定级状态**：**维持 L2 SPEC-CODE-ALIGNED / PG-1（未获 L3 / PG-2 准入）**
  - **整改复验共识**：四方专家一致确认申请所列 8 项中 6 项安全/正确性修复（高熵 task_id、max-round 不提前写盘守卫、脏工作区拒绝合并、Worktree 物理清理、vote 写盘前 Schema 校验、非法 human_resolution fail-fast）**全部真实闭环**；49/49 单元测试与 5 轮回归全绿（0 flake）；
  - **专家一致指出的关键残余阻断项（集中于 2 点）**：
    1. **REQ-TIMEOUT / P1-1**：超时弃权未带入 E7 终局 `vote_result.json`（`resolve_override` 时未携带超时 ABSTAIN，导致终局文件中缺少弃权记录与相应 `reviewers_responded` 统计）；同时需完善基于 deadline/timespan 的生产检测机制，并在回归测试中强断言票面。
    2. **P1-2（Artifact 消费与 SHA256 账本闭环）**：`fsm.py:111` 消费归档时因 `Path.stem`（得到 `codex.review` 而非 `codex`）导致 `review_manifest` 的 `consumed` 保持为 0 且 `archived_path` 为 NULL；同时 `register_artifact` 需恢复读盘补齐 `sha256`。
- **历史文档定级**：PRD **v2.3.1**（§3.2 Layer 1c 四值终局分支已单点闭环修复，达到 L1 DOC-ALIGNED / PG-0）
- **当前代码机验**：`PYTHONPATH=src python3 -m unittest discover tests -v` **49 ran / 49 PASS (100%)**；`test-clis`（4/4 PASS）/ `e2e-run`（7 步 OK，5 份物理产物）属实。

---

## 评审申请记录全量对账表 (Review Registry - 43 份历史与当前评审报告 + 7 份申请全量对账)

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
| 2026-08-29 | `2026-08-29-review-request-L3-Final-Rectification.md` | `e7ba2d2` .. `4df059e` | L3 / PG-2 | `2026-08-29-review-result-4df059e-claude.md`<br>`2026-08-29-review-result-4df059e-zcode.md`<br>`2026-08-29-review-result-4df059e-codex.md`<br>`2026-08-29-review-result-4df059e-qwen.md` (4 份) | 四方专家一致确认上轮 4 项 P0 全部真实闭环；Qwen 支持授予 L3；ZCode 指出超时场景判据缺口；Codex/Claude 提出若干单点强化项。 |
| **2026-08-29** | **`2026-08-29-review-request-L3-All-Items-Closed.md`** | **`4df059e` .. `ea536ab`** | **L3 / PG-2** | `2026-08-29-review-result-ea536ab-claude.md`<br>`2026-08-29-review-result-ea536ab-codex.md`<br>`2026-08-29-review-result-ea536ab-grok.md`<br>`2026-08-29-review-result-ea536ab-zcode.md` (4 份全部就位) | **维持 L2 / PG-1（未获 L3/PG-2 准入，差 2 项单点）**<br>1. 申请 8 项中 6 项经四方专家独立复验 100% 确认闭环；<br>2. 专家一致指出最终 2 项单点：终局 vote_result.json 需完整持久化超时 ABSTAIN 票据并提供自动判定支持；修复 `fsm.py` 消费匹配 key 与 `artifacts.sha256` 读盘补齐。 |

---

## 本轮（ea536ab 四方专家复审）精准整改清单

| 编号 | 严重度 | 问题描述与整改要求 | 涉及专家 |
|---|---|---|---|
| **P1-1** | **阻断** | **超时弃权完整持久化至终局 `vote_result.json` & 自动判定机制**：<br>1. `Orchestrator` 派发时记录 deadline，提供自动超时判定；<br>2. 超时产生的 `ABSTAIN` 票据随 `resolve_override` / E7 终局落盘写入 `vote_result.json`（计入 `votes`、`vote_breakdown.abstain`、`reviewers_responded`），符合 PRD §2.2 / §3.3 明文；<br>3. 单元测试强断言票面数据与审计事件。 | 四方专家共同指出 |
| **P1-2** | **阻断** | **`review_manifest` 消费归档 key 修复与 `artifacts.sha256` 读盘补齐**：<br>1. 修复 `src/macao/workflow/fsm.py:111`，改用 `rev_file.name.replace(".review.yml", "")` 准确匹配注册的 `reviewer_id`，确保归档后 `consumed=1` 且 `archived_path` 写入真实路径；<br>2. 修复 `src/macao/storage/store.py:82`，在 `content is None` 时自动读取磁盘文件计算 `sha256`，确保 `artifacts.sha256` 不为空；<br>3. 回归测试中明确断言全部产物 `consumed == 1`、`archived_path is not None`、`sha256 != ""`。 | claude, zcode (qwen), grok, codex |
| **P3-1** | **规范** | **清理 `docs/POC_VERIFICATION_REPORT.md:25` 尾随空白**，确保 `git diff --check` 100% 洁净。 | claude, zcode (qwen) |

---

## 下一步行动

1. 提交更新后的 `STATUS.md` 与 4 份专家评审报告；
2. 针对上述 3 项清单展开代码修改与测试断言补齐，冲刺四方全票通过并获取 L3 / PG-2 认证。
