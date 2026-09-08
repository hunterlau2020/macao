# MACAO Round 3 复审结论（`7bc8d70` / `961bcfe..7bc8d70`）

- **文档归档路径**: `docs/reviews/2026-09-08-review-result-7bc8d70-grok.md`
- **审查日期 (Review Date)**: 2026-09-08
- **审查专家 (Reviewer)**: grok（独立复审；不采信申请粘贴输出，不采信 `STATUS.md` 定级句，不采信处置单「ALL CLOSED」，不采信其他专家票）
- **被审 Commit (Checkpoint Ref)**: `7bc8d7091ba4e39c0b3282492c613817f8d664e9`
- **工作区 HEAD**: `a705a4923b76fbc253644bbdbecba7f2987270ff`（仅多 2 个文档文件：本申请与 STATUS 更新；`src/` / `tests/` 与 `7bc8d70` 逐字节相同）
- **审查轮次 (Review Round)**: `3`
- **评审对象**: [`docs/reviews/2026-09-08-review-request-7bc8d70.md`](2026-09-08-review-request-7bc8d70.md)
- **前序基线**: `961bcfe`；前序 grok 报告 [`2026-09-07-review-result-961bcfe-grok.md`](2026-09-07-review-result-961bcfe-grok.md)（**NO_APPROVE**；阻断为场景 C 操作面 + Claude 目录名回退 + L4 mock）
- **对齐基准**: `docs/MACAO_REVIEW_GUIDELINES.md` v1.1 §2–§4、§7.2、§8–§9；UC-3 d5/d6；UC-2 E7 / UC-11；`PRODUCT-FACTS.md` F-24/F-25/F-26
- **目标定级**: L3 SCENARIO-VERIFIED / PG-2 全量认证，并提请 L4 RELEASE-READY / PG-3
- **审查结论 (Verdict)**: **不授予本轮增量 L3 全量认证；拒绝 L4 / PG-3**。既有编排引擎 L3 / PG-2（`4e38ed6` 轮）维持。
- **最终投票 (Vote)**: `NO_APPROVE`
- **证据**: `BLOCKING` × 1（P1）；L4 OPS 缺口维持；`ADVISORY` × 若干；**无 P0**
- **复现归档**: [`docs/reviews/evidence/2026-09-08-7bc8d70-grok/`](evidence/2026-09-08-7bc8d70-grok/)

**结论：前序 grok 在 `961bcfe` 上的两条产品 P1（场景 C 操作面、Claude basename 串话）以及四方清单里的未知 CLI / WAL 侧车 / E7 / `task adopt` / Pi·Cursor 接线，本轮独立沙箱均翻转为真。阻断收窄到申请自称「彻底闭环」的 Codex P1-04：`check_development_checkpoint` 对全零哈希、空哈希、缺失正文文件显式跳过校验，任务仍从 `CODING` 进入 `READY_FOR_REVIEW`。官方回归只覆盖「非零篡改 vs 正确哈希」，是假绿。L4 仍被 `live-run` 的 `mock-cli` + 默认 `auto_signoff=True` 否决；申请也未按 v1.1 §7.2 填满 10 行 OPS 矩阵。**

---

## 0. Reviewer 自审

- 不采信申请 §3「162/162、14 项 P0/P1 全部闭环、0 WAL」、处置单「ALL CLOSED」、STATUS「全面具备待落票」。
- 对前序 grok P1-1/P1-2 与申请 Focus 1–5 写独立反例；Codex P1-04 用**每个反例一枚新 CODING 任务**，避免全零哈希先推进后把后续断言全部变成 `None`。
- 全量测试与独立探针均在 `tempfile.mkdtemp()` 沙箱或 `CliRunner` 临时目录执行；对宿主仓只跑了 `probe --dry-run --allow-degraded` 与一次不带该开关的 `probe --dry-run`（未新建 `state.db-wal`/`-shm`）。
- **漏审登记**：无连续同类漏审。本轮强制项是指引 §9 B（测试只打篡改哈希就把 P1-04 写成已闭环）与 §9 E（`acceptance_criteria` 写进申请「审查员上下文」，派发 payload 零字段）。

强制自检：

