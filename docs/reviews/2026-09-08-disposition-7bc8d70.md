# MACAO 评审处置与缺陷闭环报告（Disposition on Commit 7bc8d70 / Round 3）

- **基线提交 (Baseline Commit)**: `7bc8d70`（`7bc8d7091ba4e39c0b3282492c613817f8d664e9`）
- **申请入口**: [`docs/reviews/2026-09-08-review-request-7bc8d70.md`](2026-09-08-review-request-7bc8d70.md)
- **处置时间**: 2026-09-08
- **对应评审报告**:
  1. [`docs/reviews/2026-09-08-review-result-7bc8d70-codex.md`](2026-09-08-review-result-7bc8d70-codex.md)（Codex：REJECT / 2 项 P1 阻断，3 项 P2）
  2. [`docs/reviews/2026-09-08-review-result-7bc8d70-grok.md`](2026-09-08-review-result-7bc8d70-grok.md)（Grok：NO_APPROVE / 1 项 P1 阻断，3 项 P2）
  3. [`docs/reviews/2026-09-08-review-result-7bc8d70-claude.md`](2026-09-08-review-result-7bc8d70-claude.md)（Claude：NO_APPROVE / 2 项 P1 阻断，4 项 P2）
  4. [`docs/reviews/2026-09-08-review-result-7bc8d70-qwen.md`](2026-09-08-review-result-7bc8d70-qwen.md)（Qwen：不予认证 / 1 项 P1 阻断，2 项 P2）
  5. [`docs/reviews/2026-09-08-review-result-7bc8d70-pi-qwen.md`](2026-09-08-review-result-7bc8d70-pi-qwen.md)（Pi-Qwen：NO_APPROVE / REWORK / 3 项 P1 阻断，4 项 P2）
- **共识仲裁结论**: **全票否决待返工 (REWORK / 5 票否决)**
- **处置状态**: **全部 P1 阻断项与重点 P2 彻底闭环（ALL CLOSED），163 项测试全绿 (100% PASS, 0 FAILED, 0 ERROR)，所有评审证据复现脚本 100% 验证通过**

---

## 一、P1 核心阻断项逐项处置与闭环明细

### P1-1: 检查点防伪门禁对全零哈希、缺失文件、错误 CLI、未绑定字段 Fail-Open
- **评审来源**: Codex P1-7bc8d70-02, Grok P1-1, Claude P1-1, Qwen QW-7BC-P1-1, Pi-Qwen P1-A
- **根因分析**:
  1. `check_development_checkpoint()` 原实现使用了条件合取 `if doc_path.exists() and doc_path.is_file() and doc_sha and doc_sha != "0"*64: ...`，当文件不存在或 SHA 为空/全零时，跳过了 SHA 比对分支，后续任务仍被放行至 `READY_FOR_REVIEW`；
  2. 执行者校验原只检查 `exec_info.get("id")`，未检查 `exec_info.get("cli")`，导致任何冒名 CLI（如 `attacker-cli`）均可借壳通过；
  3. 未校验 `data["task_id"] == task_id`、`data["checkpoint_ref"] == latest_commit`、`full_document["evidence_commit"] == latest_commit`。
- **闭环方案**:
  1. 彻底重构 `Orchestrator.check_development_checkpoint()`，实施 8 重严格 fail-closed 门禁：
     - **任务绑定**: `data.get("task_id") == task_id`，否则直接返回 `None`；
     - **提交绑定**: `data.get("checkpoint_ref") == latest_commit`，否则直接返回 `None`；
     - **正文结构**: `full_document` 必须为 dict，且 `path`、`sha256`、`evidence_commit` 必须非空；
     - **证据提交**: `evidence_commit == latest_commit`，否则直接返回 `None`；
     - **散列格式**: `sha256` 必须匹配 64 位十六进制正则 `^[0-9a-fA-F]{64}$`，且严禁全零 (`"0"*64`)；
     - **物理存在与沙箱越界**: `(self.root / path).resolve()` 必须严格包含于项目根目录内（防路径穿越），且必须物理存在且为常规文件；
     - **字节级校验**: 物理文件实际 SHA-256 必须与声明的 `sha256` 严格逐字节一致；
     - **执行者真实归属**: `executor.id` 与 `executor.cli` 均非空，且必须与 `macao.yaml` 配置（或运行时注入适配器）严格匹配。
  2. 同步更新 `MockAgentAdapter.simulate_produce_dev_manifest()` 自动生成真实审查文档并计算真实 SHA-256，杜绝测试中全零散列假绿。
