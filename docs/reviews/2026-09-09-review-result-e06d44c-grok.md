# MACAO Round 4 复审结论（`e06d44c` / `7bc8d70..e06d44c`）

- **文档归档路径**: `docs/reviews/2026-09-09-review-result-e06d44c-grok.md`
- **审查日期 (Review Date)**: 2026-09-09
- **审查专家 (Reviewer)**: grok（独立复审；不采信申请粘贴输出，不采信 `STATUS.md` 定级句，不采信处置单「ALL CLOSED」，不采信其他专家票）
- **被审 Commit (Checkpoint Ref)**: `e06d44cb31a0dbcbe199e6bb124430e9701e087f`（短 SHA `e06d44c`）
- **工作区 HEAD**: `b8d8e9e7769e62cf0e25a4b29510e4399f25ccf9`（仅多本申请与 `STATUS.md`；`src/` / `tests/` 与 `e06d44c` 逐字节相同）
- **审查轮次 (Review Round)**: `4`
- **评审对象**: [`docs/reviews/2026-09-09-review-request-e06d44c.md`](2026-09-09-review-request-e06d44c.md)
- **前序基线**: `7bc8d70`；前序 grok 报告 [`2026-09-08-review-result-7bc8d70-grok.md`](2026-09-08-review-result-7bc8d70-grok.md)（**NO_APPROVE**；阻断为检查点全零/空/缺失哈希 fail-open）
- **对齐基准**: `docs/MACAO_REVIEW_GUIDELINES.md` v1.1 §2–§4、§7.2、§8–§9；UC-3 d5/d6；UC-11 E1；`PRODUCT-FACTS.md` F-24/F-25/F-26
- **目标定级**: L3 SCENARIO-VERIFIED / PG-2 全量认证，并提请 L4 RELEASE-READY / PG-3
- **审查结论 (Verdict)**: **授予本轮增量 L3 SCENARIO-VERIFIED / PG-2**。既有编排引擎 L3 / PG-2（`4e38ed6` 轮）维持。**拒绝 L4 / PG-3**。
- **最终投票 (Vote)**: `YES_APPROVE`（仅覆盖 L3 / PG-2；L4 单独否决，不构成有条件通过）
- **证据**: **无 P0 / 无 P1**；L4 OPS 缺口维持；`ADVISORY` × 若干
- **复现归档**: [`docs/reviews/evidence/2026-09-09-e06d44c-grok/`](evidence/2026-09-09-e06d44c-grok/)

**结论：上轮 grok P1-1（全零/空/缺失 sha256 与错误 `executor.cli` 放行）以及 Claude/Codex 的 UC-11 E1 幽灵基线，本轮独立沙箱全部翻转为真阻断。官方 10 变体电池覆盖了上轮击穿面。申请所称「8 步硬核」并非全部落地：空串 `evidence_commit` 与 `startswith` 路径前缀穿越仍 fail-open，降为 P2（UC-3 d5 的正文哈希门已成立，这两项是宣称清单的残留洞）。L4 仍被 `live-run` 的 `mock-cli` + 默认 `auto_signoff=True` 否决。申请信封写的完整 SHA `e06d44c77c688bb7…` 在仓库中不存在，§3.3 给出的 `git show --check` 命令按原文执行 rc=128。**

---

## 0. Reviewer 自审

- 不采信申请「14 项 P0/P1 全部闭环 / 165/165 / 专家脚本 100%」、处置单「ALL CLOSED」、STATUS「彻底闭环所有 P1/P2」。
- 上轮 grok 反例脚本 `probe_checkpoint_p104.py` 原样重放；本轮另写 `probe_e06d44c.py`，每个检查点反例一枚新 CODING 任务，并补空 `evidence_commit`、兄弟目录前缀穿越、adopt `deadbeef`、doctor 缺配置。
- 全量测试与独立探针均在 `tempfile.mkdtemp()` 或 `CliRunner` 临时目录执行。
- **漏审登记**：无连续同类漏审。本轮强制项是指引 §9 B（官方电池未覆盖空 `evidence_commit` / 前缀穿越就把「8 步」写成已闭环）与 §3.4（申请把不存在的完整 SHA 写进验证命令）。

强制自检：

