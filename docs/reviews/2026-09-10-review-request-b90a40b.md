# MACAO 符号链接绝对阻断、Git 树普通 Blob 强校验与演示准则透传复审申请（Commit b90a40b / Round 7）

- **文档归档路径**: `docs/reviews/2026-09-10-review-request-b90a40b.md`
- **申请日期 (Date)**: 2026-09-10
- **申请人 (Author)**: MACAO Architecture & Engineering Team
- **目标定级 (Target Level)**: **L3 SCENARIO-VERIFIED / PG-2 全量认证，并提请 L4 RELEASE-READY / PG-3 准入评审**
- **当前受审提交 (Checkpoint Ref)**: `b90a40b`（完整 SHA：`b90a40b6a59fc3e35bad38e5f77d2324f3453845`）
- **合并审计范围 (Review Range)**: `51fa456..b90a40b`
- **评审轮次 (Review Round)**: `Round 7`（`51fa456` 4 位专家评审后的 P1 全面闭环复审）
- **关联任务 ID (Task ID)**: `task-20260910-p1-closures-symlink-rejection-live-runner-wiring`
- **前序受审基线与处置单 (Previous Baseline & Disposition)**:
  - 前序受审基线：`51fa456`（4 位专家独立复审：Claude, Grok, Muse, Codex，共识仲裁结论为 **待返工 REWORK (3 票批准 / 1 票否决)**）
  - 前序处置报告：[`docs/reviews/2026-09-10-disposition-51fa456.md`](2026-09-10-disposition-51fa456.md)（所有 P1 阻断项彻底闭环，P2/P3 建议项全部解决）
  - 4 份专家评审归档：
    1. [`2026-09-10-review-result-51fa456-claude.md`](2026-09-10-review-result-51fa456-claude.md)（Claude：YES_APPROVE / 0 项 P0, 0 项 P1, 0 项 P2, 1 项 P3：`live_runner.py` 演示调用点未转发 `acceptance_criteria`）
    2. [`2026-09-10-review-result-51fa456-grok.md`](2026-09-10-review-result-51fa456-grok.md)（Grok：YES_APPROVE / 0 项 P0, 0 项 P1, 0 项 P2, P3s：旧归档复现脚本断言旧漏洞、L4 OPS 缺口维持）
    3. [`2026-09-10-review-result-51fa456-muse.md`](2026-09-10-review-result-51fa456-muse.md)（Muse：YES_APPROVE / 0 项 P0, 0 项 P1, 1 项 P2：`mock.py` 演练回退说明；P3s：旧复现脚本断言、双重错误打印）
    4. [`2026-09-10-review-result-51fa456-codex.md`](2026-09-10-review-result-51fa456-codex.md)（Codex：REJECT / 1 项 P1：P1-51fa456-01 解析符号链接后校验 Git blob，未提交的声明路径仍可借用已提交正文放行；1 项 P2：P2-51fa456-02 申请引用的“专家复现脚本机验”非修复验证脚本）
- **上位评审方法论**: [`docs/MACAO_REVIEW_GUIDELINES.md`](../MACAO_REVIEW_GUIDELINES.md)（v1.1）
- **实时门禁状态表**: [`docs/reviews/STATUS.md`](STATUS.md)

---

## 1. 变更摘要与核心目标 (Summary & Rationale)

在 Round 6（针对 Commit `51fa456`）的独立机验评审中，4 位专家评审结论为 3 票 YES_APPROVE / 1 票 REJECT（Codex），共识仲裁判定为 **REWORK**。依据 Fail-Closed 原则，本轮提审范围 `51fa456..b90a40b` 针对 Codex 指出的核心阻断项 P1-51fa456-01 及专家提出的全部建议项实施代码级、测试级彻底闭环：

