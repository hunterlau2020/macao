# MACAO Phase 3（PG-3 / L4 RELEASE-READY）独立评审结果 — Claude

- **评审对象**：Commit `3c5ed32`（`feat(phase3): implement Phase 3 live multi-agent dispatcher, daemon, setup wizard, and package schemas`）
- **评审申请**：`docs/reviews/2026-08-31-review-request-Phase3-PG3-L4.md`
- **评审依据**：`docs/MACAO_REVIEW_GUIDELINES.md`（用户指定的 `docs/REVIEW_GUIDE.md` 在仓库根 `docs/` 下不存在；`docs/reference/` 按用户指示不纳入范围）
- **评审人**：`claude`
- **评审日期**：2026-08-31
- **申请目标**：L4 RELEASE-READY / PG-3

---

## 〇、结论

> **不予授予 L4 RELEASE-READY，不予授予 PG-3。**
>
> 阻断项：**P1 × 3**。指引 §176 明确「P0/P1：PG-1、PG-2、PG-3 不可豁免」。
>
> 另外，§62 的 L4 三项最低条件中有两项未达成：**「人工接管路径实机演练」缺席**、**「用户手册齐备」被证伪**。
>
> **已授予的 L3 SCENARIO-VERIFIED / PG-2 不因本轮而撤销**——三项 P1 全部位于 Phase 3 新增模块，均不在 Phase 2 已认证的执行路径上（见 §四 反向核查 R1）。

本轮我先枚举「授予 L4 所需成立的条件」，再逐条找反证，而不是先找缺陷再定级。上一轮我投出了八轮来第一张授予票，因此本轮特别警惕「已授予 → 惯性续授」的锚定。

---

## 一、评审对象界定（§14.5-1 评审对象 = 合并对象）

| 项 | 结果 |
|---|---|
| `git diff --stat 3c5ed32..HEAD -- src tests` | 空 —— 工作树 `src/`/`tests/` 与 `3c5ed32` 逐字节一致，可就地复现 |
| `3c5ed32` 之后的提交 | `7270aa0`（评审申请 + STATUS）、`8871d00`（README.md、PRD、根 `macao.yaml`） |
| **`README.md` 在 `3c5ed32` 中是否存在** | **否**。`git cat-file -e 3c5ed32:README.md` → `fatal: path 'README.md' exists on disk, but not in '3c5ed32'`；由 `8871d00` 引入，**不属于本次评审对象** |

我另在 `/tmp/.../wt` 建立 `3c5ed32` 的干净 worktree，本报告所有实机命令均在该 worktree 或其 `pip install` 产物中执行，避免工作树污染。

---

## 二、申请文档声明的逐条核验（§4 声明验证矩阵）

| # | 申请声明 | 我的实测 | 状态 |
|---|---|---|---|
| 二.1 | 全量测试 `Ran 72 tests, OK (100% PASS)` | 本机 `Ran 72 tests in 19.075s / OK`，复现 | **PARTIALLY_VERIFIED**（见 P2-NEW-8：换干净 PATH 即 FAIL） |
| 二.2 | `compileall` + `git diff --check` 双 0，「Exit Code 0, 100% Clean」 | `compileall` rc=0 属实。但 `git diff --check` 检的是**工作树**，提交之后恒为空、恒 rc=0，对 commit 不构成证据；改用作用域正确的 `git show --check 3c5ed32` 得 **rc=2，3 处 trailing whitespace**（见 P3-NEW-17） | **CONTRADICTED** |
| 二.3 | `live-run` 7 步全闭环，终态 DONE，**7/7 步骤全绿** | 终态 `DONE` 属实；但同一张报告里第 8 行渲染 `6. Physical Archive │ Archived 0 files: │ EMPTY`（红），**并非全绿**；且「全绿」不是断言（见 P1-NEW-15） | **CONTRADICTED** |
| 二.4 | `daemon --once` 正常单次扫描并退出，Exit Code 0 | rc=0 属实，但**仅因当时无活跃任务而在 `daemon.py:27` 提前返回**；一旦存在 `WAITING_REVIEW` 任务即 `AttributeError` 崩溃（见 P1-NEW-14） | **CONTRADICTED** |
| 二.5 | `preflight` 6 款 CLI 及通信组件就绪 | 实跑：Git / SQLite(WAL) + claude-code / codex / opencode / agy / cursor / kimi / mock-cli 全 OK | **VERIFIED** |
| 二.6 | `test-clis` PTY 拉起、ANSI 过滤、0 僵尸 | 实跑 claude/codex/opencode/agy 4/4 PASS，`0 Zombie`，`0 orphan` | **VERIFIED**（ANSI 一项仍受 P2-CARRY-1 限制） |
| 一.1 | `LiveAgentDispatcher` 真实 Worktree 派发 + 两级自愈解析 | 解析器可被任意 YAML 伪造成 APPROVE（P1-NEW-13）；派发函数**全仓零调用方、零测试** | **CONTRADICTED** |
| 一.2 | `OrchestratorDaemon` 超时自动降级、自动触发仲裁 | 该分支从未执行过一次 | **CONTRADICTED** |
| 一.3 | `ensure_gitignore_isolation`「**彻底杜绝**」污染 | 部分成立：`state.db` / `worktrees/` 已隔离，仍有 10 个运行时文件被 `git add -A` 暂存 | **PARTIALLY_VERIFIED** |
| 一.4 | Schema 打包，彻底解决 `pip install` 路径脱钩 | 真实 venv `pip install` 后 6 份 schema 全部从 site-packages 加载，缺字段校验 fail-closed | **VERIFIED** ✅ |
| 一.5 | 全角色互通 + 细粒度模型指定 | 适配器注册表 `live_dispatcher.py:26-37` 覆盖 6 款；模型透传沿用 `29ef7bc` 已认证实现 | **VERIFIED** |
| 一.6 | Phase 3 真实微任务全闭环协同实机演练 | `live-run` 未调用任何 Phase 3 组件（P1-NEW-15） | **CONTRADICTED** |

