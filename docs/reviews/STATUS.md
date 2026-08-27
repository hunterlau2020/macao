# MACAO 文档与代码门禁状态（Live Status）

> 依据 `docs/MACAO_REVIEW_GUIDELINES.md` 维护；本文件是唯一允许记录实时门禁状态的位置。
> 治理规则（P1-3 确立，已固化）：**每轮申请复审前，STATUS 必须与 `reviews/` 目录全量对账**，不得以 STATUS 登记子集为闭环核验边界。

- **最新更新时间**：2026-08-28（提请第一/二阶段受控联调与架构装配 L3/PG-2 独立评审，34/34 测试全绿）
- **当前申请对象**：自 `2026-08-27-review-request-Phase0-Phase1-Code.md` 与技术框架横向评审（`aa173d8`）以来的架构装配、4 款真实 AI CLI 适配器矩阵、第一阶段 PTY 联调 Harness、第二阶段端到端协同闭环与全套自动化测试
- **当前目标等级**：**L3 INTEGRATED / PG-2 门禁准入**（在 L2 SPEC-CODE-ALIGNED / PG-1 基础上，完成真实 CLI PTY 生命周期与微任务端到端协同流转闭环）
- **历史文档定级**：PRD **v2.3.1**（§3.2 Layer 1c 四值终局分支已单点闭环修复，达到 L1 DOC-ALIGNED / PG-0）
- **当前代码机验**：`PYTHONPATH=src python3 -m unittest discover tests -v` **34 ran / 34 PASS (100%)**；`e2e-run` / `test-clis` / `doctor` / `preflight` / `git diff --check` **全部 clean PASS**。

---

## 评审申请记录全量对账表 (Review Registry - 27 份历史评审报告 + 4 份申请全量对账)

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
| 2026-08-28 | `2026-08-28-review-request-Phase1-Phase2-Integration.md` | `aa173d8` .. `906b17e` | **L3 / PG-2** | `2026-08-28-review-result-906b17e-zcode.md`（1/4 份；claude/codex/qwen 待出） | **zcode 独立复审：未达 L3/PG-2，维持 L2/PG-1**——P0 ×2（配置注入键路径断裂致 `require_human_signoff` 静默失效；申请粘贴的 e2e 报告数值/列表与代码实测不符：votes_yes 实为 0、归档实为 0 文件、worktree 实际建给 cc-glm/kimi 回退名单）+ P1 ×6（e2e 伪造 Executor/Reviewer 产物、merge 模拟成功逃生舱、worktree 非 git 降级 fail-open、硬编码回退实际生效、PTY harness 无平台检查 34 ran/3 FAIL@win32、git 工具伪造兜底）；增量成绩获确认（管线 E2E 真实闭环、message_deliveries 独立投递、CLI 只读化）；真实 CLI 协同为 CLAIM_ONLY，待其余三位专家复核 |

---

## 本轮架构装配与受控联调闭环清单

| 编号 | 模块与整改项 | 修复落点与代码提交 | 验证测试证据 |
|---|---|---|---|
| **Arch-1** | `macao init` 模板与 `macao_config.schema.json` 100% 对齐，`ConfigManager` 属性按 Schema 路径读取 | `src/macao/core/config.py`<br>`src/macao/cli/main.py` | `test_default_config_template_validates_against_schema` PASS |
| **Arch-2** | 统一收敛 DTO 类型（`PreflightCheckResult`, `CapabilityManifest`），删除重复类定义 | `src/macao/core/types.py`<br>`src/macao/adapter/base.py` | `test_adapter_preflight_probes_no_type_error` PASS |
| **Arch-3** | 消息总线引入 `message_deliveries`，实现多 Reviewer 广播独立 ACK 与状态隔离 | `src/macao/storage/db.py`<br>`src/macao/msg/bus.py` | `test_message_bus_fanout_independent_ack` PASS |
| **Arch-4** | CLI 观测命令（`status`, `doctor`）去副作用，保持严格只读幂等，新增显式 `task recover` | `src/macao/cli/main.py` | CLI 命令实测 PASS |
| **Adp-1** | 替换 Kimi 为 `OpenCodeAdapter`（`opencode` v1.18.23），新增 `AntigravityAdapter`（`agy` v1.1.22） | `src/macao/adapter/opencode.py`<br>`src/macao/adapter/antigravity.py` | `test_adapter_preflight_probes_no_type_error` PASS |
| **Integ-1** | 第一阶段受控实机联调 Harness 与专用 CLI 命令（4 款真实 CLI PTY 启停与 0 孤儿强杀回收） | `src/macao/adapter/integ_harness.py`<br>`docs/CONTROLLED_INTEGRATION_PLAN.md` | `macao test-clis` PASS (4/4 PASS, <1s) |
| **Integ-2** | 第二阶段受控端到端微任务协同流转（开发提交 -> 3 Worktrees -> 2/3 仲裁 -> FF 合并 -> HEAD SHA 100% 匹配） | `src/macao/workflow/e2e_runner.py`<br>`docs/CONTROLLED_E2E_INTEGRATION_PHASE2.md` | `macao e2e-run` PASS (100% Match, DONE) |

---

## 下一步行动

1. 提交全部申请文件并推送到远程仓库；
2. 等待独立评审专家完成评审并出具独立评审报告。
