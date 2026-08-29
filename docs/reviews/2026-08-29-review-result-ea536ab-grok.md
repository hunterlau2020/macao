# MACAO 独立复审报告 — L3 全量阻断项闭环申请 (commit `4df059e..ea536ab`)

> **评审人**：grok（独立复审，不采信申请文档或其他专家报告的结论；逐条重读源码 + 独立重跑命令 + 编写复现脚本）
> **评审日期**：2026-08-29
> **评审对象**：[`2026-08-29-review-request-L3-All-Items-Closed.md`](2026-08-29-review-request-L3-All-Items-Closed.md)
> **评审范围**：`git diff 4df059e..ea536ab`（代码提交 `ea536ab`，另含 3 份 STATUS/专家报告登记提交），重点复核申请清单 REQ-TIMEOUT、P0-1、P0-2、P0-3、P1-1、P1-2、P2-1、P2-2。
> **对齐基准**：`docs/MACAO_PRD_v2.md` v2.3.1、`docs/MACAO_REVIEW_GUIDELINES.md` v1.0、`docs/schemas/*.schema.json`

---

## 一、结论

**不予 L3 SCENARIO-VERIFIED / PG-2 准入。**

申请所列 8 项中，**6 项安全/正确性主张经独立复放属实**（高熵 `task_id`、max-round 不提前写盘、脏工作区拒绝合并、Worktree 物理清理、`register_artifact` 生产调用点恢复、vote 先校验后写盘 + 非法 `human_resolution` fail-fast）。本轮整改质量与历轮一致：针对性单点修复 + 专项回归，没有虚报"测过了"却不存在的测试函数。

但作为 **L3 唯一新增判据** 的 REQ-TIMEOUT，独立复放证明它只做到了"调用方传入超时名单后，共识层会 HOLD 并发接管请求"，**没有做到 PRD 要求的"超时弃权记入终局 `vote_result.json`"**；而申请引用的 `test_reviewer_timeout_degradation_scenario` **并不断言 ABSTAIN**——在合成弃权逻辑被删掉时该测试仍会 PASS。按本项目一贯标准（申报证据与权威产物不一致、测试无法捕获所声称行为），这构成对 L3 超时场景的 **PARTIALLY_VERIFIED**，并登记为新 P1。

GUIDELINES §2.2：PG-1 要求 P0/P1 为零，PG-2 以 PG-1 为前提。因此本轮不能授予 L3 / PG-2。

---

## 二、申请清单逐条独立复核

