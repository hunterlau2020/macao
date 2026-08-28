# MACAO 第一/二阶段受控实机联调与架构装配 独立评审（claude）

评审对象：`aa173d8..906b17e`（申请文档 `82ffe99`），目标等级 **L3 INTEGRATED / PG-2**。
评审范围：本轮沿用既定四轴分工（claude = 语义/产品/业务流转轴），但本报告对 codex 已发布的
`2026-08-28-review-result-906b17e-codex.md` 中全部 P0/P1 逐条做了独立重新推导（非转述），并补充
业务流转轴自身发现的问题。方法论依据 `docs/MACAO_REVIEW_GUIDELINES.md`：不采信"已修复"的自述，
一律重新读取代码行、重跑命令或写最小复现脚本验证。

## 结论

**不准予 L3 INTEGRATED / PG-2。且本轮新增的 3 个 P0 已使系统倒退，不再满足 `docs/MACAO_REVIEW_GUIDELINES.md`
定义的 PG-1（要求 L2 阶段 P0/P1 为零）。** 与 codex 独立同判：本轮交付的是"配置骨架就位 + 短命令 PTY 冒烟测试
+ 自制 YAML 驱动的模拟闭环"，不是申请文档所称的"真实多 Agent 协同"。34/34 测试全绿的原因是测试断言本身
过浅（见下文"新增发现 F1"），而非业务逻辑正确。

补充说明：申请文档使用的目标等级名称"L3 INTEGRATED"在 `MACAO_REVIEW_GUIDELINES.md` 中并不存在——该文件
定义的是 **L3 SCENARIO-VERIFIED**（第 61 行：要求"全同意/1:1 僵局/超时/弃权/崩溃恢复/返工循环等场景均有可
复现推演或测试证据"）。本轮既未提供这些场景的证据，也未在请求文档中说明该 L3 是否为同一等级的另一种表述，
这本身就是一处治理流程瑕疵（见新增发现 F3）。

---

## 一、独立复核 codex 的三项阻断项（P0）

### 复核 P0-1：Phase 2 Runner 未注入任何真实 Adapter，报告字段读取了不存在的 key

独立重新读取 `src/macao/workflow/e2e_runner.py:95`：

```python
orchestrator = Orchestrator(project_root=str(self.repo_dir), config=self.config)
```

未传入 `executor_adapter`/`reviewer_adapters`。回看 `orchestrator.py:47-48`：`self.reviewers = reviewer_adapters or []`，
即空列表。`dispatch_review_requests`（`orchestrator.py:155`）随即落到默认分支：

```python
rev_ids = [r.agent_id for r in self.reviewers] if self.reviewers else ["cc-glm", "kimi"]
```

也就是说实际参与分发/隔离 Worktree 创建的是内置占位 `cc-glm`/`kimi`，而不是申请文档反复强调的
`codex`/`opencode`/`antigravity`。但 `e2e_runner.py:186` 的 `steps_log` 却硬编码写入
`reviewers = ["codex", "opencode", "antigravity"]` 作为展示字段——这是与实际执行完全脱钩的伪造展示，
而非真实回填。

进一步确认 vote_breakdown 的 key 不匹配问题：`consensus/engine.py:43-47` 中 `breakdown` 字典的实际 key 是
`{"approve", "reject", "abstain"}`；但 `e2e_runner.py:225-226` 读取的是：

```python
"votes_yes": breakdown.get("yes_approve", 0),
"effective_votes": breakdown.get("effective_votes", 0),
```

两个 key 在 `breakdown` 中永远不存在，`.get(..., 0)` 恒返回 `0`。我独立执行了实机 `macao e2e-run`：

```
$ PYTHONPATH=src python3 -m macao.cli.main e2e-run
...
4. Consensus Evaluation | decision=APPROVED, state=MERGING, votes_yes=0, effective_votes=0
```

**确认与 codex 一致**：申请文档第 146-148 行展示的表格与此矛盾（显示 `votes_yes=3, effective_votes=3`），
说明申请文档中的机验证据截图本身与当前代码行为不符（要么是过时快照，要么是手工编辑），这加重了证据可信度问题。

### 复核 P0-2：合并安全策略被静默丢弃

独立重新读取 `core/config.py`：`ConfigManager.load()`（第 23-51 行）返回的是 Schema 顶层嵌套原始字典
（`project`/`team`/`policy`/`merge`），从未被拍平。`ConfigManager` 类上确实定义了正确路径的属性访问器
（如 `require_human_signoff` 读 `merge.require_human_signoff`，第 101-104 行），但 `cli/main.py:92`
的 `get_orchestrator()` 调用的是 **classmethod** `ConfigManager.load_config()`（`config.py:53-56`），
它直接返回 `mgr.load()` 的原始嵌套字典，**完全绕过了这些属性访问器**，这些属性访问器因此是死代码。

