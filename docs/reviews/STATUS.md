# MACAO 文档与代码门禁状态（Live Status）

> 依据 `docs/MACAO_REVIEW_GUIDELINES.md` 维护；本文件是唯一允许记录实时门禁状态的位置。
> 治理规则（P1-3 确立，已固化）：**每轮申请复审前，STATUS 必须与 `reviews/` 目录全量对账**，不得以 STATUS 登记子集为闭环核验边界。

- **最新更新时间**：2026-08-27（架构装配与配置单一事实源整改全部完成，28/28 测试通过）
- **当前申请对象**：自 `2026-08-26-review-request-PRD-v2.3.1.md` 后的技术架构设计、核心代码整改实现与全套自动化测试套件
- **当前目标等级**：**L2 SPEC-CODE-ALIGNED / PG-1 准入**（P0/P1 阻断项已闭环修复，28/28 PASS，待专家终审宣告）
- **历史文档定级**：PRD **v2.3.1**（§3.2 Layer 1c 四值终局分支已单点闭环修复，达到 L1 DOC-ALIGNED / PG-0）
- **当前代码机验**：`PYTHONPATH=src python3 -m unittest discover tests -v` **28 ran / 28 PASS (100%)**；`doctor` / `preflight` / `git diff --check` **全部 clean PASS**。

---

## 评审申请记录全量对账表 (Review Registry - 27 份评审结果全量对账)

| 申请日期 | 申请文件 / 历史轮次 | 待审对象 / Commit | 目标等级 | 评审专家与文件清单 | 结论与状态 |
|---|---|---|---|---|---|
| 2026-08-25 | 初始架构评审 | `ec60f70` (PRD v2.1) | L1 | `2026-08-25-review-result-ec60f70-claude.md`<br>`2026-08-25-review-result-ec60f70-codex.md`<br>`2026-08-25-review-result-ec60f70-gemini.md` (3 份) | 未通过（发现状态机与共识分歧） |
| 2026-08-26 | 历史迭代轮 1 | `47f54f2` (PRD v2.2) | L1 | `2026-08-26-review-result-47f54f2-codex.md` (1 份) | 历史追踪（指出沙箱与存储边界） |
| 2026-08-26 | 历史迭代轮 2 | `684a012` (PRD v2.2.1) | L1 | `2026-08-26-review-result-684a012-claude.md`<br>`2026-08-26-review-result-684a012-codex.md`<br>`2026-08-26-review-result-684a012-gemini.md` (3 份) | 历史追踪（收敛 AEP 信封与 Schema） |
| 2026-08-26 | 历史迭代轮 3 | `8ab9be7` (PRD v2.2.2) | L1 | `2026-08-26-review-result-8ab9be7-claude.md`<br>`2026-08-26-review-result-8ab9be7-codex.md`<br>`2026-08-26-review-result-8ab9be7-gemini.md`<br>`2026-08-26-review-result-8ab9be7-kimi.md`<br>`2026-08-26-review-result-8ab9be7-opencode.md` (5 份) | 历史追踪（确立并集方案 B 与死锁 HOLD） |
| 2026-08-26 | `2026-08-26-review-request-PRD-v2.3.md` | `cc77a94` (PRD v2.3) | L1 | `2026-08-26-review-result-cc77a94-claude.md`<br>`2026-08-26-review-result-cc77a94-codex.md`<br>`2026-08-26-review-result-cc77a94-gemini.md`<br>`2026-08-26-review-result-cc77a94-kimi.md`<br>`2026-08-26-review-result-PRD-v2.3-opencode.md` (5 份) | 未通过（提出 2 P0 + 3 P1 修订项） |
| 2026-08-26 | `2026-08-26-review-request-PRD-v2.3.1.md` | `403ddc7` (PRD v2.3.1) | L1 / PG-0 | `2026-08-26-review-result-403ddc7-claude.md`<br>`2026-08-27-review-result-403ddc7-codex.md`<br>`2026-08-27-review-result-403ddc7-zcode.md` (3 份) | 上轮 2 P0 + 3 P1 全部 VERIFIED；新增 P1（§3.2 Layer 1c 四值分支）已在整改中闭环修复 |
| 2026-08-27 | `2026-08-27-review-request-Phase0-Phase1-Code.md` | `d137a05` .. `435eeea` | L2 / PG-1 | `2026-08-27-review-result-435eeea-claude.md`<br>`2026-08-27-review-result-435eeea-codex.md`<br>`2026-08-27-review-result-435eeea-zcode.md` (3 份) | 复审提出 P0 ×2 + P1 ×7 整改项；已在本次整改中**全部闭环修复并通过 28 项回归测试** |
| 2026-08-27 | 整体技术框架横向评审（非定级轮） | `435eeea` / `23dfad5` / `aa173d8` 代码架构 | — | `2026-08-27-review-result-435eeea-tech-framework-zcode.md`<br>`2026-08-27-review-result-23dfad5-tech-framework-claude.md`<br>`2026-08-27-review-result-23dfad5-codex-framework.md`<br>`2026-08-27-review-result-aa173d8-tech-framework-qwen.md` (4 份) | 四方专家（zcode / claude / codex / qwen）横向评估：确认核心缺陷已闭环，28/28 测试通过；架构装配（配置注入、类型收敛、独立 ACK）已全部完成 |