| # | 项 | 本轮 |
|---|---|---|
| 1 | 字段/路径 vs 实际读取 | `sha256` 现先正则再逐字节比对；`executor.cli` 已读；`evidence_commit` 仅在真值时比对；路径沙箱是 `str.startswith` |
| 2 | 「已完成 / 100% / 全绿」 | 165/165 **VERIFIED**；上轮 P1-1 / adopt E1 **VERIFIED 闭环**；「8 步全部落地」「L4 准入」「专家脚本 100%」**CONTRADICTED / PARTIALLY_VERIFIED** |
| 3 | 确定性用语 | 「严禁全零」「UC-11 E1 立即退出码 1」成立；「必须非空 evidence_commit」「位于项目根目录内」未完全成立 |
| 4 | YAML/JSON Schema | 8 份契约 docs↔src 逐字节一致 **VERIFIED**；`dev_manifest.sha256` 仍只是 `type: string`，不拒全零（运行时拒） |
| 5 | P1 均附路径与复放 | 本轮无新 P1；P2 均附路径与脚本 |
| 6 | 生产调用方 | `macao task checkpoint` → `check_development_checkpoint`；`macao task adopt` → `Orchestrator.adopt_task` + `fsm.transition` **已接线** |
| 7 | 参照系 | 测试在干净临时 git 仓；`git show --check` 用**实际**完整 SHA，不用申请伪造 SHA，也不用 `git diff --check` |

---

## 1. 结论综述 (Executive Summary)

`972e0d0` 相对 `7bc8d70` 是一轮对准上轮五方 P1 的有效返工：检查点对全零/空串/缺文件/错误 cli 不再放行；`task adopt` 对 `deadbeef` 打出 `UC-11 E1` 并以退出码 1 离开，状态库无活动任务；接管走 `E2_ADOPT` / `E1_ADOPT` 白名单边并写 `TASK_ADOPTED`。`080720c` / `e06d44c` 补了探活 UI 的 model/provider 展示与 schema `provider` 字段。这些都可以被独立脚本证伪为已修。

因此本轮增量 **授予 L3 / PG-2**：上轮阻断 L3 的审计锚点（UC-3 d5 正文哈希 + d6 归属含 cli）已在生产路径上 fail-closed，且 165 项既有场景测试未回退。

不能把申请的「8 步硬核」「所有 P2 闭环」「L4 准入」一并采信：

1. 空串 `evidence_commit` 仍进入 `READY_FOR_REVIEW`（`if evidence_commit and` 把空串当成跳过）。
2. `../<reponame>-evil/secret.md` 能通过 `startswith` 前缀判定，检查点可绑定仓外兄弟目录文件。
3. `live_runner.py` 三名 Reviewer 仍是 `mock-cli`，`run_live_cycle(..., auto_signoff=True)`；§7.2 第 10 行仍 CONTRADICTED。
4. 申请写的完整 SHA `e06d44c77c688bb715bb997a3cf556bc91f6920f` 不是 git 对象；按 §3.3 原文执行 `git show --check` 得到 `fatal: bad object`。真实对象是 `e06d44cb31a0dbcbe199e6bb124430e9701e087f`。

按指引 §8.2：空 `evidence_commit` 与前缀穿越不破坏 UC-3 d5 的正文哈希门（文件哈希仍比对），也不打开无票合并，故记 P2，不回升阻断 L3。L4 仍单独否决。

---

## 2. 申请机验（独立复跑，不采信粘贴）

