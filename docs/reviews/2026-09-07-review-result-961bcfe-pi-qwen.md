# MACAO 综合编排与动态探活体系复审结论（Commit `961bcfe` / Round 2）

- **文档归档路径**: `docs/reviews/2026-09-07-review-result-961bcfe-pi-qwen.md`
- **评审日期 (Date)**: 2026-09-07（机验执行窗口 20:24–21:00 +0800）
- **评审人 (Reviewer)**: `pi-qwen`（harness: pi coding agent，`PI_MODEL=qwen3.8-max`，`PI_PROVIDER=qwen-token-plan`，`PI_SESSION_ID=01a07bd3-8b24-72e9-8e95-62179f6a5946`）
- **评审对象 (Object)**: [`docs/reviews/2026-09-07-review-request-961bcfe.md`](2026-09-07-review-request-961bcfe.md)
- **受审基线 (Checkpoint)**: `commit 961bcfe`（**本评审全部结论均以 `git archive 961bcfe` 提取的纯净树 `/tmp/v961` 为唯一评审对象**，理由见 §0.2）
- **对齐基准**: [`docs/MACAO_REVIEW_GUIDELINES.md`](../MACAO_REVIEW_GUIDELINES.md) v1.0、[`docs/usercases/PRODUCT-FACTS.md`](../usercases/PRODUCT-FACTS.md)、`AGENTS.md`（Fail-Closed / 不介入 / 只读零副作用三原则）
- **申请目标**: L3 SCENARIO-VERIFIED / PG-2 全量认证 + L4 RELEASE-READY / PG-3 准入
- **审查结论 (Verdict)**: **不授予本轮增量 L3 SCENARIO-VERIFIED / PG-2 全量认证；拒绝 L4 / PG-3 准入。判定：REWORK（第 3 轮返工）**
- **最终投票 (Vote)**: `NO_APPROVE`
- **证据统计**: **P0 × 1**、**P1 × 10**、**P2 × 9**、**P3 × 4**；全部 P0/P1 均附**可复现命令 + 观测输出 + 文件行号**
- **证据类型**: CODE（静态审读 `961bcfe`）+ TEST（纯净树复跑 145 项）+ SIM/OPS（7 个独立沙箱项目实机复放：`/tmp/v961{,b,c,d}`、`/tmp/fb`、`/tmp/fA`、`/tmp/fB`、`/tmp/fresh`、`/tmp/rv`、`/tmp/ch2`、`/tmp/walproof`）

---

## §0 Reviewer 自审记录（指引 §1.2-5 / §9 强制登记）

### §0.1 本轮激活的漏审模式

| # | 模式 | 本轮实际发生情况 |
|---|---|---|
| **A** | 字段声明位置 vs 实际读取位置不一致 | 命中：`.dev.yml` 信封声明 `full_document.sha256`，但代码库无任何位置校验该字段（见 P2-5） |
| **B** | `[x]` ≠ 已有完成证据 | 命中：§3.2 质量快照 6 项 `[x]` 中 **2 项被实测推翻**（145/145 PASS、探活零写盘 100% CLEAN），1 项口径需限定（账本对账，见 §2） |
| **C** | 确定性语言未标注"目标/已验证" | 命中：「彻底闭环」「杜绝任何」「无遗漏性」「100% CLEAN」「无损还原」5 处绝对化用语均有反例 |
| **D** | 示例代码/信封不可校验 | 命中：信封 `sha256` 为 64 个 0（真实值 `9f30a01f…`），Schema 无 `pattern` 约束故无法拦截 |

### §0.2 本评审自身的一处修正（必须入审计）

评审前期（20:24–20:38）我在 **仓库工作树**上执行 CLI 复放。20:47 我核对引用行号时发现 `src/macao/cli/main.py` 的行号发生整体位移（`clean_cmd` 由 931 → 1103），进一步核查确认：**工作树在 20:38:40 被并发改动**，新增了未提交的 `task adopt` 命令（`main.py` +172、`ui.py` +26、`tests/test_task_adopt.py` 未跟踪）。

- 处置：立即以 `git archive 961bcfe | tar -x -C /tmp/v961` 提取纯净树，**将 §4–§6 中全部 P0/P1 结论逐条在纯净树上重跑复现**（下文每条证据均标注「纯净树复现」）。
- 影响：`git diff 961bcfe -- src/macao/cli/main.py` 为**纯追加**（仅在 453 行后插入 `task_adopt`），`clean_cmd`/`task_create`/`probe_cmd` 未被触碰，故我的结论未被污染；但**任何在工作树上做的验证都已不可信**，该事实本身构成 P1-10。
- 附带澄清：Grok 报告「`macao task adopt` 不存在（`No such command 'adopt'`）」在 `961bcfe` 上**为真**（`git show 961bcfe:src/macao/cli/main.py | grep -c 'task.command("adopt")'` = **0**）。工作树上能查到 `adopt` 属于**评审期内的未提交整改**，不得用于推翻 Grok 的裁定。

---

## §1 结论综述 (Executive Summary)

本轮 8 项前序 P1 中，**4 项经独立机验为真闭环**（P1-3 三元组集合差、P1-4 三道门槛合取、P1-7 checkpoint 禁伪 `tests_passed`、P1-2 的 Codex/Cursor/Kimi 三路隔离），**4 项为部分闭环且均存在可复现反例**（P1-1 / P1-2 / P1-5 / P1-6 / P1-8 中的 5 条具体路径）。更严重的是，本轮**新引入了 1 个 P0 级门禁反转缺陷**与**2 个由"修复本身"引入的伪造路径**：

1. **P0-1（门禁反转）**：`TeamProber._get_adapter` 在配置 CLI 无法识别时，用 `agent_id` 子串模糊匹配**顶替另一个适配器**，导致配置了根本不存在二进制的评审席位被探活报成 `READY` 并附带**捏造的真实版本号**；在纯净树复现中，**2 个"READY"席位对应的 CLI 均未安装**，而 `can_dispatch` 仍为 **True**——派发闸门在伪造证据上打开。这是本轮主题（"拒绝任何伪造、Fail-Closed"）的正面反例。
2. **P1-4（新引入的会话伪造）**：`961bcfe` **新增**的 `_find_claude_sessions` 在精确路径目录不存在时，回退到**仅按项目目录同名（basename）**匹配，并把 `workspace` 字段**回填为当前项目路径**。复现中，一个真实 `cwd=/home/other/macao` 的会话被声称为属于 `/tmp/ch2/proj/macao`。`d042395` 上该函数根本不存在 → 这是**修复 P1-2 时新引入的同类缺陷**。
3. **P1-3（脱敏旁路）**：`_sanitize_session_name` 未复用新模块 `secrets.py`，而是自带一条更弱的私有正则，`ghp_*` / `Bearer` / URL 密码 / `sk-ant-*` 全部漏网。纯净树复现中，`probe --dry-run --json` **完整输出了 28 字符 GitHub PAT 明文**（`session_name`/`title`/`details` 三处）。Focus 5 的"无遗漏性"被直接推翻。
4. **P1-2（dry-run 仍写盘）**：只要项目存在 `.macao/state.db`（即场景 C 存量项目的常态），`probe --dry-run` 就会创建 `state.db-shm`(32KB) + `state.db-wal`。P1-1 专项测试只断言"`state.db` 不存在"（在该测试中恒真），**从未覆盖 WAL 场景**，故测试通过而缺陷存活。
5. **P1-1（质量快照失真）**：申请宣称 `145/145 PASS`、"全部为确定性断言"，实测该套件**非确定性**：本评审在工作树 `discover` 复跑得到 **1 failure**，单测复跑 ~17 轮出现 **1 轮失败**；Kimi 独立复跑报告 **2/17 失败**。根因为 `_find_pi_sessions` 仅按 `st_mtime` 排序（`session_locator.py:410`），mtime 相同（Linux 粗粒度时钟同 tick 写入）时由 `glob` 任意顺序决定，`find_session` 默认"最新会话"可能返回错误会话。

