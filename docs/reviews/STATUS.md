# MACAO 文档与代码门禁状态（Live Status）

> 依据 `docs/MACAO_REVIEW_GUIDELINES.md` 维护；本文件是唯一允许记录实时门禁状态的位置。
> 治理规则（P1-3 确立，已固化）：**每轮申请复审前，STATUS 必须与 `reviews/` 目录全量对账**，不得以 STATUS 登记子集为闭环核验边界。

- **最新更新时间**：2026-08-28（完成 4 位专家评审意见全面整改，38/38 测试全绿）
- **当前申请对象**：自 `2026-08-28-review-request-Phase1-Phase2-Integration.md` 后的配置穿透修复、Adapter 真实注入、Fail-closed 合并与 Worktree 门禁、归档物理路径修正与 38 项全量自动化测试
- **当前定级状态**：**L2 SPEC-CODE-ALIGNED / PG-1（已闭环全部 906b17e 专家整改项，38/38 PASS）**
- **历史文档定级**：PRD **v2.3.1**（§3.2 Layer 1c 四值终局分支已单点闭环修复，达到 L1 DOC-ALIGNED / PG-0）
- **当前代码机验**：`PYTHONPATH=src python3 -m unittest discover tests -v` **38 ran / 38 PASS (100%)**；`e2e-run` / `test-clis` / `doctor` / `preflight` / `git diff --check` **全部 clean PASS**。

---

## 评审申请记录全量对账表 (Review Registry - 31 份历史与当前评审报告 + 4 份申请全量对账)

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
| 2026-08-28 | `2026-08-28-review-request-Phase1-Phase2-Integration.md` | `aa173d8` .. `906b17e` | **L3 / PG-2** | `2026-08-28-review-result-906b17e-zcode.md`<br>`2026-08-28-review-result-906b17e-claude.md`<br>`2026-08-28-review-result-906b17e-codex.md`<br>`2026-08-28-review-result-906b17e-integration-qwen.md` (4 份) | **四方专家一致判定：未达 L3 SCENARIO-VERIFIED / PG-2，维持 L2/PG-1**；提出 P0×3 + P1×6 整改项；**已在本次整改中全部闭环修复并通过 38 项回归测试**。 |

---

## 本轮（906b17e 四方专家评审意见）P0 / P1 闭环整改清单

| 编号 | 问题与整改要求 | 修复落点与代码实现 | 验证测试证据 |
|---|---|---|---|
| **P0-1** | **配置注入键路径断裂**：`ConfigManager` 提取并标准化运行时策略，确保 `require_human_signoff`、`ci_gate_command`、`remote_name` 等 100% 贯穿至 `Orchestrator` 与 `MergeController`，杜绝未签字合并 | `src/macao/core/config.py`<br>`src/macao/workflow/orchestrator.py`<br>`src/macao/merge/controller.py` | `test_config_keys_penetration_and_require_signoff_fail_closed` PASS |
| **P0-2** | **E2E 证据真实度与 Adapter 注入**：E2E Runner 显式注入配置对应的 `MockAgentAdapter`（3 位评审人：`codex`, `opencode`, `antigravity`）；修正 `vote_breakdown` 键名（`approve`/`yes_approve` 均兼容）；修正归档路径为 `.macao/archive/<checkpoint_ref>/r1/` 并校验非空 | `src/macao/workflow/e2e_runner.py`<br>`src/macao/consensus/engine.py`<br>`src/macao/cli/ui.py` | `test_e2e_runner_truthful_evidence_and_archive`<br>`macao e2e-run` 实测 PASS（5 份归档产物，100% HEAD 匹配） |
| **P0-3** | **沙箱边界定性**：在 `ExecutionMode.SANDBOXED`、`CapabilityManifest` 及文档中如实定性为“Git Worktree 与工作目录路径隔离”，明确标注容器级命名空间隔离为后续规划，消除虚假承诺 | `src/macao/core/types.py`<br>`docs/POC_VERIFICATION_REPORT.md` | `test_mock_capabilities` PASS |
| **P1-2** | **MergeController 消除非 git 假成功逃生舱**：非 git 仓库直接返回 False 拒绝合并，严格 Fail-closed | `src/macao/merge/controller.py` | `test_merge_controller_non_git_fail_closed` PASS |
| **P1-3** | **Worktree 创建消除非 git 静默 mkdir 假成功**：非 git 目录直接抛出 `RuntimeError` 拒绝创建，严格 Fail-closed | `src/macao/utils/git_utils.py` | `test_git_utils_fail_closed_and_no_dummy_data` PASS |
| **P1-4** | **消除硬编码回退值**：`Orchestrator` 动态根据注入的 `reviewer_adapters` 与 `macao.yaml` 提取 reviewer IDs 与 executor ID，消除硬编码 `cc-glm`/`kimi`/`cc-ds4` 回退 | `src/macao/workflow/orchestrator.py` | `test_orchestrator_config_injection` PASS |
| **P1-5** | **PTY Harness 跨平台探测与 Windows 优雅跳过**：在 `integ_harness.py` 中探测 `pty` 模块，非 POSIX 平台返回 `SKIPPED` 并标注说明，消除跨平台报错 | `src/macao/adapter/integ_harness.py`<br>`tests/test_integ_harness.py` | `test_verify_all_clis` PASS |
| **P1-6** | **消除 `get_changed_files` 伪造兜底**：git 命令失败或为空时返回空列表 `[]`，严禁伪造 `src/main.py` 假数据流入权威 Review Context | `src/macao/utils/git_utils.py` | `test_git_utils_fail_closed_and_no_dummy_data` PASS |
| **P2-5** | **消除 DTO 重复定义**：移除 `types.py` 中的重复 `AEPEnvelope`，统一使用 `msg/envelope.py`，规范 `OpinionStatus` 枚举为 `APPROVED / CHANGES_REQUESTED / REJECTED` | `src/macao/core/types.py`<br>`src/macao/msg/envelope.py` | `test_aep_envelope_schema` PASS |
| **P2-6** | **合并 commit SHA 精确全量校验**：`MergeController` 解析完整 40 位 SHA 进行 `head == checkpoint_ref` 硬校验，杜绝前缀模糊匹配 | `src/macao/merge/controller.py` | `test_scenario_s1_happy_path_and_merge` PASS |

---

## 下一步行动

1. 提交全部整改代码与新增回归测试套件；
2. 保持 L2 / PG-1 严谨门禁标准，推送到远程仓库。