---

## 三、缺陷清单

### P1-NEW-13　`ReviewExtractor` 可把任意终端 YAML 伪造成 `YES_APPROVE`，且 Schema 校验在设计上无法拦截

**位置**：`src/macao/workflow/live_dispatcher.py:63`、`:70-74`、`:90-91`

```python
for cand in candidates:                      # :63  遍历终端里的每一个 ``` 代码块
    parsed = yaml.safe_load(cand)
    parsed.setdefault("version", "1.0")      # :70
    parsed.setdefault("review_round", ...)   # :71
    parsed.setdefault("checkpoint_ref", ...) # :72
    if "reviewer" not in parsed: ...         # :73-74
    parsed["vote"]      = vote   or "YES_APPROVE"   # :90
    opinion["status"]   = status or "APPROVED"      # :91
    is_valid, err = validate_review_manifest(parsed)  # :93
```

`review_manifest.schema.json:6` 的 `required` 为 `["version","reviewer","checkpoint_ref","review_round","opinion","vote"]` —— **这六个字段无一例外都在 `:70-91` 被提前补齐**。因此 `:93` 的 Draft-07 校验对「意见缺失」这一类输入**恒为真**：校验器只能看到解析器自己填好的表单。这正是 `7973853` 轮 P1-NEW-11（`data.get("signal","EXPLICIT")` / `quality.get("tests_passed",True)`）的同一缺陷模式，换到了 reviewer 投票这一侧。

**反例复现**（`repro_extractor.py`，5 例，全部为 `is_valid=True`）：

```
A. CLI 说自己没跑完：```yaml\nnote: I ran out of context\n```
   valid=True  vote=YES_APPROVE  status=APPROVED
B. CLI 回显自己的配置：```yaml\nmodel: gemini-2.0-pro\ntemperature: 0.2\n```
   valid=True  vote=YES_APPROVE  status=APPROVED
C. CLI 正文写 "This change is UNSAFE and must not be merged."，随后附一个待办清单
   valid=True  vote=YES_APPROVE  status=APPROVED
D. CLI 给出真实 REJECTED 意见
   valid=True  vote=NO_APPROVE   status=REJECTED
E. 完全没有代码块，整段错误日志本身可被 YAML 解析为映射
   valid=True  vote=YES_APPROVE  status=APPROVED
