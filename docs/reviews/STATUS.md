# MACAO 文档与代码门禁状态（Live Status）

> 依据 `docs/MACAO_REVIEW_GUIDELINES.md` 维护；本文件是唯一允许记录实时门禁状态的位置。
> 治理规则（P1-3 确立，已固化）：**每轮申请复审前，STATUS 必须与 `reviews/` 目录全量对账**，不得以 STATUS 登记子集为闭环核验边界。

- **最新更新时间**：2026-08-29（四方独立专家针对 `e7ba2d2` 提出的 P0-NEW-1 ~ P0-NEW-4 及 P1 全部闭环整改完毕，提交新一轮 L3/PG-2 复审申请，完成 100% 全量对账）
- **当前申请对象**：自 `2026-08-29-review-request-Phase1-Phase2-Rectification.md`（`e7ba2d2`）后的 `message_id` 16 位高熵防碰撞、AEP Schema 与 PRD 10 状态/7 类型对齐、人工裁定 4 选项连通、MergeController CI 失败原子回滚与配置远端 Fail-closed、Mock Adapter 契约消费全生命周期驱动、Worktree 事务性准备与 43 项全量自动化测试
- **当前定级状态**：**已提交 L3 SCENARIO-VERIFIED / PG-2 复审申请（待四方专家复核确认）**
  - **整改闭环**：四方专家针对 `e7ba2d2` 提出的 4 项新阻断项（`message_id` 碰撞、AEP 协议与人工裁定断裂、CI 门禁原子回滚、Mock Adapter 契约消费驱动）全部实施精准单点修复并通过回归测试；
  - **机验表现**：43/43 单元与回归测试 100% PASS，5 轮连续回归 0 flake / 0 碰撞；4/4 真实 CLI PTY 探针通过；E2E Runner 5 份物理产物与分支 HEAD 100% 匹配。
- **历史文档定级**：PRD **v2.3.1**（§3.2 Layer 1c 四值终局分支已单点闭环修复，达到 L1 DOC-ALIGNED / PG-0）
- **当前代码机验**：`PYTHONPATH=src python3 -m unittest discover tests -v` **43 ran / 43 PASS (100%)**；`test-clis` / `e2e-run` 路径属实。

---

## 评审申请记录全量对账表 (Review Registry - 35 份历史与当前评审报告 + 6 份申请全量对账)

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
| 2026-08-29 | `2026-08-29-review-request-Phase1-Phase2-Rectification.md` | `906b17e` .. `e7ba2d2` | L3 / PG-2 | `2026-08-29-review-result-e7ba2d2-claude.md`<br>`2026-08-29-review-result-e7ba2d2-rectification-qwen.md`<br>`2026-08-29-review-result-e7ba2d2-zcode.md`<br>`2026-08-29-review-result-e7ba2d2-codex.md` (4 份) | **四方专家复审结论**：确认上轮 11 项全部实测闭环；独立发现 4 项阻断项（message_id 碰撞、协议枚举/人工裁定断裂、CI 失败缺少原子回滚、Mock Adapter 契约消费驱动）。 |
| **2026-08-29** | **`2026-08-29-review-request-L3-Final-Rectification.md`** | **`e7ba2d2` .. HEAD** | **L3 / PG-2** | 专家复核中（待评） | **已完成本轮 4 项阻断项与 P1 问题精准闭环**：<br>1. `message_id` 升级为 16 位高熵随机数（0 碰撞，5000 次采样验证）；<br>2. 恢复 PRD 10 状态与 Schema 7 种 AEP 类型，规范 `OverrideChoice`，4 种人工裁定 100% 连通并通过 Schema 校验；<br>3. `MergeController` 增加 CI 失败原子硬回滚与配置远端 Fail-closed 检查；<br>4. Mock Adapter 契约全生命周期驱动与 Worktree 事务性准备；<br>5. 43/43 测试全绿（5 轮连续回归 0 flake）。 |

---

## 本轮（e7ba2d2 复审意见）P0 / P1 闭环整改清单

| 编号 | 问题与整改要求 | 修复落点与代码实现 | 验证测试证据 |
|---|---|---|---|
| **P0-NEW-1** | **`message_id` 短 UUID 随机碰撞导致 SQLite 主键冲突崩溃**：仅取 4 位十进制导致同日仅 ~10,000 空间。 | `src/macao/msg/envelope.py` 升级为 16 位高熵随机数 `str(uuid.uuid4().int)[:16]`，符合 `^msg-[0-9]{8}-[0-9]{3,}$` | `test_message_id_entropy_zero_collisions_in_5000` PASS（5,000 采样 0 碰撞，500 并发写 0 冲突，5 轮回归 PASS） |
| **P0-NEW-2** | **协议枚举/Schema/PRD 错配与人工裁定断裂**：恢复 `UNKNOWN` 状态与 7 种标准 AEP 类型，规范 `OverrideChoice`，修复 `resolve_override` 广播标准消息 | `src/macao/core/types.py`<br>`src/macao/workflow/orchestrator.py`<br>`src/macao/consensus/vote.py`<br>`src/macao/workflow/transitions.py` | `test_resolve_override_all_four_choices_and_valid_aep` PASS（4 种裁定全部连通，所有消息符合 Draft-07 Schema） |
| **P0-NEW-3** | **MergeController CI 失败缺少原子回滚与配置远端检查**：CI 失败时目标分支原子硬回滚至 pre_merge_head；配置 remote 不存在时 Fail-closed | `src/macao/merge/controller.py` | `test_merge_controller_ci_gate_failure_rollback` PASS<br>`test_merge_controller_missing_remote_fail_closed` PASS |
| **P0-NEW-4** | **Mock Adapter 契约消费驱动与 Worktree 事务性准备**：驱动 Mock Adapter 契约全生命周期；Worktree 创建失败不推进状态且不消费产物 | `src/macao/workflow/e2e_runner.py`<br>`src/macao/workflow/orchestrator.py` | `test_worktree_dispatch_transactional_fail_closed` PASS<br>`test_e2e_runner_truthful_evidence_and_archive` PASS |
| **P1-1** | **StateStore register_artifact 幂等安全**：已消费产物重复注册不被覆盖 | `src/macao/storage/store.py` | `test_artifact_registration_and_append_semantics` PASS |

---

## 下一步行动

1. 提交本次整改代码与复审申请文档；
2. 邀请专家委员会（Claude / Qwen / ZCode / Codex）对新提交开展独立复审并定级 L3 / PG-2。