`orchestrator.py:344-345` 随后对这个嵌套字典做扁平键读取：

```python
ci_cmd = self.config.get("ci_gate_command")       # 顶层无此键 -> None
req_signoff = self.config.get("require_signoff", False)  # 顶层无此键 -> 恒 False
```

我在仓库根 `macao.yaml` 上直接复现：

```
$ PYTHONPATH=src python3 -c "
from macao.core.config import ConfigManager
cfg = ConfigManager.load_config('macao.yaml')
print('flat require_signoff:', cfg.get('require_signoff', 'MISSING-DEFAULTS-FALSE'))
print('actual schema value merge.require_human_signoff:', cfg.get('merge',{}).get('require_human_signoff'))
"
flat require_signoff: MISSING-DEFAULTS-FALSE
actual schema value merge.require_human_signoff: True
```

即：`macao.yaml` 明确要求人工签字（`true`），但 `Orchestrator.execute_merge` 实际拿到的 `require_signoff`
恒为 `False`，人工签字门禁被静默绕过。此外 `orchestrator.py:347-352` 调用 `execute_merge_pipeline` 时从未
传 `remote_name`，`merge/controller.py:92-96` 的 `git push` 因此永远不会执行（参数默认 `None`）。
**确认与 codex 一致，P0 成立。**

另需指出：`cli/main.py:90-94` 的 `get_orchestrator()` 用 `except Exception: pass` 吞掉配置加载/校验异常，
退回到 `Orchestrator.__init__` 内建默认值（`orchestrator.py:49-54`，同样是 `require_signoff: False`）。
这是双重 fail-open：即使 Schema 校验失败（说明 `macao.yaml` 本身有问题），系统也不会拒绝执行合并，而是静默
降级为最不安全的默认策略。这与 PRD 对合并安全应当 fail-closed 的一贯要求相反。

### 复核 P0-3："sandboxed" 标签不代表任何真实隔离

独立重新读取 `adapter/integ_harness.py:61-101`：整个"生命周期联调"实际只做了：`tempfile.mkdtemp()` 建一个
空目录 → `PTYSession(cmd=[cli, "--version"], cwd=tmp_sandbox)` → 等待进程自然退出 → `os.kill(pid, 0)` 探测
是否已死。**没有调用 `session.write_input()`/`send_input()` 做任何真实的输入交互**（`write_input` 方法存在
但整个 harness 从未调用它），"ANSI 清洗"验证逻辑（第 89 行）是 `len(logs_captured) > 0 or session.process.poll() == 0`
——只要进程以退出码 0 结束就算通过，与是否真的捕获并清洗了 ANSI 转义序列无关。

再看 `PTYSession` 本身（`pty_session.py`）：直接 `Popen` 同一 OS 用户身份运行，没有容器、命名空间、网络限制
或凭据隔离；`OpenCodeAdapter.capabilities()`/`AntigravityAdapter.capabilities()`（`opencode.py:26`,
`antigravity.py:26`）却把 `execution_mode` 硬编码标记为 `ExecutionMode.SANDBOXED`。**确认与 codex 一致**：
"sandboxed" 只是一个自称的枚举值，不对应任何可验证的安全边界，如果 Reviewer CLI 被提示注入攻破，能以宿主
用户权限访问全部文件、凭据与网络。

---

## 二、独立复核 codex 的五项重要问题（P1）

| 编号 | 复核方式 | 结果 |
|---|---|---|
| Phase 1 验收标准过弱 | 重读 `integ_harness.py:87-92, 119-120` | 确认：成功判据仅为 `pty_spawn_ok and clean_kill_ok`，未验证 PGID/子进程/SIGKILL 路径，异常分支不 terminate 已启动 session |
| 归档验收假阳性 | 重读 `fsm.py:85,100`（写入 `.macao/archive/{checkpoint_ref}/r{round}`）vs `e2e_runner.py:249`（检查 `.macao/archive/{task_id}/r1`） | **确认路径不一致**，`task_id` 与 `checkpoint_ref` 是两个不同字符串，`archived_files` 恒为空列表；`cli/ui.py:134` 的 `render_e2e_report` 无条件打印 `[green]PERSISTED[/green]`，与 `archived_files` 实际内容无关——我读取该行源码确认此为无条件字面量，不是 bug 掩盖，而是压根没做条件判断 |
| 独立 ACK 可被无 recipient 的调用整体确认 | 重读 `msg/bus.py:91-106` | 确认：`ack(message_id)` 不传 `recipient` 时，`UPDATE message_deliveries SET status='ACKED' WHERE message_id=?`（无 `recipient` 过滤），会一次性 ACK 该消息全部收件人的投递记录 |
| `git diff --check` 并非 0 errors | 独立执行 `git diff --check aa173d8..HEAD` | 确认：退出码 `2`，报告多处行尾空格（`CONTROLLED_E2E_INTEGRATION_PHASE2.md`、`CONTROLLED_INTEGRATION_PLAN.md`、`POC_VERIFICATION_REPORT.md`、申请文档本身），与"0 errors (clean)"声明矛盾（性质为 Markdown 双空格换行符被误判，非破坏性，但作为"机验证据"仍属失实陈述） |
| 真实 Adapter 日志读取签名不匹配 | 独立执行复现脚本 | `PYTHONPATH=src python3 -c "..."` → `TypeError: PTYSession.get_clean_logs() takes 1 positional argument but 2 were given`，确认 `claude.py:88`/`codex.py:77`/`kimi.py:75` 传入 `tail_lines` 参数，但 `pty_session.py:115` 的 `get_clean_logs(self)` 不接受任何参数 |