| # | 项 | 本轮 |
|---|---|---|
| 1 | 字段/路径 vs 实际读取 | `full_document.sha256` 仅在「文件存在且值 ≠ 64 个 `0`」时比对；`executor.cli` 从未读取 |
| 2 | 「已完成 / 100% / 全绿」 | 162/162 **VERIFIED**；「Codex P1-04 彻底闭环」「L4 准入」**CONTRADICTED** |
| 3 | 确定性用语 | 「0 字节写入」「严格校验必须吻合」未标目标；后者被反例击穿 |
| 4 | YAML/JSON Schema | 8 份契约 docs↔src 逐字节一致 **VERIFIED**；`dev_manifest.sha256` 仍只是 `type: string`，不拒全零 |
| 5 | P1 均附路径与复放 | 是 |
| 6 | 生产调用方 | `macao task checkpoint` → `check_development_checkpoint` **已接线**；漏洞在生产路径上 |
| 7 | 参照系 | 测试在干净临时 git 仓；`git show --check 7bc8d70` 而非 `git diff --check`；负向断言看状态是否仍为 `CODING` |

---

## 1. 结论综述 (Executive Summary)

`48eea58` 相对 `961bcfe` 是一轮有效的 Fail-Closed 返工：未知 CLI 不再借壳 `READY`；只读 URI 加 `immutable=1` 后 WAL 仓 dry-run 不再长出 sidecar；Claude 短名回退已删；探活 UI 与 `task create` 终于跟三元组同一套 pending 优先序；`macao task adopt` 作为 Click 子命令存在，`--dry-run` 零落盘；`start_task` 下沉单活动任务；Pi/Cursor 能从 `LiveAgentDispatcher.get_adapter_for_reviewer` 构造出来。这些都可以被独立脚本证伪为已修，不能再用旧 grok 报告原样重开。

本轮增量 **不能** 授予 L3 全量认证，因为申请把 Codex P1-04 写成「`sha256` 必须为合法 64 位十六进制且与正文吻合；`executor.id` 与 `executor.cli` 必须与主执行席位一致」，而生产函数对占位全零、空串、缺失文件直接放行。这正是 UC-3 d5「对不上即无效信封」与 Codex 原文要求的「全零/错误 hash、外部路径、错误 executor 负向测试」未完成的部分。官方 `test_checkpoint_full_document_sha256_validation` 从未构造 `0*64`。

L4 / PG-3：`src/macao/workflow/live_runner.py` 三名 Reviewer 仍为 `cli: "mock-cli"`，`run_live_cycle(..., auto_signoff: bool = True)`。指引 v1.1 §7.2 第 10 行禁止 runner 内部合成审查意见；第 9 行要求人工 `override resolve` 实机留痕。申请未给出该矩阵任一行的独立 OPS 证据。

方法论 v1.1 正文本身（§3.4/§3.5/§5.2/§7.2/§8/§9）作为文档增量 **DOC 对齐可接受**，但作者用它当本轮判据的同时，既未在 `STATUS.md` 实例化 §5.2 已知简化表，也未按 §7.2 自检 L4。这不单独升 P1，但使「提请 L4」失去格式资格。

---

## 2. 申请机验（独立复跑，不采信粘贴）