| 编号 | 申请声明 | 独立复核方法与结果 | 判定 |
|---|---|---|---|
| **REQ-TIMEOUT** | Reviewer 超时未响应 → 标记弃权 → 法定人数不足死锁 → 人工接管全链路 | 读 `orchestrator.py:317,345,373-388,396-417`：超时完全依赖调用方传入 `timed_out_reviewers`；全仓库仅测试调用该参数，CLI/`e2e_runner` 从不传入。独立脚本：1 张 YES + 注入 `opencode` 超时 → `change is None`、磁盘无 `vote_result.json`、状态 `CONSENSUS_CHECK`、审计含 `REVIEWER_TIMEOUT_ABSTAIN`/`DEADLOCK_DETECTED`、消息含 `HUMAN_OVERRIDE_REQUEST`（以上属实）。随后 `resolve_override(APPROVED)` 写出的终局 `vote_result.json` 仅含 `codex/YES_APPROVE`，**`abstain_in_final=[]`，`reviewers_responded=1`**，与 PRD §2.2 / §3.3「弃权随 E7 终局 `vote_result.json` 一并落盘」矛盾。该测试只断言 `change is None` + HOLD + 消息类型，**不断言审计事件、不断言 ABSTAIN 票面**；`ConsensusEngine.evaluate([1×YES], N=2)` 本身就会 DEADLOCK，因此合成弃权若是空操作测试仍绿。 | **PARTIALLY_VERIFIED**（见 §三 P1-NEW-1） |
| **P0-1** | `task_id` 引入 UUID 后缀，同秒 100 任务 0 碰撞 | 读 `orchestrator.py:111-113`：`task-{YYYYMMDDHHMMSS}-{uuid4.hex[:6]}`。独立创建 100 个任务，样例 `task-20260829035341-4c25a8` / `...-1ed1a6` / `...-ab9f2d`，100/100 唯一。无 IntegrityError 重试（残留 P3）。 | **✅ VERIFIED** |
| **P0-2** | 达到 `max_rework_rounds` 时不写盘、HOLD、崩溃恢复仍 `CONSENSUS_CHECK` | 读 `orchestrator.py:419-441`：`REWORK_REQUIRED and rnd >= max_rnd` 时 publish `HUMAN_OVERRIDE_REQUEST` 后 `return None, None`，位于 `generate_vote_result(..., write_to_disk=True)` 之前。独立复放：`disk_exists=False`，reconcile 后仍为 `CONSENSUS_CHECK`，接管消息已发布。 | **✅ VERIFIED** |
| **P0-3** | 工作区未提交已跟踪修改时 Fail-closed，不破坏用户数据 | 读 `merge/controller.py:60-64`：`git diff --name-only` + `git diff --cached --name-only`。独立三变体：unstaged 拒绝且 `USER UNCOMMITTED WORK` 保留；staged 拒绝且内容保留；**untracked 未拦截**，流水线进入 CI，失败信息为 CI 而非脏树守卫（untracked 文件本身未被 `reset --hard` 删除）。流水线仍在用户工作区执行 `reset --hard`（脏检查通过后的 TOCTOU 残留 P2）。针对 Codex 原复现（已跟踪未提交被覆盖）已关闭。 | **✅ VERIFIED**（原数据丢失路径）；untracked/专用 worktree 见 P2 |
| **P1-1** | `remove_isolated_worktree` 存在且失败时物理清理 | 读 `git_utils.py:109-121`：方法存在，转调 `worktree remove --force` + `rmtree`。独立故障注入：第 2 个 reviewer 失败后 `rev1_exists=False`，`git worktree list` 仅剩主工作区，FSM 保持 `READY_FOR_REVIEW`。 | **✅ VERIFIED**（关闭 claude 在 `4df059e` 轮发现 A） |
| **P1-2** | 生产路径恢复 `register_artifact`，E2E 后 artifacts 表有 5 份 | 读 `orchestrator.py:199-205,355-362,455-461,591-597`：三处调用点属实。独立跑完整 E2E：表内 **5 行**（1 dev + 3 review + 1 vote），happy-path 不再为空。但 **5 行 `sha256` 全空**（未传 `content=`）；3 份 `review_manifest` 的 `consumed=0`、`archived_path=null`——`fsm.py:111` 用 `rev_file.stem`（`codex.review`）去匹配注册时的 `reviewer_id`（`codex`），UPDATE 影响 0 行。申请测试只断言 `kind` 存在、`len>=4`，不捕获消费语义。 | **✅ 注册路径 VERIFIED**（关闭 claude 在 `4df059e` 轮发现 B）；消费/哈希见 P2-NEW |
| **P2-1** | `validate_vote_result` 先于写盘 | 读 `vote.py:174-183`：DEADLOCK 早退；否则先 `validate_vote_result` 再写盘。 | **✅ VERIFIED** |
| **P2-2** | 非法 `human_resolution` fail-fast | 读 `vote.py:129-132`：未知值抛 `ValueError`。独立传入 `INVALID_UNRECOGNIZED_ACTION`：异常信息匹配，磁盘无文件。 | **✅ VERIFIED** |

---

## 三、本轮新发现

### P1-NEW-1：超时弃权未写入 E7 终局 `vote_result.json`；专项测试无法证伪「未标记弃权」

PRD §2.2：「弃权票仅由 Orchestrator 在超时降级时写入 `vote_result.json`」。PRD §3.3 超时行：「弃权标记由 Orchestrator 记入本轮票面，**随 E7 终局 `vote_result.json` 一并落盘**」。

