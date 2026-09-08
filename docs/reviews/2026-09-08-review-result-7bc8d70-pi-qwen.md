# MACAO 综合编排闭环与评审方法论 v1.1 升级复审结论（Commit `7bc8d70` / Round 3）

- **文档归档路径**: `docs/reviews/2026-09-08-review-result-7bc8d70-pi-qwen.md`
- **评审日期 (Date)**: 2026-09-08（机验执行窗口 00:55–01:44 +0800）
- **评审人 (Reviewer)**: `pi-qwen`（harness: pi coding agent，`PI_MODEL=qwen3.8-max`，`PI_SESSION_ID=01a07bd3-8b24-72e9-8e95-62179f6a5946`；与已归档的 `qwen` 报告为**不同评审人**，结论各自独立作出）
- **评审对象 (Object)**: [`docs/reviews/2026-09-08-review-request-7bc8d70.md`](2026-09-08-review-request-7bc8d70.md)
- **受审基线 (Checkpoint)**: `7bc8d70`（完整 SHA `7bc8d7091ba4e39c0b3282492c613817f8d664e9`，范围 `961bcfe..7bc8d70`，涵盖 `48eea58` + `7bc8d70`）。**本评审全部结论均在 `git archive` 提取的纯净树上取得**（§3.4 参照系），复现脚本已按 §3.5 归档：[`docs/reviews/evidence/2026-09-08-7bc8d70-pi-qwen/`](evidence/2026-09-08-7bc8d70-pi-qwen/)
- **对齐基准**: [`docs/MACAO_REVIEW_GUIDELINES.md`](../MACAO_REVIEW_GUIDELINES.md) **v1.1**（本轮同提交生效，评审纪律按 v1.1 执行）、`docs/usercases/PRODUCT-FACTS.md`（F-21/F-25/F-26）、`AGENTS.md`
- **申请目标**: L3 SCENARIO-VERIFIED / PG-2 全量认证 + L4 RELEASE-READY / PG-3 准入
- **审查结论 (Verdict)**: **不授予本轮增量 L3 SCENARIO-VERIFIED / PG-2 全量认证；拒绝 L4 / PG-3 准入。判定：REWORK（第 4 轮返工，收窄为 3 项 P1 + 4 项 P2）**
- **最终投票 (Vote)**: `NO_APPROVE`
- **证据统计**: P0 × 0、**P1 × 3**、P2 × 4、P3 × 2；申请方自称"彻底闭环"的 **14 项中 13 项经本评审独立机验为真**（含上轮本评审人提出的全部 10 项），**1 项（Codex P1-04 检查点防伪）被反例击穿**；另新发现 2 项 P1（`task adopt` 幽灵基线、申请证据链）与 1 项 P2（`immutable=1` 陈旧读）。
- **复现**: 全部 P1/P2 附可一键重放的归档脚本（13 项检查 V01–V13，最后实际执行 2026-09-08 01:43:37 +0800，V01–V12 全部按预期复现、V13 证实清单失配）。

---

## §0 Reviewer 自审记录（v1.1 §9 强制自检）

| 检查项 | 本轮执行情况 |
|---|---|
| □1 字段声明 vs 读取路径 | 已查：`full_document.sha256` 消费点为 `orchestrator.py:288-301`，**对全零/空值显式跳过**（P1-A 根因） |
| □2 `[x]` ≠ 证据 | 申请 §3.2 七项 `[x]` 中六项机验为真；「检查点防伪彻底闭环」在处置单与申请中的表述被 V12 反例推翻 |
| □3 确定性用语 | 「彻底闭环」「严格校验必须为合法 64 位散列」「100%」共 3 处与实现存在出入（P1-A/P2-B） |
| □5 P1 可复现 | 每项附 file:line + 归档脚本编号 |
| **□6 已实现 ≠ 已接线（模式 E）** | 上轮 Codex 指出的 `pi`/`cursor` 派发接线本轮已真实接线（`live_dispatcher.py:39` `"pi": PiAdapter`；`cursor.py:126` `CursorAdapter = CursorAgentAdapter`；`pi.py:114`/`cursor.py:91` `acceptance_criteria` 透传）——**该模式本轮无新增命中** |
| **□7 参照系自检（§3.4）** | 测试/机验全部在 `git archive 7bc8d70` 纯净树执行；负向断言全部校验非零退出码（V08）；`git show --check` 用完整 SHA（rc=0） |

