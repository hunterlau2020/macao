# MACAO P1 返工复审结论（`961bcfe` / Round 2）

- **文档归档路径**: `docs/reviews/2026-09-07-review-result-961bcfe-grok.md`
- **审查日期 (Review Date)**: 2026-09-07
- **审查专家 (Reviewer)**: grok（独立复审；不采信申请粘贴输出，不采信 `STATUS.md` 定级句，不采信处置单「ALL CLOSED」，不采信其他专家票）
- **被审 Commit (Checkpoint Ref)**: `961bcfeee054a96d6b098e495277d0e659d7bd82`（工作区 HEAD = `origin/main` = 该 SHA；`src/` 与被审提交一致。未提交差量仅为 `STATUS.md`、`templates/review-request-template.md` 与本申请文件本身）
- **审查轮次 (Review Round)**: `2`
- **评审对象**: [`docs/reviews/2026-09-07-review-request-961bcfe.md`](2026-09-07-review-request-961bcfe.md)
- **前序基线**: `d042395`；前序 grok 报告 [`2026-09-07-review-result-d042395-grok.md`](2026-09-07-review-result-d042395-grok.md)（**6 项 P1**，不是申请/STATUS 所写的「2 项 P1 / 2 项 P2」）
- **对齐基准**: `docs/MACAO_REVIEW_GUIDELINES.md` v1.0 §2–§4、§7–§9；`docs/PROBE_TECHNICAL_DESIGN.md` §3/§5；PRD §1 / `PRODUCT-FACTS.md` F-23/F-24；UC-2 E7 / UC-11
- **目标定级**: L3 SCENARIO-VERIFIED / PG-2 全量认证，并提请 L4 RELEASE-READY / PG-3
- **审查结论 (Verdict)**: **不授予本轮增量 L3 全量认证；拒绝 L4 / PG-3**。既有编排引擎 L3 / PG-2（`4e38ed6` 轮）维持。
- **最终投票 (Vote)**: `NO_APPROVE`
- **证据**: `BLOCKING` × 2（P1）；L4 OPS 缺口维持；`ADVISORY` × 若干；**无 P0**

**结论：前序 8 项 P1 中，dry-run 空仓零写盘、Codex/Cursor/Kimi 项目隔离、三元组 pending 集合差、三道 quorum 合取、密钥脱敏、clean 快照、checkpoint 禁伪 `tests_passed`、`--force` E10 + 验收标准入信封，均被独立沙箱复放为真。但本轮把场景 C 写进探活 UI / UC-2 E7 / UC-11 后，操作面仍把待审项目导向 `task create`（且命令会成功建成 `CODING`），同时 Claude 会话仍按目录名回退并回填当前仓。按指引 §8，P1 未清零不得授予 L3 全量认证；L4 仍被 `live-run` 的 `mock-cli` + 默认 `auto_signoff=True` 单独否决。**

---

## 0. Reviewer 自审

- 不采信申请 §3「145/145、dry-run 100% CLEAN、8 项 P1 全部闭环」、处置单「ALL CLOSED」、STATUS「全面具备三大要素待落票」。
- 对每一条前序 P1 与本轮 Focus 1–5 写独立反例：空仓 CLI `--dry-run` 文件集差；伪造 `~/.codex` / `~/.cursor` / `~/.claude/projects/-macao` / `~/.kimi`；脏树 + 1/3 落票；席位够权重不够；`clean --all/--restore`；`--auto` 无 `--test-cmd`；`--force` + Type A 信封；`task adopt`；`task create` 遇未决提审单。
- 全量测试与独立探针均在 `/tmp` 沙箱或 `CliRunner` 临时目录执行；对宿主仓只跑了一次 `probe --dry-run`（见 P2-4 的 WAL sidecar）。
- **漏审登记**：无连续同类漏审。本轮强制项仍是指引 §9 B（测试只断言三元组 / Codex-Cursor-Kimi，就把 UI 与 Claude 写成已闭环）与 §9 C（把 UC-11 设计稿写成可执行下一步）。

强制自检：

