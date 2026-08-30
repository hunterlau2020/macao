# MACAO 独立复审报告 — L3 / PG-2 全员一致终局定级封板申请 (commit `8296f3c`)

> **评审人**：grok（独立复审；不采信申请文档粘贴输出，亦不采信工作区中其他专家对 `8296f3c` 的未入库结论；逐条重读源码 + 独立重跑命令 + 临时仓库故障注入）
> **评审日期**：2026-08-30
> **评审对象**：[`2026-08-30-review-request-L3-PG2-Unanimous-Seal.md`](2026-08-30-review-request-L3-PG2-Unanimous-Seal.md)
> **冻结代码提交**：`8296f3cc8403759ce85d18e310ba5bced30e18f2`（短 SHA `8296f3c`）
> **冻结差异范围**：申请写作 `3ea5256..HEAD`；`HEAD` 是移动引用，本报告钉死为 `3ea5256..8296f3c`（1 个 commit）
> **对齐基准**：`docs/MACAO_PRD_v2.md` v2.3.1、`docs/MACAO_REVIEW_GUIDELINES.md` v1.0、`docs/schemas/*.schema.json`
> **证据类型**：DOC / SPEC / CODE / TEST / SIM / OPS

---

## 〇、Reviewer 自审

本对话中 grok 对 MACAO 的上一份正式结论是 `bf5ae2d` 的 **P1-NEW-8**（E9 超时处置跨代际活锁）。本申请是 grok 对本轮封板材料的**首次**评审。

按指引 §9 激活：

- **A**：字段声明 vs 实际读取——PRD 写「新 commit」，实现只做字符串 `!=` 与 `commit_exists`，未读 git 拓扑。
- **B**：`[x]` / 「已闭环」≠ 完成证据——申请把 Codex P1-1 写成已关闭，但未覆盖祖先回退 / 无关分支。

强制自检：不把「仓库新增单测绿了」当成「声称的不变式已穷尽」；对每个「新 commit」声明都补一条**非后继**反例。该自检直接命中 §三 P1-1。

本报告写就时工作区另有未跟踪的 `8296f3c-claude.md` / `8296f3c-codex.md`。二者**不是**冻结提交的一部分，**不计入**注册表，也**不作为**本结论的投票权重（指引 §8：真理不等于投票；沉默 ≠ 同意）。

---

## 一、结论

**不予授予 L3 SCENARIO-VERIFIED，亦不予授予 PG-1 / PG-2。维持 L2 SPEC-CODE-ALIGNED。申请标题中的「全员一致封板」在 grok 出具本报告前即不成立，且本报告为 REJECT。**

申请清单两项整改均有**局部**效果：E6 会拒绝与上一 checkpoint **完全相同**的 SHA，以及本任务已 `consumed` 的同 SHA `dev_manifest`；E9 源状态已收敛为仅 `CONSENSUS_CHECK`。65/65 单测、Mock `e2e-run`、真实 CLI `--version` PTY 冒烟、编译与 diff 洁净度均独立通过；冻结提交时 66 份 result / 14 份 request 与 STATUS **双向零差集**。

但 PRD §3.3 E6「新 commit」在本轮被实现成「SHA 字符串不同且对象存在」。独立临时仓库中，round 1 checkpoint = B、状态 `REWORK` 时提交**未消费的祖先 A**，或提交**与 B 无祖先关系的孤儿 commit**，系统均接受并倒退/改写 `checkpoint_ref` 进入 `READY_FOR_REVIEW`。这与「返工必须产生新工作」同类，且正是本轮声称关闭的 P1-NEW-12 / Codex P1-1 的剩余分支。仓库新单测只覆盖相同 SHA 拒绝与直接后继接受。

指引 §2.2：PG-1 / PG-2 **不可豁免 P0/P1**。现存 1 项 P1，门禁不能放行。

---

## 二、申请清单逐条独立复核

| 编号 | 申请声明 | 独立复核方法与结果 | 判定 |
|---|---|---|---|
| **P1-NEW-12 / Codex P1-1** | `REWORK` 下 `latest_commit != checkpoint_ref`；已消费同 SHA `dev_manifest` 一律拒绝 | 读 `orchestrator.py:236-254`：仅字符串不等 + `list_artifacts` consumed 过滤 + `commit_exists`。`git_utils.get_merge_base` 存在，但 E6 **未**调用 `merge-base --is-ancestor`。新单测 `test_rework_unchanged_commit_fails_closed_and_requires_fresh_commit`（`tests/test_p0_p1_rectification.py:1511-1622`）只断言相同 SHA → `None`、后继 SHA → `READY_FOR_REVIEW`。独立临时仓库：相同 SHA **拒绝**；已消费祖先 **拒绝**；**未消费祖先与无关孤儿均接受**（见 §三）。 | **⚠️ PARTIALLY_VERIFIED**（相同 SHA / 已消费 / 后继 ✅；拓扑「新」❌） |
| **Codex P2-1** | `E9` 源状态唯 `CONSENSUS_CHECK` | 读 `transitions.py:48-51`。十状态矩阵：仅 `CONSENSUS_CHECK → WAITING_REVIEW` 为 True；`UNKNOWN` 上 E9 为 False。`E7` 仍允许 `UNKNOWN → MERGING`（登记 P3，不阻断本项）。 | **✅ VERIFIED**（附 P3-1） |