**与前序报告的关系声明**：本评审人在 `961bcfe` 轮提出 P0-1 + P1-1~P1-10（见 [`2026-09-07-review-result-961bcfe-pi-qwen.md`](2026-09-07-review-result-961bcfe-pi-qwen.md)）。本轮依 v1.1 §8.3-3「验证修复而非重报旧缺陷」，对每项修复均**构造反例尝试击穿**，未简单复述。

---

## §1 结论综述 (Executive Summary)

**本轮整改质量显著且大部分为真。** 上轮四方 14 项 P0/P1 中 13 项经本评审在纯净树独立复验为真闭环，包括上轮最严重的三项：未知 CLI 借壳（V01：三席位全 `MISSING`、`can_dispatch=False`、阻断原因逐门槛列出）、WAL 侧车（V02 + 宿主仓实测：`probe --dry-run` 前后 `.macao` 文件集合逐项相等）、凭据明文外泄（V04：12 类样例全遮蔽、`probe --json` 无 PAT 明文、`_sanitize_session_name` 已复用统一 `mask_secrets`）。测试确定性修复亦为真：专项 30/30、全量套件连续 4 轮全绿。方法论 v1.1 升级本身属实且质量高（§3.4/§3.5/§5.2/§7.2/§8.1-8.3/§9-E 各节逐条在案，`REVIEW_GUIDEv2.md` 264 行真实存在）。

**但认证仍被三件事阻断：**

1. **检查点防伪存在书面声明与实现相反的豁免（P1-A）**：申请 §1.13 称「严格校验 `full_document.sha256` **必须为合法 64 位十六进制散列且与文档实际 SHA-256 吻合**」；实现（`orchestrator.py:294`）对全零/空/缺失哈希**显式跳过校验**，对 `executor.cli` 完全不校验。V12 实测：错哈希+冒名 executor 被拒 ✓，**全零哈希被接受并推进至 `READY_FOR_REVIEW`**。更关键的是：**本轮申请自己的 `.dev.yml` 信封正是以 64 个零通过这道门的**（自证），其真实 SHA-256 为 `914ecd52…`。F-21 要求产物「通过…路径和哈希相互关联」，此豁免使哈希绑定在实践中可选。该发现与 Grok/Codex/Qwen 三方独立互证（各方独立构造的反例一致）。
2. **`task adopt` 接受不存在的基线 commit（P1-B）**：V11 实测，以引用幽灵 commit `deadbeef99` 的评审单执行 `task adopt`，产生 `('task-adopt-deadbeef','WAITING_REVIEW','deadbeef99')` 的**状态机幽灵任务**——所有评审员 worktree 创建失败（commit 不存在）、评审永无进展、任务占据唯一活动名额形成死锁，而**进程退出码为 0**。这违反 F-24「按底层 Git 拓扑…如实对账」与 Fail-Closed；与 Codex P1-01 独立互证。
3. **申请自身的证据链仍未按其本轮引入的纪律闭合（P1-C）**：申请文档提交于 `a705a49`（晚于受审提交一个提交），**不存在于其自称的 `evidence_commit: 7bc8d70`**；信封 `sha256` 连续第二轮为 64 个零。上轮本评审人 P1-10（证据链）在处置单中被重编号顶替（处置单的"P1-10"是适配器接线项），**该项从未被处置且本轮复发**。

另有 4 项 P2：`immutable=1` 在写者持有未 checkpoint WAL 时**静默上报陈旧任务状态**（V03，新发现的修复代价）、变更清单 18/23 行数字失实且漏列 7 个文件（含 4 份评审归档与 `AGENTS.md`，V13，连续第二轮）、对 Kimi 上轮报告的归档记录被错误转述（「2 项 P0，5 项 P1」，实际为「P0：无，1 项 P1」）、§5.2「已知简化表」未按其自身程序落地到 PRD 附录或 STATUS。

**L4 / PG-3 不予受理**：v1.1 §7.2 十行 OPS 必测矩阵在本申请中**一行未填**（该规范与本申请同一提交生效，自我适用）；`live-run` 的 Reviewer 仍全部为 `cli: "mock-cli"`（`live_runner.py:56-58`）且 `auto_signoff` 默认 `True`（`:76`），直接触犯同提交生效的 §7.2 第 10 行「严禁由 runner 或 mock 脚本内部自行伪造 `YES_APPROVE`」。

