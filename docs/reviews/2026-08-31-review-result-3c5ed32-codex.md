# Phase 3（PG-3 / L4 RELEASE-READY）独立评审结论

- **评审日期**：2026-08-31
- **Reviewer**：Codex
- **评审对象**：`3c5ed32014fe73f0127a57b96440ba8ff6a73478`（短 SHA：`3c5ed32`）
- **增量基线**：既有 L3/PG-2 封板提交 `4e38ed6`；同时检查 `3c5ed32` 的完整树状态
- **评审申请**：`docs/reviews/2026-08-31-review-request-Phase3-PG3-L4.md`
- **权威基准**：`docs/MACAO_REVIEW_GUIDELINES.md`、`docs/MACAO_PRD_v2.md`
- **评审方式**：冻结提交静态审读、全量回归、CLI 冒烟、隔离临时仓库故障注入、发行 wheel 内容检查
- **独立性声明**：未把其他 Reviewer 的结论或票数作为证据；工作区既有未跟踪评审文件未被修改

## 1. 结论

**REJECT：不授予 L4 RELEASE-READY，不授予 PG-3。**

本轮不重审、也不撤销此前已授予的 L3 SCENARIO-VERIFIED / PG-2；在本次申请范围内，项目最高维持既有 L3/PG-2。`docs/MACAO_REVIEW_GUIDELINES.md:62,73,108` 要求 L4 同时具备真实 OPS 证据、用户可见人工接管演练、零 P0/P1 与齐备用户手册。本提交新增路径存在 **6 项 P1**，真实协同、超时驱动和人工接管证据均被独立反例推翻。

本次结论不以“72/72 测试通过”外推发布就绪。现有 Phase 3 新测试只覆盖 extractor 的批准 happy path、daemon 空任务扫描和 runner 最终状态；没有覆盖本报告列出的活跃超时、模糊输出、身份/代际错绑、真实 CLI 消费或人工接管。

## 2. 证据矩阵

| 声明 / 门禁 | 独立证据 | 状态 |
|---|---|---|
| 全量测试 72/72 | `PYTHONPATH=src python3 -m unittest discover tests -v`：`Ran 72 tests ... OK` | VERIFIED，但不足以证明 L4 |
| 编译检查 | `python3 -m compileall -q src tests`：exit 0 | VERIFIED |
| 差异 100% clean | `git diff --check 4e38ed6..3c5ed32`：`docs/reference/REVIEW_METHODOLOGY.md:4-6` 三处 trailing whitespace，exit 2 | CONTRADICTED |
| Phase 3 真实多 Agent 闭环 | 将 `LiveAgentDispatcher.dispatch_review_in_worktree()` 替换为必抛异常后，runner 仍返回 `PASS`，调用次数为 0 | CONTRADICTED |
| 人工签字实机演练 | runner 自行写入 `HUMAN_MERGE_APPROVED`，独立运行观察到 `auto_signoffs=1` | CONTRADICTED |
| daemon 活跃超时降级 | 构造已过期 `WAITING_REVIEW` 任务，`scan_once()` 抛 `AttributeError: StateStore has no attribute get_audit_events` | CONTRADICTED |
| ReviewExtractor fail-closed | 输入仅为 `notes: still investigating`，结果被补成 `APPROVED / YES_APPROVE` | CONTRADICTED |
| Reviewer/checkpoint/round 绑定 | 以 `agent_id=codex/ref=expected-ref/round=1` 调用时，显式提供的 `opencode/stale-ref/99` 原样通过 | CONTRADICTED |
| 6 CLI 实际会话联调 | `test-clis` 只执行 Claude/Codex/OpenCode/AGY 的 `--version`；Cursor/Kimi 未进入批量测试，也未执行真实 review 命令 | PARTIALLY_VERIFIED |
| package schemas | 从冻结提交构建 wheel 成功；wheel 内包含 6 个 `macao/schemas/*.schema.json`；与 `docs/schemas/` SHA-256 逐份相同 | VERIFIED |
| setup 向导 | 配置可过 Schema，但探测结果未参与团队选择，且 CLI 无条件覆盖已有 `macao.yaml` | PARTIALLY_VERIFIED |

