# MACAO CLI / 探活 / 全周期编排合并复审结论（`d042395`）

- **评审日期**：2026-09-07
- **评审人**：grok（独立复审；不采信申请粘贴输出，不采信 `STATUS.md` 定级句，不采信其他专家票）
- **评审对象**：[`docs/reviews/2026-09-07-review-request-d042395.md`](2026-09-07-review-request-d042395.md)
- **申请声称基线**：`d042395`（`origin/main`）
- **工作区 HEAD**：`519398d`（`d042395` 之后 2 个文档提交：`bb89ce6` 登记本申请 + `519398d` 方法论说明；`src/` 与 `d042395` 一致）
- **审计范围（实测）**：`95b7b35..d042395` = **20** commits、**46** files、`+5108 / -193`（与申请后半句一致）。`f9ff6bf..d042395` 仅为 **15**（含 `f9ff6bf` 为 16），与「f9ff6bf 至 d042395 的 20 个提交」前半句不一致。
- **对齐基准**：`docs/MACAO_REVIEW_GUIDELINES.md` v1.0 §2–§4、§7–§9；`docs/PROBE_TECHNICAL_DESIGN.md`；PRD §1 / `PRODUCT-FACTS.md` 不介入原则
- **定级申请**：L3 SCENARIO-VERIFIED / PG-2 全量认证，并提请 L4 RELEASE-READY / PG-3
- **机器票**：`NO_APPROVE`（不授予本轮 L3 全量认证；**拒绝 L4 / PG-3**）
- **证据**：`BLOCKING` × 6（P1）；L4 既有 OPS 缺口维持；`ADVISORY` × 若干；**无 P0**

**结论：不授予本轮增量 L3 SCENARIO-VERIFIED / PG-2 全量认证；不通过 PG-3；不授予 L4 RELEASE-READY。既有编排引擎 L3 / PG-2（`4e38ed6` 轮）维持，不外推到本轮探活/CLI 交付面。**

本轮增量把「零副作用探活、物理事实三元组、会话定位、灾难回滚、日志脱敏」写成可授予 L3/L4 的强声明。独立沙箱与宿主复放表明：这些声明在代码路径上可被证伪。128/128 与 Schema 双副本成立，但只覆盖「不创建 `state.db` / mock 团队探活」一类窄断言，不能把设计专文 §2.2 的「100% 无痕」或申请 §4 的 ELS 实录外推为已验证。

指引 §2.1 L4 仍要求 **OPS VERIFIED + 用户可见人工接管实机演练 + P0/P1 为零**。`LiveWorkflowRunner` 三名 Reviewer 仍硬编码 `cli: mock-cli`，默认 `--auto-signoff`。与 2026-08-31 `b76cbfb` 轮 grok 拒绝 L4 的 OPS 判据同一条，本轮未闭环。

---

## 0. Reviewer 自审

- 不采信申请 §4「128/128、dry-run 零副作用、ELS Last=1ad706b / Session `b5640a62-…`、脱敏掩码」。
- 对每一条强声明写反例：空仓 `--dry-run` 文件集差；伪造 `~/.codex` / `~/.cursor` / `~/.kimi`；一票结果文件关闭 pending；`M=2,S=3,W=3` 法定人数；`clean --restore` 删除 `.macao`；全库 `mask|redact` 检索。
- ELS 上调用 `TeamProber.probe()` 时 **补丁掉 `_write_probe_log`**，避免再给第三方仓制造副作用；对照已存在的 `probe_20260907_154455.log`。
- 全量测试与独立探针并行时曾出现 `test_session_locator_discovery` 1 次 FAIL；**随后串行复跑 `Ran 128 tests … OK`**。不把并行干扰写成产品 P1。
- **漏审登记**：无连续同类漏审。本轮强制项是「作者把设计目标写成已验证事实」（指引 §9 C）以及「测试只断言 `state.db` 不存在就声称零副作用」（§9 B）。

强制自检：

