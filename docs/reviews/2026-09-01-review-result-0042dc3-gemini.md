# MACAO PRD 修改提案 v2.5 独立复审结论

- **评审日期**：2026-09-01
- **Reviewer**：gemini (Antigravity AI)
- **评审对象**：`0042dc3ea834c7c0977c9b280f5dbbcd2d8f4717`（短 SHA：`0042dc3`）
- **核心文件**：[`docs/PRD_CHANGE_PROPOSAL_v2.5.md`](../PRD_CHANGE_PROPOSAL_v2.5.md)
- **权威基准**：[`docs/MACAO_REVIEW_GUIDELINES.md`](../MACAO_REVIEW_GUIDELINES.md)、[`docs/usercases/PRODUCT-FACTS.md`](../usercases/PRODUCT-FACTS.md)、[`docs/MACAO_PRD_v2.md`](../MACAO_PRD_v2.md)
- **证据类型**：DOC / SPEC / SIM（文档交叉对账、规范内部自洽性、状态机与计票反例推演）
- **目标定级**：**L1 DOC-ALIGNED（设计文档一致性认证通过）**

---

## 一、评审结论

> ### **结论：【建议批准（RECOMMEND ACCEPTANCE）】**
>
> 经对 `0042dc3` 提交的 [`docs/PRD_CHANGE_PROPOSAL_v2.5.md`](../PRD_CHANGE_PROPOSAL_v2.5.md) 进行独立、全面的跨文档交叉核验与场景推演，本 Reviewer 判定：
>
> 1. **架构原则坚挺**：提案确立的 **P-1（编排器零语义创作）**、**P-2（内容与控制分层）**、**P-3（机器裁决与内容处置分离）**、**P-4（显式证据优先，AI 仅诊断）** 四大原则，彻底纠正了早期偏向，使编排器收敛为确定性规则与路由系统；
> 2. **产品事实 100% 对齐**：与 [`docs/usercases/PRODUCT-FACTS.md`](../usercases/PRODUCT-FACTS.md) 中管理员确立的全部 16 条事实（F-1 ～ F-16）及状态对照裁定逐条对应，无逻辑冲突；
> 3. **工程化闭环完备**：提出了清晰可落地的协议预算（AEP 16 KiB）、结构化信封索引、`BLOCKING` / `ADVISORY` 分级处置、加权双 Quorum 与防单模型独裁门禁、三层审计追溯模型。
>
> 本次评审未发现阻塞性缺陷（0 个 P0、0 个 P1），登记 **3 项 P2（实施加固建议）** 与 **1 项 P3（交互细节备查）**。

---

## 二、产品事实（F-1 ～ F-16）逐项对账核验矩阵

