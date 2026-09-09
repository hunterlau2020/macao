# MACAO 检查点强归档防伪、执行者组合根 Fail-Closed 与全适配器准则透传复审申请（Commit 51fa456 / Round 6）

- **文档归档路径**: `docs/reviews/2026-09-10-review-request-51fa456.md`
- **申请日期 (Date)**: 2026-09-10
- **申请人 (Author)**: MACAO Architecture & Engineering Team
- **目标定级 (Target Level)**: **L3 SCENARIO-VERIFIED / PG-2 全量认证，并提请 L4 RELEASE-READY / PG-3 准入评审**
- **当前受审提交 (Checkpoint Ref)**: `51fa456`（完整 SHA：`51fa456ada474818a1107f1a11b061661dab1063`）
- **合并审计范围 (Review Range)**: `bdc177e..51fa456`
- **评审轮次 (Review Round)**: `Round 6`（`bdc177e` 4 位专家评审后的 P1 全面闭环复审）
- **关联任务 ID (Task ID)**: `task-20260910-p1-closures-evidence-commit-binding-failclosed-executor`
- **前序受审基线与处置单 (Previous Baseline & Disposition)**:
  - 前序受审基线：`bdc177e`（4 位专家独立复审：Claude, Grok, Pi-Qwen, Codex，共识仲裁结论为 **待返工 REWORK (3 票批准 / 1 票否决)**）
  - 前序处置报告：[`docs/reviews/2026-09-10-disposition-bdc177e.md`](2026-09-10-disposition-bdc177e.md)（所有 P1 阻断项彻底闭环，绑定条件在已知简化表完整登记）
  - 4 份专家评审归档：
    1. [`2026-09-09-review-result-bdc177e-claude.md`](2026-09-09-review-result-bdc177e-claude.md)（Claude：YES_APPROVE / 0 项 P0, 0 项 P1, 1 项 P2：未跟踪证据文件绕过 Git blob 校验）
    2. [`2026-09-09-review-result-bdc177e-grok.md`](2026-09-09-review-result-bdc177e-grok.md)（Grok：YES_APPROVE / 0 项 P0, 0 项 P1, 3 项 P2：未跟踪证据文件、未知 executor CLI、审查员提示词缺失验收准则）
    3. [`2026-09-09-review-result-bdc177e-pi-qwen.md`](2026-09-09-review-result-bdc177e-pi-qwen.md)（Pi-Qwen：YES_APPROVE / 0 项 P0, 0 项 P1，附 2 项绑定条件：`immutable=1` 陈旧读与未跟踪证据跳过边界按 §8.3-2 登记）
    4. [`2026-09-10-review-result-bdc177e-codex.md`](2026-09-10-review-result-bdc177e-codex.md)（Codex：REJECT / 2 项 P1：P1-bdc177e-01 未存在于 `evidence_commit` 的正文仍可推进 checkpoint，P1-bdc177e-02 未知 executor CLI 静默降级为空且 `--no-probe` 创建 CODING 任务）
- **上位评审方法论**: [`docs/MACAO_REVIEW_GUIDELINES.md`](../MACAO_REVIEW_GUIDELINES.md)（v1.1）
- **实时门禁状态表**: [`docs/reviews/STATUS.md`](STATUS.md)

---

## 1. 变更摘要与核心目标 (Summary & Rationale)

在 Round 5（针对 Commit `bdc177e`）的独立机验评审中，4 位专家共识仲裁为 **REWORK**（3 票 YES_APPROVE / 1 票 REJECT），依据 Fail-Closed 原则，针对 Codex 指出的 2 项 P1 阻断缺陷及其他专家提出的关键绑定项实施彻底闭环：

1. **检查点正文与声明 Git Commit 强制强归档绑定 (Codex P1-bdc177e-01 / Claude P2-1 / Grok P2-1 / Pi-Qwen 条件②)**：
   - 原实现仅在 `git cat-file -e` 返回 0 时才校验 blob 散列。当证据文档在磁盘存在但未加入版本库（如未跟踪文件或事后新增文件）时，`cat-file` 失败导致跳过 blob 比对，系统仅校验磁盘物理文件 SHA 即放行进入 `READY_FOR_REVIEW`；
   - **闭环方案**：在 Git 仓库环境下，强制要求 `git cat-file -e <latest_commit>:<rel_posix>` 必须返回 0，且提取的 Git tree blob 内容 SHA-256 必须与磁盘物理文件及 manifest 声明逐字节完全匹配；未提交、未跟踪或事后篡改一律判定为伪造证据，拒绝推进 (Fail-Closed)。

