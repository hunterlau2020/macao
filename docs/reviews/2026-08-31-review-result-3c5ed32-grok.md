# MACAO 独立复审报告 — Phase 3 / PG-3 / L4 RELEASE-READY 申请 (commit `3c5ed32`)

> **评审人**：grok（独立复审；不采信申请粘贴输出，亦不采信工作区未跟踪的其他专家结论）
> **评审日期**：2026-08-31
> **评审对象**：[`2026-08-31-review-request-Phase3-PG3-L4.md`](2026-08-31-review-request-Phase3-PG3-L4.md)
> **冻结代码提交**：申请钉 `3c5ed32`；工作区 HEAD 为 `8871d00`（其后仅 README / PRD 增补 / 本申请与 STATUS）。Phase 3 实现以 `3c5ed32` 为准；用户手册以 HEAD 的 `README.md` + `docs/FAQ.md` 一并核验。
> **冻结差异范围**：`4e38ed6..3c5ed32`（功能）+ `3c5ed32..8871d00`（手册与申请）
> **对齐基准**：`docs/MACAO_REVIEW_GUIDELINES.md` v1.0（L1–L4 / PG-0–PG-3 的权威门禁）。仓库无 `docs/REVIEW_GUIDE.md`；`docs/reference/REVIEW_GUIDE.md` 是另一项目的 FastAPI 后端指南（IDOR / 儿童隐私），**不能**作为 MACAO 发布门禁。
> **证据类型**：DOC / CODE / TEST / SIM / OPS

---

## 〇、Reviewer 自审

上轮 grok 对 `4e38ed6` **GRANT L3/PG-2**，并写明不授予 L4。本轮若把「72 测试绿 + live-run 打印 DONE」直接升格为 OPS VERIFIED，就会重复 checklist **B**（声明 ≠ 证据）和 **C**（「真实 / 100%」未标注目标）。

本轮强制自检：对每一个「真实 CLI / 生产守护 / 自愈」声明，都构造**生产路径**反例（调用 `LiveAgentDispatcher.dispatch_review_in_worktree`、`OrchestratorDaemon.scan_once` 在 `WAITING_REVIEW` 上、向 `ReviewExtractor` 喂非评审 YAML），而不是停在 CLI 退出码 0。

该自检命中 §四 四项 P1。

---

## 一、结论

**不授予 L4 RELEASE-READY，不通过 PG-3。维持既有 L3 SCENARIO-VERIFIED / PG-2（对象仍是 `4e38ed6` 的状态机与 Mock 场景，不因本轮新增表面而撤销）。**

L4 最低条件（指引 §2.1 / §3.3）是：L3 + **人工接管路径实机演练** + **回归无 P0/P1** + **用户手册齐备** + **OPS VERIFIED**。本申请在后四项上均未达到：

- `macao live-run` **不拉起真实 Reviewer CLI**，由 runner 代写三张 `YES_APPROVE`，签字为 `Live runner auto-signoff`。
- `LiveAgentDispatcher` 调用不存在的 `GitManager.create_worktree`，生产派发路径崩溃。
- `OrchestratorDaemon` 调用不存在的 `StateStore.get_audit_events`；即使补上方法，事件名/字段也与账本不一致。
- `ReviewExtractor` 对空字典 / `{foo: 1}` 默认补 `vote=YES_APPROVE` 且 Schema 通过。

72/72 单测为 **TEST VERIFIED**，但不能外推为 L4：Phase 3 新测试只覆盖 extractor happy-path、daemon **空闲**扫描、以及上述合成 live-run。

---

## 二、申请声明逐条独立复核

