# MACAO Phase 3 PG-3 / L4 加固整改复审 对齐/评审结论

- **评审日期**：2026-08-31
- **评审范围**：Commit 范围 `3c5ed32`..`15e8918`（HEAD），重点整改 Commit `23bb07f`、`2fb6031`、`8871d00`
- **评审对象**：`docs/reviews/2026-08-31-review-request-Phase3-PG3-L4-Rectification.md`
- **对齐基准**：`docs/MACAO_PRD_v2.md`（v2.4）、`docs/MACAO_REVIEW_GUIDELINES.md` v1.0
- **评审人**：glm（独立复审，机验复现）
- **结论**：**REJECT L4 RELEASE-READY / PG-3（本次不予授予）；维持 L3 SCENARIO-VERIFIED / PG-2 有效，无回归**

---

## 0. Reviewer 自审记录

- 按指南 §9 强制自检 5 项逐条执行；本轮无历史连续漏审需登记，但发现申请文档存在 **checklist-C 类确定性用语偏差**（见 P1-R1），已在本轮显式登记。

## 已对齐 / 已确认项（均经独立机验，非采信自述）

| 项 | 证据 | 验证状态 |
|---|---|---|
| **P1-1/P1-NEW-13/P1-Q6 ReviewExtractor Fail-Closed** | `live_dispatcher.py:40-131`：旧版 `parsed["vote"] = vote or "YES_APPROVE"`（3c5ed32 版 :90/:200/:216）已全部移除；现缺 vote 且缺 status 即 `continue` 拒绝；上下文字段（reviewer.id / checkpoint_ref / review_round）存在时强一致校验。配套测试 `test_phase3.py:63/77` 存在且通过 | **VERIFIED (CODE+TEST)** |
| **vote.py 软兜底移除（P2-NEW-7）** | `vote.py:94-99`：`data.get("opinion",{}).get("vote","YES_APPROVE")` → 无默认值 + `if not vote_val: continue` | **VERIFIED (CODE)** |
| **P1-2/P1-NEW-14/P1-Q5 Daemon 单一事实源与超时降级** | `daemon.py:31-53`：复用 `Orchestrator.detect_timed_out_reviewers`；`REVIEWER_TIMEOUT_ABSTAIN` 审计事件（detail 键名 `reviewer_id/review_round/checkpoint_ref`）；`timed_out_reviewers` 驱动共识仲裁；`run_loop` 异常写 stderr（daemon.py:75-77），无裸 pass | **VERIFIED (CODE+TEST)**，`test_phase3.py:150` 实测 0s 超时 → ABSTAIN×2 + 审计事件×2 |
| **P1-4 CLI 准入 Fail-Closed** | `live_dispatcher.py:108-115`：未注册 CLI 严格 `raise ValueError`；worktree 对接 `GitManager.create_isolated_worktree` | **VERIFIED (CODE)** |
| **P2-NEW-8 向导环境解耦** | `test_phase3.py:119` `assertIsInstance(clis, list)` | **VERIFIED (TEST)** |
| **Git 隔离注入** | `wizard.py:80`：注入 `.macao/worktrees/`、`.macao/.reviews/`、`.macao/.dev.yml`、`.macao/vote_result.json`、`.macao/archive/`、`.macao/*.db` 及 journal/wal/shm；幂等性有测试 | **VERIFIED (CODE+TEST)** |
| **Schema/PRD/文档同步** | `macao_config.schema.json`（src 与 docs 双份一致）新增 `team.name`、`agmsg_member_id`；PRD v2.4 §17–§20 章节实际存在（行 1701/1714/1722/1729）；README 180 行含 `preflight/test-clis/daemon/live-run` 命令文档（P2-NEW-9 实质闭环）；`docs/FAQ.md` 在 | **VERIFIED (DOC)** |
| **75/75 测试全绿** | 本机复现：`Ran 75 tests in 20.693s, OK` | **VERIFIED (TEST)** |
| **daemon --once / preflight** | 本机复现：`daemon --once` exit 0、`{'active_task': None, 'action_taken': 'NONE'}`；`preflight` 表格全 OK（claude-code/codex/opencode/agy/cursor/kimi/mock-cli），exit 0 | **VERIFIED (OPS-部分)** |

## P0：必须先解决

无。

## P1：进入 L4 前必须解决

### P1-R1　L4 核心判据"人工接管路径实机演练 + OPS VERIFIED"仍为 CLAIM_ONLY：live-run 是模拟评审而非真实 CLI 协同，"真实操作员签字"为硬编码审计事件

