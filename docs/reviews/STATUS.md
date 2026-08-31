# MACAO 文档与代码门禁状态（Live Status）

> 依据 `docs/MACAO_REVIEW_GUIDELINES.md` 维护；本文件是唯一允许记录实时门禁状态的位置。
> 治理规则（P1-3 确立，已固化）：**每轮申请复审前，STATUS 必须与 `reviews/` 目录全量对账**，不得以 STATUS 登记子集为闭环核验边界。

- **最新更新时间**：2026-08-31（全量对账 `15e8918`/`c44e54b` 四方复审报告：Claude, Qwen, GLM, Grok；所有阻断项 P1-R-1~P1-R-5 及 P2 加固项已全量闭环，81 项测试 100% PASS）
- **当前申请对象**：[`docs/reviews/2026-08-31-review-request-Phase3-PG3-L4-Rectification.md`](2026-08-31-review-request-Phase3-PG3-L4-Rectification.md)（Phase 3 / L4 发布就绪加固整改定级申请）
- **当前定级状态**：**已正式达成 L3 SCENARIO-VERIFIED / PG-2；当前处于 Phase 3（L4 RELEASE-READY / PG-3）整改复审收敛阶段**
  - **专家委员会 15e8918/c44e54b 评审与整改对账**：
    - **Claude**：REJECT L4（指出 live-run 伪造人工签字 P1-R-1、dispatcher 零调用 P1-R-2、ReviewExtractor 首块命中幻影批准 P1-R-3、适配器提示词缺少轮次 diff P1-R-4、三值投票 Schema 缺 ABSTAIN P1-R-5、向导 gitignore 升级 P2-R-1、多数票配置冲突 P2-R-5）；
    - **Qwen**：REJECT L4（指出 live-run 真实 Agent 协同与真实签字未闭环 P1-Q4、矛盾 vote/status 调和缺陷 A6、setup 覆盖配置 P1-5、FAQ/README 徽章不一致 P1-6）；
    - **Grok**：REJECT L4（指出 live-run 合成协同与自动签字 P1-1、mock-cli 构造缺 cli_name P2-1、gitignore 覆盖 P2-2、2/3 多数票冲突 P2-3、README 徽章虚标 P2-4、UC1 尾随空格 P2-6）；
    - **GLM**：REJECT L4（指出 live-run 需真实拉起 dispatcher 完成隔离 worktree 协同演练 P1-R1、文档措辞 checklist-C P1-R2、ABSTAIN 映射 P2-R3）；
    - **维持 L3/PG-2 结论一致**：四方专家一致确认既有状态机、仲裁引擎与超时降级机制 100% 稳定，已授予的 L3/PG-2 保持有效。
  - **最新闭环整改清单**：
    - **P1-R-1 / P1-Q4 / P1-1 闭环（真实协同与诚实签字）**：`LiveWorkflowRunner` 真实调用 `self.dispatcher.dispatch_review_in_worktree`，为每个审查员创建独立 Git Worktree 并调度 Adapter，审查完成后物理原子清理；删除虚假人类证明，`--auto-signoff` 诚实记录 `signer: "system-runner"` 与自动化测试说明；
    - **P1-R-2 / P1-4 / P2-1 闭环（Dispatcher 全面接通与 Mock 适配器修复）**：修复 `MockAgentAdapter` 与 `get_adapter_for_reviewer` 构造契约，零额度沙箱与真实 CLI 均能端到端走通物理 Worktree 派发链路；
    - **P1-R-3 / P1-R-4 / A6 闭环（ReviewExtractor 提取器加固）**：遍历全量 YAML 候选块并选取**最后出现的有效块**（避免草稿首块误采）；严格拒绝 `vote` 与 `status` 存在矛盾的票据（Fail-Closed）；适配器 prompt 全量注入 `review_round`、`diff` 及有效投票指令；
    - **P1-R-5 / P2-R3 闭环（三值投票与 Schema 完备性）**：`review_manifest.schema.json`（src 与 docs）及 `types.py` 同步支持 `ABSTAIN` 票与 `ABSTAINED` 状态，`allOf` 约束严格闭环；
    - **P2-R-1 / P2-2 闭环（.gitignore 存量升级）**：`wizard.py` 重构为逐条检查缺失规则并幂等追加 9 条隔离规则，单测覆盖存量升级；
    - **P2-R-5 / P2-3 闭环（多数票仲裁计算）**：`generate_smart_config` 修正 `min_effective_votes` 为 `math.ceil(2 * len(reviewers) / 3)`；
    - **P1-5 / P1-6 / P2-4 / 洁净度闭环**：`macao setup` 增加已有配置文件备份保护；`README.md` 徽章对齐为 `L3 SCENARIO-VERIFIED / PG-2` 与 `81/81 PASS`；`FAQ.md` 修正 `e2e-run` 为 `live-run` 并对齐两级自愈表述；`UC1-init-gemini.md` 尾随空格已清除，`git diff --check` 0 警告（Exit Code 0）。
  - **测试机验结果**：`PYTHONPATH=src python3 -m unittest discover tests -v` **81 ran / 81 PASS (100%)**；`macao live-run` 7 步全绿（Dispatcher 物理 Worktree 隔离派发 + 5 份产物 PERSISTED + 状态 DONE）；`python3 -m compileall -q src tests` 100% 洁净。
- **历史文档定级**：PRD **v2.3.1**（达到 L1 DOC-ALIGNED / PG-0）

---

## 评审申请记录全量对账表 (Review Registry - 82 份历史与当前评审报告 + 17 份申请全量对账)

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

---

## 下一步行动

专家委员会（Claude / Qwen / GLM / Grok / ZCode / Codex）对最新 Commit 开展 **Phase 3（PG-3 / L4 RELEASE-READY）终审验收**。