2. **CLI 组合根执行者未知类型 Fail-Closed 拦截 (Codex P1-bdc177e-02 / Grok P2-2)**：
   - 原实现中 `LiveAgentDispatcher.get_adapter_for_executor()` 对未知 CLI 返回 `None`，导致 `Orchestrator.executor` 为空；当使用 `macao task create --no-probe ...` 时跳过探活预检，直接创建无执行者的 `CODING` 任务写入数据库，造成执行者永久悬空；
   - **闭环方案**：`get_adapter_for_executor()` 对未知 CLI 严格抛出 `ValueError`；组合根 `main.py get_orchestrator()` 捕获并以退出码 1 阻断，拒绝在非法配置下向 `state.db` 写入任何任务或触发状态转移。

3. **全部七款 AI CLI 适配器审查员提示词注入验收准则 (Grok P2-3)**：
   - 适配器层不仅在 Executor 角色中透传验收标准，在 Reviewer 角色中统一格式化并注入 `Acceptance Criteria`，确保审查员在独立审查中能够获得完整的业务准则上下文。

4. **规范化已知简化登记 (Pi-Qwen 条件① / Codex P2-bdc177e-01)**：
   - 依据 Guidelines v1.1 §5.2 / §8.3-2，在 `docs/reviews/STATUS.md` 常设表中完整登记 `immutable=1` 陈旧读行为与 `task checkpoint --auto` 辅助草稿边界。

---

## 2. 变更文件与行数清单 (Git Diff Numstat Verification)

> 依据 Guidelines v1.1 §9，下述变更统计由 `git diff --numstat bdc177e..51fa456` 严格生成：

| 文件路径 | 变更属性 | 增行 / 删行 | 对应缺陷与模块说明 |
|---|---|---|---|
| `docs/reviews/2026-09-09-review-request-bdc177e.md` | 新增 | +179 / -0 | Round 5 复审申请单归档 |
| `docs/reviews/2026-09-09-review-result-bdc177e-claude.md` | 新增 | +144 / -0 | Claude Round 5 评审报告归档 |
| `docs/reviews/2026-09-09-review-result-bdc177e-grok.md` | 新增 | +320 / -0 | Grok Round 5 评审报告归档 |
| `docs/reviews/2026-09-09-review-result-bdc177e-pi-qwen.md` | 新增 | +117 / -0 | Pi-Qwen Round 5 评审报告归档 |
| `docs/reviews/2026-09-10-disposition-bdc177e.md` | 新增 | +108 / -0 | Round 5 评审处置与缺陷闭环报告 |
| `docs/reviews/2026-09-10-review-result-bdc177e-codex.md` | 新增 | +66 / -0 | Codex Round 5 评审报告归档 |
| `docs/reviews/STATUS.md` | 修改 | +51 / -30 | 实时门禁账本对账、四方结论登记与已知简化固化 |
| `docs/reviews/evidence/2026-09-09-bdc177e-claude/probe_bdc177e_claude.py` | 新增 | +175 / -0 | Claude 评审证据复现探针 |
| `docs/reviews/evidence/2026-09-09-bdc177e-pi-qwen/README.md` | 新增 | +40 / -0 | Pi-Qwen 证据说明文档 |
| `docs/reviews/evidence/2026-09-09-bdc177e-pi-qwen/repro_bdc177e_pi_qwen.py` | 新增 | +323 / -0 | Pi-Qwen 评审复现脚本 |
| `docs/reviews/evidence/2026-09-10-bdc177e-codex/reproduce_remaining_fail_closed_gaps.py` | 新增 | +144 / -0 | Codex 归档复现脚本 |
| `docs/reviews/evidence/2026-09-10-bdc177e-grok/README.md` | 新增 | +19 / -0 | Grok 证据说明文档 |
| `docs/reviews/evidence/2026-09-10-bdc177e-grok/probe_bdc177e.out.txt` | 新增 | +62 / -0 | Grok 探针执行输出归档 |
| `docs/reviews/evidence/2026-09-10-bdc177e-grok/probe_bdc177e.py` | 新增 | +403 / -0 | Grok 评审复现探针 |
| `src/macao/adapter/antigravity.py` | 修改 | +3 / -0 | 审查员提示词透传验收准则 |
| `src/macao/adapter/claude.py` | 修改 | +3 / -0 | 审查员提示词透传验收准则 |
| `src/macao/adapter/codex.py` | 修改 | +3 / -0 | 审查员提示词透传验收准则 |
| `src/macao/adapter/cursor.py` | 修改 | +3 / -0 | 审查员提示词透传验收准则 |
| `src/macao/adapter/kimi.py` | 修改 | +3 / -0 | 审查员提示词透传验收准则 |
| `src/macao/adapter/mock.py` | 修改 | +28 / -11 | 测试夹具已提交证据感知 |
| `src/macao/adapter/opencode.py` | 修改 | +3 / -0 | 审查员提示词透传验收准则 |
| `src/macao/adapter/pi.py` | 修改 | +3 / -0 | 审查员提示词透传验收准则 |
| `src/macao/cli/main.py` | 修改 | +11 / -1 | 组合根捕获未知 CLI 异常退出码 1，auto-checkpoint 自动暂存证据 |
| `src/macao/workflow/e2e_runner.py` | 修改 | +6 / -1 | 端到端测试同步提交评审证据 |
| `src/macao/workflow/live_dispatcher.py` | 修改 | +1 / -1 | get_adapter_for_executor 未知 CLI 抛出 ValueError |
| `src/macao/workflow/live_runner.py` | 修改 | +6 / -6 | 运行态 runner 同步提交评审证据 |
| `src/macao/workflow/orchestrator.py` | 修改 | +9 / -7 | 强制证据存在于 commit 并严格比对 blob 散列 |
| `tests/test_orchestrator_sim.py` | 修改 | +5 / -1 | 模拟测试夹具同步归档证据 |
| `tests/test_p0_p1_rectification.py` | 修改 | +21 / -20 | 历史整改测试适配证据提交强校验 |
| `tests/test_p1_closures_and_regressions.py` | 修改 | +139 / -0 | 新增 3 项回归测试（未提交证据拒止、未知 CLI 阻断、全审查员准则透传） |
| `tests/test_phase3.py` | 修改 | +12 / -12 | Phase 3 集成测试适配证据提交强校验 |