| 声明 | 本机 | 判定 |
|---|---|---|
| 范围 `961bcfe..7bc8d70` 30 files / +2765 / -226 | `git diff --stat` 一致；两提交为 `48eea58` + `7bc8d70` | **VERIFIED** |
| 受审 SHA `7bc8d70` = 完整 `7bc8d7091ba4e39c0b3282492c613817f8d664e9` | 一致。工作区 HEAD 已是 `a705a49`（本申请入库），源码树与 `7bc8d70` 相同 | **VERIFIED**（代码口径钉在 `7bc8d70`） |
| `git show --check 7bc8d70` rc=0 | rc=0；`48eea58` 同样 rc=0 | **VERIFIED**（参照系正确，未用 `git diff --check`） |
| `PYTHONPATH=src python3 -m unittest discover tests` 162/162 | `Ran 162 tests in 56.252s OK` | **VERIFIED** |
| `python3 -m compileall -q src tests` | rc=0 | **VERIFIED** |
| 双 Schema 8 份逐字节一致 | `docs/schemas/*.schema.json` ↔ `src/macao/schemas/` 8/8 SAME | **VERIFIED** |
| P0-1 未知 CLI `custom-claude` 不得 READY | `status=MISSING`，`not in ADAPTER_MAP`，`can_dispatch=False` | **VERIFIED** |
| P1-2 WAL dry-run 零 sidecar（WAL 模式库 + 宿主仓） | 临时 WAL 库 dry-run 前后文件集相等；宿主 `.macao/state.db*` 未新增 `-wal`/`-shm` | **VERIFIED**（前序 grok P2-4 / 本轮 P1-2） |
| 场景 C：`task adopt` 存在；pending+脏树 UI 不推荐 `task create`；E7 拒绝 create | `task --help` 含 adopt；CLI 输出 `Run 'macao task adopt'` 且无 `UNTRACKED DEV`；`task create` rc=1 含 `UC-2 E7`；adopt `--dry-run` 零新文件；adopt `--no-review` → `WAITING_REVIEW` | **VERIFIED**（前序 grok P1-1 **CLOSED**） |
| Claude 禁止 basename 回退 | 仅有 `~/.claude/projects/-macao` 时查询 `/home/debian/macao` 得 `[]`；规范目录内 `cwd=/home/other/repo` 被丢弃 | **VERIFIED**（前序 grok P1-2 **CLOSED**） |
| Codex P1-04「sha256 必须吻合、全零/缺失必须拒绝」 | 独立任务：`0*64` / 空串 / 缺失文件 → **推进 `READY_FOR_REVIEW`**；非零篡改与错误 `executor.id`、仓外路径 → 阻断；错误 `executor.cli` → 放行 | **CONTRADICTED**（P1-1） |
| 「验收标准原样透传至审查员上下文」 | `live_dispatcher.py` 审查 payload 无 `acceptance_criteria` 字段 | **CONTRADICTED**（P2，原 Codex 执行者路径已修） |
| live-run / L4 OPS | 三 Reviewer `mock-cli`；`auto_signoff: bool = True` | L4 OPS **CONTRADICTED** |
| 申请信封 `full_document.sha256` | 申请写 `0*64`；文件实际 SHA-256 = `914ecd52415aaa083dd8e6215fa5fd3739c9157640ef3ffcfac31b70700399e1` | **CONTRADICTED**（与 P1-1 同源） |
| `test_task_adopt.py` 7 项 | 该文件 5 个 `test_*` | 计数 **CONTRADICTED**（P3） |
| §5.2 已知简化表已登记 | `STATUS.md` 无 expiry/owner 表；仅出现在申请自评 | **CONTRADICTED**（P2） |

独立反例摘要：

```text
custom-claude reviewer -> MISSING, can_dispatch=False                 # P0-1 closed
Claude basename -macao + query /home/debian/macao -> []              # grok P1-2 closed
pending+dirty UI -> adopt, no UNTRACKED DEV; create rc=1 UC-2 E7    # grok P1-1 closed
adopt --dry-run new_files=[]; adopt --no-review -> WAITING_REVIEW
WAL-mode state.db + probe --dry-run -> no -wal/-shm                  # P1-2 closed
host probe --dry-run -> rc=0, no new state.db sidecars
check_development_checkpoint:
  sha=0*64           -> READY_FOR_REVIEW   # FAIL-OPEN
  missing path       -> READY_FOR_REVIEW   # FAIL-OPEN
  sha=""             -> READY_FOR_REVIEW   # FAIL-OPEN
  executor.cli mismatch -> READY_FOR_REVIEW
  executor.id mismatch  -> stays CODING    # id check works
  tampered non-zero     -> stays CODING
  path=/etc/passwd      -> stays CODING
live_runner reviewers cli=mock-cli ; auto_signoff=True               # L4
Ran 162 tests in 56.252s OK ; compileall 0 ; schema 8/8 SAME
```

---

## 3. 已确认与对齐项 (Verified & Aligned Items)

相对 `961bcfe` 轮 grok 报告，下列原阻断 **本轮独立复放为闭环**（不抵消第 4 节新 P1）：

