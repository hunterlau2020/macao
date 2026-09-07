# MACAO CLI 生产就绪、动态探活与全周期编排合并复审结论（`d042395`）

- **评审日期**：2026-09-07
- **评审人**：claude（独立评审；不采信申请自述、不采信 `STATUS.md` 定级句、不采信其他专家票，逐项独立复放）
- **评审对象**：[`docs/reviews/2026-09-07-review-request-d042395.md`](2026-09-07-review-request-d042395.md)
- **受审基线**：`d042395`（`origin/main`）。工作区 HEAD `519398d`，相对 `d042395` 仅追加申请文件、`STATUS.md`、`AGENTS.md` 三份文档（`git diff --stat d042395 HEAD`），代码正文一致。
- **一处需向用户明确披露的观察**：评审期间工作区内 `src/macao/adapter/session_locator.py`（+439/-行）、`cli/ui.py`、`cli/main.py`、`cli/wizard.py`、`workflow/live_dispatcher.py`、`workflow/prober.py`、`adapter/__init__.py`、`adapter/integ_harness.py` 存在**未提交的在制改动**，另有新文件 `src/macao/adapter/pi.py`。这些改动看起来是对本轮已收到的三份评审意见（尤其是会话定位跨项目误绑定与密钥掩码问题）的在制修复，与本次申请钉死的 `d042395` 基线无关。**本报告的全部结论均基于 `d042395` 纯净 blob（`git show d042395:<path>`）独立复核，不受这份工作区在制改动影响**；具体见 §0.3 的隔离复验方法。
- **对齐基准**：`docs/MACAO_REVIEW_GUIDELINES.md` §2–§3、§8、§9；`docs/PROBE_TECHNICAL_DESIGN.md`；`docs/usercases/UC2-task-create.md`、`UC3-dev-checkpoint.md`；`docs/usercases/PRODUCT-FACTS.md` 不介入/不捏造原则
- **定级申请**：L3 SCENARIO-VERIFIED / PG-2 全量认证，并提请 L4 RELEASE-READY / PG-3
- **机器票**：**`NO_APPROVE`**（不授予本轮 L3 全量认证；**拒绝 L4 / PG-3**；既有编排引擎 L3/PG-2 维持不变）
- **证据**：`BLOCKING` × 8（P1）；`ADVISORY` × 若干（P2/P3）；**无 P0**

**结论：不授予本轮（探活/CLI/运维层）L3 SCENARIO-VERIFIED / PG-2 全量认证；不授予 L4 RELEASE-READY / PG-3。既有编排引擎（共识/FSM/超时/E7 override）L3/PG-2 维持不变，不因本轮增量回退，也不因本轮增量升级。**

本轮申请把「零副作用探活、物理事实三元组、会话定位、灾难回滚、日志脱敏、检查点闭环」写成可直接授予 L3 全量认证的强声明。按 GUIDELINES §3.3，L3 要求「SIM/TEST 覆盖所有适用 P0/P1 场景且为 VERIFIED」。我对申请列出的六大交付维度逐一构造独立反例（空仓探活、跨项目会话伪造、法定人数边界、脏树遮蔽待审、`--auto`/`--force` 绕过内容归属、`clean --restore` 数据丢失），**六个维度中五个的核心不变量被独立复放证伪**。128/128 测试为真但断言面窄，不能填补这个缺口。

---

## 0. Reviewer 自审

### 0.1 强制自检五项

| # | 项 | 本轮 |
|---|---|---|
| 1 | 字段/路径 vs 实际读取 | `SessionLocator` 对 codex/cursor/kimi 三路读到**任意来源**后统一回填调用方 `project_path` 作为 `workspace`（设计声明按项目匹配，代码无匹配）；`quorum.achievable` 只读 `minimum_winning_seats`，`seat_quorum_required`/`weight_quorum_required` 读出但未参与判定 |
| 2 | 「已完成 / 100% / 全绿」 | 设计专文 §2「100% 幂等与无痕性」与同一文档 §1 副作用表「仅落盘 probe 审计日志」**自相矛盾**（§9 模式 SPEC 内部不一致）；申请「128/128、零副作用、脱敏掩码」多项 **CONTRADICTED** |
| 3 | 确定性用语未标目标 | 「100% 零修改」「一键快照备份」「安全清理已完成任务的临时 Worktree」均未标注"目标"而是既成事实陈述 |
| 4 | YAML/JSON Schema | 8 份契约 docs↔src 逐字节一致 **VERIFIED**（与本轮增量无关，历史项） |
| 5 | P1 均附路径与复放 | 是，全部针对 `d042395` 纯净 blob |

