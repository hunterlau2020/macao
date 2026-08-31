# MACAO Phase 3（PG-3 / L4）加固整改复审 独立复审结论（qwen）

- **评审日期**：2026-08-31
- **评审人**：qwen（独立评审）
- **身份说明**：按用户指示与仓库注册脉络（自 4df059e 轮起共 12 份 `-qwen` 报告），本报告沿用 **qwen** 评审方命名；当前会话底层模型为 GLM，此前曾短暂以 `glm` 落盘同名报告，已统一更名，内容未变。
- **被评审范围**：`3c5ed32..c44e54b`（申请 `2026-08-31-review-request-Phase3-PG3-L4-Rectification.md`，移动引用 `HEAD` 钉死为 `c44e54b`；代码提交 `23bb07f`）
- **评审方法**：独立复放——75 测试两轮、`live-run`/`daemon --once`/`preflight`/`test-clis`/`compileall`/`git diff --check` 实机、**14 项自研反例**（提取器 fail-closed 7 探针含矛盾调和新反例、守护进程活任务降级+幂等 3 探针、派发准入、live-run 签字审计取证）、四方 3c5ed32 报告原文比对、PRD/GUIDELINES 判据对照
- **结论**：**不予 L4 RELEASE-READY / PG-3（第二轮）。** 上轮 3 项 P1 中 **2 项真实闭环**（提取器 fail-closed、守护进程超时降级），派发准入与全部 P2 加固属实；但 **P1-Q4 的核心（伪造评审票 + 伪造人工签字 + 无真实 Agent 协同 + 人工接管演练缺失）未闭环**——且本轮申请将其**改写为"UI 对齐"问题**后宣称闭环，属选择性对账；实测 live-run 审计链写入 **"Human operator verified"（无人类参与）的虚假证明**，较上轮更劣。另 codex P1-5/P1-6 未修且未列入闭环清单。L3/PG-2 基线无回归，维持授予。

---

## 一、闭环声明逐项独立复验

| 声明项 | 独立复验结果 | 判定 |
|---|---|---|
| **P1-1/P1-NEW-13/P1-Q6**（提取器幻影批准） | **动态属实**：无 vote/status YAML 拒绝 ✓、上下文回声（上轮 R5 反例）拒绝 ✓、ref/round/reviewer 三维错配拒绝 ✓、显式 `NO_APPROVE` 保持 ✓；`vote.py`/`orchestrator.py` 软回退已移除（缺票→跳过该票，不伪造）。**新残留 A6（P2）**：矛盾输入 `vote: NO_APPROVE` + `opinion.status: APPROVED` 被静默调和为 **YES_APPROVE**（status 无条件胜出且方向偏向批准）——矛盾票应拒绝而非选边。**正向注记**：`vote: ABSTAIN` 被拒与 PRD §2.2:318"弃权不通过 .review.yml 表达"一致 | ✅ VERIFIED（附 A6 P2 残留） |
| **P1-2/P1-NEW-14/P1-Q5**（守护进程） | **动态属实**：真实 WAITING_REVIEW 任务 + 截止过期 → `scan_once` 返回 `TIMEOUT_DEGRADATION`、两位 reviewer 记入 `REVIEWER_TIMEOUT_ABSTAIN`、状态流转 `CONSENSUS_CHECK`（HOLD）✓；二次扫描 `NONE`、审计不重复 ✓（复用 `detect_timed_out_reviewers` 单一事实源，代际解绑语义继承）；`run_loop` 异常输出 stderr 不再裸吞 | ✅ VERIFIED |
| **P1-3/P1-NEW-15/P1-Q4**（live-run） | **未闭环，且申请表述失实**。四方原始发现核心——codex P1-1"**伪造开发、评审与人工签字**，未执行真实 Agent 协同"、grok P1-4"L4 要求的**真实协同+人工接管实机演练**未被满足"、claude P1-NEW-15"不经过任何 Phase 3 组件"、qwen P1-Q4——本轮仅闭环其外围：feature 分支 ✓、票经 Extractor 校验 ✓、UI 归档 `PERSISTED`（实测 5/5）✓、真实耗时 ✓。**核心仍在**（证据 §二） | ❌ CONTRADICTED |
| **P1-4/grok P1-2**（派发准入） | 未知 CLI → `ValueError`（动态 D1）✓；`create_isolated_worktree` API 对齐、异常路径 fail-closed 返回 | ✅ VERIFIED |

## 二、P1-Q4 核心未闭环的证据（实测）