- [x] **原 grok P1-1 场景 C 操作面**：`ui.py:351-398` 先看 `has_pending_request` 再看脏树；`task create` 在 `main.py:405-414` 实现 UC-2 E7；`task adopt` 注册于 `main.py:485`。脏树+1/3 落票的 CLI 全文含 adopt、不含 `UNTRACKED DEV`。
- [x] **原 grok P1-2 Claude basename**：`_find_claude_sessions` 在规范化目录不存在时 `return []`（`session_locator.py:155-156`），无 `-<dirname>` 回退。
- [x] **P0-1 未知 CLI**：`TeamProber._get_adapter` 仅 `ADAPTER_MAP.get(cli_name.lower())`（`prober.py:55-62`）。`custom-claude` 为 `MISSING`。
- [x] **P1-2 WAL sidecar**：只读连接 `mode=ro&immutable=1`（`prober.py:75`、`session_locator.py:232/286`、`cli/main.py:314`）。WAL 仓与宿主仓 dry-run 均无新 sidecar。
- [x] **P1-3 脱敏扩展**：`secrets.py` 含 JWT/AWS/Bearer/DB URL/PEM；SessionLocator 走 `mask_secrets`。申请所列样本无泄漏。
- [x] **P1-5 clean 幽灵 worktree**：`git worktree remove` + `prune`（`main.py:1218-1239`，`git_utils.py:140-144`）。复放后 porcelain 不含已删 worktree。
- [x] **P1-6 单活动任务**：`Orchestrator.start_task` 无 `force` 时对 `get_active_tasks()` 抛 `RuntimeError`（`orchestrator.py:156-162`）；CLI `--no-probe` 第二条 create rc=1。
- [x] **P1-7 进程退出码（probe）**：缺 `macao.yaml` / 坏 YAML 时 probe rc=2。
- [x] **P1-9 pending > 脏树**：三元组 `REVIEW_PENDING`；E7 见上。
- [x] **P1-10 / Codex P1-01·02 接线**：`get_adapter_for_reviewer` 对 `pi` / `cursor` 可构造；Pi/Cursor `inject_task` 改读 `acceptance_criteria`。
- [x] **Codex P1-03 `task adopt`**：命令存在；dry-run 零新文件；pending → `WAITING_REVIEW` 并写 `TASK_ADOPTED`。
- [x] **F-25/F-26 文本入库**：`PRODUCT-FACTS.md` 第 25–26 条存在（实现与 F-26「无 cwd 即空列表」仍有字面差，见 P2-1）。
- [x] **既有引擎场景测试未回退**：162/162 含共识/超时/返工/E2E mock。
- [x] **方法论 v1.1 章节落地**：§3.4、§3.5、§5.2、§7.2、§8.1–§8.3、§9 模式 E 均在 `docs/MACAO_REVIEW_GUIDELINES.md` 正文。

Codex P1-04 **部分**成立：非零篡改哈希、仓外路径、错误 `executor.id` 会阻断。这不够称为闭环。

---

## 4. 阻断性缺陷 (P0 / P1 Blocking Issues)

未发现 P0（无静默自动合并、无再把 `tests_passed` 写死为 true）。

### P1-1 Codex P1-04 未闭环：检查点在全零/空/缺失正文哈希上 fail-open，仍可进入 `READY_FOR_REVIEW`

- **位置**:
  - `src/macao/workflow/orchestrator.py:287-300`（`doc_sha != "0" * 64` 才比对；文件不存在则整段跳过）
  - `src/macao/workflow/orchestrator.py:302-308`（只比 `executor.id`，从不读 `executor.cli`）
  - 生产入口：`src/macao/cli/main.py:754` `check_development_checkpoint`
  - 假绿测试：`tests/test_p1_closures_and_regressions.py:578-627`（只覆盖非零篡改 vs 正确哈希）
  - UC-3 d5/d6：`docs/usercases/UC3-dev-checkpoint.md`（路径必须存在且字节级 sha256 对得上）
  - 本申请信封：`docs/reviews/2026-09-08-review-request-7bc8d70.md:192` 仍为 64 个 `0`
- **严重级别**: `P1` (BLOCKING) — §8.1 票面/审计锚点完整性；§8.2 在线真实可达（CLI checkpoint）
- **现象描述**:
  1. 申请与处置单写「`full_document.sha256` 必须为合法 64 位十六进制且与正文吻合」。实现把占位全零当成「跳过校验」的显式后门。
  2. `full_document.path` 指向不存在的文件、或 `sha256` 为空串时，同样跳过，任务照样 `E1_PRODUCED` → `READY_FOR_REVIEW`。
  3. 申请还写「强制校验 `executor.cli`」。代码只比较 `executor.id`。`cli: claude-code` 配在 `dev-mock` 席位上仍然放行。
  4. 官方回归从未构造 `0*64` / 缺失文件 / 错误 cli。Codex 原文要求的「全零/错误 hash」负向测试未落地。按 §8.3「测试不得只打 happy 修补面」与 §9 B，这是把计划完成写成已完成。
- **复现证据 / 命令**（2026-09-08 实跑，归档 `probe_checkpoint_p104.py`）:

