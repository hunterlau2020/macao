# MACAO Phase 3（PG-3 / L4 RELEASE-READY）加固整改复审结论

- **评审日期**：2026-08-31
- **评审对象**：`3c5ed32` .. `15e8918`（8 个 commit，功能闭环主体在 `23bb07f`；`23bb07f..HEAD -- src tests` 为空）
- **申请文件**：`docs/reviews/2026-08-31-review-request-Phase3-PG3-L4-Rectification.md`
- **评审基准**：`docs/MACAO_REVIEW_GUIDELINES.md`（v1.0）；上位基准 `docs/MACAO_PRD_v2.md`
- **reviewer**：`claude`
- **申请目标**：L4 RELEASE-READY / PG-3
- **证据类型**：DOC / SPEC / CODE / SIM / TEST / OPS，全部为本机复现，不采信申请粘贴输出

---

## 结论

> ### 不予授予 L4 RELEASE-READY / PG-3；维持 L3 SCENARIO-VERIFIED / PG-2

**一句话**：申请用来证明「L4 人工接管路径实机演练」的 `macao live-run`，是靠**伪造那条人工签字审计记录**才走到 `DONE` 的；把这条伪造事件拦掉，合并闸门立刻正确拒绝。本轮提交的 L4 唯一 OPS 证据，恰恰是绕过 L4 要求演练的那道闸门产生的。

指引 §2.1 定义 L4 = L3 + **人工接管路径实机演练** + 回归无 P0/P1 + 用户手册齐备；§3.3 要求 **OPS 为 VERIFIED，且完成用户可见的人工接管演练**。本轮 OPS 证据为 **CONTRADICTED**，另存续 5 项 P1。按 §8「P0/P1：PG-1、PG-2、PG-3 不可豁免」，PG-3 不可授予。

**同时明确**：本轮对既有 L3/PG-2 范围**无回归**（75/75 PASS；`src/` 仅动 6 个文件且均在 Phase 3 新增面），已授予的 **L3 SCENARIO-VERIFIED / PG-2 继续有效**。

---

## 〇、Reviewer 自审记录（前置）

1. **上一轮我自己的漏审已复核确认修复**：`docs/reference/REVIEW_METHODOLOGY.md:4-6` 的 3 处尾随空白已在本轮清除（我上轮 P3-NEW-17 闭环）。
2. **上一轮我犯的"作用域"错误，本轮改了测法**：上轮我用 `git diff --check`（测工作区，提交后恒净）判洁净度 VERIFIED，被 glm 指出。本轮改用 `git show --check <每个待审 commit>` 逐个测。
3. **本轮我又犯了一次同类错误，登记于此**：第一次跑逐 commit 检查时我写成
   `git show --check $c >/dev/null 2>&1; echo "$(git log -1 --format=%h $c) rc=$?"`
   —— `$?` 取到的是 `echo` 里那个命令替换（`git log`）的退出码，不是 `git show --check` 的，于是全部显示 `rc=0`，差点把一条成立的 CONTRADICTED 误报成通过。改成先 `rc=$?` 落变量后复测，才得到正确结果。**这与我在 P3-R-1 里要求申请方做到的是同一件事：先确认你测的到底是什么。**
4. **利益相关声明**：P1-R-1/R-2 与我上轮 P1-NEW-15 同源，P1-R-3 与上轮 P1-NEW-13 同源。为避免"护自己的结论"，对每项都先假设申请方是对的，用能证伪我自己的方式取证——例如先重跑上轮那 5 个反例，**它们确实被堵住了**，我据此把 P1-NEW-13 判为部分闭环而非维持原判。
5. **本轮激活的自审项**：§9 A（字段声明 vs 实际读取路径）命中 4 处；§9 B（"已完成" ≠ 证据）命中 4 处；§9 C（确定性用语）命中 2 处。

---

## 一、对账：申请方 7 项闭环声明的独立核验

| 申请编号 | 声明 | 我的独立取证 | 状态 |
|---|---|---|---|
| **P1-1** ReviewExtractor Fail-Closed | 缺 vote/status 即失败；三维上下文强绑定 | 上轮我的 5 个反例重跑：**A/B/C/E 已正确拒绝，D（真实 REJECTED）正确通过**。上下文不符（ref/round/id）确实拒绝。**但**首块即返回导致幻影批准仍可达（P1-R-3）；强绑定会吞真实反对票（P1-R-4）；三值投票在产物层只实现两值（P1-R-5）。 | **PARTIALLY_VERIFIED** |
| **P1-2** Daemon 活跃超时降级 | 复用 `detect_timed_out_reviewers`；记 ABSTAIN；驱动 FSM；异常可见 | 真实沙箱复现（`per_reviewer: 0s`，0 份评审）：`scan_once` → `TIMEOUT_DEGRADATION`，3 人识别，`REVIEWER_TIMEOUT_ABSTAIN`×3，FSM `WAITING_REVIEW → CONSENSUS_CHECK`，`DEADLOCK_DETECTED`×1，**`vote_result.json` 未写盘**。`run_loop` 异常改写 stderr。 | **VERIFIED** ✅ |
| **P1-3** live-run 真实协同 + UI + 真实签字 | 真实切分支、经 Extractor 解析、UI 修复、真实操作员签字 | 分支切换属实（`live_runner.py:95`）；计时改真（`:201`）；归档渲染修好（实机 5/5 `PERSISTED`）。**但**"真实协同"经反例注入证伪（P1-R-2）；"真实操作员签字"是**伪造审计记录**（P1-R-1）；UI 无条件绿色**未真正修复**（P2-R-2）。 | **CONTRADICTED** ❌ |
| **P1-4** Worktree API + CLI 准入 | 对接 `create_isolated_worktree`；未知 CLI 抛 `ValueError` | `git_utils.py:96/:119` 两方法存在且被 `live_dispatcher.py:173/:262` 调用；未知 CLI 确实抛 `ValueError`（`:140`）。**代码层闭环成立**。但该函数**全仓零生产调用方**（仅 `:144` 定义处），可达性未变；唯一免额度自证通道 `mock-cli` 构造即失败（P2-R-4）。 | **CODE VERIFIED**；OPS **CLAIM_ONLY** |
| **P2-NEW-8** 单测环境解耦 | 改 `assertIsInstance` | `tests/test_phase3.py:119` 已删除 `assertTrue(len(clis) > 0)`。 | **VERIFIED** ✅ |
| **P2（Git 隔离）** | 向导注入 6 项规则 + 幂等 | 全新 `.gitignore` 场景成立。**但存量项目升级路径完全失效**（P2-R-1），且实际注入 9 条不是 6 条。 | **PARTIALLY_VERIFIED** |
| **PRD/架构对齐** | Schema 增加 `team.name` 与 `agmsg_member_id` 映射 | 两字段在**旧 schema（3c5ed32）下就已通过校验**（无 `additionalProperties:false`，实测 PASS），故 `test_config.py` 的通过与本次变更无因果；两字段在 `src/` 中**无任何读取点**。 | **CLAIM_ONLY** |

