# MACAO 评审处置与缺陷闭环报告（Disposition on Commit bdc177e / Round 5）

- **基线提交 (Baseline Commit)**: `bdc177e` (`bdc177eaaff577e119093e686f2164bcc133f781`)
- **申请入口**: [`docs/reviews/2026-09-09-review-request-bdc177e.md`](2026-09-09-review-request-bdc177e.md)
- **处置时间**: 2026-09-10
- **对应评审报告**:
  1. [`docs/reviews/2026-09-09-review-result-bdc177e-claude.md`](2026-09-09-review-result-bdc177e-claude.md)（Claude：YES_APPROVE / 0 项 P0，0 项 P1，1 项 P2：未跟踪证据文件绕过 Git blob 校验）
  2. [`docs/reviews/2026-09-09-review-result-bdc177e-grok.md`](2026-09-09-review-result-bdc177e-grok.md)（Grok：YES_APPROVE / 0 项 P0，0 项 P1，3 项 P2：未跟踪证据文件、未知 executor CLI、审查员提示词缺失验收准则）
  3. [`docs/reviews/2026-09-09-review-result-bdc177e-pi-qwen.md`](2026-09-09-review-result-bdc177e-pi-qwen.md)（Pi-Qwen：YES_APPROVE / 0 项 P0，0 项 P1，2 项绑定条件：`immutable=1` 陈旧读与未跟踪证据跳过边界须按 §8.3-2 登记）
  4. [`docs/reviews/2026-09-10-review-result-bdc177e-codex.md`](2026-09-10-review-result-bdc177e-codex.md)（Codex：REJECT / 2 项 P1：P1-bdc177e-01 未存在于 `evidence_commit` 的正文仍可推进 checkpoint，P1-bdc177e-02 未知 executor CLI 静默降级为空且 `--no-probe` 创建 CODING 任务；1 项 P2：`task checkpoint --auto` 作者边界）
- **共识仲裁结论**: **待返工 (REWORK / 3 票批准，1 票否决，遵循 Fail-Closed 严谨闭环原则实施返工整改)**
- **处置状态**: **全部 P1 阻断项彻底闭环（ALL CLOSED），2 项 P2 绑定条件在 `STATUS.md` 完整登记已知简化，全量 173 项测试全绿**

---

## 一、P1 核心阻断项逐项处置与闭环明细

### P1-bdc177e-01: 未存在于 `evidence_commit` 的正文仍可推进 checkpoint（未提交/未跟踪证据绕过 Git Blob 校验）
- **评审来源**: Codex P1-bdc177e-01, Claude P2-1, Grok P2-1, Pi-Qwen 条件②
- **根因分析**:
  - `src/macao/workflow/orchestrator.py:430-442` 原实现为：
    ```python
    if self.git and self.git.is_git_repository():
        rel_posix = rel_doc_path.as_posix()
        code, _, _ = self.git._run("cat-file", "-e", f"{latest_commit}:{rel_posix}")
        if code == 0:
            blob_bytes = self.git.get_file_bytes_at_commit(latest_commit, rel_posix)
            ...
    ```
  - 当证据文档在本地磁盘存在但从未加入声明的 commit（未跟踪或事后新建文件）时，`git cat-file -e` 返回非零（rc=128），导致整段 Git blob 内容校验被跳过。系统仅凭借当前工作树磁盘文件的 SHA-256 即可判定有效并推进至 `READY_FOR_REVIEW`，破坏了 UC-3 关于证据文档与物理提交强绑定的审计不变量。
- **闭环方案**:
  1. **Git 仓库环境下强制物理归档校验 (Fail-Closed)**：
     - 若在 Git 仓库内，`git cat-file -e <latest_commit>:<rel_posix>` 必须返回 0；若返回非零，直接 `return None` 拒绝推进；
     - `self.git.get_file_bytes_at_commit(latest_commit, rel_posix)` 必须成功返回二进制内容（非 None）；若返回 None，直接 `return None`；
     - 计算该 blob 的 SHA-256 哈希值，必须与磁盘物理文件 SHA 及 manifest 声明的 `full_document.sha256` 逐字符相同，任一不符直接 `return None`；
  2. **端到端工作流与测试固化**:
     - `macao task checkpoint --auto` 在生成 `docs/reviews/req.md` 后自动暂存并提交至 Git，使 `head_commit` 天然包含该证据文件；
     - `LiveWorkflowRunner` 与 `ControlledE2ERunner` 在执行 feature commit 时同步提交评审申请文档，确保工作树 SHA、提交 blob SHA、manifest SHA 三者绝对一致。
- **代码变更**:
  - [`src/macao/workflow/orchestrator.py`](../../src/macao/workflow/orchestrator.py)
  - [`src/macao/cli/main.py`](../../src/macao/cli/main.py)
  - [`src/macao/workflow/live_runner.py`](../../src/macao/workflow/live_runner.py)
  - [`src/macao/workflow/e2e_runner.py`](../../src/macao/workflow/e2e_runner.py)
  - [`src/macao/adapter/mock.py`](../../src/macao/adapter/mock.py)
- **测试覆盖**:
  - `tests/test_p1_closures_and_regressions.py::test_checkpoint_uncommitted_or_untracked_evidence_rejected` (PASS，覆盖未跟踪文件、后续提交文件两种拒止场景及已提交放行场景)
  - 验证 Codex 归档复现脚本 `docs/reviews/evidence/2026-09-10-bdc177e-codex/reproduce_remaining_fail_closed_gaps.py`：原复现路径已被物理拦截，断言保持 `CODING`。

