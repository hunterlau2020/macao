# MACAO Round 5 复审结论（`bdc177e` / `e06d44c..bdc177e`）

- **文档归档路径**: `docs/reviews/2026-09-09-review-result-bdc177e-grok.md`
- **审查日期 (Review Date)**: 2026-09-10
- **审查专家 (Reviewer)**: grok（独立复审；不采信申请粘贴输出，不采信 `STATUS.md` 定级句，不采信处置单「ALL CLOSED」，不采信同轮 Claude 已出票）
- **被审 Commit (Checkpoint Ref)**: `bdc177eaaff577e119093e686f2164bcc133f781`（短 SHA `bdc177e`；与申请正文完整 SHA **逐字符一致**）
- **工作区 HEAD**: `3cb887bed449c44cdd813d6b611aa3ac848faf3e`（仅多本申请与 `STATUS.md`；`src/` / `tests/` 与 `bdc177e` 逐字节相同）
- **审查轮次 (Review Round)**: `5`
- **评审对象**: [`docs/reviews/2026-09-09-review-request-bdc177e.md`](2026-09-09-review-request-bdc177e.md)
- **前序基线**: `e06d44c`；前序 grok 报告 [`2026-09-09-review-result-e06d44c-grok.md`](2026-09-09-review-result-e06d44c-grok.md)（**YES_APPROVE** L3；P2-1 空 `evidence_commit`、P2-2 `startswith` 兄弟目录逃逸；L4 因 mock live-run 否决）
- **对齐基准**: `docs/MACAO_REVIEW_GUIDELINES.md` v1.1 §2–§4、§7.2、§8–§9；UC-3 d5/d6；UC-11 E1；`PRODUCT-FACTS.md` F-24/F-25/F-26
- **目标定级**: L3 SCENARIO-VERIFIED / PG-2 全量认证，并提请 L4 RELEASE-READY / PG-3
- **审查结论 (Verdict)**: **授予本轮增量 L3 SCENARIO-VERIFIED / PG-2**。既有编排引擎 L3 / PG-2（`4e38ed6` 轮）维持。**拒绝 L4 / PG-3**。
- **最终投票 (Vote)**: `YES_APPROVE`（仅覆盖 L3 / PG-2；L4 单独否决，不构成有条件通过）
- **证据**: **无 P0 / 无 P1**；L4 OPS 缺口维持；`ADVISORY` × 若干
- **复现归档**: [`docs/reviews/evidence/2026-09-10-bdc177e-grok/`](evidence/2026-09-10-bdc177e-grok/)

**结论：上轮 grok P2-1（空串 `evidence_commit`）与 P2-2（`startswith` 兄弟目录前缀逃逸），以及 Codex/Claude 升为 P1 的同名路径穿越，本轮独立沙箱全部翻转为真阻断。合法已跟踪证据仍可 `E1_PRODUCED`。CLI 组合根对 `mock-cli` / `claude-code` 会实例化执行者；5+2 款适配器的执行者分支已把 `acceptance_criteria` 写进 TASK prompt。申请完整 SHA 这次是仓库里的真对象，伴随信封 sha256 与 `bdc177e` 树中处置单逐字节一致，`validate_dev_manifest` 通过。L4 仍被 `live-run` 的 `mock-cli` + 默认 `auto_signoff=True` 否决。残留洞：从未入库的证据文件跳过 blob 门；未知执行者 CLI 返回 `None`（默认 `--probe` 会挡，`--no-probe` 仍建 CODING 任务）；审查员分支的 `inject_task` 仍不把验收标准写进 REVIEW_REQUEST（官方 7 适配器测试只打了带 `task_description` 的执行者分支）。**

---

## 0. Reviewer 自审