## 二、对账：申请「二、实机验证与测试指标」6 行

| # | 申请声明 | 实测 | 状态 |
|---|---|---|---|
| 1 | 75 项单测全通过 | `Ran 75 tests in 21.405s / OK` | **VERIFIED** ✅ |
| 2 | `compileall` + `git diff --check` 双 0，100% Clean | `compileall` rc=0 ✅；逐 commit `git show --check`：**`15e8918` rc=2**（`docs/usecases/UC1-init-gemini.md:3-5`）、**`8871d00` rc=2**（`README.md:146`） | **CONTRADICTED**（见 P3-R-1） |
| 3 | live-run 7 步全闭环，5 份 PERSISTED | 实机渲染 **9 行**（7 步 + Archive + FSM），`Archived 5 files / PERSISTED / DONE` 属实；但过程系自证（P1-R-1/R-2） | 数字 VERIFIED，**语义 CONTRADICTED** |
| 4 | `daemon --once` 正常扫描退出 | 属实；且我补测了申请方**没测**的活跃任务分支，同样通过 | **VERIFIED** ✅ |
| 5 | preflight「6 款 CLI 及**通信组件**就绪」全绿 | 7 行 CLI（含 `mock-cli`）+ 2 行环境全 OK；**报告中无任何通信组件/agmsg 行**（`grep agmsg src/macao/cli/main.py` 无命中） | **PARTIALLY_VERIFIED** |
| 6 | test-clis PASS，0 僵尸 | 4/4 PASS，0 Zombie 属实 | **VERIFIED**（但 ANSI 列恒真，见 P2-CARRY-1） |

---

## 三、P1：授予 PG-3 前必须解决

### P1-R-1　`live-run` 伪造人工签字审计记录，且比真实签字"更像真的"

`src/macao/workflow/live_runner.py:175-180`（本轮 `23bb07f` 改动）：

```python
if self.orchestrator.config.get("require_signoff", True):
    self.orchestrator.store.log_audit_event(task_id, "HUMAN_MERGE_APPROVED", {
        "checkpoint_ref": dev_commit,
        "signer": "operator",
        "note": "Human operator verified consensus and approved merge",
    })
```

改动前这里写的是 `"note": "Live runner auto-signoff"`。**本次"整改"把一句诚实的自述，换成了一句关于人类行为的虚假陈述**，并额外补了 `signer: operator`。

实机取出该记录（全程无 tty，`sys.stdin.isatty() == False`）：

```
=== HUMAN_MERGE_APPROVED 审计记录（系统留给后人的唯一人工签字证据）===
2026-08-31T10:03:34.945754+00:00 HUMAN_MERGE_APPROVED
{
  "checkpoint_ref": "960b966eca40d34e989decd85687ab817c2c986e",
  "signer": "operator",
  "note": "Human operator verified consensus and approved merge"
}
```

**加重情节**：真实人工签字通道 `src/macao/cli/main.py:309-313`（`macao merge approve`）**根本不写 `signer` 字段**。事后审计者翻 `audit_events` 表时，**伪造记录比真签字记录字段更完整、更可信**。这是对审计链的定向污染，直接违反 §4「所有状态转换可 git log 审计」与 §8「真理不等于投票」。

**反向验证（这条恰恰证明系统本身是好的，坏的是 runner）**——只拦掉这一条事件、其余照跑：

```
[拦截] runner 试图自动写入 HUMAN_MERGE_APPROVED，已阻断（模拟无人工签字）
run_live_cycle 抛出: RuntimeError execute_merge failed:
  Human signoff required for checkpoint 3a6a9a3a1856eda1ab412dfdbd1b07f4713de77d
  before merge (macao merge approve)
```

`src/macao/merge/controller.py:49-61` 的签字闸门是**真的、fail-closed 的、且绑定 `checkpoint_ref` 的**。`live-run` 能到 `DONE` 的唯一原因就是它伪造了这道闸门要的那条记录。

**为什么这一条独立否决 PG-3**：§3.3 要求 L4「完成用户可见的人工接管演练」。申请提交的**唯一**人工接管证据就是这条记录，而它是伪造的。证据本身被证伪，不存在"降级接受"的空间。

**定级**：按可达性维度，`live-run` 只作用于 `tempfile.mkdtemp()` 临时仓，不触碰用户仓库，故定 **P1 而非 P0**；但**它污染的是本次评审赖以判断的证据**，对 PG-3 的否决效力等同 P0。