依据指引 §8「P0/P1 在 PG-1/PG-2/PG-3 不可豁免」与 §3.3「L3 要求 SIM/TEST 覆盖所有适用 P0/P1 场景且为 VERIFIED」：**本轮不得授予 L3 全量认证**；L4/PG-3 另因缺少 OPS 级实机接管演练证据（与 Grok/Kimi 同判据）独立不成立。既有编排引擎在往轮取得的 L3/PG-2 不在本轮撤销范围，但**探活与会话发现子系统本轮不予认证**。

---

## §2 声明验证矩阵（申请文档逐条机验）

| # | 申请文档声明 | 独立验证方式与观测 | 状态 |
|---|---|---|---|
| 1 | §3.2「**145/145 PASS**，`Ran 145 tests in 63.706s, OK`，0 Failures」 | 工作树 `discover`：`Ran 145 tests in 50.519s **FAILED (failures=1)**`（`test_pi_session_discovery_and_names`：`'Implement feature X' != 'qwen-review-eng'`）；单测 17 轮 1 败；纯净树 `/tmp/v961` 复跑 `Ran 145 tests in 48.235s OK` → **非确定性** | **CONTRADICTED**（P1-1） |
| 2 | 信封 `quality_metrics.tests_passed: true` | 同上，套件存在可复现失败轮次；P1-7 恰是"禁止伪造测试凭据"，本信封在同类事实上失真 | **CONTRADICTED**（P1-1） |
| 3 | §3.2「探活零写盘：工作区文件状态保持 **100% CLEAN**」 | 全新无 `.macao` 项目：`find` 前后零差异 ✓；**存在 `state.db` 时**：纯净树复现 `BEFORE: state.db` → `AFTER: state.db state.db-shm state.db-wal`（32768 / 0 字节） | **PARTIALLY_VERIFIED**（P1-2） |
| 4 | §3.2「`.macao/logs/probe/` 目录未被创建」 | `prober.py:269` `if self.dry_run: return None` 为真守卫；4 个沙箱项目 dry-run 后均无 probe 日志 | **VERIFIED** |
| 5 | §3.2「`compileall src tests` 0 Errors」 | `python3 -m compileall -q src tests` → rc=0，无输出 | **VERIFIED** |
| 6 | §3.2「双 Schema 目录 8 份契约逐字节一致」 | 8 份 `*.schema.json` `cmp` 全 SAME；额外 `diff -r docs/schemas/fixtures src/macao/schemas/fixtures` → IDENTICAL | **VERIFIED** |
| 7 | §3.2「`docs/reviews/` 共 **191** 份（结论 146 / 申请 43 / 处置 1 / STATUS 1），双向 100% 吻合」 | `961bcfe` 已跟踪 190 份（142 result + 42 request + 1 disposition + 1 STATUS + 2 `review-2.5` + 2 `REVIEW_METHODOLOGY`）+ 未跟踪的本申请 = **191**；146 = 142+2+2 ✓；43 ✓ | **VERIFIED**（口径含未入库申请；见 P1-10 证据链问题） |
| 8 | §2 表「本轮共涉及 **27 个文件，+2379 / -237 行**」 | `git diff --numstat 519398d..961bcfe` → **27 files, +2379/-237** 完全吻合 ✓；但**逐行 27 条中 11 条与 git 不符**，且表内数字求和为 **+2616/-210 ≠ 表头 +2379/-237** | **PARTIALLY_VERIFIED**（P2-1） |
| 9 | §1「前序受审基线 `d042395`」+ 27 文件审计范围 | `git diff --numstat d042395..961bcfe` → **29 files, +2594/-228**；被排除的 `bb89ce6`/`519398d` 含**规范性文件 `AGENTS.md`(+5/-1)** 与 `2026-09-07-review-request-d042395.md`(+199)，二者从未经任何评审人裁定 | **PARTIALLY_VERIFIED**（P2-2） |
| 10 | §1.9 / §2 表「确立事实 **F-23（只读零副作用）** 与 **F-24（会话真实绑定）**」 | `git diff 519398d..961bcfe -- docs/usercases/PRODUCT-FACTS.md` 实际新增：F-23 = **任务角色职责对称性**；F-24 = **场景 C 在途接管禁止状态倒退**。全文 `grep 只读\|零副作用\|会话真实` → **无任何一条产品事实固化这两个不变量** | **CONTRADICTED**（P1-8） |
| 11 | §1.2「Codex 校验 `threads.cwd`；Cursor 精确比对；Kimi Fail-Closed 返回空」 | `session_locator.py` Codex 走 `state_*.sqlite` + `Path(cwd).resolve() != resolved_proj` 过滤；Cursor 规范化比对；`:467` Kimi 恒返回 `[]`；3 项专项测试通过；伪造 HOME 复放成立 | **VERIFIED** |
| 12 | §1.2「拒绝任何会话伪造与跨项目串话」（整体声明） | **Claude 路径**：伪造 HOME + `~/.claude/projects/-macao/cccc-dddd.jsonl`（真实 `cwd=/home/other/macao`）→ 对 `/tmp/ch2/proj/macao` 查询返回 1 条，`workspace` 被改写为 `/tmp/ch2/proj/macao` | **CONTRADICTED**（P1-4） |
| 13 | §1.3「客观提审单优先级高于脏改动，按集合差计算未出票名单」 | `prober.py:251-263` 集合差实现；本仓库实跑 dry-run 如实呈现 `REVIEW_PENDING`，Next = `Await pending reviews from: opencode, cursor, antigravity, codex` | **VERIFIED** |
| 14 | §1.4「法定人数完整合取三道门槛，杜绝偷换门槛」 | 决策逻辑 `prober.py:798-801` 三条件合取 ✓；**Focus 4 两反例实机通过**（见 §3）；但 `ui.py:272/394` 展示层仍只印 `minimum_winning_seats`（"Required: 2"），把最弱门槛当作门槛展示 | **PARTIALLY_VERIFIED**（P2-9） |
| 15 | §1.5「全链路敏感数据脱敏体系」/ Focus 5「无遗漏性」 | `secrets.py` 8 类模式实测遮蔽 sk-/ant-/ghp_/Bearer/URL 密码/kv 密码/PEM ✓；**但 `session_locator.py:25` 私有正则漏 ghp_/Bearer/URL 密码/sk-ant-**，`probe --dry-run --json` 完整泄露 PAT 明文；`secrets.py` 自身漏 JWT/AWS AKIA/Google AIza/`api_key:`/`*_TOKEN=` | **CONTRADICTED**（P1-3 + P2-4） |
| 16 | §1.6「`clean` 默认仅安全清理临时 worktree」 | 默认分支确实只动 `.macao/worktrees/` ✓；**但用 `shutil.rmtree` 而非 `GitManager.remove_worktree`**，纯净树复现：`clean` 后 `git worktree list` 残留 `prunable` 幽灵条目，`.git/worktrees/rev-codex_r1` 仍在，重建同名分支 `fatal: a branch named 'feature/rev-codex_r1' already exists` | **PARTIALLY_VERIFIED**（P1-5） |
| 17 | §1.6「`--restore` 支持**无损**还原」 | `main.py:951`（纯净树）`--restore` 先 `shutil.rmtree(macao_dir)` 再 copytree，**未对当前 `.macao` 做任何快照** → 备份后新增的任务/日志被静默销毁 | **CONTRADICTED**（P2-7） |
| 18 | §1.7「`checkpoint --auto` 默认 `tests_passed=False` 阻断状态机」 | `main.py:496/513` 默认 False ✓；`--test-cmd` 非零退出即 `return` 中止 ✓；消费侧 `state_engine.py:50`、`orchestrator.py:273` 均校验 ✓；**但 `live_runner.py:120` 仍硬编码 `tests_passed: True`**，且手写 `.dev.yml` 可完全绕过（无二次校验） | **PARTIALLY_VERIFIED**（P2-5） |
| 19 | §1.8「`task create --force` 驱动旧任务经 E10 转 CANCELLED，消除孤立僵尸任务」 | `orchestrator.py:227-232` + `transitions.py:40` E10 存在 ✓；**但取消逻辑嵌在 `main.py:386 if probe and valid_config` 之内**：纯净树复现 `task create --no-probe --force` → 两条任务同时 `CODING`，`ACTIVE COUNT = 2`，E10 审计事件 **0 条** | **CONTRADICTED**（P1-6） |
| 20 | §1.8「用户显式验收标准逐项注入 Type A AEP 信封」 | `orchestrator.py:194-207` 多态解析 ✓；**但 `store.create_task`（`store.py:24-41`）INSERT 不含 `acceptance_criteria`，`tasks` 表无该列** → 标准从不落库；且 `:205/:207` 在空/缺省时**凭空捏造** `["All unit tests pass","Zero regression"]` | **PARTIALLY_VERIFIED**（P2-3） |
| 21 | §1.9「新增 `PiAdapter`」 | `pi.py` 139 行，5 处注册齐全（`prober.py:40`、`integ_harness.py:38`、`live_dispatcher.py:39`、`adapter/__init__.py`、`wizard.py:31`）；`--tools` 经 `pi --help` 核实**为真实旗标** ✓；会话目录命名 `--<path 斜杠转连字符>--` 与真实 `~/.pi/agent/sessions/--home-debian-macao--` **一致** ✓；`session_info` 事件经 pi dist 核实**为真实事件类型** ✓ | **VERIFIED**（但见 P2-6 三项硬编/捏造） |
| 22 | 信封 `full_document.sha256: "000…000"` | 实测 `sha256sum` = `9f30a01f9436214d470bae4fc728a9f9ab5487fa145d3d8f2c79960d82b503d0`；`.macao/.dev.yml` **在磁盘上不存在**；全库无任何代码校验 `full_document.sha256` | **CONTRADICTED**（P2-5） |
| 23 | 隐含声明：`macao probe` 为派发前 Fail-Closed 闸门 | 纯净树实测：配置**缺失 / YAML 语法错误 / Schema 非法**三种情形下，`probe`、`probe --dry-run`、`probe --json`、`doctor`、`task create --dry-run` **退出码全为 0**；`tests/` 中 16 处 `exit_code` 断言**无一断言非零** | **CONTRADICTED**（P1-7） |
| 24 | 隐含声明：评审对象在投票期内保持冻结 | 投票期内（20:38:40）工作树被并发改动：`main.py` +172、`ui.py` +26、新增未跟踪 `tests/test_task_adopt.py`；申请文档与 STATUS 修改均未提交 | **CONTRADICTED**（P1-10） |

