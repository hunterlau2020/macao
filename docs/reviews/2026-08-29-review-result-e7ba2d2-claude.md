# MACAO 独立复审报告 — Phase 1/2 专家意见闭环整改 (commit `906b17e..e7ba2d2`)

> **评审人**：claude（语义/产品/业务流转轴，本轮兼核实全部机验证据）
> **评审日期**：2026-08-29
> **评审对象**：[`2026-08-29-review-request-Phase1-Phase2-Rectification.md`](2026-08-29-review-request-Phase1-Phase2-Rectification.md)
> **审查方法**：不采信申请文档或其他专家报告的既有结论，逐条重新阅读源码 + 独立重跑命令 + 编写复现脚本，只以本次实测结果为准（遵循 `docs/MACAO_REVIEW_GUIDELINES.md`）。
> **审查范围**：`git diff 906b17e..e7ba2d2`（18 文件，732+/410-）覆盖的全部改动，重点复核申请文档"二、专家意见闭环整改对照清单"中的 P0×3、P1×6、P2×2 共 11 项声明。

---

## 一、结论（先说结果）

**不予 L3 SCENARIO-VERIFIED / PG-2 准入，且当前状态也不满足 PG-1 的"P0/P1 为零"门槛**（`MACAO_REVIEW_GUIDELINES.md` §PG-1 定义）。

原因：申请文档列出的 11 项 P0/P1/P2 整改经独立复核 **全部属实、真实闭环**（见第二节）——这是一次高质量的整改，工程团队认真回应了四方专家意见。但在复核过程中，我独立发现了 **1 项新的 P0 级缺陷**：`message_id` 生成算法的碰撞概率过高，导致 `message_queue` 主键唯一性约束在正常使用下即会随机触发 `sqlite3.IntegrityError` 崩溃——这直接证伪了申请文档反复强调的核心机验证据"**38/38 测试 100% PASS**"（该数字只在约 3/4 的运行中成立，见第三节的可复现实测）。按照本项目一贯的评审文化（`906b17e` 轮 codex/claude/zcode 均将"申报证据与实测不符"定为 P0），此问题应归类为新 P0，而非 P1。

---

## 二、专家意见闭环整改对照清单——逐项独立复核结果