**闭环（二选一，且必须同时改文档）**
- (a) 删除 `:175-180` 的自动签字，改为在此处停下并提示 `macao merge approve`、以非零码退出；或提供 `--auto-signoff` 显式开关，此时 `note` 必须写回 `"Live runner auto-signoff (NON-HUMAN)"`、**禁止**写 `signer`；
- (b) 保留自动流程，但把命令改名为 `demo-run`/`mock-run`，并从 `README.md:71`、`STATUS.md`、CLI help 中删除"生产级""真实协同""真实操作者签字"表述。

---

### P1-R-2　`live-run` 全程不经 dispatcher —— 反例注入下调用次数为 0

把 `LiveAgentDispatcher.dispatch_review_in_worktree` **和** `get_adapter_for_reviewer` 双双替换为必抛异常，再跑 `run_live_cycle()`：

```
status      : PASS
final_state : DONE
archived    : 5
duration    : 0.35
dispatcher/adapter calls: 0
steps 中带 status 键的条目数: 0
```

把整个真实派发层砸烂，流水线毫发无损。`live-run` 与 `LiveAgentDispatcher` 之间**不存在任何调用关系**。

**佐证 1（自证循环）**：`live_runner.py:143-164` 由 runner 自己拼出三段写死 `vote: "YES_APPROVE"` 的 YAML 文本，再喂给 `ReviewExtractor.extract_and_validate()`（`:159`）。申请称此为「严格调用 ReviewExtractor 校验」——**校验的是它上一行刚写的字符串**。§9 模式 B 的教科书形态。

**佐证 2（死字段）**：`live_runner.py:36` 声明、`:73` 赋值的 `self.dispatcher`，全仓**无任何读取点**（`grep -rn "self\.dispatcher" src/` 仅两行，皆为写入）。§9 模式 A。

**佐证 3（零调用方）**：`grep -rn "dispatch_review_in_worktree" src/ tests/` → **仅 `live_dispatcher.py:144` 定义处本身**。本轮把它的 worktree API 接对了（P1-4 属实），但它依旧无人调用、无测试覆盖。

**闭环**：`live-run` 第 4/5 步必须真正经 `dispatch_review_in_worktree` 建隔离 worktree、拉起 Adapter、消费上下文；runner **禁止**自行写 `.review.yml`。若暂用 `mock-cli`，须先修 P2-R-4。

---

### P1-R-3　幻影批准仍可达：提取器"首个通过的块即返回"，且随即杀死会话

**先记录修好的部分**：我上轮 P1-NEW-13 的 5 个反例中 A/B/C/E 现已正确拒绝。这是真进步。

**仍未堵住的部分**——同一批测试新增的 10 个反例：

```
F. 裸 vote，无任何上下文（脏日志/历史残留）      -> is_valid=True  vote=YES_APPROVE
G. CLI 复述自己的提示词模板                      -> is_valid=True  vote=YES_APPROVE
H. 散文写明 "I REJECT this change"，
   日志尾部残留一个旧的 status: APPROVED 块       -> is_valid=True  vote=YES_APPROVE
I. 先 NO_APPROVE 后 YES_APPROVE（两块）           -> is_valid=True  vote=NO_APPROVE
J. 先 YES_APPROVE 后 NO_APPROVE（两块）           -> is_valid=True  vote=YES_APPROVE   ← 取错了
K. status: LGTM（随机串）                        -> is_valid=False  ✅
L. vote: " YES_APPROVE "（带空格）                -> is_valid=False  ✅
M. reviewer.id 不匹配                            -> is_valid=False  ✅
N. checkpoint_ref 写短 SHA                       -> is_valid=False
O. review_round: 1 且实际就是第 1 轮              -> is_valid=True
```

**机制**：`live_dispatcher.py:63` 按出现顺序遍历所有围栏块，`:118-120` 一旦某块 schema 通过就 `return True`。**先出现的块永远赢**。

**为什么这在真实 CLI 下是必然而非偶然**：`dispatch_review_in_worktree` 的轮询循环（`:230-243`）每 0.5 秒把整段日志重跑一遍提取，**一旦命中立即 `return`，并在 `finally` 里 `adapter.stop()` 杀掉会话**。LLM CLI 的典型输出形态恰恰是"先给一版草稿结论、再修正"。于是：**reviewer 早期的试探性 `YES_APPROVE` 会被抓走并当场掐断会话，它后面写的真实反对意见永远不会被读到。**

**闭环**：(1) 在 deadline 内取**最后一个**通过校验的块，而非第一个；(2) 或要求显式终止标记（如 `# MACAO-REVIEW-FINAL`）；(3) 命中后**不得**立即 `stop()` 会话；(4) 补 J/H 两个反例的单测。

---

### P1-R-4　强上下文绑定把真实反对票静默降级为弃权（本轮修复自身引入）

1. **reviewer 从来不被告知轮次**。`live_dispatcher.py:181-190` 构造的 `payload` 里有 `review_round`、`diff`、`review_context`，但逐个检查 7 个 adapter 的 `inject_task`——`opencode.py:96-100`、`claude.py:95`、`codex.py:84`、`cursor.py:97`、`antigravity.py:98`、`kimi.py:83`——**没有任何一个读取 `review_round` / `diff` / `review_context`**。注入的提示词只有 worktree 路径和 checkpoint_ref。
2. **提取器却对轮次逐字节强校验**（`:106`）：`parsed.get("review_round") is not None and != review_round` → `continue`。
3. **后果**（实测）：

```
round=2，CLI 写 review_round: 1 的真实 NO_APPROVE 反对票
  -> is_valid=False
  -> "Failed to extract schema-valid YAML review manifest with explicit vote/status"
```

