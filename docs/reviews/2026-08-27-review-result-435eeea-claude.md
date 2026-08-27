# MACAO Phase 0 / Phase 1 代码独立复审结论（语义/业务流转轴，响应 review-request-Phase0-Phase1-Code）

- 评审日期：2026-08-27
- 被评审 commit 范围：`d137a05..435eeea`（申请文件 `docs/reviews/2026-08-27-review-request-Phase0-Phase1-Code.md`）
- 承担轴线：按请求第五节排班，本报告只覆盖**语义/业务流转轴**（10 态 FSM 事件流转 E1~E10、多轮返工、Orchestrator 事件循环与 PRD v2.3.1 业务逻辑的一致性）；安全/沙箱/存储轴（codex）与治理/Schema 契约轴（opencode）留待其各自报告。
- **本轴结论：不通过，发现 1 个 P0 + 2 个 P1 + 1 个 P2。目标等级 L2 SPEC-CODE-ALIGNED / PG-1 不成立。** 其中 P0 是一个可复现的安全回归：Deadlock 场景会被系统自动、静默地判定为 REWORK，完全绕过 PRD v2.3.1 刚刚确立的人工仲裁保证——而这正是本人在 `8ab9be7`/`cc77a94`/`403ddc7` 三轮文档评审中持续追踪、且已确认 PRD 文本本身已正确闭环的那个设计点。代码实现没有遵循它刚刚通过的规格。

## 一、机器校验复现（独立执行，未直接采信申请方数字）

```bash
PYTHONPATH=src python3 -m unittest discover tests -v
```

结果：**22/22 全绿**，与申请方所述一致，独立复现成功。

## 二、traceability matrix 逐项复核（仅本轴相关行）

| 申请方声明 | 复核结果 | 证据 |
|---|---|---|
| §3.1 / 10 状态 FSM：`types.py`/`fsm.py` ✅ 对齐 | **属实** | `AgentState` 枚举 10 值与 PRD §3.3 完全一致（`src/macao/core/types.py:9-20`） |
| §3.3 / E1~E10 统一转移表：`transitions.py` ✅ "转移表白名单校验，非法前置条件一律拒绝并触发审计" | **不属实（P1，见 3.2）** | `TransitionTable.can_transition()` 从未被 `fsm.py`/`orchestrator.py` 调用，仅被其自身单元测试直接调用 |
| §2.3 / 2/3 多数仲裁算法：`engine.py`/`vote.py` ✅ 对齐 | **部分属实，但有致命副作用（P0，见 3.1）** | 判定算法本身（`ConsensusEngine.evaluate`）正确；但 `VoteAggregator.generate_vote_result` 的落盘时机违反 PRD §3.3 E3 行 |
| §3.4 / 场景 S1~S6 与死锁接管：`orchestrator.py` ✅ "完整支持平票死锁超时接管" | **不属实（P0）** | 见 3.1，Deadlock 分支在返回 HOLD 的同时把 `vote_result.json` 写为 `decision: REWORK_REQUIRED` 并落盘，任何后续状态识别都会静默转入 REWORK |
| §14.5 / MERGING 中间态与 CI 门禁：`controller.py` ✅ "人工签字放行（require_human_signoff）" | **不属实（P2，见 3.4）** | `execute_merge_pipeline` 接收 `require_signoff` 参数但函数体从未读取/校验它；且全程无 `git push` 调用 |
| §11.4/§11.5、§2.4、§5.2、§16.3 三行 | 未在本轴深入复核 | 留给 codex（存储/安全）与 opencode（Schema 契约）两份报告 |

## 三、发现详情

### 3.1（P0）Deadlock 被自动、静默判定为 REWORK——PRD v2.3.1 的核心安全设计在代码里失效

**根因**：`src/macao/workflow/orchestrator.py:204-221`（`collect_and_evaluate_consensus` 的 Step 2）在分支判断 `raw_decision` **之前**，无条件调用了 `self.vote_aggregator.generate_vote_result(...)`。而 `VoteAggregator.generate_vote_result`（`src/macao/consensus/vote.py:102-144`）内部：

1. 第 125 行：`"decision": decision.value if decision != Decision.DEADLOCK else "REWORK_REQUIRED"` —— 把 `DEADLOCK` **静默映射为 `"REWORK_REQUIRED"`**，`resolution` 字段默认 `"automatic"`（因为此处调用未传 `human_resolution`）；
2. 第 140-144 行：**无条件把这个结果写入 `.macao/vote_result.json` 并落盘**。

这与 PRD v2.3.1 §3.3 E3 行明确规定的"若判定为 Deadlock，就地发送 `HUMAN_OVERRIDE_REQUEST` 并 **HOLD，不写 `vote_result.json`**"完全相反——而这条规则正是本人在 `8ab9be7` 报告首次发现、`cc77a94` 报告持续追踪、并在今天对 `403ddc7`（PRD v2.3.1）的复审中确认已正确落地的设计点（见 `docs/reviews/2026-08-26-review-result-403ddc7-claude.md` §2.3）。**PRD 文本是对的，代码没有照着实现。**