| 声明 | 本机 | 判定 |
|---|---|---|
| 范围 `7bc8d70..e06d44c` 36 files / +3414 / -181 | `git diff --stat` 一致 | **VERIFIED** |
| 涵盖提交仅 `972e0d0`、`080720c`、`e06d44c` | 该范围还有 `a705a49`（上轮申请入库） | 提交列表 **CONTRADICTED**（P3）；文件账 **VERIFIED** |
| 受审完整 SHA = `e06d44c77c688bb715bb997a3cf556bc91f6920f` | `git rev-parse e06d44c` = `e06d44cb31a0dbcbe199e6bb124430e9701e087f`；声称对象 `cat-file` 失败 | **CONTRADICTED**（P2） |
| `git show --check <声称完整 SHA>` rc=0 | 声称 SHA rc=128；实际 SHA rc=0；`972e0d0` / `080720c` 亦 rc=0 | 命令原文 **CONTRADICTED**；实际提交洁净度 **VERIFIED** |
| `src/` `tests/` 钉在 `e06d44c` | `git diff e06d44c..HEAD -- src tests` 空 | **VERIFIED** |
| `PYTHONPATH=src python3 -m unittest discover tests` 165/165 | `Ran 165 tests in 59.829s OK` | **VERIFIED** |
| `python3 -m compileall -q src tests` | rc=0 | **VERIFIED** |
| 双 Schema 8 份逐字节一致 | 8/8 SAME | **VERIFIED** |
| `python3 -m unittest tests.test_schema` 8/8 | OK | **VERIFIED** |
| STATUS 结论类 155 / 申请 45 / 处置 3 / 合计 204 | `review-result` 151 + `review-2.5` 2 + methodology 2 = 155；申请 45；处置 3；`docs/reviews/*.md` 204 | 页眉计数 **VERIFIED**（登记表标题仍写 142/41，P3） |
| 上轮 grok P1-1「全零/空/缺文件/错误 cli 必须拒绝」 | `probe_checkpoint_p104.py`：`ALL_MATCH_CLAIM`，`fail_open_cases=` 空，rc=0 | **VERIFIED 闭环** |
| Claude 探针 zero/missing/empty/wrong_cli `advanced=False`；adopt 幽灵基线 rc=1 | 全部成立；`good` 仍 `READY_FOR_REVIEW` | **VERIFIED** |
| Qwen QW-7BC-P1-1a/b/c `not-reproduced` | SUMMARY 三行均为 `not-reproduced`；控制组真哈希 ACCEPTED / 篡改 REJECTED | **VERIFIED**（脚本 `[FAIL]` 前缀表示旧漏洞不再复现，勿与回归失败混淆） |
| Codex 归档脚本「100% 通过」 | `reproduce_fail_closed_gaps.py` 仍断言 `deadbeef` adopt `exit_code == 0`，修复后 `AssertionError` | STATUS 该句 **CONTRADICTED**（P3） |
| `task adopt` 走 FSM；E1 不脏写 | `STATE_TRANSITION_E2_ADOPT` + `TASK_ADOPTED`；`deadbeef` rc=1 且无活动任务 | **VERIFIED** |
| 审查 payload 透传 `acceptance_criteria` | `live_dispatcher.py` payload 与 `review_context` 均含该字段 | **VERIFIED**（上轮 grok P2-2 **CLOSED**） |
| Claude 无 `cwd` 丢弃 | 规范目录内无 cwd 的 jsonl → `[]` | **VERIFIED**（上轮 grok P2-1 Claude 部分 **CLOSED**） |
| doctor 缺 `macao.yaml` 非零 | `CliRunner` rc=2 | **VERIFIED**（上轮 grok P2-4 **CLOSED**） |
| §5.2 已知简化表含 expiry | `STATUS.md` 两行：In-repo → `v3.0`；`ci_gate_command: null` → `v2.6.0-rc1` | **VERIFIED**（上轮 grok P2-5 **CLOSED**） |
| 「8 步」含非空 `evidence_commit` 且匹配 | 空串 → `E1_PRODUCED` | **CONTRADICTED**（P2-1） |
| 「物理文件位于项目根内，防路径穿越」 | `../<tmpdir>-evil/secret.md` → `E1_PRODUCED` | **CONTRADICTED**（P2-2） |
| 申请信封 `full_document.sha256` = 正文真实哈希 | 声称 `d599dca0…`；`sha256sum` = `e13b9bdf0741e354b9e3ac2eeb2c7dadddf05ef8827c24972cd5d2d6e4a2b695` | **CONTRADICTED**（P2-3；块标注 EXAMPLE） |
| `src/macao/adapter/pi.py` 本范围 +4 行 | `git diff 7bc8d70..e06d44c -- src/macao/adapter/pi.py` 空；`--provider` 引入于 `961bcfe` | 变更清单 **CONTRADICTED**（P3）；接线本身 **VERIFIED**（测试本轮新增） |
| live-run / L4 OPS | 三 Reviewer `mock-cli`；`auto_signoff: bool = True`；本范围未改 `live_runner.py` | L4 OPS **CONTRADICTED** |
| 全库已无 64 个 `0` 占位哈希 | 两份申请 `grep` 零命中 | 上轮 Pi-Qwen P1-C 全零形态 **CLOSED** |

独立反例摘要：