- 不采信申请「所有 P1 彻底闭环 / 170/170 / 专家探针 100%」、处置单「ALL CLOSED」、STATUS「彻底闭环所有阻断项」。
- 上轮 grok 脚本 `probe_e06d44c.py`、`probe_checkpoint_p104.py` 原样重放；本轮另写 `probe_bdc177e.py`，每个检查点反例一枚新 CODING 任务，并补未跟踪证据、未知 CLI、审查员 prompt。
- 全量测试与独立探针均在 `tempfile.mkdtemp()` 或 `CliRunner` 临时目录执行，宿主仓 `src/` / `tests/` 零写入。
- **漏审登记**：上轮 grok 把 dispatcher payload 含 `acceptance_criteria` 记为 P2-2 CLOSED，**未**打 `inject_task` 的 reviewer 分支（payload 无 `task_description` 时走 REVIEW_REQUEST 模板）。属指引 §9 模式 A（字段写入位置 vs 实际读取位置）。本轮强制补打，见 P2-3。

强制自检：

| # | 项 | 本轮 |
|---|---|---|
| 1 | 字段/路径 vs 实际读取 | 路径改 `relative_to` / `is_relative_to`；空 `evidence_commit` 现 `if not evidence_commit`；blob 仅在 `cat-file -e` 为 0 时比对；执行者 `inject_task` 读 `acceptance_criteria`；审查员分支仍不读 |
| 2 | 「已完成 / 100% / 全绿」 | 170/170、`git show --check` rc=0、8 份 Schema 逐字节一致均 **VERIFIED**；上轮 grok P2-1/P2-2 **VERIFIED 闭环**；「Git blob 严防篡改」「7 款适配器 100% 注入 Prompt」「L4 准入」**PARTIALLY_VERIFIED / CONTRADICTED** |
| 3 | 确定性用语 | 「当文件在对应 commit 存在时」blob 比对成立；未把该限定写成无条件保证。申请仍写「严防篡改」，覆盖面窄于字面 |
| 4 | YAML/JSON Schema | 8 份契约 docs↔src 逐字节一致 **VERIFIED**；申请 §4 示例 `validate_dev_manifest` **PASS**；`sha256` / `evidence_commit` 契约仍无 pattern / `minLength` |
| 5 | P1 均附路径与复放 | 本轮无新 P1；P2 均附路径与脚本 |
| 6 | 生产调用方 | `macao task checkpoint` → `check_development_checkpoint`；`get_orchestrator` → `get_adapter_for_executor` **已接线**（未知 CLI 返回 `None`，见 P2-2） |
| 7 | 参照系 | 测试在干净临时 git 仓；`git show --check` 用申请给出的完整 SHA（本轮是真对象）；不用 `git diff --check` 冒充提交洁净度 |

---

## 1. 结论综述 (Executive Summary)

`bdc177e` 相对 `e06d44c` 是对准 Round 4 三票否决点的有效返工：路径沙箱不再靠字符串前缀；空证据提交不再跳过比对；已跟踪文件在提交后被改盘会因 blob SHA 不一致被拒；组合根对合法 `team.executor.cli` 会注入适配器；执行者 TASK prompt 吃到 `acceptance_criteria`。这些都可以被独立脚本证伪为已修。申请信封本轮第一次自洽（完整 SHA 存在、处置单 sha256 对得上、示例过契约）。

因此本轮增量 **授予 L3 / PG-2**：上轮委员会 REWORK 的阻断面（兄弟目录逃逸、执行者漏配、适配器执行者分支丢 criteria、申请 SHA 假对象）在生产路径上已 fail-closed，且 170 项场景测试未回退。

不能把申请的「Git blob 严防篡改」「验收标准 100% 注入 Prompt」「L4 准入」一并采信：

1. 证据文件从未进入声明 commit 时，`cat-file -e` 非 0，整段 blob 比对被跳过，磁盘哈希自洽即可 `E1_PRODUCED`。
2. `get_adapter_for_executor` 对未知 CLI 返回 `None`，与审查员工厂的 `ValueError` 不对称；`--no-probe` 仍创建 CODING 任务。默认 `--probe` 因 `installed=False` 退出码 1，故不升 P1。
3. 七款适配器的 REVIEW_REQUEST 模板仍不含验收标准；官方 `test_all_adapters_support_acceptance_criteria` 的 payload 带 `task_description`，只打到执行者分支。
4. `live_runner.py` 三名 Reviewer 仍是 `mock-cli`，`run_live_cycle(..., auto_signoff=True)`；本范围对该文件 **零 diff**。§7.2 第 10 行仍 CONTRADICTED。

