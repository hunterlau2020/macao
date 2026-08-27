# MACAO Phase 0 / Phase 1 核心代码与测试套件 独立评审结论（L2 定级）

- **评审日期**：2026-08-27
- **评审人**：zcode（独立评审，GLM）
- **评审对象**：commit 范围 `d137a05`..`435eeea`（技术架构文档 + `src/macao/` 27 个 Python 文件 + `tests/` 9 套件）
- **对齐基准**：`docs/MACAO_PRD_v2.md` v2.3.1（权威 PRD）、`docs/schemas/`（Draft-07 契约）、`docs/MACAO_REVIEW_GUIDELINES.md` v1.0
- **申请文件**：`docs/reviews/2026-08-27-review-request-Phase0-Phase1-Code.md`
- **结论**：**未达 L2 SPEC-CODE-ALIGNED / PG-1**——PG-1 要求 P0/P1 为零，本轮发现 **P0 × 2、P1 × 7、P2 × 6、P3 × 8**。其中两项 P0 直接违反 PRD v2.3.1 刚闭环的 P0 承诺（Deadlock HOLD 不落盘、worktree 强制注入）。追溯矩阵（申请 §三）10 行中 5 行的"✅ 对齐"声明与代码事实不符。框架骨架（Layer 作用域读取、共识公式、round+ref 双匹配、WAL、AEP 信封校验、quorum 推导）质量良好，修复路径清晰。

---

## 一、复现验证结果（申请 §四，评审人独立执行）

| 指令 | 申请声明 | 实测（Windows 10 / Python 3.11.9） |
|---|---|---|
| `PYTHONPATH=src python3 -m unittest discover tests -v` | 22/22 全绿 | **Ran 22 tests, FAILED (errors=6)**——`test_fsm_transition_lifecycle`、`test_message_bus_pub_sub_ack`、`test_reconcile_*` ×2、`test_state_store_*` ×2 全部因 SQLite 连接泄漏（WAL 句柄未关闭 → 临时目录清理 PermissionError）ERROR |
| `PYTHONPATH=src python3 -m macao.cli.main doctor` | 可复现 | **导入期崩溃**——`cli/main.py:13` → `adapter/claude.py:9` → `pty_session.py:4` `import pty`（Windows 无该模块） |
| `git diff --check` | 0 errors | clean ✓ |

申请声明"可通过标准指令 **100% 独立复现**"未附平台限定；实测在 win32 上两项主声明均不成立（详见 P1-7、P2-8）。POSIX 平台上 22 项测试的结构与断言经评审人静态核读为合理。

## 二、已对齐 / 已确认项（VERIFIED）