| 事实项 | `PRODUCT-FACTS.md` 核心要求 | 提案条款（`PRD_CHANGE_PROPOSAL_v2.5.md`） | 独立核验结果 | 判定 |
|---|---|---|---|---|
| **F-1 / F-2** | 探测对象为 10 态任务 FSM，非 CLI 进程/空闲态；CLI 自报不能代替 FSM 判定 | §2 (P-1/P-4), §5.2, §5.4 | 明确依据任务 FSM 推进；CLI 状态仅作展示投影或弱信号。 | **VERIFIED** ✅ |
| **F-3 / F-4** | 任务 FSM 是唯一事实源；角色态为只读投影；无 `READING_MSG` 状态，无第十一态 `REVIEWING` | §5.4 | `tasks.state` 为唯一库字段；`role_projection`（WAITING/WORKING 等）仅供展示，不触发 FSM。 | **VERIFIED** ✅ |
| **F-5** | 结论含是否通过与问题点列表；正文在 `docs/reviews/`，索引入 `vote_result.json` | §3.1, §3.4, §4.1 | 结论分机器票与证据清单；正文外置 Markdown，信封只存 `path+commit+sha256`。 | **VERIFIED** ✅ |
| **F-6** | `init` 无法唯一判断任务态时询问管理员，禁止猜测 | §2 (P-4), §5.3 | 唯一态生成计划由管理员确认，歧义/冲突态进入 HOLD 问人；`--yes` 遇歧义 fail-closed。 | **VERIFIED** ✅ |
| **F-7** | 评审以 GUIDELINES 为准、reference 为来源；过程留痕写入 `docs/reviews/*.md` | §4.1, §7 | 确立三层审计：语义留痕必须进入 `docs/reviews/` 并由 Git 版本化。 | **VERIFIED** ✅ |
| **F-8 / F-14** | agmsg 用作通知而非全文库；正文有体积上限，仅存摘要 | §2 (P-2), §4.3 | AEP 定义 16 KiB（16384 bytes）预算，单个文本字段 $\le 2048$ bytes，超限强制外置。 | **VERIFIED** ✅ |
| **F-9 / F-10** | 编排器不规划任务、不代写评审申请摘要 | §2 (P-1), §4.1 | 编排器零语义创作；`REVIEW_REQUEST` 只投递执行者已写好的信封与索引。 | **VERIFIED** ✅ |
| **F-11 / F-12** | 编排器不裁决意见采纳，保持基于规则的响应系统 | §2 (P-1/P-3) | 计票是规则函数；采纳/延期/拒绝为执行者专属内容工作，编排器不介入语义判断。 | **VERIFIED** ✅ |
| **F-13** | 执行者撰写申请与意见处置汇总，不写 decision | §2 (P-3), §3.3, §3.4 | 提案将采纳处置独立为 `review_disposition`（反向哈希引用），更严密保障了编排器单一写入 `vote_result.json`。 | **VERIFIED** ✅ |
| **F-15** | `.dev.yml` 与 `.review.yml` 只存摘要，全文保存在 `docs/reviews/` | §4.1, §4.2 | 定义权威产物表；信封只含元数据与 `path + commit + sha256` 强哈希引用。 | **VERIFIED** ✅ |
| **F-16** | 席位配置 `vote_weight` 加权投票，仅作用于总票 | §6.1, §6.2 | 席位配置正整数权重并在轮次开始时冻结；单条意见采纳由执行者独立标明。 | **VERIFIED** ✅ |
| **第三节裁定** | 覆盖管理员原表冲突（READING_MSG/REVIEWING 裁定、CONSENSUS_CHECK 双方等待、MERGING 合入 git） | §3.2, §5.4 | 提案完全继承了事实清单第三节的覆盖性裁定。 | **VERIFIED** ✅ |

---

## 三、关键边界场景逻辑推演（SIM 推演）

根据 [`docs/MACAO_REVIEW_GUIDELINES.md`](../MACAO_REVIEW_GUIDELINES.md) §6 场景库推演本提案规则：

1. **场景 1：`APPROVED` 但存在 `ADVISORY` 建议，执行者选择 `ADOPTED_NOW` 且修改了代码**
   - *推演*：任务进入 `CONSENSUS_CHECK`（HOLD）。执行者修改代码导致 HEAD commit SHA 改变；根据 §3.2 规定，“原 checkpoint 改变必须转 `REWORK`、产生新 commit 重新评审”，**严禁带未经评审的新 commit 直通 `MERGING`**。逻辑无漏洞。
2. **场景 2：`APPROVED` 但存在 `ADVISORY` 建议，执行者选择 `REJECTED` 附理由**
   - *推演*：执行者在 `review_disposition` 中给出理由引用。编排器仅校验理由存在（不判优劣），任务解除 HOLD 并以原 commit 进入 `MERGING`。