| 声明 | 独立复核 | 判定 |
|---|---|---|
| LiveAgentDispatcher 为每位 Reviewer 建 worktree 并 PTY 拉起真实 CLI | `git_utils.py` 只有 `create_isolated_worktree`。`live_dispatcher.py:147` 调用 `self.git.create_worktree(...)`。`hasattr(GitManager,"create_worktree")` 为 False。独立调用 `dispatch_review_in_worktree` → `AttributeError`。worktree 路径还与既有隔离约定不一致（`<task>/<reviewer>` vs `<reviewer>/<task>/r<n>`）。 | **CONTRADICTED** |
| ReviewExtractor 两级自愈 + Draft-07 强校验 | 有 fence 的合法 YAML 能解析（单测绿）。`setdefault` 注入 id/ref/round 后，`vote = vote or "YES_APPROVE"`、`status = status or "APPROVED"`（`live_dispatcher.py:90-91`）。独立：````yaml\nfoo: 1\n```` 与 ````yaml\n{}\n```` 均 `ok=True, vote=YES_APPROVE`。单测 `test_review_extractor_self_heals_omitted_metadata` 把缺字段默认赞成写成预期行为。 | **CONTRADICTED**（强校验被默认赞成架空） |
| OrchestratorDaemon 超时降级并推进 FSM | 空仓库 `daemon --once` → `active_task=None`（申请当作 PASS）。真实 `WAITING_REVIEW` 任务上 `scan_once` → `AttributeError: get_audit_events`。生产账本事件是 `type=REVIEW_REQUESTS_DISPATCHED`、字段 `detail`；daemon 找 `event_type=="REVIEW_DISPATCHED"` 与 `payload.deadline_epoch`。`run_loop` `except Exception: pass`。提交识别用 `kind.endswith(".review.yml")`，实际 kind 为 `review_manifest`。 | **CONTRADICTED** |
| `macao setup` 隔离 `.macao/` | `ensure_gitignore_isolation` 只追加 `.macao/worktrees/` 与若干 `*.db`，**不**忽略 `.dev.yml` / `.reviews/` / `vote_result.json` / `archive/`。 | **PARTIALLY_VERIFIED** |
| Schema 打进 `macao.schemas` | `src/macao/schemas/*.schema.json` 存在；`schema.py:17-20` 优先包内目录；`pyproject.toml` `package-data` 已写。 | **CODE VERIFIED** |
| 细粒度 `model` 透传 | adapter 层本轮有 model 字段改动；未做真实 CLI `-m` 活测。 | **PARTIALLY_VERIFIED** |
| `live-run` 真实 7 步协同、终态 DONE | 本机 `live-run` 退出 0、步骤打印 DONE。读 `live_runner.py:93-170`：开发是 runner 自己写 `math_lib.py`；评审循环直接 `yaml.safe_dump` 三张 YES；`HUMAN_MERGE_APPROVED` note 为 auto-signoff。**从未**调用 `LiveAgentDispatcher`。报告标题仍是 Phase 2 renderer，「Physical Archive」为 EMPTY（0 files）。 | **CLAIM_ONLY / CONTRADICTED（「真实」）** |
| 72 tests / compileall / diff-check 洁净 | 72/72 OK（22.8s）。`compileall` RC=0。`git diff --check 4e38ed6..8871d00` **RC=2**（`README.md:146` 与 `docs/reference/REVIEW_METHODOLOGY.md` 尾随空白）。申请写 100% Clean **不成立**。 | 测试 ✅；diff-check **CONTRADICTED** |
| `test-clis` 6/6 | 本机仍 **4/4**（claude/codex/opencode/agy），`--version` 冒烟。无 cursor / kimi 行。 | **PARTIALLY_VERIFIED**（4 非 6） |
| 手册齐备 | `3c5ed32` 有 `docs/FAQ.md`，无 README。HEAD `README.md` 徽章写 **L4 RELEASE-READY**（评审尚未结束），并把 live-run 写成「生产级真实协同」。 | 有文档；内容 **过宽** |

独立反例摘要：

```text
has_create_worktree=False  has_get_audit_events=False
extract {foo:1} / {}  -> ok=True vote=YES_APPROVE status=APPROVED
dispatch_review_in_worktree -> AttributeError: create_worktree
WAITING_REVIEW + daemon.scan_once -> AttributeError: get_audit_events
audit_types 实际含 REVIEW_REQUESTS_DISPATCHED（无 REVIEW_DISPATCHED）
live-run DONE 但 runner 手写 YES + auto-signoff；Archived 0
test-clis 4/4 非 6/6
git diff --check RC=2
```

---

## 三、P0

未发现需单列的 P0（无越权数据面；本对象不是多租户 HTTP API）。

---

## 四、P1：进入 L4 / PG-3 前必须解决

### P1-1：ReviewExtractor 缺字段默认赞成，非评审 YAML 可变成合法 YES

**验证状态**：CONTRADICTED

**证据**：`src/macao/workflow/live_dispatcher.py:69-91`；`tests/test_phase3.py:45-61`；独立 SIM：`foo: 1` 与 `{}` 均通过 `validate_review_manifest` 且 `vote=YES_APPROVE`。

PRD / 指引要求产物型转移 Fail-closed。默认补 `YES_APPROVE`/`APPROVED` 会把客套话、截断输出或无关 YAML 写进 `.reviews/`，进入 2/3 多数。

**验收**：缺少显式 `vote` **且** 缺少显式 `opinion.status` 时必须拒绝；禁止用 dispatcher 参数覆盖 YAML 里已有的 `checkpoint_ref`/`review_round` 若与当前派发不一致；单测覆盖空 dict / 无关键 / 仅 status=REJECTED（后者当前能映射 NO，应保留）。

### P1-2：LiveAgentDispatcher 生产派发 API 不存在，声称的真实 worktree+PTY 路径无法执行

**验证状态**：CONTRADICTED

**证据**：`live_dispatcher.py:147` vs `git_utils.py:96-117`。独立调用立即 `AttributeError`。`live_runner` 不调用 dispatcher，故 72 测与 `live-run` 绿无法为该路径背书。

**验收**：接到真实的 `create_isolated_worktree`（或实现并测试 `create_worktree`）；至少一条测试在临时 git 仓上真正 `worktree add`、失败 Fail-closed、finally 删除；禁止用合成 YES 代替。

### P1-3：OrchestratorDaemon 无法读取生产审计，超时降级在活跃任务上崩溃

**验证状态**：CONTRADICTED