**以上五项 P1 全部独立复现成功，与 codex 报告结论一致，无一为夸大或误判。**

---

## 三、业务流转轴补充发现（codex 报告未覆盖）

### F1（新增·根因说明）：`test_e2e_phase2.py` 断言过浅，是 34/34 全绿掩盖上述 P0 的直接原因

`tests/test_e2e_phase2.py:15-19` 仅断言：

```python
self.assertEqual(res["status"], "PASS")
self.assertEqual(res["final_state"], "DONE")
self.assertEqual(res["decision"], "APPROVED")
self.assertTrue(res["merge_exact_match"])
self.assertEqual(len(res["steps"]), 5)
```

未断言 `votes_yes`/`effective_votes` 是否与实际参与人数一致，未断言 `archived_files` 非空，未断言
`reviewers` 展示字段与 `orchestrator.reviewers` 实际注入的 Adapter 集合一致。这是本项目第三轮（继
Phase0/1 Code 评审、23dfad5 技术框架评审之后）重复出现"测试覆盖路径表面绿、但只断言外壳状态字段、不断言
语义内容"的模式（详见 `2026-08-27-review-result-23dfad5-tech-framework-claude.md` 的"Reviewer 自审记录"）。
建议：新增回归测试显式断言 `votes_yes == 3`、`archived_files` 非空、`reviewers == [r.agent_id for r in orchestrator.reviewers]`，
这些断言在当前代码下会直接失败，可作为修复验收的机验判据。

### F2（新增）：`configured_reviewers=3` 硬编码与实际注入的 Reviewer 集合（0 个）脱钩，仲裁计算基准本身失真

`e2e_runner.py:216`：`orchestrator.collect_and_evaluate_consensus(task_id, configured_reviewers=3)`。
但 `collect_and_evaluate_consensus` 内部（`orchestrator.py:225`）用于过滤合法评审人的 `allowed_rev_ids`
取自 `self.reviewers`（为空 → `None`，即不过滤，见 `vote.py:49`：`allowed_reviewer_ids is None` 时不限制
reviewer_id）。这意味着法定人数分母（`configured_reviewers=3`）是调用方手写的魔法数字，与 Orchestrator
实际知道的"团队规模"完全无关联——如果有人在 `.macao/.reviews/` 下伪造第 4 份评审文件，也会被无条件采纳并
计入仲裁，因为没有 `allowed_reviewer_ids` 白名单约束。这是比 P0-1 更深一层的问题：即使按 codex 的修复建议
把真实 Adapter 注入 Orchestrator，只要 `configured_reviewers` 仍是外部硬编码而不是从 `self.reviewers`
派生，仲裁的分母/白名单就仍然可能与真实团队组成不一致。

修复建议：`configured_reviewers` 应当由 `len(self.reviewers)` 派生而非调用方传入字面量；`collect_reviews`
的 `allowed_reviewer_ids` 在 `self.reviewers` 为空时应视为"无合法评审人"直接判定 DEADLOCK/拒绝，而不是
退化为"不过滤"（当前的 `None` 语义等价于信任模式，安全性上是 fail-open，应改为 fail-closed）。

### F3（新增·治理流程）：申请目标等级名称与治理文件定义不一致，且本轮已跌出 PG-1

`docs/MACAO_REVIEW_GUIDELINES.md` 定义的等级阶梯是 L1 DOC-ALIGNED → L2 SPEC-CODE-ALIGNED →
**L3 SCENARIO-VERIFIED** → L4 RELEASE-READY，门禁阶梯是 PG-1（L2 + P0/P1 为零）→ PG-2（PG-1 + 接口稳定 +
消费方场景测试）。申请文档标题使用的是"L3 INTEGRATED"，该名称在治理文件中不存在。若这是笔误应更正为
L3 SCENARIO-VERIFIED；若是有意引入的新等级，需要先修订 `MACAO_REVIEW_GUIDELINES.md` 再引用，否则无法
判断本轮到底要满足哪些准出条件。

