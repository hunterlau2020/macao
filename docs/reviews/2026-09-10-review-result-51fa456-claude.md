# MACAO 检查点强归档防伪、执行者组合根 Fail-Closed 与全适配器准则透传（`51fa456` / Round 6）独立复审结论

- **评审日期**：2026-09-10
- **评审人**：claude（独立评审；不采信申请自述、不采信 `STATUS.md` 定级句；本轮工作区已存在 grok、muse 的未跟踪报告文件，但本报告在完成独立机验与独立复现之前未读取二者内容——见 §0.2）
- **评审对象**：[`docs/reviews/2026-09-10-review-request-51fa456.md`](2026-09-10-review-request-51fa456.md)
- **受审提交**：`51fa456ada474818a1107f1a11b061661dab1063`（申请文档自称的完整 SHA 与 `git rev-parse 51fa456` 结果**逐字符一致**，见 §一）
- **合并审计范围**：`bdc177e..51fa456`
- **工作区 HEAD**：`8953b8d`，相对 `51fa456` 仅追加 Round 6 申请文件与 `STATUS.md` 更新（文档类增量，不影响受审代码）
- **对齐基准**：`docs/MACAO_REVIEW_GUIDELINES.md` v1.1 §3.4、§3.5、§5.2、§8、§9
- **前序基线**：`bdc177e`（四方评审：claude/grok/pi-qwen YES_APPROVE，codex REJECT，仲裁为 **REWORK**，2 项 P1 待闭环）
- **目标定级**：L3 SCENARIO-VERIFIED / PG-2 全量认证，并提请 L4 RELEASE-READY / PG-3 准入评审
- **机器票**：**`YES_APPROVE`**（限本轮申报范围：证据 Git 强归档绑定、执行者组合根 Fail-Closed、全适配器审查员准则透传；L4/PG-3 仍拒绝，见 §四）
- **证据**：`BLOCKING` × 0；`ADVISORY` × 1（P3，新发现，非阻断，可达面极窄）；**无 P0，无 P1**

**结论：授予本轮 L3 SCENARIO-VERIFIED / PG-2（限本轮申报范围）；不授予 L4 RELEASE-READY / PG-3。既有编排引擎 L3/PG-2 维持不变。**

这是我连续第二轮投出 `YES_APPROVE`。本轮申请聚焦于彻底闭环 Round 5 仲裁阶段 Codex 提出的两项 P1（我自己在 Round 5 报告 §三 中以 P2 记录的"未跟踪证据文件绕过 blob 反篡改校验"，以及"未知 executor CLI 静默降级为空导致 `--no-probe` 建立悬空 CODING 任务"），并新增全部七款适配器审查员侧验收准则透传。我用全新构造（非沿用旧脚本）独立复现了两项闭环，均确认为真实修复；额外新发现一处窄可达面的非阻断缺口（`macao live-run` 自带演示流程的 reviewer 派发调用点未转发 `acceptance_criteria`），定级 P3。

---

## 0. Reviewer 自审

### 0.1 强制自检

| # | 项 | 本轮 |
|---|---|---|
| 1 | 字段/路径 vs 实际读取 | `orchestrator.py:430-441` 的 blob 校验分支已从"`cat-file -e` 成功才校验，失败则跳过"改为"必须成功，失败即 `return None`"，真正 Fail-Closed |
| 2 | 「已完成 / 100% / 全绿」 | 173/173、`git show --check` rc=0、`compileall` rc=0 均 **VERIFIED**（申请称 173，与本机一致，无夸大）；Round 5 两项遗留 P1 **均 VERIFIED 闭环** |
| 3 | 确定性用语未标目标 | 申请正文对"强制"措辞与实现严格一致：`cat-file -e` 返回非 0 现在确实无条件拒绝，未见夸大或话术软化 |
| 4 | YAML/JSON Schema | 未改动 Schema 文件，沿用既有校验，未复查（本轮 diff 未触及） |
| 5 | P1 均附路径与复放 | 无 P1；P3 已附路径与复放，见 §三 |