实测终局产物（独立脚本，人工裁定 APPROVED 之后）：

```text
votes = [{reviewer: codex, vote: YES_APPROVE}]
abstain_in_final_vote_result = []
reviewers_responded = 1
decision = APPROVED
resolution = human_override
```

根因：`collect_and_evaluate_consensus` 把超时 ABSTAIN 只放进内存 `votes_list` 做死锁判定（`orchestrator.py:373-388`），DEADLOCK 分支不写盘（正确）；但 `resolve_override`（`orchestrator.py:578-588`）再次 `collect_reviews` 时只收集磁盘上的 `.review.yml`，**不会把已审计的超时弃权重新注入** `generate_vote_result`。

专项测试盲区：`test_reviewer_timeout_degradation_scenario` 不断言 `REVIEWER_TIMEOUT_ABSTAIN`、不断言票面含 `ABSTAIN`。对 2-reviewer 配置，1 张 YES 本身就会因有效票 < 法定人数进入 DEADLOCK（`engine.py:54-55`）。因此「标记弃权」这一申请标题中的关键动词，**没有被该测试约束**。

另：生产路径从未传入 `timed_out_reviewers`（`cli/main.py` 甚至没有调用 `collect_and_evaluate_consensus` 的命令；`e2e_runner.py:232` 亦不传）。无时钟、无 §6.1 的 ping / 「Mark as abstain?」人工确认。此项降为伴随观察（P2），不单独作为本轮阻断；**阻断点是权威产物与 PRD 及申请声称不一致**。

**放行条件**：

1. `resolve_override`（及任何 E7 写盘路径）必须把本轮已审计的超时弃权写入终局 `vote_result.json` 的 `votes`（`vote=ABSTAIN`），`reviewers_responded` / `vote_breakdown.abstain` 与之一致；
2. 回归测试必须正向断言：审计事件 `REVIEWER_TIMEOUT_ABSTAIN`、终局票面含对应 reviewer 的 ABSTAIN、在去掉合成弃权逻辑后测试失败。

### P2-NEW-1：`review_manifest` 注册后从未被标记 consumed（`stem` vs `reviewer_id` 错配）+ 全部产物 `sha256` 为空

E2E 后 `macao status` 将显示 3 份 review 产物 Consumed=NO，尽管磁盘归档目录里文件已存在。`register_artifact(..., content=)` 从未传入字节，哈希列恒为空字符串，无法做双账本对账。建议：`mark_artifact_consumed` 使用 YAML 内 `reviewer.id`（或注册时的同一字段）；注册时读盘计算 sha256。

### P2-NEW-2：超时降级没有运行时触发源

`timed_out_reviewers` 是纯注入 API。L3 要的是场景证据而非完整 OPS 时钟，故不升为 P1；但 PG-2「消费方接口稳定」仍缺 deadline 扫描 / CLI 入口。补 fake-clock 或明确文档化「超时名单由外部调度注入」均可。

### P2-NEW-3：脏树守卫不覆盖 untracked；合并仍在用户工作区 `reset --hard`

untracked 变体独立复放：守卫放行，CI 失败后走 `reset --hard`。untracked 文件未被删除，故不构成 P0 数据丢失，但未满足 Codex 原修复要求中的 untracked 策略与专用 worktree。

### 历史未闭环（非本轮声明范围，独立复确认仍开放，不计入本轮「虚报」）

- **签字未绑定 checkpoint**（Codex 上轮 P1-5）：独立写入旧 SHA 的 `HUMAN_MERGE_APPROVED` 后，对新 checkpoint 执行合并 → `ok=True`。建议升留 P1 待下轮，但因不在本申请闭环清单内，本报告不把它当作申请方虚报。
- E2E 仍把 `.review.yml` 写到主仓库 `.macao/.reviews/`，Worktree 内 0 份评审产物。AEP `isolated_worktree_path` 三路径均真实存在（Codex 上轮 P0-4 的「路径不存在」假阳性已消除），消费模型仍未闭环，作 P2 跟踪。
- `integ_harness.py:109` `ansi_stripped_ok = True` 仍为常量；真实 Adapter `get_logs(tail_lines)` 仍调用无参 `PTYSession.get_clean_logs()`。
- `get_schemas_dir()` 向上遍历（Qwen R1）本轮未触及。

