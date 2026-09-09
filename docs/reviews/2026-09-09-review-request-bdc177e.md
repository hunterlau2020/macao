# MACAO 检查点防伪加固、执行者接线闭环与全适配器验收准则透传复审申请（Commit bdc177e / Round 5）

- **文档归档路径**: `docs/reviews/2026-09-09-review-request-bdc177e.md`
- **申请日期 (Date)**: 2026-09-09
- **申请人 (Author)**: MACAO Architecture & Engineering Team
- **目标定级 (Target Level)**: **L3 SCENARIO-VERIFIED / PG-2 全量认证，并提请 L4 RELEASE-READY / PG-3 准入评审**
- **当前受审提交 (Checkpoint Ref)**: `bdc177e`（完整 SHA：`bdc177eaaff577e119093e686f2164bcc133f781`）
- **合并审计范围 (Review Range)**: `e06d44c..bdc177e`
- **评审轮次 (Review Round)**: `Round 5`（`e06d44c` 4 位专家评审后的 P1 全面闭环复审）
- **关联任务 ID (Task ID)**: `task-20260909-p1-closures-wire-executor-criteria-blob-check`
- **前序受审基线与处置单 (Previous Baseline & Disposition)**:
  - 前序受审基线：`e06d44c`（4 位专家独立复审：Grok, Codex, Claude, Pi-Qwen，共识仲裁结论为 **待返工 REWORK (3 票否决 / 1 票批准)**）
  - 前序处置报告：[`docs/reviews/2026-09-09-disposition-e06d44c.md`](2026-09-09-disposition-e06d44c.md)（所有 P1 阻断项与重点项彻底闭环）
  - 4 份专家评审归档：
    1. [`2026-09-09-review-result-e06d44c-grok.md`](2026-09-09-review-result-e06d44c-grok.md)（Grok：YES_APPROVE / 0 项 P0，0 项 P1；空 commit 与前缀逃逸作为 P2 提出）
    2. [`2026-09-09-review-result-e06d44c-codex.md`](2026-09-09-review-result-e06d44c-codex.md)（Codex：REJECT / 3 项 P1：兄弟目录逃逸与 Git blob 校验、组合根执行者漏配与 5 款适配器 criteria 丢失、提交哈希与 manifest 规范性）
    3. [`2026-09-09-review-result-e06d44c-claude.md`](2026-09-09-review-result-e06d44c-claude.md)（Claude：NO_APPROVE / 3 项 P1：兄弟目录逃逸、组合根漏配执行者与 5 款适配器 criteria 丢失、提交哈希与示例；全部闭环）
    4. [`2026-09-09-review-result-e06d44c-pi-qwen.md`](2026-09-09-review-result-e06d44c-pi-qwen.md)（Pi-Qwen：NO_APPROVE / REWORK / 2 项 P1：提交哈希 typo 导致 bad object、5 款适配器丢弃验收标准）
- **上位评审方法论**: [`docs/MACAO_REVIEW_GUIDELINES.md`](../MACAO_REVIEW_GUIDELINES.md)（v1.1）
- **实时门禁状态表**: [`docs/reviews/STATUS.md`](STATUS.md)

---

## 1. 变更摘要与核心目标 (Summary & Rationale)

在 Round 4（针对 Commit `e06d44c`）的独立机验评审中，4 位专家共识仲裁为 **REWORK**（1 票 YES_APPROVE / 3 票 NO_APPROVE / REJECT），并精确指出了 3 项核心阻断缺陷：
1. **检查点防伪门禁路径越界与 Git Blob 校验漏洞 (Codex P1-01 / Claude P1-1 / Grok P2-1)**：
   - 原实现使用 `str(doc_path).startswith(str(self.root.resolve()))`，导致项目同名前缀的兄弟目录（如 `/path/repo_sibling/evil.md`）可逃逸沙箱越界被放行；
   - `if evidence_commit and evidence_commit != latest_commit:` 导致空提交哈希直接跳过校验被放行；
   - 缺少对 Git 树对象 blob 散列的校验，无法防止已提交与未提交磁盘篡改的不一致。
2. **CLI 组合根漏配 Executor 适配器，且 5 款 AI CLI 适配器丢弃 `acceptance_criteria` (Codex P1-02 / Claude P1-2 / Pi-Qwen P1-2)**：
   - `main.py get_orchestrator()` 仅组装了 `reviewers`，未调用分发器组装注入 `executor_adapter`；且 `Orchestrator.__init__` 默认为 `None`，导致执行者链路悬空；
   - 5 款执行者适配器（`claude.py`, `codex.py`, `opencode.py`, `antigravity.py`, `kimi.py`）在 `inject_task()` 中仅读取 `task_payload.get("success_criteria")`，未读取 `acceptance_criteria`，导致任务声明的验收标准在 5/7 的适配器中被丢弃。