### 0.2 独立性声明与复现证据归档（按 v1.1 §3.5）

工作区在本报告写作前已存在 `docs/reviews/2026-09-10-review-result-51fa456-grok.md`、`-muse.md` 两份未跟踪报告及 `evidence/2026-09-10-51fa456-grok/` 目录。本报告的机验命令、代码阅读与四个独立探针均在**读取上述文件之前**完成并写定结论；本节之后不再回读它们，以保持本报告作为独立第一手结论的有效性。

复现脚本：[`docs/reviews/evidence/2026-09-10-51fa456-claude/probe_51fa456_claude.py`](evidence/2026-09-10-51fa456-claude/probe_51fa456_claude.py)。五个探针均使用独立 `tempfile.mkdtemp()` 沙箱或纯源码内省，对宿主仓库零写入。最后执行：2026-09-10。环境：Linux、Python 3.12、系统 git，无网络、无真实厂商 CLI。

---

## 一、申请 §2/§3 机验独立复跑

| 声明 | 本机 | 判定 |
|---|---|---|
| 完整 SHA `51fa456ada474818a1107f1a11b061661dab1063` | `git rev-parse 51fa456` 结果逐字符一致 | **VERIFIED** |
| `PYTHONPATH=src python3 -m unittest discover tests` 173/173 | `Ran 173 tests in 66.175s … OK` | **VERIFIED** |
| `python3 -m compileall -q src tests` rc=0 | rc=0 | **VERIFIED** |
| `git show --check 51fa456...` rc=0 | rc=0，命令按申请字面文本可直接执行成功 | **VERIFIED** |
| `docs/reviews/evidence/2026-09-10-bdc177e-codex/reproduce_remaining_fail_closed_gaps.py` 保持 CODING 未越权 | 未在本报告中执行第三方脚本（保持独立性，见 §0.2），改用自建等价探针复现相同断言，结果一致 | **INDEPENDENTLY REPRODUCED**（见 §二） |

---

## 二、Round 5 遗留 P1 闭环核验（本人独立复放，全新构造，非沿用旧脚本）

### 2.1 未跟踪证据文件绕过 Git blob 反篡改校验（我 Round 5 P2-1 / Codex P1-bdc177e-01）—— CLOSED

**独立复现**（磁盘上放一份真实存在、SHA 与信封声明完全一致，但从未 `git add`/`git commit` 过的文件）：

```text
untracked_evidence_bypass (Round5 P2-1) -> advanced=False  # 上轮为 True，本轮已拒绝
```

**对照组**（验证 blob 检查在文件被追踪后仍能正确捕获"提交后本地篡改"，证明该机制本身逻辑仍然正确、未被本轮改动破坏）：

```text
tampered_tracked_file (control) -> advanced=False
```

**根因确认**（`orchestrator.py:430-441`）：

```python
if self.git and self.git.is_git_repository():
    rel_posix = rel_doc_path.as_posix()
    code, _, _ = self.git._run("cat-file", "-e", f"{latest_commit}:{rel_posix}")
    if code != 0:
        return None                      # 新增：cat-file 失败即拒绝，不再静默跳过
    blob_bytes = self.git.get_file_bytes_at_commit(latest_commit, rel_posix)
    if blob_bytes is None:
        return None
    calc_blob_sha = hashlib.sha256(blob_bytes).hexdigest()
    if calc_blob_sha.lower() != str(doc_sha).lower():
        return None
```

`code != 0`（文件未被该 commit 追踪）分支现在显式 `return None`，取代了此前"跳过整段校验、退化为仅磁盘哈希比对"的行为。我 Round 5 报告 §三 指出的缺口已按建议的"选项一"（而非仅登记已知简化）彻底修复。

### 2.2 未知 executor CLI 静默降级导致悬空 CODING 任务（Codex P1-bdc177e-02）—— CLOSED