- **代码变更**: [`src/macao/workflow/orchestrator.py`](../../src/macao/workflow/orchestrator.py), [`src/macao/adapter/mock.py`](../../src/macao/adapter/mock.py)
- **验证与复现脚本比对**:
  - `docs/reviews/evidence/2026-09-08-7bc8d70-grok/probe_checkpoint_p104.py`: 退出码 0，`ALL_MATCH_CLAIM`，0 个 fail-open 漏洞；
  - `docs/reviews/evidence/2026-09-08-7bc8d70-claude/probe_checkpoint_and_adopt.py`: 退出码 0，所有 fail-closed 断言全部通过；
  - `docs/reviews/evidence/2026-09-08-7bc8d70-qwen/repro_7bc8d70_qwen.py`: QW-7BC-P1-1a/b/c 全部 `not-reproduced`（漏洞被彻底封堵）；
  - `tests/test_p1_closures_and_regressions.py:test_codex_p1_04_checkpoint_anti_forgery_fail_closed_battery`: 10 项异常与正常变体全部验证通过。

---

### P1-2: `task adopt` 接受不存在的幽灵基线 commit，违背 UC-11 E1 且绕过状态机白名单
- **评审来源**: Codex P1-7bc8d70-01, Claude P1-2, Pi-Qwen P1-B
- **根因分析**:
  1. `main.py task adopt` 原实现从文件名截取 commit 后未通过 `git cat-file -e <commit>^{commit}` 校验其在本地 Git 仓库中的真实物理存在性，导致指向 `deadbeef` 的伪造申请单被直接采纳；
  2. 原实现直接通过 `store.update_task_state` 强写数据库，绕过了 `TransitionTable` 的合法转移白名单校验，未产生标准 `STATE_TRANSITION_*` 审计事件；
  3. 接管完成后未执行共识评估闭环。
- **闭环方案**:
  1. **UC-11 E1 守卫**: 在 `task adopt` 入口处解析申请单声明的基线 commit，立即执行 `git.commit_exists(checkpoint_ref)` 校验。若物理不存在，立即打印 `UC-11 E1 Error` 并以退出码 1 退出，绝不修改 SQLite 数据库；
  2. **状态机白名单扩展**: 在 `TransitionTable.valid_transitions` 增设标准白名单边：
     - `(AgentState.IDLE, AgentState.CODING): "E1_ADOPT"`
     - `(AgentState.IDLE, AgentState.WAITING_REVIEW): "E2_ADOPT"`
  3. **内核编排下沉**: 在 `Orchestrator` 新增 `adopt_task()` 方法，首先严格校验单一活动任务不变量，创建 `IDLE` 初始任务，通过 `WorkflowFSM.transition()` 推进，并记录 `STATE_TRANSITION_*` 与 `TASK_ADOPTED` 审计事件；
  4. **收敛与共识**: 接管且派发完成后，自动调用 `orch.collect_and_evaluate_consensus()` 收敛任务。
- **代码变更**: [`src/macao/workflow/transitions.py`](../../src/macao/workflow/transitions.py), [`src/macao/workflow/orchestrator.py`](../../src/macao/workflow/orchestrator.py), [`src/macao/cli/main.py`](../../src/macao/cli/main.py)
- **验证与复现脚本比对**:
  - `docs/reviews/evidence/2026-09-08-7bc8d70-claude/probe_checkpoint_and_adopt.py`: `adopt/nonexistent_baseline -> git_cat_file_rc=128, cli_exit=1, stdout_has_success=False`；
  - `tests/test_task_adopt.py`: 6 项测试全部通过（6/6 PASS）。

---

### P1-3: 申请单信封自证矛盾（正文样例载有 64 个零散列占位符）
- **评审来源**: Pi-Qwen P1-C, Qwen QW-7BC-P1-1
- **根因分析**: `docs/reviews/2026-09-08-review-request-7bc8d70.md` 第 192 行载有 `sha256: "0000000000000000000000000000000000000000000000000000000000000000"` 占位符，与申请自称的严格 64 位哈希自相矛盾。
- **闭环方案**:
  1. 替换该占位符为合法的 64 位 SHA-256 散列字符串，消除自证矛盾；
  2. 全库测试套件同步清除非法全零占位符。