| # | 项 | 本轮 |
|---|---|---|
| 1 | 字段/路径 vs 实际读取 | 三元组 `Next` 设计要名单，实现是固定句；会话 `workspace` 被写成当前仓而非索引里的仓 |
| 2 | 「已完成 / 100% / 全绿」 | 申请 ELS 实录与 dry-run 无痕 **CONTRADICTED**；128/128 串行复跑 **VERIFIED** |
| 3 | 确定性用语 | 「100% 零修改」「摒弃 NOT_SPAWNED」「脱敏掩码」未标目标 |
| 4 | YAML/JSON Schema | 8 份契约 docs↔src 逐字节一致 **VERIFIED** |
| 5 | P1 均附路径与复放 | 是 |

---

## 一、申请机验（独立复跑，不采信粘贴）

| 声明 | 本机 | 判定 |
|---|---|---|
| 基线 `d042395` = `origin/main` | `HEAD=519398d` = `origin/main`；相对 `d042395` 仅 3 个文档文件（申请 + STATUS + AGENTS） | 代码基线 **VERIFIED**；申请钉 SHA **过时** |
| 20 commits / 46 files / +5108 -193 | `git rev-list --count 95b7b35..d042395` = 20；`git diff --stat 95b7b35..d042395` 46 files, +5108/-193。表内 20 个 SHA 均可 `rev-parse` | **VERIFIED**（范围口径见 P3） |
| `PYTHONPATH=src python3 -m unittest discover tests` 128/128 | 串行：`Ran 128 tests in 44.276s OK`。与探针并行的一次：128 ran / 1 FAIL（`test_session_locator_discovery`），不可复现 | 串行 **VERIFIED** |
| `compileall -q src tests` 0 Errors | rc=0 | **VERIFIED** |
| Schema 8 份逐字节一致 | `docs/schemas/*.schema.json` ↔ `src/macao/schemas/` 8/8 无 diff（目录级仅 `__init__.py` / README / `__pycache__`） | **VERIFIED** |
| 全库 Markdown 0 控制字符；申请写 228 份 | 工作区 `*.md` **230** 份、C0 控制字节 **0**；`git ls-files '*.md'` = **229** | 无控制字符 **VERIFIED**；份数 **CONTRADICTED** |
| `git diff --check 95b7b35..d042395` | rc=2：`ui.py`/`templates/README.md`/若干测试 EOF 空行 + `test_clean_and_rollback.py:88` trailing whitespace | 申请未写此项；记 P3 |
| 12 份 templates | `find templates -type f` = **15**（6 份 md 指南 + 8 份 manifests + `README.md`） | 申请「6+8=12」漏 README 与计数；结构在 |
| `macao probe --dry-run` 零 DDL / 零改文件 | 空仓：`state.db` 不创建 **真**；同时创建 `.macao/logs/probe/probe_*.log`；横幅仍打印 `DRY-RUN (Pure Read-Only)` | **CONTRADICTED**（P1-1） |
| ELS：恢复 agy session `b5640a62-…`；Last=`1ad706b`；Now=待审；Reviewer=In-repo | 现配置 executor=`dev-opencode`，session=`ses_fb1844eedffeh8a0xeOU6SALyy`；Last=`4bad9f3`；HEAD=`5b283d4`；progress=`ACTIVE_DEV (UNTRACKED)`（5 dirty）；latest request 文件名排序落到 `…-v3-r2-r9.md`，baseline=`null`；In-repo 展示成立 | 申请 ELS 实录 **CONTRADICTED**；In-repo 无任务路径 **VERIFIED** |
| `test_logger_and_audit.py` 覆盖脱敏掩码 | 5 个测试：落盘 / gitignore / audit CLI / logs / reviewer log。全库无 `mask`/`redact` 实现函数 | **CONTRADICTED**（P1-5） |
| live-run / L4 OPS | `live_runner.py` 三 Reviewer `cli: "mock-cli"`；`auto_signoff: bool = True` | L4 OPS **CONTRADICTED** |

独立反例摘要：