---

## §2 声明验证矩阵（申请文档逐条机验）

| # | 申请声明 | 独立验证（脚本编号） | 状态 |
|---|---|---|---|
| 1 | §3.2「162/162 PASS」 | 纯净树 `discover`：`Ran 162 tests in 56.131s OK`，另 3 轮复跑全绿（合计 4/4） | **VERIFIED** |
| 2 | §3.2「测试确定性（前序 P1-1）」 | `tests.test_pi_and_session_locator` 连续 **30/30 OK**；`session_locator.py` 排序键已为 `(st_mtime, name)` | **VERIFIED** |
| 3 | §1.2「`&immutable=1` 彻底消除 WAL/SHM 侧车」 | V02：WAL 库存在时 dry-run 前后文件集相等；宿主仓实测 `exit=0`、`.macao` 仍仅 `logs state.db` | **VERIFIED**（代价见 P2-A） |
| 4 | §1.1「未知 CLI 一律 MISSING，阻断派发（P0-1）」 | V01：三席位 `MISSING` + `Unrecognized CLI '...'` + `can_dispatch=False` + 三门槛短板齐列 | **VERIFIED** |
| 5 | §1.4「脱敏 6 大类并全面集成（P1-3）」 | V04：`ghp_/sk-ant-/Bearer/db-url/JWT/AWS/api_key:/环境变量 token` 全遮蔽；`probe --json` 无明文；`_sanitize_session_name` 已复用 `mask_secrets` | **VERIFIED** |
| 6 | §1.5「realpath 严格比对杜绝串话（P1-4）」 | V05：同名子目录跨项目 Claude 会话 → `[]`（basename 回退与 workspace 回填均已移除） | **VERIFIED** |
| 7 | §1.6「worktree remove+prune 消灭幽灵（P1-5）」 | V06：clean 后 `git worktree list` 无 prunable、`.git/worktrees/` 为空 | **VERIFIED** |
| 8 | §1.7「单一活动任务下沉 start_task（P1-6）」 | V07：`--no-probe` 二次创建 rc=1 被阻；`--force` → E10 审计留痕、活动任务恒为 1；`tasks` 表新增 `acceptance_criteria` 列（P2-3 闭环） | **VERIFIED** |
| 9 | §1.8「probe/doctor 退出码 2/1 + `--allow-degraded`（P1-7）」 | V08：畸形 YAML→2、doctor→2、缺失→2、Schema 非法 create --dry-run→1；`--allow-degraded`→0（V08 附加项） | **VERIFIED** |
| 10 | §1.9「F-25 只读零副作用 / F-26 会话真实绑定固化（P1-8）」 | `PRODUCT-FACTS.md:57/:59` 逐字在案，措辞含「零 sidecar/写锁」与「严禁 basename 模糊推定或回填」 | **VERIFIED** |
| 11 | §1.10「待决评审单优先 + E7 阻断（P1-9）」 | V09：`task create` rc=1 + `UC-2 E7` 提示 + 指向 `task adopt`；探活报表输出 `SCENARIO_C (Adopt via 'macao task adopt')`，不再诱导 `task create` | **VERIFIED** |
| 12 | §1.11「Pi/Cursor 接线 + 验收标准透传（P1-10/Codex 01/02）」 | `live_dispatcher.py:39`、`cursor.py:126`、`pi.py:114`/`cursor.py:91`（`acceptance_criteria or success_criteria`） | **VERIFIED** |
| 13 | §1.12「`task adopt` 完整实现 + `--dry-run`（Codex P1-03）」 | V10：`--dry-run` 零文件变更 ✓；**但 V11：接受不存在基线 commit → 幽灵 `WAITING_REVIEW` + rc=0** | **PARTIALLY_VERIFIED → P1-B** |
| 14 | §1.13「sha256 必须合法且吻合；executor 必须一致（Codex P1-04）」 | V12：错哈希/冒名 id 被拒 ✓；**全零哈希被接受**（`orchestrator.py:294` `doc_sha != "0"*64` 豁免）；`executor.cli` 不校验（仅 `:306-308` 比对 `id`） | **CONTRADICTED → P1-A** |
| 15 | §3.2「`git show --check 7bc8d70` rc=0」 | 完整 SHA 实测 rc=0（§3.4 参照系：非 `git diff --check`） | **VERIFIED** |
| 16 | §3.2「compileall 无错误」 | 纯净树 `python3 -m compileall -q src tests` rc=0 | **VERIFIED** |
| 17 | §2「30 个文件，+2765/-226」 | `git diff --shortstat 961bcfe..7bc8d70` 完全吻合 ✓；**但表内 23 行中 18 行数字失实（全部虚高），且漏列 7 个文件**（V13） | **PARTIALLY_VERIFIED → P2-B** |
| 18 | §3.2 / 处置单「`test_task_adopt.py` 7 项 / 5 项测试」 | 实测 `def test_` = **5 项**；申请两处写 7 项 | **CLAIM_ONLY（误记）→ P3-1** |
| 19 | 前序轮次引述「Kimi：REWORK / 2 项 P0，5 项 P1」 | Kimi 归档报告原文「## P0：必须先解决 — **无**」，P1 仅 `P1-NEW-1` 一项（另 3 项 P2/P3）；申请/处置单/STATUS 三处均误述 | **CONTRADICTED → P2-C** |
| 20 | 信封 `full_document.sha256: 000…000` / `evidence_commit: 7bc8d70` | 实际 SHA-256 = `914ecd52415aaa08…`；申请文档首次出现于 `a705a49`（不在 `7bc8d70` 内）；连续第二轮全零 | **CONTRADICTED → P1-C** |
| 21 | §4.1「已知简化」两项依 §5.2 豁免 | §5.2 规则 3 要求常设表置于 **PRD 附录或 STATUS.md**；两表仅见于申请 §4.1，PRD/STATUS 均无该表（grep 无命中） | **PARTIALLY_VERIFIED → P2-D** |
| 22 | 方法论 v1.1 各新增章节 | §3.4/§3.5/§5.2/§7.2/§8.1-8.3/§9 模式 E/§10 模板逐节在案；`docs/reference/REVIEW_GUIDEv2.md` 264 行实质内容 | **VERIFIED** |
| 23 | 隐含：探活只读但**不失真**（F-25 精神） | V03：写者持有未 checkpoint WAL 时，probe 静默上报旧任务（`task-OLD` 而非 `task-NEW`），`state_store.error=None` | **CONTRADICTED → P2-A** |