更关键的是：`MACAO_REVIEW_GUIDELINES.md` 第 71 行明确 PG-1 的条件是"L2；P0/P1 为零"。本轮新增的 3 个 P0
（经我独立复现全部成立）意味着即使不考虑 L3/PG-2，**该 commit 也已经不满足此前已经达标的 PG-1**，是一次
真实的回退，而不只是"这次没能再往前一步"。建议 STATUS.md 在登记本轮结论时明确写"倒退出 PG-1"，而不是维持
"L2/PG-1 已达标，本轮争取 L3/PG-2"的既有措辞，避免掩盖回退事实。

### F4（新增·轻微）：新增的 OpenCode/Antigravity Adapter 的 `ack()` 是硬编码桩，从未接入 Arch-3 声称的独立 ACK 机制

`adapter/opencode.py:85-86`、`adapter/antigravity.py:85-86`：

```python
def ack(self, message_id: str) -> bool:
    return True
```

不调用 `MessageBus.ack()`，不做任何状态更新。同时两个类都没有实现 `get_logs()`（`grep` 全文件确认不存在该方法，
继承自 `AgentAdapter` 抽象基类也没有默认实现，`base.py` 中 `get_logs` 甚至不在抽象方法列表里）。这意味着
"Arch-3 消息总线独立 ACK"即便在 Orchestrator 层被正确调用，落到这两个新 Adapter 上也是空操作——不算阻断项
（因为当前 Orchestrator 从不调用 Adapter 的 `ack()`，前面 P0-1 已覆盖"Adapter 整体未接线"），但作为独立观测
记录，避免下一轮把"新增两个 Adapter"误当作已完整对齐 Arch-3 的证据。

---

## 四、正向确认项（独立验证仍然成立，未回退）

- `PYTHONPATH=src python3 -m unittest discover tests -v`：独立重跑，**34 ran / 34 PASS**，与申请文档一致。
- `fsm.py:32` 的 `TransitionTable.can_transition(...)` 门禁调用仍然存在（此前轮次修复的 P1 未回退）。
- `dispatch_review_requests`（`orchestrator.py:156-168`）的 Fail-closed Worktree 创建逻辑仍然存在：
  worktree 创建失败时 `raise RuntimeError("Security Gate Blocked...")`，未回退为静默降级主工作区。
- `message_deliveries` 表（`storage/db.py:87`）与按 recipient 的 `INSERT`（`msg/bus.py:48-55`）结构性存在，
  只是 F4 指出的两个新 Adapter 未真正使用它，以及 P1 指出 `ack()` 无 recipient 时的语义漏洞。
- `merge/controller.py` 的 `require_signoff` 检查（第 49-53 行）、`shlex.split` CI 命令执行（第 74 行）、
  HEAD 与 checkpoint 硬校验（第 88-90 行）代码本身逻辑正确，问题只在于 Orchestrator 层从未把真实配置值
  传给它（P0-2 的根因在调用方，不在 `MergeController` 自身）。

---

## 五、准入建议

与 codex 独立同判：**在上述 3 个 P0 全部关闭前，定级应回退为 L2（且需要重新确认是否仍满足 PG-1 的"P0/P1
为零"条件），不得进入 L3/PG-2。** 复审前至少需要：

1. Composition Root（`get_orchestrator()` / `ControlledE2ERunner`）按 `macao.yaml.team` 真实构造并注入
   全部 Executor/Reviewer Adapter，`configured_reviewers` 从 `len(self.reviewers)` 派生（对应 F2）；
2. `ConfigManager` 的嵌套结构与 `Orchestrator`/`MergeController` 消费的扁平字段之间建立单一映射点（建议
   引入一个显式的运行时策略 DTO，在 Composition Root 处一次性转换，而不是让调用方各自 `.get()` 嵌套字典）；
   配置加载/校验失败必须拒绝而非静默退回不安全默认值；
3. 为归档校验、投票展示、Adapter 日志读取分别补充与真实字段名对齐的回归测试（对应 F1，且应直接写成会在
   当前代码下失败的断言，作为验收判据而非事后补充）；
4. 明确"sandboxed"标签的可验证定义（容器/命名空间/网络限制等任一项），preflight 与集成测试中验证隔离失败
   即拒绝接入；
5. 统一"L3 INTEGRATED"与治理文件术语（对应 F3），STATUS.md 如实记录本轮相对 PG-1 的回退状态。
