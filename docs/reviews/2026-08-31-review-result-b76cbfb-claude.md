# MACAO Phase 3（PG-3 / L4 RELEASE-READY）终审验收评审结论

- **评审日期**：2026-08-31
- **评审对象**：`15e8918` .. `b76cbfb`（功能闭环主体 `ac32dbb`；完整范围 `3c5ed32`..`b76cbfb`）
- **申请文件**：`docs/reviews/2026-08-31-review-request-Phase3-PG3-L4-Final.md`
- **评审基准**：`docs/MACAO_REVIEW_GUIDELINES.md`（v1.0）；上位基准 `docs/MACAO_PRD_v2.md`
- **reviewer**：`claude`
- **申请目标**：L4 RELEASE-READY / PG-3
- **证据类型**：DOC / SPEC / CODE / SIM / TEST / OPS，全部本机复现，不采信申请粘贴输出

---

## 结论

> ### 不予授予 L4 RELEASE-READY / PG-3；维持 L3 SCENARIO-VERIFIED / PG-2
> ### 但本轮是迄今质量最高的一次整改：我上轮提的 **11 项中已闭环 10 项**，且是**真闭环**，不是措辞闭环。

**唯一实质阻断**：L4 的 OPS 判据仍未满足——**全系统至今没有任何一次真实 CLI 进程完成过一轮评审闭环**。`live-run` 现在确实走真 worktree 派发了（这是真进步），但实测 `PTYSession.start` 调用次数为 **0**，三张赞成票由 `MockAgentAdapter` 内置产出（`mock.py:74` `vote_val = cfg_dict.get("mock_vote", "YES_APPROVE")`）。同时，申请用来证明「人工接管实机演练」的 `test_manual_override_resolution` 在三处绕开了生产路径。

**但必须同时说明**：我**亲自用真实 CLI 命令把人工接管链路完整跑通了**（见 §六 R1）——`daemon --once`（真实超时检测）→ `DEADLOCK` HOLD 于 `CONSENSUS_CHECK` → `macao override resolve` → `macao merge approve`，全部 rc=0。**功能是存在且用户可见的，缺的是"用真实 CLI 演练一次并留档"，不是缺功能。** 因此本轮阻断项只剩 1 项，且闭环成本很低（§七给出最小可执行方案）。

指引 §2.1：L4 = L3 + 人工接管路径**实机**演练 + 回归无 P0/P1 + 用户手册齐备；§3.3：L4 要求 **OPS 为 VERIFIED**。§8：P0/P1 对 PG-3 不可豁免。

**L3/PG-2 无回归**（81/81 PASS），继续有效。

---

## 〇、Reviewer 自审记录（前置）

1. **本轮我改变了两处自己上轮的判定**，如实登记：
   - 上轮 **P3-R-1（洁净度 CONTRADICTED）**：申请方本轮用的是 `git diff --check 3c5ed32..HEAD`（**累积差异**口径），我实测 **rc=0**，`README.md:146` 与 `UC1-init-gemini.md:3-5` 的尾随空白确已清除。**按申请方声明的口径，该项成立，我撤回上轮的 CONTRADICTED**。（逐 commit 口径下 `15e8918`/`8871d00` 仍为 rc=2，但那是已成历史的中间态，不构成发布阻断。）
   - 上轮 **P1-R-3（幻影批准，P1）**：决定性反例 J（先 YES 后 NO）已被"末块优先"修正，矛盾票已 fail-closed。**我把它降级为 P2**（残余的 F/G/H 三例仍在，见 P2-F-3）。
2. **我上轮的漏审在本轮补上了**：上轮我漏携带 `min_effective_votes` 一项（我自己在 `3c5ed32` 轮提出过），经 grok 提醒补入——本轮已确认闭环。
3. **本轮的取证方式**：对每一条"已闭环"声明，我都先跑**能证伪它**的反例，而不是跑能证实它的用例。例如 P1-R-2 我不是去数调用次数，而是把 dispatcher 打成必抛异常看流水线会不会失败（会）；人工接管我不是去读测试，而是自己敲 CLI 命令走一遍（走通了）。
4. **本轮激活的自审项**：§9 A 命中 1 处（worktree 双重创建）；§9 B 命中 2 处（单测绕开生产路径、README 徽章数字）。

---

## 一、对账：申请方 9 项闭环声明的独立核验

