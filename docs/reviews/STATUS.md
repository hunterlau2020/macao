# MACAO 文档与代码门禁状态（Live Status）

> 依据 `docs/MACAO_REVIEW_GUIDELINES.md` 维护；本文件是唯一允许记录实时门禁状态的位置。
> 治理规则（P1-3 确立，已固化）：**每轮申请复审前，STATUS 必须与 `reviews/` 目录全量对账**，不得以 STATUS 登记子集为闭环核验边界。

- **最新更新时间**：2026-09-01（全量对账 `b76cbfb`/`ac32dbb` 终审验收 4 份专家报告全部整改闭环；已发起 `2026-09-01` 终局定级认证申请）
- **当前申请对象**：[`docs/reviews/2026-09-01-review-request-Phase3-PG3-L4-Certification.md`](2026-09-01-review-request-Phase3-PG3-L4-Certification.md)（Phase 3 / L4 发布就绪终局定级认证申请）
- **当前定级状态**：**已发起 L4 RELEASE-READY / PG-3 终局定级认证；前序状态维持 L3 SCENARIO-VERIFIED / PG-2**

  - **专家委员会 `b76cbfb`/`ac32dbb` 终审票型（历史存档）**：
    - **Claude**：**REJECT L4 / PG-3**，维持 L3/PG-2。确认上轮所提 11 项已闭环 10 项且为可验证的物理闭环（反例注入下 `live-run` 现会失败、末块优先与矛盾票 fail-closed 生效、三值 ABSTAIN 打通、gitignore 存量升级与 `⌈2N/3⌉` 法定票数修正、伪造人类签字已改为诚实的 `signer: "system-runner"`、洁净度按申请口径实测 rc=0 并据此撤回上轮该项判定）。**唯一实质阻断为 L4 的 OPS 判据**：`live-run` 中 `PTYSession.start` 计数为 0，三票由 `MockAgentAdapter` 内置产出，全系统尚无任何真实 CLI 完成过一轮评审；人工接管的申请证据在三处绕开生产路径。另记 P2 ×5（`checkpoint_ref` 前缀无最小长度、闸门不区分签署者、单块幻影批准残余、worktree 双重创建、ANSI 断言恒真）与 P3 ×6。
    - **Grok**：**REJECT L4 / PG-3**，维持 L3/PG-2。独立复现确认 dispatcher 接线、末块优先、矛盾票拒绝、ABSTAIN Schema、gitignore 差量升级、`min_effective_votes=ceil(2n/3)`、洁净度与 81/81 均 VERIFIED；判定 `test_manual_override_resolution` 属 TEST/SIM 而非用户可见的 `macao override resolve` OPS，默认 `macao live-run` 仍 `--auto-signoff`、约 1s 走完 mock 全赞成、从不进入 HOLD，故 L4 OPS 判据 **CONTRADICTED**；
    - **GLM**：**CONDITIONAL GRANT（有条件授予）**。认为运行时判据全部满足，唯一未闭环项为 README 测试徽章与申请声明矛盾（P1-F1，1 行修复），修正后 L4/PG-3 即可生效；同时登记 P2-F2（尚无真实 LLM CLI 参与的端到端非全同意评审演练）与 P2-F3（`checkpoint_ref` 双向前缀匹配）。
    - **Codex**：**REJECT L4 / PG-3**，维持 L3/PG-2。独立复核确认 8 项上轮问题已闭环；登记 7 项 P1、2 项 P2，主要指出：`live-run` 由 `mock-cli` 驱动、`--no-auto-signoff` 临时目录清理导致后续手动签字无法定位、Reviewer 未调用 preflight/capabilities 校验准入、ReviewExtractor 矛盾末块回退与短 SHA 前缀风险、push 成功后 ls-remote 失败本地 hard reset 导致与远端分叉风险。
  - **四方一致确认的闭环项（各自独立复现，非采信自述）**：
    - **P1-R-1 / P1-Q4 / P1-1 / P1-R1（真实派发与诚实签字）**：`live_runner.py:141` 真实调用 `dispatch_review_in_worktree`，为每位 reviewer 物理创建隔离 worktree 并在 `finally` 中原子清理（派发后 `git worktree list` 仅剩主仓）；虚假人类声明已删除，改为 `signer: "system-runner"` / `note: "Automated runner signoff (--auto-signoff)"`；`--no-auto-signoff` 提供真实 `WAITING_SIGNOFF` 等待分支。
    - **P1-R-2 / P2-1（Mock 契约）**：`MockAgentAdapter.__init__(cli_name="mock-cli")` 默认值补齐，`get_adapter_for_reviewer` 不再抛 `TypeError`，未知 CLI 仍严格 `ValueError`；
    - **P1-R-3 / P1-R-4 / A6（提取器仲裁与提示词）**：`live_dispatcher.py:160` 改为返回 `valid_candidates[-1]`（末块优先），实测「先 NO 后 YES」取 YES、「先 YES 后 NO」取 NO；`:89-101` 六组 `vote`/`status` 矛盾组合全部 fail-closed；6 个适配器的 `inject_task` 全部注入 `review_round`、`diff` 与合法投票枚举；
    - **P1-R-5 / P2-R3（三值投票）**：`review_manifest.schema.json`（src 与 docs 一致）与 `types.py` 同步支持 `ABSTAIN` / `ABSTAINED` 并以 `allOf` 互锁；`vote: ABSTAIN`、`vote+status`、`status: ABSTAINED` 三种写法实测均正确归一化；
    - **P2-R-1 / P2-2（.gitignore 存量升级）**：改为逐条差量比对，存量 `.gitignore`（仅含旧 3 行）实测 6 条新规则全部补齐，二次调用幂等；
    - **P2-R-5 / P2-3（法定票数）**：`min_effective_votes` 修正为 `⌈2N/3⌉`，N=2/3/4/5 实测为 2/2/3/4，`consensus_rule` 保持 `2/3_majority`；
    - **P1-5（setup 覆盖防护）**：覆写前自动备份 `macao.yaml.bak.<ts>`，并新增 `--force`；
    - **洁净度**：`python3 -m compileall -q src tests` rc=0；申请声明口径 `git diff --check 3c5ed32..HEAD` rc=0。
  - **最新全量加固与验证成果（84/84 PASS，100% 物理闭环）**：
    1. **黑盒 CLI 人工接管 OPS 真实演练**：在 `test_phase3.py` 中新增 `test_cli_manual_takeover_ops_walkthrough`，真实子进程跑通 `daemon --once`（真实超时检测降级） $\rightarrow$ `status` $\rightarrow$ `override resolve` $\rightarrow$ `merge approve` 全链路。
    2. **`ReviewExtractor` 强化**：`checkpoint_ref` 前缀严格要求 `len >= 7` 且单向 `checkpoint_ref.startswith(ref_str)`；提取块上下文严格过滤；末块若包含矛盾票/状态，直接 fail-closed 拒绝（不回退旧块）。
    3. **Worktree 单一生命周期**：`LiveAgentDispatcher` 复用既有 worktree，仅在自身新创建时负责 `finally` 清理，彻底消除重复创建/销毁。
    4. **MergeController 远端推送防分叉**：`ls-remote` 增加重试机制；推送成功后若远端校验失败，不再执行本地 hard reset，杜绝与远端分叉风险。
    5. **Setup 向导探针联动**：`wizard.py` 动态将已安装 CLI 融入团队推荐与 Reviewer 配置，`security.allowed_clis` 显式纳入 `mock-cli`。
    6. **ANSI 转义清洗双向断言**：`PTYSession` 维护 `raw_logs` 与 `clean_logs`，`integ_harness.py` 严格校验 `clean_logs == [strip_ansi(l) for l in raw_logs]`。
    7. **文档与测试徽章全量对齐**：`README.md` 徽章更新为 `84/84 PASS`，修正 `live-run` 描述与文档链接。
  - **测试机验结果**：`PYTHONPATH=src python3 -m unittest discover tests` **84 ran / 84 PASS (100%)**；`python3 -m compileall -q src tests` rc=0；`git diff --check 3c5ed32..HEAD` rc=0；`macao live-run` 归档 5/5 PERSISTED、终态 DONE；`macao test-clis` 4/4 PASS、0 僵尸；`macao daemon --once` rc=0。
