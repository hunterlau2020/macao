# MACAO 文档与代码门禁状态（Live Status）

> 依据 `docs/MACAO_REVIEW_GUIDELINES.md` 维护；本文件是唯一允许记录实时门禁状态的位置。
> 治理规则（P1-3 确立，已固化）：**每轮申请复审前，STATUS 必须与 `reviews/` 目录全量对账**，不得以 STATUS 登记子集为闭环核验边界。

- **最新更新时间**：2026-08-30（已全量闭环 `bf5ae2d` 专家评审意见：P1-NEW-8 / P1-Q3 / P1-1 超时处置代际解绑与 E9 重试全流程自愈、P2-CARRY-1 ANSI 真实转义校验、Schema 环境变量单测真实覆盖、GOV-1 注册表全量勘误；全量对账 100% 一致）
- **当前申请对象**：[`docs/reviews/2026-08-30-review-request-L3-Final-Seal.md`](2026-08-30-review-request-L3-Final-Seal.md)（最新认证申请）
- **当前定级状态**：**已完成 P1-NEW-8 / P1-Q3 / P1-1 全量闭环整改（待专家委员会复验授予定级）**
  - **整改与加固完成情况**：
    - **P1-NEW-8 / P1-Q3 / P1-1 闭环**：`collect_and_evaluate_consensus` 与 `resolve_override` 中，超时处置严格绑定当前轮次的最新派发代际（`sequence_id >= latest_dispatch_seq`）。当管理员执行 `RETRY_REVIEW` 时，新派发生成的 `sequence_id` 自动使上一代际的超时记录失效，重试窗口内如期提交的新票正常计入共识并自动推进至 `MERGING`（`resolution=automatic`），彻底根除 E9 重试活锁；
    - **P2-CARRY-1 闭环**：`integ_harness.py` 引入 `ANSI_ESCAPE_RE`，对捕获的 `clean_logs` 进行真实逐行扫描检测，确保 0 残留 ANSI 控制符；
    - **Schema 单测覆盖闭环**：`test_config.py` 中补充了使用临时目录真实设置 `MACAO_SCHEMAS_DIR` 并验证优先级的单测；
    - **GOV-1 闭环**：`2026-08-29-review-result-bf5ae2d-zcode.md` 正式更名为 `2026-08-29-review-result-bf5ae2d-qwen.md`，台账总数修正为 55 份结果 + 11 份申请。
  - **测试机验结果**：`PYTHONPATH=src python3 -m unittest discover tests -v` **60 ran / 60 PASS (100%)**；5 轮连续全量高压回归（300 次用例执行）0 flake / 0 碰撞 / 0 崩溃；`macao test-clis`（4/4 PASS，0 僵尸）/ `macao e2e-run`（7 步 OK，5 份物理产物与数据库记录完全匹配：全 `consumed=1`、全 `sha256` 64 位非空）实测属实；`git diff --check` 100% 洁净，返回码 0。
- **历史文档定级**：PRD **v2.3.1**（§3.2 Layer 1c 四值终局分支已单点闭环修复，达到 L1 DOC-ALIGNED / PG-0）

---

## 评审申请记录全量对账表 (Review Registry - 55 份历史与当前评审报告 + 11 份申请全量对账)

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
| 2026-08-29 | `2026-08-29-review-request-L3-Final-Seal.md` | `7935da3` .. `f41b9da` | L3 / PG-2 | `2026-08-29-review-result-f41b9da-claude.md`<br>`2026-08-29-review-result-f41b9da-codex.md`<br>`2026-08-29-review-result-f41b9da-grok.md`<br>`2026-08-29-review-result-f41b9da-qwen.md` (4 份) | Grok 支持授予 L3/PG-2；Claude / Qwen / Codex 复核确认 P1-NEW-3/4 属实闭环，独立提出 P1-NEW-5（签字绑定 checkpoint）、P1-NEW-6（RETRY_REVIEW 重试活锁）与 P1-NEW-7/P1-Q2（迟到票绕过接管）。已全部闭环修复。 |
| 2026-08-29 | `2026-08-29-review-request-L3-Final-Certification.md` | `f41b9da` .. `bf5ae2d` | L3 / PG-2 | `2026-08-29-review-result-bf5ae2d-claude.md`<br>`2026-08-29-review-result-bf5ae2d-qwen.md`<br>`2026-08-29-review-result-bf5ae2d-grok.md`<br>`2026-08-30-review-result-bf5ae2d-codex.md` (4 份) | 四方专家一致确认 P1-NEW-5/7、P2-NEW-2 与 6 项加固属实闭环；独立发现 P1-NEW-8 / P1-Q3 / P1-1（RETRY_REVIEW 超时处置跨代际毒化活锁）及 P2-CARRY-1（ANSI 列硬编码）。已在当前提交中闭环修复。 |
| 2026-08-30 | `2026-08-30-review-request-L3-Final-Seal.md` | `99526aa` .. `HEAD` | L3 / PG-2 | 待专家评审（Claude, Codex, Qwen, Grok, Kimi） | 已闭环 P1-NEW-8 / P1-Q3 / P1-1 超时处置代际解绑与 E9 重试全流程自愈，修复 ANSI 真实转义校验；60 项测试 100% 通过。 |

---

## 下一步行动

等待专家委员会（Claude / Codex / Qwen / Grok / Kimi）基于 `2026-08-30-review-request-L3-Final-Seal.md` 开展终局复验并授予定级认证。