| 申请编号 | 声明 | 我的独立取证 | 状态 |
|---|---|---|---|
| **P1-R-1** live-run 真实派发 + 诚实签字 | 真调 dispatcher；`signer: "system-runner"` | **两项均属实**。`live_runner.py:141` 真实调用 `dispatch_review_in_worktree`；`:174-177` 签字改为 `signer: "system-runner"` / `note: "Automated runner signoff (--auto-signoff)"`，虚假人类声明已删除；`--no-auto-signoff` 走 `WAITING_SIGNOFF` 真实等待分支（`:182`）。**残余**：`main.py:402` 默认 `--auto-signoff`，且闸门不区分签署者（P2-F-2）。 | **VERIFIED** ✅ |
| **P1-R-2 / P2-1** Mock 契约与工厂接线 | `cli_name` 默认值；工厂正确构造 | `MockAgentAdapter.__init__(cli_name="mock-cli")`；`get_adapter_for_reviewer({'cli':'mock-cli'})` 不再抛 `TypeError`。 | **VERIFIED** ✅ |
| **P1-R-3 / P1-R-4** 末块优先 + 矛盾拒绝 + 提示词补全 | 取最后有效块；矛盾 fail-closed；注入 round/diff | `live_dispatcher.py:160` `return True, valid_candidates[-1], None`；`:89-101` 六条矛盾互斥判定。实测反例 I/J 均取到**正确的最后一块**；`vote NO + status APPROVED`、`vote YES + status REJECTED` 均 `ok=False`。**6 个 adapter 全部**注入 `review_round`、`diff` 与合法 vote 枚举（`opencode.py:97-105` 等）。**但引入了新的 fail-open**（P2-F-1）。 | **VERIFIED**（含新回归） |
| **P1-R-5** 三值投票 Schema | `ABSTAIN`/`ABSTAINED` 闭环 | 三种写法实测**全部 `ok=True`**：`vote: ABSTAIN`、`vote+status`、`status: ABSTAINED` 单独 → 均归一化为 `vote=ABSTAIN / status=ABSTAINED`。`review_manifest.schema.json` 与 `types.py` 已同步三值。 | **VERIFIED** ✅ |
| **P2-R-1** gitignore 存量升级 | 逐条差量扫描 | 存量 `.gitignore`（只含旧 3 行）实测 `changed: True`，6 条新规则**全部注入**，再调一次 `changed: False`（幂等）。 | **VERIFIED** ✅ |
| **P2-R-5** 法定票数算术 | `ceil(2N/3)` | N=2→2、3→2、4→3、5→4，与 `⌈2N/3⌉` 逐个吻合，`consensus_rule` 保持 `2/3_majority`。 | **VERIFIED** ✅ |
| **P1-5 (Qwen)** setup 覆盖防护 | 自动备份 | `main.py:360-364` 覆写前 `shutil.copy` 到 `macao.yaml.bak.<ts>`，并加了 `--force`。 | **VERIFIED** ✅ |
| **P1-6 / P2-4 / P2-6** 手册与洁净度 | FAQ 修正、徽章对齐、空白清除 | 徽章门禁已改为 `L3 SCENARIO-VERIFIED / PG-2` ✅；`git diff --check 3c5ed32..HEAD` **rc=0** ✅。**但**测试徽章仍写 `tests-75/75`，实测 **81**，与申请自述的「对齐为 81/81 PASS」不符（P3-F-1）。 | **PARTIALLY_VERIFIED** |
| **OPS 人工接管实机演练** | `test_manual_override_resolution` 100% PASS | 该测试确实通过，DEADLOCK→`resolve_override`→MERGING 逻辑正确。**但它是 TEST 不是 OPS**，且三处绕开生产路径（见 P1-F-1）。 | **CONTRADICTED（作为 OPS 证据）** ❌ |

## 二、对账：申请「二、实机验证与测试指标」6 行