1. **共识算法**（`consensus/engine.py:12-64`）：`ceil(2N/3)` 法定人数（N=2→2、N=3→2 ✓）；有效票=赞成+反对（弃权不计分母）；先判法定人数再判 2/3 占比（含 1e-6 浮点容差）；1:1/1弃权+1票/全弃权 → DEADLOCK——与 PRD §2.3 决策表七行逐行一致。
2. **状态作用域读取**（`workflow/state_engine.py:33-103`）：Layer 1a 仅 CODING/REWORK 读 `.dev.yml`（signal/status/round/tests/commit 五重校验）；Layer 1b 仅 WAITING_REVIEW 读当前 ref+round 的 `.review.yml` 并对 quorum 判定；Layer 1c 仅 CONSENSUS_CHECK 读 vote_result——无固定顺序全目录扫描，符合 §3.2"作用域化"要求。
3. **AEP 信封**（`msg/envelope.py:30-45` + `msg/bus.py:21-46`）：create 即经 `aep_envelope.schema.json` 强校验，非法即抛错；message_id 满足 `^msg-[0-9]{8}-[0-9]{3,}$`；bus 落盘 SQLite 队列、按接收者过滤、ACK 幂等（rowcount 判定）。
4. **Schema 绑定**（`core/schema.py`）：全部产物校验直读 `docs/schemas/`（单一契约源），dev/review/vote_result/context/envelope/config 六验证器齐备；mock 适配器产物自产即校验（`adapter/mock.py:121,164`）。
5. **配置加载**（`core/config.py:23-50`）：YAML → Schema 校验失败拒绝启动；`min_effective_votes` 按 ⌈2N/3⌉ 推导、显式低于推导值时强制抬升——与 §13 加载规则一致。
6. **E2/E6 轮次推进**（`workflow/fsm.py:35-39` + S2 仿真）：进入 REWORK 即 round+1，REWORK_REQUEST 携带新 round；round+ref 双匹配使跨轮旧产物不遮蔽（S2 全流程测试验证）。
7. **E9/E10 命令转移存在**（`workflow/orchestrator.py:292-295`）：RETRY_REVIEW→WAITING_REVIEW、CANCEL→CANCELLED 转移本身可用（落盘问题见 P1-5）。
8. **死锁人工接管入口**（`orchestrator.py:242-261`）：DEADLOCK → 发 HUMAN_OVERRIDE_REQUEST（options 四值、10m 时限）+ 审计事件，任务保持 CONSENSUS_CHECK——入口行为与 §3.3 E3 行一致（落盘问题见 P0-1）。
9. **适配器契约与能力矩阵**（`adapter/base.py` + claude/codex/kimi capabilities）：与 §12.1/§12.3 矩阵逐字段一致（claude: execute/full/hook、codex/kimi: review/sandboxed/worktree）。
10. **WAL 与预写库**（`storage/db.py:95-99`）：每连接 WAL + foreign_keys；消息队列表即 §11.6 agmsg SQLite 形态。

## 三、P0：必须先解决

### P0-1 Deadlock 轮 vote_result.json 被提前落盘，且 decision 伪写为 REWORK_REQUIRED

- **违反**：PRD §3.3 E3 伴随动作（`MACAO_PRD_v2.md:829`）"**HOLD，不写 `vote_result.json`**…不提前写决策未定的文件"——这是 v2.3.1 分歧项（并集方案 B）闭环的核心承诺；PRD §3.4 场景三（`:900`）据此声称"不存在 Deadlock 被误读为 REWORK 的路径"。
- **代码事实**：
  - `workflow/orchestrator.py:215-221`：`collect_and_evaluate_consensus` 在决策分支判断（`:224`）**之前**无条件调用 `generate_vote_result`；
  - `consensus/vote.py:141-144`：`generate_vote_result` 直接写盘 `.macao/vote_result.json`；
  - `consensus/vote.py:125`：`"decision": decision.value if decision != Decision.DEADLOCK else "REWORK_REQUIRED"`——Deadlock 时**字面伪写** decision=REWORK_REQUIRED、resolution=automatic 落盘。
- **可复现后果链**：死锁 HOLD 期间用户执行 `macao status` 或 `doctor`（`cli/main.py:118,146` 每次运行都调 `reconciler.reconcile()`）→ `storage/reconcile.py:40-44` 读到该伪文件（round 匹配、Schema 合法）→ `update_task_state(REWORK)`——**人工裁定期被静默劫持为自动返工**，且审计以"CRASH_RECONCILE"名义洗白。S3 测试未暴露是因为 `resolve_override(APPROVED)` 随后重写同一文件掩盖了伪文件；S6（CANCEL）路径不重写（见 P1-5），伪文件永久残留。
- **修复方向**：`generate_vote_result` 拆分"计算"与"落盘"；DEADLOCK 分支仅发 Type G + 审计，不落盘；或落盘不含 decision 的中间票据（需先修 PRD/Schema，不建议）。

### P0-2 review_context.repository.workspace_path 注入主工作区，worktree 失败静默回退主工作区

