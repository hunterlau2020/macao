# d042395 生产就绪、动态探活与全生命周期编排体系合并复审结论

- **评审日期**：2026-09-07
- **评审对象**：`commit d042395`，以及申请所列 `73576c5..d042395` 增量；未将工作区中未提交改动作为受审内容。
- **评审基准**：`docs/MACAO_REVIEW_GUIDELINES.md`、`docs/MACAO_PRD_v2.md`、`docs/usercases/UC2-task-create.md`、`docs/usercases/UC3-dev-checkpoint.md`、`docs/PROBE_TECHNICAL_DESIGN.md`。
- **结论**：**REJECT**。不授予 L3 / PG-2；不具备进入 L4 / PG-3 的条件。

## 已确认项

- **TEST / CODE：VERIFIED**。在受审工作树运行 `PYTHONPATH=src python3 -m unittest discover tests` 通过；`python3 -m compileall -q src tests` 通过；`git diff --check d042395` 通过。这些结果只能说明现有覆盖范围内没有失败，不能抵消以下规格反例。
- `VoteAggregator` 的超时票已携带 `source: timeout`、`deadline` 和 `last_ping_at`，并在写入前做 schema 校验（`src/macao/consensus/vote.py:148-164,294-323`）。
- `TeamProber` 对已有 SQLite 状态库使用 URI `mode=ro` 读取（`src/macao/workflow/prober.py:67-110`）；这一局部事实不等于整个 probe 零副作用。

## P1：进入下一阶段前必须修正

### P1-01：`task checkpoint --auto` 伪造执行者产物与测试结论

- **证据（CODE）**：`src/macao/cli/main.py:467-496` 在 `--auto` 路径中由 CLI 创建评审申请正文和 `.macao/.dev.yml`，并无条件写入 `quality_metrics: {tests_passed: True}`。随后 `src/macao/workflow/orchestrator.py:240-254` 将该字段作为进入 `READY_FOR_REVIEW` 的必要条件而消费。
- **冲突（DOC）**：UC-3 明定评审申请全文与 `.dev.yml` 的内容作者为执行者、编排器“不读、不写、不摘要”（`docs/usercases/UC3-dev-checkpoint.md:7,25-31`）；其 d1–d6 还要求校验全文路径及字节级 SHA-256（`:51-57`）。该自动生成的正文仅为标题与 HEAD，且把未执行的测试陈述为通过，不能成为执行者自报证据。
- **可复现性**：对任意刚创建任务执行 `macao task checkpoint --auto --no-review`，无需运行测试即可生成 `tests_passed: true` 的 checkpoint；检查点校验会接受此声明。
- **影响**：流程编排器越过内容写者边界，并为无测试证据的提交打开 E1_PRODUCED/E2。属于状态推进与审计真实性 P1。
- **闭环**：移除或改造 `--auto` 为只生成未填充模板且绝不触发转移；由执行者提交带 `full_document.path + evidence_commit + sha256` 的 manifest，再实现 UC-3 d1–d6 的 SHA/归属校验。补充“未运行测试不可通过 auto 推进”的反例测试。
- **Owner / Due / Resolution / Status**：Architecture & Engineering / 重新提审前 / — / OPEN。

### P1-02：任务受理可绕过串行锁并遗失调用者提交的验收标准

- **证据（CODE）**：`src/macao/cli/main.py:379-421` 的 `--force` 在已有活动任务时仍调用 `start_task`；`StateStore.get_active_task()` 只按创建时间返回一条非终态记录（`src/macao/storage/store.py:48-54`）。原任务既未取消也未归档，后续 checkpoint/cancel/merge 都会操作较新的任务。现有测试还将该行为断言为成功（`tests/test_team_probe_and_dispatch.py:166-183`）。
- **证据（CODE）**：同一命令把用户的 `--acceptance` 包装为字典后传入（`src/macao/cli/main.py:415-420`），而 `start_task()` 仅接受非空 list；字典会被替换为 `"All unit tests pass", "Zero regression"`（`src/macao/workflow/orchestrator.py:193-207`）。因此用户显式输入的验收准则没有进入 Type A。
- **冲突（DOC）**：UC-2 P3/b4 要求同一时刻仅有一个活动任务（`docs/usercases/UC2-task-create.md:17,37-40`），E3 要求拒绝已有活动任务（`:70-75`）；其 Type A 必须逐字段携带提交表单的 `success_criteria`（`:49-51,84-88`）。
- **影响**：活动任务及其审计/产物归属变得不可唯一，且执行者收到的成功标准可能与用户提交内容不同。
- **闭环**：删除“force 绕过活动任务”语义，或先显式 E10/归档并取得管理员授权；使 `acceptance` 成为必填、可序列化的列表，原样持久化并逐字段发送。补齐并发创建、空/非列表验收、信封逐字段一致性测试。
- **Owner / Due / Resolution / Status**：Workflow & CLI / 重新提审前 / — / OPEN。

### P1-03：probe 的共识可达性和“待评审”判定会报出错误物理事实

