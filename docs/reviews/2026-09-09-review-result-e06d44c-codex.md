# Commit e06d44c 检查点防伪、场景 C 与 Provider 扩展复审结论

- **评审日期**：2026-09-09
- **评审范围**：`7bc8d70..e06d44c`；实际受审对象为 `e06d44cb31a0dbcbe199e6bb124430e9701e087f`。
- **评审基准**：`docs/MACAO_REVIEW_GUIDELINES.md` v1.1、`docs/MACAO_PRD_v2.md`、UC-2、UC-3、UC-11。
- **结论**：**REJECT**。不授予 **L3 / PG-2**；**L4 / PG-3 为 UNKNOWN，不能准入**。

## 已对齐 / 已确认项

1. 实际 commit 的提交级格式检查通过：`git show --check e06d44cb31a0dbcbe199e6bb124430e9701e087f` 返回 0。
2. 在从该 commit 导出的独立临时副本中，`PYTHONPATH=src python3 -m unittest discover tests` 返回 0；`tests/test_schema.py` 的 8 项契约测试及 `compileall -q src tests` 通过。
3. 申请所列的旧检查点反例已封闭：Grok 的 `probe_checkpoint_p104.py`、Claude 的 `probe_checkpoint_and_adopt.py` 均显示全零 SHA、缺失文件、错误 executor CLI 和幽灵 baseline 被拒绝；Qwen 脚本也将前三项旧 P1 报为 `not-reproduced`。
4. `adopt_task()` 现通过 `E1_ADOPT` / `E2_ADOPT` 调用 FSM，且 CLI 对待评审接管的 baseline 执行 `commit_exists()` 检查（`src/macao/workflow/orchestrator.py:258-324`，`src/macao/cli/main.py:583-636`）。

## P0：必须先解决

无新增 P0。

## P1：发布/进入下一阶段前应修正

### P1-e06d44c-01：检查点正文的路径与 Git 证据提交仍可伪造

- **证据（CODE/SIM，VERIFIED）**：申请声称正文必须位于项目根目录内且与 `evidence_commit` 严格绑定（`docs/reviews/2026-09-09-review-request-e06d44c.md:36-44`），UC-3 也要求正文的路径与 SHA 校验失败即拒绝（`docs/usecases/UC3-dev-checkpoint.md:51-53`）。实际实现把路径归属判断写成字符串前缀比较（`src/macao/workflow/orchestrator.py:405-409`）；例如 `<root>-sibling/file` 以 `<root>` 开头，却不在 `<root>` 内。`evidence_commit` 也只与 manifest 的 `latest_commit` 做字符串比较（`:399-400`），没有验证 `path` 的 Git blob 存在于该 commit，实际 SHA 则读取当前工作树（`:411-413`）。
- **复现结果（SIM，VERIFIED）**：归档脚本在独立临时 Git 仓库中构造两个 schema 合法的显式 checkpoint：(1) 指向与项目根同名前缀的兄弟目录；(2) 指向 HEAD 之后才写入、因而根本不存在于 `evidence_commit` 的未跟踪正文。两者都进入 `READY_FOR_REVIEW`。详见 [reproduce_checkpoint_sibling_escape.py](evidence/2026-09-09-e06d44c-codex/reproduce_checkpoint_sibling_escape.py)。
- **影响**：执行者或错误自动化可把根目录外、未提交或事后替换的正文绑定到旧 checkpoint；`evidence_commit` 成为无真实性约束的标签，审计对象不再等于被评审对象。这由正常 `task checkpoint` 生产路径可达，属于 P1。
- **处置**：以 `doc_path.relative_to(self.root.resolve())` 做路径包含判断；要求 `evidence_commit` 为存在的完整 commit，并读取 `git show <evidence_commit>:<relative_path>` 的 blob，校验该 blob SHA 与 manifest 相同。若运行时工作树文件仍被用作显示，也必须逐字节等于该 blob；否则拒绝转移。
- **Owner / Due date / Resolution commit / Status**：Architecture & Engineering Team / 下次复审前 / TBD / **OPEN**。

### P1-e06d44c-02：生产 CLI 未创建 executor adapter，任务创建不会派发执行者

- **证据（CODE/SIM，VERIFIED）**：UC-2 要求 E1 后向 executor 投递包含验收标准的 `DEVELOPMENT_STARTED`（`docs/usecases/UC2-task-create.md:50-56`）。但所有 CLI 任务入口使用的 composition root 仅把配置传给 `Orchestrator`，没有构造或注入 `executor_adapter`（`src/macao/cli/main.py:179-189`）。`task create` 虽调用 `start_task()`（`:459-470`），后者却只在 `self.executor` 非空时才启动并注入任务（`src/macao/workflow/orchestrator.py:207-215`）。因此正常 CLI 创建的任务会进入 `CODING` 和写出消息记录，但不会启动或通知配置的 executor。
- **复现结果（SIM，VERIFIED）**：归档脚本使用默认有效 `macao.yaml` 调用生产 `get_orchestrator()`；结果 `orchestrator.executor is None`。同一脚本还证明，一旦将 Claude、Codex、OpenCode、Antigravity 或 Kimi adapter 接入，这五个 adapter 又会丢弃真实字段 `acceptance_criteria`，因为它们读取的是不存在的 `success_criteria`。详见 [reproduce_executor_acceptance_loss.py](evidence/2026-09-09-e06d44c-codex/reproduce_executor_acceptance_loss.py)。
- **影响**：用户看到“Assigned Executor”与下一步提示，但没有实际执行进程收到任务；工作流会停在 `CODING`，Provider 扩展也不能构成可用功能。这是标准 `macao task create` 路径，定级 P1。
- **处置**：在 CLI composition root 按 `team.executor` 的 `cli`、`adapter`、`provider` 和工作区构造唯一 executor adapter，注入 `Orchestrator`，并以黑盒 CLI 测试断言其接收到完整 `task_description` 与 `acceptance_criteria`。同时统一所有 executor adapter 使用 `acceptance_criteria`（可兼容回退 `success_criteria`），避免接线后再次静默丢失验收条件。
- **Owner / Due date / Resolution commit / Status**：Architecture & Engineering Team / 下次复审前 / TBD / **OPEN**。

