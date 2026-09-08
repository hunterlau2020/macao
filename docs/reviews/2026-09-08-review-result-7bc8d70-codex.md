# Commit 7bc8d70 综合编排闭环与评审方法论 v1.1 复审结论

- **评审日期**：2026-09-08
- **评审范围**：`961bcfe..7bc8d70`（实现整改提交 `48eea58` 与方法论提交 `7bc8d70`）
- **评审基准**：`docs/MACAO_REVIEW_GUIDELINES.md` v1.1、`docs/MACAO_PRD_v2.md`、UC-3、UC-11
- **结论**：**REJECT**。不授予 **L3 / PG-2**；**L4 / PG-3 为 UNKNOWN，不能准入**。

## 已确认项

1. `7bc8d70` 的提交级格式检查通过：`git show --check 7bc8d7091ba4e39c0b3282492c613817f8d664e9` 返回 0。
2. 在从 `7bc8d70` 导出的独立临时副本中，`tests/test_task_adopt.py`、`tests/test_p1_closures_and_regressions.py`、`tests/test_pi_and_session_locator.py` 共 **34** 项测试通过；`compileall -q src tests` 通过。
3. Pi/Cursor 已注册到 `LiveAgentDispatcher.get_adapter_for_reviewer()`，Pi executor 已读取 `acceptance_criteria`（`src/macao/workflow/live_dispatcher.py:202-234`、`src/macao/adapter/pi.py:107-135`）。这解决了上一轮的“零接线”问题。
4. v1.1 新增的验证参照系、复现脚本归档、可达性定级、反例纪律和 L4 OPS 矩阵，对后续评审有实际约束价值。

## P0：必须先解决

无新增 P0；下列 P1 已足以阻断所有申请门禁。

## P1：发布/进入下一阶段前应修正

### P1-7bc8d70-01：`task adopt` 接受不存在的评审基线、绕过 FSM，且无法完成已接管的评审闭环

- **证据（CODE/SIM，VERIFIED）**：UC-11 要求申请单指向不存在 commit 时原子拒绝（`docs/usercases/UC11-scenarioc-inflight-adoption.md:95-99`），并要求接管以 `E2_ADOPT` 记录合法 FSM 前序和审计（`:64-70, 102-109`）。但 CLI 仅从文件名推导 baseline，随后直接使用它（`src/macao/cli/main.py:514-545`），没有 `git commit_exists`/拓扑校验；并以 `StateStore.create_task()` 和 `StateStore.update_task_state()` 直接写入 `WAITING_REVIEW`（`:590-615`），绕过 `WorkflowFSM.transition()` 的状态表校验和 `STATE_TRANSITION_*` 审计（`src/macao/workflow/fsm.py:22-70`）。
- **复现结果（SIM，VERIFIED）**：归档脚本创建合法临时 Git 仓库和名为 `*-review-request-deadbeef.md` 的申请单；`macao task adopt --no-review` 返回 0，创建 `task-adopt-deadbeef` 并写入 `WAITING_REVIEW`，而 `git cat-file -e deadbeef^{commit}` 返回非零。脚本还验证该不合法 checkpoint 被持久化。
- **闭环缺口**：默认 `--review` 在派发循环后直接返回（`main.py:620-650`），没有收票/计票；`--no-review` 的提示要求用户运行 `task checkpoint --review`（`:649-651`），但 checkpoint 仅接受 `CODING`/`REWORK`（`workflow/orchestrator.py:255-257`）。因此已接管任务可停在 `WAITING_REVIEW`，无可达的收敛入口。`--from-request` 也只验证路径存在、却不解析该文件的 baseline（`main.py:522-530`）。
- **影响**：任何伪造或过期文件名可制造没有真实审查对象的活动任务；状态机与审计链被绕过，且合法场景 C 也可能永久挂起。这是在线 CLI 可达的状态机/审计 P1。
- **处置**：将 adopt 下沉为 Orchestrator/FSM 的专用、白名单化 transition；解析并验证指定申请单、commit 存在性、目标分支关系、round、已交票集合；原子登记 E2_ADOPT 和审计；接入后只派发 `R_missing`，再通过正式收票/共识入口推进。为不存在 ref、`--from-request` 非最新申请、重复 adopt、`--no-review` 后续派发和全员已交票分别添加隔离集成反例。
- **Owner / Due date / Resolution commit / Status**：Architecture & Engineering Team / 下次复审前 / TBD / **OPEN**。

### P1-7bc8d70-02：检查点“防伪”仍对缺失全文、全零 hash、错误 CLI 和错绑字段 fail-open