| 编号 | 申请文档声明 | 独立复核方法 | 结论 |
|---|---|---|---|
| P0-1 配置注入键路径 | `ConfigManager.to_runtime_config()` 统一展平；Orchestrator/MergeController 从单一真理源读取；`require_signoff=True` 时无签字 Fail-closed | 读 `core/config.py:53-92`、`workflow/orchestrator.py:57-91,374-391`；跑 `test_p0_p1_rectification.py::test_config_keys_penetration_and_require_signoff_fail_closed`（PASS）；人工构造 `require_human_signoff: true` 配置并调用 `execute_merge` 验证确实返回 `False, "Human signoff required..."` | **✅ 属实**。`Orchestrator.__init__` 现在正确读取 `merge_policy.get("require_human_signoff", True)` 等嵌套键，且默认值本身是安全的（fail-closed 默认 `True`）。|
| P0-2 E2E 证据真实度 | 注入真实 3 个 Reviewer Adapter；`votes_yes=3, effective_votes=3`；归档路径修正为 `<checkpoint_ref>/r1/` | 读 `e2e_runner.py:105-122,243-249,278-280`；读 `consensus/engine.py:43-51`（`breakdown` 同时含 `approve`/`yes_approve`/`effective_votes`）；读 `workflow/fsm.py:85,100`（归档路径确认为 `.macao/archive/{checkpoint_ref}/r{round}`，与 runner 检查路径一致）；实跑 `python3 -m macao.cli.main e2e-run` 两次，均得到 `votes_yes=3, effective_votes=3`, `Archived 5 files` | **✅ 属实**。`MockAgentAdapter` 实例被真实传入 `Orchestrator(executor_adapter=..., reviewer_adapters=...)`，其 `agent_id` 列表驱动了 `reviewer_ids`/审阅白名单（`orchestrator.py:270-272` 的 `allowed_revs` 不再是空集合导致的"未过滤"状态）。见第四节 D 项关于产物内容仍绕开 Adapter 的补充说明（非阻断项）。|
| P0-3 沙箱边界定性 | `types.py`/`base.py`/`POC_VERIFICATION_REPORT.md` 改为"工作目录与 Git Worktree 物理隔离（Process-isolated）"，容器隔离标注为 Phase 3 规划 | 读 `core/types.py:74`：`SANDBOXED = "sandboxed"  # Worktree and working directory isolation (Process-isolated; Container namespaces planned for Phase 3)` | **✅ 属实**。不再暗示 OS 级容器沙箱。|
| P1-2 MergeController non-git 逃生舱 | 彻底移除模拟成功分支 | 读 `merge/controller.py:54-57`：非 git 目录直接 `return False, "...not a valid git repository (Fail-closed)"`；跑 `test_merge_controller_non_git_fail_closed`（PASS） | **✅ 属实**。|
| P1-3 Worktree 静默 mkdir 降级 | 非 git 目录直接 `RuntimeError` | 读 `utils/git_utils.py:95-98`；跑 `test_git_utils_fail_closed_and_no_dummy_data`（PASS） | **✅ 属实**。|
| P1-4 硬编码回退值 | 消除 `cc-glm`/`kimi`/`cc-ds4` 硬编码 | 读 `orchestrator.py:64-75`：默认回退改为 `["codex","opencode","antigravity"]`（与真实适配器矩阵一致），且优先从注入的 `reviewer_adapters`/`config.reviewers` 动态派生 | **✅ 属实**。|
| P1-5 PTY 跨平台探测 | `HAS_PTY` 检测 + 非 POSIX 优雅 SKIPPED | 读 `adapter/integ_harness.py:11-15,59-67` | **✅ 属实**（代码路径合理；本机为 Linux，无法在 Windows 上实测，但逻辑正确）。|
| P1-6 `get_changed_files` 伪造数据 | 失败时返回 `[]` | 读 `utils/git_utils.py:65-84`（返回类型从 `List[str]` 改为 `List[Dict]`，同时确认调用方 `context_builder.py:68-75` 已同步适配，未破坏消费方）；跑 `test_git_utils_fail_closed_and_no_dummy_data`（PASS） | **✅ 属实**。|
| P2-5 DTO/枚举收敛 | 删除 `types.py` 中重复 `AEPEnvelope`；`OpinionStatus` 对齐 | `grep AEPEnvelope` 确认仅 `msg/envelope.py` 定义；`core/types.py:42-46` 确认 `OpinionStatus = {APPROVED, CHANGES_REQUESTED, REJECTED}` | **✅ 属实**。|
| P2-6 完整 SHA 校验 | `MergeController` 硬校验完整 40 位 SHA | 读 `merge/controller.py:86-89`：`resolve_ref()` + `head_commit != full_checkpoint_ref` | **✅ 属实**（此前一轮已具备，本轮维持）。|

此外确认一项文档层面的进步：本轮申请文档已将目标等级正确命名为 **L3 SCENARIO-VERIFIED**（对照 `MACAO_REVIEW_GUIDELINES.md` §61），修正了上一轮"L3 INTEGRATED"的术语误用（我在 `2026-08-28-review-result-906b17e-claude.md` F3 中提出的问题）。

---

## 三、新发现（P0）：`message_id` 生成碰撞导致 `message_queue` 主键冲突崩溃

### 3.1 复现过程

```bash
$ for i in 1 2 3; do PYTHONPATH=src python3 -m unittest discover tests 2>&1 | tail -5; done
=== RUN 1 ===  Ran 38 tests in 7.436s  OK
=== RUN 2 ===  Ran 38 tests in 7.276s  OK
=== RUN 3 ===  Ran 38 tests in 7.642s  OK
```
但在评审过程中首次运行（第 4 次）实测得到：
```
ERROR: test_scenario_s2_rework_loop (test_orchestrator_sim.TestOrchestratorSimulation.test_scenario_s2_rework_loop)
Traceback (most recent call last):
  File ".../src/macao/workflow/orchestrator.py", line 231, in dispatch_review_requests
    self.msg_bus.publish(...)
  File ".../src/macao/msg/bus.py", line 39, in publish
    conn.execute(...)
sqlite3.IntegrityError: UNIQUE constraint failed: message_queue.message_id

Ran 38 tests in 7.433s
FAILED (errors=1)
```