- **违反**：PRD §16.3（`:1629`"评审专家**绝不进入** Executor 主工作区"）、§5.2/§2.4（workspace_path = 注入后的独立 worktree 路径，v2.3.1 P0-2 修复的核心字段）、§12.2（supports_worktree 为准入硬条件）。
- **代码事实**：
  - `workflow/orchestrator.py:137`：`ReviewContextBuilder(..., workspace_path=str(self.root))`——权威 context 的 workspace_path 恒为主工作区；
  - `orchestrator.py:147-155`：真实 worktree 路径（`git.create_isolated_worktree` 返回值）被放入**契约外**顶层字段 `isolated_worktree_path`，而 Reviewer 标准工作流（§5.3 Step 2）只读 `review_context.repository.workspace_path`；
  - `orchestrator.py:148-149`：worktree 创建异常 `except: pass`，失败时 `isolated_worktree_path` **静默回退 `str(self.root)`**（`:155`）——安全红线被降级为 best-effort。
- **后果**：按 PRD §5.3 工作流的 Reviewer 将在 Executor 主工作区执行 fetch/diff/构建；prompt injection 场景下"破坏工作区/外传代码"的暴露面正是 §12.2 强制隔离所要消除的。
- **修复方向**：worktree 路径注入 `repository.workspace_path`；创建失败应阻断该 Reviewer 的分发（准入硬条件），并记审计告警，而非回退。

## 四、P1：进入下一阶段前应修正

### P1-1 转移表白名单校验未接入运行时（追溯矩阵 §3.3 行声明不成立）

`workflow/transitions.py` 的 `TransitionTable.can_transition` 在 `src/` 与 `tests/` 中**无任何生产调用**——`WorkflowFSM.transition`（`workflow/fsm.py:21-63`）不做来源/前置状态校验直接 `update_task_state`。`tests/test_fsm.py:44` 甚至以表外触发 ID `"EXPLICIT_SIGNAL"` 成功驱动转移。PRD §3.3 验收标准"白名单校验，非法前置条件一律拒绝并触发审计"完全未实现；`resolve_override` 亦不校验当前状态（任意状态可 E7）。

### P1-2 E5 缺 max_rework_rounds 守卫

`orchestrator.py:227-228` 与 `state_engine.py:100-101` 对 REWORK_REQUIRED 无条件转移 REWORK；PRD §3.2 Layer 1c（`:783-787`）与 E5 行（`:834` "且 round < max_rework_rounds"）要求达上限时改走 E7 人工裁定。`core/config.py:81-82` 已提供 `max_rework_rounds` 但全仓无消费者。

### P1-3 E7 终局落盘不完整，Decision 枚举缺两值，CLI 与 Orchestrator 双实现互相分歧

- `core/types.py:49-53`：`Decision` 无 RETRY_REVIEW/CANCELLED（且含 Schema 外的 DEADLOCK 值）——代码模型未同步 v2.3.1 P2-9 四值终局模型；
- `orchestrator.py:277-286`：仅 APPROVED/REWORK 写终局 vote_result；RETRY_REVIEW/CANCEL 不写（PRD E7 行 `:836`"裁定结果落盘为终局 vote_result.json…后按选择转移"对四选项一体适用，§3.4 6c/6d 同）；
- `cli/main.py:163-186`：CLI `override resolve` 是**另一套实现**（不写任何终局 vote_result、不采集当前票面）。同一 E7 语义两处实现且均不完整。

### P1-4 MERGING 流水线为死代码；人工签字与 push 未实现（追溯矩阵 §14.5 行声明不成立）

`merge/controller.py` 全仓无 import/调用（grep 证实）；Orchestrator E4 转移到 MERGING 后**无任何推进 E4a/E4b 的代码路径**；`execute_merge_pipeline` 中 `require_signoff` 参数（`:25`）被完全忽略（无 `macao merge approve` 消费点）、无 push 步骤、无"push 对象 == checkpoint_ref"显式校验（仅靠 `--ff-only` 隐式保证）。S1 仿真亦只测到 MERGING（`tests/test_orchestrator_sim.py:77`），申请将本测试列为 §14.5 证据不成立。

### P1-5 artifacts 表回退 v2.3.1 P1-2 修复：覆盖式写入抹历史（追溯矩阵 §11.4/§11.5 行声明不成立）