---

### P1-bdc177e-02: 未知 executor CLI 被静默降级为空执行者，`--no-probe` 仍可创建 CODING 任务
- **评审来源**: Codex P1-bdc177e-02, Grok P2-2
- **根因分析**:
  - `src/macao/workflow/live_dispatcher.py` 的 `get_adapter_for_executor()` 对未知 CLI 类型直接 `return None`，而审查员工厂则抛出 `ValueError`，两者行为不对称；
  - `macao.cli.main.get_orchestrator()` 将返回的 `None` 传给 `Orchestrator`；而 `Orchestrator.__init__` 的配置自愈分支对同一未知 CLI 再次得到 `None`，最终导致 `orchestrator.executor is None`；
  - 当用户使用公开选项 `macao task create --no-probe ...` 时，跳过了探活预检，直接调用 `orchestrator.start_task()`，由于 `self.executor is None`，任务成功创建并持久化为 `CODING` 状态写入 `state.db`，但实际没有任何执行者可以接管或推进任务，造成执行者永久悬空。
- **闭环方案**:
  1. **工厂层 Fail-Closed 异常收敛**:
     - `LiveAgentDispatcher.get_adapter_for_executor()` 对无法识别的 CLI 类型严格抛出 `ValueError(f"Unknown or unsupported CLI executor type: '{cli_type}' (Fail-closed)")`，与审查员工厂保持严格对称；
  2. **组合根防御性拦截与零状态污染**:
     - `main.py get_orchestrator()` 捕获 `ValueError`，向用户打印清晰的配置错误提示 `[bold red]Configuration Error:[/bold red] ...`，并立即通过 `sys.exit(1)` 退出；
     - 确保在非法配置下阻断一切下游逻辑，`state.db` 保持 0 写入、0 任务生成、0 事务半行。
- **代码变更**:
  - [`src/macao/workflow/live_dispatcher.py`](../../src/macao/workflow/live_dispatcher.py)
  - [`src/macao/cli/main.py`](../../src/macao/cli/main.py)
- **测试覆盖**:
  - `tests/test_p1_closures_and_regressions.py::test_task_create_no_probe_unknown_executor_fails_closed` (PASS，黑盒验证未知 CLI 触发非零退出、输出包含未知 CLI 名称、`state.db` 0 任务创建)。

---

## 二、P2 建议项与绑定条件处置明细

### 1. Grok P2-3: 七款 AI CLI 适配器 REVIEW_REQUEST 模板补齐验收标准
- **评审来源**: Grok P2-3
- **处置**:
  - 针对 `claude.py`, `codex.py`, `opencode.py`, `antigravity.py`, `kimi.py`, `pi.py`, `cursor.py` 全部 7 款适配器，在 `inject_task()` 的审查员分支（Reviewer）统一格式化并注入 `Acceptance Criteria`：
    ```python
    criteria = task_payload.get("acceptance_criteria") or task_payload.get("success_criteria") or []
    criteria_section = f"\nAcceptance Criteria:\n{criteria}\n" if criteria else ""
    ```
  - 无论 Agent 充当 Executor 还是 Reviewer，均能完整感知该任务的验收标准准则。
- **测试覆盖**:
  - `tests/test_p1_closures_and_regressions.py::test_all_adapters_reviewer_prompt_includes_acceptance_criteria` (PASS，覆盖全部 7 款适配器的审查员 Prompt 格式化断言)。

### 2. Pi-Qwen 条件①: `immutable=1` 陈旧读（Stale Read under Live WAL）登记
- **评审来源**: Pi-Qwen 条件① (H07)
- **处置**:
  - 依据 Guidelines v1.1 §5.2 / §8.3-2，在 `docs/reviews/STATUS.md` 常设「已知简化」表中正式登记该已知行为：探活只读连接为了 0 物理副作用使用 `immutable=1`，在写者持有未 checkpoint WAL 时可能读取历史事务快照，决策路径（RW 连接）不受影响；计划在 `v2.6.0` 增加 WAL 状态提示。

### 3. Codex P2-bdc177e-01: `task checkpoint --auto` 作者边界登记
- **评审来源**: Codex P2-bdc177e-01, Pi-Qwen 条件②
- **处置**:
  - 依据 Guidelines v1.1 §5.2，在 `docs/reviews/STATUS.md` 登记 `--auto` 辅助骨架生成机制为开发与演练阶段的已知简化，正式生产环境由执行者自主生成；计划在 `v2.6.0` 将 `--auto` 生成的信封默认设为 `signal: IMPLICIT` 或草稿态。

---

## 三、质量门禁审计与验证结果

1. **自动化单元与集成测试全量执行**:
   - `python3 -m unittest discover tests` $\rightarrow$ **173 项测试全绿 (100% PASS, 0 FAIL, 0 ERROR)**，耗时 ~71s。
2. **专项回归套件验证**:
   - `python3 -m unittest tests/test_p1_closures_and_regressions.py` $\rightarrow$ **29/29 PASS**。
3. **JSON Schema 8 份逐字节对称性与校验**:
   - `python3 -m unittest tests.test_schema` $\rightarrow$ **8/8 PASS**。
4. **Python 模块编译检查**:
   - `python3 -m compileall -q src tests` $\rightarrow$ **0 Errors**。
5. **专家复现脚本验证**:
   - Codex 归档复现脚本 `docs/reviews/evidence/2026-09-10-bdc177e-codex/reproduce_remaining_fail_closed_gaps.py` 运行证明原缺陷不再发生。