| # | 声明 | 实测 | 状态 |
|---|---|---|---|
| 1 | 81 项单测全通过 | `Ran 81 tests in 20.533s / OK` | **VERIFIED** ✅ |
| 2 | `compileall` + `git diff --check 3c5ed32..HEAD` 双 0 | `compileall` rc=0；`git diff --check 3c5ed32..HEAD` **rc=0** | **VERIFIED** ✅ |
| 3 | 真实 Worktree 隔离派发，7 步全闭环，5 份 PERSISTED | Worktree 隔离派发**属实**（3 个 worktree 真实创建、派发后 `git worktree list` 仅剩主仓）；归档 5/5 PERSISTED、DONE 属实。**但**实机渲染仍是 **9 行**不是 7 步；且"真实"仅限 worktree，**零 CLI 进程**（P1-F-1） | 派发 VERIFIED；**"真实协同" CONTRADICTED** |
| 4 | `daemon --once` 正常扫描退出 | 属实；我另在真实 `WAITING_REVIEW` + 真实超时上复测，正确降级 | **VERIFIED** ✅ |
| 5 | preflight「6 款 CLI 及**通信组件**就绪」 | 7 行 CLI + 2 行环境全 OK；**报告中仍无任何通信组件/agmsg 行** | **PARTIALLY_VERIFIED** |
| 6 | test-clis PASS，0 僵尸 | 4/4 PASS，0 Zombie 属实 | **VERIFIED**（ANSI 列仍恒真，P2-CARRY-1） |

---

## 三、P1：授予 PG-3 前必须解决（仅剩 1 项）

### P1-F-1　L4 的 OPS 判据仍未满足：零次真实 CLI 评审闭环 + 人工接管证据绕开生产路径

#### (a) `live-run` 里没有任何 CLI 进程被拉起

我在派发链路上打桩（spy `create_isolated_worktree` / `get_adapter_for_reviewer` / `PTYSession.start`）后跑 `run_live_cycle()`：

```
status: PASS | final: DONE | duration: 0.46

-- 派发时真实创建的 worktree --
   .../worktrees/opencode-rev/task-.../r1   created_ok= True
   .../worktrees/agy-rev/task-.../r1        created_ok= True
   .../worktrees/cursor-rev/task-.../r1     created_ok= True   （每个各出现两次，见 P2-F-4）

-- 实际构造的 adapter --
   ('opencode-rev', 'mock-cli', 'MockAgentAdapter')
   ('agy-rev',      'mock-cli', 'MockAgentAdapter')
   ('cursor-rev',   'mock-cli', 'MockAgentAdapter')

-- PTYSession.start 被调用次数 -- 0

-- 派发结束后 worktree 是否清理 -- 全部 still_exists= False
-- git worktree list -- 仅主仓

-- 收集到的评审产物 --
   agy-rev.review.yml:      vote=YES_APPROVE status=APPROVED summary=Mock reviewer validated code changes.
   cursor-rev.review.yml:   vote=YES_APPROVE status=APPROVED summary=Mock reviewer validated code changes.
   opencode-rev.review.yml: vote=YES_APPROVE status=APPROVED summary=Mock reviewer validated code changes.
```

**结构上是真的，内容上仍是 MACAO 自己写的赞成票**。上一轮赞成票由 `live_runner` 内嵌字符串产出，这一轮改由 `mock.py:70-100` 的 `inject_task` 无 `behavior_fn` 分支产出，默认 `vote_val = cfg_dict.get("mock_vote", "YES_APPROVE")`（`mock.py:74`）。**批准的制造者从 runner 搬到了 adapter，但仍然是 MACAO 自己。**

`setup_sandbox_repo` 里三名 reviewer 的 `cli` 已从 `opencode`/`agy`/`agent` 全部改成 `mock-cli`。这在工程上是正确的选择（不烧真实额度、CI 可跑），我不反对；**我反对的是把它当作 L4 的 OPS 证据**。指引 §3.1 定义 OPS 为「PTY 进程管理、并发、崩溃恢复、agmsg 队列演练」，§3.3 要求 L4 的 OPS 为 VERIFIED。一次 0 个 PTY、0 个真实 CLI、0.46 秒的闭环是 **SIM**，不是 OPS。

而 MACAO 的产品定义就是"编排真实 AI CLI"。**在从未有任何一款真实 CLI 完成过一轮评审的情况下授予 RELEASE-READY，等于用 mock 证据为头号能力背书。**

#### (b) 人工接管的证据是绕开生产路径的单测

`tests/test_phase3.py:356` `test_manual_override_resolution` 逻辑正确、断言到位，但作为 **L4 OPS 演练**证据有三处绕行：