| # | 项 | 本轮 |
|---|---|---|
| 1 | 字段/路径 vs 实际读取 | 三元组 `progress=REVIEW_PENDING` 已对；探活 UI Active Task 仍先看脏树；Claude `workspace` 写成查询仓而非会话仓 |
| 2 | 「已完成 / 100% / 全绿」 | 145/145 串行 **VERIFIED**；「8 项 P1 全部闭环」「场景 C 交付」**CONTRADICTED** |
| 3 | 确定性用语 | 「零伪造」「场景 C 无痛接入」未标目标 |
| 4 | YAML/JSON Schema | 8 份契约 docs↔src 逐字节一致 **VERIFIED** |
| 5 | P1 均附路径与复放 | 是 |

---

## 1. 结论综述 (Executive Summary)

`961bcfe` 相对 `d042395` 的代码返工是实打实的：前序 grok 报告里可被空仓脚本证伪的 dry-run 写盘、Codex/Cursor/Kimi 串话、pending 被脏树吃掉、quorum 只看 `minimum_winning_seats`、无脱敏、`clean` 先删后「恢复」、`--auto` 写 `tests_passed: true`、`--force` 孤立僵尸任务，本轮机验已翻转为 PASS。145 项测试（含 `tests/test_p1_closures_and_regressions.py` 10 项）串行全绿，不能被用来否掉这些闭环。

阻断来自本轮**新写入的操作面**，以及 P1-2 声称覆盖、测试未覆盖的 Claude 回退路径：

1. 探活在「有未决提审单 + 工作区脏」时，内部三元组已是 `REVIEW_PENDING`，但摘要表与下一步文案仍是 `UNTRACKED DEV` / `macao task create`；`task create` 不实现本轮写入的 UC-2 E7，会成功创建 `CODING` 任务。干净待审时摘要表改写 `macao task adopt`，Click 子命令表里没有 `adopt`。
2. `SessionLocator._find_claude_sessions` 在完整规范化目录不存在时，回退到 `~/.claude/projects/-<dirname>`，并把 `workspace` 填成**当前查询路径**。这与处置单「Claude 全量统一为规范化绝对路径精确匹配」直接矛盾，复放可将无关项目的会话贴到 `/tmp/unrelated/macao`。

L4 / PG-3：`src/macao/workflow/live_runner.py` 三名 Reviewer 仍为 `cli: "mock-cli"`，`run_live_cycle(..., auto_signoff: bool = True)`。与 `d042395` 轮、`b76cbfb` 轮同一条 OPS 判据，本轮 27 个文件未改该路径。

---

## 2. 申请机验（独立复跑，不采信粘贴）

