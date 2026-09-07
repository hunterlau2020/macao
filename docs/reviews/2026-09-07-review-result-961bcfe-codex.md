# Commit 961bcfe 综合编排与动态探活体系复审结论

- **评审日期**：2026-09-07
- **评审对象**：`961bcfe`；申请文件 `docs/reviews/2026-09-07-review-request-961bcfe.md`
- **基准**：`docs/MACAO_REVIEW_GUIDELINES.md`、`docs/MACAO_PRD_v2.md`、UC-3、UC-11
- **范围说明**：仅审查该 commit。工作区中其后的未提交改动，以及其他 reviewer 的未跟踪报告，均未计入本结论。
- **结论**：**REJECT**。不授予 **L3 SCENARIO-VERIFIED / PG-2**；**L4 / PG-3 为 UNKNOWN，不能准入**。

## 已确认项

1. `TeamProber` 对 `dry_run=True` 已在 `src/macao/workflow/prober.py:244-247, 788-813` 跳过审计日志写入；P1-1 的该项局部整改可静态确认。
2. 探活可达性计算已把最少胜方席位、席位 quorum、权重 quorum 作联合条件（`src/macao/workflow/prober.py:765-788`）；针对席位/权重不足的专项测试也已提交。
3. `task create --force` 会经 E10 取消当时的活动任务，且 CLI 端将换行验收条件构造成列表（`src/macao/cli/main.py:386-400, 428-438`）。

上述局部修复不消除以下阻塞项。

## P1：必须先解决

### P1-961-01：Pi 适配器没有接入真实派发链路，且会丢失验收标准

- **证据（CODE/SIM，VERIFIED）**：`PiAdapter` 已声明可 review（`src/macao/adapter/pi.py:21-30`），但 `LiveAgentDispatcher.get_adapter_for_reviewer()` 仅处理 mock、Claude、Codex、OpenCode、Antigravity、Cursor、Kimi，未处理 `cli_type == "pi"`（`src/macao/workflow/live_dispatcher.py:202-225`）。在从 `961bcfe` 导出的独立副本中执行 `LiveAgentDispatcher(...).get_adapter_for_reviewer({'id':'pi-review','cli':'pi'})`，实际抛出 `ValueError: Unknown or unsupported CLI reviewer type: 'pi'`。
- **附加矛盾**：`PiAdapter.inject_task()` 读取 `success_criteria`（`pi.py:107-113`），而编排器发出的 Type-A 信封使用 `acceptance_criteria`（`workflow/orchestrator.py:209-220`）；即便直接构造 Pi executor，用户验收条件仍为空。
- **影响**：申请中“Pi Coding Agent 适配与场景 C 规范”的可运行性没有成立，也破坏 P1-8 所称的验收条件原样透传。
- **处置**：在派发器和 executor 构造路径注册 `PiAdapter`；统一使用 `acceptance_criteria`，并加入 Pi reviewer 与 Pi executor 的端到端测试（含真实派发器选择）。
- **Owner / Due / Resolution commit / Status**：Architecture & Engineering Team / 下次复审前 / TBD / **OPEN**。

### P1-961-02：Cursor 的真实 reviewer 派发入口导入了不存在的类

- **证据（CODE/SIM，VERIFIED）**：派发器在 `src/macao/workflow/live_dispatcher.py:218-220` 导入 `CursorAdapter`，但模块只定义 `CursorAgentAdapter`（`src/macao/adapter/cursor.py:12`）。在独立副本中以 `{'id':'cursor-review','cli':'cursor'}` 调用同一入口，实际得到 `ImportError: cannot import name 'CursorAdapter'`。
- **影响**：配置 Cursor/agent reviewer 时，派发在创建适配器前即失败；这与 L3 所需的适用 reviewer 场景可复现相矛盾。
- **处置**：修正导入和构造参数，并补 Cursor/agent 的 `get_adapter_for_reviewer` 回归测试。
- **Owner / Due / Resolution commit / Status**：Architecture & Engineering Team / 下次复审前 / TBD / **OPEN**。

### P1-961-03：UC-11 承诺的场景 C 接管命令不存在，文档不能作为 L3 实现证据

- **证据（DOC/CODE，VERIFIED）**：UC-11 把 `macao task adopt [--from-request ...]` 定义为态 2/3 的主成功路径（`docs/usercases/UC11-scenarioc-inflight-adoption.md:54-79`），并把“仅唤醒缺票 reviewer、保留既有票”列为验收标准（`:102-109`）。该 commit 的 task CLI 只注册 `probe/create/recover/checkpoint/cancel`（`src/macao/cli/main.py:350-630`）；对 `961bcfe` 的代码搜索中 `task adopt` 仅出现在 UC-11 和 UI 提示，未发现命令、状态接管实现或测试。
- **影响**：申请所称“场景 C（存量半途项目接入）产品用例规范”仍是 UC-11 标注的“设计稿”（`:3-7`），不能支持 PG-2 的消费方场景测试，更不能支持“全量认证”。
- **处置**：实现 fail-closed 的 `task adopt`：解析指定申请单和 baseline、建立合法 `WAITING_REVIEW` 账本/审计、只向 `R_missing` 派发、拒绝物理证据冲突；为态 2、态 3、冲突和重复执行提供隔离集成测试。
- **Owner / Due / Resolution commit / Status**：Architecture & Engineering Team / 下次复审前 / TBD / **OPEN**。