---

## §3 申请方 5 项 Focus 的逐项裁定

| Focus | 申请方要求核验的边界 | 本评审核验方式 | 裁定 |
|---|---|---|---|
| **1** | `.macao` 不存在的全新项目执行 `probe --dry-run`，绝不创建任何文件/目录/SQLite | `/tmp/fresh`、`/tmp/probe_ro_test` 两个新建 git 仓（含合法 `macao.yaml`）：`find` 前后**零差异**，无 `.macao` | **PASS（空仓路径）** |
| **1'** | 同一不变量在**存量项目**（场景 C，本轮主打用例）下是否成立 | `/tmp/v961b`（纯净树）预置 `.macao/state.db` 后 dry-run：新增 `state.db-shm`(32768B) + `state.db-wal`(0B)；本仓库 `/home/debian/macao` 与 `/tmp/rv`、`/tmp/sbx` **三次独立复现同一结果** | **FAIL → P1-2** |
| **2** | Codex/Cursor 会话 `cwd` 与当前项目不一致时严格过滤、绝不回填当前路径 | Codex/Cursor：伪造 HOME 复放，跨项目返回 `[]`，命中时 `workspace` 为真实 cwd → **PASS**；**Claude：`session_locator.py:155-163` basename 回退 + `:214` 回填当前路径 → 复现跨项目串话** | **FAIL → P1-4** |
| **3** | 工作区 dirty 且存在待表决提审单时，Executor 维持 `REVIEW_PENDING`，Next 列出未出票 Reviewer | 本仓库实跑 dry-run：`Work Progress = REVIEW_PENDING`；`Now = Review requested for commit 961bcfe`；`Next = Await pending reviews from: opencode, cursor, antigravity, codex`（`prober.py:251-263` 集合差） | **PASS** |
| **4** | "席位达标但权重不足"与"权重达标但席位不足"两反例应标记 BLOCKED 并分别指出短板 | **反例 A**（`/tmp/fA`：3 席位 2 READY，权重 4.0 < wq 5.0）→ `achievable=false`，`blocking=['Quorum cannot be reached … (effective weight 4.0 < weight quorum 5.0)']` ✓；**反例 B**（`/tmp/fB`：4 席位 2 READY，权重 6.0 ≥ wq 6.0 但 2 < seat_quorum 3）→ `achievable=false`，`blocking=['… (ready seats 2 < seat quorum 3)']` ✓ | **PASS（决策层）**，展示层见 P2-9 |
| **5** | Reviewer 输出含各类 API Key / GitHub Token / 带密码连接串时，**落盘日志与终端回显均被遮蔽** | 构造 pi 会话名 = `ghp_ABCDEFGHIJKLMNOPQRSTUVWX`：`probe --dry-run --json` **完整输出明文 PAT**（`session_name`/`title`/`details`）；终端表格亦回显（被列宽截断为 `ghp_ABCDEFGHIJK…`）；`sk-ant-api03-…` 同样不被遮蔽。（落盘的 probe 审计日志仅记 `Active Session: sid9`，未含名称 → 泄露面为**终端 + JSON**） | **FAIL → P1-3** |

> Focus 4 补充证据（Fail-Closed 正向确认）：构造 `seat_quorum_required: 1`（N=4）被 `core/schema.py:141-145` 拒绝（`less than required minimum ceil(2N/3) = 3`）；构造 `vote_weight: 5 / W=7` 被独裁上限规则拒绝（`3*5=15 >= 2*7=14`）；缺失 `dictator_cap_enabled` 被 JSON Schema 拒绝。**策略层 fail-closed 为真**，缺陷集中在**适配器解析层**（P0-1）与**进程退出码层**（P1-7）。

---

## §4 P0：必须先解决

### P0-1 探活适配器子串模糊匹配 → 捏造 READY 席位与版本号，派发闸门在伪造证据上打开

- **位置**：`src/macao/workflow/prober.py:55-61`
  ```python
  cls = ADAPTER_MAP.get(cli_name.lower())
  if not cls:
      for k, v in ADAPTER_MAP.items():
          if k in agent_id.lower() or k in cli_name.lower():   # ← 用 agent_id 子串顶替适配器
              cls = v
              break
  ```
- **机理**：配置的 `cli` 无法识别时，不 fail-closed，而是按 `agent_id` 子串命中任意适配器（`"cursor" in "cursor"` → `CursorAgentAdapter`，其 preflight 探测的是 `agent` 二进制；`"codex" in "codex"` → `CodexAdapter`，探测 `codex` 二进制），随后把**另一个二进制的真实版本号**当作该席位的版本上报。
- **纯净树复现**（`/tmp/fb`，`PYTHONPATH=/tmp/v961/src`，配置 3 席位、CLI 全为不存在的二进制）：
  ```text
  reviewers: [('cursor','definitely-not-installed-xyz','READY','2026.09.02-c22c1a3'),
              ('codex', 'totally-bogus-bin-qqq',      'READY','2.1.0'),
              ('zzz9',  'totally-bogus-bin-www',      'MISSING','unknown')]
  quorum: {"ready_count":2,"minimum_winning_seats":2,"seat_quorum_required":2,
           "weight_quorum_required":2.0,"total_effective_weight":2.0,"achievable":true}
  CAN_DISPATCH = True   blocking = []
  $ command -v definitely-not-installed-xyz totally-bogus-bin-qqq   →  NOT-FOUND（0/2 安装）
  ```
  对照组 `zzz9`（id 不含任何 ADAPTER_MAP 键）被正确判为 `MISSING`，证明差异**唯一来自子串回退**。
