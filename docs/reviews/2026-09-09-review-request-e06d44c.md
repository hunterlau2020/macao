# MACAO 检查点防伪闭环、UC-11 E1 守卫与 Provider 参数扩展复审申请（Commit e06d44c / Round 4）

- **文档归档路径**: `docs/reviews/2026-09-09-review-request-e06d44c.md`
- **申请日期 (Date)**: 2026-09-09
- **申请人 (Author)**: MACAO Architecture & Engineering Team
- **目标定级 (Target Level)**: **L3 SCENARIO-VERIFIED / PG-2 全量认证，并提请 L4 RELEASE-READY / PG-3 准入评审**
- **当前受审提交 (Checkpoint Ref)**: `e06d44c`（完整 SHA：`e06d44cb31a0dbcbe199e6bb124430e9701e087f`）
- **合并审计范围 (Review Range)**: `7bc8d70..e06d44c`（涵盖提交 `972e0d0`、`080720c`、`e06d44c`）
- **评审轮次 (Review Round)**: `Round 4`（`7bc8d70` 专家评审全员否决后的 P1/P2 全面闭环复审）
- **关联任务 ID (Task ID)**: `task-20260909-checkpoint-antiforgery-adopt-e1-provider-support`
- **前序受审基线与处置单 (Previous Baseline & Disposition)**:
  - 前序受审基线：`7bc8d70`（5 位专家独立复审：Codex, Grok, Claude, Qwen, Pi-Qwen，共识仲裁结论为 **全票否决待返工 REWORK**）
  - 前序处置报告：[`docs/reviews/2026-09-08-disposition-7bc8d70.md`](2026-09-08-disposition-7bc8d70.md)（所有 P1 阻塞项逐项闭环）
  - 5 份专家评审归档：
    1. [`2026-09-08-review-result-7bc8d70-codex.md`](2026-09-08-review-result-7bc8d70-codex.md)（Codex：REJECT / 2 项 P1，1 项 P2）
    2. [`2026-09-08-review-result-7bc8d70-grok.md`](2026-09-08-review-result-7bc8d70-grok.md)（Grok：NO_APPROVE / 1 项 P1，3 项 P2）
    3. [`2026-09-08-review-result-7bc8d70-claude.md`](2026-09-08-review-result-7bc8d70-claude.md)（Claude：NO_APPROVE / 2 项 P1，4 项 P2）
    4. [`2026-09-08-review-result-7bc8d70-qwen.md`](2026-09-08-review-result-7bc8d70-qwen.md)（Qwen：不予认证 / 1 项 P1，2 项 P2）
    5. [`2026-09-08-review-result-7bc8d70-pi-qwen.md`](2026-09-08-review-result-7bc8d70-pi-qwen.md)（Pi-Qwen：NO_APPROVE / REWORK / 3 项 P1，4 项 P2）
- **上位评审方法论**: [`docs/MACAO_REVIEW_GUIDELINES.md`](../MACAO_REVIEW_GUIDELINES.md)（v1.1）
- **实时门禁状态表**: [`docs/reviews/STATUS.md`](STATUS.md)

---

## 1. 变更摘要与核心目标 (Summary & Rationale)

在 Round 3（针对 Commit `7bc8d70`）的独立机验复审中，5 位评审专家通过构造独立反例脚本，指出了核心安全与编排闭环上的 3 类阻断性缺陷：
1. **检查点防伪门禁形同虚设 (P1-1 / Codex P1-02/04, Grok P1-1, Claude P1-1, Qwen P1-1, Pi-Qwen P1-A)**：`check_development_checkpoint` 对全零哈希、空哈希、缺失文件直接跳过比对放行，未比对 `executor.cli`，导致伪造信封也能进入 `READY_FOR_REVIEW`；
2. **`task adopt` UC-11 E1 守卫缺失与绕过 FSM (P1-2 / Codex P1-01, Claude P1-2, Pi-Qwen P1-B)**：`macao task adopt` 接受不存在的幽灵基线 commit（如 `deadbeef`），且未通过 `TransitionTable` 白名单推进；
3. **申请文档信封自证矛盾 (P1-3 / Pi-Qwen P1-C, Qwen QW-7BC-P1-1)**：前序申请正文信封载有全零占位符，自相矛盾。

本轮提审范围 `7bc8d70..e06d44c` 对上述问题实施彻底的代码级与文档级闭环，并增加了多 Provider CLI 的架构支持：

### 核心改进明细

1. **检查点 8 步硬核 Fail-Closed 防伪门禁**：
   - 必须满足 `task_id` 匹配当前任务；
   - `checkpoint_ref` 匹配执行分支最新 commit；
   - `full_document` 必须为 dict 且包含非空 `path`、`sha256`、`evidence_commit`；
   - `evidence_commit` 匹配 `latest_commit`；
   - `sha256` 必须完全匹配 64 位十六进制正则 `^[0-9a-fA-F]{64}$`，**且严禁全零 (`"0"*64`)**；
   - 物理文件必须真实存在、为 regular file、且位于项目根目录内（防止路径穿越）；
   - 逐字节对账物理文件真实 SHA-256，必须完全一致；
   - 严格校验 `executor.id` 与 `executor.cli` 非空且与系统配置/注入的主执行席位严格吻合。