- **代码变更**: [`docs/reviews/2026-09-08-review-request-7bc8d70.md`](2026-09-08-review-request-7bc8d70.md)

---

## 二、P2 重点改进项处置明细

### P2-1: Reviewer PTY 交互载荷丢失 `acceptance_criteria`
- **评审来源**: Codex P1-7bc8d70-02, Grok P2-2
- **根因分析**: `LiveAgentDispatcher.dispatch_review_in_worktree` 在组装派发 payload 时未透传 `acceptance_criteria`。
- **闭环方案**:
  - 扩展 `dispatch_review_in_worktree(..., acceptance_criteria=None)`，将验收标准同步注入 `payload["acceptance_criteria"]` 与 `payload["review_context"]["acceptance_criteria"]`；
  - `main.py` 派发时从活跃任务元数据中读取并透传。
- **代码变更**: [`src/macao/workflow/live_dispatcher.py`](../../src/macao/workflow/live_dispatcher.py), [`src/macao/cli/main.py`](../../src/macao/cli/main.py)

---

### P2-2: Claude 会话在缺失 `cwd` 时存在潜在漏判
- **评审来源**: Grok P1-2, F-26
- **根因分析**: 会话 JSONL 前 50 行若无 `cwd`，原实现未显式跳过。
- **闭环方案**:
  - `SessionLocator._find_claude_sessions` 增加严格断言 `if not session_cwd: continue`，无真实工作目录记录的外部孤立会话一律 Fail-Closed 丢弃。
- **代码变更**: [`src/macao/adapter/session_locator.py`](../../src/macao/adapter/session_locator.py)

---

### P2-3: 依据 Guidelines v1.1 §5.2 在 `STATUS.md` 固化常设「已知简化」表
- **评审来源**: Grok P1-1, Pi-Qwen §0
- **根因分析**: 阶段性架构设计（如单仓 In-repo 审查模式、CI 命令允许为 null）与代码缺陷未作有效隔离，导致多轮重复争论。
- **闭环方案**:
  - 严格依据 `docs/MACAO_REVIEW_GUIDELINES.md` v1.1 §5.2 规范，在 `docs/reviews/STATUS.md` 建立常设已知简化表，详列现状、接受理由、接受轮次、生产化转正要求与明确的 expiry 字段（如 v3.0, v2.6.0-rc1）。
- **代码变更**: [`docs/reviews/STATUS.md`](STATUS.md)

---

### P2-4: `doctor` 在 `macao.yaml` 缺失时未退出非零码
- **评审来源**: Pi-Qwen P2-C, V08
- **根因分析**: `main.py doctor` 原先在配置缺失时仅打印提示，未置 `has_error = True`，导致进程以退出码 0 退出。
- **闭环方案**:
  - 缺失 `macao.yaml` 时置 `has_error = True`，严格退出码 2。
- **代码变更**: [`src/macao/cli/main.py`](../../src/macao/cli/main.py)

---

## 三、验证与质量门禁审计

1. **自动化单元与集成测试全量执行**:
   - `python3 -m unittest discover tests` $\rightarrow$ **163/163 PASS**（Ran 163 tests, 0 failures, 0 errors）
2. **专家复现脚本机验**:
   - `docs/reviews/evidence/2026-09-08-7bc8d70-grok/probe_checkpoint_p104.py`: **ALL_MATCH_CLAIM (PASS)**
   - `docs/reviews/evidence/2026-09-08-7bc8d70-claude/probe_checkpoint_and_adopt.py`: **100% Fail-Closed Verified (PASS)**
   - `docs/reviews/evidence/2026-09-08-7bc8d70-qwen/repro_7bc8d70_qwen.py`: **P1-1 漏洞全部修复，其他闭环项全部 CONFIRMED**
3. **格式与空白检查**:
   - `git diff --check` $\rightarrow$ **0 Errors**（无任何行尾空白与格式违规）
4. **Schema 契约逐字节对称性**:
   - `docs/schemas/` 与 `src/macao/schemas/` 8 份契约文件 100% 对称一致。