## 3. 已确认项

1. `src/macao/schemas/` 的 6 份 JSON Schema 与 `docs/schemas/` 内容逐份一致；`pyproject.toml:40-41` 的 package-data 配置有效，冻结提交可构建 wheel，包内资源完整。
2. `SchemaValidator` 优先读取包内 schemas（`src/macao/core/schema.py:17-20`），安装后不再依赖仓库相对路径；本项申请声明属实。
3. `ReviewExtractor` 能剥离 ANSI、解析 fenced YAML，并利用 Draft-07 Schema 拒绝部分结构错误；这只是解析能力的局部正例，不等于决策安全。
4. `ensure_gitignore_isolation()` 的重复调用具备基本幂等性；生成的 `macao.yaml` 能通过当前配置 Schema。
5. 72 项现有测试全部通过；新增 Phase 3 代码没有破坏既有测试集所覆盖的 L3 状态机路径。

## 4. P0

本轮未登记 P0。以下 P1 均为 L4/PG-3 不可豁免阻断项。

## 5. P1：发布前必须关闭

### P1-1：`live-run` 伪造开发、评审与人工签字，未执行真实 Agent 协同

**证据**：

- `src/macao/workflow/live_runner.py:93-117` 由 runner 自己写业务代码、提交 commit 并生成 `.dev.yml`，没有启动 Executor；而且没有创建/切换 `feature/calc-live`，开发 commit 实际直接落在 `main`。
- `src/macao/workflow/live_runner.py:125-132` 只调用原编排器创建 worktree 和发布消息。
- `src/macao/workflow/live_runner.py:134-155` 随后由 runner 为全部 Reviewer 直接写入 `YES_APPROVE / APPROVED`；`self.dispatcher` 从未被调用。
- `src/macao/workflow/live_runner.py:165-170` 以 `Live runner auto-signoff` 自动写入本应由人类产生的签字。
- `src/macao/workflow/live_runner.py:197` 将耗时硬编码为 `0.5`。
- 独立故障注入把 `dispatch_review_in_worktree()` 改成必抛异常，运行结果仍为 `PASS`、`dispatcher_calls=0`、`auto_signoffs=1`。

这只能证明“runner 自产三张赞成票后旧 FSM 可以 DONE”，不能证明申请 `:44-52,62` 所称真实多 Agent、真实意见提取、人工签字或 source→target fast-forward。它也不满足 L4 的用户可见人工接管要求。

**验收标准**：真实 Executor 生成 commit/.dev.yml；每个 Reviewer 必须经生产 dispatcher 启动、消费上下文并独立生成 manifest；禁止 runner 代写票或人类签字；使用真实 source branch；保存会话命令、PID、cwd、ACK、输出、耗时和归档证据；至少演练一次真实 HOLD→人工裁定，以及拒绝/超时路径。

### P1-2：daemon 的活跃超时路径确定性崩溃，持续模式还会静默吞错

**证据**：

- `src/macao/workflow/daemon.py:34` 调用不存在的 `StateStore.get_audit_events()`；真实 API 是 `list_audit_events()` / `get_audit_events_by_type()`（`src/macao/storage/store.py:163-212`）。
- 即使修正方法名，`daemon.py:38-41` 仍查 `REVIEW_DISPATCHED`、读取 `event_type/payload/deadline_epoch`；生产写入的是 `REVIEW_REQUESTS_DISPATCHED` 及 `type/detail/deadline`（`src/macao/workflow/orchestrator.py:358-364`）。
- `daemon.py:47-49` 把 artifact `kind` 当成 `<reviewer>.review.yml`，而台账 kind 是 `review_manifest`，reviewer 位于 `reviewer_id`。
- `daemon.py:61` 调用共识计算时未传 `timed_out_reviewers`，所以即使前述接线全部修复，超时 ABSTAIN 也不会进入该次 vote result。
- `daemon.py:75-78` 在持续模式吞掉所有异常，没有审计、告警或退避升级。
- 新测试 `tests/test_phase3.py:89-95` 仅覆盖无活跃任务；申请 `:63` 的 `--once` exit 0 是空转证据。