`storage/db.py:26-38`：复合主键、**无 `artifact_id` 自增列**；`storage/store.py:84`：`INSERT OR REPLACE`（同键重登即删旧行）；`mark_artifact_consumed`（`store.py:92-102`）原行 UPDATE、归档不追加新行——三处合计正是 PRD §11.5（`:1353`）明确废除的"同路径 upsert…抹掉历史审计行"语义。另 `artifacts` 表删除了 PRD DDL 的 `REFERENCES tasks(task_id)` 外键。

### P1-6 review_context 携带伪造质量快照与错误 base_commit（追溯矩阵 §5.2 行声明部分不成立）

- `utils/context_builder.py:29-41`：`files_list=[src/main.py]`、`files_changed=1/insertions=20/deletions=5`、`tests_passed=1`、`coverage=0.85`、`lint_errors=0` 全为硬编码占位默认值；
- `orchestrator.py:133-139`：真实分发路径**未调用** `set_diff_info/set_quality_snapshot` 即 `build()`——每份真实 REVIEW_REQUEST 携带上述伪造数据，违反 §5.2"质量指标（来自 .dev.yml）"与 code_changes 真实摘要语义，直接误导评审；
- `orchestrator.py:135`：`base_commit=task.get("target_branch", "main")`——以**分支名冒充 base commit**（§5.2 refs 语义错误；`tests/test_context_builder.py` 的断言 `base_commit=="main"` 固化了该错误）。

### P1-7 SQLite 连接泄漏；"22/22 全绿、100% 复现"声明在 win32 不成立

`storage/db.py:94-99`：`get_connection` 每次调用新开连接，`with conn:` 仅管理事务**不关闭连接**，全仓无 `close()`——每次存储操作泄漏一个 WAL 句柄。实测后果：win32 上 6 项测试 ERROR（临时目录无法删除锁定文件）、CLI 完全不可用（叠加 P2-8 的 `import pty`）。申请 §四"100% 独立复现"与 STATUS"22/22 PASS"均为平台条件性结论而未声明平台限定。

## 五、P2：可延期但需登记

- **P2-1 reconcile 误映射与弱校验**：`reconcile.py:42` 非 APPROVED 一律 REWORK（RETRY_REVIEW/CANCELLED 合法值被误映射）；`:40` 只核 round 不核 checkpoint_ref；§11.5 场景 B（git 已提交→补 SQLite）与"git > 磁盘 > SQLite"优先级完全未实现（reconciler 无任何 git 调用）。
- **P2-2 归档生命周期部分实现**：`.dev.yml` 仅复制不删除、全程无 git 提交（`git_utils.stage_and_commit` 零调用，§3.4 归档三步"git 提交→复制→删除"仅实现一步半）；`.review.yml` 无任何归档代码（PRD 生命周期表"E3 触发时随 git 提交存档；进入下一轮前已固化于归档目录"）；E5 不归档 vote_result（表定"E4/E5 执行后归档"，代码仅 E4a/E4b）。
- **P2-3 消息总线缺 §11.6 语义**：无 TTL/deadline 过期扫描、无退避重试（"未 ACK 重试最多 3 次"）、DLQ 仅手动 `fail_to_dlq`。
- **P2-4 审计链弱化**：`vote.py:90` input_artifacts.message_id 伪造为 `msg-local-<reviewer_id>`（不满足 AEP ID 模式，亦非真实 REVIEW_RESPONSE 消息 id）——违反 §2.3"必须记录对应 AEP message_id"。
- **P2-5 真实适配器接口未就绪**：`codex.py:65-66` 读取 `review_context` 后**赋值未用**，prompt 不含任何上下文（申请声明"真实 CLI 适配器代码接口已就绪"）；`claude.py:59` 硬编码 `--dangerously-skip-permissions`（§12.6 要求非交互参数登记于 Capability Manifest 并 preflight 校验）。
- **P2-6 Layer 1a 弱于 §2.1 最小有效性**：`state_engine.py:42-51` 不校验 `commit_exists` 与"未被消费过"（PRD `:217` 五条件中两条件缺失；`commit_exists` 已有实现但未接线）。