```text
empty-repo probe --dry-run -> created .macao/logs/probe/probe_*.log ; state.db absent
banner contains "DRY-RUN (Pure Read-Only)"
pending: 0 results -> REVIEW_PENDING; 1 muse result file -> pending=False, awaiting=[]
Next never contains reviewer ids (canned sentence)
active_task -> worktree display ".../r1 (NOT_SPAWNED)"
codex last-line of global index stamped onto proj_a
kimi ~/.kimi exists -> session_id="auto-discovered"
cursor latest global chat unbound to project
clean --restore -> rmtree .macao THEN copy yaml.bak
quorum M=2 S=3 W=3 ready=2 -> achievable=True can_dispatch=True (design formula False)
Last of chore/docs/feat stack = "docs: handbook" (design said skip chore)
secrets: flag-only in wizard.yaml ; no mask/redact helper
live-run hardcoded mock-cli x3
ELS probe: Last=4bad9f3 not 1ad706b; Now=ACTIVE_DEV not REVIEW_PENDING
ELS latest_request=v3-r2-r9.md baseline=null despite 4bad9f3 results existing
128/128 OK (serial); compileall 0; schema 8/8 SAME
```

---

## 二、已对齐 / 已确认项（不抵消 P1）

1. **SQLite 探活连接本身是 `mode=ro`**：`prober.py:78,99` 在 `state.db` 存在时用 URI 只读；文件不存在则跳过，不跑 `DatabaseManager` DDL。这项与「不创建 state.db」一致。
2. **无 active_task 时 Reviewer 工作区走 In-repo**：`prober.py:628-635` 文案 `In-repo (Shared Workspace / Direct Review)`；ELS 四席实测如此。`git worktree list --porcelain` 有读取路径。
3. **`macao init` 向导主路径可用**：数字/`1-4`/`前4位` 解析、最少 2 席循环拒绝、4 席时 `minimum_winning_seats=3` 与 `test_reviewer_selection_parsing_and_4_reviewers_flow` 一致；生成 YAML 带中文注释并通过 `validate_config`。
4. **`task checkpoint` / `task cancel` / `merge execute` 命令存在且接到既有 Orchestrator / MergeController**（含 `merge --ff-only`）。本轮未做真实多 CLI 联调，不把接线写成 L4 OPS。
5. **PTY ANSI 剥离存在**：`PTYSession._read_loop` 调 `strip_ansi`；与「密钥掩码」不是同一件事。
6. **编排引擎既有 L3 场景测试未在本轮被这 20 个提交拆掉**：串行 128/128 含共识/超时/返工/E2E mock 路径。

---

## 三、P0

未发现需单列的 P0（无数据损坏级「静默自动合并」新回归；本轮问题是探活/运维声明被证伪，以及 L4 OPS 仍缺）。

---

## 四、P1：进入本轮 PG-2 全量认证 / 任何 L4 之前必须修正

### P1-1　`--dry-run` / 「Pure Read-Only」/ 设计 §2.2 零副作用 CONTRADICTED

申请 §1.2：「`--dry-run` … 绝不擅自创建空数据库文件或执行 DDL，保证 100% 零修改、零写锁」。设计专文 §2.2 更强：「绝对不创建空数据库文件或**空目录**」「100% 幂等与无痕性」。CLI 横幅：`DRY-RUN (Pure Read-Only)`（`cli/ui.py:187`）。

**实现**：`TeamProber.probe()` 结尾无条件 `_write_probe_log`（`prober.py:811-813`）。该函数 `log_dir.mkdir(parents=True, exist_ok=True)` 后写 `probe_<ts>.log`（`:247-250,298`）。`dry_run` 只进日志正文（`:260`），**不门控写盘**。

**复放**（空 `git init` + mock `macao.yaml`）：

```text
created=['.macao/logs/probe/probe_20260907_154757.log']
state.db exists = False
```

同一份设计专文 §4.1 / §5 又写「无论是否 `--dry-run` 都落盘审计」。原则与实现说明自相矛盾；申请与 UI 采信的是「100% 无痕」那一侧。

`test_probe_root_command_dry_run_zero_side_effects` 只断言 `state.db` 不存在（`tests/test_team_probe_and_dispatch.py:92-93`），对 `.macao/` 目录无断言 → **假绿**。