3. **审查申请单元数据失真 (Codex P1-03 / Claude P1-3 / Pi-Qwen P1-1)**：
   - 前序申请正文完整哈希误植为不存在的 `e06d44c77c688bb715bb997a3cf556bc91f6920f`，导致 `git cat-file` 校验返回 rc=128（fatal: bad object）；
   - 伴随 `.dev.yml` 示例缺少 `dev_manifest.schema.json` 强校验的必填字段。

本轮提审范围 `e06d44c..bdc177e` 对上述问题实施彻底的代码级、测试级与文档级闭环：

### 核心改进明细

1. **检查点防伪多重加固**：
   - **严格路径相对约束**：采用 `doc_path.is_relative_to(self.root.resolve())` 以及 `doc_path.relative_to(self.root.resolve())` 替换 `startswith`，若逃逸出项目根目录立即返回 `None` (Fail-Closed)；
   - **证据提交非空强校验**：升级为 `if not evidence_commit or evidence_commit != latest_commit: return None`，空提交或不匹配立即阻断；
   - **Git Blob 逐字节比对**：在 `GitManager` 增加 `get_file_bytes_at_commit(commit, rel_path)`。在 Git 仓库环境下，当文件在对应 commit 存在时，通过 `git cat-file -p <commit>:<rel_path>` 获取提交时的树对象字节，严格校验其 SHA-256 与磁盘及 manifest 声明一致，严防篡改。
2. **CLI 组合根完整装配与全适配器标准透传**：
   - 在 `LiveAgentDispatcher` 增加 `get_adapter_for_executor(executor_cfg, workspace_path)`，统一执行者适配器实例化；
   - `main.py get_orchestrator()` 自动读取 executor 配置并调用分发器组装注入 `executor_adapter`；
   - `Orchestrator.__init__` 增加自愈逻辑，若传入为空自动兜底实例化，保障内核完整拥有执行者；
   - 将 `claude.py`, `codex.py`, `opencode.py`, `antigravity.py`, `kimi.py` 全部统一为：
     `criteria = task_payload.get("acceptance_criteria") or task_payload.get("success_criteria") or []`，确保验收标准 100% 注入 Prompt。
3. **真实基线校验与 Schema 契约完备**：
   - 本申请文档采用 `git rev-parse HEAD` 生成真实 40 位 SHA `bdc177eaaff577e119093e686f2164bcc133f781`，经 `git cat-file -e` 物理核对；
   - 伴随机器信封经 `macao.core.schema.validate_dev_manifest` 严格校验，100% 符合 JSON Schema。

---

## 2. 变更文件与行数清单 (Git Diff Numstat Verification)

> 依据 Guidelines v1.1 §9，下述变更统计由 `git diff --numstat e06d44c..bdc177e` 严格生成：

| 文件路径 | 变更属性 | 增行 / 删行 | 对应缺陷与模块说明 |
|---|---|---|---|
| `docs/reviews/2026-09-09-disposition-e06d44c.md` | 新增 | +84 / -0 | Round 4 评审处置与缺陷闭环报告 |
| `docs/reviews/2026-09-09-review-request-e06d44c.md` | 修改 | +188 / -0 | Round 4 申请单勘误与哈希校正 |
| `docs/reviews/2026-09-09-review-result-e06d44c-claude.md` | 新增 | +200 / -0 | Claude Round 4 评审报告归档 |
| `docs/reviews/2026-09-09-review-result-e06d44c-codex.md` | 新增 | +70 / -0 | Codex Round 4 评审报告归档 |
| `docs/reviews/2026-09-09-review-result-e06d44c-grok.md` | 新增 | +319 / -0 | Grok Round 4 评审报告归档 |
| `docs/reviews/2026-09-09-review-result-e06d44c-pi-qwen.md` | 新增 | +164 / -0 | Pi-Qwen Round 4 评审报告归档 |
| `docs/reviews/STATUS.md` | 修改 | +37 / -14 | 实时门禁账本对账与状态更新 |
| `docs/reviews/evidence/2026-09-09-e06d44c-claude/probe_e06d44c_claude.py` | 新增 | +126 / -0 | Claude 评审证据复现探针 |
| `docs/reviews/evidence/2026-09-09-e06d44c-codex/reproduce_checkpoint_sibling_escape.py` | 新增 | +119 / -0 | Codex 兄弟目录逃逸复现探针 |
| `docs/reviews/evidence/2026-09-09-e06d44c-codex/reproduce_executor_acceptance_loss.py` | 新增 | +75 / -0 | Codex 执行器 criteria 丢失复现探针 |
| `docs/reviews/evidence/2026-09-09-e06d44c-grok/README.md` | 新增 | +24 / -0 | Grok 证据说明文档 |
| `docs/reviews/evidence/2026-09-09-e06d44c-grok/probe_e06d44c.out.txt` | 新增 | +43 / -0 | Grok 探针执行输出归档 |
| `docs/reviews/evidence/2026-09-09-e06d44c-grok/probe_e06d44c.py` | 新增 | +255 / -0 | Grok 评审复现探针 |
| `docs/reviews/evidence/2026-09-09-e06d44c-pi-qwen/README.md` | 新增 | +40 / -0 | Pi-Qwen 证据说明文档 |
| `docs/reviews/evidence/2026-09-09-e06d44c-pi-qwen/repro_e06d44c_pi_qwen.py` | 新增 | +259 / -0 | Pi-Qwen 6 组审计用例复现脚本 |
| `src/macao/adapter/antigravity.py` | 修改 | +1 / -1 | 增加 acceptance_criteria 读取支持 |
| `src/macao/adapter/claude.py` | 修改 | +1 / -1 | 增加 acceptance_criteria 读取支持 |
| `src/macao/adapter/codex.py` | 修改 | +1 / -1 | 增加 acceptance_criteria 读取支持 |
| `src/macao/adapter/kimi.py` | 修改 | +1 / -1 | 增加 acceptance_criteria 读取支持 |
| `src/macao/adapter/opencode.py` | 修改 | +1 / -1 | 增加 acceptance_criteria 读取支持 |
| `src/macao/cli/main.py` | 修改 | +9 / -1 | get_orchestrator 组合根自动注入 executor 适配器 |
| `src/macao/utils/git_utils.py` | 修改 | +15 / -0 | get_file_bytes_at_commit Git blob 字节提取 |
| `src/macao/workflow/live_dispatcher.py` | 修改 | +47 / -0 | get_adapter_for_executor 执行者适配器实例化 |
| `src/macao/workflow/orchestrator.py` | 修改 | +31 / -5 | is_relative_to 防逃逸、非空 evidence_commit、Git blob 对账、__init__ 兜底 |
| `tests/test_p1_closures_and_regressions.py` | 修改 | +199 / -0 | 新增 5 项针对性回归测试（覆盖兄弟逃逸、空commit、blob校验、组合根、全适配器） |

