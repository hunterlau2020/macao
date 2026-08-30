# MACAO 独立复审报告 — L3 / PG-2 全员一致终局定级封板最终申请 (commit `4e38ed6`)

> **评审人**：grok（独立复审；不采信申请文档粘贴输出，亦不采信其他专家对 `8296f3c` / 本轮的结论；逐条重读源码 + 独立重跑命令 + 临时仓库故障注入）
> **评审日期**：2026-08-30
> **评审对象**：[`2026-08-30-review-request-L3-PG2-Unanimous-Final-Seal.md`](2026-08-30-review-request-L3-PG2-Unanimous-Final-Seal.md)
> **冻结代码提交**：`4e38ed662a255a8a84b92d1b8b8cdcdb9fea326c`（短 SHA `4e38ed6`）
> **冻结差异范围**：申请写作 `8296f3c..HEAD`；本报告钉死为 `8296f3c..4e38ed6`（`3a8683f` 文档 + `4e38ed6` 代码/申请）
> **对齐基准**：`docs/MACAO_PRD_v2.md` v2.3.1、`docs/MACAO_REVIEW_GUIDELINES.md` v1.0、`docs/schemas/*.schema.json`
> **证据类型**：DOC / SPEC / CODE / TEST / SIM / OPS

---

## 〇、Reviewer 自审

上轮 grok 对 `8296f3c` **REJECT**：申请把「新 commit」写成已闭环，实现只做 SHA 字符串不等，未消费祖先与孤儿 commit 仍能离开 `REWORK`（P1-1）。按指引 §9，同一 reviewer 对**同一类盲点**（声明 vs 实际读取路径）连续漏审必须登记。

本轮强制自检：

- **A**：不把仓库新增的 4 分支单测当成穷尽；在单测之外再注入「从 A 分出的兄弟分支」与「B 之上两跳后继」。
- **B**：不把 STATUS「Qwen/Kimi 已授予」或申请标题「全员一致」当作证据。

该自检确认：上轮 P1-1 的祖先 / 孤儿反例现已 Fail-closed；兄弟分支同样拒绝；两跳后继仍接受。未再发现新的 P1。

仓库无 `docs/REVIEW_GUIDE.md`；本报告依据 `docs/MACAO_REVIEW_GUIDELINES.md` v1.0。

---

## 一、结论

**支持授予 L3 SCENARIO-VERIFIED；支持授予 PG-1 与 PG-2。不授予 L4 / PG-3。申请标题中的「全员一致」不是事实陈述，只表示目标；本文件是 grok 一票 GRANT，不能代替其余委员对本冻结提交的独立结论。**

上轮 grok 唯一阻断项 P1-1（E6 无 git 拓扑）及申请同时列出的 ZCode P1-1（win32 归档路径断言）经独立复放均属实闭环。指引 §2.2 PG-1 要求的 P0/P1 在本评审人复核范围内归零。L3 返工循环在祖先回退 / 孤立 commit 上不再 CONTRADICTED。PG-2 的接口稳定与 Mock 消费方场景（`e2e-run`）沿用既有证据；真实 CLI 评审链路与若干恢复缺口仍为 P2，不升格为阻断。

---

## 二、申请清单逐条独立复核

| 编号 | 申请声明 | 独立复核方法与结果 | 判定 |
|---|---|---|---|
| **P1-1 (Grok / Codex)** | `REWORK` 下 `is_ancestor(prev, latest)`，祖先回退与孤立 commit Fail-closed | 读 `git_utils.py:53-56`：`merge-base --is-ancestor`，非 0 即 False。读 `orchestrator.py:242-251`：先 `latest == prev` 拒绝（必要：`is_ancestor(X,X)` 为 True），再要求 `is_ancestor(prev, latest)`。独立临时仓库（不复用单测路径）：相同 SHA 拒绝；祖先 A 拒绝且 checkpoint 仍为 B；`commit-tree` 孤儿拒绝；从 A 长出的兄弟分支拒绝；B→C→D 两跳后继接受并进入 `READY_FOR_REVIEW`。仓库单测 Case A–D（`tests/test_p0_p1_rectification.py:1582-1667`）与上述一致，但未覆盖兄弟分支与两跳后继——本评审人已补 SIM。 | **✅ VERIFIED** |
| **P1-1 (ZCode)** | `archived_path` 断言改为 `Path(...).as_posix().startswith(".macao/archive/")` | 读 `tests/test_p0_p1_rectification.py:471`，落点属实。本机 POSIX 65/65 含该断言 PASS。未在 win32 实跑；`as_posix()` 是正确的跨平台写法。 | **✅ VERIFIED**（本机 POSIX；win32 为 CODE 推理，未 OPS） |