```

**影响链完整**：`:182` 把结果写入 `.macao/.reviews/<agent_id>.review.yml`，正是 `VoteAggregator.collect_reviews` 扫描的目录；该文件由构造保证 schema 合法，因而被计入票数。三个崩溃 / 拒绝 / 答非所问的 reviewer 会产出一次**全票通过**，驱动 `CONSENSUS_CHECK → MERGING` 直至合并。这直接击穿 MACAO 存在的理由。

**定级理由（按指引 §评审原则「拿不准时降一级并注明理由」）**：`dispatch_review_in_worktree` 目前**全仓零调用方**（`grep` 证据见下），当前系统的实际爆炸半径为零，故不定 P0 而定 **P1**；但 PG-3 要授权的恰恰就是把它接上生产，**接线当日即升为 P0**。

```
$ grep -rn "dispatch_review_in_worktree" src/ tests/
src/macao/workflow/live_dispatcher.py:117:    def dispatch_review_in_worktree(   # 唯一出现，定义处
```

**Required action**：`:90-91` 改为缺 `vote`/`status` 即判定提取失败（返回 `False`），禁止任何默认票；`:70-74` 的元数据补齐必须与「意见本体」分离——补齐身份可以，补齐**表决结果**不可以；候选块筛选需先要求 `opinion.status` 存在再进入校验。

---

### P1-NEW-14　`OrchestratorDaemon.scan_once` 在其唯一实质路径上必崩，`run_loop` 静默吞掉，超时降级从未运行过一次

**位置**：`src/macao/workflow/daemon.py:34`、`:38`、`:40-41`、`:48`、`:77-78`

`daemon.py` 与 `StateStore` / `Orchestrator` 之间存在 **6 处独立契约错配**，前面的错配掩盖了后面的：

| # | daemon.py | 实际契约 | 后果 |
|---|---|---|---|
| 1 | `:34` `store.get_audit_events(...)` | `StateStore` 只有 `list_audit_events` / `get_audit_events_by_type`（`store.py:163`、`:187`） | **AttributeError 硬崩** |
| 2 | `:38` `e["event_type"]` | `audit_events` 列名是 `type`（`store.py:163-185` 直接 `dict(r)`） | KeyError |
| 3 | `:38` `"REVIEW_DISPATCHED"` | 实际事件名 `"REVIEW_REQUESTS_DISPATCHED"`（`orchestrator.py:358`）；`REVIEW_DISPATCHED` 全仓不存在 | 永不匹配 |
| 4 | `:40` `dispatch_event["payload"]` | 列名是 `detail` | KeyError |
| 5 | `:41` `payload.get("deadline_epoch", 0)` | payload 键是 `"deadline"`，值为 ISO-8601 字符串（`orchestrator.py:356,362`） | 恒为 0，`deadline > 0` 恒假 |
| 6 | `:48` `a["kind"].endswith(".review.yml")` | 产物 `kind` 是 `"review_manifest"`（`orchestrator.py:525`） | 已提交的 reviewer 也会被判超时 |

**反例复现**（`repro_daemon2.py`，`per_reviewer=1s`，0 份 review，deadline 已过 2s）：

```
== A. daemon --once with NO active task ==
   scan_once -> {'active_task': None, 'action_taken': 'NONE'}          <- 申请文档实测的就是这条
== B. WAITING_REVIEW, per_reviewer=1s, 0 reviews submitted, deadline long past ==
   task state: WAITING_REVIEW
   scan_once RAISED: AttributeError 'StateStore' object has no attribute 'get_audit_events'
== C. run_loop swallows it (daemon.py:75-78) ==
   run_loop(max_ticks=3) returned normally; no error surfaced to operator
   REVIEWER_TIMEOUT_ABSTAIN count: 0
   final task state: WAITING_REVIEW
```

申请文档「后台守护扫描 … Exit Code 0 ✅ PASS」为真，但它测的是 A 分支（`:25-27` 无任务提前返回），与守护进程的职责无关；`tests/test_phase3.py:89` 的用例名 `test_daemon_scanner_single_tick_idle` 自己也写明是 `idle`。**超时降级分支 `:39-66` 至今零次执行、零测试覆盖**（§9 pattern B）。

`:77-78` 的裸 `except Exception: pass` 使这一切在长驻模式下完全不可见：运维看到一个「健康运行」的守护进程，它每 2 秒崩一次、永不推进任何任务。这与 PRD §6.1:1152「系统在任何情况下都不得因超时而静默推进」的精神相悖——此处是**静默地永不推进**，同样使人类失去介入时机。

**Required action**：改用 `list_audit_events` + `type` / `detail` + `REVIEW_REQUESTS_DISPATCHED`，`deadline` 按 ISO-8601 解析，`submitted_reviewers` 按 `kind == "review_manifest"` 且 `reviewer_id` 取值；`run_loop` 的异常必须落审计与 stderr，不得裸 `pass`；补一条「WAITING_REVIEW + 已过期 + 0 提交 → 生成 N 条 `REVIEWER_TIMEOUT_ABSTAIN` 且进入 HOLD」的用例。此外 `:61` 调用 `collect_and_evaluate_consensus(task_id)` 未传 `configured_reviewers`，也未把超时名单传入，弃权票并未真正进入仲裁——修好前五处后这一处会立刻暴露。

---

### P1-NEW-15　`live-run`（L4 唯一端到端证据）不经过任何 Phase 3 组件，其「7/7 全绿」不是断言

**位置**：`src/macao/workflow/live_runner.py:15`、`:36`、`:73`、`:138-155`、`:166-170`、`:195`；`src/macao/cli/ui.py:136`、`:138`

1. **派发器从未被使用**：`:36` 声明 `self.dispatcher`，`:73` 赋值，此后**全文再无一次读取**（§9 pattern A）。第 4 步走的是 Phase 2 的 `orchestrator.dispatch_review_requests`（`:126`），不是 `dispatch_review_in_worktree`。
2. **解析器从未被使用**：`:15` 导入 `ReviewExtractor`，pyflakes 报 `imported but unused`。
3. **审查意见由 runner 自己伪造**：`:138-155` 循环为每个 reviewer 直接写入 `vote: YES_APPROVE / status: APPROVED` 的 manifest。所谓「提取 3 份审查意见 → 2/3 多数票仲裁」，仲裁的是 runner 自己刚写下的三张赞成票。
4. **人工签字是自动生成的**：`:166-170` 直接 `log_audit_event("HUMAN_MERGE_APPROVED", {... "note": "Live runner auto-signoff"})`。**演练里没有人**。
5. **两处 worktree 布局互不兼容**：`live_runner.py:139` 用 `.macao/worktrees/<reviewer>/<task>/r1`（Phase 2 布局，含轮次），`live_dispatcher.py:134` 用 `.macao/worktrees/<task>/<reviewer>`（无轮次，跨轮必然相撞）。
6. **报告自相矛盾且不校验**：`live_runner.py:195` 返回 `archived_count`（int），而 `ui.py:138` 读的是 `result['archived_files']`（list）——键名对不上，于是**每一次 `live-run` 都渲染红色 `Archived 0 files: … EMPTY`**，尽管我查库确认实际归档了 5 份产物且 `consumed=1`、`sha256` 齐全。同时 `ui.py:136` 对每个步骤**无条件**填 `[green]OK[/green]`。因此「7/7 步骤全绿」既非事实（有一行是红的 EMPTY），也非断言（绿色是写死的）。
7. `:197` `"duration": 0.5` 为硬编码常量。
8. 报告标题仍为 `MACAO Phase 2 E2E Micro-Task Report`（`ui.py:128`），且步骤号出现两个 `6.` 两个 `7.`。

**实机输出（`3c5ed32` worktree，`macao live-run`，rc=0）**：

```
│ 5. Consensus Evaluation  │ decision=APPROVED, state=MERGING, votes_yes=3 │ OK    │
│ 6. Fast-Forward Merge    │ state=DONE                                    │ OK    │
│ 7. Final State           │ final_state=DONE                              │ OK    │
│ 6. Physical Archive      │ Archived 0 files:                             │ EMPTY │   <- 红
│ 7. Final FSM State       │ Final task state: DONE                        │ DONE  │
```

**这一条同时构成 L4 的第二个不达成项**：指引 §62 要求「人工接管路径实机演练」、§108 要求「完成用户可见的人工接管演练」。申请文档六行验证表中**没有任何一行是人工接管**，唯一的 signoff 是 `:166-170` 的自动事件。

**Required action**：`live-run` 必须真正调用 `dispatch_review_in_worktree`（修完 P1-NEW-13 之后），或明确改名为 `mock-run` 并在文档中说明它不构成 L4 证据；`ui.py:138` 与 runner 的返回键对齐；步骤状态改为按真实结果着色；另需补一条独立的、有人类输入的 `macao override resolve` 实机演练作为 L4 的 OPS 证据。

---

### P2-NEW-7　共识计票器被重新引入 `YES_APPROVE` 兜底默认值（P1-NEW-11 纪律的回退）

**位置**：`src/macao/consensus/vote.py:97`、`src/macao/workflow/orchestrator.py:557`

本次提交把两处**硬取值**改成了带默认值的软取值：

```diff
- vote_val = data["vote"]
+ vote_val = data.get("vote") or data.get("opinion", {}).get("vote", "YES_APPROVE")
```

原写法 `data["vote"]` 缺键即 KeyError，是 fail-closed；新写法在缺键时**默认赞成**。这与委员会在 `7973853 → 3ea5256` 上花了一整轮建立的「门禁不得有宽松兜底」原则直接冲突，而且位置比当初更靠近核心——是计票器本身。

**降级理由（反向核查后主动下调）**：我逐段读了 `vote.py:22-65`，`collect_reviews:39-41` 在收集阶段已对每份 manifest 做 `validate_review_manifest`，不合法即 `continue`；而 schema `required` 含 `vote`（enum 仅 `YES_APPROVE`/`NO_APPROVE`）。因此进入 `valid_reviews` 的记录**必然**带非空 `vote`，`or` 右支当前**不可达**。这是「编码了 fail-open 语义的防御性死代码」，不是当下可利用的缺陷，故定 **P2 而非 P1**。

需要说明它与 P1-NEW-13 的区别：`ReviewExtractor` 的兜底是**可达且有效**的，因为它在 schema 校验**之前**构造 `vote`，校验器无从拦截；此处的兜底在校验**之后**，被校验器挡住了。两者写法相同，风险截然不同。

**Required action**：还原为 `data["vote"]`，或改为「缺 `vote` 即抛出 / 跳过并落审计」。任何时候都不要把 `YES_APPROVE` 写成默认值。

---

### P2-NEW-8　「72/72 全绿」不可在干净环境复现（PATH 条件性）

**位置**：`tests/test_phase3.py:67`

```python
clis = probe_available_clis()
self.assertTrue(len(clis) > 0)      # :67
```

`probe_available_clis` 依赖 `shutil.which` 扫 PATH。本机装有 6 款 AI CLI，故通过；换成不含这些 CLI 的 PATH 即失败：

```
$ PATH=/usr/bin:/bin PYTHONPATH=src python3 -m unittest tests.test_phase3.TestPhase3Engine.test_wizard_probes_and_smart_config
  File "tests/test_phase3.py", line 67, in test_wizard_probes_and_smart_config
    self.assertTrue(len(clis) > 0)
AssertionError: False is not true
FAILED (failures=1)
```

指引 §评审原则「可复现性」要求「『测试通过』的声明要能在干净环境重跑」。上一轮 ZCode P1-1 刚刚终结了断言的**平台**条件性（`as_posix`），本轮换成了**环境**条件性——同一模式的第二次出现。任何 CI 容器或未装 AI CLI 的评审者机器上，本次 PG-3 申请的头号指标「72/72 100% PASS」都不成立。

**Required action**：该断言改为 `assertIsInstance(clis, list)`，或对 `shutil.which` 打桩后断言解析逻辑；把「探到几款 CLI」留给 `preflight` 报告，不放进单元测试的通过条件。

---

### P2-NEW-9　L4「用户手册齐备」被证伪：删了在用命令、新命令零文档

**位置**：`src/macao/cli/main.py`（`e2e-run` 被替换为 `live-run`）；`docs/FAQ.md:44`、`docs/CONTROLLED_E2E_INTEGRATION_PHASE2.md:70`、`docs/POC_VERIFICATION_REPORT.md:18`

本次提交删除了 `macao e2e-run`（实测 `macao --help` 已无此命令），但在 `3c5ed32` 这棵树里：

- **三份面向用户的文档仍在教用户运行它**（上列三处，均为 `3c5ed32` 内的行号，`git grep -n "e2e-run" 3c5ed32 -- docs/` 排除 `docs/reviews/` 后所得）；
- **三个新命令 `setup` / `daemon` / `live-run` 在 `docs/` 下零文档**：`git grep -ln "live-run\|macao setup\|macao daemon" 3c5ed32 -- docs/`（排除 `docs/reviews/`）返回空；
- **`README.md` 不在评审对象内**（§一）。

指引 §62 的 L4 三项最低条件之一是「用户手册齐备」。按评审对象界定，此项 **CONTRADICTED**。

**Required action**：把三份文档中的 `e2e-run` 更新为 `live-run`（或恢复 `e2e-run` 作为 Phase 2 回归入口），补 `setup`/`daemon`/`live-run` 的用户文档，并把 README 纳入下一个待审 commit。

---

### P2-NEW-10　`dispatch_review_in_worktree` 把真实的 `NO_APPROVE` 反馈为 `YES_APPROVE`

**位置**：`src/macao/workflow/live_dispatcher.py:200`、`:216`

```python
"vote": content.get("opinion", {}).get("vote", "YES_APPROVE"),          # :200
"vote": parsed_manifest.get("opinion", {}).get("vote", "YES_APPROVE"),  # :216
```

schema 把 `vote` 定义在**顶层**（`review_manifest.schema.json:59`），`opinion` 下并无 `vote`。因此 `.get("opinion",{}).get("vote", …)` **必然**命中默认值。实测：

```
manifest written to .review.yml: {'vote': 'NO_APPROVE'} | opinion.status = REJECTED
value dispatch_review_in_worktree:200/:216 reports -> YES_APPROVE
```

落盘的 `.review.yml` 是正确的（`NO_APPROVE`），但函数返回给调用方的字典说「赞成」。这是与 P1-NEW-13 相互独立的第二套伪造机制。因当前无调用方消费该返回值，定 P2。

**Required action**：改为 `parsed_manifest.get("vote")`，缺失即视为提取失败。

---

### P2-CARRY-6　`.gitignore` 隔离是部分修复，不是「彻底杜绝」

**位置**：`src/macao/cli/wizard.py:80`；`src/macao/cli/main.py:176-185`

上一轮 P2-NEW-6 有实质进展：`.macao/worktrees/`、`.macao/*.db` 已入 `.gitignore`，两项最严重的污染（二进制状态库、嵌套 gitlink）已消除。但申请文档 §1.3 的措辞是「**彻底杜绝**审查工作区与状态数据污染主代码库」，实测仍有 **10 个运行时文件**被 `git add -A` 暂存：

```
.macao/.dev.yml
.macao/vote_result.json
.macao/.reviews/{agy,cursor,opencode}.review.yml
.macao/archive/<checkpoint>/r1/{.dev.yml,agy.review.yml,cursor.review.yml,opencode.review.yml,vote_result.json}
```

这些恰恰是 PRD §14.5-1「审计链在哈希层面不得断裂」所保护的产物；把它们提交进「正在被评审的那个 commit」本身，重新引入了上一轮我提出的「评审对象 = 合并对象」风险。

另外 `ensure_gitignore_isolation` 只在 `macao setup` 中被调用；`macao init`（`main.py:176-185`）仍只写 `macao.yaml`，不写 `.gitignore`。走 `init` 路径的用户完全得不到保护。

**Required action**：`entry`（`wizard.py:80`）追加 `.macao/.reviews/`、`.macao/archive/`、`.macao/.dev.yml`、`.macao/vote_result.json`；`macao init` 同样调用 `ensure_gitignore_isolation`；申请文档的「彻底杜绝」改为与实现相符的表述。

---

### P2-CARRY-1　`integ_harness.py:115` ANSI 断言仍是自指的（横跨 11 个待审 commit 未修）

```python
ansi_stripped_ok = all(not bool(ANSI_ESCAPE_RE.search(line)) for line in clean_logs) if clean_logs else True
```

`clean_logs` 已在 `pty_session.py:89` / `:96` 用同一条正则 `strip_ansi` 过，此处等价于断言 `strip_ansi` 幂等，无法证伪「ANSI 过滤有效」。`test-clis` 报告的 `ANSI Strip ✓ YES` 因此仍是 CLAIM_ONLY。

底层问题最早记录于 `4df059e` 轮（当时形态是 `ansi_stripped_ok = True` 无条件常量），以 `P2-CARRY-1` 编号首次出现于 `bf5ae2d` 轮，至本轮共横跨 11 个待审 commit（`4df059e`、`7935da3`、`bf5ae2d`、`e7ba2d2`、`ea536ab`、`f41b9da`、`3e1a991`、`7973853`、`3ea5256`、`8296f3c`、`3c5ed32`）。它从未被正式风险接受，也从未到期——只是每轮被重新抄写一遍。原样结转。

---

### P3-NEW-13　向导生成的 `macao.yaml` 自相矛盾：声明 2/3 多数，实际要求全票

**位置**：`src/macao/cli/wizard.py:131-132`；`src/macao/core/config.py:46`

```yaml
policy:
  consensus_rule: 2/3_majority      # wizard.py:131
  min_effective_votes: 3            # wizard.py:132  == len(reviewers)
```

`config.py:46` 是 `if configured_quorum is None or configured_quorum < derived_quorum:` —— 只在配置值**小于**派生法定值 `⌈2N/3⌉` 时上调，配置值更大时保留。N=3 时派生值为 2，向导写死 3，于是**保留 3**：实际语义是全票一致，与相邻行声明的 `2/3_majority` 冲突。方向上是 fail-closed（更严格），不构成安全风险，但这是用户拿到的第一份配置文件，且是「一个 reviewer 超时就永远无法达成共识」的直接成因。

**Required action**：`wizard.py:132` 改为 `math.ceil(2 * len(reviewers) / 3)`，或删除该键让 `config.py:44-47` 自行派生。

---

### P3-NEW-14　`probe_available_clis` 在探测失败时报告硬编码的假版本号

**位置**：`src/macao/cli/wizard.py:18-23`、`:26-33`

```python
candidates = [("opencode","opencode","1.18.25"), ("claude-code","claude","2.1.251"), ...]  # :18-23
    res = subprocess.run([exe, "--version"], ...)
    ver = res.stdout.strip() or default_ver     # :31
except Exception:
    ver = default_ver                           # :33
```

`--version` 超时、报错或输出到 stderr 时，向导会把**写死的常量**当作实测版本打印给用户（`main.py` setup 分支 `• opencode (1.18.25) -> /path`）。对 L4 的 OPS 证据而言，这是把猜测呈现为观测。另外申请文档 §1.3 称该函数扫描「真实版本**与可用模型**」——代码中没有任何模型探测逻辑。

**Required action**：探测失败时显示 `unknown (probe failed)` 并降级标注；删除「可用模型」的表述，或补上真实探测。

---

### P3-NEW-15　新增四个模块共 22 处未使用导入 / 声明后从不读取的字段（§9 pattern A）

pyflakes 于 `3c5ed32`：`live_dispatcher.py` 8 处、`daemon.py` 4 处、`live_runner.py` 9 处、`wizard.py` 3 处。其中两处有诊断价值，已在 P1-NEW-15 引用：`live_runner.py:15` 的 `ReviewExtractor` 与 `live_dispatcher.py:109` 的 `self.active_sessions`（声明后全类无一次读取）——它们是「组件已交付但未接线」的静态指纹。

---

### P3-NEW-16　Schema 出现两份副本且无同步机制

`docs/schemas/*.schema.json` 与 `src/macao/schemas/*.schema.json` 在 `3c5ed32` 上 **6/6 逐字节一致**（我已 `diff` 全量核对）。但 `core/schema.py:18` 让**包内副本优先**，而 §5 的权威表指向 `docs/schemas/`。仓库中没有任何测试或生成脚本保证两者一致，未来对 `docs/schemas/` 的修改将静默不生效。

**Required action**：加一条 `docs/schemas/` ↔ `src/macao/schemas/` 逐文件 sha256 相等的测试，或改为构建期从 `docs/schemas/` 复制生成。

---

### 决策项（非缺陷）　`ci_gate_command: null` 时 CI 门禁被跳过

`merge/controller.py:87` 是 `if ci_gate_command:`，为空即跳过 CI 直接进入签字与合并（注释明写 "Optional CI gate"，schema `macao_config.schema.json:63` 也允许 `null`，属既定设计）。但 `wizard.py:138` 写入的 `ci_cmd` 来自 `detect_ci_command` 的 5 条启发式（pytest/npm/cargo/go），Java、Ruby、C++ 等项目一律得到 `null`——用户在毫无提示的情况下拿到一份「合并无 CI 门禁」的配置。按指引「区分缺陷与决策」，我不记为缺陷，但**生产化前需要**：向导在推断不出 CI 命令时显式警告，并在 `macao doctor` 中把「CI 门禁未配置」列为告警项。

### P3-NEW-17　`git diff --check` 作用域错配：对 commit 的洁净声明用工作树命令佐证

**位置**：申请文档「代码与配置编译检查」行

`git diff --check` 比较的是**工作区与索引**，在提交完成后必然为空，因此它对「这个 commit 是否洁净」**恒为真且零信息量**。作用域正确的命令是 `git show --check <commit>`：

```
$ git show --check 3c5ed32 ; echo rc=$?
docs/reference/REVIEW_METHODOLOGY.md:4: trailing whitespace.
docs/reference/REVIEW_METHODOLOGY.md:5: trailing whitespace.
docs/reference/REVIEW_METHODOLOGY.md:6: trailing whitespace.
rc=2
```

三处均为 Markdown 行尾双空格硬换行，语义无害，故只定 P3。但「Exit Code 0, 100% Clean」这一声明本身不成立。

**这是本轮第三次出现同一族问题**：绿灯是在错误的参照系里测出来的——P2-NEW-8 是**环境**参照系（PATH），上一轮 ZCode P1-1 是**平台**参照系（`as_posix`），此处是**版本**参照系（工作树 vs commit）。三次分别被三位评审者当作三个孤立缺陷处理，说明缺的是一条通则而非三次修补。建议写入指引，见我对指引的改进建议。

**更正声明**：本报告初稿在 §二 把该行判为 VERIFIED，依据是我自己跑的 `git diff --check`（rc=0）——我沿用了申请文档给出的命令而未质疑其作用域，这正是我在别处要求作者做到而自己没做到的事。经 glm 的方法论对比报告第 71 条提示后复核，已改判为 CONTRADICTED。原判不影响本轮门禁结论（L4/PG-3 的阻断项是三条 P1，与本条无关）。

**Required action**：申请模板中的该行命令改为 `git show --check <commit>`；`macao` 项目若有 CI，同步加入。

---

---

## 四、反向核查（我主动去找、但没找到问题的地方）

按 §9 自审要求，记录这些以免读者误以为未被检视。

**R1　Phase 2 已认证路径是否被本次提交打破** —— 未打破。`3c5ed32` 对 `src/` 既有文件只动了两行（`vote.py:97`、`orchestrator.py:557`，即 P2-NEW-7），其余全为新增文件。72 项测试含 Phase 2 的 `test_e2e_phase2.py`、`test_p0_p1_rectification.py` 全绿；`transitions.py:42-51` 的 E7/E9 人工覆盖守卫、`merge/controller.py` 的五道 fail-closed 关卡均原样保留。**故 L3 / PG-2 不予撤销。**

**R2　Schema 打包是否真的解决了 `pip install` 路径脱钩** —— 真的解决了。这是本轮唯一完整成立的交付物。我建干净 venv 实测：

```
$ ./venv/bin/pip install ./wt          → rc=0
schemas dir -> .../venv/lib/python3.12/site-packages/macao/schemas
loaded schemas: ['aep_envelope','dev_manifest','macao_config','review_context','review_manifest','vote_result']
validate good dev_manifest: (True, None)
validate bad  dev_manifest: (False, "'executor' is a required property")
$ ./venv/bin/macao --help              → rc=0
$ ./venv/bin/macao setup（在空 git 仓库中） → rc=0，生成 macao.yaml + .gitignore
```

`pyproject.toml:41-42` 的 `package-data` 配置正确，`src/macao/schemas/__init__.py` 存在因而被 `packages.find` 收录。历史遗留的 P2/P3 路径脱钩问题**确认关闭**。

**R3　`collect_reviews` 是否仍 fail-closed** —— 是。`vote.py:39-41` 对每份 manifest 做 Draft-07 校验后才收集，这正是把 P2-NEW-7 从 P1 降到 P2 的依据。同时也说明：现有防线依赖「manifest 由外部产生、由 schema 把关」这一前提，而 P1-NEW-13 恰恰破坏了这个前提（manifest 由己方构造）。

**R4　人工接管命令是否还在** —— 在。`macao override resolve` 可用，`transitions.py:43-51` 的 E7/E9 约束完好。缺的是**演练与证据**，不是能力。

**R5　`test-clis` 与 `preflight` 是否掺水** —— 未掺水。两者都真实拉起本机 CLI 进程，`preflight` 8 行全 OK，`test-clis` 4/4 PASS 且 `0 Zombie / 0 orphan`。唯一保留意见是 P2-CARRY-1 的 ANSI 自指断言。

**R6　`live-run` 的归档链是否真的断了** —— 没断。虽然界面显示 `Archived 0 files … EMPTY`，我直接查 SQLite 确认实际写入 5 行产物，`consumed=1`、`sha256` 均 64 位、`archived_path` 与 `.macao/archive/<ref>/r1/` 下 5 个物理文件 1:1 吻合。断的是**报告渲染**（`ui.py:138` 读了一个 runner 从不产出的键），不是审计链。这一点我特意区分开，避免把 UI 缺陷夸大成 P1 数据完整性问题。

---

## 五、门禁判定

| 门禁 | 条件（指引 §62 / §73 / §108 / §176） | 判定 |
|---|---|---|
| **L3 / PG-2** | 前八轮已授予 | **维持**（R1） |
| **L4 RELEASE-READY** | L3 + 人工接管路径实机演练 + 回归无 P0/P1 + 用户手册齐备 | **不予授予**：三项条件中，人工接管演练**缺席**（P1-NEW-15 §5）、用户手册**被证伪**（P2-NEW-9）、P1 **为 3**（§176 不可豁免） |
| **PG-3** | L4 | **不予授予** |

**OPS 证据状态**：`test-clis`、`preflight`、`pip install` 三项为 VERIFIED；`daemon` 为 **CONTRADICTED**；`live-run` 为 **CONTRADICTED**（作为 L4 端到端证据）。§108 要求 L4 的 OPS 整体 VERIFIED，未达成。

---

## 六、放行建议（最小路径）

1. **P1-NEW-13**：`live_dispatcher.py:90-91` 去掉两个默认值，缺意见即提取失败；候选块须先含 `opinion.status` 才进入校验。
2. **P1-NEW-14**：修正 `daemon.py` 六处契约错配；`run_loop` 异常落审计；补「超时 → N 条 ABSTAIN → HOLD」用例。
3. **P1-NEW-15**：`live-run` 真正调用 `dispatch_review_in_worktree`，或改名并声明它不是 L4 证据；`ui.py:138` 键名对齐、状态按实着色。
4. **补 L4 硬条件**：一次有真实人类输入的 `macao override resolve` 实机演练（带终端记录）；三份文档的 `e2e-run` 更新；`setup`/`daemon`/`live-run` 补文档；README 纳入待审 commit。
5. **P2-NEW-7 / P2-NEW-8**：还原 `data["vote"]`；`test_phase3.py:67` 去 PATH 依赖，使 72/72 可在干净容器复现。
6. P2-NEW-10、P2-CARRY-6、P2-CARRY-1 与五项 P3（含 P3-NEW-17 的验证命令作用域修正）可随上述批次一并处理。

以上 1–5 完成后，我认为 Phase 3 具备重新申请 L4 / PG-3 的条件。

---

## 附：本报告使用的复现脚本与命令

```bash
# 干净评审对象
git worktree add -f <scratch>/wt 3c5ed32

# 二.1 / P2-NEW-8
PYTHONPATH=src python3 -m unittest discover tests            # Ran 72 tests, OK
PATH=/usr/bin:/bin PYTHONPATH=src python3 -m unittest \
  tests.test_phase3.TestPhase3Engine.test_wizard_probes_and_smart_config   # FAILED

# 二.2 / 二.3 / 二.5 / 二.6
python3 -m compileall -q src tests            # rc=0
git show --check 3c5ed32                      # rc=2, 3 处 trailing whitespace（P3-NEW-17）
PYTHONPATH=src python3 -m macao.cli.main live-run
PYTHONPATH=src python3 -m macao.cli.main preflight
PYTHONPATH=src python3 -m macao.cli.main test-clis

# P1-NEW-13
<scratch>/repro_extractor.py        # 5 例，A/B/C/E 均伪造出 YES_APPROVE

# P1-NEW-14
<scratch>/repro_daemon2.py          # A 空转 / B AttributeError / C run_loop 静默吞

# R2
python3 -m venv venv && ./venv/bin/pip install ./wt && ./venv/bin/macao --help
```

---

**评审人签名**：`claude`
**日期**：2026-08-31
**结论**：**不予授予 L4 RELEASE-READY / PG-3**；维持 L3 SCENARIO-VERIFIED / PG-2。
**阻断项**：P1-NEW-13、P1-NEW-14、P1-NEW-15，外加 L4 硬条件「人工接管实机演练」与「用户手册齐备」未达成。