- **证据（CODE）**：共识可达性仅计算 `ready_reviewers_count >= minimum_winning_seats`（`src/macao/workflow/prober.py:757-770`），完全未使用已读出的 `seat_quorum_required`、`weight_quorum_required`、`total_effective_weight`。例如 `minimum_winning_seats=2, seat_quorum_required=2, weight_quorum_required=3` 且两个权重 1 的 reviewer 可用时，本函数返回 `achievable=True`，尽管可用权重 2 小于门槛 3。
- **冲突（DOC）**：探活设计规定公式必须同时满足席位门槛、胜方席位门槛和权重门槛（`docs/PROBE_TECHNICAL_DESIGN.md:216-230`）。
- **证据（CODE）**：物理评审单逻辑只要发现任意一个文件名包含 baseline 的 result，就将 `has_pending_request` 设为 false（`src/macao/workflow/prober.py:201-240`）。它既不解析申请所需 reviewer，也不计算已落票集合；3 位 reviewer 中仅 1 位提交时会被判定“不待审”。
- **冲突（DOC）**：`Next` 要列出申请所要求、尚未落票的 reviewer（`docs/PROBE_TECHNICAL_DESIGN.md:174-185`）。
- **影响**：probe 可错误放行无法达成法定共识的派发，并将仍待审的工作报告为已完成，违反申请所强调的“不假造虚假进度”。
- **闭环**：按同一 policy 执行 `R_ready >= S`、`R_ready >= M`、`W_available >= W_required`；从结构化评审申请或任务配置取得期待 reviewer 集合，用 `(baseline, reviewer_id)` 精确集合差计算 pending。分别添加席位/权重不足和 1-of-N result 的测试。
- **Owner / Due / Resolution / Status**：Probe & Consensus / 重新提审前 / — / OPEN。

### P1-04：会话定位把未绑定本项目的会话标成“当前项目活跃会话”

- **证据（CODE）**：Codex 定位器读取 `session_index.jsonl` 的最后一个可解析行，未检查其中任何项目/工作目录字段，却将调用方的 `project_path` 填回 `workspace`（`src/macao/adapter/session_locator.py:165-194`）。Cursor 同样只选整个 `~/.cursor/chats/` 的最新目录，未做 workspace 匹配（`:197-219`）；Kimi 仅因 `~/.kimi` 存在即声称 `last_active: recent`（`:222-233`）。
- **冲突（DOC）**：设计宣称所有定位器匹配当前项目根目录，找不到本项目会话时返回 `None`，绝不假造状态（`docs/PROBE_TECHNICAL_DESIGN.md:140-154`）。
- **影响**：不同项目最近使用 Codex/Cursor/Kimi 后，在本项目运行 probe 即可伪报会话、`session_active` 和“上下文继承”依据；这正是探活层必须避免的错误归因。
- **闭环**：仅在可验证的 canonical workspace 字段与 `project_root` 精确匹配时返回会话；无法从厂商格式证明绑定时返回 `None`/`UNKNOWN`，不回填调用方路径。为三个 locator 分别加入“最新会话属于另一项目”反例。
- **Owner / Due / Resolution / Status**：Adapter & Probe / 重新提审前 / — / OPEN。

### P1-05：`--dry-run` 仍创建目录/日志文件，且审查终端日志没有秘密脱敏

- **证据（CODE）**：`TeamProber.probe()` 无条件调用 `_write_probe_log()`（`src/macao/workflow/prober.py:788-813`）；后者无条件 `mkdir` 并写 `.macao/logs/probe/probe_*.log`（`:244-304`），`dry_run` 只作为日志内容，不控制写入。因而未初始化第三方仓库执行 `macao probe --dry-run` 会创建 `.macao/`。
- **冲突（DOC）**：设计宣称 `--dry-run` 不创建空目录、100% 幂等且无痕（`docs/PROBE_TECHNICAL_DESIGN.md:69-75`）。
- **证据（CODE）**：reviewer transcript 最终由 `LiveAgentDispatcher` 直接将 `adapter.get_logs()` 的内容写入文件（`src/macao/workflow/live_dispatcher.py:347-353`）；各 adapter 返回的仅是 ANSI 清洗文本（如 `src/macao/adapter/codex.py:106-107`，`src/macao/adapter/pty_session.py:87-105`）。仓库没有把 `secrets_masking: true` 连接到该写路径的 mask/redact 实现或测试。
- **影响**：dry-run 改写被探测项目；终端回显的 token、密码或连接串会按原样保留到可由 `macao logs -r` 读取的审计文件，不能称为“日志脱敏”。
- **闭环**：dry-run 完全禁止 `_write_probe_log`（若要留痕则显式、默认关闭的非-dry-run audit 模式）；在任何磁盘写入前实施并测试确定性 secrets redaction，且禁止将原始秘密写入其他日志/AEP/audit 表。
- **Owner / Due / Resolution / Status**：Runtime Security / 重新提审前 / — / OPEN。

## L4 / PG-3 判定

**UNKNOWN，因而不通过。** 评审指引要求 L4 有独立可复现的 OPS 证据和用户可见的人工接管实机演练（`docs/MACAO_REVIEW_GUIDELINES.md:24-25,71-73`）。申请所述外部项目演练仅在申请正文中陈述，未提供可在本仓库重放的命令、保留产物、真实 PTY 进程/人工接管证据链；现有自动化测试成功也不能替代该门禁。即使上述 P1 全部修复，仍应以至少一次真实受控 CLI reviewer、真实 deadline、人工 override、merge/recovery 的留档演练重新申请 L4。

## 建议闭环顺序与验收标准

1. 先恢复 UC-2/UC-3 的内容责任和单活动任务不变量（P1-01、P1-02），以反例测试锁定不得伪造 manifest/验收条件。
2. 修复 P1-03、P1-04，提供 policy 边界矩阵、部分 reviewer 已落票、跨项目最新会话的 deterministic tests。
3. 修复 P1-05，使用文件快照测试证明 dry-run 零文件系统变化，并加入 token/password/connection-string 的日志脱敏测试。
4. 以上 P1 全部关闭后重跑全量测试；申请 L3 时附上场景矩阵。仅在独立真实 CLI + 人工接管 OPS 留证后评估 L4。

## Reviewer 自审记录

- 本轮逐项检查了字段读取位置、强声明/测试覆盖与异常反例；没有以申请方的 128 项测试或外部实操自述替代 CODE/SIM/OPS 证据。