**可复现验证**（`PYTHONPATH=src python3` 独立执行，未依赖任何测试桩之外的改动）：

```
1 Approve + 1 Reject -> collect_and_evaluate_consensus() 返回 (None, vdata)，DB 状态仍为 CONSENSUS_CHECK（表面正确）
  但同时 .macao/vote_result.json 已写盘，内容为 {"decision": "REWORK_REQUIRED", "resolution": "automatic", ...}
再调用一次 fsm.step("task-x")（模拟事件循环的下一次轮询/一次 status 刷新/一次重试）：
  -> StateChange(from_state=CONSENSUS_CHECK, to_state=REWORK, source='E5', ...)
  -> DB 状态变为 REWORK
```

即：**只要在人工裁定 Deadlock 之前，Orchestrator 事件循环再被调用一次（这在其自身"single-process event loop"架构下是完全正常、大概率会发生的操作——状态轮询、CLI `status` 命令触发的刷新、或仅仅是重复调用同一个评估函数），Deadlock 就会被永久性地、不可逆地自动判为 REWORK，人工从未被真正问询过（`HUMAN_OVERRIDE_REQUEST` 消息虽然发出，但在其被响应前状态已经被别的路径抢先推进）。** 这不是边界情况，是 2 人 Reviewer 配置下 1:1 平票这一**高频路径**的必然结果。

**建议**：`generate_vote_result` 的调用必须移到 `raw_decision` 分支判断**之后**，且只在 `APPROVED`/`REWORK_REQUIRED`（自动决策）或人工裁定（`resolve_override`）两种场景下调用；Deadlock 分支绝不能调用它，也不能在磁盘上产生任何 `vote_result.json`。此外 `generate_vote_result` 函数本身不应该接受"把 DEADLOCK 静默改写成 REWORK_REQUIRED"这种能力——如果调用方传入的票面本身是 Deadlock，函数应该拒绝生成（`raise`），而不是自己悄悄改写决策，这是纵深防御：即使未来某个调用点重犯本报告发现的调用顺序错误，也不应该允许一个不存在的自动决策被写盘。

### 3.2（P1）`TransitionTable.can_transition` 是死代码——统一转移表在运行时从未被强制执行

`src/macao/workflow/fsm.py:21-63`（`WorkflowFSM.transition`）直接接受调用方传入的任意 `(to_state, trigger_id)` 组合并执行落库，全程不调用 `TransitionTable.can_transition`。全仓库 `grep -rn "can_transition"` 只命中 `transitions.py` 自身定义和 `tests/test_fsm.py` 对该静态方法的直接单元测试——生产路径（`fsm.py`、`orchestrator.py`）零调用。

这意味着 PRD §3.3 "验收标准：任意时刻每一步最多命中一个合法转移""任何实现不得引入其他状态转移路径"这条核心不变式，在当前实现里**没有任何运行时防线**——它能通过测试只是因为目前所有调用点碰巧都是手写的合法组合，而不是因为有代码真的会拒绝非法组合。3.1 节的 P0 之所以能发生，根本原因之一就是这里：如果 `can_transition` 真的被接入调用链，`WorkflowFSM.transition` 至少有机会在写入非常规转移前发出告警或拒绝（虽然 3.1 的问题主要出在"写错了 vote_result.json 内容"而非"转移非法"，但两者是同一类"契约定义了但没接线"问题）。

**建议**：`WorkflowFSM.transition()` 在更新 State Store 前调用 `TransitionTable.can_transition(from_state, to_state, trigger_id)`，非法组合应 `raise` 并写审计日志（`log_audit_event`），而不是静默执行。

### 3.3（P1）E10（CANCEL）可以对已终态（DONE/CANCELLED）的任务再次生效

PRD §3.3 E10 行明确限定来源状态为"`*`（任意活动态，即除 DONE/CANCELLED 外）"，但 `transitions.py:25` 的规则 `"E10": (None, AgentState.CANCELLED)` 里 `rule[0]` 是 `None`（不限来源），且如 3.2 节所述这条规则本身也从未被实际调用来做校验。`orchestrator.resolve_override`（`src/macao/workflow/orchestrator.py:265-297`）在执行 CANCEL 分支前，同样没有检查 `current_st not in (AgentState.DONE, AgentState.CANCELLED)`。

**可复现验证**：直接对一个已经 `state=DONE` 的任务调用 `fsm.transition(task_id, AgentState.CANCELLED, "E10", ...)`，执行成功，DB 状态从 `DONE` 变为 `CANCELLED`——一个已经完成合并的任务可以被"事后取消"，产生误导性的审计记录（对一个已经进了 `main` 分支的变更标记 CANCELLED，与实际情况不符）。

**建议**：在 `resolve_override` 与（一旦 3.2 节修复后）`TransitionTable` 的 E10 规则里都加入终态排除检查。

### 3.4（P2）Merge Controller 未实现人工签字校验与 push 步骤，与其自身 traceability 声明不符