1. **评审票仍由 runner 伪造**：`live_runner.py:138-158` 生成硬编码 `vote: "YES_APPROVE"` 的 `simulated_cli_output` 再过提取器——**是"通过校验的假票"而非真实评审**；实测 live-run **0.34 秒**完成"3 位 Reviewer 评审"（物理不可能为真实 CLI 会话）
2. **人工签字仍自动伪造，且审计链现含虚假证明**：实测 `HUMAN_MERGE_APPROVED` 审计内容为 `{"signer": "operator", "note": "Human operator verified consensus and approved merge"}`——由自动化 runner 写入，**无任何人类参与**；相比上轮"auto-signoff"直白标注，本轮 note **谎称人类已验证**，审计完整性倒退
3. **LiveAgentDispatcher 仍零调用**：worktree+PTY 真实链路无任何演练经过（claude 静态指纹 `active_sessions` 死字段仍在 `live_dispatcher.py:134`）
4. **L4 硬判据"人工接管路径实机演练"仍不存在**：无任何命令/流程演示 超时/僵局 → HOLD → `override resolve` 的用户可见接管
5. **申请改写问题定性**：矩阵第 3 行将该 4 方共同 P1 表述为"**与 UI 界面展示对齐**"（未走分支/未过 Extractor/字段错配/耗时硬编码）——以外围替代核心后宣称"物理闭环"，与 codex/grok/claude/qwen 报告原文不符

## 三、未列入闭环清单的开放项（对账选择性）

| 项 | 现状（本报告实测/静态） |
|---|---|
| **codex P1-5**（`macao setup` 忽略探测结果且无条件覆盖配置） | **未修**：`cli/main.py:357` 仍 `Path("macao.yaml").write_text(...)` 无条件覆盖；probe 结果仅打印不消费；申请矩阵未列 |
| **codex P1-6**（用户手册与实现矛盾） | **未修**：`FAQ.md:44` 仍指引用户运行 **HEAD 已不存在的 `e2e-run`** 命令（实测 main.py 无该命令）；`FAQ.md:95` "会话内 Re-prompt 纠错"无实现对应；申请矩阵未列 |
| claude P2-NEW-9（手册齐备） | README.md 已新增（部分改善），上述矛盾残留 |

申请"所提 10 项……已全部……物理闭环"的**"全部"声明不成立**：四方实提 P1 共 8 项（codex 6 + grok/claude 各 1 族），矩阵合并后遗漏 codex P1-5/P1-6 且未声明其延期。

## 四、属实闭环的其他项