```text
probe_checkpoint_p104.py -> ALL_MATCH_CLAIM fail_open_cases=   # 上轮 P1-1 CLOSED
claude: zero/missing/empty/wrong_cli advanced=False
        adopt deadbeef git_cat_file_rc=128 cli_exit=1 success=False
qwen:   QW-7BC-P1-1a/b/c not-reproduced; control ACCEPTED/REJECTED
empty_evidence:   advanced=True  trigger=E1_PRODUCED   # P2-1
prefix_escape:    advanced=True  trigger=E1_PRODUCED   # P2-2
missing_evidence: advanced=False                       # schema required 生效
adopt deadbeef:   rc=1 UC-11 E1, no active task
adopt real HEAD:  WAITING_REVIEW + E2_ADOPT + TASK_ADOPTED
doctor missing yaml: rc=2
F-26 Claude no cwd: []
live_runner: mock-cli + auto_signoff=True               # L4
Ran 165 tests in 59.829s OK ; compileall 0 ; schema 8/8 SAME
claimed full sha e06d44c77c688bb7… -> bad object
actual  full sha e06d44cb31a0dbcb… -> show --check rc=0
```

---

## 3. 已确认与对齐项 (Verified & Aligned Items)

相对 `7bc8d70` 轮 grok 报告，下列原阻断 **本轮独立复放为闭环**：

- [x] **原 grok P1-1 / Codex P1-04**：`check_development_checkpoint` 对 `0*64`、空串、缺文件、非零篡改、仓外 `/etc/passwd`、错误 `executor.id`、错误 `executor.cli` 均保持 `CODING`。合法哈希 + 匹配席位 → `E1_PRODUCED`。`MockAgentAdapter` 改为落真实文档并计算 SHA-256。官方 `test_codex_p1_04_checkpoint_anti_forgery_fail_closed_battery` 覆盖上轮击穿面（仍未覆盖空 `evidence_commit` / 前缀穿越）。
- [x] **Codex/Claude/Pi-Qwen adopt 幽灵基线**：CLI 在 `WAITING_REVIEW` 目标下调用 `git.commit_exists`；不存在则打印 `UC-11 E1 Error` 并 `sys.exit(1)`。`Orchestrator.adopt_task` 同样校验。`TransitionTable` 注册 `E1_ADOPT` / `E2_ADOPT`。实放：`deadbeef` 无活动任务；真实申请 → `WAITING_REVIEW` 且审计含 `STATE_TRANSITION_E2_ADOPT`、`TASK_ADOPTED`。
- [x] **上轮 grok P2-2 审查 payload 验收标准**：`dispatch_review_in_worktree` 写入 `payload["acceptance_criteria"]` 与 `review_context`。
- [x] **上轮 grok P2-1 Claude 无 cwd**：`if not session_cwd: continue`（`session_locator.py:202-203`）。
- [x] **上轮 grok P2-4 doctor 缺配置**：`has_error = True` → `sys.exit(2)`。
- [x] **上轮 grok P2-5 §5.2 表**：`STATUS.md` 实例化 In-repo 与 `ci_gate_command: null`，含 expiry。
- [x] **上轮 grok P2-3 adopt 旁路 FSM**：已下沉 `adopt_task` + `fsm.transition`。
- [x] **Pi-Qwen P1-C 全零占位**：两份申请正文不再含 64 个 `0`。
- [x] **既有引擎场景测试未回退**：165/165 含共识/超时/返工/E2E mock。
- [x] **provider 架构**：双侧 `macao_config.schema.json` 增加 `provider`；`OpenCodeAdapter` 组合 `-m {provider}/{model}`（单测断言 `deepseek/deepseek-chat`）；`PiAdapter --provider` 在 `961bcfe` 已存在，本轮补了单测。

上轮 L4 mock **未闭**。

---

## 4. 阻断性缺陷 (P0 / P1 Blocking Issues)

未发现 P0。未发现达到 §8.1 P1 的新路径（无静默自动合并；UC-3 d5 正文哈希门与 d6 含 cli 的归属门在生产入口上成立）。

上轮唯一 L3 阻断 **P1-1 已闭环**，见第 3 节。残留洞按可达性记 P2，见第 6 节。

---

## 5. L4 / PG-3 与 §7.2 OPS 矩阵（单独否决）

本范围 **未修改** `src/macao/workflow/live_runner.py`。指引 §2.1 / §3.3 / §7.2：L4 需要 OPS VERIFIED、用户可见人工接管、且 P0/P1 为零。缺任一行视为证据不完整。申请未按十行逐格提交 OPS 证据。