### P1-961-04：检查点完整正文的哈希、归属和“编排器不写正文”约束仍未被执行

- **证据（DOC/CODE，VERIFIED）**：UC-3 要求执行者独占评审申请全文和 `.dev.yml`，编排器仅验证指针、字节级 SHA-256、拓扑、轮次和 executor 归属（`docs/usercases/UC3-dev-checkpoint.md:7, 27-53, 80-98`）。但 `task checkpoint --auto` 仍由 CLI 创建评审申请、生成 `.dev.yml`（`src/macao/cli/main.py:486-542`）。`check_development_checkpoint()` 在 schema 后仅检查 round/status/signal、commit 存在、返工祖先关系和质量字段（`src/macao/workflow/orchestrator.py:261-324`）；没有读取或校验 `full_document.path`、`full_document.sha256` 或 `executor.id`。
- **进一步证据**：CLI 从不存在的 `orchestrator.config['executor']` 取执行者配置，退回为 `dev-claude/claude-code`（`main.py:492-495`；`orchestrator.py:125-140` 的规范化配置仅保存 `executor_id` 和 `team`）。由于归属未校验，错误席位生成的信封仍可推进状态。
- **影响**：一个指向不存在全文、伪造 SHA-256 或错误 executor 的 schema 合法 manifest 可被消费并触发 `READY_FOR_REVIEW`，审计锚点与“不介入”边界均失效。申请末尾自称“伴随机器信封”的 SHA-256 也是全零，而该申请正文的实际 SHA-256 为 `9f30a01f9436214d470bae4fc728a9f9ab5487fa145d3d8f2c79960d82b503d0`，不能作为合格的 UC-3 证据。
- **处置**：移除或改造成仅显式文件校验的自动正文/manifest写入；在状态转移前对路径限定、文件存在、实际 SHA-256、task/ref/round、配置 executor 身份和提交拓扑逐项 fail-closed 校验。添加篡改全文、全零/错误 hash、外部路径、错误 executor、初始轮旧 commit 的负向测试。
- **Owner / Due / Resolution commit / Status**：Architecture & Engineering Team / 下次复审前 / TBD / **OPEN**。

## P2：可延期但需登记

### P2-961-01：提交未通过基础 diff 格式检查

- **证据（CODE，VERIFIED）**：`git diff --check 961bcfe^ 961bcfe` 报告 `src/macao/adapter/session_locator.py:469`、`src/macao/utils/logger.py:78` 的 EOF 空白行，以及 `tests/test_pi_and_session_locator.py:75` 的行尾空白。
- **处置**：修正空白并将 `git diff --check` 纳入提交前检查。
- **Owner / Due / Resolution commit / Status**：Architecture & Engineering Team / 下次复审前 / TBD / **OPEN**。

## L4 / PG-3 评定

**OPS：UNKNOWN。** 申请只陈述曾在 `english_learning_system` 等真实工程演练，未提供本提交可独立复现的命令、脱敏后的 PTY/人工接管记录、恢复后审计链和回归结果。依据评审指引 §2.1 与 §3.3，人工接管实机演练是 L4 的必要条件；因此即使上述 P1 均修复，也须另行提交 OPS 证据后才能评定 L4。

## 建议闭环顺序与复验标准

1. 先修 P1-961-04，确保检查点和评审对象的真实性/归属不可绕过；再修 P1-961-01、P1-961-02，使每个已声明 adapter 都能走到真实派发器。
2. 实现 P1-961-03 的 `task adopt`，以临时 Git 仓库重放态 2、态 3、重复调用与冲突拒绝，并检查 SQLite 审计和既有结果未被覆盖。
3. 在干净 detached/临时副本运行全量测试、专项 E2E 测试、`compileall` 与 `git diff --check`；复审申请中提供真实计算出的 manifest SHA-256。
4. 另行提供一次人工接管、超时/崩溃恢复和日志脱敏的可重放 OPS 证据，才可申请 L4/PG-3。

## Reviewer 自审记录

- 已按指引检查字段/读取路径、强完成声明、YAML/JSON 证据以及 P1 的路径和行号。
- 未把其他 reviewer 的结论、当前工作区的后续未提交修改或申请人的自评当作验证证据。