1. **绕开超时检测**：`:410` 直接 `timed_out_reviewers=["agy-rev"]` 显式传参，没有走 `detect_timed_out_reviewers` 的真实判定；
2. **绕开用户可见路径**：直接调 `orch.resolve_override(...)`（`orchestrator.py:740`）与 `store.log_audit_event(...HUMAN_MERGE_APPROVED...)`，**全程不经 `macao override resolve` / `macao merge approve` 两条 CLI**。§3.3 要求的是"**用户可见的**人工接管演练"；
3. **用了生产加载器会拒绝的配置**：`:369` `cfg["project"]["repository"]["remote_name"] = ""`，直接以 `config=` 传入绕过 schema 校验。我照抄这份配置走 CLI 时，得到
   `ValueError: Invalid macao.yaml schema: Validation failed at 'project.repository.remote_name': '' is too short`。
   即：**该测试所验证的那个配置形态，生产入口根本加载不了。**

这正是我在方法论提案里写的那条——「测试不得以显式传参绕开生产路径」。

#### 闭环要求（成本很低，见 §七）

一次以 **`mock-cli` 之外的真实 CLI**（`test-clis` 已证明 claude/codex/opencode/agy 四款可正常 PTY 启停）完成的评审闭环，**外加**一次经 `macao override resolve` + `macao merge approve` 的用户可见接管演练留档。**我已经替你们跑通了后半段**（§六 R1），前半段是唯一剩下的工作。

---

## 四、P2：应修正

### P2-F-1（本轮新引入的 fail-open）　`checkpoint_ref` 退化为双向前缀匹配，1 个字符即可通过

为修我上轮的反例 N（短 SHA 被拒），`live_dispatcher.py:136` 改成了：

```python
if ref_str != checkpoint_ref and not checkpoint_ref.startswith(ref_str) and not ref_str.startswith(checkpoint_ref):
    continue
```

**没有最小长度约束**。实测（派发上下文 `checkpoint_ref = 365185eb24650b7a...`）：

```
checkpoint_ref='365185eb24650b7a1c2d3e4f5a6b7c8d9e0f1a2b'  -> accepted=True   （应通过）
checkpoint_ref='365185eb'                                  -> accepted=True   （合理，git 短 SHA）
checkpoint_ref='3'                                         -> accepted=True   ← 单个字符
checkpoint_ref='36'                                        -> accepted=True   ← 两个字符
checkpoint_ref='3f2a'                                      -> accepted=False  ✅
checkpoint_ref='deadbeef'                                  -> accepted=False  ✅
```

任何 1 字符前缀有 1/16 概率命中任意 commit。命中后 `:144` 会把它**静默改写成完整的派发 ref**，产物上再也看不出原始值。方向是对的（应当支持短 SHA），但边界开得过大。

**闭环**：要求 `len(ref_str) >= 7`（git 默认 abbrev）且必须是 `checkpoint_ref` 的前缀（单向），拒绝反向包含；补 `'3'` / `'36'` 两条反例单测。

### P2-F-2　诚实的标签没有改变闸门行为：机器签名仍能满足"Human signoff required"

`live_runner.py:174-177` 现在诚实写 `signer: "system-runner"`，这是实质进步。但 `merge/controller.py:49-61` 的闸门**只校验 `checkpoint_ref` 是否匹配，不校验签署者**——一条 `signer: "system-runner"` 的记录照样能通过一道错误信息写着 `Human signoff required for checkpoint ...` 的闸门。

同时 `main.py:402` `--auto-signoff/--no-auto-signoff` **默认 True**，因此 `macao live-run` 的默认行为仍是自签自批。

**闭环**：(1) `controller.py` 增加签署者白名单/黑名单，或在 `require_signoff=True` 时拒绝 `signer` 属于自动化角色的记录；(2) `live-run` 的默认值改为 `--no-auto-signoff`，让默认路径就是"停在等签字"；(3) 或把闸门的错误文案与语义从"Human"改为"Approver"，使名实相符。三选一，但**名与实必须一致**（§5）。

### P2-F-3　幻影批准残余：单块场景下仍可从非评审文本产出赞成

"末块优先"解决了多块顺序问题，但单块场景未变。实测仍被接受：