### 0.2 撤回记录

无需撤回项。本轮我对每条反例都先针对当前工作区（含在制改动）复现，再改用 `git show d042395:<path>` 抽取纯净 blob 独立执行，两次结果一致时才计入报告（见 §0.3）；`session_locator.py` 一项两次结果确认一致（在制改动未影响 `d042395` 的可复现性判定，改动本身另计）。

### 0.3 隔离复验方法（应对在制工作区改动）

对每个被 `git diff d042395` 标记为已变更的受审文件，先执行 `git show d042395:<path> > /tmp/.../pure_blob.py`，再用 `importlib.util.spec_from_file_location` 直接加载纯净 blob 做反例复放，隔离工作区在制改动的干扰。`prober.py`、`cli/main.py`、`cli/wizard.py`、`live_dispatcher.py` 相对 `d042395` 的工作区差异经检查均只是新增 `pi` CLI 适配器注册（与本报告任何一条 P1 的判定逻辑无交集）；`session_locator.py` 差异较大（439 行），已按上述方法单独隔离验证，P1-2 的复放结果在纯净 blob 与工作区版本下一致。

### 0.4 与三份既有报告的定位

本报告完成时 `grok`、`muse`、`codex` 三份结论已存在于 `docs/reviews/`。我在完全写出自己的独立复验（§一~§四）之后才通读三份报告用于交叉核对（§六），三份报告中我独立重新推导并证实的结论标注「独立复现」，仅经三方提出、我读码确认成立但未重新设计反例的标注「读码确认」。

---

## 一、申请 §4 机验独立复跑

| 声明 | 本机（纯净 `d042395` blob 或工作区等价路径） | 判定 |
|---|---|---|
| `PYTHONPATH=src python3 -m unittest discover tests` 128/128 | `Ran 128 tests … OK`（58.5s，串行） | **VERIFIED** |
| `compileall -q src tests` 0 Errors | rc=0 | **VERIFIED** |
| Schema 8 份逐字节一致 | `docs/schemas/` ↔ `src/macao/schemas/` 8/8 无 diff（仅 `__init__.py`/`__pycache__`/`README.md` 预期差异） | **VERIFIED** |
| `templates/` 12 份 | `find templates -type f` = **15**（6 指南 + 8 manifest + `README.md`）。申请正文自列「6+8=14」，标题写「12」，两处申请自身数字互不一致，且均非 15 | **CONTRADICTED**（P3） |
| 全库 228 份 Markdown 0 控制字符 | `git ls-files '*.md'` = **229**；控制字节 **0** | 控制字符结论 **VERIFIED**；份数 **CONTRADICTED**（P3，连续多轮复发） |
| `macao probe --dry-run` 100% 零修改 | 见 P1-1 | **CONTRADICTED** |
| SessionLocator 零 LLM + 项目绑定 | 零 LLM 部分 **VERIFIED**（仅 stdlib）；项目绑定部分见 P1-2 | **PARTIALLY_VERIFIED** |
| 进度三元组物理推导 | 见 P1-3 | **PARTIALLY_VERIFIED** |
| 「日志脱敏与 API Key/Token 掩码」 | 见 P1-5 | **CONTRADICTED** |
| `macao clean` 灾难回滚 | 见 P1-6 | **CONTRADICTED** |

---

## 二、P1：本轮 L3 全量认证前必须修正

### P1-1　`--dry-run` 无条件写盘，与「100% 零修改 / Pure Read-Only」矛盾

**独立复现**（与 grok P1-1、muse B-1、codex P1-05 三方各自独立收敛，我重新设计了空仓探针）：

```python
# 全新 git init 仓库，无 .macao/
from macao.workflow.prober import TeamProber
r = TeamProber(project_root='.', dry_run=True).probe()
# 结果：
# dry_run: True
# log_file: .macao/logs/probe/probe_20260907_155948.log
# state_db exists: False
```

```text
$ find .macao -type f
.macao/logs/probe/probe_20260907_155948.log
```