1. **禁止符号链接路径解析与 Git 树普通 Blob 强校验 (Codex P1-51fa456-01)**：
   - 原实现先对用户声明路径调用 `.resolve()`，导致工作树上的未跟踪符号链接（如 `untracked-alias.md -> committed.md`）被解析为目标已提交文件，进而在 `git cat-file -e` 与 blob 读取中误判放行；
   - **闭环方案**：
     - 彻底摒弃 `.resolve()`，采用 `os.path.normpath` 严格词法规范化，以未解析的原始相对声明路径作为物理检查与 Git 索引基准；
     - 沿路径向上回溯至项目根目录，检查路径自身及其所有祖先目录：任一节点若是符号链接（`is_symlink()`），立即返回 `None` 拒止；
     - 操作系统层使用 `os.lstat` 检查常规文件 (`stat.S_ISREG`)，并以 `os.O_NOFOLLOW` 方式打开读取，杜绝 TOCTOU 符号链接竞争；
     - 在 Git 仓库环境下，使用 `git ls-tree <commit> <rel_posix>` 严格检查树对象模式，必须为普通文件 blob（`100644` 或 `100755`）；若模式为符号链接（`120000`）或目录/子模块，立即返回 `None` 拒止。

2. **正向绿灯验证探针落地 (Codex P2-51fa456-02 / Grok P3-1 / Muse A-2)**：
   - 采纳专家委员会意见，不在申请中直接引用断言漏洞成立的原复现脚本；
   - 建立专用正向验证探针 [`docs/reviews/evidence/2026-09-10-51fa456-codex/verify_p1_51fa456_01_closed.py`](evidence/2026-09-10-51fa456-codex/verify_p1_51fa456_01_closed.py)，正向断言未跟踪符号链接、已提交符号链接、父目录符号链接均被拒止保持 `CODING`，常规合法文件放行，执行退出码为 0。

3. **`live_runner.py` 演示流程验收准则完整透传 (Claude P3-1)**：
   - 在 `LiveWorkflowRunner.run_live_cycle` 的 `dispatch_review_in_worktree` 调用点显式透传 `acceptance_criteria=crit_list`，与 `task adopt` 和 `review` 生产命令保持一致。

4. **终端日志去重与演练说明完善 (Muse A-1 / Muse A-3)**：
   - 消除 `main.py` 组合根未知 CLI 报错的双重打印，仅保留 Rich `console.print`；
   - 在 `mock.py` 明确补充注释，说明回退创建仅为单测演练夹具简化。

---

## 2. 变更文件与行数清单 (Git Diff Numstat Verification)

> 依据 Guidelines v1.1 §9，下述变更统计由 `git diff --numstat 51fa456..b90a40b` 严格生成：

| 文件路径 | 变更属性 | 增行 / 删行 | 对应缺陷与模块说明 |
|---|---|---|---|
| `docs/reviews/2026-09-10-disposition-51fa456.md` | 新增 | +87 / -0 | Round 6 评审处置与缺陷闭环报告 |
| `docs/reviews/2026-09-10-review-request-51fa456.md` | 新增 | +171 / -0 | Round 6 复审申请单归档 |
| `docs/reviews/2026-09-10-review-result-51fa456-claude.md` | 新增 | +163 / -0 | Claude Round 6 评审报告归档 |
| `docs/reviews/2026-09-10-review-result-51fa456-codex.md` | 新增 | +52 / -0 | Codex Round 6 评审报告归档 |
| `docs/reviews/2026-09-10-review-result-51fa456-grok.md` | 新增 | +283 / -0 | Grok Round 6 评审报告归档 |
| `docs/reviews/2026-09-10-review-result-51fa456-muse.md` | 新增 | +45 / -0 | Muse Round 6 评审报告归档 |
| `docs/reviews/STATUS.md` | 修改 | +39 / -13 | 实时门禁账本对账、四方结论登记与状态更新 |
| `docs/reviews/evidence/2026-09-10-51fa456-claude/probe_51fa456_claude.py` | 新增 | +177 / -0 | Claude 评审证据复现探针 |
| `docs/reviews/evidence/2026-09-10-51fa456-codex/reproduce_untracked_symlink_evidence_bypass.py` | 新增 | +111 / -0 | Codex 符号链接复现脚本归档 |
| `docs/reviews/evidence/2026-09-10-51fa456-codex/verify_p1_51fa456_01_closed.py` | 新增 | +168 / -0 | 符号链接防伪闭环正向验证探针 |
| `docs/reviews/evidence/2026-09-10-51fa456-grok/README.md` | 新增 | +23 / -0 | Grok 证据说明文档 |
| `docs/reviews/evidence/2026-09-10-51fa456-grok/probe_51fa456.out.txt` | 新增 | +77 / -0 | Grok 探针执行输出归档 |
| `docs/reviews/evidence/2026-09-10-51fa456-grok/probe_51fa456.py` | 新增 | +523 / -0 | Grok 评审复现探针 |
| `src/macao/adapter/mock.py` | 修改 | +3 / -0 | 补充演练简化说明注释 (Muse A-1) |
| `src/macao/cli/main.py` | 修改 | +0 / -1 | 消除组合根报错双重打印 (Muse A-3) |
| `src/macao/workflow/live_runner.py` | 修改 | +12 / -1 | 演示流程透传验收准则 (Claude P3-1) |
| `src/macao/workflow/orchestrator.py` | 修改 | +59 / -7 | 符号链接严格拒止与 Git 普通 Blob 强校验 (Codex P1-51fa456-01) |
| `tests/test_p1_closures_and_regressions.py` | 修改 | +128 / -0 | 新增 2 项回归测试（符号链接多场景拒止、演示准则透传） |