即申请文档反复引用的"**38 / 38 项自动化测试 100% PASS**"这一核心证据，在我本次独立复现中，4 次连续运行里出现 1 次崩溃——**并非确定性绿色，而是一个约 20~25% 概率随机失败的 flaky 套件**。

### 3.2 根因

`src/macao/msg/envelope.py:17-20`：
```python
@classmethod
def generate_message_id(cls) -> str:
    date_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d")
    rand_suffix = str(uuid.uuid4().int)[:4].zfill(4)
    return f"msg-{date_str}-{rand_suffix}"
```
`message_id` 格式为 `msg-YYYYMMDD-XXXX`，其中 `XXXX` 仅取自 UUID4 整数值的前 4 位十进制数字——**同一自然日内只有约 10,000 个可能取值**。而 `src/macao/storage/db.py:64` 中 `message_queue.message_id` 定义为 `PRIMARY KEY`（唯一约束）。

单次 `python3 -m unittest discover tests` 全量跑下来，仅 `test_orchestrator_sim.py`/`test_p0_p1_rectification.py`/`test_e2e_phase2.py` 等测试用例合计即会发布数十条 AEP 消息（`DEVELOPMENT_STARTED`、`REVIEW_REQUEST` × N reviewer、`REWORK_REQUEST`、`HUMAN_OVERRIDE_REQUEST`、`MERGE_COMPLETED`、`OVERRIDE_RESOLVED` 等）。按生日悖论估算，同一天内发布 ~30-50 条消息、10,000 个桶的碰撞概率约为 4%~12% 每次全量测试运行；加上本机同一天内已运行多轮（含人工 `e2e-run`/`test-clis` 调用），实际碰撞概率会随当日累计消息数进一步升高——与实测的 1/4 崩溃率量级吻合。

### 3.3 为什么定为 P0 而非 P1

1. **直接证伪申请文档的核心机验证据**："38/38 100% PASS" 被写入申请文档标题、第一/五节共 3 处，作为 L3/PG-2 准入的首要支撑材料；但该断言在正常复现条件下不成立，属于"申报证据与独立实测不符"——这是本项目历次评审（含 `906b17e` 轮 codex/zcode 的 P0 判定）一贯采用的最高严重级别归类标准。
2. **不是测试专属问题，是生产数据完整性缺陷**：`MessageBus.publish()` 是 Orchestrator 每次状态流转都会调用的核心路径（`start_task`/`dispatch_review_requests`/`collect_and_evaluate_consensus`/`execute_merge`/`resolve_override` 均会发布 AEP 消息）。真实项目运行一天、消息量增长后，同样会在生产环境随机触发 `IntegrityError` 导致任务流转崩溃，而非仅在测试里出现。
3. `PG-1` 门禁定义为"L2 + P0/P1 为零"（`MACAO_REVIEW_GUIDELINES.md` §71）——本发现意味着当前 commit 甚至不满足既有 PG-1，遑论申请的 PG-2。

### 3.4 建议修复

`generate_message_id()` 应使用完整 `uuid.uuid4().hex`（或至少 8~12 位十六进制/十进制随机后缀）保证足够的碰撞空间，并建议补充一条回归测试：在同一进程内快速连续调用 `MessageBus.publish()` O(1000) 次断言无 `IntegrityError`。

---

## 四、非阻断性遗留观察（供下一轮参考，均未被本轮申请文档声明为已闭环，不构成"申报不实"）