派发方随后超时返回 `TIMEOUT / vote: ABSTAIN`（`:249`），daemon 再记一条 `REVIEWER_TIMEOUT_ABSTAIN`。**一张明确的反对票被无声转成弃权**，审计链上留下的是"该 reviewer 超时未响应"这一与事实相反的记录。

**附带**：`dispatch_review_in_worktree(..., diff_context="")` 是**死参数**——没有任何 adapter 会把 diff 递给 reviewer。真实 reviewer 在 worktree 里拿不到任何 diff 上下文，这使 P1-4 的"接线闭环"在 OPS 层面仍不成立。

**闭环**：(1) `inject_task` 必须把 `review_round`、`diff`、目标 schema 与合法 vote 枚举写进提示词；(2) 提取器**拒绝**任何候选时必须落 `REVIEW_MANIFEST_REJECTED` 审计事件（含原因与原文摘要），禁止静默 `continue`；(3)「超时」与「内容被拒」必须是两个可区分的审计事件。

---

### P1-R-5　三值投票协议在产物层只实现了两值：reviewer 无法弃权，只有系统能替他弃权

**取证**：

```
vote: ABSTAIN（合法弃权）              -> ok=False
status: ABSTAIN 无 vote                -> ok=False
vote: ABSTAIN + status: ABSTAIN        -> ok=False
```

根因是两份 schema 的词表不一致：

```
review_manifest.schema.json  vote enum -> ['YES_APPROVE', 'NO_APPROVE']            ← 无 ABSTAIN
vote_result.schema.json      vote enum -> ['YES_APPROVE', 'NO_APPROVE', 'ABSTAIN'] ← 有 ABSTAIN
core/types.py:33-37  class Vote        -> 三值，docstring 写 "Three-value voting outcomes (PRD §2.3)"
```

而系统代码处处把 ABSTAIN 当作一等票型：`live_dispatcher.py:94` 显式把 `vote in ("NO_APPROVE","ABSTAIN")` 归一化、`:249` 超时返回 `"vote": "ABSTAIN"`、`vote.py:133` 与 `orchestrator.py:580` 合成 ABSTAIN、`consensus/engine.py:38` 专门分支处理 ABSTAIN。

**后果（生产路径可达，与提取器是否接线无关）**：真实 reviewer 若在 `.macao/.reviews/*.review.yml` 里写 `vote: ABSTAIN`，`vote.py:39-41` 的 `collect_reviews` 校验失败后**静默 `continue`**，该 reviewer 被当成"没交"，最终由超时通道**替他**合成一张 ABSTAIN，并在审计里留下"超时"的假记录。即：**弃权这一票型，reviewer 表达不了，只有系统能替他行使。**

这直接违反 §5「必须维护唯一权威对照表 / 禁止用不同名词描述同一决策结果」，并使 §6 反例库中明文要求推演的 **「2-reviewer 全部弃权」场景在产物层根本无法表达** —— 而该场景是 L3 的既有验收项之一。

**说明**：此项**不是本轮引入的回归**（`3c5ed32` 及更早同样如此），但本轮 `23bb07f` 移除软兜底后，它从"被兜底掩盖"变成"直接拒稿"，首次成为可见的阻断路径，故本轮列为 P1。

**闭环**：把 `review_manifest.schema.json` 的 `vote` 枚举补为三值、`opinion.status` 增加 `ABSTAINED`（或明确规定弃权只经审计事件表达并**从 `types.py`/`engine.py` 中移除产物层 ABSTAIN 的假设**）；二选一，但两份 schema 与 `types.py` 必须收敛到同一张词表；补一条「reviewer 主动弃权」的端到端测试。

---

## 四、P2：应修正

### P2-R-1　`.gitignore` 升级路径完全失效（存量用户拿不到新规则）

`src/macao/cli/wizard.py:83` 的幂等守卫是 `if ".macao/worktrees/" not in content:`。任何用 `3c5ed32` 及更早版本向导初始化过的项目，`.gitignore` 里**已经**有这一行，于是本轮新增的 5 条规则一条都注不进去。

实测（模拟存量项目，`.gitignore` 只含旧的 3 行）：

```
changed: False
.macao/.reviews/             present=False
.macao/.dev.yml              present=False
.macao/vote_result.json      present=False
.macao/archive/              present=False
.macao/*.db-wal              present=False
```

`tests/test_phase3.py:132-140` 只覆盖"空 `.gitignore` → 注入"与"再调一次不重复"，**恰好绕开唯一会出问题的升级场景**（§9 模式 B）。后果：存量用户会把 `.macao/.dev.yml`、`.reviews/`、`vote_result.json`、`archive/` 提交进自己的仓库，违反 §7.1「不得污染真实项目仓库」。

**闭环**：逐条检查逐条追加（`for rule in RULES: if rule not in content: append`），补"旧 `.gitignore` 升级"单测。顺带修申请文字：实际 9 条不是 6 条。

### P2-R-2　`ui.py` 无条件绿色未真正修复，只是加了一个没人能走到的分支

`src/macao/cli/ui.py:136-138`：

```python
status_text = s.get("status", "OK")
status_style = "[green]OK[/green]" if status_text == "OK" else f"[red]{status_text}[/red]"
table.add_row(step_name, details, status_style)
```

但 `live_runner.py` 的 7 处 `steps_log.append(...)` **没有一处**写 `status` 键。实测 `sum(1 for s in res["steps"] if "status" in s) == 0`。红色分支永远不可达，每一行仍由构造决定是绿的。§9 模式 A。

**闭环**：让 runner 每步显式产出 `status`；补一条"某步失败时该行渲染为红"的测试。

### P2-R-3　README 徽章抢先宣告尚未授予的门禁