```
F. 裸 vote，无任何上下文（脏日志/历史残留）        -> is_valid=True  vote=YES_APPROVE
G. CLI 复述自己的提示词模板                       -> is_valid=True  vote=YES_APPROVE
H. 散文写明 "I REJECT this change"，
   日志尾部残留一个 status: APPROVED 块            -> is_valid=True  vote=YES_APPROVE
```

考虑到 (a) 决定性的 J 已修、(b) 矛盾票已 fail-closed、(c) 现在提示词明确要求 CLI 输出完整清单，残余风险显著下降，故**由上轮的 P1 降为 P2**。

**闭环**：要求候选块至少同时含 `reviewer` 与 `vote`/`status` 两类字段（而非仅一个 `vote:` 键）才视为评审清单；或引入显式终止标记。

### P2-F-4　Worktree 双重创建：dispatcher 静默销毁了 orchestrator 的事务性 worktree

`orchestrator.py:331-333` 在 `dispatch_review_requests` 里已经为每位 reviewer 建好隔离 worktree，注释明写 `FAIL-CLOSED & TRANSACTIONAL`。随后 `live_dispatcher.py:213` 又为同一 `(agent_id, task_id, round)` 建一次；而 `git_utils.py:107-109`：

```python
# Remove existing if any
if worktree_dir.exists():
    self.remove_worktree(worktree_dir)
```

**第二次创建会先把第一次的删掉再重建**。派发结束后 `live_dispatcher.py:302` 的 `finally` 再删一次——于是 orchestrator 认为自己事务性创建且从未移除的那批 worktree，实际已经不存在了。实测同一路径在打桩里出现 **6 次创建（3 名 reviewer × 2）**，终态 0 个存活。

两个所有者共管同一生命周期，orchestrator 的 fail-closed 保证被静默作废。

**闭环**：明确单一所有者——要么 dispatcher 复用 orchestrator 已建的 worktree（存在即跳过创建、且不负责删除），要么 orchestrator 不再预建。补一条"派发全程 worktree 只被创建一次"的测试。

### P2-CARRY-1（沿用，仍未修）　ANSI 断言恒真

`src/macao/adapter/integ_harness.py:115` 未变：

```python
ansi_stripped_ok = all(not bool(ANSI_ESCAPE_RE.search(line)) for line in clean_logs) if clean_logs else True
```

`clean_logs` 在 `pty_session.py:89 / :96` 写入时已 `strip_ansi` 过，该断言恒真，`test-clis` 报告里整列 `ANSI Strip ✓ YES` 不承载信息。该形态定型于 `3e1a991`——正是宣称闭环「ANSI真实转义检测」的那次提交。自 `4df059e` 起主干已推进 33 个 commit。

**闭环**：断言改打 `session.get_raw_logs()`，或注入含 `\x1b[31m` 的已知输出后验证 raw 有、clean 无。

---

## 五、P3：登记备查

| 编号 | 问题 | 证据 |
|---|---|---|
| **P3-F-1** | README 测试徽章仍是 `tests-75/75 PASS`，实测 **81**；申请表格却自述「徽章对齐为 …`81/81 PASS`」 | `grep -o "tests-[0-9]*%2F[0-9]*" README.md` → `tests-75%2F75` |
| **P3-F-2** | 申请文字与实机输出不符 | ①"7 步全绿" vs 实机渲染 9 行；②"6 款 CLI 及**通信组件**就绪" vs preflight 无通信组件行 |
| **P3-F-3** | `active_sessions`（`live_dispatcher.py:171`）仍是死字段 | `grep -rn "active_sessions" src/` 仅此一行（`:171`） |
| **P3-F-4** | `agmsg_member_id` / `team.name` 仍无任何读取点 | `grep -rn "agmsg_member_id" src/` 除 schema 外零命中 |
| **P3-F-5** | `test_live_workflow_runner_end_to_end_cycle` 仍以日志条数作主断言 | `assertEqual(len(res["steps"]), 7)` |
| **P3-F-6** | 单测污染 stdout（git 回显未捕获） | `unittest discover` 输出夹杂 `[main (root-commit) ...]` |

---

## 六、反向核验（我主动找"申请方没错"的证据，结果如实记录）