**A. ANSI Strip 校验仍是橡皮图章。** `adapter/integ_harness.py:108-109`：
```python
clean_logs = session.get_clean_logs()
ansi_stripped_ok = True
```
`clean_logs` 被获取后未做任何断言（既不检查非空，也不检查是否含残留 ANSI 转义序列），`ansi_stripped_ok` 无条件为 `True`。这比上一轮的弱校验（`len(logs_captured) > 0 or process.poll() == 0`）更彻底地不做任何验证。`macao test-clis` 报告中的"ANSI Strip ✓ YES"列因此对任何 CLI 都恒为 YES，不具备鉴别力。建议下一轮改为实际断言 `clean_logs` 中不含 `\x1b[` 等转义序列。

**B. 新增 Adapter 的 `ack()` 仍是空桩。** `adapter/opencode.py:85-86`、`adapter/antigravity.py:85-86` 的 `ack(message_id) -> bool: return True` 从未调用 `MessageBus.ack()`，未接入本轮宣称的"`message_deliveries` 独立投递"机制。此为上一轮我的 F4 发现的延续，本轮未声明修复，故不计入不实申报，仅供留档。

**C. E2E 产物内容生成仍绕开 Adapter 抽象。** `e2e_runner.py:172-195,225-240` 中 `.dev.yml`/`*.review.yml` 的具体内容仍由脚本直接 `yaml.safe_dump()` 手工构造字典写入，并未调用 `MockAgentAdapter.simulate_produce_dev_manifest()` / `simulate_produce_review_manifest()`（`adapter/mock.py:76-162` 中已存在的、专为此设计的方法）。P0-2 修复真实解决的是"审阅者身份/白名单是否来自真实 Adapter 对象"这一层（已验证为真），但"产物内容是否经由 Adapter 接口产生"这一层仍是手工绕过。建议后续申请措辞避免使用"Adapter 驱动生成产物"这类可能被解读为覆盖内容层的表述。

**D. `git diff --check` 仍不干净，但范围已显著收窄。** 复测 `git diff --check 906b17e e7ba2d2` 与 `e7ba2d2 afc85e0`，尾随空白仅出现在 `docs/*.md` 文档文件（如 `POC_VERIFICATION_REPORT.md:25`、本轮及上轮申请文档自身），**src/ 与 tests/ 下代码已完全干净**。相比上一轮，这已是真实收敛，仅剩纯文档格式问题，不影响功能，非阻断项。

---

## 五、正向确认（复核后仍成立，未被本轮改动破坏）

- 10 状态 FSM 与 `TransitionTable.can_transition` 白名单机制维持正确；
- Deadlock "HOLD + 不写 vote_result.json" 分支（`orchestrator.py:342-370`）维持正确；
- Worktree 创建 fail-closed（本轮进一步移除了残余的 mkdir 降级路径，见 P1-3）；
- `test_p0_p1_rectification.py` 新增的 4 个用例断言的是真实字段值（`votes_yes==3`、`reviewers==[...]`、`archived_count>=4` 等），而非仅检查 `status=="PASS"` 这类肤浅断言——这是对我上一轮 F1 发现（"浅层测试导致假绿"）的实质性正面回应，方法论上值得肯定。

---

## 六、准入建议

**暂不批准 L3 SCENARIO-VERIFIED / PG-2**，且建议 STATUS.md 将本轮登记为"11/11 项既有 P0/P1/P2 已闭环，但独立评审新发现 1 项 P0（`message_id` 碰撞），故仍未达 PG-1 零 P0/P1 门槛"，而非笼统的"整改未通过"——以准确反映本轮工程团队的真实进展（这是一轮高质量、可验证的整改，唯一缺口是一处此前从未被任何一方专家提及的新缺陷）。

**放行条件**（预计工作量小，建议可在一轮内closed）：
1. 修复 `AEPEnvelope.generate_message_id()` 的碰撞问题（改用完整 `uuid4().hex` 或等效方案）；
2. 补充一条针对该问题的回归测试（高频连续 `publish()` 无 `IntegrityError`）；
3. （可选，非阻断）修正第四节 A 项的 ANSI Strip 橡皮图章校验，使报告中的该列真正具备鉴别力。

其余 11 项 P0/P1/P2 整改经独立复核 **予以确认，全部属实**，无需返工。