**根因**：`prober.py:811-813` 在 `probe()` 结尾无条件调用 `self._write_probe_log(probe_result)`；该函数 `:247-250` 无条件 `log_dir.mkdir(parents=True, exist_ok=True)` 后写文件；`dry_run` 只作为日志正文的一个字段（`:260`），从不 gate 写盘动作。CLI 横幅（`cli/ui.py:187`）打印 `[DRY-RUN (Pure Read-Only)]`；设计专文 §2「100% 幂等与无痕性」与同一文档后段副作用表「仅落盘 probe 审计日志到 `.macao/logs/`」自相矛盾——申请与 UI 采信的是前一句。

**假绿测试**：`tests/test_team_probe_and_dispatch.py:80-93` 的 `test_probe_root_command_dry_run_zero_side_effects` 只断言 `state.db` 不存在，对 `.macao/` 目录本身或其他文件无任何断言——测试名承诺的范围大于其实际验证的范围。

**验收**：`dry_run=True` 时完全跳过 `_write_probe_log`（内存返回 `log_file: None`），或将设计文档与 CLI 横幅措辞统一收窄为「除审计日志外不触碰 `state.db` 与 Git」。补一条对空仓执行 `--dry-run` 前后 `find .macao` 文件集合差为空的测试。

### P1-2　`SessionLocator` 对 Codex / Cursor / Kimi 三路捏造项目绑定

**独立复现**（与 grok P1-2、codex P1-04 各自独立收敛；我用伪造 `$HOME` 单独构造反例，隔离验证纯净 `d042395` blob 与工作区版本行为一致）：

```python
# $HOME/.codex/session_index.jsonl 最后一行是「project B」的会话
# 对 project_a 目录调用：
SessionLocator.find_session('codex', Path('proj_a'))
# -> {'session_id': 'sess-proj-b-latest',
#     'title': 'unrelated project B session',
#     'workspace': '.../proj_a',      # 被强行回填成调用方路径，与实际会话归属无关
#     ...}
```

```python
SessionLocator.find_session('agent', Path('proj_a'))
# -> {'session_id': 'chat-other', 'workspace': '.../proj_a', ...}  # 全局最新 chat，与 proj_a 无关

SessionLocator.find_session('kimi', Path('proj_a'))
# -> {'session_id': 'auto-discovered', 'workspace': '.../proj_a', ...}  # 仅目录存在即返回固定占位符，无真实会话查找
```

**根因**（`session_locator.py:165-233`，`d042395` 纯净 blob）：
- `_find_codex_session`：读 `~/.codex/session_index.jsonl` **最后一行**，不检查其中任何 workspace/项目字段，随后**无条件**把 `workspace` 写成调用方传入的 `project_path`；
- `_find_cursor_session`：取 `~/.cursor/chats/` 下全局按 mtime 最新的目录，无任何项目过滤；
- `_find_kimi_session`：`~/.kimi` 目录存在即返回固定字符串 `session_id: "auto-discovered"`，不读取任何真实会话数据。

对照：`agy`（`:59`，比较 `Path(ws).resolve() == project_path`）与 `opencode`（`:143-145`，SQL `WHERE directory = ?`）两路确有项目过滤，claude 路径亦按 sanitize 后的路径匹配目录。仅 codex/cursor/kimi 三路无过滤即回填。

**影响**：这直接违反 `PRODUCT-FACTS.md` 与设计专文 §1「绝不假造虚假进度」「MACAO 不得替 Executor 想当然编造任务标题或业务意图」——探活报告会把**另一个项目**的会话展示为「当前项目活跃会话」，且展示的时间戳、标题均为真实数据（并非全空），迷惑性强于「返回 None」。

**验收**：三路定位器改为仅在可验证的 workspace/cwd 字段与 `project_root` 精确匹配时才返回；无法证明绑定时返回 `None`，不得回填调用方路径。补三条「最新会话属于另一项目 → 返回 None」的否定测试。

### P1-3　进度三元组算法与设计文档、申请声明多处不一致

**独立复现**（设计文档 §3 明确写出算法，我逐条对照代码取值路径与实测行为）：