---

## §3 申请方 5 项 Focus 的逐项裁定

| Focus | 裁定 | 证据 |
|---|---|---|
| **1** 未知 CLI Fail-Closed | **PASS** | V01：3/3 席位 `MISSING`、无借壳版本号、`can_dispatch=False`、`Unrecognized CLI` 阻断原因在列 |
| **2** 只读零侧车 | **PASS（常规路径）/ PARTIAL（失真路径）** | V02 + 宿主仓：零 `-wal`/`-shm` ✓；但 V03 证实 WAL 未 checkpoint 时**静默陈旧读**（P2-A）——零副作用达成，真实性出现新代价 |
| **3** `task adopt` 与 `--dry-run` | **PASS（dry-run）/ FAIL（基线真实性）** | V10：`--dry-run` 零变更 ✓；V11：幽灵 commit 被接纳为 `WAITING_REVIEW` 且 rc=0（P1-B） |
| **4** 检查点防伪与归属 | **PARTIAL** | V12：错哈希/冒名 `executor.id` 被拒 ✓；全零哈希豁免放行、`executor.cli` 不校验（P1-A）；申请自身信封即全零反例 |
| **5** 方法论 v1.1 自洽性 | **PASS（文本）/ FAIL（自我适用）** | 各节在案且质量高；但 §7.2 十行矩阵本申请一行未填、`live-run` 违反第 10 行、§3.4 纪律未阻止 §2 变更清单失实（P2-B）、§5.2 程序未自我执行（P2-D）——**新规范对申请自身的约束力尚未兑现** |

---

## §4 P1：进入下一阶段前必须修正

### P1-A 检查点防伪对全零/缺失哈希 fail-open，`executor.cli` 不校验；申请信封自证通过

- **声明 vs 实现**：申请 §1.13「`sha256` **必须**为合法 64 位十六进制散列且与正文吻合；`executor.id` 与 `executor.cli` **必须**与主执行席位一致」；实现 `orchestrator.py:293-301`：
  ```python
  if doc_path.exists() and doc_path.is_file() and doc_sha and doc_sha != "0" * 64:
      calc_sha = ...  # 仅当哈希非空且非全零才校验
  ```
  `orchestrator.py:302-313` 仅比对 `exec_info["id"] != cfg_exec_id`，`cli` 字段从不比对。