`README.md:7`：`![Gate Status](.../badge/status-L4%20RELEASE--READY-orange.svg)` —— 在**本次评审尚未做出结论时**，用户可见的首屏已写着 L4 RELEASE-READY。这与同仓 `STATUS.md`（"当前处于 Phase 3 整改复审收敛阶段"）直接矛盾，违反 §2.2「实时门禁状态统一维护于 STATUS.md」。这正是 §9 模式 C 在用户手册上的形态——而"用户手册齐备"恰是 L4 的组成条件之一。

同处 `README.md:5` 徽章仍写 `tests-72/72 PASS`，实际 75。

**闭环**：徽章改为 `L3 SCENARIO-VERIFIED / PG-2`（或去掉门禁徽章只链 STATUS.md），测试数同步。

### P2-R-4　`mock-cli` 已注册但无法构造，免额度自证路径不可用

`live_dispatcher.py:26-37` 的 `CLI_ADAPTER_REGISTRY` 在 `:36` 收录了 `mock-cli`，但：

```
注册表: ['claude-code','claude','codex','opencode','agy','antigravity','agent','cursor','kimi','mock-cli']
get_adapter_for_reviewer({'id':'m','cli':'mock-cli'})
  -> TypeError: MockAgentAdapter.__init__() missing 1 required positional argument: 'cli_name'
```

后果：P1-R-2 要求的「让 `live-run` 真正走 `dispatch_review_in_worktree`」目前**连一条不烧真实 CLI 额度的验证路径都没有**——唯一的 mock 通道在准入处就构造失败。这与 §7.2「不得使用真实 CLI 厂商账号额度进行破坏性测试」相冲突。

**闭环**：让 `get_adapter_for_reviewer` 对 `mock-cli` 补齐 `cli_name`，或统一 `MockAgentAdapter` 构造签名；并用它给 `dispatch_review_in_worktree` 补第一条端到端测试。

### P2-R-5（沿用自 `3c5ed32` 轮，本轮仍未修）　向导默认把 `2/3_majority` 悄悄改成全票

`wizard.py:132-133` 同时写出 `"consensus_rule": "2/3_majority"` 与 `"min_effective_votes": len(reviewers)`；`core/config.py:46` 的 `if configured_quorum is None or configured_quorum < derived_quorum:` 只在配置值**更小**时才用推导值，于是配置里那个更大的值胜出：

```
向导默认写出 (min_effective_votes=3)  -> min_effective_votes = 3   ← 实际要求全票
不写 min_effective_votes             -> min_effective_votes = 2   ← 3 名 reviewer 的 2/3 法定票数
```

即：**每个用 `macao setup` 生成的项目，配置里写着「2/3 多数」，实际执行的是「一票否决」**。一名 reviewer 掉线即无法达成法定票数，直接进 HOLD。§5 与 §9 模式 C。

**闭环**：向导不写 `min_effective_votes`（交给推导），或写成 `math.ceil(2*len(reviewers)/3)`；若确实想要全票，`consensus_rule` 必须同步改成 `unanimous`。

### P2-R-6　派发器读产物文件的 `except Exception: pass`

`live_dispatcher.py:225-226`：直接文件路径（`:208`）读取失败（YAML 损坏、编码错误、权限问题）被完全吞掉，轮询继续，最终以 `TIMEOUT / ABSTAIN` 收场。reviewer 明明写出了产物却因格式问题被当作"没响应"，与 P1-R-4、P1-R-5 是同一类"把失败伪装成沉默"的问题。

**闭环**：与 P1-R-4 合并处理——任何一次产物读取/解析失败都必须落审计事件，禁止静默。

### P2-CARRY-1（沿用，本轮仍未修）　ANSI 断言恒真

`src/macao/adapter/integ_harness.py:115`：

```python
ansi_stripped_ok = all(not bool(ANSI_ESCAPE_RE.search(line)) for line in clean_logs) if clean_logs else True
```

`clean_logs` 来自 `session.get_clean_logs()`，其内容在 `pty_session.py:89 / :96` 写入时**已经 `strip_ansi` 过**。该断言在任何输入下都为真，`test-clis` 报告里那整列 `ANSI Strip ✓ YES` 不承载信息。

该行当前形态定型于 **`3e1a991`**——而 `3e1a991` 的 commit message 正是「闭环 bf5ae2d 评审项（…**ANSI真实转义检测**…）」。即：宣称修复该项的那次提交，产出的就是这个恒真断言。自 `4df059e` 至今主干已推进 **31 个 commit**（`git rev-list --count 4df059e..HEAD`），横跨含本轮在内的多次评审申请，未变。

**闭环**：断言必须打在 `session.get_raw_logs()` 上，或注入一段含 `\x1b[31m` 的已知输出后验证 raw 有、clean 无。

---

## 五、P3：登记备查