这是本轮探活的核心不变量，不是文档笔误。

### P1-2　`SessionLocator` 对 Codex / Cursor / Kimi 捏造项目绑定

申请 §1.2 / 设计「零 LLM 的**项目绑定**会话」。实现：

- **Codex**（`session_locator.py:165-194`）：读 `~/.codex/session_index.jsonl` **最后一行**，不比较 workspace，然后把 `workspace` 写成**当前** `project_path`。
- **Cursor/agent**（`:197-216`）：取 `~/.cursor/chats/` 下全局最新目录，不绑定当前仓。
- **Kimi**（`:222-232`）：`~/.kimi` 存在即返回 `session_id: "auto-discovered"`，无真实会话 ID。

**复放**（伪造 HOME）：Codex 索引里是 `sess-other-project`（属于 proj_b），对 proj_a 查询得到 `workspace=proj_a` + 同一 `session_id`。Kimi 空目录 → `auto-discovered`。Cursor 得到无关 `chat-zzz`。

这与 PRODUCT-FACTS「不假造进度/上下文」同类：把**别的项目或主机级最新聊天**贴到当前仓。agy/opencode 路径有目录匹配，不能覆盖这三路。

### P1-3　进度三元组算法与设计 §3 / 申请 §1.2 不一致（可证伪）

设计 §3 写明：

1. `Last` 过滤 merge/chore；
2. `Now` **先**看未终局提审单，再看脏树；
3. `Next` 在 `REVIEW_PENDING` 时列出**待落票审查员名单**。
4. 最新提审单应对账 `*-review-result-*.md`。

**实现与复放**：

| 设计 | 代码 | 实测 |
|---|---|---|
| Last 跳过 chore | 只跳过 `msg.startswith("docs(review)")`（`prober.py:191`） | feat+chore+docs 栈的 Last = `docs: handbook` |
| Now 提审优先于脏树 | 先 `not is_clean` → `ACTIVE_DEV`，再 pending（`:565-575`） | ELS：`has_pending_request=True` 但 executor progress=`ACTIVE_DEV (UNTRACKED)`（5 dirty） |
| Next 列出缺票人 | 固定句 `Await reviewer evaluations and verdicts before next commit`（`:575`） | 句中无 `rev-*` |
| 一票未齐仍 pending | `has_pending_request = (len(matching)==0)`（`:238`）；matching 是 **文件名包含 baseline SHA 的任意 result** | 仅 muse 一份 `…-abc1234-muse.md` → pending=False，三席 `awaiting=[]`，progress 被脏文件改成 ACTIVE_DEV |
| 最新申请 | `sorted(glob)` 字典序（`:203`） | ELS 同日文件取到 `…-v3-r2-r9.md` 而非 `…-4bad9f3.md` |
| 无 7 位 hex 的文件名 | baseline=`null` 则 **永远** `has_pending_request=True` 且 matching 为空（`:239-240`） | `v3-r2-r9` 已有 grok/claude/muse/kimi 结果，探针仍 pending；Reviewer 显示 `AWAITING_REVIEW (@ HEAD)` |

申请 §4 ELS「Last=1ad706b / Now=Pending review」在本机为假：Last=`4bad9f3`，HEAD=`5b283d4`，Now=`ACTIVE_DEV`。该「实战证据」不能作为 L3 场景证明。

无 MACAO `state.db` 的场景 C 正是本轮要卖的能力；上述算法在 ELS 上已经走偏。

### P1-4　派发门禁法定人数只用 `minimum_winning_seats`，丢掉 S 与 W

设计 §5：

```text
QuorumAchievable = (R_ready ≥ S) ∧ (R_ready ≥ M) ∧ (W_avail ≥ W_req)
```

代码（`prober.py:758-761,777-786`）：

```text
quorum_achievable = ready_reviewers_count >= min_winning   # 仅 M
```

`seat_quorum_required` / `weight_quorum_required` 写入报告但不参与判定。