| # | 场景 | 本轮 | 判定 |
|---|---|---|---|
| 1 | 守护进程单次扫描 + 超时弃权 | 代码仍在 `daemon.py`；本范围无实机扫描日志 | CODE 沿用 **PARTIALLY_VERIFIED**；OPS **CLAIM_ONLY** |
| 2 | 常驻循环内部异常 | 未在本 commit 重放 | 沿用 **PARTIALLY_VERIFIED** |
| 3 | Reviewer PTY 中途断开 | 无本轮故障注入 | **UNKNOWN** |
| 4 | Worktree 创建失败 | 未改 `create_isolated_worktree` | CODE 沿用 **VERIFIED**；OPS 未演练 |
| 5 | 崩溃后冷重启 | 未在 `e06d44c` 重放 | 沿用 **PARTIALLY_VERIFIED** |
| 6 | 并发写 `state.db` | 未对打 | CODE 沿用 **PARTIALLY_VERIFIED** |
| 7 | 磁盘写失败 | 无 ENOSPC 反例 | **UNKNOWN** |
| 8 | 演练后清理 | 未做残留巡检 | **UNKNOWN** |
| 9 | 人工接管 `macao override resolve` | 命令存在；申请无真实人类输入全程留痕 | **CLAIM_ONLY** |
| 10 | 端到端真实性 / 禁止 mock 合成票 | `live_runner.py:56-58` 三 Reviewer `mock-cli`；`:76` `auto_signoff: bool = True` | **CONTRADICTED** |

第 10 行单独足以拒绝 L4 / PG-3。与 `d042395` / `961bcfe` / `7bc8d70` 轮 grok 同一条 OPS 判据。已知简化表 **未** 将 mock live-run 登记为可豁免项。

---

## 6. 建议性问题 (P2 / P3 Advisory Issues)

未在 `STATUS.md` 按 §8.3 做风险接受登记的条目，下一轮仍须面对，但不阻断本轮 L3。

### P2-1 空串 `evidence_commit` 跳过提交绑定（宣称的 8 步第 3/4 步未闭合）

- **位置**: `src/macao/workflow/orchestrator.py:396-400`（`if evidence_commit and evidence_commit != latest_commit`）；官方电池 `tests/test_p1_closures_and_regressions.py:631-738` 测了错误 evidence 值，**未**测 `""`
- **现象**: `full_document.evidence_commit: ""` 时 schema 仍过（字段存在、`type: string`、无 `minLength`），运行时把空串当假值跳过比对，任务 `E1_PRODUCED` → `READY_FOR_REVIEW`。缺键会被 schema 拒绝（`missing_evidence` 本机 `advanced=False`）。`checkpoint_ref == latest_commit` 与文件 sha256 仍有效，故不升 P1。
- **复现**: `probe_e06d44c.py` 用例 `empty_evidence`
- **修复建议**: `if not evidence_commit or evidence_commit != latest_commit: return None`；schema 给 `evidence_commit` / `sha256` 加 `minLength: 1` 与 sha256 pattern；官方电池加空串行。

### P2-2 路径沙箱用 `startswith`，兄弟目录前缀可逃逸

- **位置**: `orchestrator.py:405-407`
- **现象**: 仓根 `/tmp/e06_XXX` 时，`path: ../e06_XXX-evil/secret.md` 的 `resolve()` 结果仍以仓根字符串为前缀，文件存在且哈希匹配则放行。`../../etc/passwd` 仍被拒（官方第 9 变体因此假绿）。
- **复现**: `probe_e06d44c.py` 用例 `prefix_escape`
- **修复建议**: `doc_path.is_relative_to(self.root.resolve())`（或 `os.path.commonpath`），禁止依赖前缀匹配。

### P2-3 申请机器信封与验证命令自证失败

- 完整 SHA 写成不存在的 `e06d44c77c688bb715bb997a3cf556bc91f6920f`；§3.3 命令按原文不可执行。
- 示例 `sha256: d599dca0…` 与文件实际 `e13b9bdf0741e354b9e3ac2eeb2c7dadddf05ef8827c24972cd5d2d6e4a2b695` 不符。块虽标 EXAMPLE，申请同时写「以物理文件的真实 64 位 SHA-256 签名」。哈希写在被哈希文件内部时不可能自洽，应改为独立 `.dev.yml` 产物或明确「示意、勿对账」。
- 上轮 `7bc8d70` 申请现写 `914ecd52…`（当时含全零正文的旧哈希），当前文件实际 `ec7cacc8d50cafb433ce54f911fe856b7988895808a13ffd683e5cadb330f8c0`。全零形态已消失，对账仍失败。