| 声明 | 本机 | 判定 |
|---|---|---|
| 基线 `961bcfe` = `origin/main` | `HEAD=961bcfeee054a96d6b098e495277d0e659d7bd82` | **VERIFIED** |
| 本提交 27 files / +2379 / -237 | `git diff --shortstat 961bcfe^..961bcfe` 一致。`d042395..961bcfe` 另含 `bb89ce6`+`519398d`，为 29 files / +2594/-228，不作为对本提交计数的否证 | **VERIFIED**（口径钉在单提交） |
| `PYTHONPATH=src python3 -m unittest discover tests` 145/145 | `Ran 145 tests in 47.321s OK` | **VERIFIED** |
| `python3 -m compileall -q src tests` | rc=0 | **VERIFIED** |
| 双 Schema 8 份逐字节一致 | `docs/schemas/*.schema.json` ↔ `src/macao/schemas/` 8/8 SAME | **VERIFIED** |
| `docs/reviews/` 191 份（结论 146 / 申请 43 / 处置 1 / STATUS 1） | **git HEAD**：reviews 下 `*.md` = **190**，申请 **42**，`review-result-*` **142** + methodology 2 + review-2.5-2 两份 = 结论类 146，处置 1，STATUS 1。工作区另有未跟踪的本申请 → 191/43 | 口径含未入库申请时 **PARTIALLY_VERIFIED**；HEAD 上申请数是 42 |
| 空仓 `probe --dry-run` 不创建 `.macao/` | 独立临时 git 仓 + mock `macao.yaml`：`new_files=[]`，`.macao` 不存在，rc=0 | **VERIFIED**（原 P1-1） |
| Codex/Cursor 跨项目返回 `[]`，命中时 `workspace` 为真实 cwd；Kimi 恒 `[]` | 伪造 HOME 复放全部成立 | **VERIFIED**（原 P1-2 三路） |
| 1/3 落票 + 脏树 → `REVIEW_PENDING` 且 Next 列出缺席 | `missing=['rev-codex','rev-grok']`，`next=Await pending reviews from: rev-codex, rev-grok` | **VERIFIED**（三元组层） |
| 探活 UI 在待审时不把状态说成 ACTIVE_DEV / 不建议 `task create` | 同场景摘要表同时出现 `AWAITING REVIEW VERDICTS` 与 `UNTRACKED DEV (Run 'macao task create' to adopt)`，底部指引仍是 `task create` | **CONTRADICTED**（P1-1） |
| `macao task adopt` 可接管场景 C | `cli task [OPTIONS]`：`No such command 'adopt'`。子命令仅 `probe/create/recover/checkpoint/cancel` | **CONTRADICTED**（P1-1） |
| UC-2 E7：未决提审单时拒绝 `task create` | 同沙箱 `task create --title ...` rc=0，建成 `CODING` | **CONTRADICTED**（P1-1） |
| Claude 精确路径匹配、不回填当前仓 | 仅存在 `~/.claude/projects/-macao` 时，查询 `/tmp/unrelated/macao` 得到 `session_id=sess-foreign` 且 `workspace=/tmp/unrelated/macao` | **CONTRADICTED**（P1-2） |
| quorum 三合取 | `M=2,S=2,W=3, ready=2, weight=2.0` → `achievable=False`，blocking 含 `effective weight 2.0 < weight quorum 3.0` | **VERIFIED**（原 P1-4） |
| `mask_secrets` 覆盖申请所列 Key/Token/Bearer/DB 密码 | `sk-` / `ghp_` / Bearer / URL 密码均变为 `******`；AWS `AKIA…` 未掩（申请未列 AWS，不升级 P1） | 声明范围 **VERIFIED** |
| `clean` 默认保 `state.db`；`--all` 写 `.macao.bak.<ts>`；`--restore` 还原运行时 | 三步复放成立 | **VERIFIED**（原 P1-6） |
| `--auto` 不写 `tests_passed: true`，FSM 停在 CODING | `.dev.yml` 为 false，输出 `tests have not passed` | **VERIFIED**（原 P1-7） |
| `--force` 走 E10；验收标准进 Type A | 旧任务 `CANCELLED`；`message_queue` payload 含 `Explicit criterion 1` | **VERIFIED**（原 P1-8） |
| live-run / L4 OPS | 三 Reviewer `mock-cli`；`auto_signoff: bool = True` | L4 OPS **CONTRADICTED** |

独立反例摘要：

```text
empty-repo probe --dry-run -> new_files=[] ; .macao absent          # P1-1 closed
codex/cursor foreign cwd -> [] ; kimi ~/.kimi -> []                # P1-2 closed for those CLIs
claude ~/.claude/projects/-macao + query /tmp/unrelated/macao
  -> session_id=sess-foreign workspace=/tmp/unrelated/macao        # P1-2 residual
1/3 votes + dirty -> executor.progress=REVIEW_PENDING (OK)
  UI Active Task = UNTRACKED DEV / 'macao task create'             # P1-1
task adopt -> No such command 'adopt'                              # P1-1
task create with pending request -> CODING (E7 not implemented)    # P1-1
Last of feat+docs+chore stack = "chore: bump deps"                 # P2
M=2 S=2 W=3 ready=2 weight=2 -> achievable=False                   # P1-4 closed
mask_secrets: claimed patterns OK; AKIA still visible              # P3
clean default keeps state.db; --all snapshot; --restore restores   # P1-6 closed
checkpoint --auto tests_passed=false blocks FSM                    # P1-7 closed
--force E10 + acceptance in DEVELOPMENT_STARTED payload            # P1-8 closed
live_runner reviewers cli=mock-cli ; auto_signoff=True             # L4
Ran 145 tests in 47.321s OK ; compileall 0 ; schema 8/8 SAME
```