按指引 §8.2：未跟踪证据不破坏 UC-3 d5 的正文哈希门（磁盘哈希仍比对），也不打开无票合并；未知 CLI 的生产默认入口被 probe 挡住。故记 P2，不回升阻断 L3。L4 仍单独否决。

---

## 2. 申请机验（独立复跑，不采信粘贴）

| 声明 | 本机 | 判定 |
|---|---|---|
| 完整 SHA `bdc177eaaff577e119093e686f2164bcc133f781` | `git rev-parse bdc177e` 逐字符相同；`git cat-file -e` rc=0 | **VERIFIED**（Round 4 P1-3 同类问题本轮未重犯） |
| 范围 `e06d44c..bdc177e` 25 files / 申请 numstat | `git diff --numstat` 与申请表逐文件一致；`+2309 / -25` | **VERIFIED** |
| 涵盖提交仅 `bdc177e` | 该范围还有 `b8d8e9e`（Round 4 申请入库） | 提交列表 **CONTRADICTED**（P3）；文件账 **VERIFIED** |
| `git show --check bdc177eaaff577e119093e686f2164bcc133f781` rc=0 | rc=0，可按申请原文执行 | **VERIFIED** |
| `src/` `tests/` 钉在 `bdc177e` | `git diff bdc177e..HEAD -- src tests` 空 | **VERIFIED** |
| `PYTHONPATH=src python3 -m unittest discover tests` 170/170 | `Ran 170 tests in 55.347s OK` | **VERIFIED** |
| `tests/test_p1_closures_and_regressions.py` 26/26 | `Ran 26 tests in 2.425s OK` | **VERIFIED** |
| `python3 -m compileall -q src tests` | rc=0 | **VERIFIED** |
| 双 Schema 8 份逐字节一致 | 8/8 SAME | **VERIFIED** |
| `python3 -m unittest tests.test_schema` 8/8 | OK | **VERIFIED** |
| STATUS 结论类 159 / 申请 46 / 处置 4 | `git ls-files`：`review-result` 155 + `review-2.5` 2 + methodology 2 = 159；申请 46；处置 4 | 页眉分类计数 **VERIFIED**（`docs/reviews/*.md` 合计 214，与「总计 209」口径不符，P3） |
| 上轮 grok P2-1 空 `evidence_commit` 必须拒绝 | `probe_e06d44c.py` / `probe_bdc177e.py`：`empty_evidence advanced=False` | **VERIFIED 闭环** |
| 上轮 grok P2-2 / Codex P1-01 兄弟目录前缀逃逸 | `prefix_escape` 与 `../<name>_sibling` 均为 `advanced=False` | **VERIFIED 闭环** |
| 已跟踪文件改盘后信封用磁盘哈希 | `blob_tamper_tracked` 保持 CODING | **VERIFIED**（官方 `test_checkpoint_git_blob_verification` 同构） |
| 「当文件在对应 commit 存在时」blob 比对 | 未跟踪文件 `git cat-file -e` rc=128，仍 `E1_PRODUCED` | 限定语 **VERIFIED**；「严防篡改」**PARTIALLY_VERIFIED**（P2-1） |
| `get_orchestrator` 注入 executor | 临时仓 `mock-cli` → `MockAgentAdapter`；Claude 探针 `claude-code` → `ClaudeCodeAdapter` | **VERIFIED**（合法 CLI） |
| 未知 CLI 执行者 fail-closed | 工厂返回 `None`；审查员工厂 `ValueError`；`--no-probe` rc=0 且 CODING；默认 `--probe` rc=1 | 合法配置 **VERIFIED**；未知 CLI **PARTIALLY_VERIFIED**（P2-2） |
| 「7 款适配器 100% 注入 Prompt」 | 执行者分支 7/7 含准则；审查员分支 7/7 不含 | 执行者 **VERIFIED**；全称 **CONTRADICTED**（P2-3） |
| 伴随信封 sha256 = 处置单 | `git show bdc177e:docs/reviews/2026-09-09-disposition-e06d44c.md \| sha256sum` = `877f4bc2…d07d56c` | **VERIFIED** |
| 示例经 `validate_dev_manifest` | 从申请抽出的 YAML → `(True, None)` | **VERIFIED** |
| live-run / L4 OPS | 三 Reviewer `mock-cli`；`auto_signoff: bool = True`；`e06d44c..bdc177e` 未改 `live_runner.py` | L4 OPS **CONTRADICTED** |
| 上轮 grok P1-1 全零/空/缺文件/错误 cli | `probe_checkpoint_p104.py`：`ALL_MATCH_CLAIM`，`fail_open_cases=` 空 | **仍 CLOSED** |
| UC-11 E1 `deadbeef` | `probe_e06d44c.py`：rc=1，`UC-11 E1`，无活动任务 | **仍 CLOSED** |
| Claude 无 `cwd` 丢弃 | 仍 `[]` | **仍 CLOSED** |
| doctor 缺 `macao.yaml` | rc=2 | **仍 CLOSED** |