| 设计声明（`docs/PROBE_TECHNICAL_DESIGN.md`） | 代码（`prober.py`，`d042395`） | 实测 |
|---|---|---|
| `:174-185` `Next` 应列出待落票审查员名单，示例 `[rev-opencode, rev-cursor...]` | `:575` 固定句 `"Await reviewer evaluations and verdicts before next commit"` | 句中从不出现具体 reviewer id |
| Last 应跳过非功能性提交 | `:191` 仅排除 `msg.startswith("docs(review)")` | `feat → chore → docs: handbook` 提交栈下，Last 落到 `docs: handbook` |
| 待审优先于脏树判定 | `:563` `if not git_info["is_clean"]:` 排在 `:568` 待审检查**之前** | 有 1 个无关脏文件即可把 `REVIEW_PENDING` 完全遮蔽为 `ACTIVE_DEV (UNTRACKED)` |
| Next 应比对提审单要求的 reviewer 与已提交的 `*-review-result-*.md` | `:235` `has_pending_request = (len(matching) == 0)`，`matching` 是文件名含 baseline 的**任意**结果文件 | 3 席审查员中仅 1 份结果文件落盘，`has_pending_request` 即变 `False`，其余 2 席不再显示为待审 |
| — | `:203` `sorted(reviews_dir.glob(...))[-1]` 按**字典序**取「最新」申请 | 同日多份申请时可能选中与 HEAD 无关的文件，而非按时间/commit 邻近性 |
| — | `:219-224` baseline 正则要求 7-40 位 hex；申请文件名不含此模式（如 `...-v3-r2-r9.md`）时 `baseline=None` → `has_pending_request` **永远** `True` | 已有多方落票的申请仍被判定「待审」 |

**根因定性**：这不是单点笔误，是 §3 描述的算法与 `:191/:203/:219-240/:563-575` 五处实现均存在偏差，且偏差方向不一致（有的过早判定 not-pending，有的永久 pending，有的被脏树完全遮蔽）——`_inspect_physical_reviews` 与 `_synthesize_progress_triplet` 两个函数在「什么算已落票」「先看什么」两个关键点上都未落实设计文档写下的规则。

**验收**：`matching_results` 改为按 `(baseline, reviewer_id)` 精确集合与配置席位数比对，而非「≥1 份文件即非 pending」；baseline 解析失败不得导致永久 pending；脏树与待审并存时不得让待审被吃掉（或在文档中明确改为「脏树优先」并同步改申请措辞）；`Next` 插入实际缺票 reviewer id 列表；最新申请选取改按 mtime 或与 HEAD 拓扑邻近性排序。

### P1-4　派发法定人数判定只用 `minimum_winning_seats`，丢弃席位与权重两道法定人数门槛

**独立复现**（我构造 N=4、`S=3,W=3,M=2`，2 席就绪配置，直接对照设计专文 §5 公式验证）：

```yaml
# minimum_winning_seats: 2, seat_quorum_required: 3, weight_quorum_required: 3
# 2 个 reviewer 用 mock-cli（就绪），2 个 reviewer 用不存在的 CLI（未就绪）
```

```text
quorum: {'ready_count': 2, 'minimum_winning_seats': 2,
         'seat_quorum_required': 3, 'weight_quorum_required': 3, 'achievable': True}
can_dispatch: True
```

设计专文 `:228`：$\text{QuorumAchievable} = (R_{ready} \ge S) \land (R_{ready} \ge M) \land (W_{avail} \ge W_{req})$。按此公式 $2 \ge 3$ 为假，应为 `False`；代码（`prober.py:758-761`）`quorum_achievable = ready_reviewers_count >= min_winning` 只做了 $(R_{ready} \ge M)$ 一项，`seat_quorum_required`/`weight_quorum_required` 被读出、写进报告字典（`:759-760,767-768`），却从未参与 `achievable` 或 `can_dispatch`（`:777-786`）的判定。

**影响**：探活会在实际法定人数不足时仍报告「可派发」，这正是设计专文 §1.1 明确要防止的「盲目派发」——而这条门禁恰恰是本轮申请列为核心交付的「$2/3$ 法定仲裁阈值」在探活层的落地。

**验收**：`achievable` 改为设计公式的三合取；补 `S=3,M=2,ready=2` → `achievable=False` 的否定测试。

### P1-5　「API Key / Token 敏感词掩码」在 `d042395` 无任何实现

**独立复现**：

```bash
$ grep -rn "mask\|redact" src/macao/ --include=*.py | grep -v test
src/macao/cli/wizard.py:436:  secrets_masking: true      # 仅写入 YAML 模板的静态注释/字面量
src/macao/cli/wizard.py:549:  "secrets_masking": True    # 同上
src/macao/cli/main.py:162:  secrets_masking: true        # 同上
```