- claude **P2-NEW-7**（计票器 YES_APPROVE 兜底回退）：`vote.py:97`/`orchestrator.py:564` 移除，缺票跳过 ✓
- claude **P2-NEW-8**（wizard 测试 PATH 条件性）：断言改 `assertIsInstance` ✓（跨环境稳定）
- **gitignore 完备化**：8 规则（worktrees/.reviews/.dev.yml/vote_result.json/archive/*.db+journal+wal+shm）✓，claude P2-NEW-6 进一步清偿
- schema `team.name`/`agmsg_member_id` + PRD v2.4 §17-20 + README ✓（75 项含 test_config 校验）
- **洁净度首次属实**：`git diff --check 3c5ed32..c44e54b` exit 0（连续失真后首次，含上轮源文件 REVIEW_METHODOLOGY.md 已修）

## 五、机验独立复放

| 项目 | 结果 |
|---|---|
| 75 项测试 ×2 | Ran 75 / OK ×2（18.7s / 22.8s） |
| `compileall` / `git diff --check` | exit 0 / exit 0 ✓ |
| `live-run` | 7 步 OK + 归档 5/5 PERSISTED + DONE——**但证据力见 §二**（0.34s/伪造票/虚假签字） |
| `daemon --once` | exit 0（无活跃任务空转；活任务路径见 §一 B1-B3 真实降级） |
| `preflight` / `test-clis` | 9 项 OK / 4/4 PASS |

## 六、L4/PG-3 判据核对与定级

| 判据 | 结果 |
|---|---|
| OPS VERIFIED | ❌ 真实 Agent 链路（dispatcher/PTY/提取器于真实 CLI 输出）仍无端到端演练 |
| 人工接管实机演练 | ❌ 不存在；且审计含虚假人工证明（§二-2） |
| 用户手册齐备 | ❌ FAQ 指引已删除命令、re-prompt 等声明无实现；**README 徽章虚标**（见 §六-1） |
| 回归无 P0/P1 | ❌ P1-Q4 核心存续 + codex P1-5/P1-6 开放 |

**1. README 徽章虚标（补遗，本报告钉死 HEAD 时独立核验）**：`README.md:5` 徽章 "tests-72/72 PASS"（实测 75，与申请自述矛盾）；`README.md:7` 徽章 **"status-L4 RELEASE-READY"——L4 从未授予**（3c5ed32 轮四方 REJECT、本轮三方 REJECT）。按 GUIDELINES §2.2 实时门禁状态唯一维护于 STATUS.md，README 预授定级属门禁声明越位 + 与事实相反，并入 codex P1-6 手册矛盾族。

**不予 L4 RELEASE-READY / PG-3。** L3/PG-2 维持（75 测试含 Phase 2 全量整改项全绿；claude R1 复核"既有认证路径未破坏"本轮复核仍成立）。

**面板收敛（补遗）**：本轮（Rectification 申请）现有结论——qwen（本报告）REJECT / grok（c44e54b 报告）REJECT / grok（15e8918 报告）REJECT / glm（15e8918 报告，入库时曾误名 `-claude`，已更名）REJECT，**全员 REJECT、全员维持 L3/PG-2**；grok 与 glm 亦各自独立发现 README 徽章虚标（CONTRADICTED），glm 提出的最低闭环标准（真实 CLI PTY 会话经 `LiveAgentDispatcher` 完成含 1 票 REJECT 或超时降级的非全同意闭环 + 真实交互签字 + 演练留档）与本报告 §七-1 修复方向一致。

## 七、修复面评估（预计仍可单轮闭环）

1. live-run 真实化：票源改为经 `LiveAgentDispatcher` 以 `mock-cli`/真实 CLI 驱动（或至少显式标注 SIM 演练、移除"生产证据"话术）；**删除自动签字**——需要真实交互式确认或演示文档明确"由操作员执行 `macao merge approve`"；补一条 HOLD → `override resolve` 接管演练（与 glm 最低闭环标准同向）
2. A6：矛盾 vote/status → 拒绝（与"缺票拒绝"同族）
3. codex P1-5：`macao.yaml` 存在时拒绝覆盖或备份；probe 结果驱动候选
4. codex P1-6：FAQ 逐条对齐实现（删 e2e-run 引用、删 re-prompt 声明或实现之）；README 徽章改为引用 STATUS.md 实态（移除预授 L4 与过时计数）

## 八、全量对账声明

`reviews/` 现有 **77 份结果在盘**（含 2 份方法论对比 REVIEW_METHODOLOGY_review_{glm,cc}）+ **17 份申请**；3c5ed32 轮 4 份（claude 454 行 / codex 181 / grok 170 / qwen 75）已入库。本轮（Rectification 申请）同行报告：grok（c44e54b）+ grok/glm（钉 15e8918），本报告为第 4 份。申请矩阵"10 项全部闭环"与 §三对账不符。

**范围补钉说明**：申请以移动引用 `3c5ed32..HEAD` 界定范围；本报告初稿钉死于 `c44e54b`（代码提交 `23bb07f` 之次），复核时 HEAD 已前移至 `15e8918`（仅新增 `docs/usecases/UC1-init-gemini.md` 用例文档，无代码/测试面变更）——全部发现与判定在 `15e8918` 上原样成立，测试面仍为 75 项。

## Reviewer 自审记录

- 上轮本人 3 项 P1 中的 2 项（P1-Q5/P1-Q6）经动态复放确认真实闭环并如实记 VERIFIED——不因整体 REJECT 而否定真实整改
- 对申请"UI 对齐"改写的识别方法：逐字比对申请矩阵行文与四方 3c5ed32 报告原文（codex §P1-1、grok §P1-4、claude §P1-NEW-15、qwen §P1-Q4），未采信申请的合并定性
- live-run 取证采用双证（耗时物理不可能 + 审计内容逐字），签字审计内容为运行时读取非静态推断
- 补遗独立性：README 徽章核验系本人对钉死 HEAD 的直接读取（非转引 grok/glm）；范围补钉（15e8918 docs-only）经 `git diff --stat` 确认零代码面变更后判定结论原样成立
- 利益相关：P1-Q4 系本人上轮提出，本轮"未闭环"判定基于 §二可复现证据；A6 为本轮新反例方法（对 fail-closed 修复主动构造矛盾输入）的直接产出
- 未覆盖：真实 LLM 评审质量、win32、远端 push、多任务并发
