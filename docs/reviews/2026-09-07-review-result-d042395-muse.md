# MACAO 合并复审（基线 `d042395`）评审结论

- **评审日期**：2026-09-07
- **评审人**：muse（独立评审）
- **评审对象**：`docs/reviews/2026-09-07-review-request-d042395.md`，钉死 `d042395`（HEAD 仅增申请/STATUS，交付物一致）
- **结论**：**授予 L3 SCENARIO-VERIFIED / PG-2；L4 RELEASE-READY / PG-3 暂不授予（P1 × 3）**
- **结构化 issue**：`BLOCKING` × 3（P1，均为 L4 门槛阻断）、`ADVISORY` × 4（P2 × 2 / P3 × 2）

---

## 1. 机验复核（本机全部重放）

| 申请 §4 声明 | 独立复验 | 判定 |
|---|---|---|
| 128/128 全绿（~66s） | `PYTHONPATH=src python3 -m unittest discover tests` → **Ran 128 tests, OK**（42.5s） | ✅ 为真 |
| compileall 0 | `python3 -m compileall -q src tests` → 0 Errors | ✅ 为真 |
| 全库 228 md 零控制字符 | 工作区 242 命中含 `docs/usecases/` 软链接重复计数 13；`git ls-files *.md` = **229**；控制字符 0 | ✅ 实质为真（计数口径差 1，见 A-4） |
| 双 Schema 目录 0 diff | 仅 `__init__.py`/`__pycache__`/README 等预期差异，8 份契约逐字节一致 | ✅ 为真 |
| PRD snippet 6/6 | `test_prd_snippets_schema.py` 6 个测试方法全过；另含全用例/提案/template snippet 覆盖（`tested_count ≥ 3/6` 断言在位） | ✅ 为真 |
| SessionLocator 零 LLM | 仅 stdlib 导入（json/os/re/sqlite3/pathlib）；无网络/LLM 调用 | ✅ 为真 |
| 真实 worktree 探测 | `_inspect_worktree` 为真实存在性 + `rev-parse` 检查；`git worktree list --porcelain` 解析在位；未挂载分支如实 `In-repo (Shared Workspace / Direct Review)` | ✅ 为真 |
| 进度三元组物理推导 | Git 历史 + `docs/reviews/*-review-request-*` + 结果文件比对；沙箱实测场景 C 正确输出 `ACTIVE_DEV (UNTRACKED)` | ✅ 为真（含真机运行，见 §2） |
| DB 只读 | probe 全程 `file:...?mode=ro`；沙箱实测未生成 `state.db`、无 DDL | ✅ 为真（但见 B-1） |

## 2. 真机实操（沙箱，非污染）

在 `/tmp/probetest`（全新 `git init` + 复制 `macao.yaml`）运行 `probe --dry-run`：真实发现宿主 `opencode (GLM 5.3 max)` 会话、脏文件计数与 `ACTIVE_DEV (UNTRACKED)` 判定；`logs --probe` 可回溯审计日志。运行后沙箱已删除，本仓库零污染。

## 3. BLOCKING（P1，L4 门槛；L3 不受影响）

### B-1　`--dry-run` 落盘审计日志，与"100% 零修改 / Pure Read-Only"声明矛盾（实测复现）

- **复现**：`prober.py:812` 无条件调用 `_write_probe_log`（`:248` `mkdir -p .macao/logs/probe` + `:298` 写文件），`dry_run` 仅被记录进日志正文（`:260`），不 gating 写动作。沙箱实测：纯净仓库一次 `--dry-run` 即产生 `.macao/logs/probe/probe_*.log`；终端横幅却宣称 `[DRY-RUN (Pure Read-Only)]`。
- **定性**：AGENTS.md 字面（禁 SQLite/DDL/git 副作用）成立；但申请 §1.2"保证 100% 零修改"与 CLI 横幅的更强承诺被证伪。安全属性声明必须精确（Fail-Closed 原则）。
- **修正（二选一）**：① `dry_run` 时跳过落盘（内存返回 `log_file: None`）；② 将声明与横幅收窄为"除审计日志落盘外，不碰 state.db 与 git"。

### B-2　"API Key/Token 敏感词掩码"零实现（CLAIM_ONLY 的安全特性）