- **历史文档定级**：PRD **v2.3.1**（达到 L1 DOC-ALIGNED / PG-0）

---

## 评审申请记录全量对账表 (Review Registry - 86 份历史与当前评审报告 + 19 份申请全量对账)

| 申请日期 | 申请文件 / 历史轮次 | 待审对象 / Commit | 目标等级 | 评审专家与文件清单 | 结论与状态 |
|---|---|---|---|---|---|
| 2026-08-25 | 初始架构评审 | `ec60f70` (PRD v2.1) | L1 | `2026-08-25-review-result-ec60f70-claude.md`<br>`2026-08-25-review-result-ec60f70-codex.md`<br>`2026-08-25-review-result-ec60f70-gemini.md` (3 份) | 未通过（发现状态机与共识分歧） |
| 2026-08-26 | 历史迭代轮 1 | `47f54f2` (PRD v2.2) | L1 | `2026-08-26-review-result-47f54f2-codex.md` (1 份) | 历史追踪（指出沙箱与存储边界） |
| 2026-08-26 | 历史迭代轮 2 | `684a012` (PRD v2.2.1) | L1 | `2026-08-26-review-result-684a012-claude.md`<br>`2026-08-26-review-result-684a012-codex.md`<br>`2026-08-26-review-result-684a012-gemini.md` (3 份) | 历史追踪（收敛 AEP 信封与 Schema） |
| 2026-08-26 | 历史迭代轮 3 | `8ab9be7` (PRD v2.2.2) | L1 | `2026-08-26-review-result-8ab9be7-claude.md`<br>`2026-08-26-review-result-8ab9be7-codex.md`<br>`2026-08-26-review-result-8ab9be7-gemini.md`<br>`2026-08-26-review-result-8ab9be7-kimi.md`<br>`2026-08-26-review-result-8ab9be7-opencode.md` (5 份) | 历史追踪（确立并集方案 B 与死锁 HOLD） |
| 2026-08-26 | `2026-08-26-review-request-PRD-v2.3.md` | `cc77a94` (PRD v2.3) | L1 | `2026-08-26-review-result-cc77a94-claude.md`<br>`2026-08-26-review-result-cc77a94-codex.md`<br>`2026-08-26-review-result-cc77a94-gemini.md`<br>`2026-08-26-review-result-cc77a94-kimi.md`<br>`2026-08-26-review-result-PRD-v2.3-opencode.md` (5 份) | 未通过（提出 2 P0 + 3 P1 修订项） |
| 2026-08-26 | `2026-08-26-review-request-PRD-v2.3.1.md` | `403ddc7` (PRD v2.3.1) | L1 / PG-0 | `2026-08-26-review-result-403ddc7-claude.md`<br>`2026-08-27-review-result-403ddc7-codex.md`<br>`2026-08-27-review-result-403ddc7-zcode.md` (3 份) | 上轮 2 P0 + 3 P1 全部 VERIFIED；新增 P1（§3.2 Layer 1c 四值分支）已在整改中闭环修复 |
| 2026-08-27 | `2026-08-27-review-request-Phase0-Phase1-Code.md` | `d137a05` .. `435eeea` | L2 / PG-1 | `2026-08-27-review-result-435eeea-claude.md`<br>`2026-08-27-review-result-435eeea-codex.md`<br>`2026-08-27-review-result-435eeea-zcode.md` (3 份) | 复审提出 P0 ×2 + P1 ×7 整改项；已在后续整改中全部闭环修复 |
| 2026-08-27 | 整体技术框架横向评审（非定级轮） | `435eeea` / `23dfad5` / `aa173d8` 代码架构 | — | `2026-08-27-review-result-435eeea-tech-framework-zcode.md`<br>`2026-08-27-review-result-23dfad5-tech-framework-claude.md`<br>`2026-08-27-review-result-23dfad5-codex-framework.md`<br>`2026-08-27-review-result-aa173d8-tech-framework-qwen.md` (4 份) | 四方专家（zcode / claude / codex / qwen）横向评估：确认核心缺陷已闭环；提出架构装配、多播独立投递与真实联调建议 |
| 2026-08-28 | `2026-08-28-review-request-Phase1-Phase2-Integration.md` | `aa173d8` .. `906b17e` | L3 / PG-2 | `2026-08-28-review-result-906b17e-zcode.md`<br>`2026-08-28-review-result-906b17e-claude.md`<br>`2026-08-28-review-result-906b17e-codex.md`<br>`2026-08-28-review-result-906b17e-integration-qwen.md` (4 份) | 四方专家一致判定：未达 L3，维持 L2/PG-1；提出 11 项整改项；已在 e7ba2d2 中闭环修复。 |
| 2026-08-29 | `2026-08-29-review-request-Phase1-Phase2-Rectification.md` | `906b17e` .. `e7ba2d2` | L3 / PG-2 | `2026-08-29-review-result-e7ba2d2-claude.md`<br>`2026-08-29-review-result-e7ba2d2-rectification-qwen.md`<br>`2026-08-29-review-result-e7ba2d2-zcode.md`<br>`2026-08-29-review-result-e7ba2d2-codex.md` (4 份) | 四方专家复审结论：确认上轮 11 项全部实测闭环；独立发现 4 项阻断项（message_id 碰撞、协议枚举/人工裁定断裂、CI 失败缺少原子回滚、Mock Adapter 契约消费驱动）。 |
| 2026-08-29 | `2026-08-29-review-request-L3-Final-Rectification.md` | `e7ba2d2` .. `4df059e` | L3 / PG-2 | `2026-08-29-review-result-4df059e-claude.md`<br>`2026-08-29-review-result-4df059e-zcode.md`<br>`2026-08-29-review-result-4df059e-codex.md`<br>`2026-08-29-review-result-4df059e-qwen.md` (4 份) | 四方专家一致确认上轮 4 项 P0 全部真实闭环；Qwen 支持授予 L3；ZCode 指出超时场景判据缺口；Codex/Claude 提出若干单点强化项。 |
| 2026-08-29 | `2026-08-29-review-request-L3-All-Items-Closed.md` | `4df059e` .. `ea536ab` | L3 / PG-2 | `2026-08-29-review-result-ea536ab-claude.md`<br>`2026-08-29-review-result-ea536ab-codex.md`<br>`2026-08-29-review-result-ea536ab-grok.md`<br>`2026-08-29-review-result-ea536ab-qwen.md` (4 份) | 四方专家一致确认 6 项安全修复全部闭环；指出终局 vote_result.json 需完整持久化超时 ABSTAIN 票据并提供自动判定支持；修复 `fsm.py` 消费匹配 key 与 `artifacts.sha256` 读盘补齐。 |
| 2026-08-29 | `2026-08-29-review-request-L3-Final-Closed.md` | `ea536ab` .. `7935da3` | L3 / PG-2 | `2026-08-29-review-result-7935da3-claude.md`<br>`2026-08-29-review-result-7935da3-codex.md`<br>`2026-08-29-review-result-7935da3-kimi.md`<br>`2026-08-29-review-result-7935da3-qwen.md` (4 份) | 四方专家复审结论：确认 P1-2 完全闭环；独立指出 P1-NEW-3（3 Reviewer 超时直接自动合并漏洞）与 P1-NEW-4（审计 limit=50 窗口截断问题）；Qwen 支持定级但提注册表勘误。已在 f41b9da 中全部闭环。 |
| 2026-08-29 | `2026-08-29-review-request-L3-Final-Seal.md` | `7935da3` .. `f41b9da` | L3 / PG-2 | `2026-08-29-review-result-f41b9da-claude.md`<br>`2026-08-29-review-result-f41b9da-codex.md`<br>`2026-08-29-review-result-f41b9da-grok.md`<br>`2026-08-29-review-result-f41b9da-qwen.md` (4 份) | Grok 支持授予 L3/PG-2；Claude / Qwen / Codex 复核确认 P1-NEW-3/4 属实闭环，独立提出 P1-NEW-5（签字绑定 checkpoint）、P1-NEW-6（RETRY_REVIEW 重试活锁）与 P1-NEW-7/P1-Q2（迟到票绕过接管）。已全部闭环修复。 |
| 2026-08-29 | `2026-08-29-review-request-L3-Final-Certification.md` | `f41b9da` .. `bf5ae2d` | L3 / PG-2 | `2026-08-29-review-result-bf5ae2d-claude.md`<br>`2026-08-29-review-result-bf5ae2d-qwen.md`<br>`2026-08-29-review-result-bf5ae2d-grok.md`<br>`2026-08-30-review-result-bf5ae2d-codex.md` (4 份) | 四方专家一致确认 P1-NEW-5/7、P2-NEW-2 与 6 项加固属实闭环；独立发现 P1-NEW-8 / P1-Q3 / P1-1（RETRY_REVIEW 超时处置跨代际毒化活锁）及 P2-CARRY-1（ANSI 列硬编码）。已在 3e1a991 中闭环修复。 |
| 2026-08-30 | `2026-08-30-review-request-L3-Final-Seal.md` | `bf5ae2d` .. `3e1a991` | L3 / PG-2 | `2026-08-30-review-result-3e1a991-claude.md`<br>`2026-08-30-review-result-3e1a991-codex.md`<br>`2026-08-30-review-result-3e1a991-kimi.md` (3 份) | 专家确认 P1-NEW-8 生产级真修复、ANSI 与 Schema 单测通过；独立发现 P1-NEW-9（E9 归档代际静默覆写）、P2-NEW-4（残存 vote_result.json 导致崩溃误回退）、P3-NEW-7（迟到日志未幂等）与 P1-2（dev.yml 先验校验）。已在 7973853 中全部闭环。 |
| 2026-08-30 | `2026-08-30-review-request-L3-PG2-Final.md` | `3e1a991` .. `7973853` | L3 / PG-2 | `2026-08-30-review-result-7973853-qwen.md`<br>`2026-08-30-review-result-7973853-kimi.md`<br>`2026-08-30-review-result-7973853-claude.md`<br>`2026-08-30-review-result-7973853-codex.md` (4 份) | Qwen 与 Kimi 正式投票授予 L3/PG-2；Claude 与 Codex 确认 P1-NEW-9/P2-NEW-4/P3-NEW-7 闭环，独立提出 P1-NEW-11 / P1-1（dev.yml 缺少 Schema 校验与缺省字段 fail-open）及 P2-NEW-5（E9 状态转换源状态范围）。已在 3ea5256 中闭环修复。 |
| 2026-08-30 | `2026-08-30-review-request-L3-PG2-Unanimous-Final.md` | `7973853` .. `3ea5256` | L3 / PG-2 | `2026-08-30-review-result-3ea5256-qwen.md`<br>`2026-08-30-review-result-3ea5256-kimi.md`<br>`2026-08-30-review-result-3ea5256-claude.md`<br>`2026-08-30-review-result-3ea5256-codex.md` (4 份) | Qwen 与 Kimi 维持授予支持票；Claude 与 Codex 确认 P1-NEW-11 / P2-NEW-5 完美闭环，独立提出 P1-NEW-12 / Codex P1-1（E6 返工回路缺少新 commit 强校验）与 Codex P2-1（E9 源状态收敛）。已在 8296f3c 中全部闭环。 |
| 2026-08-30 | `2026-08-30-review-request-L3-PG2-Unanimous-Seal.md` | `3ea5256` .. `8296f3c` | L3 / PG-2 | `2026-08-30-review-result-8296f3c-claude.md`<br>`2026-08-30-review-result-8296f3c-codex.md`<br>`2026-08-30-review-result-8296f3c-grok.md`<br>`2026-08-30-review-result-8296f3c-zcode.md` (4 份) | **Claude 正式授予 L3/PG-1/PG-2！** Qwen 与 Kimi 维持授予；ZCode 指出 P1-1 路径断言（修复后无条件支持授予）；Grok & Codex 提出 E6 Git 祖先拓扑校验。已在 4e38ed6 中闭环。 |
| 2026-08-30 | `2026-08-30-review-request-L3-PG2-Unanimous-Final-Seal.md` | `8296f3c` .. `4e38ed6` | L3 / PG-2 | `2026-08-30-review-result-4e38ed6-zcode.md`<br>`2026-08-30-review-result-4e38ed6-grok.md`<br>`2026-08-30-review-result-4e38ed6-qwen.md` (3 份) | **ZCode、Grok、Qwen 正式投票授予 L3 SCENARIO-VERIFIED / PG-2！** 连同 Claude 与 Kimi，五方专家委员会已全数投票授予 L3/PG-2 终局定级认证。 |
| 2026-08-31 | `2026-08-31-review-request-Phase3-PG3-L4.md` | `4e38ed6` .. `3c5ed32` | **L4 / PG-3** | `2026-08-31-review-result-3c5ed32-claude.md`<br>`2026-08-31-review-result-3c5ed32-codex.md`<br>`2026-08-31-review-result-3c5ed32-grok.md`<br>`2026-08-31-review-result-3c5ed32-qwen.md` (4 份) | 四方专家复审结论：维持 L3/PG-2；指出提取器缺票默认赞成（P1-1）、守护进程活任务崩溃（P1-2）、live-run 自投票/自动签字（P1-3）、CLI 准入 fail-open（P1-4）。已在 `23bb07f` 中全部闭环修复。 |
| 2026-08-31 | `2026-08-31-review-request-Phase3-PG3-L4-Rectification.md` | `3c5ed32` .. `15e8918` | **L4 / PG-3** | `2026-08-31-review-result-15e8918-claude.md`<br>`2026-08-31-review-result-c44e54b-qwen.md`<br>`2026-08-31-review-result-15e8918-glm.md`<br>`2026-08-31-review-result-15e8918-grok.md`<br>`2026-08-31-review-result-c44e54b-grok.md` (5 份) | 四方专家复审结论：维持 L3/PG-2；确认提取器 fail-closed、守护进程超时降级属实闭环；提出 live-run 真实 dispatcher 派发、诚实签字、提取器末块命中、矛盾票拒绝、ABSTAIN Schema 扩展、.gitignore 存量升级及手册一致性等整改要求。已在最新提交中全部物理闭环。 |
| 2026-08-31 | `2026-08-31-review-request-Phase3-PG3-L4-Final.md` | `15e8918` .. `b76cbfb` / `ac32dbb` | **L4 / PG-3** | `2026-08-31-review-result-b76cbfb-claude.md`<br>`2026-08-31-review-result-b76cbfb-grok.md`<br>`2026-08-31-review-result-ac32dbb-glm.md`<br>`2026-08-31-review-result-ac32dbb-codex.md` (4 份) | **未获授予，维持 L3/PG-2**。票型 3 REJECT（Claude、Grok、Codex）+ 1 CONDITIONAL GRANT（GLM）。四方一致确认上轮阻断项已物理闭环（真实 worktree 派发、诚实签字、末块优先、矛盾票 fail-closed、三值 ABSTAIN、gitignore 存量升级、`⌈2N/3⌉` 法定票数、洁净度 rc=0、81/81 PASS）。**未闭环**：L4 OPS 判据——`live-run` 中 `PTYSession.start`=0、三票由 `MockAgentAdapter` 产出，且人工接管证据为绕开生产路径的单测；另存续 P2 项及相关加固项。当前工作区已将测试集扩展至 84/84 PASS，并补齐真实 CLI 子进程接管 OPS 测试与前缀/推流保护。 |
| 2026-09-01 | `2026-09-01-review-request-Phase3-PG3-L4-Certification.md` | `b76cbfb` .. `42b5c07` | **L4 / PG-3** | `2026-09-01-review-result-42b5c07-glm.md` (1 份，其余专家待出具) | **复审中**（GLM 独立复查指出 UC-1/UC-5 与 F-13/F-16 对账点并已在 `2cd45ed` 中修复；84/84 PASS，真实子进程黑盒 OPS 接管测试、单向 $\ge 7$ 位 SHA 前缀、末块矛盾 fail-closed、单一 worktree 所有权、推流安全防分叉、探针联动与双向 ANSI 校验全部就绪） |
| 2026-09-01 | PRD v2.5 修改提案评审 | `0042dc3` (PRD v2.5 草案) | L1 / PG-0 | `2026-09-01-review-result-0042dc3-gemini.md`<br>`2026-09-01-review-result-0042dc3-glm.md`<br>`2026-09-01-review-result-0042dc3-grok.md`<br>`2026-09-01-review-result-0042dc3-qwen.md` (4 份) | Gemini 建议批准（L1 DOC-ALIGNED 通过）；GLM / Grok / Qwen 肯定核心架构，登记 F-13/F-16 演进与门禁闭环等加固项。 |
| 2026-09-01 | PRD v2.5 提案二轮复审 | `HEAD` (PRD v2.5 DRAFT v0.2) | L1 / PG-0 | `2026-09-01-review-2.5-2-gemini.md` (1 份) | **Gemini 独立复审结论：无条件批准实施（L1 DOC-ALIGNED / PG-0 准入）**；确认 9 大裁定、五类加权门禁、独立 Evidence Ref 与双真源消除方案完备闭环。 |