独立复现：创建实际字段格式的过期 `WAITING_REVIEW` 任务后，第一次扫描即抛上述 `AttributeError`，任务无法降级。申请 `:21-26` 的“生产级后台守护轮询器”声明为 CONTRADICTED。

**验收标准**：复用已经存在的 `Orchestrator.detect_timed_out_reviewers()` 单一语义源；活跃任务实测超时后持久化 ABSTAIN、进入 HOLD、生成正确 terminal audit；覆盖部分响应、重复扫描、重启、80+ audit、迟到票和二次 retry generation；daemon 异常必须可见且以非零健康状态上报。

### P1-3：ReviewExtractor 将无投票输出默认批准，并接受错误身份/检查点/轮次

**证据**：

- `src/macao/workflow/live_dispatcher.py:69-75` 对身份字段只用 `setdefault`，已有但错误的 reviewer/checkpoint/round 不会与调用上下文比较。
- `live_dispatcher.py:90-91` 在 vote/status 都不存在时默认填入 `YES_APPROVE / APPROVED`。
- `src/macao/consensus/vote.py:97` 和 `src/macao/workflow/orchestrator.py:557` 又引入第二层 `YES_APPROVE` 默认值，形成全链路向批准倾斜。
- `live_dispatcher.py:189-201` 的直接文件路径也只做通用 Schema 校验，不绑定当前 agent/ref/round；返回 vote 还从错误路径 `opinion.vote` 读取并默认批准，而正式 vote 位于根节点。
- Schema 只验证字段形状，不能替代运行时主体和代际绑定。

独立反例一：输入 `notes: still investigating`，得到 schema-valid 的 `YES_APPROVE / APPROVED`。独立反例二：当前调用上下文为 `codex / expected-ref / round 1`，输出写成 `opencode / stale-ref / round 99` 仍返回 valid。

这会把模型的未完成说明、日志片段或旧轮次输出转为赞成票；一旦 P1-1 的真实链路接通，可能直接影响合并决策。

**验收标准**：缺少明确 vote/status 必须拒绝或记 ABSTAIN，绝不默认批准；所有产物强制等于预期 reviewer/checkpoint/round/generation/message_id；直接文件与终端提取共用同一绑定校验；加入模糊文本、旧票、身份冒用、错 round、空 YAML 和多代码块反例。

### P1-4：真实 Reviewer 准入与 CLI conformance 仍是 fail-open

**证据**：

- `LiveAgentDispatcher.get_adapter_for_reviewer()` 对未知 CLI 静默回退到 OpenCode（`src/macao/workflow/live_dispatcher.py:111-115`）；独立输入 `not-a-real-cli` 实得 `OpenCodeAdapter`。
- dispatcher 启动前没有调用 `preflight()`，也没有检查 `can_review`、`supports_worktree`、`execution_mode` 或 `security.allowed_clis`。
- Claude 声明 `execution_mode=FULL`（`src/macao/adapter/claude.py:19-27`）并以 `--dangerously-skip-permissions` 启动（`:60-69`），却在 registry 中被允许作为 Reviewer；这违反 PRD `docs/MACAO_PRD_v2.md:1405-1418` 的 Reviewer 必须 sandboxed 以及 Claude 仅 Executor 的硬门禁。
- 所谓 PTY 沙箱只是 cwd/worktree，未提供 PRD 对 sandboxed 定义的容器/受限环境、网络默认禁止或命令白名单（PRD `:1407-1410`）。
- 批量 `test-clis` 只枚举四项（`src/macao/adapter/integ_harness.py:153-159`），每项只运行 `--version`（`:83-95`）；没有 Cursor/Kimi，也没有启动生产 review 命令、注入任务、产出 manifest、ACK、限流、凭据失败或断线恢复。
- 多个 adapter 的 `auth_valid` / `in_matrix` 是发现二进制后的常量，并非认证或版本矩阵验证；把所有 `shutil.which` 模拟为失败时，`macao preflight` 仍 exit 0。