- **影响**：
  1. `ready_count` / `total_effective_weight` 由**幽灵席位**构成 → `quorum.achievable` 与 `can_dispatch` 可被错误置真（上例即为 True），MACAO 会向根本不存在的 CLI 派发评审请求；
  2. 捏造的版本号进入终端报告与 `.macao/logs/probe/*.log` **审计留痕**，污染 F-21 要求的审计可信性；
  3. 操作者的配置错误（拼写、未安装）被**静默吞掉**，永不暴露。
- **违反**：`AGENTS.md`「Fail-Closed Principle：若配置/CLI 工具/Schema 不被识别，必须 fail fast 并拒绝推进；绝不捏造」；`AGENTS.md`「`preflight` 专司基础设施预检：`shutil.which` + `<cli> --version`」；指引 §8「UNKNOWN 若可能影响状态机行为、投票结果或审计完整性，按 P0/P1 处理」。
- **溯源诚实声明**：该缺陷在 `d042395` 已存在（`git show d042395:src/macao/workflow/prober.py` 第 57 行同代码），**非本轮新引入**；但本轮申请的是**探活子系统的 L3 全量认证**，且本轮主题即"拒绝伪造物理事实"，故不可豁免。若团队约定 P0 仅保留给数据损毁/状态腐化，可降级为 P1，但**闸门反转事实与复现步骤不变**。
- **修复要求（验收标准）**：
  1. 删除 `agent_id` 子串回退；`ADAPTER_MAP` 精确未命中即 `status="MISSING"`、`installed=False`、`error=f"Unrecognized CLI '<cli>' (not in ADAPTER_MAP)"`，并计入 `blocking_reasons`；
  2. 上报的 `version` 必须来自**该席位所配置 CLI 的二进制**，禁止跨二进制借用；
  3. 新增负向测试：配置 `cli: "definitely-not-installed-xyz"` + `id: "cursor"`，断言 `status=="MISSING"` 且 `can_dispatch is False` 且 `quorum["total_effective_weight"]` 不含该席位权重。

---

## §5 P1：进入下一阶段前必须修正

### P1-1 质量快照失真：测试套件非确定性，`145/145 PASS` 与 `tests_passed: true` 不成立

- **观测**：
  ```text
  # 工作树 discover
  FAIL: test_pi_session_discovery_and_names (tests/test_pi_and_session_locator.py:107)
  AssertionError: 'Implement feature X' != 'qwen-review-eng'
  Ran 145 tests in 50.519s   FAILED (failures=1)
  # 单测复跑 17 轮：1 败 16 过    # 纯净树 /tmp/v961 discover：Ran 145 tests in 48.235s OK
  ```
  Kimi 同轮独立复跑报告 **2/17 失败**（约 12%）→ 两方独立观测交叉印证。
- **根因**：`src/macao/adapter/session_locator.py:410`
  ```python
  jsonl_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
  ```
  仅以 mtime 排序；Linux 文件时间戳取自**粗粒度缓存时钟**（同 tick 内写入的多个文件 mtime 完全相同），此时 `sort` 稳定但**输入顺序由 `glob()` 的目录项顺序决定**（依赖 inode/文件系统，非确定）→ `sessions[0]` 与 `find_session()` 默认返回的"最新会话"随机漂移。同一缺陷存在于 Claude 路径 `:173`。
- **产品影响**：不止测试抖动——真实场景中同一秒内产生的多个 pi/claude 会话，`find_session` 可能选中**错误会话**用于评审派发（`live_dispatcher` 依赖该结果）。
- **违反**：申请 §3.2「全部为…**确定性**负向/边界断言」、信封 `tests_passed: true`；指引 §3.3「L3 要求 TEST 为 VERIFIED」。
- **修复要求**：排序键改为 `(st_mtime, 文件名)` 双键降序（pi/claude 文件名前缀均内嵌 ISO 时间戳，天然可比较）；新增断言"两个 mtime 相同的会话，顺序由文件名时间戳决定"；`discover` 连续复跑 **≥20 轮全绿**方可复提。

### P1-2 dry-run 探活仍写盘：`mode=ro` 打开 WAL 库必然创建 `-shm`/`-wal`（P1-1 未闭环）

- **位置**：`prober.py:80`、`prober.py:101`（同类：`cli/main.py:312`、`session_locator.py:229/283`）
  ```python
  conn = sqlite3.connect(f"file:{db_path.resolve()}?mode=ro", uri=True, timeout=5.0)
  ```
- **机理**：目标库为 **WAL 模式**（`storage/db.py:113/128` 显式 `PRAGMA journal_mode=WAL`）。SQLite 对 WAL 库即使以 `mode=ro` 打开，只要目录可写就会创建 `-shm` 与 `-wal`，且**关闭后不回收**。通用证明（`/tmp/walproof`）：
  ```text
  after writer close: ['ext_cli_state.sqlite']
  DURING ro open:     ['ext_cli_state.sqlite', 'ext_cli_state.sqlite-shm', 'ext_cli_state.sqlite-wal']
  after ro close:     ['ext_cli_state.sqlite', 'ext_cli_state.sqlite-shm', 'ext_cli_state.sqlite-wal']
  ```
- **纯净树复现**（`/tmp/v961b`）：
  ```text
  BEFORE: state.db
  $ python3 -m macao.cli.main probe --dry-run     (exit=0)
  AFTER : state.db state.db-shm state.db-wal
  -rw-r--r-- 1 debian debian 32768 state.db-shm
  -rw-r--r-- 1 debian debian     0 state.db-wal
  ```
  本仓库 `/home/debian/macao`、副本 `/tmp/rv`、`/tmp/sbx` **三次独立复现同一结果**（评审结束后我已删除本仓库中由我这次探活产生的两个 sidecar，恢复原状）。
- **为何测试漏掉**：`tests/test_p1_closures_and_regressions.py:81-92` 仅断言 `not Path(".macao/state.db").exists()`——该测试从未创建 `state.db`，断言恒真；亦未断言 `.macao/` 目录内容零增量。
- **附带风险**：同一模式用于读取**第三方 CLI 私有库**（`~/.codex/state_*.sqlite`、`~/.local/share/opencode/opencode.db`，实测均为 WAL）。本机因其 sidecar 已由宿主 CLI 存在而未新增；一旦缺失，MACAO 的"只读探活"将**向他人数据目录写入文件**。
- **违反**：`AGENTS.md`「probe/doctor 必须严格只读（`mode=ro`），绝不创建 SQLite 文件/表」；PRODUCT-FACTS 场景 C 用例前提；申请 §1.1「杜绝任何未授权的文件、目录创建」。
- **修复要求**：dry-run 路径改用 `?immutable=1`（并在文档中声明"仅在无并发写者时使用"）或**复制 `state.db` 至临时目录后打开副本**；无法安全只读时 fail-closed 上报 `state_store: SKIPPED(dry-run)` 而非写盘。测试须**先建 WAL 库**再断言 `.macao/` 目录条目集合前后完全相等。

### P1-3 脱敏旁路：`_sanitize_session_name` 未复用 `secrets.py`，完整凭证明文进入 `probe --json`（P1-5 未闭环）

- **位置**：`src/macao/adapter/session_locator.py:25`
  ```python
  cleaned = re.sub(r"\b(sk-[a-zA-Z0-9]{15,}|[0-9a-fA-F]{24,}\.[a-zA-Z0-9_-]{10,})\b", "******", cleaned)
  ```
  该私有正则不含连字符字符类 → `sk-ant-api03-…` 不匹配；完全不覆盖 `ghp_/gho_/github_pat_`、`Bearer`、`://user:pass@`、`password=`。而同一提交新建的 `utils/secrets.py` 已覆盖上述全部类别，却**未被调用**。