2. **`task adopt` UC-11 E1 异常流物理守卫与 FSM 下沉**：
   - 入口处执行 `git.commit_exists(checkpoint_ref)` 校验，若物理不存在立即退出码 1 退出，绝不脏写状态库；
   - 在 `TransitionTable` 白名单中正式注册 `(IDLE, CODING): "E1_ADOPT"` 与 `(IDLE, WAITING_REVIEW): "E2_ADOPT"`；
   - 下沉到 `Orchestrator.adopt_task()` 执行标准审计与状态机推进，接管后自动串联共识仲裁。
3. **审查员 PTY 载荷验收标准全量透传**：
   - `LiveAgentDispatcher.dispatch_review_in_worktree` 显式提取 `task.acceptance_criteria` 注入审查交互 payload。
4. **Claude 会话 `cwd` 强制校验**：
   - 过滤无合法 `cwd` 的外部孤立会话，防范跨项目会话穿透。
5. **多 Provider 支持（`macao.yaml` 架构扩展）**：
   - 在 `macao_config.schema.json`（双侧 byte-identical）为 executor 和 reviewers 增加 `provider` 属性；
   - `PiAdapter` 自动拼接 `--provider <provider>`；
   - `OpenCodeAdapter` 自动组合 `-m {provider}/{model}`；
   - 调度器与动态探活 UI 呈现 `cli (provider/model) (w:weight)`。
6. **历史档案精细化对账与勘误 (P2-C / P2-D)**：
   - 纠正 `STATUS.md` 与处置单中对 Kimi 上轮结论的引用（Kimi 原文为 0 P0, 1 P1-NEW-1）；
   - 在 `STATUS.md` 中固化 Guidelines v1.1 §5.2 常设已知简化表；
   - 清除所有占位符，以物理文件的真实 64 位 SHA-256 签名。

---

## 2. 靶向变更清单 (Targeted Code Changes & Issue Mapping)

本次提审范围 `7bc8d70..e06d44c` 累计涉及 **36 个文件，+3414 / -181 行**（由 `git diff --numstat 7bc8d70..e06d44c` 严格生成）：

| 文件路径 | 模块分类 | 变动行数 | 核心修改说明 | 闭环 Issue |
| :--- | :--- | :--- | :--- | :--- |
| `src/macao/workflow/orchestrator.py` | 核心编排 | +194 / -68 | 8 重 fail-closed 检查点防伪；下沉 `adopt_task` | P1-1, P1-2 |
| `src/macao/cli/main.py` | CLI 命令 | +97 / -58 | UC-11 E1 git 存在性检查；adopt 状态机与共识对齐 | P1-2 |
| `src/macao/workflow/live_dispatcher.py` | 审查调度 | +9 / -2 | 透传 `acceptance_criteria` 与 `provider` | P1-3, Feat |
| `src/macao/adapter/session_locator.py` | 会话发现 | +7 / -6 | 强制校验并过滤无 cwd 的外部会话 | P1-3 |
| `src/macao/adapter/mock.py` | 测试适配器 | +34 / -4 | 物理生成自评文件并真实计算 64 字节 SHA-256 | P1-1 |
| `src/macao/cli/ui.py` | 终端 UI | +25 / -3 | 终端表格直观展示各席位 model 与 provider | Feat, UI |
| `src/macao/adapter/opencode.py` | CLI 适配器 | +6 / -2 | 支持 provider 参数并自动组合 `-m provider/model` | Feat |
| `src/macao/workflow/prober.py` | 探活引擎 | +4 / -0 | 提取并在探活数据中记录 provider 字段 | Feat |
| `src/macao/workflow/transitions.py` | 状态机转移 | +2 / -0 | 白名单注册 `E1_ADOPT` 与 `E2_ADOPT` 边 | P1-2 |
| `src/macao/schemas/macao_config.schema.json` | 契约 Schema | +2 / -0 | 增加 `provider` 属性定义 | Feat |
| `docs/schemas/macao_config.schema.json` | 契约文档 | +2 / -0 | 保持与 src 侧 100% 逐字节对齐 | Feat |
| `docs/reviews/STATUS.md` | 状态台账 | +56 / -7 | 补齐 §5.2 已知简化表；勘误 Kimi 引述；更新资产账目 | P2-C, P2-D |
| `docs/reviews/2026-09-08-disposition-7bc8d70.md` | 处置报告 | +125 / -0 | Round 3 正式处置报告 | 规范 |
| `tests/test_p1_closures_and_regressions.py` | 回归测试 | +111 / -0 | 10 重检查点防伪 fail-closed 变体专项测试套件 | P1-1 |
| `tests/test_task_adopt.py` | 回归测试 | +45 / -10 | UC-11 E1 守卫与 adopt 状态转移全面测试 | P1-2 |
| `tests/test_p0_p1_rectification.py` | 回归测试 | +32 / -13 | 适配物理自评文件生成与真实 SHA-256 对账 | P1-1 |
| `tests/test_pi_and_session_locator.py` | 回归测试 | +21 / -0 | PiAdapter model + provider 命令行拼接测试 | Feat |
| `tests/test_config.py` | 回归测试 | +12 / -0 | OpenCodeAdapter model + provider 命令行测试 | Feat |
| `tests/test_phase3.py` | 集成测试 | +16 / -3 | 消除全零 hash 旁路，适配物理自评 | P1-1 |
| `tests/test_clean_and_rollback.py` | 集成测试 | +2 / -0 | 适配最新任务模型 | P1-1 |
| `AGENTS.md` | 仓储规范 | +4 / -4 | 测试用例计数同步至 165 项 | 规范 |