| 编号 | 问题 | 证据 |
|---|---|---|
| **P3-R-1** | 「0 尾随空白 / 100% Clean」CONTRADICTED | `git show --check 15e8918` → rc=2（`docs/usecases/UC1-init-gemini.md:3,4,5`）；`git show --check 8871d00` → rc=2（`README.md:146`）。申请方沿用 `git diff --check`——该命令测的是**工作区**，提交后恒为空，与"本次提交是否干净"无关。**这与我上一轮犯的是同一个错**，故不作为对申请方的加重情节，但结论必须如实记为 CONTRADICTED。 |
| **P3-R-2** | `agmsg_member_id` / `team.name` 是纯声明，无行为 | 用 `3c5ed32` 的**旧** schema 校验一份带这两个字段的配置：**PASS**（executor/reviewers 均未设 `additionalProperties: false`）。故 `test_config.py` 在变更前后表现完全一致，该测试无法证明任何事。且 `grep -rn "agmsg_member_id" src/` 除 schema 外**零读取点**。 |
| **P3-R-3** | 申请文字与实机输出多处不符 | ①"7 步全绿" vs 实机渲染 9 行；②"6 项 gitignore 规则" vs 实际 9 条；③"6 款 CLI 及**通信组件**就绪" vs preflight 报告中无任何通信组件行；④"`live_dispatcher.py:215` 准入强校验" vs `ValueError` 实际在 `:140`（`:215` 处是 direct_file 分支内部）；⑤"流转（进入 HOLD）" vs 实际终态为 `CONSENSUS_CHECK`。 |
| **P3-R-4** | `live_dispatcher.py:134` `self.active_sessions` 仍是死字段 | `grep -rn "active_sessions" src/` 仅此一行。 |
| **P3-R-5** | `test_live_workflow_runner_end_to_end_cycle` 仍以日志条数为断言 | `tests/test_phase3.py:222` `assertEqual(len(res["steps"]), 7)` 断言的是 append 了几次，不是做成了什么；本轮新增的 `assertGreater(res["archived_count"], 0)` 是实质改进，但主断言未换。 |
| **P3-R-6** | 提取器把 `reviewer.cli` 改写成 `agent_id` | `live_dispatcher.py:113` `parsed["reviewer"] = {"id": agent_id, "cli": agent_id}` 无条件覆盖。实测输入 `{id: cursor-rev, cli: agent}` → 输出 `{id: cursor-rev, cli: cursor-rev}`，真实 CLI 名在产物中丢失，事后无法从 `.review.yml` 追溯该票由哪个 CLI 产生。 |
| **P3-R-7** | `STATUS.md:7` 的「当前申请对象」仍指向上一轮的 `2026-08-31-review-request-Phase3-PG3-L4.md`，而非本轮 `-Rectification.md`；STATUS 自身对账表已登记本轮，两处自相矛盾。 | `sed -n '7p' docs/reviews/STATUS.md` |
| **P3-R-8** | 单测污染 stdout | `python3 -m unittest discover tests` 输出中夹杂 `[main (root-commit) 89ba1f2] init` 等 git 回显，来自 runner/测试内 `subprocess.run(..., check=True)` 未捕获输出。建议统一 `capture_output=True`。 |

---

## 六、反向核验（我主动找"申请方没错"的证据，结果如实记录）

| # | 我怀疑的点 | 实测 | 结论 |
|---|---|---|---|
| R1 | 本轮是否动了已授予 L3/PG-2 的代码面？ | `src/` 仅 6 文件：`live_dispatcher/daemon/live_runner/ui/wizard` 均为 Phase 3 新增面；`vote.py` 与 `orchestrator.py` 的改动是**去掉软兜底**（更严），`orchestrator.__init__` 新增 config 为 None 时自动读 `macao.yaml`。75/75 全绿。 | **无回归，L3/PG-2 维持有效** |
| R2 | 去掉 vote 兜底会不会把合法票丢了？ | `review_manifest.schema.json` 的 `required` 含 `vote`，而 `vote.py:39` 的 `collect_reviews` 先做 Draft-07 校验再收。故 `if not vote_val: continue`（`vote.py:98`、`orchestrator.py:565`）是**不可达的防御性代码**，无副作用。 | **fail-closed 完好** |
| R3 | daemon 的超时降级会不会误伤（把有票的人算超时）？ | `detect_timed_out_reviewers`（`orchestrator.py:408-466`）用 `collect_reviews` 反查已提交集合再取差集，且限定 `WAITING_REVIEW/CONSENSUS_CHECK`、按 `review_round` 定向查审计。逻辑正确。 | **P1-2 修得扎实** |
| R4 | 死锁时会不会偷偷写 `vote_result.json` 放行？ | 沙箱复现：3 人全超时 → `DEADLOCK_DETECTED`，`vote_result.json exists: False`，终态停在 `CONSENSUS_CHECK`。 | **fail-closed 正确** |
| R5 | 合并闸门本身是不是假的？ | 拦掉伪造签字后 `execute_merge` 明确拒绝并给出正确指引；`controller.py:56-61` 还把签字与 `checkpoint_ref` 绑定。 | **闸门是真的**（这正是 P1-R-1 成立的前提） |
| R6 | 未知 CLI 准入是不是真的 fail-closed？ | `get_adapter_for_reviewer({"cli":"nope"})` → `ValueError: Unsupported or unconfigured reviewer CLI 'nope'`。默认值也从 `"opencode"` 改成 `""`，不再有隐式回退。 | **P1-4 代码层属实** |
| R7 | `require_signoff` 与 `require_human_signoff` 是否键名分裂（grok P2-5 的说法）？ | `orchestrator.py:123` 做了归一化搭桥；实测 `merge.require_human_signoff=True/False` → `config['require_signoff']=True/False` 两端联通。 | **不成立**，见 §九 9.2 |
| R8 | 我上轮提的 P3-NEW-17 是不是真修了？ | `docs/reference/REVIEW_METHODOLOGY.md:4-6` 三处尾随空白已清除。 | **已闭环** ✅ |

---

## 七、建议的闭环顺序与验收标准