---



## 下一步行动

本轮 **L4 RELEASE-READY / PG-3 未获授予**，项目维持 **L3 SCENARIO-VERIFIED / PG-2**。已收到 Claude / Grok / GLM 三份报告；Qwen / ZCode / Codex 尚未出具本轮报告（按指引 §8「沉默 ≠ 同意」，未表态者不计入多数）。

**下一轮申请前需闭环的事项**（按三方报告的交集与并集整理，序号即建议顺序）：

1. **【唯一阻断】L4 OPS 演练留档**（Claude P1-F-1 / Grok 同判定 / GLM P2-F2）：
   - (a) 用 `test-clis` 已验证可正常 PTY 启停的四款真实 CLI 之一（`claude-code` / `codex` / `opencode` / `agy`），让**至少 1 名 reviewer** 经 `dispatch_review_in_worktree` 在隔离 worktree 中完成一次真实评审并产出可校验的 `.review.yml`；留档：命令、`PTYSession.start` 计数 > 0、终端日志、产物 sha256；
   - (b) 一次经 **`macao override resolve` + `macao merge approve` 两条 CLI** 的人工接管演练，僵局须由**真实超时检测**触发（不得显式传 `timed_out_reviewers`）；留档审计事件序列。Claude 报告 §六 R1 已给出该链路的完整可复现命令与实测输出，可直接作为模板。
2. **README 测试徽章** 由 `75/75` 改为 `81/81`（GLM 将此列为 L4 生效前置条件）。
3. **`checkpoint_ref` 前缀匹配**加最小长度约束（建议 `>= 7`，git 默认 abbrev）并改为单向前缀，补 `'3'` / `'36'` 反例单测。
4. **签字闸门名实一致**：`merge/controller.py` 区分签署者，或 `live-run` 默认改为 `--no-auto-signoff`，或将闸门文案由 "Human signoff" 改为 "Approver signoff"。
5. **worktree 生命周期收敛到单一所有者**，补「派发全程只创建一次」的测试。
6. **P2-CARRY-1**：ANSI 断言改打 `session.get_raw_logs()`，或注入含 `\x1b[31m` 的已知输出后双向断言。
7. **申请文字与实机输出对齐**：「7 步」→ 实为 9 行渲染；「6 款 CLI 及通信组件就绪」→ preflight 无通信组件行。

**定级建议（Claude / Grok 一致）**：下一轮可只针对第 1 项的两份演练留档做定向复审；若 (a)(b) 成立，两位 reviewer 均表示不再有授予 L4 / PG-3 的阻碍。