### 机验清单（不采信申请粘贴输出）

| # | 声明 | 本机实测 | 状态 |
|---|---|---|---|
| 1 | 全量 65 项 PASS | `Ran 65 tests in 18.240s OK`；再跑一轮 `18.100s OK`（2×65，0 flake）。**未**按申请复放 5 轮。 | ✅ 属实方向；5 轮 PARTIALLY_VERIFIED |
| 2 | `compileall -q src` 与 `git diff --check` | `compileall` RC=0；`git diff --check 8296f3c..4e38ed6` RC=0 | ✅ |
| 3 | `macao test-clis` 4/4、0 僵尸 | claude 2.1.251 / codex 2.1.0 / opencode 1.18.25 / agy 1.1.22 均 PASS。命令均为 `--version`。ANSI 列见 P2-2。 | ✅（冒烟 VERIFIED） |
| 4 | `macao e2e-run` 7/7、DONE | 7 步 OK，`decision=APPROVED`，`votes_yes=3`，终态 DONE。Mock Adapter。 | ✅ |
| 5 | 注册表 70 result + 15 request | `git ls-tree`：**70** / **15**；STATUS 抽出的文件名与 HEAD **双向零差集**。 | ✅（冻结提交时） |

独立故障注入摘要（临时 git + 临时 SQLite，未污染本仓库）：

```text
is_ancestor(B, A)=False  is_ancestor(A, B)=True  is_ancestor(B, B)=True
same_sha           accepted=False  state=REWORK
ancestor           accepted=False  state=REWORK  checkpoint 未倒退
orphan             accepted=False  is_anc=False
sibling_from_A     accepted=False  is_anc=False     # 单测未覆盖
multi_successor    accepted=True   READY_FOR_REVIEW is_anc=True  # 两跳，单测未覆盖
no_git_repo stub   accepted=True   READY_FOR_REVIEW  # 见 P3-1
```

上轮同一脚本在 `8296f3c` 上 `ancestor`/`orphan` 为 `accepted=True`。本轮对应两支已翻转。

---

## 三、P0 / P1

本轮未发现新的 P0 或 P1。上轮 grok `8296F3C-P1-1` 以 `4e38ed6` 为 resolution_commit，状态 **CLOSED**。

---

## 四、P2 / P3：可延期但必须登记

下列不阻断本轮 L3/PG-2；延期 ≠ 没问题。

### P2-1：E6 未约束任务 `source_branch`

上轮验收标准曾要求新 SHA 可从任务 source branch 解析。本轮只做了严格祖先。后继可以落在任意包含该祖先链的分支上。拓扑「新」已成立，分支归属是产品策略，记 P2。

### P2-2：`test-clis` ANSI 列不是独立证据

`integ_harness.py:109-110` 检查的是 clean logs；空日志判 True；PASS 不依赖 `ansi_stripped`。4/4 只证明 `--version` 生命周期。L4 前需要可控 ANSI fixture。

### P2-3：E9 作废仍是 `unlink`；collector 不绑定 message_id / generation

PRD E9 要求作废已收意见并重发新 `message_id`。manifest schema 无代际字段。上轮 SIM：E9 后写回第一代 REJECTED 仍参与共识。本轮 diff 未触及。

### P2-4：REVIEW_REQUEST fan-out 可部分提交

E2 / 消费 dev 先于逐 reviewer `publish`。第二次 publish 失败时状态已 `WAITING_REVIEW`、仅部分投递、dev 已 consumed。本轮未改。

### P2-5：`macao init` 不写入 `.gitignore`

产品代码仅 `e2e_runner.py` 给沙箱写 `.macao/`。下游 `git add -A` 会扫入 `state.db` 与嵌套 worktree。建议在下游实际接入前修复。

### P2-6：真实 Reviewer Adapter 未消费 MessageBus envelope

`test-clis` = `--version`；`e2e-run` = Mock。PG-2 消费方场景以 Mock 全链路 + CLI 冒烟为 **PARTIALLY_VERIFIED**；真实 envelope → worktree → manifest → ACK 仍是 L4 前缺口。

### P2-7 / P2-8（CODE，本轮未重做注入）

push 成功而 `ls-remote` 失败只回退本地（`merge/controller.py:123-134`）；artifact 唯一键无 generation、UPSERT 覆盖代际指针（`store.py:99-106`）。维持上轮登记。

### P3-1：非 git 仓库时跳过存在性与拓扑闸

`orchestrator.py:238-251`：`if self.git and self.git.is_git_repository()` 为假则不跑 `commit_exists` / `is_ancestor`。独立 stub `is_git_repository=False` 后祖先 SHA 被接受。生产路径始终在 git 仓库内；属防御性缺口，不升 P1。