**复放**：4 席、2 个 `mock-cli` READY、2 个不存在的 CLI；`M=2, S=3, W_req=3` → `achievable=True`，`can_dispatch=True`。按设计公式应为 False / BLOCKED。这正是专文 §1.1 要防的「盲目派发」。

### P1-5　「API Key / Token 脱敏掩码」无实现；申请把未覆盖的测试写成证据

申请 §1.3、§5 核验表、§4「`test_logger_and_audit.py`: 日志捕获、**脱敏掩码**、Session 日志」。

`src/macao/` 内 `secrets_masking` 仅出现在 `wizard.py` / `main.py` 生成的 YAML 开关。无 `mask`/`redact`/`sanitize_secret` 函数。`tests/test_logger_and_audit.py` 五个用例均不注入密钥、不断言掩码。ANSI 清洗 ≠ 脱敏。

按指引 §9 B，这是把计划写成已完成。

### P1-6　`macao clean` 灾难回滚强声明 CONTRADICTED

申请 §1.1：

- 默认「安全清理**已完成任务的临时 Worktree**」；
- `--all`「一键快照备份（`.macao.bak.<timestamp>`）并安全重置」；
- `--restore`「恢复最近一次**配置与数据**备份」。

**实现**（`cli/main.py:892-916`）：

1. 默认：`shutil.rmtree(.macao)` —— 删除整个运行时（含 `state.db`、日志、进行中任务），不是「已完成 worktree」。
2. 全库无 `.macao.bak.<timestamp>` 写入点。
3. `--restore` **先**删 `.macao`，**再**把 `macao.yaml.bak.*` 拷回 `macao.yaml`。运行时数据不可恢复。`--all` 还会删掉那些 bak。

**复放**：`--restore` 后 `runtime_exists=False`，yaml 内容变为 backup。测试 `test_clean_restore_backup` 只断言 yaml 恢复，不保护 `.macao`。与申请「数据备份」不是同一行为。

---

## 五、L4 / PG-3（单独否决，不与上表混写）

指引 §2.1 / §3.3：L4 需要 OPS VERIFIED，且用户可见人工接管实机演练。

`src/macao/workflow/live_runner.py:54-58` 三名 Reviewer 仍为 `mock-cli`；`run_live_cycle(..., auto_signoff: bool = True)`。`macao live-run` 默认自动签字。这与 `b76cbfb` 轮 grok P1（TEST/SIM 外推 OPS）同类。本轮 20 个提交未把真实 CLI 评审环或 `macao override resolve` 用户路径补成 OPS 证据。

**即使 P1-1～P1-6 全部修好，本项仍单独阻断 L4。**

---

## 六、P2 / P3（不阻断「引擎既有 L3」，阻断把本轮包装成无瑕疵）

### P2-1　「摒弃 NOT_SPAWNED」过宽

无 `active_task` 时确实 In-repo。有任务时（`prober.py:610-618`）仍输出 `.macao/worktrees/<id>/<task>/rN (NOT_SPAWNED)`。`test_probe_executor_and_reviewer_progress_and_worktree` **断言**该状态。CLI 操作指南与 TECH_INTRODUCE 写「绝不硬编码 NOT_SPAWNED」。路径是编排器预期沙箱而非随机假路径，但申请「全面自愈 / 摒弃」不成立。

### P2-2　脏树遮蔽待审（P1-3 的 Now 序）在场景 C 会把「待落票」说成「正在编码」

ELS 已复现。若只修 pending 匹配、不改优先级，脏的评审仓永远看不到 REVIEW_PENDING。

### P2-3　向导在 PATH 无 CLI 时 fail-open 出 6 个虚构候选

`wizard.py:604-612`：`detected_clis` 为空则塞入 claude/opencode/codex/agy/cursor/kimi 假列表。与仓库 Fail-Closed 原则相反。

### P2-4　`macao audit` / `status` 经 `StateStore()` → `DatabaseManager` 会 `mkdir` + 执行 DDL

`storage/db.py:105-106,132-134`。申请把 audit 写成「直读不可变账本」。在从未初始化的仓上跑 `audit` 会创建 `state.db`。与 probe 的 ro 路径不对称。

### P3