## 六、P3：登记备查

1. `transitions.py:25` E10 源为 None 允许自 DONE/CANCELLED 终态取消（PRD"任意活动态，除 DONE/CANCELLED 外"）；
2. `types.py:46` OpinionStatus 含 Schema 外死值 ABSTAIN；
3. `context_builder.py:27` fetch_policy 默认 "auto"（PRD 示例 "fetch_before_diff"）；
4. `git_utils.py:43` worktree 路径 `.macao/worktrees/<id>/<task>/r<n>` 与 PRD §5.3/fixture 形状 `<id>/r<n>` 不一致（语义更严，仅形状偏差）；
5. `cli/main.py:192-198` usage 命令输出硬编码假数据；
6. `adapter/base.py` 缺 §12.1 契约的 `subscribe_events(callback)`；
7. 申请 §二声称"18 个模块"，实际 `src/macao/` 为 26 模块 + `__init__`（27 文件）；
8. `tests/test_consensus.py` 未覆盖 3-Reviewer evaluate 场景（仅 quorum 计算），申请"2 人/3 人配置…算法测试"表述略超实际。

## 七、PLAN/ROADMAP 完成声明与证据不符（GUIDELINES §9-B 违例汇总）

| 声明 | 位置 | 事实 |
|---|---|---|
| "实现 E4/E5 触发时的 `.review.yml` 与 `vote_result.json` 归档 ✅ 已完成（测试通过）" | `PLAN.md:77` | `.review.yml` 归档代码不存在（grep 证实）；E5 不归档；无对应测试 |
| "确保无孤儿进程残留 ✅（测试通过）"（Task 0.3） | `PLAN.md:56` | pty_session 零测试覆盖（win32 下更无法导入） |
| "worktree…评审后可靠清理 ✅（测试通过）"（Task 0.4） | `PLAN.md:57` | 无 worktree 创建/清理生命周期测试；`remove_worktree` 零调用 |
| "✅ 产出《PoC 三假设验证技术报告》" | `ROADMAP.md:63` | **全仓不存在该文件**；"产物跨模型解析率 100%"为无实测支撑的确定性表述 |
| "状态转移全量记录于 SQLite 审计日志表与 Git 归档目录" | `ROADMAP.md:92`、`PLAN.md:83` | 审计表 ✓；"Git 归档"仅目录复制，全程无 git 提交 |

## 八、建议的闭环顺序与验收标准

1. **P0-1/P0-2**（死锁不落盘 + worktree 注入）：改 `orchestrator.py`/`vote.py`，新增回归测试——"deadlock 后 `.macao/vote_result.json` 不存在"、"REVIEW_REQUEST 的 `repository.workspace_path` == worktree 路径且创建失败时分发中断"；
2. **P1-1~P1-6** 按 FSM 校验接线 → E5 守卫 → E7 落盘统一（收敛为 Orchestrator 单实现）→ MergeController 接线 + signoff/push → artifacts DDL 迁移（artifact_id + UNIQUE + 追加行）→ context 真实数据源（.dev.yml/git diff）；
3. **P1-7/P2-8** 连接生命周期（连接池或 try/finally close）+ 适配器惰性导入（`pty` 移入函数级 import）后，在 win32 与 POSIX 双平台重跑全套测试，双平台全绿方可复述"22/22"；
4. PLAN/ROADMAP 虚假 ✅ 逐项改回待办或补证据；《PoC 三假设验证技术报告》要么产出要么删除该 ✅ 行；
5. 验收：重新提交时附双平台测试输出 + 修订后的追溯矩阵（每行证据引用到测试函数名）。

## 九、Reviewer 自审记录

- 首次参与 MACAO 评审，无连续漏审史；GUIDELINES §9 五项自检已过（本报告全部 REJECT 附路径+行号；测试声明以本机实测为准并注明平台）。
- 边界声明：本轮为 L2 代码对齐评审，未执行任何真实三方 CLI（与申请的安全前置声明一致）；win32 实测仅覆盖申请 §四的复现指令本身。