独立反例摘要：

```text
probe_checkpoint_p104.py -> ALL_MATCH_CLAIM fail_open_cases=
probe_e06d44c.py         -> ALL_MATCH  (empty_evidence/prefix_escape 现均为 advanced=False)
claude R5 probe          -> sibling_escape=False; tampered_tracked=False; untracked=True
codex remaining script   -> REPRODUCED untracked accepted + unknown executor --no-probe CODING
probe_bdc177e.py         -> ALL_MATCH (observations)
  empty_evidence / prefix_escape / sibling_underscore / blob_tamper -> blocked
  good_tracked -> E1_PRODUCED
  untracked    -> E1_PRODUCED (cat-file rc=128)
  composition_root_wires_mock=True
  unknown --no-probe rc=0 CODING; default --probe rc=1
  executor_criteria 7/7; reviewer_criteria 0/7
  example_manifest_schema PASS
  L4 mock-cli + auto_signoff=True
Ran 170 tests in 55.347s OK ; 26/26 P1 regressions ; compileall 0 ; schema 8/8 SAME
claimed full sha bdc177eaaff577e119093e686f2164bcc133f781 -> cat-file rc=0 ; show --check rc=0
```

---

## 3. 已确认与对齐项 (Verified & Aligned Items)

相对 `e06d44c` 轮 grok 报告，下列原问题 **本轮独立复放为闭环**：

- [x] **原 grok P2-1 空串 `evidence_commit`**：`orchestrator.py:408` 现为 `if not evidence_commit or evidence_commit != latest_commit: return None`。`empty_evidence` / `missing_evidence` / `unbound_evidence` 保持 `CODING`。
- [x] **原 grok P2-2 / Codex P1-01 / Claude P1-1 兄弟目录前缀逃逸**：`relative_to` 抛 `ValueError` 即拒；`is_relative_to` 双保险。`../<tmpdir>-evil/secret.md` 与 `../<tmpdir>_sibling/evil.md` 均 `advanced=False`。
- [x] **已跟踪 blob 篡改（Codex 本轮要的那一刀）**：提交后改盘、信封用磁盘哈希 → `None`。改回与 blob 一致 → `E1_PRODUCED`（官方测试覆盖）。
- [x] **Codex/Claude P1-02 组合根漏配（合法 CLI）**：`main.py:186-196` 调 `get_adapter_for_executor`；`Orchestrator.__init__:101-107` 兜底。临时仓 `mock-cli` 与默认模板 `claude-code` 均非 `None`。
- [x] **5 款执行者适配器 `acceptance_criteria`（Codex/Claude/Pi-Qwen P1-02）**：`claude/codex/opencode/antigravity/kimi`（以及本轮未改的 `cursor/pi`）执行者分支 7/7 把准则写进 TASK prompt。
- [x] **申请 SHA / 信封（Codex/Claude/Pi-Qwen P1-03）**：完整 SHA 是真 git 对象；处置单 sha256 与树对象一致；示例过 `dev_manifest` 契约。
- [x] **既有引擎场景测试未回退**：170/170 含共识/超时/返工/E2E mock；回归套件 26/26。
- [x] **上轮已闭环且本轮未回退**：UC-11 E1、全零/空 sha256、错误 `executor.cli`、Claude 无 cwd、doctor rc=2、审查 dispatcher payload 含 `acceptance_criteria`、§5.2 已知简化表。