---

## 四、机验记录（本机 Linux，不采信申请粘贴输出）

| 项目 | 结果 |
|---|---|
| `PYTHONPATH=src python3 -m unittest discover tests -v` | **49/49 OK**（11.805s） |
| 连续再跑 ×2 | **49/49 OK** ×2（11.204s / 11.001s），0 flake |
| `python3 -m macao.cli.main e2e-run` | 7 步 OK；`votes_yes=3, effective_votes=3`；Archived 5 files；终态 DONE；task_id 已带 6 位后缀（`task-20260829035538-33cad5`） |
| `git diff --check 4df059e..HEAD` | `docs/POC_VERIFICATION_REPORT.md:25` 仍有尾随空白（申请 §二.5 跑的是裸 `git diff --check`，只证明工作区干净） |
| `src/` `tests/` 范围 `git diff --check 4df059e..HEAD` | 干净 |
| 独立复现脚本 | 见第三节；超时终局票面无 ABSTAIN、artifacts 5 行但 3 份 review 未 consumed、Worktree 失败后物理目录消失、脏树 unstaged/staged 拒绝、max-round 不写盘，均可复现 |

未在本轮重跑 `macao test-clis`（与申请清单无增量关系；PTY 假阳性代码本轮未改）。

---

## 五、申请文档需修正的声明

1. 「全部阻断项已全部单点闭环」过宽。Codex 上轮 P0-4（Worktree 内产物/从 MessageBus 消费）与多条 P1（ACK、签字绑定 checkpoint、归档消费语义、PTY 合同）不在本清单且多数仍开放。应改为「本清单 8 项」而非「四方提出的全部阻断项」。
2. REQ-TIMEOUT 写成「标记弃权」缺少对终局 `vote_result.json` 的证据；现有测试不能支撑该动词。
3. 「5 份产物」在物理归档层属实，在 SQLite 消费语义层对 3 份 review 不属实。
4. 代码洁净度请使用 `git diff --check <base>..<head>`，不要用裸 `git diff --check`。

---

## 六、准入建议

**暂不批准 L3 SCENARIO-VERIFIED / Process Gate 2 (PG-2)。**

claude 在 `4df059e` 轮提出的 2 项 P1（Worktree 孤儿清理、artifacts 表永久为空）**均已真实闭环**。P0 级数据丢失（脏工作区 `reset --hard`）与 max-round 恢复绕过亦已关闭。距离 L3 的剩余阻断是 **超时场景的权威产物与测试断言**，不是再发现一类全新架构缺陷。

**建议闭环（预计仍可一轮内完成）**：

1. **必须（P1）**：E7 终局 `vote_result.json` 写入超时 ABSTAIN；测试正向断言弃权票面，并保证去掉合成逻辑后失败。
2. **建议随手（P2）**：`mark_artifact_consumed` 的 reviewer 键对齐；注册时写入 sha256；脏树守卫明确 untracked 策略。
3. 完成 (1) 并经任一面审书面确认后，本人支持授予 L3 / PG-2（历史未修 P1 如签字绑定 checkpoint 须在 STATUS 中显式降级或列入已知限制，不得再写「全部阻断项已闭环」）。

---

## Reviewer 自审记录

- 本报告未采信申请文档或其他专家结论作为证据；清单 8 项均经源码行号 + 独立脚本或命令复放。
- 重点检查了申请测试未断言的物理副作用：终局 `vote_result` 票面、artifacts 的 `consumed`/`sha256`、`git worktree list`、untracked 脏树、旧签字跨 checkpoint。
- 本轮先读全量 `4df059e..HEAD` diff，再写反例脚本，避免只复核「清单内测试是否绿」。
- 未覆盖：真实 CLI PTY、真实远端 push、Windows。