### P3-2：STATUS 正文把未入库的 Qwen/Kimi 票写成「已授予」

`8296f3c` 受控结果仅 claude / codex / grok / zcode 四份；无 `8296f3c-qwen.md` / `8296f3c-kimi.md`。注册表文件计数 70/15 仍双向一致。请把「维持授予」改成「无本轮独立结果文件」或补交报告。

### P3-3：申请标题「全员一致」与范围 `..HEAD`

`HEAD` 是移动引用；本报告已钉死 `4e38ed6`。在其余委员对本 SHA 出具结论之前，「全员一致」不能写进 STATUS 定级句。

---

## 五、L3 场景对账（GUIDELINES §2.1 / §6）

| 场景 | 本轮证据 | 状态 |
|---|---|---|
| 全同意 | 独立 `e2e-run`：3 YES，DONE | VERIFIED |
| 1:1 僵局 | 上轮 grok SIM + 本轮 65/65 含共识单测 | VERIFIED（本轮未重放专用脚本） |
| 超时 | 既有 `detect_timed_out_reviewers` 单测仍绿；无生产 scanner（P2） | PARTIALLY_VERIFIED（测试路径 VERIFIED） |
| 弃权 | 终局票面 ABSTAIN 路径由既有 override 测试覆盖 | TEST VERIFIED |
| 崩溃恢复 | `test_reconcile_*` 在 65/65 中 PASS | TEST VERIFIED |
| 返工循环 | 相同 SHA / 祖先 / 孤儿 / 兄弟分支拒绝；两跳后继接受 | **VERIFIED**（上轮 CONTRADICTED 已翻转） |

---

## 六、门禁判定

| 级别/门禁 | 判定 | 依据 |
|---|---|---|
| L1 DOC-ALIGNED | 保持 PRD v2.3.1 | 本轮未重审设计文档全文 |
| L2 SPEC-CODE-ALIGNED | **维持并确认 E6 拓扑已对齐「新 commit」** | CODE + 独立 SIM |
| L3 SCENARIO-VERIFIED | **通过** | 返工循环 P1 已闭环；六类场景有 TEST/SIM |
| PG-0 | 保持 | 绑定 L1 |
| PG-1 | **通过** | 本评审人范围内 P0/P1 = 0 |
| PG-2 | **通过** | PG-1 + Schema/`types` 多轮未变 + Mock 消费方 E2E；真实 Adapter 记 P2-6 |
| L4 / PG-3 | **不授予** | 不在申请范围；缺 OPS 手册与真实联调 |
| 「全员一致封板」 | **非本文件可裁定的事实** | 仅 grok GRANT；须其余委员对 `4e38ed6` 独立表态 |

---

## 七、建议的后续工作（不作为本轮否决条件）

1. E6 在非 git 仓库上 Fail-closed（有 `prev_ref` 则拒绝），并可选校验 source branch（P3-1 / P2-1）。
2. `macao init` 幂等写入 `.gitignore`（P2-5）。
3. E9 把 attempt/message_id 贯通 manifest 与 collector（P2-3）。
4. STATUS 去掉未入库的 Qwen/Kimi「已授予」措辞；范围钉死 SHA（P3-2 / P3-3）。

---

## 八、Known issues 登记

| issue_id | 严重度 | owner | due_date | resolution_commit | status |
|---|---|---|---|---|---|
| 8296F3C-P1-1 | P1 | Workflow / Git | — | `4e38ed6` | **CLOSED** |
| 4E38ED6-P2-1 | P2 | Workflow / branch | 可延期 | 待补 | OPEN |
| 4E38ED6-P2-2 | P2 | Adapter / PTY Test | L4 前 | 待补 | OPEN |
| 4E38ED6-P2-3 | P2 | Workflow / Protocol | 可延期 | 待补 | OPEN |
| 4E38ED6-P2-4 | P2 | Workflow / MessageBus | 可延期 | 待补 | OPEN |
| 4E38ED6-P2-5 | P2 | CLI / init | 下游接入前建议修 | 待补 | OPEN |
| 4E38ED6-P2-6 | P2 | Adapter / E2E | L4 前 | 待补 | OPEN |
| 4E38ED6-P2-7 | P2 | MergeController | 可延期 | 待补 | OPEN |
| 4E38ED6-P2-8 | P2 | Artifact ledger | 可延期 | 待补 | OPEN |
| 4E38ED6-P3-1 | P3 | E6 git 缺席 | 可延期 | 待补 | OPEN |
| 4E38ED6-P3-2 | P3 | STATUS 措辞 | 下轮申请前 | 待补 | OPEN |
| 4E38ED6-P3-3 | P3 | 申请标题 / HEAD | 下轮申请前 | 待补 | OPEN |