- **反例（V12，纯净树）**：
  ```text
  wrong-sha('deadbeef'+a*56) + executor.id=IMPOSTER -> REJECTED ✓
  all-zero sha(0*64) + executor.id=opencode-dev   -> ACCEPTED (READY_FOR_REVIEW) ✗
  ```
- **自证**：本轮申请信封 `sha256: 000…000`（真实值 `914ecd52415aaa08…`）正是走此豁免；官方回归 `test_checkpoint_full_document_sha256_validation` 只构造「非零篡改 vs 正确哈希」，**从未构造 `0*64`**——测试绿灯不能证明门禁闭合（§9-B）。
- **定级（§8.1/§8.2）**：影响域=审计完整性（F-21 哈希关联在实践中可选，执行者写全零即免绑定）；可达性=在线真实可达（`.dev.yml` 由执行者手写）。**P1**。与 Grok（主阻断）、Codex P1-02、Qwen（同反例）独立互证。
- **验收标准**：`0*64`/空/缺失哈希与文档存在时一律 `return None`（或强制要求非占位哈希）；`executor.cli` 一并比对；回归测试必须含 `0*64`、空串、缺失 `full_document`、错误 `cli` 四个负例（均断言不推进 + 非零退出码）；**本轮申请信封改为真实 SHA-256 后重提**。

### P1-B `task adopt` 接纳不存在的基线 commit：幽灵 `WAITING_REVIEW` 任务 + 退出码 0

- **反例（V11，纯净树）**：评审单引用 `Checkpoint: deadbeef99 (nonexistent commit)`：
  ```text
  ! cursor FAIL: Cannot create worktree: commit 'deadbeef99' does not exist in repository
  ! antigravity FAIL / ! codex FAIL（同因）
  tasks: [('task-adopt-deadbeef','WAITING_REVIEW','deadbeef99')]   进程 rc=0
  ```
  任务被推进至 `WAITING_REVIEW` 但 checkpoint 在 Git 中不存在：评审永不可达、占据唯一活动名额（P1-6 不变量反被该缺陷锁死为死锁）、且对外报成功。
- **定级**：影响域=状态机违约（应阻断而放行）+ 物理事实失真（违反 F-24「按底层 Git 拓扑如实对账」）；可达性=在线真实可达（任意匹配 glob 的 markdown 写一个不存在的 commit 即触发）。**P1**。与 Codex P1-01 独立互证。
- **验收标准**：adopt 在建任务前 `git rev-parse --verify <commit>`，失败即 fail-closed 退出非零并**不产生任何任务行**；补负向测试（幽灵 commit → rc≠0 且 `tasks` 表零新增）；同时审视 adopt 的 FSM 入口（不得绕过转移表合法路径）。

### P1-C 申请证据链连续第二轮未闭合：文档不在 `evidence_commit`、信封哈希全零、上轮 P1-10 从未被处置

- **事实**：① 申请文档首次提交于 `a705a49`，`git show 7bc8d70 --stat | grep -c review-request-7bc8d70` = **0**；② 信封 `sha256` 第二轮为 64 个零；③ 处置单第 137 行把「P1-10」编号分配给了适配器接线项，本评审人上轮 P1-10（证据链/原子提交/冻结工作树）**未出现在处置清单任何条目中**且本轮原样复发。
- **定级**：影响域=审计链在提交层面断裂（§8.1 P0/P1 域原文「审计链在哈希/提交层面断裂」——因属申请侧元数据而非生产代码路径，按 §8.2 降一级记 **P1**）；连续第二轮出现，说明非偶发疏漏而是流程缺口。
- **验收标准**：申请文档、STATUS 更新与整改代码**同一提交**落地（或至少在受审提交内）；信封哈希填真实值；为「评审冻结窗口」（投票期内禁改工作树）建立成文规则并登记入 §5.2 决策项。

---

## §5 P2 / P3

### P2（发布前应修正）