`secrets_masking` 从未在 `utils/logger.py`（仅 2 个函数：`setup_logger`/`get_logger`）或 `adapter/pty_session.py` 中被读取或消费。`live_dispatcher.py:347-353`（codex 独立读码定位，我复核成立）把 `adapter.get_logs()` 的原始输出直接写入 reviewer transcript 文件，各 adapter 只做 ANSI 清洗（`strip_ansi`），不做任何字符串脱敏。`tests/test_logger_and_audit.py` 5 个用例覆盖落盘/gitignore/audit CLI/logs/reviewer log，无一注入密钥或断言掩码。

**影响**：`.macao/logs/reviewers/<id>_r<round>.log` 会以明文落盘终端回显中的 token/密码/连接串，且这些日志文件通过 `macao logs -r <id>` 可被任意本地用户读取；申请 §1.3/§4/§5 把「脱敏掩码」列为已交付特性和测试覆盖点。

**验收**：实现真实的密钥模式识别与掩码（工作区在制的 `session_locator.py` 已在 `_sanitize_session_name` 中加入了一个正则示例，可作为起点，但覆盖面仅限会话名，不含 PTY transcript 主体），补密钥注入类反例测试；或从申请与核验表中删除该特性声明直至真正实现。

### P1-6　`macao clean` 默认删除全部运行时状态，`--restore` 先删后「恢复」，无任何路径创建过声称的 `.macao.bak.<timestamp>` 快照

**独立复现**（端到端 CliRunner 调用）：

```text
# 预置 .macao/state.db、.macao/logs/probe/probe_20260101.log、macao.yaml.bak.<ts>
$ macao clean --restore
✓ .macao/ (runtime directory)
✓ Restored macao.yaml from macao.yaml.bak.<ts>

--- 之后 ---
.macao exists: False
state.db exists: False
probe log exists: False
```

**根因**（`cli/main.py:891-908`）：第 1 步无条件 `shutil.rmtree(macao_dir)`（删除整个 `.macao/`，含 `state.db`、全部审计日志、所有 worktree），不区分"已完成任务的临时 Worktree"还是正在进行中的运行时状态；`--restore` 分支排在**之后**，只把 `macao.yaml.bak.*` 拷回 `macao.yaml`。全库搜索 `\.bak\.` 只有两处写入点，均为 `wizard.py:587` 在**覆盖已存在 `macao.yaml` 时**写的单文件配置备份——**代码里不存在任何创建 `.macao.bak.<timestamp>` 目录级快照的路径**。

**影响**：申请 §1.1 明确写「默认安全清理已完成任务的临时 Worktree 沙箱」「`--all` 支持一键快照备份（`.macao.bak.<timestamp>`）并安全重置运行时」「`--restore` 支持恢复最近一次配置**与数据**备份」——三句话，实现只兑现了"删除"，"备份"与"数据恢复"均不存在。这是一条会造成不可逆数据丢失、且被文档描述成"安全"操作的命令。

**验收**：默认行为改为只清理已完成任务对应的 worktree 子目录，不动 `state.db`/日志/进行中任务；`--all` 若要保留「快照备份」承诺，必须先执行 `.macao/ → .macao.bak.<ts>/` 的目录级拷贝再清理；`--restore` 不得在恢复前无条件删除运行时状态。

### P1-7　`task checkpoint --auto` 无条件写入 `tests_passed: true`，且该字段直接门控 FSM 向 `READY_FOR_REVIEW` 的推进

**读码确认**（codex P1-01 首先提出；我独立追踪到 orchestrator 消费点，确认字段直接门控状态转移，非展示性字段）：

`cli/main.py:467-496`（`d042395` 纯净 blob）：`--auto` 分支生成 `.macao/.dev.yml` 时无条件写入 `"development": {"quality_metrics": {"tests_passed": True}, ...}`，**不运行任何测试命令**。

`orchestrator.py:250-252`：

```python
tests_passed = quality.get("tests_passed") is True or quality.get("tests_exempt") is True
if dev_rnd == rnd and status == "ready_for_review" and signal == "EXPLICIT" and latest_commit and tests_passed:
    ...  # 允许推进
```

`tests_passed` 是五个合取条件之一，直接门控 checkpoint 是否被编排器采信为合法的 `READY_FOR_REVIEW` 信号。也就是说执行者对任意失败或从未运行过测试的代码，只需 `macao task checkpoint --auto` 一条命令即可让编排器采信「测试已通过」并推进到评审派发。这与 `docs/usercases/UC3-dev-checkpoint.md:7,25-31` 明定的「执行者独占产物内容与自评，编排器不读、不写、不摘要」直接冲突——本例中**是编排器自己的 CLI 代笔写下了执行者从未做出的自评**。