### P2-4 L4 runner 仍 mock（同时是 L4 阻断，不升本轮 L3 P1）

见第 5 节。`live_runner.py` 本范围零 diff。

### P2-5 Pi 会话无 `cwd` 仍回填查询仓（F-26 未扩到 Pi）

- **位置**: `session_locator.py:457-474`（有 cwd 才校验；无 cwd 仍 `workspace: str(session_cwd or resolved_proj)` 并入列）
- 本轮只宣称修 Claude；Claude 路径已 fail-closed。Pi 残留记 P2。

### P2-6 未知 CLI 降级探活仍不点名（Qwen QW-7BC-P2-1 仍 CONFIRMED）

`probe --json --allow-degraded` 对 `custom-claude` 退出码 2，但 stdout/stderr 不含 CLI 名或 `MISSING`。不阻断 L3。

### P2-7 `dev_manifest.schema.json` 的 `sha256` 仍无 64 位正则

运行时已拒全零与非十六进制；契约层仍 fail-open。Codex 上轮 P2 残留。

### P3

- P3-1：范围说明漏 `a705a49`。
- P3-2：信封把 `pi.py` 写成未轮改动；`--provider` 属 `961bcfe`。
- P3-3：STATUS 页眉 155/45 对，文内登记表标题仍写「142 份结论 + 41 份申请」；「专家脚本 100%」被 Codex 复现脚本证伪。
- P3-4：`test_task_adopt.py` 6 项（处置单写 6/6，申请未再写 7，上轮 P3 计数已对齐）。
- P3-5：`workspace: str(session_cwd or resolved_proj)` 在 Claude 分支已是死代码。

---

## 7. 前序条目逐条对照（避免「全部闭环」被误读）

| 来源 | 本轮机验 | 定级影响 |
|---|---|---|
| grok `7bc8d70` P1-1 检查点全零/空/缺文件/cli | **CLOSED** | 解除 L3 阻断 |
| Codex P1-7bc8d70-01 / Claude P1-2 adopt 幽灵基线 + FSM | **CLOSED** | 不阻断 |
| grok P2-2 审查 payload 验收标准 | **CLOSED** | — |
| grok P2-1 Claude 无 cwd | **CLOSED**（Pi 仍回填 → 新 P2-5） | — |
| grok P2-3 adopt 旁路 FSM | **CLOSED** | — |
| grok P2-4 doctor rc | **CLOSED** | — |
| grok P2-5 §5.2 表 | **CLOSED** | — |
| Pi-Qwen P1-C 全零占位 | 全零形态 **CLOSED**；真实哈希对账 **未闭** → P2-3 | 不阻断 L3 |
| grok L4 mock-cli | **未闭** | 单独拒 L4 |
| Qwen 未知 CLI 诊断静默 | **未闭** → P2-6 | 不阻断 |

---

## 8. 建议闭环顺序与验收

1. **P2-1 / P2-2**（建议同轮，避免下一轮再把「8 步」写成已闭环）：空 `evidence_commit` fail-closed；`is_relative_to` 替换 `startswith`；官方电池各加一行。验收：`probe_e06d44c.py` 对 `empty_evidence` / `prefix_escape` 均为 `advanced=False`，且 `good` 仍为 True。
2. **L4**：真实 CLI 至少一轮非全同意；人类路径 HOLD → `macao override resolve`；按 §7.2 十行填证据。不要再拿 `mock-cli` live-run 申请 PG-3。
3. **文档**：申请只写 `git rev-parse` 得到的完整 SHA；示例信封不要声称等于载有该哈希的同一文件；STATUS 不要写「专家脚本 100%」除非复现脚本已改成闭包断言（Codex 脚本目前断言漏洞仍在）。

---

## 9. 准入建议

- **本轮增量**：**授予** L3 SCENARIO-VERIFIED / PG-2。上轮阻断本增量的检查点 fail-open 与 adopt E1 已独立复放闭环；165 项场景测试全绿。
- **既有编排引擎**：**维持** L3 SCENARIO-VERIFIED / PG-2。
- **L4 RELEASE-READY / PG-3**：**拒绝**。§7.2 第 9–10 行未满足；mock live-run 不在已知简化表内。
- 「8 步硬核」表述本轮最高记 **PARTIALLY_VERIFIED**，不得在 STATUS 写成已全部闭环。