因此申请 `:15,41-42,64-65` 只能证明本机存在若干二进制且四个 `--version` 进程能退出，不能证明六种 Adapter 作为 Executor/Reviewer 可生产使用。

**验收标准**：未知/不允许 CLI fail-closed；dispatcher 强制执行 capability 和 preflight 门禁；Reviewer 必须具有可验证的受限执行边界；六个 CLI 逐一用生产命令完成 prompt→manifest→binding→ACK→cleanup，并覆盖凭据失效、版本不兼容、限流、PTY 断开和僵尸检查；任何必需项失败令命令非零退出。

### P1-5：`macao setup` 忽略探测结果且无条件覆盖已有配置

**证据**：

- `probe_available_clis()` 只探测 PATH 和 `--version`（`src/macao/cli/wizard.py:14-40`），没有申请 `:30` 所称“可用模型”探测；探针异常时还用硬编码版本代替失败。
- `generate_smart_config()` 不消费 probe 结果，而是无条件选择 Cursor、Claude、AGY 三名 Reviewer（`wizard.py:101-106`），可能生成当前机器根本不可运行的团队。
- CLI 的 `--executor` 未验证是否安装或在 allowed list，模型也未做 CLI-specific 校验。
- `src/macao/cli/main.py:351-360` 探测只用于打印，随后无确认、无备份地覆盖 `macao.yaml`。这与 `macao init` 已有的“文件存在则拒绝覆盖”保护不一致。
- 配置 Schema 的 agent id/cli/adapter 仅要求 string，不能证明适配器存在、角色能力兼容或模型可用。

**验收标准**：已有配置默认拒绝覆盖或原子备份；探测结果实际驱动候选选择；不存在、未认证、角色不兼容或模型不可用的 Agent 不得进入生成配置；生成后执行完整 conformance，失败则不落盘；补充 CLI 级覆盖/恢复测试。

### P1-6：冻结提交的用户手册与实现矛盾，未达到“手册齐备”

**证据**：

- `docs/FAQ.md:41-45` 指引用户运行已被本提交删除的 `e2e-run`；实际命令改为 `live-run`（`src/macao/cli/main.py:392-410`）。
- FAQ `:93-95` 声称 Schema 失败会进行会话内 re-prompt，代码没有任何 re-prompt；只会继续轮询同一输出直至超时。
- FAQ `:103-113` 声称超时自动 ABSTAIN→HOLD，P1-2 已证明活跃超时确定性崩溃。
- FAQ `:233-234` 声称派发前探测 Session Lock、API Token 和 PTY 延迟，代码不存在这些门禁。
- FAQ `:241` 与申请 `:14` 使用 `.macao/worktrees/<task>/<reviewer>`，旧编排器实际路径是 `.macao/worktrees/<reviewer>/<task>/r<round>`（`src/macao/utils/git_utils.py:96-122`），新增 dispatcher 又使用前一种路径，形成两套不兼容生命周期。

**验收标准**：以真实可执行命令重写快速上手；所有“自动”“100%”“真实”“沙箱”“人工”等强声明逐条绑定测试/OPS 证据；统一 worktree 路径与唯一 owner；补充安装、升级、daemon 运维、故障告警、人工接管、回滚和卸载说明，并由干净环境用户照文档重放。

## 6. P2 / P3

### P2-1：申请的洁净度声明不实

申请 `docs/reviews/2026-08-31-review-request-Phase3-PG3-L4.md:61` 声称 `git diff --check` exit 0；冻结增量 `4e38ed6..3c5ed32` 实际在 `docs/reference/REVIEW_METHODOLOGY.md:4-6` 报三处 trailing whitespace，exit 2。应在 CI 中固定检查明确 base/head，禁止以未说明范围的工作区命令作为证据。