**验收**：`--auto` 生成的 manifest 不得包含任何自我断言的质量指标；要么完全不写 `quality_metrics` 字段（交由 schema 的可选性处理），要么强制要求执行者显式提供该字段来源（如真实测试命令的 exit code）。补一条「`--auto --no-review` 生成的 checkpoint 在 `tests_passed` 缺失时不得推进 E1_PRODUCED」的否定测试。

### P1-8　`macao task create --force` 绕过唯一活动任务约束，孤立旧任务且丢弃用户传入的验收标准

**读码确认**（codex P1-02 首先提出；我独立复核了 `get_active_task()` 的查询语义以及 `acceptance_criteria` 类型判定分支，确认孤立任务与验收标准丢失两条后果均成立）：

`cli/main.py:381-388`：`if active and not force:` 才会拒绝创建；`--force` 时直接跳过检查继续调用 `start_task`。`orchestrator.py:144-173`（`start_task`）本身对"是否已有活动任务"**无任何校验**——它总是生成一个新的随机 `task_id` 并转移到 `CODING`。`storage/store.py:48-54`：`get_active_task()` 按 `created_at DESC LIMIT 1` 只返回**最新**的非终态任务。三者叠加：`--force` 后旧任务仍处于非终态（未取消、未归档），但从此再无法被任何 CLI 命令寻址到（`checkpoint`/`cancel`/`merge` 全部经由 `get_active_task()` 定位目标）——旧任务及其 `.macao/.dev.yml`/checkpoint 指针永久孤立。

同一命令（`cli/main.py:415`）：`acceptance_criteria={"raw": acceptance, "tests_passed": True}` 把用户 `--acceptance` 输入包装为 dict；`orchestrator.py:193`：`crit_list = acceptance_criteria if isinstance(acceptance_criteria, list) ... else ["All unit tests pass", "Zero regression"]`——dict 类型判定失败，回退到硬编码的通用列表。用户显式传入的验收标准**从未进入**发给执行者的 `DEVELOPMENT_STARTED` Type A 信封。

这与 `docs/usercases/UC2-task-create.md:17,37-40,49-51,84-88`（单一活动任务不变量 + Type A 必须逐字段携带表单验收标准）直接冲突。

**验收**：删除 `--force` 绕过活动任务的语义，或改为先显式执行 E10 归档旧任务并要求管理员授权；`acceptance` 参数改为构造非空 list 并原样透传，补充「用户传入的验收标准逐字段出现在 Type A payload 中」的断言测试。

---

## 三、L4 / PG-3（单独否决，三方一致）

GUIDELINES §3.3：L4 要求「OPS 为 VERIFIED，且完成用户可见的人工接管演练」。`live_runner.py:55-57`（`d042395`）三名 reviewer 硬编码 `cli: "mock-cli"`；`cli/main.py:860` `--auto-signoff/--no-auto-signoff` 默认 `True`；`live_runner.py:180-183` 在 `auto_signoff=True` 时写入的审计事件类型是 `HUMAN_MERGE_APPROVED`（`signer: "system-runner"`）——事件类型自称"人类批准"，实际签署者是系统。申请所述"在 `english_learning_system` 实操"仅为申请正文中的一段自然语言陈述，未提供可在本仓库重放的命令、留存产物或真实 PTY 人工接管证据链。**即使 §二 全部 P1 闭环，L4 仍需一次真实 CLI reviewer + 真实 deadline + 人工 override + merge/recovery 的留档演练。**

---

## 四、已对齐 / 已确认项（不抵消上述 P1）