---

## 3. 质量门禁与机验命令 (Quality Gates & Verification Commands)

专家委员会机验复现可直接执行以下标准命令：

### 3.1 自动化测试套件全量执行
```bash
PYTHONPATH=src python3 -m unittest discover tests
# 预期结果：Ran 170 tests in ~96s, OK (100% 通过，0 failures, 0 errors)
```

### 3.2 针对性回归测试套件执行
```bash
PYTHONPATH=src python3 -m unittest tests/test_p1_closures_and_regressions.py
# 预期结果：Ran 26 tests, OK (含 Round 4 闭环的 5 项新增测试)
```

### 3.3 提交洁净度校验
```bash
git show --check bdc177eaaff577e119093e686f2164bcc133f781
# 预期结果：无任何行尾空白与格式违规，退出码 0
```

### 3.4 Python 语法编译校验
```bash
python3 -m compileall -q src tests
# 预期结果：0 Errors，退出码 0
```

### 3.5 专家复现脚本机验
```bash
# 1. Claude 探针验证（sibling_escape advanced=False, executor is None=False, acceptance criteria reaches prompt=True）
python3 docs/reviews/evidence/2026-09-09-e06d44c-claude/probe_e06d44c_claude.py
# 预期结果：退出码 0，所有缺陷在当前代码中已彻底修复
```

---

## 4. 伴随机器信封样例 (Accompanying Development Checkpoint - EXAMPLE)

> 注：本小节为伴随机器信封 `.macao/.dev.yml` 格式规范快照样例。经过 `macao.core.schema.validate_dev_manifest` 严格校验，包含所有必填字段。

```yaml
version: "1.0"
timestamp: "2026-09-09T23:10:00Z"
task_id: "task-20260909-p1-closures-wire-executor-criteria-blob-check"
checkpoint_ref: "bdc177e"
review_round: 5
status: "ready_for_review"
signal: "EXPLICIT"
executor:
  id: "opencode-dev"
  role: "Lead Orchestrator Architect"
  cli: "opencode"
full_document:
  path: "docs/reviews/2026-09-09-disposition-e06d44c.md"
  evidence_commit: "bdc177e"
  sha256: "877f4bc28fd444cba43e67782ac1129486447e91ccb915e972b6f22c6d07d56c"
development:
  phase: "Phase 3 Orchestrator Hardening & Multi-Agent Dispatch"
  description: "Remediate all P1 blocking findings from Round 4 (e06d44c), enforce sibling escape guard, git blob sha check, executor adapter wiring, and criteria passthrough"
  artifacts:
    - type: "code"
      path: "src/macao/workflow/orchestrator.py"
      changed_lines: 36
      updated: true
    - type: "code"
      path: "src/macao/cli/main.py"
      changed_lines: 10
      updated: true
    - type: "code"
      path: "src/macao/utils/git_utils.py"
      changed_lines: 15
      updated: true
    - type: "code"
      path: "src/macao/workflow/live_dispatcher.py"
      changed_lines: 47
      updated: true
    - type: "code"
      path: "tests/test_p1_closures_and_regressions.py"
      changed_lines: 199
      updated: true
  quality_metrics:
    tests_passed: true
    tests_total: 170
  git:
    latest_commit: "bdc177e"
    branch: "main"
```