- **纯净树复现**（`/tmp/v961c`，pi 会话名 = `ghp_ABCDEFGHIJKLMNOPQRSTUVWX`）：
  ```text
  $ python3 -m macao.cli.main probe --dry-run --json
  FULL GitHub PAT present in machine-readable probe output: True
  pirev -> {"session_name":"ghp_ABCDEFGHIJKLMNOPQRSTUVWX",
            "title":"ghp_ABCDEFGHIJKLMNOPQRSTUVWX",
            "details":"Pi session: ghp_ABCDEFGHIJKLMNOPQRSTUVWX (sid9...)"}
  ```
  直接调用验证：
  ```text
  input : sk-ant-api03-AbCdEfGhIjKlMn   →  output: sk-ant-api03-AbCdEfGhIjKlMn   (LEAKED)
  ghp_…  LEAK | Bearer …  LEAK | postgres://u:Sup3rSecret@h/db  LEAK   （对照 mask_secrets 全部 ok）
  ```
- **泄露面**：终端 Rich 表格（受列宽截断，短凭证可完整显示）+ **`probe --json` 机器可读输出完整明文**——后者最易被重定向、粘贴进 issue 或喂给下游 Agent。落盘的 probe 审计日志本次未含会话名（仅 `Active Session: <sid>`），故泄露面为终端 + JSON。
- **违反**：申请 §1.5「全链路敏感数据脱敏体系」、Focus 5「无遗漏性」、§2 表对 `session_locator.py` 的"引入 `_sanitize_session_name` 脱敏 → P1-5"声明；`macao.yaml security.secrets_masking: true`。
- **修复要求**：`_sanitize_session_name` 内部改为调用 `mask_secrets`（单一真相源，删除私有正则）；对 `session_name`/`title`/`details`/`last_prompt` 在**进入 JSON 与终端前**统一脱敏；新增回归测试断言 `ghp_`/`sk-ant-`/`Bearer`/URL 密码在 `probe --json` 输出中不出现明文。

### P1-4 新引入的会话伪造：Claude 路径按 basename 回退匹配并回填当前项目路径（P1-2 未闭环，且为回归）

- **位置**：`session_locator.py:150-163`（回退）+ `:214`（回填）
  ```python
  if not target_dir.exists() or not target_dir.is_dir():
      exact_name_dir = claude_dir / f"-{resolved_proj.name}"          # 仅按目录同名
      short_sanitized = "-" + re.sub(r"[^a-zA-Z0-9]", "-", resolved_proj.name)
      ...
  "workspace": str(resolved_proj),                                    # 无视记录内真实 cwd
  ```
  Claude 的 JSONL 记录**自带 `cwd` 字段**（Codex 路径正是用它做严格比对），此处却从不读取。
- **复现**（伪造 HOME，`/tmp/ch2`）：
  ```text
  会话文件 ~/.claude/projects/-macao/cccc-dddd.jsonl 内真实 cwd = /home/other/macao
  查询项目 = /tmp/ch2/proj/macao（仅 basename 同为 "macao"）
  → sessions claimed: 1
     session_id= cccc-dddd | reported workspace= /tmp/ch2/proj/macao | name= work on OTHER project
  VERDICT: 跨项目串话 + workspace 回填当前仓 = True
  ```
- **回归证据**：`git show d042395:src/macao/adapter/session_locator.py | grep -n "_find_claude_sessions"` → **无匹配**；该函数为 `961bcfe` 新增。即：**本轮为闭环 P1-2（拒绝会话伪造）而新增的代码，自身引入了一条同类伪造路径**。
- **附带**：`workspace` 回填当前路径同样存在于 pi 路径（`:458`），pi 侧因目录名由完整路径 sanitize 而来风险较低，但字段语义仍是"推定"而非"观测"，应统一改为读取记录内 `cwd` 并以其为准。
- **违反**：申请 §1.2「拒绝任何会话伪造与跨项目串话」、Focus 2「绝不回填当前路径」；PRODUCT-FACTS 会话真实绑定原则（注：该原则本轮并未真的写入 F-24，见 P1-8）。
- **修复要求**：删除 basename 回退；无法验证绑定即返回 `[]`（与 Kimi 同一 fail-closed 策略，`:467` 已有先例）；`workspace` 一律取记录内真实 `cwd`，与 `resolved_proj` 不一致则丢弃该会话；新增跨项目负向测试（同 basename、不同绝对路径）。

### P1-5 `macao clean` 遗留 Git worktree 幽灵注册与分支锁，阻断下一轮派发（P1-6 部分闭环）

- **位置**：`src/macao/cli/main.py:1018`（纯净树；工作树 1190）
  ```python
  shutil.rmtree(wt, ignore_errors=True)     # 未调用 git worktree remove / prune
  ```
  仓库已有正确实现 `utils/git_utils.py:140-147`（`worktree remove --force` + `worktree prune` + 兜底 rmtree），`clean` 未复用。
- **纯净树复现**（`/tmp/v961d`）：
  ```text
  BEFORE: /tmp/v961d/.macao/worktrees/rev-codex_r1  0c2ee5a [feature/rev-codex_r1]
  $ macao clean → "✓ MACAO safe clean completed… Removed 1 temporary review worktree(s)"
  AFTER : /tmp/v961d/.macao/worktrees/rev-codex_r1  0c2ee5a [feature/rev-codex_r1] prunable
          .git/worktrees entries: rev-codex_r1
  重新派发同一评审分支: fatal: a branch named 'feature/rev-codex_r1' already exists
  ```
- **影响**：
  1. Round 2/3 返工再派发时 `create_isolated_worktree` 面对同名分支与残留注册，进入失败或需人工 `git worktree prune`；
  2. `git worktree list --porcelain` 出现 `prunable` 幽灵条目，与 `AGENTS.md`「工作区如实探测而非硬编」冲突（探活虽对 expected 路径正确标注 `NOT_SPAWNED`，但 Git 侧账实已不一致）；
  3. 提示语自称 "safe clean"，实际留下需人工介入的仓库元数据损伤。
- **修复要求**：`clean` 默认分支改为遍历 `.macao/worktrees/` 并调用 `GitManager.remove_worktree()`，收尾执行 `git worktree prune`；新增测试断言 clean 后 `git worktree list --porcelain` 无残留条目、且同名分支可被重新创建。

### P1-6 `task create --force` 的任务唯一性不变量可被 `--no-probe` 完全绕过（P1-8 部分闭环）

- **位置**：`main.py:386`（取消逻辑嵌在探活分支内）+ `main.py:399`
  ```python
  if probe and probe_result.get("valid_config"):     # ← --no-probe 或配置非法时整段跳过
      ...
          orch.cancel_task(old_task_id, reason="Superseded by forced new task creation")
  ```
  下层亦无兜底：`orchestrator.start_task`（`:144-181`）与 `store.create_task`（`store.py:24-41`）都不检查是否已有活动任务；`store.get_active_task`（`store.py:48-54`）用 `LIMIT 1` 取最新一条，**天然掩盖多重活动任务**。
- **纯净树复现**（`/tmp/v961d`）：
  ```text
  $ macao task create --title TaskA --no-probe            exit=0
  $ macao task create --title TaskB --no-probe --force    exit=0
  tasks: TaskA → CODING ; TaskB → CODING
  ACTIVE COUNT = 2  -> invariant violated: True
  E10 cancel audit events: []          ← 零条取消留痕
  ```
  注：配置非法（`valid_config=False`）时同样跳过取消，即"配置坏掉"反而更容易产生僵尸任务。
- **违反**：申请 §1.8「消除孤立僵尸任务」；F-21（审计留痕完整性）；指引 §6 反例库「同一 checkpoint 收到重复产物 / 状态机不变量」。
- **修复要求**：把不变量下沉到 `Orchestrator.start_task`（存在活动任务即 fail-closed 抛错或强制 E10 并留痕），CLI 层不得作为唯一守卫；新增 `get_active_tasks()` 复数接口并在探活中如实上报"多重活动任务"异常；新增 `--no-probe --force` 负向测试。

### P1-7 Fail-Closed 在进程边界失效：配置缺失/语法错误/Schema 非法时退出码恒为 0