上轮 L4 mock **未闭**。

---

## 4. 阻断性缺陷 (P0 / P1 Blocking Issues)

未发现 P0。未发现达到 §8.1 P1 的新路径（无静默自动合并；UC-3 d5 正文哈希门与 d6 含 cli 的归属门在生产入口上成立；Round 4 的兄弟逃逸与执行者漏配在合法配置下已关）。

同工作区未跟踪的 Codex 脚本把「未跟踪证据」和「未知执行者 `--no-probe`」标成 P1。两件事实本机均复现，按 §8.2 可达性降为 P2，见第 6 节（回升条件写在条目里）。

---

## 5. L4 / PG-3 与 §7.2 OPS 矩阵（单独否决）

本范围 **未修改** `src/macao/workflow/live_runner.py`。指引 §2.1 / §3.3 / §7.2：L4 需要 OPS VERIFIED、用户可见人工接管、且 P0/P1 为零。缺任一行视为证据不完整。申请未按十行逐格提交 OPS 证据。

| # | 场景 | 本轮 | 判定 |
|---|---|---|---|
| 1 | 守护进程单次扫描 + 超时弃权 | 代码仍在 `daemon.py`；本范围无实机扫描日志 | CODE 沿用 **PARTIALLY_VERIFIED**；OPS **CLAIM_ONLY** |
| 2 | 常驻循环内部异常 | 未在本 commit 重放 | 沿用 **PARTIALLY_VERIFIED** |
| 3 | Reviewer PTY 中途断开 | 无本轮故障注入 | **UNKNOWN** |
| 4 | Worktree 创建失败 | 未改 `create_isolated_worktree` | CODE 沿用 **VERIFIED**；OPS 未演练 |
| 5 | 崩溃后冷重启 | 未在 `bdc177e` 重放 | 沿用 **PARTIALLY_VERIFIED** |
| 6 | 并发写 `state.db` | 未对打 | CODE 沿用 **PARTIALLY_VERIFIED** |
| 7 | 磁盘写失败 | 无 ENOSPC 反例 | **UNKNOWN** |
| 8 | 演练后清理 | 未做残留巡检 | **UNKNOWN** |
| 9 | 人工接管 `macao override resolve` | 命令存在；申请无真实人类输入全程留痕 | **CLAIM_ONLY** |
| 10 | 端到端真实性 / 禁止 mock 合成票 | `live_runner.py:56-58` 三 Reviewer `mock-cli`；`:76` `auto_signoff: bool = True` | **CONTRADICTED** |

第 10 行单独足以拒绝 L4 / PG-3。与 `d042395` / `961bcfe` / `7bc8d70` / `e06d44c` 轮 grok 同一条 OPS 判据。已知简化表 **未** 将 mock live-run 登记为可豁免项。

---

## 6. 建议性问题 (P2 / P3 Advisory Issues)

未在 `STATUS.md` 按 §8.3 做风险接受登记的条目，下一轮仍须面对，但不阻断本轮 L3。

### P2-1 从未提交的证据文件跳过 Git blob 门（申请「严防篡改」覆盖面过宽）