- **复现**：`src/macao/` 全库无 redact/mask/脱敏实现；`tests/test_logger_and_audit.py` 5 个测试仅覆盖落盘/gitignore/audit/logs 查阅，无一涉及密钥掩码。ANSI 清洗（`strip_ansi`）存在，但与密钥掩码是两回事。
- **定性**：申请 §1.3/§5 把掩码列为交付特性； reviewer PTY 日志（`.macao/logs/reviewers/`）将以明文落盘终端字符流。发布门槛下不可接受。
- **修正**：实现掩码 + 反例测试，或从申请中删除该特性声明。

### B-3　`live_run` 默认 mock 评审团 + 默认自动签收 `HUMAN_MERGE_APPROVED`（整风轮 P1-R1 谱系）

- **复现**：`live_runner.py:55-57` 默认评审团 `cli: "mock-cli"`；`main.py:857` `--auto-signoff` **默认 True**；`:183` 以 `"signer": "system-runner"` 写入 **`HUMAN_MERGE_APPROVED`** 事件（note 自述自动化，但事件类型断言人类批准）。
- **定性**：相对整风轮"operator 代签"已有进步（显式 flag + note），但开箱默认行为仍是在无人类参与下写 `HUMAN_*` 审计事件，直接动摇 §1.3"不可变审计账本"的可信度。本申请未把 live 路径列为证据（诚实），故不阻断 L3；但 L4（对外演示/发布）门槛下必须关闭。
- **修正**：事件改名（如 `SYSTEM_AUTO_SIGNOFF`）或默认 `--no-auto-signoff`；`live_run` 默认评审团应拒绝 mock（fail-closed）或显式标注演练模式。

## 4. ADVISORY

- **A-1（P2）**：wizard `minimum_winning_seats = max(2, ceil(2W/3))`（`:295`、`:527`），且 seat_quorum 取权重口径（`:505`）——4 席等权队写出 `3`，严于 PRD §13 示例、根配置与引擎默认之 `2`；N=4 的 2-1-1 场景在默认下 APPROVED、在向导配置下 DEADLOCK。Schema 合法，但推导无规范依据，UC-1 亦无记载。建议：规范明确或向导对齐默认值 2。
- **A-2（P2）**：模板计数"12 份"与正文自列（6 指南 + 8 manifest = 14 个模板，15 文件含 README）矛盾。实测 8 manifest 全可解析且被 snippet 测试覆盖——交付物本身合格，仅计数文字错误。
- **A-3（P3）**：md 计数 228 vs 受审树 229（差申请文件自身）；计数口径问题连续多轮复发。
- **A-4（P3）**：`prober.py:617-618` 保留 `(NOT_SPAWNED)` 字面——仅在 `active_task` 存在而物理路径缺失的**真实**分支使用，非虚构；建议改名 `EXPECTED_BUT_MISSING` 以绝歧义。

## 5. 定级意见

- **授予 L3 SCENARIO-VERIFIED / PG-2**：探活/会话/日志/模板/向导五大维度场景均有 TEST + 真机 SIM 证据；探活路径无伪造（与整风轮教训对照已查）；L1/L2 基线无回退。
- **L4 RELEASE-READY / PG-3 暂不授予**：B-1～B-3 均为"安全/审计诚实性"类缺陷，修复面窄（条件落盘、掩码实现、事件改名/默认值三处单点），复审单轮可闭环。人工接管实机演练（GUIDELINES §3.3 L4 必需）在新 CLI 面上亦未呈现实证，B-3 闭环时应一并补足。

## 6. Reviewer 自审记录

- 本人为 `73576c5` 轮双轨 APPROVE 出具者之一；本轮对合并新增面（此前未审）全量新查，不因前票惯性免检；
- B-1/B-3 均经沙箱/读码实证，非转述；B-2 经全库 grep + 测试清单双重确认（`mask|redact|脱敏` 零命中）；
- `live_dispatcher.py:98` "Neither status nor vote is present: Reject (do not fabricate approval)" fail-closed 注释已读，dispatch 解析层未发现伪造模式——B-3 仅针对签收事件与默认 mock 评审团；
- 未覆盖：win32、真实厂商 CLI 额度消耗类演练、Phase 1 实现。