---

## 3. 质量门禁与机验命令 (Quality Gates & Verification Commands)

专家委员会机验复现可直接执行以下标准命令：

### 3.1 自动化测试套件全量执行
```bash
PYTHONPATH=src python3 -m unittest discover tests
# 预期结果：Ran 175 tests in ~69s, OK (100% 通过，0 failures, 0 errors)
```

### 3.2 针对性回归测试套件执行
```bash
PYTHONPATH=src python3 -m unittest tests/test_p1_closures_and_regressions.py
# 预期结果：Ran 31 tests, OK (含 Round 6 闭环的 2 项新增测试)
```

### 3.3 提交洁净度校验
```bash
git show --check b90a40b6a59fc3e35bad38e5f77d2324f3453845
# 预期结果：无任何行尾空白与格式违规，退出码 0
```

### 3.4 Python 语法编译校验
```bash
python3 -m compileall -q src tests
# 预期结果：0 Errors，退出码 0
```

### 3.5 专家复现与验证探针机验
```bash
# 执行符号链接正向绿灯验证探针（覆盖未跟踪、已提交、父目录符号链接拒止与常规文件放行）
python3 docs/reviews/evidence/2026-09-10-51fa456-codex/verify_p1_51fa456_01_closed.py
# 预期结果：打印 "ALL SYMLINK REMEDIATION CHECKS PASSED (P1-51fa456-01 CLOSED)"，退出码 0
```

---

## 4. 伴随机器信封样例 (Accompanying Development Checkpoint - EXAMPLE)

> 注：本小节为伴随机器信封 `.macao/.dev.yml` 格式规范快照样例。经过 `macao.core.schema.validate_dev_manifest` 严格校验，包含所有必填字段。

```yaml
version: "1.0"
timestamp: "2026-09-10T21:20:00Z"
task_id: "task-20260910-p1-closures-symlink-rejection-live-runner-wiring"
checkpoint_ref: "b90a40b"
review_round: 7
status: "ready_for_review"
signal: "EXPLICIT"
executor:
  id: "opencode-dev"
  role: "Lead Orchestrator Architect"
  cli: "opencode"
full_document:
  path: "docs/reviews/2026-09-10-disposition-51fa456.md"
  evidence_commit: "b90a40b"
  sha256: "98a06d178924e501654a6a0b242d926d8f1b8ce15d6d3a9b4fd664d4e5130cd3"
development:
  phase: "Phase 3 Orchestrator Hardening & Multi-Agent Dispatch"
  description: "Remediate P1-51fa456-01 symlink bypass, enforce Git regular blob mode, forward acceptance criteria in live runner, and eliminate terminal duplicate logs"
  artifacts:
    - type: "code"
      path: "src/macao/workflow/orchestrator.py"
      changed_lines: 66
      updated: true
    - type: "code"
      path: "src/macao/workflow/live_runner.py"
      changed_lines: 13
      updated: true
    - type: "code"
      path: "src/macao/cli/main.py"
      changed_lines: 1
      updated: true
    - type: "code"
      path: "src/macao/adapter/mock.py"
      changed_lines: 3
      updated: true
    - type: "code"
      path: "tests/test_p1_closures_and_regressions.py"
      changed_lines: 128
      updated: true
  quality_metrics:
    tests_passed: true
    tests_total: 175
  git:
    latest_commit: "b90a40b"
    branch: "main"
```