---

## 3. 证据与机验指令 (Verification Commands & Invariant Checks)

请评审专家在全新干净导出目录或隔离沙箱中执行以下机验指令（依据 Guidelines v1.1 §3.4 参照系纪律）：

### 3.1 单元与集成测试全量验证
```bash
PYTHONPATH=src python3 -m unittest discover tests
# 预期结果：Ran 165 tests in ~75s, OK (0 failures, 0 errors)
```

### 3.2 契约与编译检查
```bash
# 8 份 JSON Schema 逐字节对齐验证
python3 -m unittest tests/test_schema.py
# 预期结果：Ran 8 tests, OK (0 failures, 0 errors)

# Python 字节码全量编译检查
python3 -m compileall -q src tests
# 预期结果：返回码 0，零输出
```

### 3.3 提交级差异与格式检查
```bash
git show --check e06d44c77c688bb715bb997a3cf556bc91f6920f
# 预期结果：返回码 0，无尾随空白或冲突标记
```

### 3.4 专家复现脚本反向回归验证
```bash
# 1. Grok 检查点防伪探针（0 个 fail-open）
PYTHONPATH=src python3 docs/reviews/evidence/2026-09-08-7bc8d70-grok/probe_checkpoint_p104.py
# 预期结果：ALL_MATCH_CLAIM, fail_open_cases= (空), 退出码 0

# 2. Claude 检查点与 adopt 探针（100% fail-closed 拦截）
PYTHONPATH=src python3 docs/reviews/evidence/2026-09-08-7bc8d70-claude/probe_checkpoint_and_adopt.py
# 预期结果：zero_hash/missing_file/empty_sha/wrong_cli 全部 advanced=False，adopt nonexistent baseline 返回 1，退出码 0

# 3. Qwen 漏洞复现探针（P1 全部 not-reproduced）
PYTHONPATH=src python3 docs/reviews/evidence/2026-09-08-7bc8d70-qwen/repro_7bc8d70_qwen.py
# 预期结果：QW-7BC-P1-1a/b/c 全部 not-reproduced，退出码 0
```

---

## 4. 伴随机器信封样例 (Accompanying Development Checkpoint - EXAMPLE)

> 注：本小节为伴随机器信封 `.macao/.dev.yml` 格式规范快照样例。依据 Guidelines v1.1 §9 确定性表述纪律，物理信封由主执行席位签署并逐字节对账正文真实 SHA-256。

```yaml
version: "1.0"
timestamp: "2026-09-09T00:22:00Z"
task_id: "task-20260909-checkpoint-antiforgery-adopt-e1-provider-support"
checkpoint_ref: "e06d44c"
review_round: 4
status: "ready_for_review"
signal: "EXPLICIT"
executor:
  id: "opencode-dev"
  role: "Lead Orchestrator Architect"
  cli: "opencode"
full_document:
  path: "docs/reviews/2026-09-09-review-request-e06d44c.md"
  evidence_commit: "e06d44c"
  sha256: "d599dca03ec19592bb519b8a7b3f4a7bf6fb5f48d39e9163435f4d40fd246222"
development:
  phase: "Phase 3 Orchestrator Hardening & Multi-Agent Dispatch"
  description: "Remediate all P1 blocking findings from Round 3 (7bc8d70), enforce 8-step checkpoint anti-forgery, adopt UC-11 E1 guard, add provider support for multi-provider CLIs, and reconcile review archives"
  artifacts:
    - type: "code"
      path: "src/macao/workflow/orchestrator.py"
      changed_lines: 262
      updated: true
    - type: "code"
      path: "src/macao/cli/main.py"
      changed_lines: 155
      updated: true
    - type: "code"
      path: "src/macao/adapter/pi.py"
      changed_lines: 4
      updated: true
    - type: "code"
      path: "src/macao/adapter/opencode.py"
      changed_lines: 8
      updated: true
    - type: "schema"
      path: "src/macao/schemas/macao_config.schema.json"
      changed_lines: 2
      updated: true
  quality_metrics:
    unit_tests_passing: 165
    unit_tests_total: 165
    all_tests_green: true
    schema_parity_verified: true
```