### 机验清单（不采信申请粘贴输出）

| # | 声明 | 本机实测 | 状态 |
|---|---|---|---|
| 1 | 全量 65 项 PASS | `Ran 65 tests in 15.646s OK`；另跑一轮 `15.305s OK`（共 2×65，0 flake）。**未**按申请复放 5 轮。 | ✅ 属实方向；5 轮为 PARTIALLY_VERIFIED |
| 2 | `compileall -q src` 与 `git diff --check` | `compileall` RC=0；`git diff --check 3ea5256..8296f3c` RC=0 | ✅ |
| 3 | `macao test-clis` 4/4、0 僵尸 | claude 2.1.251 / codex 2.1.0 / opencode 1.18.25 / agy 1.1.22 均 PASS，`✓ DEAD (0 Zombie)`。命令均为 `--version`。ANSI 列证据强度见 P2-2。 | ✅（冒烟 VERIFIED；ANSI PARTIALLY_VERIFIED） |
| 4 | `macao e2e-run` 7/7、DONE | 7 步 OK，终态 `DONE`，`decision=APPROVED`，`votes_yes=3`。Mock Adapter happy path。 | ✅（Mock E2E VERIFIED） |
| 5 | 注册表 66 result + 14 request，与 STATUS 100% 对账 | `git ls-tree -r HEAD docs/reviews`：**66** / **14**；从 STATUS 抽出的文件名与 HEAD 受控文件**双向零差集**。 | ✅（冻结提交时） |

独立故障注入摘要（临时 git + 临时 SQLite，脚本事后删除，未污染本仓库业务状态）：

```text
e6_same_sha            accepted=False  state=REWORK
e6_ancestor            is_ancestor=True  sha_equal=False  accepted=True
                       transition=READY_FOR_REVIEW  checkpoint 倒退到祖先
e6_unrelated           orphan SHA  accepted=True  checkpoint 改为孤儿
e6_successor           accepted=True  is_descendant=True
e6_consumed_ancestor   accepted=False  state=REWORK
e9_unknown             False
e9_true_sources        [CONSENSUS_CHECK]
e9_stale_restore       E9 后目录为空；写回第一代 REJECTED + 新 YES
                       → CONSENSUS_CHECK / decision=None（作废票仍参与）
timeout_without_driver state=WAITING_REVIEW  timeouts=0
partial_publish        E2 已 WAITING_REVIEW；仅 1 条 REVIEW_REQUEST；dev consumed=1
```

---

## 三、P0：必须先解决

本轮未发现需单列为 P0 的问题。

---

## 四、P1：进入 L3 / PG-1 / PG-2 前必须解决

### P1-1：E6「新 commit」未校验提交拓扑，未消费祖先或无关 SHA 可冒充返工产物

**验证状态**：CONTRADICTED

**证据**：

- DOC：`docs/MACAO_PRD_v2.md:831`「新 commit + round 匹配」；`:839` E6「round+1、**新 commit**」；`:216` `latest_commit`「存在于本地 git 历史且**未被消费过**」。三者合读：「新」不是「任意另一个存在的对象」。
- CODE：`src/macao/workflow/orchestrator.py:238-254` 在 `REWORK` 下只拒绝 `latest_commit == prev_ref`，再拒绝已消费同 SHA，再 `commit_exists`。不验证 `prev` 是 `latest` 的严格祖先，也不验证 SHA 属于任务 `source_branch`。
- TEST：`tests/test_p0_p1_rectification.py:1511-1622` 无祖先回退、无无关分支、无孤立 commit。
- SIM（本评审人，临时仓库 A→B）：

```text
previous=B  submitted_ancestor=A  is_ancestor=True  sha_equal=False
→ accepted=True  to_state=READY_FOR_REVIEW  new_checkpoint=A

orphan side commit（与 B 无 merge-base 祖先关系）
→ accepted=True  checkpoint 改为孤儿 SHA
```

已消费祖先（round 1 用过 A 之后再提交 A）会被 `:243-249` 拦住——这只证明「未消费」闸有效，**不能**外推为「新 commit」闸有效。Executor 只要把 `latest_commit` 写成历史上任意未被本任务登记过的 SHA（含 init、其它功能分支），即可在零新工作的情况下离开 `REWORK`，后续评审与合并对象变成更旧或无关代码。