| ID | 问题 | 证据 | 建议 |
|---|---|---|---|
| **P2-A** | `immutable=1` 陈旧读：写者持有未 checkpoint 的 WAL 时（daemon 写入中、或崩溃后首次 RW 打开前），`probe` **静默**上报旧任务（V03：报 `task-OLD`，真相 `task-NEW`，`state_store.error=None`）；纯新库场景可致 `no such table` 错误。决策路径（`task create` 守卫 `main.py:418` 走 RW 连接）不受影响，失真限于诊断面 | V03 归档脚本；`prober.py:75/96`、`main.py:314`、`session_locator.py:232/286` | 当 `state.db-wal` 存在且非空时：复制主库+wal 至临时目录后读取，或直接标注 `state_store: STALE(WAL_PRESENT)`；至少在 `PROBE_TECHNICAL_DESIGN.md` 与 F-25 注明该权衡（上轮报告已预警「immutable 仅在无并发写者时安全」） |
| **P2-B** | 变更清单连续第二轮失实：23 行中 **18 行数字虚高**（如 `prober.py` +30/-10，实 +10/-20；`secrets.py` +64/-6，实 +37/-27；`STATUS.md` +46/-2，实 +40/-6），行合计 +1923/-142 ≠ 自称 +2765/-226；**漏列 7 个文件**（4 份上轮评审归档、`2026-09-07-review-request-961bcfe.md`、`AGENTS.md`、`tests/test_phase3.py`） | V13 归档脚本；`git diff --numstat 961bcfe..7bc8d70` | 表格由 `git diff --numstat` 生成并附区间；本轮已引入 §3.4 纪律，应同样适用于申请文档自身 |
| **P2-C** | 归档评审记录被错误转述：申请/处置单/STATUS 三处称 Kimi 上轮「2 项 P0，5 项 P1」，其归档报告原文为「P0：必须先解决 — **无**」+ 1 项 `P1-NEW-1`；处置单各条目「评审来源: Kimi P0-1 / Kimi P1-1…P1-5」引用了不存在的编号（实质内容系本评审人与 Grok 的发现） | `2026-09-07-review-result-961bcfe-kimi.md:44-52` 对照申请 :17、处置单 :9/:19…:102、STATUS :41 | 三处文件按归档原文更正；处置单「评审来源」改引真实出处 |
| **P2-D** | §5.2「已知简化表」未按其规则 3 落地（须置于 PRD 附录或 STATUS.md；增删须 §11 修订程序）；两项简化仅见于申请 §4.1。另 `ci_gate_command: null` 跳过外部 CI 门禁直推合并，依 §5.2 规则 2 应作为**决策项**显式登记业务代价，而非与「In-repo 工作区」并列静默豁免 | STATUS.md 与 PRD v2 中 grep「已知简化」零命中；`PRD v2:1420` 仅为配置默认值 | 在 STATUS.md 建常设表并补齐 §5.2 要求的五列（现状/接受理由/接受轮次/生产化前需补什么/expiry）；`ci_gate_command` 立决策项 |

### P3（登记即可）

| ID | 问题 | 证据 |
|---|---|---|
| **P3-1** | 测试计数误记：申请 §2 表与 §3.2 称 `test_task_adopt.py`「7 项」，实测 `def test_` = **5**（处置单自记亦为 5） | `grep -c "def test_" tests/test_task_adopt.py` = 5 |
| **P3-2** | `AIza` 规则定长刚性：`AIza[0-9A-Za-z\-_]{35}` 对规范 39 字符键遮蔽 ✓，但 38/40 字符邻域变体漏网（规范键定长 39，实际风险低，登记备查） | 归档脚本 V04 附加样例：39 字符 MASKED、38 字符 LEAK |

---

## §6 L4 / PG-3 准入独立裁定（v1.1 §7.2）

| # | 必测行 | 本申请证据 | 裁定 |
|---|---|---|---|
| 1-8 | 守护进程异常、PTY 断开、worktree 失败、冷重启幂等、并发写、磁盘失败、现场清理 | **未提供**（申请全文无 §7.2 矩阵） | **UNKNOWN** |
| 9 | `macao override resolve` 人工接管实机演练 | **未提供** | **UNKNOWN** |
| 10 | 端到端演练组件保真（禁 mock 伪造票） | `live_runner.py:56-58` Reviewer 全为 `mock-cli`、`:76` `auto_signoff=True` 默认——与同提交生效的 §7.2 第 10 行正面冲突 | **CONTRADICTED** |

**结论：L4 OPS 证据完整性不满足（缺漏任何一行即视为不完整），PG-3 不予受理。** 该判据与本轮交付的 v1.1 同提交生效，属自我适用要求，非外部追加。

---

## §7 交叉文档需做的文字修订