```text
PYTHONPATH=src python3 docs/reviews/evidence/2026-09-08-7bc8d70-grok/probe_checkpoint_p104.py

zero_hash:     advanced=True  trigger=E1_PRODUCED   # 必须阻断
missing_path:  advanced=True  trigger=E1_PRODUCED   # 必须阻断
empty_sha:     advanced=True  trigger=E1_PRODUCED   # 必须阻断
wrong_cli:     advanced=True  trigger=E1_PRODUCED   # 相对申请声明必须阻断
wrong_id:      advanced=False                       # 此项已修
tampered:      advanced=False                       # 非零篡改已修
outside_path:  advanced=False                       # 仓外路径已修
good:          advanced=True                        # happy path
FAIL_OPEN
fail_open_cases=zero_hash,missing_path,empty_sha,wrong_cli
```

- **修复建议**:
  1. 删除 `doc_sha != "0" * 64` 后门。`sha256` 必须匹配 `^[0-9a-fA-F]{64}$` 且等于文件字节哈希；缺字段、空串、全零、文件不存在一律保持 `CODING` 并给出原因（不要静默 `return None` 与「测试未通过」混写）。
  2. 若坚持校验 `executor.cli`，与 `macao.yaml` `team.executor.cli` 做精确比较；否则从申请/处置单删除该句。
  3. 回归必须含：全零、空串、缺失文件、错误 id、错误 cli、仓外路径、1 字节篡改正文。全部走 `macao task checkpoint` 或至少 `check_development_checkpoint` 且任务仍为 `CODING`。
  4. 下一份申请信封填写真实 SHA-256（本文件当前为 `914ecd52415aaa083dd8e6215fa5fd3739c9157640ef3ffcfac31b70700399e1`）。

---

## 5. L4 / PG-3 与 §7.2 OPS 矩阵（单独否决）

指引 §2.1 / §3.3 / §7.2：L4 需要 OPS VERIFIED、用户可见人工接管、且 P0/P1 为零。缺任一行视为证据不完整。

| # | 场景 | 本轮 | 判定 |
|---|---|---|---|
| 1 | 守护进程单次扫描 + 超时弃权 | `OrchestratorDaemon.scan_once` 对超时写 `REVIEWER_TIMEOUT_ABSTAIN` 后走共识（`daemon.py:24-55`）。无本轮实机扫描日志 | CODE **PARTIALLY_VERIFIED**；OPS **CLAIM_ONLY** |
| 2 | 常驻循环内部异常 | `except Exception` 写 stderr（`daemon.py:65-68`），**不写审计事件**。非裸 `pass`，未满足「审计事件与 stderr」双写 | **PARTIALLY_VERIFIED** |
| 3 | Reviewer PTY 中途断开 | 无本轮故障注入。历史有 extractor/超时测试，不能外推本提交 | **UNKNOWN** |
| 4 | Worktree 创建失败 | `GitManager.create_isolated_worktree` 失败抛 `RuntimeError`（`git_utils.py:123-131`），无静默回退主仓 | CODE **VERIFIED**；OPS 未演练 |
| 5 | 崩溃后冷重启 | `StateReconciler` / 既有恢复测试沿用历史轮次，未在 `7bc8d70` 重放 | 沿用 **PARTIALLY_VERIFIED**（最后验证不在本 commit） |
| 6 | 并发写 `state.db` | 写连接 `PRAGMA journal_mode=WAL` + `timeout=30`（`db.py:112-114`）。无多进程对打 | CODE **PARTIALLY_VERIFIED** |
| 7 | 磁盘写失败 | 无 ENOSPC/只读盘反例 | **UNKNOWN** |
| 8 | 演练后清理 | dispatcher 在成功路径会摘 worktree；本轮未做残留进程/锁巡检 | **UNKNOWN** |
| 9 | 人工接管 `macao override resolve` | 命令存在（`main.py:966-984`）。申请未提供真实人类输入全程留痕 | **CLAIM_ONLY**（§7.2 第 9 行未满足） |
| 10 | 端到端真实性 / 禁止 mock 合成票 | `live_runner.py:56-58` 三 Reviewer `mock-cli`；`:76` `auto_signoff: bool = True` | **CONTRADICTED** |

即使 P1-1 当天修好，本矩阵仍单独阻断 L4。与 `d042395` / `961bcfe` 轮 grok 第五节同一条 OPS 判据。