- `AGENTS.md` 模块树仍写 126 tests，命令区写 128。
- STATUS 头「申请类 42」与后文登记表「41」不一致；`git ls-files` 申请 **42**。工作区另有未跟踪的 muse 结论，不计入 git。
- 申请「f9ff6bf 至 d042395 共 20 commits」应用 `95b7b35..d042395` 或写清「16 含 f9ff6bf + 4 前序」。
- `git diff --check 95b7b35..d042395` 空白行告警。
- 申请 ELS session / Last 已过期，应标「当时一次运行」或删掉当成现行证据。

---

## 七、L3 场景对账（本轮增量 vs 既有引擎）

| 场景 | 本轮增量 | 既有引擎测试 | 本轮定级 |
|---|---|---|---|
| 探活零副作用 | P1-1 CONTRADICTED | 单测只禁 state.db | 不能作为 L3 新场景 |
| 三元组 Last/Now/Next | P1-3 CONTRADICTED | `test_probe_physical_reviews_and_triplet` 只覆盖「无 result 文件 → pending」 | 未覆盖「部分落票 / 非 hex 文件名 / 脏树」 |
| 会话定位 | P1-2；单测只 mock agy + 错误形态的 claude 目录名 | 无 Codex/Cursor/Kimi 项目隔离反例 | 不足 |
| 全同意/僵局/超时/弃权/崩溃/返工 | 本轮未改判定核 | 128 测仍绿 | **维持既有 L3** |
| 人工接管 OPS | 仍 mock live-run | `test_cli_manual_takeover_ops_walkthrough` 属 TEST | **不足 L4** |

---

## 八、建议闭环顺序与验收

1. **P1-1**：`dry_run=True` 时禁止 `mkdir`/写日志；或删除「Pure Read-Only / 100% 无痕」用语，改为「只读 DB，允许日志」。测试断言空仓文件集差分为空（或仅允许文档已声明的那一类文件）。设计 §2.2 与 §4 必须改成同一句话。
2. **P1-2**：Codex/Cursor 必须按 workspace/cwd 过滤；无命中返回 `None`。Kimi 无真实 ID 时返回 `None`。补三条「外项目会话不得出现在本仓」否定测试。
3. **P1-3**：最新申请按 mtime 或与 HEAD/短 SHA 对齐；baseline 解析失败不得永久 pending；pending 改为「配置席位 − 已落票席位」；`Next` 插缺票名单；脏树与待审并存时不得把待审吃掉（或文档改成脏树优先并改申请）。ELS 申请段按现行 HEAD 重跑，禁止沿用 1ad706b / 旧 session。
4. **P1-4**：`achievable` 使用设计 §5 三合取；补 `S=3,M=2,ready=2` → 不可派发测试。
5. **P1-5**：实现掩码并测，或从申请/核验表/测试说明删除「脱敏」。
6. **P1-6**：默认只清 worktree 或改申请；`--all` 若宣称快照必须先写 `.macao.bak.<ts>`；`--restore` 不得先删后「恢复空数据」。
7. **L4**：真实 CLI 至少一轮非全同意 + 用户命令路径的 HOLD → `override resolve` / `merge approve`。mock `live-run` 不能当 OPS。

验收时请再跑：空仓 dry-run 文件集、Session 外项目反例、部分 result 文件、法定人数三合取、`clean --restore` 后 `.macao` 是否还在、全库脱敏测试。不要只贴 128/128。

---

## 九、准入建议

- **本轮增量**：**不授予** L3 全量认证 / 新 PG-2。探活与运维的关键不变量可被独立脚本证伪。
- **既有编排引擎**：**维持** L3 SCENARIO-VERIFIED / PG-2。
- **L4 RELEASE-READY / PG-3**：**拒绝**。P1 未清零，且 live-run 仍为 mock + 默认自动签字。

STATUS 建议（非本文件职责，供申请方）：删除「ELS 实录全部通过」「dry-run 严格只读零副作用」「脱敏掩码」完成式；登记 P1-1～P1-6；申请范围写 `95b7b35..d042395` 或显式 HEAD `519398d`。
