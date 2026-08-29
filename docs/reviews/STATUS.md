# MACAO 文档与代码门禁状态（Live Status）

> 依据 `docs/MACAO_REVIEW_GUIDELINES.md` 维护；本文件是唯一允许记录实时门禁状态的位置。
> 治理规则（P1-3 确立，已固化）：**每轮申请复审前，STATUS 必须与 `reviews/` 目录全量对账**，不得以 STATUS 登记子集为闭环核验边界。

- **最新更新时间**：2026-08-29（已全量闭环 `f41b9da` 专家评审意见，并完成基于六大专家模型的全局深度自查与加固；全量对账 100% 一致）
- **当前申请对象**：[`docs/reviews/2026-08-29-review-request-L3-Final-Certification.md`](2026-08-29-review-request-L3-Final-Certification.md)（最新认证申请）
- **当前定级状态**：**已完成 P1-NEW-5 / P1-NEW-6 / P1-NEW-7 / GOV-1 全量闭环与 6 项深度自查强化（待专家委员会复验授予定级）**
  - **整改与加固完成情况**：
    - **P1-NEW-5 闭环**：`MergeController.execute_merge_pipeline` 中签字校验不仅采用定向 SQL 查询，而且强绑定 `checkpoint_ref`（`detail.checkpoint_ref == task.checkpoint_ref`），彻底杜绝第 1 轮签字误放行第 2 轮返工代码，完全对齐 PRD §3.3 E4a 与 §14.5；
    - **P1-NEW-6 闭环**：`resolve_override(RETRY_REVIEW)`（E9）执行完整的重试语义：清空 `.macao/.reviews/` 活跃目录旧票、重新派发带全新 deadline 的 `REVIEW_REQUEST` 并记录 `REVIEW_REQUESTS_DISPATCHED` 审计，彻底消除超时活锁；
    - **P1-NEW-7 / P1-Q2 闭环**：在 `collect_and_evaluate_consensus` 与 `generate_vote_result` 中建立**持久化超时处置（Timeout Disposition）**：一旦 reviewer 被判定超时弃权（审计已落库），后续即便补交迟到 manifest 也一律被隔离，绝不参与自动共识评估，持久化维持 HOLD 于 `CONSENSUS_CHECK` 并要求人工接管，终局 `vote_result.json` 保持 ABSTAIN；
    - **P2-NEW-2 闭环**：`resolve_override` 先行校验状态机转移合法性，非法转移直接抛出异常，绝不残留孤儿 `vote_result.json` 产物；
    - **GOV-1 闭环**：注册表历史文件归属勘误完毕（`2026-08-29-review-result-ea536ab-qwen.md` 与 `2026-08-29-review-result-f41b9da-qwen.md` 正确对齐 Qwen 署名）；
    - **全局自查深度加固**：统一 Adapter/PTY 接口签名与抽象（`cancel` / `get_logs` 消除 `TypeError`）、Schema 四级动态寻址机制、Task ID 32-bit 高熵与 5 次并发重试自愈、产物归档 `mark_artifact_consumed` 自动补齐 64 位 `sha256`、`GitManager.is_git_repository` 显式守卫、`docs/EXPERT_QUALITY.md` 专家模型与自查十律沉淀。
  - **测试机验结果**：`PYTHONPATH=src python3 -m unittest discover tests -v` **58 ran / 58 PASS (100%)**；5 轮连续回归（290 次用例执行）0 flake / 0 碰撞 / 0 崩溃；`macao test-clis`（4/4 PASS）/ `macao e2e-run`（7 步 OK，5 份物理产物与数据库记录完全匹配：全 `consumed=1`、全 `sha256` 64 位非空）实测属实；`git diff --check` 100% 洁净，返回码 0。
- **历史文档定级**：PRD **v2.3.1**（§3.2 Layer 1c 四值终局分支已单点闭环修复，达到 L1 DOC-ALIGNED / PG-0）

---

## 评审申请记录全量对账表 (Review Registry - 47 份历史与当前评审报告 + 10 份申请全量对账)

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
| 2026-08-29 | `2026-08-29-review-request-L3-All-Items-Closed.md` | `4df059e` .. `ea536ab` | L3 / PG-2 | `2026-08-29-review-result-ea536ab-claude.md`<br>`2026-08-29-review-result-ea536ab-codex.md`<br>`2026-08-29-review-result-ea536ab-grok.md`<br>`2026-08-29-review-result-ea536ab-qwen.md` (4 份) | 四方专家一致确认 6 项安全修复全部闭环；指出终局 vote_result.json 需完整持久化超时 ABSTAIN 票据并提供自动判定支持；修复 `fsm.py` 消费匹配 key 与 `artifacts.sha256` 读盘补齐。 |
| 2026-08-29 | `2026-08-29-review-request-L3-Final-Closed.md` | `ea536ab` .. `7935da3` | L3 / PG-2 | `2026-08-29-review-result-7935da3-claude.md`<br>`2026-08-29-review-result-7935da3-codex.md`<br>`2026-08-29-review-result-7935da3-kimi.md`<br>`2026-08-29-review-result-7935da3-qwen.md` (4 份) | 四方专家复审结论：确认 P1-2 完全闭环；独立指出 P1-NEW-3（3 Reviewer 超时直接自动合并漏洞）与 P1-NEW-4（审计 limit=50 窗口截断问题）；Qwen 支持定级但提注册表勘误。已在 f41b9da 中全部闭环。 |
| 2026-08-29 | `2026-08-29-review-request-L3-Final-Seal.md` | `7935da3` .. `f41b9da` | L3 / PG-2 | `2026-08-29-review-result-f41b9da-claude.md`<br>`2026-08-29-review-result-f41b9da-codex.md`<br>`2026-08-29-review-result-f41b9da-grok.md`<br>`2026-08-29-review-result-f41b9da-qwen.md` (4 份) | Grok 支持授予 L3/PG-2；Claude / Qwen / Codex 复核确认 P1-NEW-3/4 属实闭环，独立提出 P1-NEW-5（签字绑定 checkpoint）、P1-NEW-6（RETRY_REVIEW 重试活锁）与 P1-NEW-7/P1-Q2（迟到票绕过接管）。已全部在最新提交中闭环修复。 |
| 2026-08-29 | `2026-08-29-review-request-L3-Final-Certification.md` | `f41b9da` .. `HEAD` | L3 / PG-2 | 待专家评审（Claude, Codex, Qwen, Grok, Kimi） | 已全量闭环 P1-NEW-5/6/7 与 GOV-1，并完成 Adapter/Schema/TaskID/SHA256 六大维度深度自查加固；58 项测试 100% 通过。 |

---

## 下一步行动

等待专家委员会（Claude / Codex / Qwen / Grok / Kimi）基于 `2026-08-29-review-request-L3-Final-Certification.md` 开展终局复验并授予定级认证。