---

## 3. 已确认与对齐项 (Verified & Aligned Items)

相对 `d042395` 轮 grok 报告，下列原 P1 **本轮独立复放为闭环**（不抵消第 4 节新 P1）：

- [x] **原 P1-1 dry-run 写盘**：`TeamProber._write_probe_log` 入口 `if self.dry_run: return None`（`prober.py:269-270`），`probe()` 仅在 `not self.dry_run` 时写盘（`:859-862`）。CLI `probe --dry-run` 传入 `dry_run=True`（`cli/main.py:335-336`）。空仓文件集差为空。`test_p1_1_prober_dry_run_zero_disk_mutation` 现断言 `.macao/logs/probe` 不存在。
- [x] **原 P1-2 Codex / Cursor / Kimi**：Codex 读 `state_*.sqlite` 且 `Path(cwd).resolve() == resolved_proj`，`workspace` 保留真实 cwd；Cursor 只收 `meta.json.cwd` 精确相等；Kimi 恒返回 `[]`。跨项目反例 PASS。
- [x] **原 P1-3 三元组层**：`has_pending_request` 优先于脏树（`prober.py:595-611`）；`missing_reviewers` 为配置席位与文件名集合差（`:253-257`）；`next_planned` 列出缺席 id。最新申请改为 `mtime` 排序（`:205`），不再纯字典序。
- [x] **原 P1-4**：`quorum_achievable` 为 `ready>=min_winning AND ready>=seat_quorum AND weight>=weight_quorum`（`:798-802`），blocking 分列短板。
- [x] **原 P1-5**：`src/macao/utils/secrets.py` 实装；`SecretMaskingFormatter`、PTY `_read_loop`、`live_dispatcher` 落盘、`macao logs` 回显均调用 `mask_secrets`。申请所列样本无泄漏。
- [x] **原 P1-6**：默认只删 `.macao/worktrees/*`；`--all` 先 `copytree` 为 `.macao.bak.<ts>` 再删；`--restore` 从目录快照还原运行时，不再「先 rmtree 再只拷 yaml」。
- [x] **原 P1-7**：`--auto` 默认 `tests_passed=False`；仅 `--test-cmd` 退出码 0 或 `--tests-exempt` 可通过 `check_development_checkpoint`（`orchestrator.py:273-275`）。
- [x] **原 P1-8**：`--force` 调用 `cancel_task` → E10；CLI 把 `--acceptance` 收成 list；Type A payload 含用户原文（独立查询 `message_queue` 证实）。`test_p1_8_*` 未断言信封，但代码路径成立。
- [x] **Pi 适配器骨架**：`PiAdapter` 注册进 prober / dispatcher / wizard / SessionLocator；单测覆盖 capabilities / preflight mock / 会话目录绑定。
- [x] **既有引擎场景测试未回退**：145/145 含共识/超时/返工/E2E mock。

---

## 4. 阻断性缺陷 (P0 / P1 Blocking Issues)

未发现新的 P0（无静默自动合并、无把 `tests_passed` 再写回 true）。

### P1-1 场景 C 操作面 CONTRADICTED：待审时引导 `task create`，命令会建成 CODING；`task adopt` 不存在

- **位置**:
  - `src/macao/cli/ui.py:364-409`（脏树优先于 pending；写死 `macao task create` / `macao task adopt`）
  - `src/macao/cli/main.py:364-438`（`task create` 只拦 `active_task` 与 quorum，不看物理提审单）
  - Click 任务子命令：`probe/create/recover/checkpoint/cancel`（无 `adopt`）
  - 本轮文档：`docs/usercases/UC2-task-create.md:77` E7；`docs/usercases/UC11-scenarioc-inflight-adoption.md:54-61`；`PRODUCT-FACTS.md` F-24；探活 UI 本轮 +23 行