---

## 3. 质量门禁与机验命令 (Quality Gates & Verification Commands)

专家委员会机验复现可直接执行以下标准命令：

### 3.1 自动化测试套件全量执行
```bash
PYTHONPATH=src python3 -m unittest discover tests
# 预期结果：Ran 173 tests in ~71s, OK (100% 通过，0 failures, 0 errors)
```

### 3.2 针对性回归测试套件执行
```bash
PYTHONPATH=src python3 -m unittest tests/test_p1_closures_and_regressions.py
# 预期结果：Ran 29 tests, OK (含 Round 5 闭环的 3 项新增测试)
```

### 3.3 提交洁净度校验
```bash
git show --check 51fa456ada474818a1107f1a11b061661dab1063
# 预期结果：无任何行尾空白与格式违规，退出码 0
```

### 3.4 Python 语法编译校验
```bash
python3 -m compileall -q src tests
# 预期结果：0 Errors，退出码 0
```

### 3.5 专家复现脚本机验
```bash
# 执行 Codex 归档复现脚本，验证未跟踪文件与未知 CLI 已被物理拦截
python3 docs/reviews/evidence/2026-09-10-bdc177e-codex/reproduce_remaining_fail_closed_gaps.py
# 预期结果：任务保持在 CODING 状态，未被非法越权推进至 READY_FOR_REVIEW
```

---

## 4. 伴随机器信封样例 (Accompanying Development Checkpoint - EXAMPLE)

> 注：本小节为伴随机器信封 `.macao/.dev.yml` 格式规范快照样例。经过 `macao.core.schema.validate_dev_manifest` 严格校验，包含所有必填字段。

```yaml
version: "1.0"
timestamp: "2026-09-10T01:30:00Z"
task_id: "task-20260910-p1-closures-evidence-commit-binding-failclosed-executor"
checkpoint_ref: "51fa456"
review_round: 6
status: "ready_for_review"
signal: "EXPLICIT"
executor:
  id: "opencode-dev"
  role: "Lead Orchestrator Architect"
  cli: "opencode"
full_document:
  path: "docs/reviews/2026-09-10-disposition-bdc177e.md"
  evidence_commit: "51fa456"
  sha256: "a78035b8786d7a59c9379af169427d7ea0643eebb2ba12fa1c5e6c4ba04ac451"
development:
  phase: "Phase 3 Orchestrator Hardening & Multi-Agent Dispatch"
  description: "Remediate all P1 blocking findings from Round 5 (bdc177e), enforce Git commit existence for evidence documents, fail-closed on unknown executor, and propagate criteria to all reviewers"
  artifacts:
    - type: "code"
      path: "src/macao/workflow/orchestrator.py"
      changed_lines: 16
      updated: true
    - type: "code"
      path: "src/macao/workflow/live_dispatcher.py"
      changed_lines: 2
      updated: true
    - type: "code"
      path: "src/macao/cli/main.py"
      changed_lines: 12
      updated: true
    - type: "code"
      path: "src/macao/adapter/mock.py"
      changed_lines: 39
      updated: true
    - type: "code"
      path: "tests/test_p1_closures_and_regressions.py"
      changed_lines: 139
      updated: true
  quality_metrics:
    tests_passed: true
    tests_total: 173
  git:
    latest_commit: "51fa456"
    branch: "main"
```