1. SQLite 探活连接对已存在的 `state.db` 确实使用 `mode=ro` URI（`prober.py:67-110`）；文件不存在时不跑 DDL——这与「不初始化空 `state.db`」一致。
2. 无 `active_task` 时 reviewer 工作区展示走 `In-repo (Shared Workspace / Direct Review)`；`git worktree list --porcelain` 有真实读取路径（`worktree-lifecycle-norm` 中登记的可选策略在此处落实）。
3. `macao init` 向导主路径可用：数字/`1-4`/前 N 位多种输入格式解析、最少 2 席循环拒绝、生成的 YAML 通过 `validate_config` 语义校验。
4. `VoteAggregator` 超时票携带 `source: timeout`/`deadline`/`last_ping_at` 并在写前做 schema 校验（历史项，本轮未回退，codex 读码确认）。
5. PTY ANSI 转义序列剥离存在（`strip_ansi`）——但如 P1-5 所述，ANSI 清洗不等于密钥脱敏，两者是不同的安全属性。
6. 编排引擎既有 L3 场景测试（全同意/僵局/超时/弃权/崩溃恢复/返工）未被本轮 20 个提交拆掉，128/128 串行全绿，历史 L3/PG-2 判定不受影响。

---

## 五、P2 / P3

| ID | 级 | 问题 |
|---|---|---|
| P2-1 | P2 | `wizard.py:604-612`：`probe_available_clis()` 返回空列表时静默塞入 6 个硬编码的虚构 CLI 候选（含捏造版本号），呈现给用户如同真实探测结果。与仓库反复强调的"绝不捏造"原则相反 |
| P2-2 | P2 | `wizard.py:529-530`：`minimum_winning_seats = max(2, quorum_votes)` 把"最少胜方席位"（应为独立配置项，默认 2）与"席位法定人数" `ceil(2W/3)` 混为一谈；4 席等权队向导生成 `minimum_winning_seats=3`，比根配置/引擎默认的 `2` 更严格，PRD/UC-1 均无此推导依据，同一票型在默认配置下 `APPROVED`、在向导配置下 `DEADLOCK` |
| P2-3 | P2 | `storage/db.py`：`macao audit`/`status` 经 `DatabaseManager` 在从未初始化的仓上会 `mkdir`+执行 DDL，与 probe 的 `mode=ro` 路径不对称；申请把 `audit` 描述为"直读不可变账本"，未提及其可能是首次触发建库的命令 |
| P2-4 | P2 | `prober.py:617-618`：有 `active_task` 但物理路径缺失的分支仍保留字面 `(NOT_SPAWNED)`。这是合法分支（非虚构），但申请"全面自愈 / 摒弃机械虚假占位符"的表述过宽，未如实说明这条分支仍在 |
| P3-1 | P3 | `templates/` 实际 15 个文件，申请标题写 12、正文自列 14，两处申请自身数字互不一致 |
| P3-2 | P3 | `git ls-files '*.md'` = 229，申请写 228，连续多轮口径复发 |
| P3-3 | P3 | 申请「f9ff6bf 至 d042395 共 20 commits」；`git rev-list --count f9ff6bf..d042395` = 15（含 `f9ff6bf` 为 16），实际 20 需用 `95b7b35..d042395`，两句范围表述互相矛盾 |
| P3-4 | P3 | `AGENTS.md` 模块树仍写 126 tests，命令区已同步 128，文档内部口径不一致 |

---

## 六、交叉核对（grok / muse / codex）

**与 grok（两轨 `NO_APPROVE`）**：P1-1/P1-2/P1-3/P1-4/P1-5/P1-6 六项与 grok 报告的 P1-1/P1-2/P1-3/P1-4/P1-5/P1-6 逐条**独立同结论**——我在写出自己的反例之前未读 grok 报告；完成后对照，双方的复现输入不同（例如 P1-4 我用 `S=3,W=3,M=2,ready=2`，grok 用类似构造），拒因字符串与根因定位一致。grok 额外指出的"并行测试跑出一次 `test_session_locator_discovery` FAIL、串行复跑通过"，我未复现（未做并行测试），采信其"不作为产品 P1"的判断，不改变整体票型。

**与 codex（合并 `REJECT`）**：P1-01/P1-02（我的 P1-7/P1-8）为 codex 独立提出，我逐行追踪到 `orchestrator.py` 的消费点后确认成立，非转述；P1-03（我的 P1-4）、P1-04（我的 P1-2）、P1-05（我的 P1-1 + P1-5 的合并表述）与我各自独立收敛。codex 未讨论 P1-3（进度三元组的 Last/Next/优先级偏差）与 P1-6（`clean` 数据丢失），这两项为我与 grok 独立命中、codex 未覆盖的维度。