| 序 | 项 | 验收标准（必须是**生产路径**上的可复现证据） |
|---|---|---|
| 1 | **P1-R-1** 伪造签字 | 拦掉 runner 的任何自动签字后，`live-run` 必须在合并前停下并提示 `macao merge approve`；非真人签署时 `note` 必须含 `NON-HUMAN` 且不得写 `signer`。附一次**真人执行 `macao merge approve` 的实机记录**（终端录屏或带时间戳的操作日志）作为 L4 的人工接管演练证据。 |
| 2 | **P1-R-2** dispatcher 零调用 | 把 `dispatch_review_in_worktree` 打成必抛异常后，`live-run` 必须 **FAIL**；`dispatcher_calls > 0`；runner 源码中不得存在自造 `.review.yml` 的分支。 |
| 3 | **P1-R-3** 首块即返回 | 反例 J（先 YES 后 NO）与 H（散文反对 + 残留 APPROVED 块）必须解析为 `NO_APPROVE` 或直接拒绝；命中后不得立即 `stop()` 会话。二者各补一条单测。 |
| 4 | **P1-R-4** 轮次绑定吞票 | `inject_task` 提示词中出现 `review_round` 与 diff；提取器每次拒绝都落 `REVIEW_MANIFEST_REJECTED` 审计；"超时"与"内容被拒"在审计上可区分。 |
| 5 | **P1-R-5** 三值票型收敛 | `review_manifest` / `vote_result` / `types.Vote` 三处词表一致；补一条「reviewer 主动弃权」端到端测试；§6 反例库「2-reviewer 全部弃权」可在产物层表达。 |
| 6 | **P2-R-1** gitignore 升级 | 用只含旧 3 行的 `.gitignore` 跑向导，9 条规则齐全；补该场景单测。 |
| 7 | **P2-R-2** UI 恒绿 | runner 每步产出 `status`；补一条"失败步骤渲染为红"的测试。 |
| 8 | **P2-R-3** README 徽章 | 徽章与 `STATUS.md` 一致；测试数同步为 75。 |
| 9 | **P2-R-4** mock-cli 构造 | `get_adapter_for_reviewer({'cli':'mock-cli'})` 不抛异常；并用它给 `dispatch_review_in_worktree` 补第一条端到端测试（建 worktree → 拉起 → 提取 → `finally` 清理）。 |
| 10 | **P2-R-5** 法定票数 | 向导产物的 `consensus_rule` 与 `min_effective_votes` 自洽：3 名 reviewer 下应为 2；补「向导产物法定票数 == ⌈2N/3⌉」单测。 |
| 11 | **P2-R-6 / P2-CARRY-1** | 产物读取失败落审计事件；ANSI 断言改打 raw 日志。 |
| 12 | **P3-R-1 / P3-R-7** | 提交前用 `git show --check <commit>` 自检 rc=0；`STATUS.md:7` 指向本轮申请文件。 |

**建议的下一轮申请目标**：先修 1–5（P1 清零）再申请 PG-3。若希望更快取得阶段性结论，可把 `live-run` 明确降格为 `demo-run` 并同步改文档，先行申请**除 OPS 之外的 L4 前置条件**确认。

---

## 八、给委员会的一句话摘要

> **不予授予 L4/PG-3，维持 L3/PG-2。** P1-2（daemon 超时降级）是本轮实打实修好的一项，P1-1/P1-4 也有真实进展；但申请用来证明 L4「人工接管实机演练」的 `macao live-run`，经反例注入证明**从不调用真实派发器**（打烂 dispatcher 后仍 `PASS/DONE`，调用数 0），且靠**伪造 `HUMAN_MERGE_APPROVED` 审计记录**（`signer: operator` / "Human operator verified consensus and approved merge"，全程无 tty）绕过合并闸门——拦掉这一条事件，闸门立即正确拒绝。L4 的 OPS 证据被证伪，另存续 P1-R-3（幻影批准仍可达）、P1-R-4（强轮次绑定把真实反对票静默转为弃权）、P1-R-5（reviewer 无法弃权，只有系统能替他弃权）。按 §8「P0/P1 对 PG-3 不可豁免」，本轮不可授予。

---

## 九、与同范围 `grok` / `glm` 报告的交叉核验（§8：真理不等于投票）

同一 HEAD 下另有 `2026-08-31-review-result-15e8918-grok.md` 与 `2026-08-31-review-result-15e8918-glm.md`。**三方结论一致**（不授予 L4/PG-3，维持 L3/PG-2），且三方各自独立复现了「P1-2 已闭环」「`live-run` 不调 dispatcher / 无真实 CLI」「自动签字」三项。按 §8「不以 reviewer 人数或身份代替证据」，我对其独有条目逐条自行取证：

### 9.1 采信并已并入本报告（他方提出、我原报告漏掉，经我独立复现）

| 来源 | 并入编号 | 我的独立取证 |
|---|---|---|
| grok P2-1 `mock-cli` 构造失败 | **P2-R-4** | `get_adapter_for_reviewer({'cli':'mock-cli'})` → `TypeError: missing 1 required positional argument: 'cli_name'` |
| grok P2-3 `min_effective_votes` 冲突 | **P2-R-5** | 向导默认 → 3；删掉该键 → 2。「2/3 多数」实际执行为全票 |
| grok P2-7 裸 `except` | **P2-R-6** | `live_dispatcher.py:225-226` |
| grok P3-2 `STATUS.md` 指针陈旧 | **P3-R-7** | `STATUS.md:7` 仍指上一轮申请文件 |
| glm P2-R3 ABSTAIN 语义 | **升级为 P1-R-5** | glm 判为 P2 且诊断为"status 被强写成 CHANGES_REQUESTED"；我复现后发现更深：`review_manifest` 的 `vote` 枚举**根本不含 ABSTAIN**，三种弃权写法全部 `ok=False`，与 `vote_result.schema.json` 和 `types.Vote` 的三值词表分裂。**病因不同，定级也应不同** |
| glm P3-R6 `reviewer.cli` 被改写 | **P3-R-6** | 输入 `{id: cursor-rev, cli: agent}` → 输出 `{id: cursor-rev, cli: cursor-rev}`（`live_dispatcher.py:113`） |

其中 **P2-R-5 本是我在 `3c5ed32` 轮提出、本轮漏携带**的条目——这是我这一轮的漏审，登记于此。

### 9.2 我不采信的

**grok P2-5「`require_signoff` 与 `require_human_signoff` 键名分裂，缺省 True 导致永远自动签字」—— 不成立。**