- **位置**: `src/macao/workflow/orchestrator.py:430-439`。官方 `test_checkpoint_git_blob_verification` 只覆盖「已提交后改盘」。
- **现象**: `full_document.path` 指向仓内真实文件、磁盘 SHA 与信封一致、`evidence_commit == latest_commit`，但该路径在声明 commit 中不存在（`git cat-file -e` rc=128）时，blob 分支整段跳过，任务 `E1_PRODUCED` → `READY_FOR_REVIEW`。
- **为何不升 P1**: 申请正文写明「**当文件在对应 commit 存在时**」才做树对象比对；磁盘哈希门（UC-3 d5）仍成立；不打开无票合并。可达面窄于上轮兄弟目录逃逸（不能再指到仓外）。
- **回升条件**: 若后续申请把 blob 门写成无条件「证据必须可被 git 溯源」而不改代码，或未跟踪文件被用来替代已提交审查包且工作区评审依赖该文件，则回升 P1。
- **复现**: `probe_bdc177e.py` 用例 `untracked`；Claude `probe_untracked_evidence_bypass`；Codex `reproduce_untracked_document`。
- **修复建议**: `cat-file -e` 非 0 时同样 `return None`（要求证据文件必须在声明 commit 的树上）；或按 §5.2 把「允许未跟踪证据、仅磁盘哈希」登记为已知简化并给 expiry。官方电池加「从未 add/commit」一行。

### P2-2 未知执行者 CLI 返回 `None`，与审查员工厂 fail-closed 不对称

- **位置**: `live_dispatcher.py:283-284`（`else: return None`）vs `:237`（审查员 `raise ValueError`）；`main.py:186-196`；`orchestrator.py:216-224`（`if self.executor:` 才 `inject_task`）。
- **现象**: `cli: "unknown-executor"` 时 `get_orchestrator(...).executor is None`。`task create --no-probe` 退出码 0、活动任务 `CODING`。默认 `task create`（`--probe`）因 `installed=False` 退出码 1。
- **为何不升 P1**: 生产默认入口被 probe 挡住（§8.2：被上游守卫阻断则下调一级）。`--no-probe` 是用户显式跳过预检，不是静默自动合并。
- **回升条件**: 默认 `--probe` 路径也放行未知 CLI，或 `valid_config=False` 时仍创建任务。
- **复现**: `probe_bdc177e.py` 用例 `unknown_*`；Codex `reproduce_unknown_executor`（该脚本只打了 `--no-probe`）。
- **修复建议**: 执行者工厂对未知 CLI 与审查员一样 `raise ValueError`；组合根捕获后非零退出。不要把 `return None` 写成 fail-closed。

### P2-3 审查员 `inject_task` 仍丢弃 `acceptance_criteria`；官方测试只打执行者分支

- **位置**: 七款适配器 `inject_task` 的 `else`（REVIEW_REQUEST）模板，例如 `claude.py:93-107`、`opencode.py:98-111`。官方测试 `tests/test_p1_closures_and_regressions.py:922-937` 的 payload **含** `task_description`，命中 `if role==executor or "task_description" in payload` 的执行者分支。
- **现象**: `LiveAgentDispatcher.dispatch_review_in_worktree` 把 `acceptance_criteria` 放进 payload（上轮 grok P2-2 已确认），但审查员分支 prompt 不含该字段。本机 7/7 `REVIEWER criteria MISS`。
- **漏审**: 上轮只核了 payload 键，没核 reviewer 模板是否读取（§9 模式 A）。
- **复现**: `probe_bdc177e.py` 用例 `reviewer_criteria_omitted`。
- **修复建议**: REVIEW_REQUEST 模板写入准则；官方测试增加**无** `task_description`、`role=reviewer` 的 payload 行。

### P2-4 L4 runner 仍 mock（同时是 L4 阻断，不升本轮 L3 P1）

见第 5 节。`live_runner.py` 本范围零 diff。

### P2-5 Pi 会话无 `cwd` 仍回填查询仓（F-26 未扩到 Pi）

- **位置**: `session_locator.py:457-474`（有 cwd 才校验；无 cwd 仍 `workspace: str(session_cwd or resolved_proj)` 并入列）
- 本轮未宣称修 Pi。Claude 路径仍 fail-closed。残留记 P2。

### P2-6 `dev_manifest.schema.json` 的 `sha256` / `evidence_commit` 仍无正则与 `minLength`

运行时已拒全零、空 evidence、非十六进制；契约层仍 fail-open。上轮 grok P2-7 残留。

### P3