- **纯净树复现**（`/tmp/v961tests`）：
  ```text
  malformed YAML      -> probe exit=0 ; probe --dry-run exit=0 ; doctor exit=0
  missing macao.yaml  -> probe exit=0
  schema-invalid      -> probe exit=0 ; task create --dry-run exit=0
  ```
  同时人类可读输出确实打印了 `Configuration Error: …`，`--json` 也如实给出 `valid_config:false` + `blocking_reasons`（**带内信息正确**），`task create --dry-run` 亦打印 `✗ Dry-run probe failed`（`main.py:383`）后 `return`。
- **影响**：任何以退出码为判据的 CI / 守护进程 / 上层脚本都会把"配置非法、闸门关闭"读成"探活成功"。这与 `AGENTS.md`「fail fast 并拒绝推进」相悖；本轮全部 fail-closed 努力在进程边界被清零。
- **测试盲区**：`tests/` 内 16 处 `assertEqual(res.exit_code, 0)`，**无一处断言非零退出码**。
- **修复要求**：`valid_config=False` 或 `can_dispatch=False`（含 `--dry-run`）时以非零码退出（建议 `probe`=2、`doctor`=2、`task create --dry-run`=1），并提供显式 `--allow-degraded` 逃生阀；为三类失败配置各补一条 `assertNotEqual(res.exit_code, 0)` 测试。

### P1-8 规范性事实被错误映射：F-23/F-24 并非申请所称内容，本轮两大不变量**未被固化**

- **申请声明**：§1.9「完善…产品事实（**F-23, F-24**）」；§2 表「确立事实 **F-23（只读零副作用）** 与 **F-24（会话真实绑定）**」。
- **实测**（`git diff 519398d..961bcfe -- docs/usercases/PRODUCT-FACTS.md`，逐字）：
  ```text
  +23. F-23. 任务具有角色职责对称性：CODING/REWORK 唯一责任方为 Executor，
              WAITING_REVIEW 唯一责任方为各 Reviewer 席位，Executor 评审期间只读挂起(STANDBY)。
  +24. F-24. 编排器介入在途项目(场景 C)时必须按 Git 拓扑与物理评审产物如实对账，
              严禁强制倒退为 IDLE -> CODING 或错误建议执行 macao task create。
  ```
  `grep -n "只读\|零副作用\|会话真实\|SessionLocator" docs/usercases/PRODUCT-FACTS.md` → 除 F-1（无关语义）与 F-23 中"只读挂起"（指 Executor 席位状态，非探活副作用）外，**没有任何一条产品事实约束"探活只读零副作用"或"会话必须真实绑定"**。
- **后果**：本轮两条最核心的不变量（正是 P1-1/P1-2 的整改目标）**没有进入规范层**，因此没有可被后续评审引用的裁定依据；而其中一条（只读零副作用）恰在实测中回归（P1-2）。同时申请文档对 normative 产物的描述与产物本身矛盾，属指引 §4「声明 vs 产物」与 §9-B「`[x]` ≠ 证据」的典型失效。
- **修复要求**：新增 **F-25（探活与诊断只读零副作用：任何 probe/doctor/preflight 调用不得在项目或第三方 CLI 目录产生文件、目录、SQLite sidecar 或写锁）** 与 **F-26（会话真实绑定：会话归属必须由记录内可验证的项目路径证明，无法验证即返回空，禁止 basename 推定与路径回填）**，并在 UC-11、`PROBE_TECHNICAL_DESIGN.md` 交叉引用；或修正申请文档中的事实编号与描述，二者必须一致。

### P1-9 探活操作面把"待表决项目"导向 `task create`，与同一提交新增的 F-24 正面冲突

- **观测**（`/tmp/rv`，本仓库副本，存在待表决提审单 + 5 个未提交改动）：
  ```text
  │ Review Baseline │ docs/reviews/2026-09-07…(Baseline: 961bcfe) │ AWAITING REVIEW VERDICTS │
  │ Active Task     │ None (5 files uncommitted in git)            │ UNTRACKED DEV (Run       │
  │                 │                                              │ 'macao task create' to   │
  │                 │                                              │ adopt)                   │
  ```
  底部指引同样落在 `macao task create`；`961bcfe` 上**不存在** `task adopt`（`git show 961bcfe:src/macao/cli/main.py | grep -c 'task.command("adopt")'` = 0），操作者唯一可执行的建议就是把客观处于 `REVIEW_PENDING` 的项目**倒退为 `IDLE -> CODING`**——这正是 F-24 明文禁止的动作，也是 UC-11 §1.1 所称"灾难性状态倒退"。
- **交叉印证**：与 Grok 本轮 P1 第 1 项同一结论；本评审独立复现并补充"`961bcfe` 上无 `adopt` 命令"的 git 级证据（真理不等于投票，此处为证据互证）。
- **修复要求**：当 `physical_reviews` 检出待表决提审单时，`Active Task` 行与底部指引必须改为"等待未出票 Reviewer / 使用 `macao task adopt` 接管"，禁止出现 `task create` 建议；`task adopt` 的实装必须以**新 checkpoint** 提交后重新提审（见 P1-10）。

### P1-10 证据链断裂：申请文档未入库、信封哈希为全零、投票期内工作树被并发整改

- **三项事实**：
  1. `docs/reviews/2026-09-07-review-request-961bcfe.md` 为 **untracked**（`git status`），即**不存在于其自称的 `evidence_commit: 961bcfe`**；`docs/reviews/STATUS.md`、`templates/review-request-template.md` 的修改同样未提交 → 违反指引 §4「产物按 checkpoint/round 区分或**原子提交**，同名覆盖时审计链仍须完整」。
  2. 信封 `full_document.sha256: "0000…0000"`，真实值为 `9f30a01f9436214d470bae4fc728a9f9ab5487fa145d3d8f2c79960d82b503d0`；`.macao/.dev.yml` **磁盘上不存在**；全库无代码校验 `full_document.sha256`（仅 `orchestrator.py:930-939` 校验 `vote_result_ref.sha256` 与 `issues_index_sha256`）→ 该完整性字段目前是装饰性的。
  3. 投票期内（**20:38:40**，晚于申请文档 18:06、晚于 Grok 18:53 / Kimi 18:59）工作树被并发修改：`src/macao/cli/main.py` +172（新增 `task_adopt`）、`src/macao/cli/ui.py` +26（`render_task_adopt_plan`）、新增未跟踪 `tests/test_task_adopt.py`。**评审对象在投票过程中发生了物理变化**。
- **影响**：不同评审人实际审的可能不是同一份代码（本评审已因此必须重做全部复现，见 §0.2）；任何以工作树为准的"PASS"结论都不可复现、不可追溯。
- **修复要求**：将申请文档 + STATUS + 模板 + 整改代码**原子提交**为新 checkpoint（如 `<new-sha>`），在信封中填入**真实 sha256**，重新发起 Round 3 申请；投票期内冻结工作树（整改须在独立 worktree/分支进行）；为 `full_document.sha256` 增加落盘前的真实计算与消费侧校验（不匹配即 fail-closed 拒绝状态推进）。

---

## §6 P2 / P3：可延期但必须登记

### P2（发布前应修正）