---

## 6. 建议性问题 (P2 / P3 Advisory Issues)

未在 `STATUS.md` 按 §5.2 / §8.3 登记 expiry 的条目，**不能**当已知简化豁免。

- `P2-1` **F-26 字面未兑现**：无 `cwd` 的 Claude jsonl 仍写入 `workspace: str(session_cwd or resolved_proj)`（`session_locator.py:217`）。规范目录匹配避免了前序跨仓串话，但 F-26 禁止「回填当前项目路径」。可达，影响小于跨仓泄漏，故 P2。
- `P2-2` **申请「透传至审查员」未接线**：`live_dispatcher.py:274-283` payload 只有 diff/checkpoint。Pi/Cursor **执行者** `inject_task` 已改读 `acceptance_criteria`（原 Codex P1-01 这部分 CLOSED）。§9 模式 E。
- `P2-3` **`task adopt` 绕过 TransitionTable**：`store.create_task`（IDLE）后 `update_task_state(..., WAITING_REVIEW)`（`main.py:590-602`），无 `fsm.transition`。F-24 允许接管到 `WAITING_REVIEW`，但 E1/E2 审计链缺席。默认 `--review` 还可能用文件名里的短 SHA 去 `worktree add`（失败被 per-reviewer `except` 吃掉，任务仍留下）。
- `P2-4` **doctor 缺 `macao.yaml` 仍 rc=0**：只打黄字。申请把「非法配置」写成 probe/doctor 一律非零；probe 缺配置 rc=2 已成立。
- `P2-5` **§5.2 表未实例化**：指引本轮才要求 STATUS/PRD 附录含 expiry。申请自评两条（In-repo、`ci_gate_command=null`）没有 owner/expiry，不能当豁免。
- `P2-6` **Last 仍不跳过 chore/docs**（`prober.py:188` 只跳 `docs(review)`）。上轮 P2，未动。
- `P2-7` **`PiAdapter.preflight` 仍 `auth_valid=True`**（`pi.py:65`）；空版本改写 `detected` 优于上轮写死 `0.85.1`，认证仍 fail-open。
- `P2-8` **向导在 PATH 无 CLI 时仍填虚构候选**（上轮 P2-3，未作为本范围焦点复放）。
- `P3-1` `test_task_adopt.py` 5 项，申请写 7 项。
- `P3-2` `AGENTS.md:14` 仍写 126 tests，同文件命令区写 162。
- `P3-3` STATUS 把前序 grok 票概括成 WAL/多任务/退出码；原文阻断是场景 C + Claude。对账口径继续漂移。
- `P3-4` 本申请机器信封 `sha256` 全零、`tests_passed: true`，与 P1-1 叙事并置。

---

## 7. 前序条目逐条对照（避免「全部闭环」被误读）

| 来源 | 本轮机验 | 定级影响 |
|---|---|---|
| grok `961bcfe` P1-1 场景 C | **CLOSED** | 不阻断 |
| grok `961bcfe` P1-2 Claude basename | **CLOSED** | 不阻断 |
| grok L4 mock-cli | **未闭** | 单独拒 L4 |
| Pi-Qwen/Kimi P0-1 未知 CLI | **CLOSED** | 不阻断 |
| WAL sidecar | **CLOSED** | 不阻断 |
| Codex P1-01 Pi 接线 + 执行者验收字段 | 接线 **CLOSED**；审查员上下文 **未传** → P2-2 | 不单独阻 L3 |
| Codex P1-02 Cursor 导入 | **CLOSED** | 不阻断 |
| Codex P1-03 `task adopt` | 命令与 dry-run **CLOSED**；FSM 旁路 → P2-3 | 不单独阻 L3 |
| Codex P1-04 sha256 / 归属 | id、非零篡改、仓外路径 **CLOSED**；全零/空/缺文件/cli **未闭** → **P1-1** | 阻断 L3 |
| F-25 零 sidecar | dry-run 路径 **CLOSED** | 不阻断 |

---

## 8. 建议闭环顺序与验收

1. **P1-1**：去掉全零后门；缺文件/空哈希 fail-closed；按声明补 `executor.cli` 或删声明；用 `probe_checkpoint_p104.py` 同类反例扩官方测试；申请信封改真实哈希。
2. **L4**：真实 CLI 至少一轮非全同意；人类路径 HOLD → `macao override resolve` / `merge approve`；按 §7.2 十行逐格填写证据。不要再拿 `mock-cli` live-run 申请 PG-3。
3. **P2（可选同轮）**：无 cwd 则丢弃会话或填写会话目录而非查询仓；审查 payload 纳入 `acceptance_criteria`；adopt 走带审计的 FSM 事件。
4. 文档：STATUS 实例化 §5.2 表；不要再把 grok 上轮票改写成别人的编号。