- P3-1：范围说明漏 `b8d8e9e`（Round 4 申请入库提交）。
- P3-2：申请写 `git cat-file -p` 取 blob，实现是 `cat-file -e` + `git show commit:path`（`git_utils.py:76-77`）。行为对 blob 通常等价，文档不对称。
- P3-3：`if blob_bytes is not None` 套在 `cat-file -e` 成功之后——若 `git show` 失败会跳过比对。未见可稳定触发的生产输入，记防御缺口。
- P3-4：STATUS 页眉分类 159/46/4 对；「总计 209」与 `git ls-files 'docs/reviews/*.md'`=214 不符；文内登记表标题仍写「142 份结论 + 41 份申请」。

---

## 7. 前序条目逐条对照（避免「全部闭环」被误读）

| 来源 | 本轮机验 | 定级影响 |
|---|---|---|
| grok `e06d44c` P2-1 空 `evidence_commit` | **CLOSED** | 不阻断 |
| grok `e06d44c` P2-2 / Codex P1-01 / Claude P1-1 兄弟目录逃逸 | **CLOSED** | 解除 Round 4 REWORK 主因之一 |
| Codex/Claude P1-02 组合根漏配（合法 CLI）+ 执行者 criteria | **CLOSED** | 不阻断 |
| Codex/Claude/Pi-Qwen P1-03 申请 SHA / 信封 | **CLOSED** | 不阻断 |
| grok `7bc8d70` P1-1 全零/空/缺文件/cli | **仍 CLOSED** | — |
| UC-11 E1 adopt 幽灵基线 | **仍 CLOSED** | — |
| grok dispatcher payload 验收标准 | payload **仍 CLOSED**；reviewer 模板未读 → 新 P2-3 | — |
| grok P2-1 Claude 无 cwd | **仍 CLOSED**（Pi 仍回填 → P2-5） | — |
| grok L4 mock-cli | **未闭** | 单独拒 L4 |
| 未跟踪证据 / 未知执行者 | 事实成立，按可达性 **P2**（不采信升 P1） | 不阻断 L3 |

---

## 8. 建议闭环顺序与验收

1. **P2-1**（建议同轮，避免下一轮再把「严防篡改」写成已闭环）：`cat-file -e` 失败则 `return None`；官方电池加从未提交行。验收：`probe_bdc177e.py` 的 `untracked_advances` 从 True 翻转为 False，且 `good_tracked` 仍 True。
2. **P2-3**：REVIEW_REQUEST 写入 `acceptance_criteria`；测试去掉 `task_description` 再断言。验收：七款适配器 reviewer 分支 prompt 含准则。
3. **P2-2**：未知执行者 CLI 抛错并让 CLI 非零退出，不要 `return None`。验收：`--no-probe` 对 `unknown-executor` 亦非零，且无活动任务。
4. **L4**：真实 CLI 至少一轮非全同意；人类路径 HOLD → `macao override resolve`；按 §7.2 十行填证据。不要再拿 `mock-cli` live-run 申请 PG-3。

---

## 9. 准入建议

- **本轮增量**：**授予** L3 SCENARIO-VERIFIED / PG-2。Round 4 阻断本增量的兄弟逃逸、合法 CLI 执行者漏配、执行者 criteria 丢失、申请 SHA 假对象已独立复放闭环；170 项场景测试全绿。
- **既有编排引擎**：**维持** L3 SCENARIO-VERIFIED / PG-2。
- **L4 RELEASE-READY / PG-3**：**拒绝**。§7.2 第 9–10 行未满足；mock live-run 不在已知简化表内。
- 「Git blob 严防篡改」「验收标准 100% 注入 Prompt」本轮最高记 **PARTIALLY_VERIFIED**，不得在 STATUS 写成已全部闭环。

本票是对 L3 的 `YES_APPROVE`，**不是**对 L4 的有条件通过（指引对「有条件通过」视为不通过）。L4 必须另走一轮带 OPS 证据的申请。

---

## 10. 复现脚本与命令