**与 muse（`YES_APPROVE` 授予 L3，仅拒 L4）**：muse 的 B-1（dry-run 落盘）与我 P1-1、B-2（掩码缺失）与我 P1-5 结论一致，但 muse 将其定性为"L4 门槛，不影响 L3"。**我不同意这一定性**：GUIDELINES §3.3 对 L3 的最低要求是"SIM/TEST 覆盖所有适用 P0/P1 场景且为 VERIFIED"，而申请本身把"零副作用探活"列为本轮 L3 认证请求的核心交付维度之一（§1.2）——一个被申请自己列为 L3 交付物的核心不变量被独立复放证伪，理应计入本轮 L3 判定，而非顺延到 L4。muse 也未发现 P1-2（会话跨项目误绑定）、P1-3（进度三元组多点偏差）、P1-4（法定人数判定漏项）、P1-6（clean 数据丢失）、P1-7/P1-8（checkpoint/task create 伪造与孤立），这六项独立来看已经在申请所称的"探活/CLI/运维"三大维度上全面失守，不足以支撑"探活/会话/日志/模板/向导五大维度场景均有 TEST + SIM 证据"的授予表述。

**票型汇总**：

| 评审人 | 本轮判定 |
|---|---|
| claude | `NO_APPROVE`（不授予新增量 L3；拒 L4；维持既有引擎 L3/PG-2） |
| grok | `NO_APPROVE`（同上） |
| codex | `REJECT`（同上，L4 判 UNKNOWN 因而不通过） |
| muse | `YES_APPROVE`（授予 L3；仅拒 L4） |

四方中三方独立收敛为不授予本轮 L3 全量认证，且三方对 L4 全部拒绝。按 GUIDELINES §8「真理不等于投票」「沉默 ≠ 同意」，本票不因多数而成立，而是因为 P1-1～P1-6（申请自陈的六大交付维度中五项）与 P1-7/P1-8（新增 CLI 命令的 FSM 完整性）在独立复放下均可被证伪，且证伪路径均已在本报告给出可复跑的最小反例。

---

## 七、建议闭环顺序与验收标准

1. **P1-7 / P1-8**（FSM 完整性，最优先，涉及审计真实性根基）：移除 `--auto` 对 `tests_passed` 的无条件写入；移除 `--force` 绕过活动任务锁的语义或改为显式归档；修复 `acceptance_criteria` 的 list 传参与消费。
2. **P1-2 / P1-4**（探活核心不变量）：Codex/Cursor/Kimi 定位器补项目匹配，无法证明时返回 `None`；`quorum.achievable` 改为三合取公式。
3. **P1-1 / P1-5**（安全属性诚实性）：`--dry-run` 真正零写盘或收窄措辞；实现密钥脱敏并测试。
4. **P1-3**（三元组算法与设计文档对齐）：`Now` 优先级、`Next` 缺票名单、`matching_results` 精确集合、baseline 解析健壮性四点逐一补测试。
5. **P1-6**：`clean` 默认行为收窄，`--all`/`--restore` 的备份承诺要么真实实现要么从文档删除。
6. 以上全部关闭、补齐对应反例测试后，重新提交本轮 L3 全量认证申请；L4 需额外一次真实 CLI + 人工接管的留档演练，不接受 mock 数据外推。

---

## 附：机器票与结构化 issue 索引

| issue_id | severity | disposition_class | 摘要 |
|---|---|---|---|
| `claude/P1-1` | critical | `BLOCKING` | `--dry-run` 无条件写盘，与"100% 零修改"设计声明矛盾；测试假绿 |
| `claude/P1-2` | critical | `BLOCKING` | Codex/Cursor/Kimi 会话定位跨项目伪造绑定 |
| `claude/P1-3` | major | `BLOCKING` | 进度三元组 Last/Now/Next 与设计文档五处偏差 |
| `claude/P1-4` | major | `BLOCKING` | 法定人数判定丢弃席位与权重门槛，仅比对 `minimum_winning_seats` |
| `claude/P1-5` | major | `BLOCKING` | 密钥脱敏零实现，PTY transcript 明文落盘 |
| `claude/P1-6` | critical | `BLOCKING` | `macao clean` 默认删除全部运行时状态；`--restore` 先删后"恢复"；声称的快照备份路径不存在 |
| `claude/P1-7` | critical | `BLOCKING` | `task checkpoint --auto` 无条件伪造 `tests_passed: true` 并直接门控 FSM 推进 |
| `claude/P1-8` | critical | `BLOCKING` | `task create --force` 孤立旧活动任务且丢弃用户验收标准 |

`vote`: `NO_APPROVE`