| ID | 问题 | 证据 | 建议 |
|---|---|---|---|
| **P2-1** | 变更清单逐行行数**不可复现**：27 行中 **11 行与 git 不符**，且表内求和 `+2616/-210` ≠ 表头 `+2379/-237`（表头与 git 完全吻合，说明表头来自真实 git 而逐行数字非实测）。例：`session_locator.py` 称 +496/-120，实为 **+366/-130**；`main.py` 称 +196/-58，实为 **+150/-46**；`STATUS.md` 称 +45/-3，实为 **+25/-20** | `git diff --numstat 519398d..961bcfe` 逐行比对 | 表格数字由 `git diff --numstat` 自动生成，禁止手填 |
| **P2-2** | 审计范围排除 2 个**未经任何评审**的提交：`bb89ce6`、`519398d`（自基线 `d042395` 起累计应为 **29 files / +2594 / -228**），其中含**规范性文件 `AGENTS.md`(+5/-1)** 与 `2026-09-07-review-request-d042395.md`(+199) | `git diff --numstat d042395..961bcfe` | Round 3 审计范围改为"自上一裁定基线起的全量累计"，并在申请中显式列出被纳入的提交区间 |
| **P2-3** | 验收标准**从不落库**：`store.create_task`（`store.py:24-41`）的 INSERT 不含 `acceptance_criteria`，`tasks` 表无该列（实测 `PRAGMA table_info` = 9 列）；崩溃恢复/Round 2 再派发时无法还原用户标准。且 `orchestrator.py:205/207` 在空或缺省时**凭空捏造** `["All unit tests pass","Zero regression"]`；CLI `--acceptance` 默认 `""` → 实际注入 `[""]`（一条空标准） | `main.py:367`（`default=""`）、`main.py:428-430`、`orchestrator.py:194-207` | 新增 `tasks.acceptance_criteria` 列（JSON）并持久化；空标准时 fail-closed 要求用户显式提供或标记 `UNSPECIFIED`，严禁代拟 |
| **P2-4** | `secrets.py` 覆盖面与"全链路"不符：实测 **LEAK** = JWT(`eyJ…`)、AWS `AKIA…`/`aws_secret_access_key`、Google `AIza…`、`api_key:`/`token:`/`secret:` KV、`*_TOKEN=` 环境变量值；且 `mask_secrets` 以 `pat.pattern.startswith("(Bearer")` 之类**字符串嗅探**决定替换模板（`secrets.py:37-41`），新增模式极易错配 | 13 组样例实测：7 MASKED / 6 LEAKED | 改为 `List[Tuple[pattern, replacement_template]]` 结构；补 JWT/AWS/GCP/通用 KV 三类；为每类补断言 |
| **P2-5** | 完整性与测试凭据字段存在"装饰性/伪造"路径：`live_runner.py:113` 写死 `sha256: 0*64`、`:120` 写死 `tests_passed: True`；`context_builder.py:125/136/144/179` 全部使用 `sha_zero`；`.dev.yml` 已存在时 `checkpoint --auto` 整段跳过校验（手写 `tests_passed: true` 即可绕过 P1-7 闸门） | 见行号；`main.py:486` 条件 `if auto and not dev_path.exists()` | 统一由工具函数计算真实 sha256；对**已存在**的 `.dev.yml` 也执行 `tests_passed` 来源校验（要求同时存在 `test_cmd` 记录或 `tests_exempt` 显式声明），否则 fail-closed |
| **P2-6** | `PiAdapter` 三处环境硬编/捏造：`:37` 硬编 `~/.nvm/versions/node/v24.15.0/bin/pi`；`:50` 修复建议文本内嵌 `/home/debian/.nvm/...`（开发者私有绝对路径进入生产代码）；`:54` `version = res.stdout.strip() or "0.85.1"`（**无输出即凭空捏造版本**，同类反模式见 `antigravity.py:42`、`claude.py:41`、`cursor.py:42`、`opencode.py:42`）。另：`:80` `--tools read,grep,find,ls` 中 `grep/find/ls` 并非 pi 内建工具名（`pi --help` 首行："pi - AI coding assistant with **read, bash, edit, write** tools"）；`capabilities()` 声明 `supports_noninteractive=True` 但 `start()` 从不使用 `-p/--print` | `pi --version` = `0.85.1`（本机真实）；`pi --help` 实测旗标列表 | 版本取不到即 `installed=False`/`version=None`，禁止默认值；路径发现改为遍历 `~/.nvm/versions/node/*/bin/pi` 或读 `npm bin -g`；`--tools` 仅列真实工具名；非交互能力须实装或改为 `False` |
| **P2-7** | `--restore` 并非"无损"：`main.py:951`（纯净树）先 `shutil.rmtree(macao_dir)` 再 copytree，**未对当前 `.macao` 做快照** → 备份之后产生的任务/日志被静默销毁。`--all` 用 `copytree` 快照**活跃 WAL 库**（不含 `-wal`）→ 备份可能不一致；同秒重复 `--all` 时 `copytree` 抛错被 `except` 吞掉并告警，随后**仍执行 rmtree** → 无备份的数据丢失 | `main.py:941-1004`（纯净树） | restore 前自动快照当前 `.macao` 为 `.macao.pre-restore.<ts>/`；快照失败即中止删除（fail-closed）；备份 SQLite 使用 `sqlite3 .backup` 或 `VACUUM INTO` |
| **P2-8** | `vote_weight` Schema 与代码类型不一致：Schema 要求 **integer**（实测 `vote_weight: 0.5` 被拒：`0.5 is not of type 'integer'`），而 `prober.py` 以 float 累加 `total_effective_weight`、`ui.py` 以 `(w:1.0)` 展示、申请文档亦写 `w:1.0` → 分数权重（如初级评审员 0.5）在配置层被禁止 | `schemas/macao_config.schema.json` `vote_weight`；`/tmp/q1` 实测拒绝信息 | 统一为 `number`（含 `minimum`/独裁上限校验），或统一为 integer 并同步修正全部展示与文档（当前 Schema 位置：`macao_config.schema.json:54` `"vote_weight": { "type": "integer", "minimum": 1 }`） |
| **P2-9** | 展示层仍在"偷换门槛"：`ui.py:272` 与 `:394` 只印 `minimum_winning_seats`（本仓库配置为 2，而 `seat_quorum_required=3`、`weight_quorum_required=3`）→ 报告标题写 "Quorum Required: **2** of 4"、摘要行写 "4/4 Ready (Required: **2**)"。决策层正确（Focus 4 已验证），但操作者读到的是**最弱门槛** | `/tmp/fA`：`Consensus Quorum │ 2/3 Ready (Required: 2) │ BLOCKED`（真实短板是 weight 5.0）；`/tmp/fB`：`2/4 Ready (Required: 2) │ BLOCKED`（真实短板是 seat_quorum 3） | 展示 `ready/max(min_winning, seat_quorum)` + `weight/weight_quorum` 双维度，BLOCKED 时在同一行附 `q_reasons` |

### P3（登记即可）

| ID | 问题 | 证据 |
|---|---|---|
| **P3-1** | 申请称脱敏覆盖"日志文件与 **stderr** 全量"，实际 stderr handler 仅在 `MACAO_LOG_CONSOLE=1` 或 `MACAO_DEBUG=1` 时才挂载 | `logger.py:65-70` |
| **P3-2** | `security.allowed_clis` 在配置与向导中均被声明，但**代码中无任何消费点**（`grep -rn allowed_clis src/macao --include=*.py` 仅命中向导默认值与帮助文本）→ CLI 白名单形同虚设，与 fail-closed 叙事不符 | `wizard.py:549`、`main.py:153` |
| **P3-3** | STATUS 账本已滞后：文头声明"结论类 146 / 申请类 43 / 总计 191"，目录实测 **193 份 md（144 result / 43 request）**，因本轮 Grok、Kimi 两份结论尚未登记（其自身亦未提交） | `ls docs/reviews/*.md \| wc -l` = 193；STATUS 第 4/6 行的全量对账规则要求每轮申请前对齐 |
| **P3-4** | 会话名提取仅读文件前 50 行（pi，`:422`）/ 前 30 行（claude，`:184`），长前导（compaction、大量 model_change）时退化为 `pi-<sid8>` 之类无语义名称 | `session_locator.py:422`、`:184` |

---

## §7 跨文档需做的文字修订