1. 申请 §1.13：改为如实描述豁免边界（或删豁免后重述）；§2 表、§3.2 数字以 git/实测为准（P2-B/P3-1）。
2. 申请/处置单/STATUS 中 Kimi 引述三处更正（P2-C）。
3. `PROBE_TECHNICAL_DESIGN.md`：补 `immutable=1` 的适用前提与陈旧读边界（P2-A）；F-25 可加一句「只读且不失真：WAL 存在时标注 STALE」。
4. STATUS.md：建 §5.2 已知简化常设表 + `ci_gate_command` 决策项（P2-D）。
5. 处置单模板：增设「前序编号映射表」，防止跨轮重编号顶替（P1-C 根因之一）。

---

## §8 建议的闭环顺序与验收标准（Round 4）

| 序 | 项 | 验收标准 |
|---|---|---|
| 1 | **P1-A** | `0*64`/空/缺失 + 错 `cli` 四负例（生产入口驱动，断言非零退出与不推进）；申请信封改真实 SHA-256 |
| 2 | **P1-B** | 幽灵 commit → rc≠0 且 `tasks` 零新增；adopt 全路径仅经合法 FSM 转移（可加 `git rev-parse --verify` 前置） |
| 3 | **P1-C** | 申请文档+STATUS+整改同一提交；信封哈希=实测；评审冻结窗口规则成文 |
| 4 | **P2-A** | WAL 非空时探活标注 `STALE(WAL_PRESENT)` 或读副本；负例：daemon 持锁期间 probe 不得静默报旧任务 |
| 5 | **P2-B/C/D** | 变更清单脚本化生成；三处 Kimi 引述更正；已知简化常设表落 STATUS |
| 6 | **L4（如仍申请）** | §7.2 十行逐项 VERIFIED + `live-run` 去除 `mock-cli`/`auto_signoff` 默认 True（改真实 CLI 与人工 signoff），并留演练归档 |

**Round 4 提审门槛**：P1=0（P2-A~D 可带完整风险接受登记延期）。本轮 13/14 的真实闭环质量表明剩余项均为窄口径修复，**不构成架构性返工**。

---

## §9 复现脚本与命令（含最后执行日期与完整可重放环境）

- **归档位置**: [`docs/reviews/evidence/2026-09-08-7bc8d70-pi-qwen/`](evidence/2026-09-08-7bc8d70-pi-qwen/)（`repro_7bc8d70_pi_qwen.py` + `README.md` 元数据）
- **最后实际执行**: **2026-09-08 01:43:37 +0800**；运行环境：Debian / Python 3.12 / git 2.39+，仓库 `/home/debian/macao`（HEAD `a705a49`，脚本内部自行 `git archive 7bc8d7091ba4e39c0b3282492c613817f8d664e9` 提取纯净树于 `tempfile.mkdtemp` 沙箱并自清理）
- **一键重放**:
  ```bash
  python3 docs/reviews/evidence/2026-09-08-7bc8d70-pi-qwen/repro_7bc8d70_pi_qwen.py
  # 预期：V01–V12 PASS（其中 V03/V11/V12 为"缺陷按预期复现"的演示性 PASS），V13 FAIL（即 P2-B 证实）
  ```
- **独立于脚本另行执行的机验**（纯净树 `/tmp/v7bc`，2026-09-08 00:55–01:44 +0800）：全量套件 4 轮全绿、专项 30/30、`git show --check <full_sha>` rc=0、`compileall` rc=0、宿主仓 `probe --dry-run` 零侧车实测。
- **评审副作用声明**：一切破坏性实验均在脚本自建沙箱内完成并清理；宿主仓库内仅执行只读命令与 `probe --dry-run`（零侧车已验证）；本评审新增产物仅本报告与 evidence 目录两项。

---

**投票 (Vote)**: `NO_APPROVE`
**结论 (Verdict)**: REWORK — 不授予 `7bc8d70` 增量 L3 SCENARIO-VERIFIED / PG-2 全量认证；L4 RELEASE-READY / PG-3 不予受理。
**阻断项**: P1 × 3（检查点防伪全零豁免与 `executor.cli` 失校验、`task adopt` 幽灵基线、申请证据链复发）。
**肯定项**: 前序 14 项中 13 项真实闭环（含本评审人上轮全部 10 项），方法论 v1.1 交付属实且高质量；剩余阻断均为窄口径修复。