| # | 我怀疑的点 | 实测 | 结论 |
|---|---|---|---|
| **R1** | **人工接管到底能不能用真实 CLI 走通？**（申请只给了单测） | 我自建沙箱，用 **1 赞成 + 1 反对 + 1 不交**、`per_reviewer: 0s`，**不显式传 `timed_out_reviewers`**，全程只敲 CLI：<br>`daemon --once` → rc=0，FSM 进 `CONSENSUS_CHECK`，审计留下 `REVIEWER_TIMEOUT_ABSTAIN` + `DEADLOCK_DETECTED(reason=TIMEOUT_ESCALATION)`；<br>`macao status` → 操作员看到 `FSM State: CONSENSUS_CHECK`；<br>`macao override resolve --choice APPROVED` → rc=0，`✓ Override resolved successfully: CONSENSUS_CHECK -> MERGING`；<br>`macao merge approve --note "signed by operator"` → rc=0，`✓ Merge signoff recorded`。 | **人工接管链路功能完好、用户可见、审计留痕完整**。这是申请方**本可以直接拿来当 OPS 证据**却没有用的东西 |
| R2 | 反例注入：dispatcher 现在真被调用了吗？ | 把 `dispatch_review_in_worktree` 打成必抛异常 → `run_live_cycle()` **直接抛 `RuntimeError` 失败**（上轮此处仍 `PASS`） | **P1-R-2 真闭环** ✅ |
| R3 | worktree 是真建真删，还是只是路径字符串？ | 3 个 worktree 真实创建（`created_ok=True`），派发后 `git worktree list` 仅剩主仓，无残留 | **真实隔离成立** ✅ |
| R4 | 末块优先会不会把顺序取反了？ | I（先 NO 后 YES）→ 取 YES；J（先 YES 后 NO）→ 取 NO。两例都取到了**时间上最后**的那块 | **语义正确** ✅ |
| R5 | 三值票型是真闭环还是只改了 schema？ | `vote: ABSTAIN` 单独、`vote+status` 组合、`status: ABSTAINED` 单独，三种写法全部 `ok=True` 并归一化为 `ABSTAIN/ABSTAINED` | **真闭环** ✅ |
| R6 | 洁净度是不是又用错了口径？ | 申请方口径 `git diff --check 3c5ed32..HEAD` 实测 **rc=0**；`README.md:146` 与 `UC1-init-gemini.md:3-5` 确已清除 | **成立，撤回我上轮的 CONTRADICTED** ✅ |
| R7 | 81/81 是不是掺了水（新增测试是否只测好路径）？ | 新增 6 条含 `test_review_extractor_last_valid_block_wins`、`test_review_extractor_rejects_contradictory_vote_and_status`、`test_wizard_gitignore_isolation_upgrade`、`test_live_dispatcher_worktree_mock_execution`、`test_manual_override_resolution` ——**都是失败路径/反例方向的测试**，方向正确 | **新增测试质量良好** ✅ |
| R8 | L3/PG-2 有无回归？ | 81/81 全绿；`src/` 改动集中在 Phase 3 面与 6 个 adapter 的提示词；`git_utils` 仅新增 `get_diff` | **无回归** ✅ |

---

## 七、建议的闭环顺序与验收标准

| 序 | 项 | 验收标准 |
|---|---|---|
| **1** | **P1-F-1（唯一阻断）** | **(a)** 用 `test-clis` 已验证可用的四款真实 CLI 之一（claude / codex / opencode / agy），让**至少 1 名 reviewer** 经 `dispatch_review_in_worktree` 在隔离 worktree 里完成一次真实评审，产出可校验的 `.review.yml`；留档：命令、`PTYSession.start` 计数 > 0、终端日志、产物 sha256。<br>**(b)** 一次经 **`macao override resolve` + `macao merge approve` 两条 CLI** 的人工接管演练（僵局由真实超时检测触发，不得显式传 `timed_out_reviewers`），留档审计事件序列。<br>**§六 R1 的输出可直接作为 (b) 的模板**——把它换成真人操作并录屏/留日志即可。 |
| 2 | P2-F-1 | `checkpoint_ref` 前缀匹配加 `len >= 7` 且改为单向；补 `'3'`/`'36'` 反例单测 |
| 3 | P2-F-2 | 闸门区分签署者，或 `live-run` 默认改为 `--no-auto-signoff`，或统一改名为 "Approver signoff"；名实必须一致 |
| 4 | P2-F-4 | worktree 生命周期收敛到单一所有者；补"全程只创建一次"的测试 |
| 5 | P2-F-3 | 候选块须同时含 `reviewer` 与票型字段方视为评审清单 |
| 6 | P2-CARRY-1 | ANSI 断言改打 raw 日志 |
| 7 | P3-F-1/F-2 | README 徽章改 81/81；申请文字与实机输出对齐（9 行 / 无通信组件行） |