**验收标准**：

1. E6 在对象存在之外，验证上一 `checkpoint_ref` 是新 SHA 的**严格祖先**（例如 `merge-base --is-ancestor prev new` 成功且 SHA 不同），并拒绝无法从任务 source branch 解析的对象。
2. 测试至少覆盖：相同 SHA、未消费祖先回退、无关/孤儿 SHA、已消费 SHA、直接后继、多 commit 后继、崩溃重启后 consumed 记录仍拒绝。

---

## 五、P2 / P3：可延期但必须登记

下列项本轮 diff **未声称关闭**。本评审人做了有界独立复核，**不把它们升为与 P1-1 同等的封板唯一理由**，但也不因「别的专家已授予」而当作已关闭。

### P2-1：E9 作废仍只是 `unlink`，collector 不绑定派发代际 / message_id

PRD §3.3:841 要求作废本轮已收意见并重发带新 `message_id` 的 `REVIEW_REQUEST`。`review_manifest.schema.json` 无 generation / attempt / 响应 message_id；`VoteAggregator.collect_reviews` 只匹配 `checkpoint_ref + review_round`。

SIM：E9 后 `.reviews/` 为空（unlink 属实）；把第一代 `opencode` REJECTED 写回后再交新的 `codex` YES，状态进入 `CONSENSUS_CHECK` 且 `decision=None`（僵局）——说明作废票仍参与，而不是被隔离后只剩 1 张 YES、留在 `WAITING_REVIEW`。

建议：把不可变 attempt/message_id 贯通 request、manifest、collector；清理失败 fail-closed。在 P1-1 关闭前可延期，但 E9 场景不能称为完全 VERIFIED。

### P2-2：`test-clis` ANSI 列不是独立证据

`integ_harness.py:109-110` 对 **clean logs** 做正则；空日志也判 True。PASS 判定 `:131` 不要求 `ansi_stripped`。4/4 只证明 `--version` 进程生命周期。L4 前需要可控 ANSI fixture。

### P2-3：timeout 无生产 scanner；不调用 detector 则状态不前进

`src/` 无 timeout 后台循环；CLI 亦无轮询入口。`per_reviewer=0s` 派发后不调用 `collect`：状态保持 `WAITING_REVIEW`，timeout 审计 0。PRD `:849` 写明「超时不是独立的状态来源」，故 L3 允许测试里主动调用 detector；生产 driver 是 L4/OPS 缺口，记 P2 而非把 L3 超时场景判为不存在。

### P2-4：REVIEW_REQUEST fan-out 可部分提交

`dispatch_review_requests` 先 E2 / 归档 dev，再逐 reviewer `publish`。注入第二次 `REVIEW_REQUEST` 失败后：状态已 `WAITING_REVIEW`，队列仅 `codex` 一条，`dev_manifest consumed=1`。建议 outbox 或失败 HOLD。

### P2-5：`.macao/` 不被 `macao init` 写入 `.gitignore`

产品代码仅 `e2e_runner.py:46-47` 给**自己的沙箱**写 ignore。`cli/main.py` 的 `init` 只写 `macao.yaml`。下游 `git add -A` 会扫入 `state.db` 与嵌套 worktree。不造成错误状态转移，故 P2；PG-2「可被依赖」在工程接入上应先修。

### P2-6：真实 Reviewer Adapter 未消费 MessageBus envelope

`test-clis` = `--version`；`e2e-run` = Mock 自造 payload。协议消费方场景（Mock E2E）可作为 PG-2 的**部分**证据，不能外推为真实 CLI 评审闭环。L4 前至少一条真实 Adapter：envelope → 隔离 worktree → schema-valid manifest → ACK。

### P2-7（CODE，本轮未做注入）：push 成功而 `ls-remote` 失败时只 `reset` 本地

`merge/controller.py:123-134`：push 返回 0 后 `ls-remote` 失败则本地 hard reset 并返回失败，workflow 走 E4b。远端可能已前移。本轮未独立 stub，以静态阅读登记。

### P2-8（CODE）：artifact 唯一键无 generation，UPSERT 覆盖代际指针

`store.py:99-106` `ON CONFLICT DO UPDATE`；唯一键无 attempt。磁盘可留多代文件，ledger 每 reviewer 一行。审计完整性缺口，记 P2。

### P3-1：E7 仍允许 `UNKNOWN` 为源，E9 不允许

`transitions.py:43-51`。UNKNOWN 为死状态时运行时打不到，属表内口径不一致，不阻断。

---

## 六、交叉文档与申请书需做的文字修订

