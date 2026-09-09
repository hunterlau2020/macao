# Commit bdc177e 检查点防伪与执行者接线复审结论

- **评审日期**：2026-09-10
- **评审范围**：`e06d44c..bdc177e`；受审 commit：`bdc177eaaff577e119093e686f2164bcc133f781`。
- **评审基准**：`docs/MACAO_REVIEW_GUIDELINES.md` v1.1、`docs/MACAO_PRD_v2.md`、UC-2、UC-3、UC-11。
- **结论**：**REJECT**。不授予 **L3 / PG-2**；**L4 / PG-3 为 UNKNOWN，不能准入**。

## 已对齐 / 已确认项

1. 申请引用的完整 SHA 可由 Git 解析；`git show --check bdc177eaaff577e119093e686f2164bcc133f781` 通过。
2. 申请的 `.dev.yml` 样例可被 `validate_dev_manifest()` 接受；其 `full_document.sha256` 与 `bdc177e` 中 `2026-09-09-disposition-e06d44c.md` 的 blob SHA-256 一致（`877f4bc28fd444cba43e67782ac1129486447e91ccb915e972b6f22c6d07d56c`）。
3. 在从受审 commit 导出的干净副本中，`tests/test_p1_closures_and_regressions.py` 的 **26** 项测试通过；全量 `unittest discover tests` 返回 0，`compileall -q src tests` 通过。
4. 已提交正文被篡改、空 `evidence_commit`、同名前缀兄弟目录三种申请已覆盖且会被当前实现拒绝；五个此前遗漏的 adapter 现读取 `acceptance_criteria`。

## P0：必须先解决

无新增 P0。

## P1：发布/进入下一阶段前应修正

### P1-bdc177e-01：未存在于 `evidence_commit` 的正文仍可推进 checkpoint

- **证据（CODE/SIM，VERIFIED）**：申请把 Git blob 校验描述为“严格校验”且承诺阻止未提交正文（`docs/reviews/2026-09-09-review-request-bdc177e.md:42-45`）；UC-3 要求全文与提交形成可审计的强引用（`docs/usecases/UC3-dev-checkpoint.md:27-29,51-53`）。但实现只在 `git cat-file -e <commit>:<path>` **成功**时才比较 blob；失败时没有 `return None`（`src/macao/workflow/orchestrator.py:430-439`）。因此将一个在 checkpoint 之后新建、从未加入该 commit 的文件写入当前工作树，并在 manifest 中把 `evidence_commit` 填为该 commit，仍会仅凭当前磁盘 SHA 获得放行。
- **复现结果（SIM，VERIFIED）**：归档脚本在独立临时 Git 仓库中提交 HEAD 后才创建 `docs/reviews/written-after-head.md`，确认 `git cat-file -e HEAD:docs/reviews/written-after-head.md` 非零；携带该文件正确磁盘 SHA 的 `.dev.yml` 仍令任务进入 `READY_FOR_REVIEW`。
- **影响**：`evidence_commit` 不是正文的真实性锚点，执行者可在未产生对应 commit 的条件下把任意事后正文送入评审。该路径由正常 `task checkpoint` 调用，破坏“评审对象 = checkpoint 中的产物”的审计不变量，定级 P1。
- **处置**：Git 仓库内必须把 `cat-file -e` 失败和 `get_file_bytes_at_commit()` 返回 `None` 都视为拒绝；只接受存在于 `evidence_commit` 的相对路径，且 blob SHA、工作树 SHA、manifest SHA 三者完全相同。新增“未跟踪文件”“文件只在后续 commit 中出现”“读取 blob 失败”三条否定回归。
- **Owner / Due date / Resolution commit / Status**：Architecture & Engineering Team / 下次复审前 / TBD / **OPEN**。

### P1-bdc177e-02：未知 executor CLI 被静默降级为空执行者，`--no-probe` 仍可创建 CODING 任务