**独立复现**（构造合法 `macao.yaml`，仅将 `team.executor.cli` 改为一个不存在的取值，走真实 `macao task create --no-probe` CLI 子进程，而非直接调用内部函数）：

```text
unknown_cli get_adapter_for_executor raises ValueError -> True
macao task create --no-probe with bogus executor cli -> exit_code=1
  stderr tail: "Configuration Error: Unknown or unsupported CLI executor type: 'totally-bogus-cli-xyz' (Fail-closed)"
state.db contains any task row after failed create -> False
```

**根因确认**：`live_dispatcher.py:281` 的 `get_adapter_for_executor()` 对未识别 `cli_type` 从"返回 `None`（静默降级）"改为 `raise ValueError(...)`；`cli/main.py:179-201` 的组合根 `get_orchestrator()` 用 `try/except ValueError` 捕获并 `sys.exit(1)`，且该调用在 `task_create` 命令流程中位于 `orchestrator.start_task(...)` 之前（`main.py:472` vs `:476`），无论 `--probe` 还是 `--no-probe` 均先于任何数据库写入执行——我特意验证了 `--no-probe` 路径（Codex 原始复现场景），确认 `state.db` 中确实零任务行残留，未闭环时报告的"执行者永久悬空"场景已消除。

### 2.3 全部七款适配器审查员提示词注入验收准则（Grok P2-bdc177e-03）—— 已实现，但存在一处未接线的调用点（见 §三）

`git diff bdc177e..HEAD` 显示 `claude.py`/`codex.py`/`opencode.py`/`antigravity.py`/`cursor.py`/`kimi.py`/`pi.py` 七个适配器统一新增：

```python
criteria = task_payload.get("acceptance_criteria") or task_payload.get("success_criteria") or []
criteria_section = f"\nAcceptance Criteria:\n{criteria}\n" if criteria else ""
```

并插入到 `REVIEW_REQUEST` 提示词模板中。我追踪了 `dispatch_review_in_worktree()`（`live_dispatcher.py:286`）的 `payload` 构造，确认其正确地将 `acceptance_criteria=` 参数放入 `task_payload["acceptance_criteria"]`；进一步追踪了**全部三个**真实调用点：

- `cli/main.py:667`（`task adopt` 补派缺失评审员）：传入 `acceptance_criteria=adopted_task.get("acceptance_criteria") or []` —— **正确透传**
- `cli/main.py:843`（正式 `review` 派发命令）：传入 `acceptance_criteria=active.get("acceptance_criteria") or []` —— **正确透传**
- `workflow/live_runner.py:154`（`macao live-run` 自带端到端演示流程）：**未传 `acceptance_criteria=` 关键字参数**，尽管该演示任务在 `live_runner.py:88` 的 `start_task(..., acceptance_criteria={"unit_tests_pass": True})` 中确实声明了验收准则 —— 见 §三

两个真实生产命令路径均已正确闭环；演示命令路径存在遗漏，定级为 P3，详见下节。

---

## 三、P3（新发现，非阻断）：`macao live-run` 演示流程未将已声明的验收准则转发给审查员

**独立复现**（对 `live_runner.py:run_live_cycle` 源码内省，定位其唯一一处 `dispatch_review_in_worktree(...)` 调用）：

```text
live_runner.py dispatch_review_in_worktree() call passes acceptance_criteria= -> False
```

**根因**：`live_runner.py:154` 的调用只传了 `reviewer_cfg`/`task_id`/`checkpoint_ref`/`review_round`/`diff_context`/`timeout_sec`，未透传 `acceptance_criteria=`。而同文件 `:88` 处该演示任务的 `start_task()` 调用确实声明了 `acceptance_criteria={"unit_tests_pass": True}`。这意味着运行 `macao live-run` 命令时，三位 mock reviewer 收到的 `REVIEW_REQUEST` 提示词中不会出现 `Acceptance Criteria:` 段落，尽管本轮新增的 `Acceptance Criteria` 特性在适配器层是完整的。