- **严重级别**: `P1` (BLOCKING)
- **现象描述**:
  1. 三元组层已把「未决提审 + 脏树」定为 `REVIEW_PENDING`（原 P1-3 的代码修复成立）。
  2. 同一份 `render_team_probe_report` 在 `not git.is_clean` 时**不再进入** pending 分支，Active Task 写成 `UNTRACKED DEV (Run 'macao task create' to adopt)`，底部指引同样是 `task create`。表格上半仍显示 `AWAITING REVIEW VERDICTS`，同一屏自相矛盾。
  3. 按该指引执行 `macao task create`：**成功**，状态 `CODING`，Executor 被指派实现。这正是 UC-11 §1.1 所称「灾难性状态倒退」，也是本轮写入的 UC-2 E7 / F-24 明文禁止的行为。
  4. 若工作区干净且仅有待审单，摘要表改写 `SCENARIO_C (Adopt via 'macao task adopt' / UC-11)`。`python3 -m macao.cli.main task adopt` → `Error: No such command 'adopt'`。
- **复现证据 / 命令**:
  ```text
  # 沙箱：1/3 落票 + dirty.txt
  executor.progress = REVIEW_PENDING          # 数据层 OK
  probe CLI 输出含:
    Review Baseline ... AWAITING REVIEW VERDICTS
    Active Task ... UNTRACKED DEV (Run 'macao task create' to adopt)
    Run 'macao task create --title "..."' to adopt existing changes

  macao task adopt
    -> No such command 'adopt'   (rc=2)

  macao task create --title "Should be blocked by E7"
    -> Task '... successfully created'  Initial State: CODING  (rc=0)
  ```
  `tests/test_p1_3_progress_triplet_review_pending_with_partial_votes` 只断言 `executor.progress` 与 `missing_reviewers`，不断言 UI，也不断言 `task create` 被拒绝 → **假绿**。
- **修复建议**:
  1. UI 与底部指引与三元组同一优先序：pending 高于脏树；待审时禁止推荐 `task create`。
  2. 实现 UC-2 E7：存在未决物理提审单时 `task create` fail-closed（除非显式覆盖开关，且不得作为默认）。
  3. 要么实现 `macao task adopt`（按 UC-11 把任务建成 `WAITING_REVIEW`、只派缺票 Reviewer），要么从 UI / UC-2 / UC-11 / doctor 导流中删除该命令名，改成「设计稿、本轮不可执行」。
  4. 补测试：脏树+部分落票时 CLI 输出不含 `task create`；`task create` 在 pending 下 rc≠0；若保留 adopt，则有正向接管测试。

### P1-2 Claude 会话仍按目录名回退，并把 `workspace` 伪造成当前仓

- **位置**: `src/macao/adapter/session_locator.py:144-217`（回退 `:154-163`；`workspace: str(resolved_proj)` 在 `:214`）
- **严重级别**: `P1` (BLOCKING)
- **现象描述**: 处置单写「Claude / AGY / Pi：全量统一为规范化工作区路径精确匹配」。AGY/Pi/Codex/Cursor 的精确比对成立。Claude 在 `-<full-sanitized-path>` 不存在时，改用 `-<project.name>`。命中后 **不读取会话真实路径**，把 `workspace` 写成调用方 `project_path`。任意两个同名目录会串话，且报告里看起来像「本仓会话」。
- **复现证据 / 命令**:
  ```text
  HOME 仅有 ~/.claude/projects/-macao/sess-foreign.jsonl
  SessionLocator.list_sessions("claude", Path("/tmp/unrelated/macao"))
    -> [{session_id: "sess-foreign",
         session_name: "hello from other macao",
         workspace: "/tmp/unrelated/macao"}]    # 非空，且 workspace 被回填
  ```
  `test_p1_2_*` 只覆盖 Codex/Cursor/Kimi，不覆盖 Claude 短名回退。