### P2-2：参考资料目录混入非 MACAO 领域规范并形成多份评审准则

提交新增 `docs/reference/REVIEW_METHODOLOGY.md`，正文是财务数据 Loader/Pipeline 规范并引用仓库不存在的上位原则；同时复制多份 review guide。它们不属于 Phase 3 运行时交付物，且会与唯一权威 `docs/MACAO_REVIEW_GUIDELINES.md` 产生来源歧义。应删除无关材料，或明确标注归档来源、非规范性和适用边界。

## 7. Known Issues 登记

| issue_id | 级别 | owner | due_date | resolution_commit | status |
|---|---|---|---|---|---|
| P3-L4-CODEX-01 | P1 | Phase 3 Runner owner | PG-3 重新申请前 | TBD | OPEN |
| P3-L4-CODEX-02 | P1 | Daemon / Orchestrator owner | PG-3 重新申请前 | TBD | OPEN |
| P3-L4-CODEX-03 | P1 | Review protocol owner | PG-3 重新申请前 | TBD | OPEN |
| P3-L4-CODEX-04 | P1 | Adapter / Security owner | PG-3 重新申请前 | TBD | OPEN |
| P3-L4-CODEX-05 | P1 | CLI Setup owner | PG-3 重新申请前 | TBD | OPEN |
| P3-L4-CODEX-06 | P1 | Documentation / OPS owner | PG-3 重新申请前 | TBD | OPEN |
| P3-L4-CODEX-07 | P2 | CI owner | 下一整改提交 | TBD | OPEN |
| P3-L4-CODEX-08 | P2 | Documentation owner | 下一整改提交 | TBD | OPEN |

## 8. 建议闭环顺序与复审门槛

1. 先关闭 P1-3 与 P1-4：建立明确票、强绑定和 Reviewer 安全准入，否则真实接线会扩大误合并风险。
2. 将 LiveDispatcher 接入唯一生产编排链，删除 runner 代写 dev/review/signoff；统一 worktree owner 与路径。
3. 让 daemon 复用 Orchestrator 的 timeout API，并完成活跃任务、重启、迟到票和重复扫描测试。
4. 修复 setup 覆盖与探测逻辑；六个真实 CLI 完成生产命令 conformance，而非 `--version` 冒烟。
5. 完成一次可旁观、可复现的真实批准路径和一次 HOLD→人工接管路径；原始 OPS 证据进入不可变归档。
6. 修正文档、清理 reference 污染、通过明确范围的 `git diff --check`，再申请 L4/PG-3。

重新申请至少应附：

- 六个 CLI 中本次声明支持者的逐项 capability/preflight/真实会话报告；
- 实际命令、cwd、checkpoint、review round、PID、退出码、产物 SHA-256 与 ACK；
- 不由 runner 生成的真实 `.dev.yml`、各 Reviewer `.review.yml`、vote result 和人工签字；
- 活跃超时、模糊输出、旧代票、错误身份、进程崩溃、凭据失败、限流和重启恢复反例；
- 干净安装环境按用户手册从 setup 到人工接管/merge 的完整录像或等价不可变日志。

## 9. Reviewer 自审记录

- 已检查字段名与实际读取路径：daemon 的 method/event/detail/deadline/artifact key 不一致已登记 P1-2。
- 已检查 `[x]`、`PASS`、`100%`、`真实` 等强声明：测试通过未外推 L4，洁净度与真实协同声明均已反证。
- 已检查 YAML/JSON：6 份 package schema 可解析且已进入 wheel；同时补测 extractor 的非票文本与错绑定反例。
- 每项 P1 均给出文件、行号、可复现输入及验收标准。
- 本轮没有沿用其他 Reviewer 的票作为事实依据；没有发现需要登记的连续同类漏审。