**定性**：定级 P3 而非 P1/P2，理由：(1) 该调用点仅存在于 `macao live-run` 自带的自包含演示/回归场景中（硬编码任务标题、硬编码 `math_lib.py`、硬编码三个 `mock-cli` reviewer），不影响 §2.3 中两条真实生产命令路径（`task adopt`、`review` 派发）——这两条路径均已验证正确透传；(2) 申请正文的表述"适配器层……统一格式化并注入"本身准确描述的是适配器层改动范围，并未声称"全部调用点均已接线"，不构成夸大；(3) 新增回归测试 `test_all_adapters_reviewer_prompt_includes_acceptance_criteria`（`tests/test_p1_closures_and_regressions.py:1057`）也只覆盖适配器单元级别的 `inject_task()` 行为，并未覆盖 `live_runner.py` 这条集成调用链，故该缺口也未被现有测试意外掩盖或误报为已覆盖。

**建议（不阻断本轮）**：在 `live_runner.py:154` 补上 `acceptance_criteria=[...]`（可复用 `:88` 处已声明的 `{"unit_tests_pass": True}` 转为列表形式，或读取 `self.orchestrator` 已创建任务的 `acceptance_criteria` 字段），使 `macao live-run` 命令本身也能作为该特性的端到端演示证据；若认为该演示流程本就不打算体现此特性，应在代码注释或 `STATUS.md` §5.2 已知简化表中说明。

---

## 四、L4 / PG-3（单独否决，沿用未闭）

本轮 diff 触及 `live_runner.py`（+6/-6）、`e2e_runner.py`（+6/-1）、`mock.py`（+28/-11），但全部改动仅用于让演示/回归夹具的证据文档"先提交后校验"以适配本轮新增的强制 blob 归档要求（见 §2.1），**未改变** reviewer 团队构成或签收策略本身：

```text
live_runner.py:56-58  reviewers 仍为 3 × cli: "mock-cli"
live_runner.py:76     def run_live_cycle(..., auto_signoff: bool = True)
```

GUIDELINES v1.1 §7.2 的 10 行 OPS 必测矩阵本轮申请仍未提供任何一行独立证据。**L4 仍需一次真实 CLI + 真实人工接管的留档演练才可申请，与此前各轮判定一致。**

---

## 五、建议闭环顺序

1. **P3**（可延期，不阻断本轮）：`live_runner.py:154` 补 `acceptance_criteria=` 转发，或在 `STATUS.md` §5.2 登记为已知简化边界。
2. **L4**：真实 CLI 至少一轮非全同意评审 + 人工 `override resolve` 实机留痕；按 v1.1 §7.2 十行矩阵逐格提供证据。

验收 P3 时请重放本报告归档脚本 [`evidence/2026-09-10-51fa456-claude/probe_51fa456_claude.py`](evidence/2026-09-10-51fa456-claude/probe_51fa456_claude.py) 的 `probe_live_run_demo_drops_acceptance_criteria()`：期望结果从 `has_kwarg=False` 翻转为 `True`；其余四个探针（未跟踪证据、篡改对照、未知 CLI ValueError、`--no-probe` fail-closed）结果不得回归。

---

## 附：机器票与结构化 issue 索引

| issue_id | severity | disposition_class | 摘要 |
|---|---|---|---|
| `claude/P3-1` | trivial | `ADVISORY` | `macao live-run` 演示流程的 reviewer 派发调用点未转发已声明的 `acceptance_criteria`，仅限自包含演示路径，两条真实生产命令路径已确认正确透传 |

`vote`: `YES_APPROVE`（限本轮申报范围：证据 Git 强归档绑定、执行者组合根 Fail-Closed、全适配器审查员准则透传；L4/PG-3 另行拒绝，见 §四）