- **证据 1**：`live_runner.py:144-166` —— 第 5 步"评审"由代码字符串模板 `simulated_cli_output = f"""```yaml ... vote: "YES_APPROVE" ..."""` 直接构造，经 `ReviewExtractor` 校验后落盘。**没有任何真实 CLI 进程被拉起**，3 位 reviewer 全部硬编码 `YES_APPROVE`。申请文档称"7 步全绿实机演练"（§二）、"真实协同流程重塑"（§一 P1-3 行），属把 SIM 冒充 OPS。
- **证据 2**：`live_runner.py:173-179` —— 所谓"记录真实操作员签字"实为 `log_audit_event(task_id, "HUMAN_MERGE_APPROVED", {"signer": "operator", ...})` 硬编码写审计，无任何人工介入点。这与上轮 Qwen P1-Q4（自动签字）的整改声称直接矛盾。
- **判据**：指南 §2.1 L4 = L3 + **人工接管路径实机演练**；§3.3 L4 要求 OPS VERIFIED。当前 OPS 证据全部为模拟闭环（sandbox git repo + 模板 YAML），preflight/test-clis 仅证明 CLI 可拉起，不构成端到端真实协同演练。
- **最低闭环标准**：(a) live-run 至少一次以真实 CLI PTY 会话（经 `LiveAgentDispatcher.dispatch_review_in_worktree`）完成非全同意的评审闭环（含至少 1 票 REJECT 或超时降级）；(b) 人工签字改为真实交互输入（或演示记录中含可辨识的操作员介入点），演练留档（日志 + 产物 sha256）。

### P1-R2　申请文档措辞把设计目标/模拟结果表述为既成事实（checklist-C 复发）

- 申请 §一 P1-3 行"真实操作员签字"、§二"`macao live-run` 7 步全绿实机演练"如上所述与代码事实不符；§三"全套系统具备生产级鲁棒性"在未做任何失败路径实机演练（真实 CLI 超时、PTY 断连、部分评审失败）前属 CLAIM_ONLY。按指南 §9-C，确定性/完成性用语必须区分"目标"与"已验证"。

## P2/P3：可延期但需登记

- **P2-R3**　`ReviewExtractor` 语义映射失真：`live_dispatcher.py:92-94` 将 `vote: "ABSTAIN"` 的 status 强制写为 `CHANGES_REQUESTED`（弃权被标注为"要求修改"）；且仅有 `status: "ABSTAIN"` 无 vote 的合法弃权会被整体拒绝。建议：ABSTAIN 保持 ABSTAIN/ABSTAINED 语义闭环。
- **P2-R4**　上下文绑定仅在元数据"存在时"生效（`live_dispatcher.py:102-107`）：一份不含 reviewer/checkpoint 字段但含显式 vote 的无关 YAML 仍可被接受并回填派发上下文。与申请措辞"若包含…必须一致"字面一致，但作为幻影批准防线弱于其宣称强度，建议要求 reviewer.id 必填。
- **P3-R5**　申请文档引用 "`live_dispatcher.py:215` 准入强校验" 行号错误（实际为 :108-115；:215 处是 direct_file 读取逻辑）。
- **P3-R6**　`parsed["reviewer"] = {"id": agent_id, "cli": agent_id}`（:117）将 cli 字段回填为 agent_id，与配置中真实 cli 名可能不一致。

## 交叉文档需做的文字修订

1. 申请文档 P1-3 行"真实操作员签字"→"演练中记录操作员签字占位审计事件（待真实人工演练替换）"；"实机演练"→"沙箱模拟闭环演练"。
2. STATUS.md 测试机验段 `macao live-run` 描述同步加"模拟评审"限定，避免下游按 OPS VERIFIED 采信。

## 建议的闭环顺序与验收标准

1. 修复 P1-R1：真实 CLI PTY 演练（含 1 次非全同意 + 1 次真实超时降级）+ 真实人工签字交互，留档日志与产物哈希 → OPS 达 VERIFIED；
2. 同步修订申请/STATUS 措辞（P1-R2）；
3. P2-R3/R4 登记排期，随下轮 L4 申请批处理；
4. 验收：重新提交 PG-3/L4 申请时附演练证据（命令、commit、审计事件序列、归档产物 sha256 清单）。

## 最终判定

| 门禁 | 判定 |
|---|---|
| 上轮 10 项整改项闭环 | **7 项 VERIFIED、P1-3 部分 VERIFIED（见 P1-R1/R2）** |
| L3 / PG-2 | **维持有效**（75/75 全绿本机复现，Phase 2 已认证路径无回归） |
| **L4 / PG-3** | **不予授予**，阻断项 P1-R1、P1-R2（不可豁免） |