- **修复建议**: 删除 name-only 回退；仅当规范化绝对路径目录存在时返回会话；`workspace` 必须来自会话记录而非查询参数。补「同名异路径 → `[]`」否定测试。Kimi 的 fail-closed 模式可直接套用。

---

## 5. L4 / PG-3（单独否决，不与上表混写）

指引 §2.1 / §3.3：L4 需要 OPS VERIFIED，且用户可见人工接管实机演练，且 P0/P1 为零。

`src/macao/workflow/live_runner.py:54-58` 三名 Reviewer 仍为 `cli: "mock-cli"`；`:75` `auto_signoff: bool = True`。`macao live-run` 默认自动签字。本轮提交未改该文件。即使 P1-1、P1-2 当天修好，本项仍单独阻断 L4。与 `d042395` 轮 grok 第五节同一条。

---

## 6. 建议性问题 (P2 / P3 Advisory Issues)

- `P2-1` **Last 仍不按设计过滤 chore/docs**：`PROBE_TECHNICAL_DESIGN.md` §3 要求跳过 merge/chore。实现只跳 `docs(review)`（`prober.py:193`）。feat→docs→chore 栈的 Last = `chore: bump deps`。本轮处置单未宣称修此项，不升 P1。
- `P2-2` **有 `active_task` 时仍展示 `NOT_SPAWNED`**（`prober.py:654-655`）。无任务时 In-repo 路径仍成立。
- `P2-3` **向导在 PATH 无 CLI 时 fail-open 填 6 个带版本号的虚构候选**（`wizard.py:606-614`）。上轮 P2，未动。
- `P2-4` **已存在 WAL 模式 `state.db` 时，`mode=ro` 仍会创建 `state.db-wal` / `state.db-shm`**。空仓 dry-run 不创建 `.macao`，原 P1-1 不因此重开；但「100% 零写盘」对存量库不成立。本机对宿主仓一次 `--dry-run` 新建了这两个 sidecar（gitignored）。
- `P2-5` **`PiAdapter.preflight` 在 `--version` 空输出时写死 `0.85.1`，并无条件 `auth_valid=True`**（`pi.py:54-60`）；二进制路径硬编码 `/home/debian/.nvm/versions/node/v24.15.0/bin/pi`。与「不捏造」不一致，属适配器层 fail-open。
- `P2-6` **`_sanitize_session_name` 未走 `mask_secrets`**，正则弱于全链路脱敏（只拦部分 `sk-`）。会话标题里的 `ghp_` / `ant-` 可能进探活报告。
- `P2-7` **默认 `macao clean` 删除 `.macao/worktrees/` 下全部目录**，注释写「已完成 worktree」，实现无完成态判断；也未走 `git worktree remove`。
- `P3-1` 申请/STATUS 把前序 grok 票写成「2 项 P1 + 2 项 P2」。原文是 `BLOCKING × 6`（P1-1～P1-6）。
- `P3-2` `AGENTS.md` 仍写 126 / 128 tests，本轮实测 145。
- `P3-3` 本申请信封 `sha256` 仍是 64 个 `0`；`tests_passed: true` 写在申请机器信封里，与 P1-7 叙事并置，易误读。
- `P3-4` 申请「reviews 191 / 申请 43」计入了尚未入库的本申请；git HEAD 为 190 / 42。

---

## 7. 前序 8 项逐条对照（避免「全部闭环」被误读）

| 原编号 | 本轮机验 | 定级影响 |
|---|---|---|
| P1-1 dry-run 写 probe log | 空仓 CLI **CLOSED** | 不阻断 |
| P1-2 Codex/Cursor/Kimi | **CLOSED** | 不阻断 |
| P1-2 Claude 精确匹配（处置单加码） | **未闭** → 本轮 P1-2 | 阻断 |
| P1-3 三元组 pending / 缺席名单 | 数据层 **CLOSED**；UI/create **未闭** → 本轮 P1-1 | 阻断 |
| P1-4 quorum 三合取 | **CLOSED** | 不阻断 |
| P1-5 脱敏 | 声明范围 **CLOSED** | 不阻断 |
| P1-6 clean 快照 | **CLOSED** | 不阻断 |
| P1-7 tests_passed | **CLOSED** | 不阻断 |
| P1-8 force + acceptance | **CLOSED** | 不阻断 |
| 场景 C / UC-11 / F-24 | 规范入库，运行时 **未落地** | 计入 P1-1 |
| L4 live-run | **未动** | 单独拒 L4 |