**给委员会的定级建议**：本轮已把 4 份专家报告的绝大多数阻断项做成了**可验证的物理闭环**，质量与诚实度都明显提升。**建议下一轮只针对 P1-F-1 的两份演练留档做定向复审**，若 (a)(b) 成立，我这一侧不再有授予 L4/PG-3 的阻碍。

---

## 八、给委员会的一句话摘要

> **不予授予 L4/PG-3，维持 L3/PG-2——但只差最后一步。** 我上轮 11 项已闭环 10 项且是真闭环：dispatcher 反例注入现在会让 `live-run` 失败（上轮仍 PASS）、末块优先与矛盾票 fail-closed 已生效、三值弃权已打通、gitignore 存量升级与 `⌈2N/3⌉` 法定票数均已修正、伪造的人类签字已换成诚实的 `signer: "system-runner"`、洁净度按申请方口径实测 rc=0（我撤回上轮该项判定）。**唯一剩下的阻断是 L4 的 OPS 判据**：`live-run` 中 `PTYSession.start` 计数为 **0**，三张赞成票由 `MockAgentAdapter` 内置产出，全系统至今没有任何一款真实 CLI 完成过一轮评审；而人工接管的证据是一条在三处绕开生产路径的单测。**但我已亲自用 `daemon --once` → `macao override resolve` → `macao merge approve` 把人工接管链路完整跑通（全部 rc=0，审计留痕完整）——功能是有的，缺的只是"用真实 CLI 演练一次并留档"。**

---

## 附录：本轮复现命令

```bash
# 全量测试与洁净度
PYTHONPATH=src python3 -m unittest discover tests           # Ran 81 tests ... OK
python3 -m compileall -q src tests; echo $?                 # 0
git diff --check 3c5ed32..HEAD; echo $?                     # 0  （申请方口径，成立）

# 实机
PYTHONPATH=src python3 -m macao.cli.main live-run           # 9 行，5/5 PERSISTED，DONE
PYTHONPATH=src python3 -m macao.cli.main test-clis          # 4/4 PASS，0 Zombie
PYTHONPATH=src python3 -m macao.cli.main preflight          # 全 OK；无通信组件行

# P1-F-1(a)：派发链路打桩（spy create_isolated_worktree / get_adapter_for_reviewer / PTYSession.start）
#   -> worktree 真建真删；adapter 全为 MockAgentAdapter；PTYSession.start = 0

# P1-F-1(b) 与 §六 R1：真实 CLI 人工接管演练（1 赞成 + 1 反对 + 1 超时，不显式传 timed_out_reviewers）
#   macao daemon --once            -> rc=0, FSM=CONSENSUS_CHECK, REVIEWER_TIMEOUT_ABSTAIN + DEADLOCK_DETECTED
#   macao status                   -> FSM State: CONSENSUS_CHECK
#   macao override resolve --choice APPROVED   -> rc=0, CONSENSUS_CHECK -> MERGING
#   macao merge approve --note "signed by operator" -> rc=0

# R2 反例注入
#   LiveAgentDispatcher.dispatch_review_in_worktree := raise
#   -> run_live_cycle() 抛 RuntimeError（上轮此处返回 PASS）

# P2-F-1 前缀匹配边界
#   checkpoint_ref='3' / '36' -> accepted=True    ← fail-open
#   checkpoint_ref='3f2a' / 'deadbeef' -> accepted=False

# P1-R-3/R-5 提取器
#   I(先NO后YES)->YES ; J(先YES后NO)->NO ; 矛盾票 ->False ; ABSTAIN 三种写法 ->True
#   F/G/H 单块幻影批准 ->仍 True（P2-F-3）

# P2-R-1 / P2-R-5
#   存量 .gitignore -> changed:True，6 条全注入，再调 False
#   reviewers=2/3/4/5 -> min_effective_votes=2/2/3/4 == ceil(2N/3)

# 可达性
grep -rn "active_sessions"   src/     # 仅 live_dispatcher.py:171
grep -rn "agmsg_member_id"   src/     # 仅 schema
```