- 归档目录：`docs/reviews/evidence/2026-09-10-bdc177e-grok/`
- 最后执行：2026-09-10T00:45:52+08:00
- 完整 SHA：`bdc177eaaff577e119093e686f2164bcc133f781`
- 外部前提：无网络、无厂商 CLI 额度；Python 3.10+；系统 git/sqlite3

```bash
cd /home/debian/macao
git rev-parse bdc177e
git cat-file -e bdc177eaaff577e119093e686f2164bcc133f781
git show --check bdc177eaaff577e119093e686f2164bcc133f781
PYTHONPATH=src python3 -m compileall -q src tests
PYTHONPATH=src python3 -m unittest discover tests
PYTHONPATH=src python3 -m unittest tests.test_p1_closures_and_regressions tests.test_schema
PYTHONPATH=src python3 docs/reviews/evidence/2026-09-08-7bc8d70-grok/probe_checkpoint_p104.py
PYTHONPATH=src python3 docs/reviews/evidence/2026-09-09-e06d44c-grok/probe_e06d44c.py
PYTHONPATH=src python3 docs/reviews/evidence/2026-09-10-bdc177e-grok/probe_bdc177e.py
git show bdc177e:docs/reviews/2026-09-09-disposition-e06d44c.md | sha256sum
```

---

## 11. Reviewer 自审记录 (Self-Audit Log)

- [x] 已对照 `e06d44c..bdc177e` 25 个文件与申请清单（含漏列的 `b8d8e9e`）
- [x] 已串行执行 `unittest discover tests`（170/170）与 `compileall` 与 schema 8/8
- [x] 已重放上轮 grok/Claude 探针与 P1-04 电池；未把 Codex 未跟踪脚本的 P1 标签直接当成定级
- [x] 已用新脚本击穿未跟踪证据、未知 CLI、审查员 prompt，并按 §8.2 降为 P2 而非阻断 L3
- [x] 未发现未报告的 P0
- [x] 未在宿主仓执行会写状态的 `task adopt` / `task create`
- [x] `git show --check` 使用申请给出的完整 SHA，本轮该对象存在且 rc=0
- [x] 登记上轮对 reviewer `inject_task` 读取路径的漏审（模式 A）

---

## 伴随机器信封：`.macao/.reviews/r5/grok.review.yml`

```yaml
version: "1.0"
task_id: "task-20260909-p1-closures-wire-executor-criteria-blob-check"
checkpoint_ref: "bdc177e"
review_round: 5
reviewer:
  id: "grok"
  role: "reviewer"
  cli: "cursor-grok"
vote: "YES_APPROVE"
opinion:
  status: "APPROVED"
  confidence: 0.90
  summary: "Round 4 兄弟逃逸、合法 CLI 执行者接线、执行者 criteria、申请 SHA 已独立复放闭环，授予本轮增量 L3/PG-2；未跟踪证据跳过 blob 门、未知执行者 --no-probe、审查员 prompt 仍丢准则记 P2；L4 因 live-run mock-cli 与 §7.2 矩阵未填而否决。"
full_document:
  path: "docs/reviews/2026-09-09-review-result-bdc177e-grok.md"
  evidence_commit: "bdc177e"
  sha256: "ee0b99de1a830a7b39eb28950dbdf8977336d0ec12a3112ae93364febc207867"
items:
  - issue_id: "grok/L4-OPS"
    disposition_class: "MUST_FIX"
    severity: "blocker"
    title: "L4 only: live-run still hardcodes mock-cli reviewers and default auto_signoff=True; §7.2 matrix not evidenced"
  - issue_id: "grok/P2-1"
    disposition_class: "SHOULD_FIX"
    severity: "major"
    title: "Untracked full_document skips git blob check and still advances to READY_FOR_REVIEW"
  - issue_id: "grok/P2-2"
    disposition_class: "SHOULD_FIX"
    severity: "major"
    title: "Unknown executor CLI returns None; task create --no-probe still opens a CODING task"
  - issue_id: "grok/P2-3"
    disposition_class: "SHOULD_FIX"
    severity: "major"
    title: "Reviewer inject_task omits acceptance_criteria; official adapter test only hits executor branch"
```