`src/macao/merge/controller.py:20-73` 的 `execute_merge_pipeline(..., require_signoff: bool = True)`：
- 参数 `require_signoff` 在函数体内**从未被读取或用于任何分支判断**——`require_human_signoff: true` 这个 PRD 称为"刻意的保守安全默认值"的开关，在代码里是纯装饰性参数；
- 函数全程只做 `checkout` → `merge --ff-only` → 可选 CI 命令 → 读取本地 HEAD，**没有任何 `git push` 调用**，也没有发送 `MERGE_COMPLETED`。

这本身对 Phase 0/1（尚未接入真实 CLI、尚未做实机联调）而言是可以理解的克制，但申请文件第三节 traceability matrix 把这一行标注为"✅ 对齐：...人工签字放行（`require_human_signoff`）"——这个具体表述与代码不符，容易让复审方误判该项已实现。

**建议**：要么在 `execute_merge_pipeline` 里补上对 `require_signoff` 的实际校验（未通过时返回 `False` 并要求走 `merge approve`），要么把 traceability matrix 该行的措辞改为"待补：签字与 push 步骤规划于后续阶段"，避免"✅ 对齐"与实现范围不一致。

## 四、本轴确认无误的部分（予以认可）

- `WorkflowFSM.transition` 的 round 递增逻辑（进入 `REWORK` 时 `round+1`）与 `orchestrator.py` 里 `REWORK_REQUEST` payload 的 `round` 字段计算一致，S2（多轮返工）测试场景下人工复核了完整调用链（round 1→2），未发现 off-by-one；
- `.dev.yml` 归档（E2）与 `vote_result.json` 归档（E4a/E4b）的触发时机（`fsm.py:57-61`）与 PRD §3.4 产物生命周期表一致；
- `state_engine.py` 的作用域读取（Layer 1a/1b/1c 分别限定 `checkpoint_ref`/`review_round` 双匹配）正确实现了 PRD §3.2 的核心不变式，S1/S2 两条 happy-path/rework-loop 仿真测试真实执行了这条代码路径（非桩测试）；
- `ConsensusEngine.evaluate` 的法定人数与 2/3 比例判定算法本身（不含调用方对结果的处理）与 PRD §2.3 公式一致，含浮点容差处理合理。

## 五、结论与建议

**不建议宣告 L2 SPEC-CODE-ALIGNED / PG-1。** 3.1 节的 P0 是一个可复现的安全回归，且恰好发生在本人过去三轮文档评审重点追踪、PRD 文本本身已确认正确闭环的那个场景——代码与刚刚定稿的规格在这一点上直接冲突，风险等级不能因为"文档已经对齐"而降级。3.2/3.3 两个 P1 是同一类"契约定义了但未接入运行时校验"问题的不同表现，建议一并修复（很可能是同一个补丁：把 `TransitionTable.can_transition` 接入 `WorkflowFSM.transition`，并把 `generate_vote_result` 移出 Deadlock 路径）。3.4 的 P2 主要是 traceability 表述与实现范围不一致，不阻塞本身，但建议连同其余矩阵行一并核实后再提交下一轮。

## 六、建议的闭环顺序

1. 修复 P0：调整 `collect_and_evaluate_consensus` 的调用顺序，禁止 Deadlock 路径写 `vote_result.json`；补一个回归测试断言"Deadlock 后 `.macao/vote_result.json` 不存在，且后续 `fsm.step()` 不会转移状态"（当前 `test_scenario_s3`/`s6` 都没有这个断言，是本次未能提前发现该问题的直接原因）；
2. 修复 P1（3.2/3.3）：`WorkflowFSM.transition` 接入 `TransitionTable.can_transition`；`resolve_override` 加终态排除检查；
3. 修复 P2（3.4）：明确 `require_signoff`/push 的实现范围，更正 traceability matrix 措辞或补代码；
4. 以上完成并补齐回归测试后，建议连同 codex（安全/沙箱/存储轴）与 opencode（治理/Schema 契约轴）的独立报告一并提交下一轮复审，再定级 L2 SPEC-CODE-ALIGNED / PG-1。

## Reviewer 自审记录

方法：不满足于"22/22 测试全绿"这一表面信号，逐条对照 traceability matrix 声明与实际调用链（`grep` 确认函数是否真的被调用，而非只看是否被 import），并对最关键的 Deadlock 路径用独立脚本实际复现（而非只读代码猜测行为）。这一方法直接命中了测试套件本身的覆盖盲区——S3/S6 两个 Deadlock 场景测试只断言了 DB 状态与返回值，未断言磁盘产物的存在性与内容，这正是 bug 藏身之处，也提示未来测试补齐时应把"不应该产生的副作用"同样纳入断言，而不仅验证"应该产生的效果"。未覆盖安全/沙箱（PTY、git worktree 生命周期、SQLite WAL 并发）与 Schema 契约完整性两个轴，留给 codex 与 opencode 的独立报告。