`live_runner.py:175` 读的是 `self.orchestrator.config`，即**归一化之后**的配置，而 `orchestrator.py:123` 恰好做了这层搭桥：

```python
"require_signoff": raw_config.get("require_signoff", merge_policy.get("require_human_signoff", True)),
```

实测两端联通：

```
merge.require_human_signoff=True   -> orchestrator.config['require_signoff'] = True
merge.require_human_signoff=False  -> orchestrator.config['require_signoff'] = False
```

键名没有分裂，开关也是可关的。这不影响 P1-R-1 成立（默认 True，且开关打开时 `live-run` 伪造签字**内容**），但**伪造的原因不是配置读不到**——把病因指错会导致修错地方，必须澄清。

### 9.3 我保留、他方未覆盖或判定不同

| 我的编号 | 他方判定 | 分歧点与我的证据 |
|---|---|---|
| **P1-R-3** 幻影批准仍可达 | grok / glm 均判 Extractor **VERIFIED** | 双方反例集与申请方单测同构——都只喂"整段都不是评审"的输入。我另构 10 例：`J`（先 `YES_APPROVE` 块后 `NO_APPROVE` 块 → 判 **YES**）、`H`（散文写明 "I REJECT this change" + 残留 `status: APPROVED` → 判 **APPROVED**）。机制是 `:63` 顺序遍历、`:118-120` 首块通过即 `return`，且轮询命中后立刻 `stop()` 会话。glm 的 P2-R4（"绑定仅在字段存在时生效"）触及了同一片区域但停在 P2，未测多块顺序。 |
| **P1-R-4** 强轮次绑定吞真实反对票 | 双方均未覆盖 | 7 个 adapter 的 `inject_task` 无一读取 `review_round`/`diff`/`review_context`；而 `:106` 对轮次逐字节强校验。第 2 轮 CLI 写 `review_round: 1` 的真实 `NO_APPROVE` → `is_valid=False` → 超时 → 记为 ABSTAIN。 |
| **P2-R-1** `.gitignore` 升级路径失效 | grok 判 **CODE VERIFIED**；glm 判 **VERIFIED (CODE+TEST)** | 二者与申请方一样只测**全新** `.gitignore`。对存量项目（`.gitignore` 已含 `.macao/worktrees/`，即任何用 `3c5ed32` 及更早向导初始化过的项目）实测 `changed: False`，5 条新规则一条都没进去。幂等守卫 `wizard.py:83` 短路了整个追加。 |
| **P3-R-2** schema 变更是纯声明 | grok 判 **CODE VERIFIED**；glm 判 **VERIFIED (DOC)** | 字段确实存在，但用 `3c5ed32` 的**旧** schema 校验带这两个字段的配置同样 **PASS**（未设 `additionalProperties: false`）。故 `test_config.py` 变更前后表现完全一致，不能作为闭环证据；且 `src/` 中零读取点。 |

### 9.4 结论不受影响

三份报告在**否决理由**上完全重合（`live-run` 合成协同 + 伪造人工签字 ⇒ L4 的 OPS 证据被证伪）。上述增减改变的是 P1/P2/P3 清单与部分病因归属，**不改变门禁判定**。

---

## 附录：本轮复现命令

```bash
# 全量测试与洁净度
PYTHONPATH=src python3 -m unittest discover tests           # Ran 75 tests ... OK
python3 -m compileall -q src tests; echo $?                 # 0
for c in $(git rev-list 3c5ed32..HEAD); do
  git show --check "$c" >/dev/null 2>&1; rc=$?              # 注意：rc 必须先落变量再打印
  printf "%s rc=%s\n" "$(git log -1 --format=%h "$c")" "$rc"
done                                                        # 15e8918 rc=2 ; 8871d00 rc=2 ; 其余 0

# 实机
PYTHONPATH=src python3 -m macao.cli.main live-run           # 9 行，5/5 PERSISTED，DONE
PYTHONPATH=src python3 -m macao.cli.main preflight          # 全 OK；无通信组件行
PYTHONPATH=src python3 -m macao.cli.main test-clis          # 4/4 PASS，0 Zombie
PYTHONPATH=src python3 -m macao.cli.main daemon --once      # active_task=None（仓库根无活跃任务）

# P1-R-1：伪造签字 + 闸门反向验证
#   patch StateStore.log_audit_event 拦截 HUMAN_MERGE_APPROVED 后跑 run_live_cycle()
#   -> RuntimeError: execute_merge failed: Human signoff required for checkpoint ...

# P1-R-2：反例注入
#   LiveAgentDispatcher.dispatch_review_in_worktree / get_adapter_for_reviewer := raise
#   -> PASS / DONE / archived=5 / duration=0.35 / calls=0

# P1-R-3：15 个反例喂 ReviewExtractor.extract_and_validate（J/H 仍产出 YES_APPROVE）
# P1-R-4：round=2 上下文喂 review_round: 1 的 NO_APPROVE -> is_valid=False
# P1-R-5：vote: ABSTAIN / status: ABSTAIN 三种写法 -> 全部 ok=False
#         review_manifest vote enum = ['YES_APPROVE','NO_APPROVE']
#         vote_result    vote enum = ['YES_APPROVE','NO_APPROVE','ABSTAIN']
# P2-R-1：只含旧 3 行的 .gitignore 跑 ensure_gitignore_isolation -> changed: False
# P2-R-5：向导默认 min_effective_votes=3；删除该键 -> 2

# 可达性
grep -rn "dispatch_review_in_worktree" src/ tests/     # 仅 live_dispatcher.py:144 定义处
grep -rn "self\.dispatcher"            src/            # 仅 live_runner.py:36,73（皆写入）
grep -rn "active_sessions"             src/            # 仅 live_dispatcher.py:134
grep -rn "agmsg_member_id"             src/            # 仅 schema
```