- **证据（CODE/SIM，VERIFIED）**：配置 schema 对 `team.executor.cli` 只要求字符串，不限制其值（`src/macao/schemas/macao_config.schema.json:30-38`）。新的 executor 工厂对未知 CLI 直接 `return None`（`src/macao/workflow/live_dispatcher.py:239-284`）；`get_orchestrator()` 将该 `None` 传入，而 `Orchestrator.__init__` 的所谓兜底会对同一未知配置再次返回 `None`（`src/macao/cli/main.py:179-197`、`src/macao/workflow/orchestrator.py:97-112`）。`start_task()` 仅在 `self.executor` 非空时启动/注入执行者（`:207-215`）。
- **复现结果（SIM，VERIFIED）**：归档脚本创建 schema 合法的 `cli: unknown-executor` 配置，确认生产 `get_orchestrator()` 的 `executor is None`；随后由正式 CLI 入口执行 `macao task create --no-probe --title ... --acceptance ...`，返回 0 并留下 `CODING` 活动任务，却没有执行者进程或接收者。`--no-probe` 是公开 CLI 选项，故该路径在线可达。
- **影响**：不受 schema 拦截的错误配置被静默接受，用户获得成功提示但任务永久无执行者，与本轮“完整装配、杜绝执行者悬空”的声明相反。按 fail-closed 原则和 UC-2 的执行者投递要求，这是 P1。
- **处置**：`get_adapter_for_executor()` 对未知/不受支持的 CLI 抛出明确异常；composition root 和 `Orchestrator` 必须将其转换为非零 CLI 退出且不得写任务状态。`--force` / `--no-probe` 不能绕过 adapter 类型合法性。新增黑盒 CLI 反例，断言无任务、无审计半行、错误中包含配置的 CLI 名称。
- **Owner / Due date / Resolution commit / Status**：Architecture & Engineering Team / 下次复审前 / TBD / **OPEN**。

## P2/P3：可延期但需登记

### P2-bdc177e-01：`task checkpoint --auto` 仍违背 UC-3 的产物作者边界

- **证据（CODE/DOC，VERIFIED）**：`src/macao/cli/main.py:722-778` 在 `--auto` 下创建 review request 正文和 `.dev.yml`；UC-3 规定这两类产物由执行者独占写入，编排器不得创作/摘要正文（`docs/usecases/UC3-dev-checkpoint.md:7,27-31`）。本轮没有修改该路径，也未在已知简化表登记完整风险接受。
- **处置**：移除自动创作，或使草稿不带 `EXPLICIT`、永远不能触发状态转移，并按 Guidelines §8.3 完整登记风险接受。

## L4 / PG-3 评定

**OPS：UNKNOWN。** 申请仍未对 Guidelines §7.2 的十项 L4 运维矩阵逐项给出状态和可重放证据；没有真实 provider CLI、PTY 断开、冷重启、并发写、磁盘写失败及 `macao override resolve` 的用户可见演练。P1 未清零前更不能准入。

## 建议的闭环顺序与验收标准

1. 先将 Git blob 缺失/读取失败改为 fail-closed，新增未跟踪、后续提交、读失败三条隔离回归；所有反例均断言任务保持 `CODING`。
2. 将 executor factory 的返回类型收敛为“有效 adapter 或异常”，以 `task create --no-probe` 黑盒测试验证未知 CLI 返回非零且零状态写入。
3. 处理或正式登记 `--auto` 的作者边界，再重新申请 L3。
4. P1 为零后按 Guidelines §7.2 完成十项 OPS 和人工接管实机演练，才可申请 L4。

## 复现脚本与命令

- [reproduce_remaining_fail_closed_gaps.py](evidence/2026-09-10-bdc177e-codex/reproduce_remaining_fail_closed_gaps.py)：验证 P1-bdc177e-01 与 P1-bdc177e-02；受审 commit `bdc177eaaff577e119093e686f2164bcc133f781`；前提为 Linux、Python 3.10+、Git、PyYAML/jsonschema，无网络或厂商 CLI；最后执行于 2026-09-10 Asia/Taipei。

```bash
PYTHONPATH=src python3 docs/reviews/evidence/2026-09-10-bdc177e-codex/reproduce_remaining_fail_closed_gaps.py
```

## Reviewer 自审记录

- 使用受审 commit 的独立导出副本执行提交级检查与专项回归，未采信当前工作树或申请人自述作为提交证据。
- 反例分别由生产 checkpoint 入口和公开 CLI `task create --no-probe` 驱动；未以直接注入私有状态替代生产路径。