本票是对 L3 的 `YES_APPROVE`，**不是**对 L4 的有条件通过（指引对「有条件通过」视为不通过）。L4 必须另走一轮带 OPS 证据的申请。

---

## 10. 复现脚本与命令

- 归档目录：`docs/reviews/evidence/2026-09-09-e06d44c-grok/`
- 最后执行：2026-09-09T00:44:04+08:00
- 完整 SHA（实际）：`e06d44cb31a0dbcbe199e6bb124430e9701e087f`
- 外部前提：无网络、无厂商 CLI 额度；Python 3.10+；系统 git/sqlite3

```bash
cd /home/debian/macao
git rev-parse e06d44c
git show --check e06d44cb31a0dbcbe199e6bb124430e9701e087f
PYTHONPATH=src python3 -m compileall -q src tests
PYTHONPATH=src python3 -m unittest discover tests
PYTHONPATH=src python3 -m unittest tests.test_schema
PYTHONPATH=src python3 docs/reviews/evidence/2026-09-08-7bc8d70-grok/probe_checkpoint_p104.py
PYTHONPATH=src python3 docs/reviews/evidence/2026-09-08-7bc8d70-claude/probe_checkpoint_and_adopt.py
PYTHONPATH=src python3 docs/reviews/evidence/2026-09-08-7bc8d70-qwen/repro_7bc8d70_qwen.py
PYTHONPATH=src python3 docs/reviews/evidence/2026-09-09-e06d44c-grok/probe_e06d44c.py
sha256sum docs/reviews/2026-09-09-review-request-e06d44c.md
```

---

## 11. Reviewer 自审记录 (Self-Audit Log)

- [x] 已对照 `7bc8d70..e06d44c` 36 个文件与申请清单（含漏列的 `a705a49` 与未改的 `pi.py`）
- [x] 已串行执行 `unittest discover tests`（165/165）与 `compileall` 与 schema 8/8
- [x] 已重放上轮 grok/Claude/Qwen 探针；未把 Codex 仍断言旧漏洞当成「修复失败」
- [x] 已用新脚本击穿空 `evidence_commit` 与前缀穿越，并按 §8.2 降为 P2 而非阻断 L3
- [x] 未发现未报告的 P0
- [x] 未在宿主仓执行会写状态的 `task adopt` / `task create`
- [x] `git show --check` 使用实际完整 SHA，并记录申请伪造 SHA 的 rc=128

---

## 伴随机器信封：`.macao/.reviews/r4/grok.review.yml`

```yaml
version: "1.0"
task_id: "task-20260909-checkpoint-antiforgery-adopt-e1-provider-support"
checkpoint_ref: "e06d44c"
review_round: 4
reviewer:
  id: "grok"
  role: "reviewer"
  cli: "cursor-grok"
vote: "YES_APPROVE"
opinion:
  status: "APPROVED"
  confidence: 0.91
  summary: "上轮 P1 检查点 fail-open 与 adopt 幽灵基线已独立复放闭环，授予本轮增量 L3/PG-2；空 evidence_commit 与 startswith 前缀穿越降 P2；L4 因 live-run mock-cli 与 §7.2 矩阵未填而否决。申请完整 SHA 在仓库中不存在。"
full_document:
  path: "docs/reviews/2026-09-09-review-result-e06d44c-grok.md"
  evidence_commit: "e06d44c"
  sha256: "da2e12876ec5d5e08591ee91e3fde44e36709583c478bc28e0a242dac5ecf60c"
items:
  - issue_id: "grok/L4-OPS"
    disposition_class: "MUST_FIX"
    severity: "blocker"
    title: "L4 only: live-run still hardcodes mock-cli reviewers and default auto_signoff=True; §7.2 matrix not evidenced"
  - issue_id: "grok/P2-1"
    disposition_class: "SHOULD_FIX"
    severity: "major"
    title: "Empty evidence_commit skip-compares and still advances to READY_FOR_REVIEW"
  - issue_id: "grok/P2-2"
    disposition_class: "SHOULD_FIX"
    severity: "major"
    title: "Path sandbox uses str.startswith; sibling directory with repo-name prefix escapes"
  - issue_id: "grok/P2-3"
    disposition_class: "SHOULD_FIX"
    severity: "major"
    title: "Review request full SHA is not a git object; example sha256 does not match the file"
```