### P1-e06d44c-03：本轮申请的 commit 与伴随信封无法作为可验证审计证据

- **证据（DOC/SPEC，VERIFIED）**：申请第 7 行把不存在的 `e06d44c77c688bb715bb997a3cf556bc91f6920f` 标为“完整 SHA”；`git cat-file -t` 对该对象失败，实际完整 SHA 是本报告范围所列值。因此申请第 118 行的验证命令不能执行。其 YAML 样例（`docs/reviews/2026-09-09-review-request-e06d44c.md:143-188`）也缺少 schema 必填的 `development.git.latest_commit` 和 `development.quality_metrics.tests_passed`（`src/macao/schemas/dev_manifest.schema.json:42-83`）；独立 `validate_dev_manifest()` 返回 `False`。样例的正文 SHA `d599...6222` 亦不等于文件实际 SHA-256 `e13b9bdf0741e354b9e3ac2eeb2c7dadddf05ef8827c24972cd5d2d6e4a2b695`。
- **影响**：Guidelines §2.1 的 L1 前提要求所有 YAML 示例可解析且合法；错误的完整 commit 与摘要信封使本轮“已消除占位符、可逐字节复现”的审计声明不能成立。此类自证矛盾已在上一轮按 P1 处置，不能以新的错误引用重新申请 L3/L4。
- **处置**：以 `git rev-parse --verify <full_sha>^{commit}` 生成并冻结完整 SHA；从真实、已包含在对应 commit 的 `.dev.yml` 自动提取/验证示例，或删除非真实“伴随信封”。在提交申请前以 `validate_dev_manifest()` 和 `sha256sum` 作为 CI 检查。
- **Owner / Due date / Resolution commit / Status**：Architecture & Engineering Team / 下次复审前 / TBD / **OPEN**。

## P2/P3：可延期但需登记

### P2-e06d44c-01：`task checkpoint --auto` 仍由编排器创作正文和 `.dev.yml`

- **证据（CODE/DOC，VERIFIED）**：`src/macao/cli/main.py:722-778` 在 `--auto` 下写入 review request 正文及 `.macao/.dev.yml`。UC-3 则规定全文和信封均由执行者独占写入，编排器不得读、写或摘要正文（`docs/usecases/UC3-dev-checkpoint.md:7,27-31`）。
- **处置**：移除正文/信封自动生成；若保留草稿助手，必须不具 `EXPLICIT` 信号、不能驱动状态转移，并在 `STATUS.md` 依 Guidelines §8.3 完整登记风险接受信息。

## L4 / PG-3 评定

**OPS：UNKNOWN。** 申请没有针对 Guidelines §7.2 的 10 项必测矩阵逐项给出状态、可重放证据和真实人工接管记录；尤其没有真实 provider CLI、PTY 断开、崩溃恢复、并发写、磁盘写失败及 `macao override resolve` 的用户可见实机演练。即使上述 P1 修复，也不得据此申请 L4 / PG-3。

## 建议的闭环顺序与验收标准

1. 先修 P1-e06d44c-01：新增兄弟目录、未跟踪正文、正文 blob 与 `evidence_commit` 不一致的三条否定回归，全部断言状态不离开 `CODING`。
2. 修 P1-e06d44c-02：从 `macao task create` 黑盒入口验证恰好一个配置 executor 被启动并收到原始验收列表；覆盖五个现有 adapter 的字段兼容性。
3. 由 CI 生成申请中的完整 SHA 和样例 SHA，并对所有 Markdown YAML 块做 schema 验证后，再申请 L3。
4. P1 为零后，逐项完成 Guidelines §7.2 的 OPS 矩阵与人工接管实机留痕，才可申请 L4。

## 复现脚本与命令

- [reproduce_checkpoint_sibling_escape.py](evidence/2026-09-09-e06d44c-codex/reproduce_checkpoint_sibling_escape.py)：验证 P1-e06d44c-01；受审 commit `e06d44cb31a0dbcbe199e6bb124430e9701e087f`；前提为 Linux、Python 3.10+、Git、PyYAML/jsonschema，无网络和厂商 CLI；最后执行于 2026-09-09 Asia/Taipei。命令：`PYTHONPATH=src python3 docs/reviews/evidence/2026-09-09-e06d44c-codex/reproduce_checkpoint_sibling_escape.py`。
- [reproduce_executor_acceptance_loss.py](evidence/2026-09-09-e06d44c-codex/reproduce_executor_acceptance_loss.py)：验证 P1-e06d44c-02 与 P2-e06d44c-01；同一 commit 与环境前提；最后执行于 2026-09-09 Asia/Taipei。命令：`PYTHONPATH=src python3 docs/reviews/evidence/2026-09-09-e06d44c-codex/reproduce_executor_acceptance_loss.py`。

## Reviewer 自审记录

- 本次在实际受审 commit 的独立导出副本运行测试与静态检查；未把申请作者自述或当前工作区状态作为提交级证据。
- 已按 Guidelines §8.2 检查可达性：adapter 字段丢失本身当前未由 CLI 注入，故与其根因“CLI 未创建 executor”一并复现；其接线后的字段错误单列为 P2，而非重复夸大为第二项 P1。