---

## 8. 建议闭环顺序与验收

1. **P1-1**：统一 pending 优先序到 UI 与 `task create`；删除或实现 `task adopt`；补「脏树+部分落票不得 create」「CLI 输出不得推荐 create」两条否定测试。
2. **P1-2**：去掉 Claude 短名回退；`workspace` 不得回填查询路径；补同名异路径反例。
3. **L4**：真实 CLI 至少一轮非全同意 + 用户命令路径 HOLD → `override resolve` / `merge approve`。不要再拿 mock `live-run` 申请 PG-3。
4. 文档：STATUS/申请不要把 grok 上轮 6 项 P1 改写成 2 项；UC-11 在命令落地前保持「设计稿」且 UI 不得当已交付。

验收时请再跑：脏树+pending 的 **CLI 全文**（不要只测 JSON 三元组）、`task create` 遇提审单、Claude 同名异路径、空仓 dry-run 文件集差、既有 145 项回归。不要只贴 145/145。

---

## 9. 准入建议

- **本轮增量**：**不授予** L3 SCENARIO-VERIFIED / PG-2 全量认证。探活内部不变量大部分已修，但本轮自己写上的场景 C 下一步与 Claude「零伪造」仍可被独立脚本证伪。
- **既有编排引擎**：**维持** L3 SCENARIO-VERIFIED / PG-2。
- **L4 RELEASE-READY / PG-3**：**拒绝**。P1 未清零，且 live-run 仍为 mock + 默认自动签字。

---

## 5. Reviewer 自审记录 (Self-Audit Log)

- [x] 已对照 `961bcfe^..961bcfe` 27 个文件与申请清单
- [x] 已串行执行 `unittest discover tests`（145/145）与 `compileall`
- [x] 已用独立 `/tmp/probe_961bcfe.py` 复放 Focus 1–5 及场景 C 命令面（不采信 `test_p1_*` 绿条）
- [x] 未把 WAL sidecar、Last/chore、AWS AKIA、Pi 版本捏造升为 P1
- [x] 未发现未报告的 P0

---

## 伴随机器信封：`.macao/.reviews/r2/grok.review.yml`

```yaml
version: "1.0"
task_id: "task-20260907-orchestrator-p1-remediation"
checkpoint_ref: "961bcfe"
review_round: 2
reviewer:
  id: "grok"
  role: "reviewer"
  cli: "cursor-grok"
vote: "NO_APPROVE"
opinion:
  status: "REJECTED"
  confidence: 0.93
  summary: "原 P1-1/4/5/6/7/8 与 Codex-Cursor-Kimi 隔离已独立复放闭环；阻断为场景 C 操作面（UI 建议 task create 且命令会建成 CODING，task adopt 不存在）以及 Claude 目录名回退伪造 workspace。L4 仍因 live-run mock-cli 否决。"
full_document:
  path: "docs/reviews/2026-09-07-review-result-961bcfe-grok.md"
  evidence_commit: "961bcfe"
  sha256: "0000000000000000000000000000000000000000000000000000000000000000"
items:
  - issue_id: "grok/P1-1"
    disposition_class: "MUST_FIX"
    severity: "blocker"
    title: "Probe UI and task create regress pending Scenario C into CODING; task adopt does not exist"
  - issue_id: "grok/P1-2"
    disposition_class: "MUST_FIX"
    severity: "blocker"
    title: "Claude SessionLocator basename fallback spoofs workspace to the queried project"
  - issue_id: "grok/L4-OPS"
    disposition_class: "MUST_FIX"
    severity: "blocker"
    title: "live-run still hardcodes mock-cli reviewers and default auto_signoff=True"
```