1. **申请 §1.5 / §2 表 / Focus 5**：删除"全链路""无遗漏性"绝对化用语，改为列出**已覆盖类别清单**并注明未覆盖类别（JWT/AWS/GCP/通用 KV），或待 P1-3 + P2-4 闭环后再作全量声明。
2. **申请 §1.9 / §2 表**：F-23/F-24 的描述必须与 `PRODUCT-FACTS.md` 实际条文一致（见 P1-8）；若新增只读/会话绑定事实，使用新编号并回填引用。
3. **申请 §3.2**：「145/145 PASS」须附**可复现证据**（如连续 N 轮 `discover` 全绿的日志摘要），并将"确定性断言"改为经抖动测试验证后的表述；`Ran 145 tests in 63.706s` 这类单次耗时不应作为质量指标呈现。
4. **申请 §2 表**：逐行行数改为 `git diff --numstat` 自动填充，并在表头注明比较区间（`<base>..<head>`），避免"27 文件"与"基线 `d042395`"两个口径并存（P2-1/P2-2）。
5. **申请 §1.6**：「无损还原」须限定为"在存在有效快照时"，并披露 P2-7 的当前行为差异。
6. **`AGENTS.md` 项目状态速览**：仍写「128 项测试全部通过」，与本轮 145 项不一致，应随 STATUS 一并更新（该文件属规范性上下文，滞后会误导后续会话）。
7. **`docs/PROBE_TECHNICAL_DESIGN.md`**：需补充"只读实现细节"章节，明确 WAL sidecar 处置策略与第三方 CLI 目录写入禁令（P1-2 的设计层落点）。

---

## §8 建议的闭环顺序与验收标准

| 序 | 项 | 验收标准（复现命令） |
|---|---|---|
| 1 | **P0-1** 适配器子串回退 | 配置不存在 CLI 的席位 → `status=="MISSING"`、`can_dispatch is False`；`probe --json` 中不出现任何非本席位二进制的版本号 |
| 2 | **P1-1** 会话排序抖动 | `for i in $(seq 1 30); do python3 -m unittest discover tests; done` → **30/30 OK**；新增 mtime 相同场景的确定性断言 |
| 3 | **P1-2** dry-run 写盘 | 预置 WAL `state.db` 后 `probe --dry-run`；`find .macao -type f \| sort` 前后**逐行相等**；对 `~/.codex`、`~/.local/share/opencode` 做同样的前后集合比对 |
| 4 | **P1-3** 脱敏旁路 | 会话名含 `ghp_…`/`sk-ant-…`/`Bearer …`/URL 密码时，`probe --json` 与终端输出中**均无明文**；`_sanitize_session_name` 单元测试直接复用 `mask_secrets` |
| 5 | **P1-4** Claude 跨项目 | 同 basename、不同绝对路径的两项目互查 → 均返回 `[]`；`workspace` 字段恒等于记录内真实 `cwd` |
| 6 | **P1-5** clean 残留 | `clean` 后 `git worktree list --porcelain` 无 `prunable` 条目，`.git/worktrees/` 为空，同名评审分支可重新创建 |
| 7 | **P1-6** 任务唯一性 | `task create --no-probe --force` 场景下活动任务恒为 1，且 `audit_events` 存在对应 `TASK_CANCELLED`(E10) 记录 |
| 8 | **P1-7** 退出码 | 三类非法配置 × `probe`/`probe --dry-run`/`probe --json`/`doctor`/`task create --dry-run` → 全部非零退出 |
| 9 | **P1-8 / P1-9** 规范与操作面 | `PRODUCT-FACTS.md` 出现只读零副作用与会话真实绑定两条事实；待表决项目的探活报告与底部指引**不再出现 `task create` 建议** |
| 10 | **P1-10** 证据链 | 申请文档、STATUS、模板与整改代码在**同一提交**内；信封 `sha256` 等于 `sha256sum` 实测值；投票期内 `git status --porcelain` 对 `src/`、`tests/` 恒为空 |
| 11 | **L4/PG-3** | 依指引 §3.3 补 OPS 证据：真实多 CLI（非 `mock-cli`）实机接管演练 + 人工接管路径演练 + 崩溃恢复重复投票检查；`live-run` 默认 `auto_signoff=True` 需改为默认关闭 |

**Round 3 提审门槛**：P0 = 0 且 P1 = 0（指引 §8 不可豁免），P2 至少完成 P2-1/P2-2/P2-3/P2-5（涉及证据可信性与规范一致性），其余 P2/P3 可带风险登记延期。

---

## §9 复现附录（环境与命令）

```bash
# 0. 提取纯净评审对象（关键：工作树在投票期内被改动，见 §0.2 / P1-10）
cd /home/debian/macao
git archive 961bcfe | tar -x -C /tmp/v961
export PYTHONPATH=/tmp/v961/src

# 1. P0-1 幽灵席位（3 席位配置为不存在的 CLI）
cd /tmp/fb && python3 -m macao.cli.main probe --dry-run --json | python3 -m json.tool | head -40
command -v definitely-not-installed-xyz totally-bogus-bin-qqq   # → NOT-FOUND，但报告 READY

# 2. P1-1 测试抖动
cd /home/debian/macao && for i in $(seq 1 20); do
  python3 -m unittest tests.test_pi_and_session_locator.TestSessionLocator.test_pi_session_discovery_and_names 2>&1 | tail -1
done | sort | uniq -c

# 3. P1-2 dry-run 写盘（WAL sidecar）
cd /tmp/v961b && ls .macao/            # BEFORE: state.db
python3 -m macao.cli.main probe --dry-run; ls .macao/   # AFTER: + state.db-shm state.db-wal

# 4. P1-3 凭证明文外泄
cd /tmp/v961c && python3 -m macao.cli.main probe --dry-run --json | grep -o 'ghp_[A-Za-z]*' | sort -u

# 5. P1-4 Claude 跨项目串话
cd /tmp/ch2/proj/macao && PYTHONPATH=/home/debian/macao/src python3 -c "<见 §5 P1-4 脚本>"

# 6. P1-5 clean 残留
cd /tmp/v961d && git worktree add .macao/worktrees/rev-codex_r1 -b feature/rev-codex_r1 HEAD
python3 -m macao.cli.main clean && git worktree list      # → prunable 幽灵条目

# 7. P1-6 双活动任务
cd /tmp/v961d && python3 -m macao.cli.main task create --title TaskA --no-probe
python3 -m macao.cli.main task create --title TaskB --no-probe --force
sqlite3 .macao/state.db "select task_id,state from tasks;"   # → 两条 CODING

# 8. P1-7 退出码
cd /tmp/v961tests && printf 'team: [unclosed\n' > macao.yaml
python3 -m macao.cli.main probe; echo "exit=$?"              # → exit=0

# 9. Focus 4 两反例（PASS）
cd /tmp/fA && python3 -m macao.cli.main probe --dry-run --json | grep -o 'effective weight[^"]*'
cd /tmp/fB && python3 -m macao.cli.main probe --dry-run --json | grep -o 'ready seats[^"]*'
```

- **宿主环境**：Debian，Python 3.12，`pi 0.85.1`（`~/.nvm/versions/node/v24.15.0/bin/pi`），`codex 2.1.0`，`agent`（cursor）`2026.09.02-c22c1a3`，`opencode 1.18.29`；`~/.codex/state_5.sqlite`、`~/.local/share/opencode/opencode.db`、`/home/debian/macao/.macao/state.db` 经 SQLite 头字节校验（offset 18）**均为 WAL 模式**。
- **评审副作用声明**：本评审全部破坏性实验均在 `/tmp/*` 沙箱执行；在 `/home/debian/macao` 内仅执行只读命令与 `probe`，并已删除由该次 probe 产生的 `.macao/state.db-shm` / `.macao/state.db-wal`，仓库工作树未被本评审修改（`git status` 中 `src/`、`tests/`、`docs/` 的改动均为**评审开始前既存**或**执行方并发整改**所致，见 P1-10）。本报告文件为本评审唯一新增产物。

---

**投票 (Vote)**: `NO_APPROVE`
**结论 (Verdict)**: REWORK — 不授予 `961bcfe` 增量 L3 SCENARIO-VERIFIED / PG-2 全量认证；拒绝 L4 RELEASE-READY / PG-3 准入。
**阻断项**: P0 × 1（探活门禁在捏造席位上打开）、P1 × 10（其中 4 项为前序 P1 未真闭环，2 项为本轮修复新引入的回归，4 项为新发现）。