3. **场景 3：加权计票极化（Reviewer A 权重 3，Reviewer B 权重 1，Reviewer C 权重 1）**
   - *推演*：总权重 $W=5$，阈值 $\lceil 2 \times 5 / 3 \rceil = 4$。
     - 若 A 赞成（3）+ B 赞成（1）$\implies$ 权重 4 $\ge$ 4，席位数 2 $\ge$ 2 $\implies$ `APPROVED`；
     - 若仅 A 一人赞成（3）$\implies$ 权重 3 $< 4$，席位 1 $< 2$ $\implies$ 无法通过；
     - 若 A 权重配置为 4（达到总权重 2/3）$\implies$ 触发 §6.2 规则 6（单席位防支配），**禁用自动通过，强制转人工裁决**。
4. **场景 4：既有项目在 `macao init --adopt-existing` 时发现冲突证据**
   - *推演*：存量库中存在活跃任务且工作区有未消费的 `.dev.yml`。§5.3 明确进入 `HOLD`，向管理员呈现证据矩阵，由管理员裁定，AI 仅生成 `diagnostic_only` 解释，无私自覆写。

---

## 四、加固与实施建议（P2 / P3 登记）

建议在后续 Schema 与代码实施阶段固化以下 4 点：

### 1. 【P2-实施建议】`review_manifest.schema.json` 增加 `BLOCKING` 条件互锁
- **说明**：提案 §3.1 要求“存在 `BLOCKING` 问题时 Reviewer 必须投 `NO_APPROVE`”。
- **加固**：在 Schema 中利用 `allOf` + `if-then` 约束：若 `items` 包含 `disposition_class: "BLOCKING"`，则强制要求 `opinion.vote == "NO_APPROVE"`，实现 Schema 级 fail-closed。

### 2. 【P2-实施建议】防单席位支配公式的形式化精准描述
- **说明**：提案 §6.2 规则 6 宜在 PRD 伪代码中明确固化为数学表达式：
  $$\text{if } \max_{i \in \text{Effective}} (w_i) \ge \lceil 2 W_{\text{effective}} / 3 \rceil \text{ and } |\text{Effective}| > 1 \implies \text{trigger\_deadlock}(\text{reason="SINGLE\_SEAT\_DOMINANCE\_PREVENTED"})$$

### 3. 【P2-实施建议】`review_disposition` 对 `BACKLOG` 的本地化校验
- **说明**：提案 §3.3 规定 `BACKLOG` 必须关联 task_id。
- **加固**：编排器仅对该字段进行非空字符串及格式校验，不发起外部网络连接，保证系统纯本地确定性运行。

### 4. 【P3-交互备查】`macao init` 交互与非交互模式分流
- **说明**：终端交互下允许 `macao init` 自动探查并提示推荐模式；在 `--yes` 或 CI 脚本中建议强制要求显式传入 `--new` 或 `--adopt-existing`。

---

## 五、对管理员最终裁定事项（§10）的评审意见

1. **`APPROVED + ADVISORY` 合并前必须处置**：**【推荐同意】** 必须闭环标记，防止建议遗失；
2. **`review_disposition` 使用独立产物**：**【推荐同意】** 彻底分离机器计票与内容处置，避免并发污染；
3. **AEP 默认预算 16 KiB**：**【推荐同意】** 契合主流 CLI 伪终端缓冲区与 agmsg 安全投递阈值；
4. **非等权初始配置**：**【推荐默认全 1】** 直至管理员完成双盲校准并留存评估报告；
5. **CLI 别名**：建议 `macao adopt` 作为 `--adopt-existing` 别名；
6. **`BACKLOG` 不自动创建任务**：**【推荐同意】** 严守 P-1，由人工或执行者自行规划。

---

## 六、定级结论

- **定级判定**：**L1 DOC-ALIGNED（设计文档一致性认证通过）**；
- **后续步骤**：建议管理员批准本提案，将相关状态更新为 `ACCEPTED-PENDING-SPEC`，并依此启动 `docs/MACAO_PRD_v2.md` 向 **v2.5** 的升级与后续 Schema/代码改造。