---

## 本轮（2026-08-27）P0 / P1 及架构装配整改闭环清单

| 编号 | 问题与整改要求 | 修复落点与代码提交 | 验证测试证据 |
|---|---|---|---|
| **PRD P1-1** | PRD §3.2 Layer 1c 补充四值终局分支（APPROVED, REWORK_REQUIRED, RETRY_REVIEW, CANCELLED） | `docs/MACAO_PRD_v2.md:776-791` | 文档机验通过 |
| **Code P0-1** | Deadlock 轮严禁提前落盘 `vote_result.json`，严禁伪写为 REWORK_REQUIRED | `src/macao/consensus/vote.py`<br>`src/macao/workflow/orchestrator.py` | `test_p0_deadlock_does_not_write_fake_vote_result_and_holds` PASS |
| **Code P0-2** | Reviewer 身份严格去重，拒绝未知 ID 与重复投递伪造法定人数 | `src/macao/consensus/vote.py`<br>`src/macao/workflow/state_engine.py` | `test_p0_reviewer_deduplication` PASS |
| **Code P0-3** | Reviewer Worktree 强制注入至 `review_context.repository.workspace_path`，失败时 Fail-closed 绝不回退主工作区 | `src/macao/workflow/orchestrator.py`<br>`src/macao/utils/git_utils.py` | `test_orchestrator_sim.py` PASS |
| **Code P0-4** | FSM 转移表白名单强制接入运行时（`TransitionTable.can_transition`），非法转移一律拦截 | `src/macao/workflow/transitions.py`<br>`src/macao/workflow/fsm.py` | `test_transition_rules_and_whitelist_enforcement` PASS |
| **Code P0-5** | MERGING 流水线接入，实现快速合并、CI 门禁命令与硬校验 | `src/macao/merge/controller.py`<br>`src/macao/workflow/orchestrator.py` | `test_scenario_s1_happy_path_and_merge` PASS |
| **Code P1-1** | E5 增加 `max_rework_rounds` 守卫，超限触发人工接管 | `src/macao/workflow/orchestrator.py`<br>`src/macao/workflow/state_engine.py` | `test_p1_max_rework_rounds_guard` PASS |
| **Code P1-2** | E7 终局四值决策与 CLI `override resolve` 统一委托编排器 | `src/macao/core/types.py`<br>`src/macao/cli/main.py` | CLI doctor/override PASS |
| **Code P1-3** | artifacts 表 DDL 迁移为自增主键 + 追加归档语义（杜绝覆盖历史） | `src/macao/storage/db.py`<br>`src/macao/storage/store.py` | `test_artifact_registration_and_append_semantics` PASS |
| **Code P1-4** | Review Context 从真实 `.dev.yml` 与 git diff 读取质量快照与 base commit | `src/macao/utils/context_builder.py` | `test_full_review_context_builder` PASS |
| **Code P1-5** | SQLite 连接生命周期管理（杜绝句柄泄漏）与 PTY 平台安全导入 | `src/macao/storage/db.py`<br>`src/macao/adapter/pty_session.py` | `test_state_store.py` PASS |
| **Arch-1** | `macao init` 模板与 `macao_config.schema.json` 100% 对齐，`ConfigManager` 属性按 Schema 路径读取 | `src/macao/core/config.py`<br>`src/macao/cli/main.py` | `test_default_config_template_validates_against_schema` PASS |
| **Arch-2** | 统一收敛 DTO 类型（`PreflightCheckResult`, `CapabilityManifest`），删除重复类定义 | `src/macao/core/types.py`<br>`src/macao/adapter/base.py` | `test_adapter_preflight_probes_no_type_error` PASS |
| **Arch-3** | 消息总线引入 `message_deliveries`，实现多 Reviewer 广播独立 ACK 与状态隔离 | `src/macao/storage/db.py`<br>`src/macao/msg/bus.py` | `test_message_bus_fanout_independent_ack` PASS |
| **Arch-4** | CLI 观测命令（`status`, `doctor`）去副作用，保持严格只读幂等 | `src/macao/cli/main.py` | CLI 命令实测 PASS |

---

## 下一步行动

1. 提交全部整改代码与更新文档；
2. 申请用户批准，准备进入受控真实三方 CLI（`claude-code`, `codex`, `kimi`）环境探针与实机 PTY 连通性测试阶段。