**证据**：`daemon.py:34-48,77-78`；`store.py:163-192`。独立：任务已 `WAITING_REVIEW` 且存在 `REVIEW_REQUESTS_DISPATCHED` 时 `scan_once` 抛 `AttributeError`。`run_loop` 吞掉异常后守护进程静默空转。单测只覆盖无任务。

即便改名调用 `list_audit_events`，仍会因 `event_type`/`payload`/`REVIEW_DISPATCHED`/`kind=*.review.yml` 全错而永不触发。上轮已关闭的 `limit=50` 截断也在此复现。

**验收**：调用 `detect_timed_out_reviewers` / `get_audit_events_by_type(..., "REVIEW_REQUESTS_DISPATCHED")`；deadline 用 ISO/`per_reviewer`；提交集合用 `reviewer_id` + `kind==review_manifest`；活跃 `WAITING_REVIEW` 过期必须写出 `REVIEWER_TIMEOUT_ABSTAIN` 并 HOLD；禁止裸 `except: pass`。

### P1-4：L4 要求的「真实协同 + 人工接管实机演练」未被满足，`live-run` 把合成路径标成生产证据

**验证状态**：CONTRADICTED

**证据**：指引 §2.1 L4、§3.3 OPS；`live_runner.py:93-170`；CLI 成功文案 `main.py:406`。本机 `live-run` 约 1s 结束（与真实三路 CLI 评审耗时不符）。无 `override resolve` 实机剧本（僵局/超时 HOLD → 人裁）。

**验收**：至少一条 **真实** Reviewer Adapter：MessageBus/PTY → 隔离 worktree → 非自愈伪造的 schema-valid manifest → ACK；另做一次人工 `RETRY_REVIEW` 或超时 HOLD 的实机记录（命令、状态、票面）。合成 runner 须改名，不得再写「Live / L4 Ready / 100% 真实」。

---

## 五、P2 / P3

| ID | 说明 |
|---|---|
| P2-1 | `.gitignore` 仍不覆盖 `.macao/.dev.yml`、`.reviews/`、`vote_result.json`（上轮 P2-5 未闭） |
| P2-2 | `git diff --check` 不洁净；申请「100% Clean」过宽 |
| P2-3 | `test-clis` 仍为 `--version`；申请 6/6 与实测 4/4 不符；ANSI 列仍弱 |
| P2-4 | `generate_smart_config` 把 `min_effective_votes` 设为 reviewer 人数（3=全票），与「2/3」文案冲突 |
| P2-5 | README 徽章在评审完成前写 L4；live-run 报告混用 Phase 2 renderer，归档显示 EMPTY |
| P2-6 | 上轮未修：E9 unlink 代际、fan-out 部分提交、push/`ls-remote` 分裂、artifact UPSERT（L4 前建议处理，本轮未作为唯一否决） |
| P3-1 | `docs/reference/` 混入财务/英语学习评审指南，易被当成 MACAO 门禁 |
| P3-2 | 申请钉 `3c5ed32`，手册在 `8871d00`；范围应写清 |

---

## 六、L4 / 场景对账

| L4 条件 | 状态 |
|---|---|
| 继承 L3 | 维持（既有 65+ 单测仍绿；本轮未击穿 E6 拓扑） |
| 人工接管实机演练 | **CONTRADICTED**（auto-signoff） |
| 回归无 P0/P1 | **不成立**（本轮 4×P1） |
| 用户手册齐备 | PARTIALLY_VERIFIED（有 FAQ/README，但 L4/真实协同表述错误） |
| OPS VERIFIED | **CONTRADICTED**（dispatcher/daemon 生产路径崩溃；live-run 非 OPS） |

---

## 七、门禁判定

| 级别/门禁 | 判定 |
|---|---|
| L3 / PG-2 | **维持**（不因 Phase 3 表面撤销） |
| L4 RELEASE-READY | **不通过** |
| PG-3 | **不通过**（绑定 L4） |

---

## 八、建议闭环顺序

1. 删除或反转 extractor 默认 YES；补垃圾 YAML 拒绝测试。
2. 把 dispatcher 接到 `create_isolated_worktree`；单测必须真正建/删 worktree。
3. daemon 改用现有定向审计 API + `detect_timed_out_reviewers`；活跃超时路径要有测试。
4. `live-run` 要么接真实 Adapter，要么改名为 mock 并改掉 README/STATUS/徽章。
5. 补人工接管 OPS 记录后再申请 L4。

---

## 九、Known issues

| issue_id | 严重度 | resolution_commit | status |
|---|---|---|---|
| 3C5ED32-P1-1 | P1 | 待补 | OPEN |
| 3C5ED32-P1-2 | P1 | 待补 | OPEN |
| 3C5ED32-P1-3 | P1 | 待补 | OPEN |
| 3C5ED32-P1-4 | P1 | 待补 | OPEN |
| 3C5ED32-P2-1 … P2-6 | P2 | 待补 | OPEN |
| 3C5ED32-P3-1 … P3-2 | P3 | 待补 | OPEN |