- **证据（CODE/DOC，VERIFIED）**：UC-3 要求全文存在、字节级 SHA-256 匹配、`executor.id`/归属正确、评审对象与新 commit 绑定；任一失败即拒绝（`docs/usercases/UC3-dev-checkpoint.md:7, 51-57, 80-98`）。不过 schema 仅要求 `full_document` 三字段为字符串（`src/macao/schemas/dev_manifest.schema.json:33-40`）。运行时代码只在“文件存在、为普通文件、hash 非全零”时才比较 SHA（`src/macao/workflow/orchestrator.py:287-300`）：缺失文件与全零 hash 均继续放行；它只校验 executor `id` 而不校验 `cli`（`:302-308`），也不比对 manifest 的 `task_id`、`checkpoint_ref`、`evidence_commit`。
- **复现结果（SIM，VERIFIED）**：归档脚本提交一个 schema 合法 manifest：`task_id` 与活动任务不同、`checkpoint_ref=deadbeef`、`full_document.path` 不存在、hash 为 64 个 `0`、`executor.cli=attacker-cli`，但 `development.git.latest_commit` 为真实 HEAD。`check_development_checkpoint()` 返回状态变更，任务进入 `READY_FOR_REVIEW`。
- **附加矛盾**：`task checkpoint --auto` 仍由编排 CLI 创建评审正文和 `.dev.yml`（`src/macao/cli/main.py:689-745`），与 UC-3 的“全文作者 = 执行者、编排器永不生成此文件”（`UC3:27-30`）相冲突；该 CLI 从不存在的 `orchestrator.config['executor']` 取配置，退回 `dev-claude/claude-code`（`main.py:695-697`），进一步放大归属错误。
- **影响**：攻击者或错误自动化可把伪造的内容指针、身份和审查对象推进至评审状态，破坏审计锚点及“评审对象 = 合并对象”不变量。该路径由正常 `task checkpoint` 调用到达，定级为 P1。
- **处置**：使 Schema 约束 SHA-256 格式和最小 commit 前缀；在转移前无条件验证全文在允许目录内且存在、实际 hash 相等、`task_id`/两个 checkpoint ref/round/evidence commit 与任务和 Git 一致、executor 的 id 与 cli 均匹配配置；初始轮也验证新 commit 拓扑。移除正文自动生成，或把它降为不具 `EXPLICIT` 信号且绝不能触发状态转移的草稿辅助。为本条全部反例加入正式回归。
- **Owner / Due date / Resolution commit / Status**：Architecture & Engineering Team / 下次复审前 / TBD / **OPEN**。

## P2/P3：可延期但需登记

### P2-7bc8d70-01：方法论 v1.1 的“已知简化表”尚未真正落地

- **证据（DOC，VERIFIED）**：v1.1 §5.2 要求在 PRD 附录或 `docs/reviews/STATUS.md` 维护带接受理由、生产化要求和 expiry 的常设表；当前 `MACAO_PRD_v2.md` 与 `STATUS.md` 没有该表。申请文件 §4.1 的两条“已知局限”也没有该规范要求的有效期和转正条件。
- **处置**：在所选唯一位置建立表，补齐每行字段与双人审阅记录；在形成前不把任何“阶段性边界”视为自动豁免。
- **Owner / Due date / Resolution commit / Status**：Architecture & Engineering Team / 下次文档复审前 / TBD / **OPEN**。

## L4 / PG-3 评定

**OPS：UNKNOWN。** 本轮申请未按 v1.1 §7.2 的 10 行必测矩阵逐项给出 `VERIFIED/PARTIALLY_VERIFIED/CONTRADICTED/NOT_APPLICABLE` 结论、可重放证据和人工接管记录。即使 P1 修复，也仍须完成真实 CLI/PTy、超时、崩溃恢复、并发写入、磁盘写失败、清理以及 `macao override resolve` 人工交互的 OPS 演练，才可申请 L4。

## 建议闭环顺序与验收标准

1. 先以 P1-7bc8d70-01 修复 Scenario C 的真实性、合法 FSM 转移与可达收敛路径，再以 P1-7bc8d70-02 封闭 checkpoint 的全部引用/身份/拓扑校验。
2. 使用归档脚本中的两个反例作为永久回归，再新增 `--from-request`、重复 adopt、无效 commit、无效 hash、缺失文件、身份/CLI 错配和初始轮旧 commit 的黑盒 CLI 测试。
3. 在 `7bc8d70` 后续干净 checkout 中重新运行全量测试、提交级 `git show --check`、专项反例；申请文件的伴随 manifest 必须填写真实 SHA-256，而非全零占位。
4. 完整提交 v1.1 §7.2 OPS 矩阵和人工接管实机记录后，才可复审 L4/PG-3。

## 复现脚本与命令

- **脚本**：[reproduce_fail_closed_gaps.py](evidence/2026-09-08-7bc8d70-codex/reproduce_fail_closed_gaps.py)
- **验证 issue**：P1-7bc8d70-01、P1-7bc8d70-02
- **受审 commit**：`7bc8d7091ba4e39c0b3282492c613817f8d664e9`
- **环境前提**：Linux、Python 3.10+、项目依赖（PyYAML/jsonschema）、Git；无网络、无真实 CLI 或账号需求。
- **执行命令**：`PYTHONPATH=src python3 docs/reviews/evidence/2026-09-08-7bc8d70-codex/reproduce_fail_closed_gaps.py`
- **最后实际执行**：2026-09-08 Asia/Taipei；输出：`REPRODUCED: nonexistent adoption baseline and unbound checkpoint were accepted`。脚本使用 `tempfile.mkdtemp()` 创建并清理临时 Git 仓库与状态库。

## Reviewer 自审记录

- 已按 v1.1 §3.4 在提交级使用 `git show --check`，并在独立导出副本运行专项测试；未将申请人自报或当前工作区状态当作提交测试证据。
- 已检查本轮新增接线、字段读取路径、P1 可达性和 L4 OPS 证据；每个 P1 均有路径/行号和可重放反例。