验收时请再跑：`probe_checkpoint_p104.py`（必须 `FAIL_OPEN` 消失）、脏树+pending 的 **CLI 全文**、`task create` E7、Claude 同名异路径、WAL dry-run 文件集差、既有 162 项。不要只贴 162/162。

---

## 9. 准入建议

- **本轮增量**：**不授予** L3 SCENARIO-VERIFIED / PG-2 全量认证。场景 C / Fail-Closed / 只读零侧车已可独立复放，但检查点审计锚点仍可被全零信封推进。
- **既有编排引擎**：**维持** L3 SCENARIO-VERIFIED / PG-2。
- **L4 RELEASE-READY / PG-3**：**拒绝**。P1 未清零，且 §7.2 第 9–10 行未满足。
- **方法论 v1.1**：**允许作为后续评审判据使用**（DOC）；§11 双人审阅以本轮独立报告为一票，不代替代码门禁。

---

## 10. 复现脚本与命令

- 归档目录：`docs/reviews/evidence/2026-09-08-7bc8d70-grok/`
- 最后执行：2026-09-08T00:55:55+08:00
- 完整 SHA：`7bc8d7091ba4e39c0b3282492c613817f8d664e9`
- 外部前提：无网络、无厂商 CLI 额度；Python 3.10+；系统 git/sqlite3

```bash
cd /home/debian/macao
git show --check 7bc8d7091ba4e39c0b3282492c613817f8d664e9
PYTHONPATH=src python3 -m compileall -q src tests
PYTHONPATH=src python3 -m unittest discover tests
PYTHONPATH=src python3 docs/reviews/evidence/2026-09-08-7bc8d70-grok/probe_7bc8d70.py
PYTHONPATH=src python3 docs/reviews/evidence/2026-09-08-7bc8d70-grok/probe_checkpoint_p104.py
```

---

## 11. Reviewer 自审记录 (Self-Audit Log)

- [x] 已对照 `961bcfe..7bc8d70` 30 个文件与申请清单
- [x] 已串行执行 `unittest discover tests`（162/162）与 `compileall`
- [x] 已用隔离脚本击穿 Codex P1-04（每个反例新任务），未采信被全零推进污染的第一次混跑
- [x] 未把 F-26 无 cwd 回填、adopt 旁路 FSM、审查员未收到验收标准升为 P1
- [x] 未发现未报告的 P0
- [x] 未在宿主仓执行会写状态的 `task adopt` / `task create`

---

## 伴随机器信封：`.macao/.reviews/r3/grok.review.yml`

```yaml
version: "1.0"
task_id: "task-20260908-orchestrator-p0-p1-remediation-and-guidelines-v1.1"
checkpoint_ref: "7bc8d70"
review_round: 3
reviewer:
  id: "grok"
  role: "reviewer"
  cli: "cursor-grok"
vote: "NO_APPROVE"
opinion:
  status: "REJECTED"
  confidence: 0.94
  summary: "前序 grok P1 场景C与Claude basename、以及未知CLI/WAL/E7/adopt/Pi-Cursor接线均独立复放闭环；阻断为检查点全零/空/缺失哈希仍可进入 READY_FOR_REVIEW（Codex P1-04 假绿）。L4 仍因 live-run mock-cli 与 §7.2 矩阵未填而否决。"
full_document:
  path: "docs/reviews/2026-09-08-review-result-7bc8d70-grok.md"
  evidence_commit: "7bc8d70"
  sha256: "faf4908b036d4f1b28ea7f74e07e29cd22e016d719f3481fc2be0d69b4418b46"
items:
  - issue_id: "grok/P1-1"
    disposition_class: "MUST_FIX"
    severity: "blocker"
    title: "Checkpoint accepts all-zero/empty/missing sha256 and ignores executor.cli; official test is a false green"
  - issue_id: "grok/L4-OPS"
    disposition_class: "MUST_FIX"
    severity: "blocker"
    title: "live-run still hardcodes mock-cli reviewers and default auto_signoff=True; §7.2 matrix not evidenced"
```