1. 申请与 STATUS 不得把 Codex P1-1 写成「全量闭环」；应写成「相同 SHA / 已消费已拦截；git 拓扑仍开放」。
2. 范围写作 `3ea5256..HEAD` 应改为钉死 SHA（本轮为 `8296f3c`）。
3. 「全员一致封板」在任一委员会成员 REJECT 或未表态时不得作为标题（指引 §8）。
4. 「5 轮 325 次」若要作为机验声明，评审人应能独立复放；否则改为「N 轮全量、0 flake」并给出 N。

---

## 七、L3 场景对账（GUIDELINES §2.1 / §6）

| 场景 | 本轮证据 | 状态 |
|---|---|---|
| 全同意 | 独立 `e2e-run`：3 YES，DONE | VERIFIED |
| 1:1 僵局 | E9 前置：YES+NO → `CONSENSUS_CHECK`，无自动票面 | VERIFIED |
| 超时 | 不调用 detector 则不前进（符合「非独立来源」）；主动 detector 路径沿用既有单测，本轮未重做时钟推进 | PARTIALLY_VERIFIED |
| 弃权 | 未本轮专项重放 | UNKNOWN（不升 P1：非本轮声明） |
| 崩溃恢复 | `test_reconcile_*` 在 65/65 中 PASS | TEST VERIFIED |
| 返工循环 | 相同 SHA / 已消费 / 后继 VERIFIED；**祖先回退与无关 SHA CONTRADICTED** | **CONTRADICTED** |

L3 要求适用 P0/P1 场景 SIM/TEST 为 VERIFIED。返工循环在本轮申请的核心不变式上 CONTRADICTED，故不能授 L3。

---

## 八、门禁判定

| 级别/门禁 | 判定 | 依据 |
|---|---|---|
| L1 DOC-ALIGNED | 保持既有 PRD v2.3.1 文档定级 | 本轮未重审四份设计文档全文 |
| L2 SPEC-CODE-ALIGNED | **维持** | E9 源状态已对齐；E6 拓扑与 PRD「新 commit」仍偏离；单测绿 |
| L3 SCENARIO-VERIFIED | **不通过** | 返工循环存在可复现 P1 反例 |
| PG-0 | 保持 | 绑定 L1 |
| PG-1 | **不通过** | P0/P1 非零（P1-1） |
| PG-2 | **不通过** | 继承 PG-1；消费方真实 Adapter 仅 PARTIALLY_VERIFIED |
| L4 / PG-3 | **不授予** | 不在申请范围；缺 OPS 与手册 |
| 「全员一致封板」 | **不成立** | 本报告 REJECT；标题不能代替未出齐的独立结论 |

---

## 九、建议闭环顺序与验收标准

1. **先关闭 P1-1**：E6 增加严格祖先（及 source branch）约束；补祖先 / 孤儿 / 后继 / 已消费测试。验收：本节 SIM 中 `e6_ancestor` 与 `e6_unrelated` 必须 `accepted=False` 且状态停在 `REWORK`；`e6_successor` 仍接受。
2. 再处理 P2-1（E9 代际身份）与 P2-4（fan-out 原子性），避免下一轮把 TOCTOU 再报成新 P1。
3. `macao init` 幂等写入 `.gitignore`（`.macao/`），或把 `state.db` / worktree 移出被评审仓库（P2-5）。
4. STATUS / 申请书按实际闸门重写，去掉「全员一致」「P1-1 全量闭环」等过宽句。

---

## 十、Known issues 登记

| issue_id | 严重度 | owner | due_date | resolution_commit | status |
|---|---|---|---|---|---|
| 8296F3C-P1-1 | P1 | Workflow / Git / Checkpoint | 下次 L3 申请前 | 待补 | OPEN |
| 8296F3C-P2-1 | P2 | Workflow / Protocol | 可延期 | 待补 | OPEN |
| 8296F3C-P2-2 | P2 | Adapter / PTY Test | 可延期 | 待补 | OPEN |
| 8296F3C-P2-3 | P2 | Workflow / Timeout | L4 前 | 待补 | OPEN |
| 8296F3C-P2-4 | P2 | Workflow / MessageBus | 可延期 | 待补 | OPEN |
| 8296F3C-P2-5 | P2 | CLI / init | 下游接入前建议修 | 待补 | OPEN |
| 8296F3C-P2-6 | P2 | Adapter / E2E | L4 前 | 待补 | OPEN |
| 8296F3C-P2-7 | P2 | MergeController | 可延期 | 待补 | OPEN |
| 8296F3C-P2-8 | P2 | Artifact ledger | 可延期 | 待补 | OPEN |
| 8296F3C-P3-1 | P3 | transitions E7/E9 | 可延期 | 待补 | OPEN |
