# PRD 修改提案 v2.5 评审结论

- **评审日期**：2026-09-01
- **评审对象**：`docs/PRD_CHANGE_PROPOSAL_v2.5.md`（DRAFT，commit `0042dc3`）
- **评审人**：grok
- **评审范围**：提案全文 vs 权威基线 `docs/MACAO_PRD_v2.md` v2.3.1、`docs/usercases/PRODUCT-FACTS.md` F-1～F-16、FAQ Q13–Q15、UC-1 h0 / UC-5 / UC-6、现行 `ConsensusEngine`
- **定级**：本文件是**设计变更提案**，申请的是「可否升格为 PRD v2.5 编码基线」（L1 / PG-0），不是 L4
- **机器票**：`NO_APPROVE`
- **证据**：`BLOCKING` × 2，`ADVISORY` × 若干

**结论：方向正确，不能作为 v2.5 编码基线。** P-1～P-4 与「编排器零语义创作、内容/控制分层、机器裁决与处置分离」与已裁定事实同向；但提案内部有两处会迫使编排器做内容判断或无法唯一推出转移，且与 F-13/F-16/独裁帽/§5.2 的冲突未写成可执行修订。关闭下方 P0 并处理标为进入编码前必改的 P1 后，可再评 L1。

---

## 一、已确认（不阻塞，但实现时必须保持）

| # | 声明 | 判定 | 证据 |
|---|---|---|---|
| C1 | 编排器不得写申请/结论/采纳、不得语义合并问题 | VERIFIED | 提案 §2 P-1；对齐 F-10/F-11/F-12、FAQ Q13 |
| C2 | `YES_APPROVE` 不得表示「有条件通过」；条件修复 = `NO_APPROVE + BLOCKING` | VERIFIED | 提案 §3.1；消除现行文字/FSM 二义性 |
| C3 | `issues_index` 原样复制、不出现采纳字段 | VERIFIED | 提案 §3.4；对齐 F-5、UC-5 c2 |
| C4 | agmsg/AEP 只放引用；超限拒绝发送、禁止静默截断；路径越界失败关闭 | VERIFIED | 提案 §4.3；对齐 F-8/F-14 |
| C5 | 权重是管理员静态政策，运行时不按文笔/条数改 | VERIFIED | 提案 §6.1；对齐 F-16 |
| C6 | 单一任务 FSM；角色态只读投影，不引入第十一态 `REVIEWING` | VERIFIED | 提案 §5.4；对齐 F-4 |
| C7 | `--yes` 不得在歧义态替管理员选择；AI 诊断不得写 State Store | VERIFIED | 提案 §5.3；对齐 F-6/F-12 |
| C8 | 迁移期同一 round 不得混用等权/加权、内联/引用 context；先 Schema 后切默认 | VERIFIED | 提案 §9.2 |
| C9 | YAML/JSON 示例可解析 | VERIFIED（SIM） | 工作区对 3 个 yaml + 1 个 json 围栏 `yaml.safe_load` / `json.loads` 均 OK |

---

## 二、P0：BLOCKING（不关闭则不得 ACCEPTED）

### P0-1　E4c 的「需要改变代码」是语义判断，违反本提案自己的 P-1

- **证据**：提案 L91、L94：`ADVISORY` 处置「不改代码则进入 `MERGING`；需要立即改码则经新增 E4c 进入 `REWORK`」；「若标记为 `ADOPTED_NOW` **并需要改变代码**」。
- **矛盾**：P-1（L38–44）禁止编排器「判断两条自然语言意见是否是同一个问题」和「决定某条意见是否采纳」。是否改码同样是内容判断。YAML 示例（L119–123）只有 `decision: ADOPTED_NOW | BACKLOG | REJECTED | NEEDS_ADMIN`，**没有**机器可校验的 `requires_new_checkpoint`（或等价布尔）。
- **不可唯一推出的输入**：
  - `ADOPTED_NOW` 但理由是「文档里已经写了，保持现状」→ MERGING 还是 E4c？
  - `ADOPTED_NOW` 只改 `docs/` 非业务文件 → 是否算「新业务 commit」、是否破坏 checkpoint 不变式？
- **修正（择一，必须写进 Schema 与 §3.3）**：
  1. `ADOPTED_NOW` **一律** E4c（需要新 checkpoint + 新 round）；不改码的采纳改用 `ACKNOWLEDGED` / `ADOPTED_NOCHANGE`；或
  2. 处置项增加 Executor 填写的 `requires_new_checkpoint: boolean`，编排器只读该布尔，禁止从 `reason` 推断。
- **验收**：fixture 仅含 `ADOPTED_NOW`、无布尔字段时，实现不得自行进入 E4c 或 MERGING；必须 fail-closed。

### P0-2　`BACKLOG` +「已创建的后续 task」与单一任务 FSM 互斥

- **证据**：提案 L129：`BACKLOG` 必须关联已创建的后续 task，或管理员豁免；§10 第 6 项默认编排器不创建 task（对齐 F-9）。PRD §3.3 / §11.4 与 F-4：库内只有一个权威 `tasks.state`。
- **矛盾**：`APPROVED + ADVISORY` 时任务停在 `CONSENSUS_CHECK` HOLD。此时无法再 `task create` 出第二条活跃任务，除非：
  - 放开多任务并发（提案未改 FSM）；或
  - 允许引用**尚不存在**的 task id（与「已创建」字面冲突）；或
  - 实际路径几乎总是「管理员豁免」，则「必须关联 task」变成死文。
- **修正（须三选一并写转移表）**：
  1. `BACKLOG` 只要求 `reason` + 可选 `followup_task_id`（格式合法即可，不查库）；合并完成后由人开后续任务；或
  2. 明确支持「当前任务 DONE 之前登记 deferred_task 草稿」，草稿不是第二套 FSM；或
  3. 取消 `BACKLOG` 对 task id 的硬门禁，只保留管理员豁免/备注。
- **验收**：单任务仓库、`CONSENSUS_CHECK` HOLD、disposition 全 `BACKLOG` 且无第二任务时，行为可从条文唯一推出（通过 / 拒绝 / 问管理员），不得实现期现场发明。

---

## 三、P1：进入编码 / 回写 PRD 前应修正

### P1-1　独立 `review_disposition` 与已裁定 F-13/F-16 直接冲突，不能只标 PENDING-SPEC

- **证据**：
  - 提案 P-3、§3.3：`vote_result` 单一写者 = Orchestrator；采纳只在独立 disposition。
  - `PRODUCT-FACTS.md` F-13：「把…是否采纳**写入 `vote_result`**」；F-16：「执行者**在汇总段**标明」；第三节裁定：「筛选意见、总结采纳发生在 `REWORK`，由执行者写入 `vote_result` 汇总段」。
  - UC-1 h0(2)、FAQ Q15、UC-6 b：四段式 `vote_result`，`issues_summary` 在同一文件。
- **评价**：独立 YAML 在工程上优于双写者（哈希冻结、防改 `decision`），**可以作为管理员新裁定**。但 §11 只把 FACTS 标 `ACCEPTED-PENDING-SPEC`，没有给出 F-13/F-16/第三节的替换陈述句。实现者会同时看见「写入 vote_result」和「不得写入 vote_result」。
- **修正**：§10 第 2 项获批后，立刻改写 F-13/F-16/第三节/Q15/UC-5/UC-6 的写者与载体；废止 `issues_summary` 双写方案，而不是与之并存。

### P1-2　§6.1 示例权重 2:1（N=2）与 FAQ 独裁帽冲突，且在 `minimum_winning_seats=2` 下权重无效

- **证据**：提案 L307–313 示例 `codex:2, kimi:1`。FAQ Q15 / UC-1 h0(3)：**独裁帽**「任一席位权重 / 总权重必须 < 2/3，否则拒绝启动」→ `2/3` 不小于 `2/3`，该配置会被拒绝。
- **SIM**（按提案 §6.2 整数公式 + `minimum_winning_seats=2`）：N=2 且 2:1 时，双方 YES→APPROVED，分裂→DEADLOCK，一人弃权→席位法定人数失败。与等权 N=2 **结果集相同**，多出来的权重不改变任何决策。
- **修正**：
  1. 正文写明：加权规则 **取代** 还是 **叠加** 独裁帽（建议：N≥3 保留独裁帽作配置期门禁，`minimum_winning_seats` 作运行期防支配；二者同时写进 `policy_snapshot`）。
  2. 示例改为 N=3、`2:1:1`（独裁帽允许：`2/4=0.5<2/3`；权重真正起作用：高权重+一票 YES、一票 NO → APPROVED）。
  3. `minimum_winning_seats` 定义为 `min(配置值, N)`，并声明 PRD 既有 `N≥2`；§9.3 第 8 项「单席位达到权重阈值」写清是「N≥3 时一席权重触及阈值」而非 N=1 配置。
  4. 计票用整数：`3 * approve_weight >= 2 * effective_weight`，禁止 `float >= 2/3`。

### P1-3　`CONSENSUS_CHECK` HOLD 等待 disposition 缺少产物边、超时和 AEP 类型

- **证据**：提案 §3.2 给了 HOLD 语义；§8.1 说 §6 增加「处置缺失」接管。现行 AEP 仅 7 类（PRD §2.4 / `AEPType`），无 `DISPOSITION_REQUIRED`。§6.1 对 Deadlock 有 10 分钟承诺，对本 HOLD **无时限、无催促、无过期动作**。
- **历史同类缺陷**：Deadlock「票已齐但转移边缺失」曾阻断 L1（`docs/reviews/2026-08-26-review-result-cc77a94-claude.md`）。本处同构：决策已是 `APPROVED`，但 E4 被新守卫挡住，入口/出口不完整。
- **修正**：§3.3 增行：E3 后若 `requires_disposition` 则 ping 执行者（新 Type 或复用现 Type 并写 payload 契约）+ 时限 + 超时 → HOLD/告警/E7，禁止静默 MERGING。E6 同步增加「本轮 BLOCKING 必须已覆盖」守卫（§8.1 目前只写了 E4/E4c）。

### P1-4　管理员豁免 BLOCKING、以及 `NEEDS_ADMIN` 未接入转移表

- **证据**：§3.1「合并前必须修复**或由管理员显式豁免**」；YAML 枚举含 `NEEDS_ADMIN`。E7 现行四选项仍是 `APPROVED | REWORK | RETRY_REVIEW | CANCEL`（PRD §3.3），无 `EXEMPT_ISSUE` / 按 issue 豁免。
- **修正**：要么删除「豁免」与 `NEEDS_ADMIN`，要么给 E7 增加 issue 级选项，并规定豁免记录进 `docs/reviews/` + 审计，不回写 `vote_result.decision`。

### P1-5　`review_context` 示例被当成完整契约时，会丢掉现行 §5.2 语义块

- **证据**：提案 §4.2 示例顶层仅 `repository / checkpoint / evidence / review_request / dev_manifest`。权威 §5.2 另有 `task_info`、`code_changes`、`quality_snapshot`、`executor_self_assessment`、`history`、`references`（PRD L983–1059）。返工轮还需要上轮 `vote_result` / disposition / 申请全文。
- **评价**：改成「定位信息集合」是对的（长文外置）。但「必须完整提供 Reviewer 获取全部上下文所需的定位信息」未给出**必填引用清单**。实现者会按示例少传 GUIDELINES、上轮证据、质量信封。
- **修正**：用一张表把现行 §5.2 每一块映射为 `path+commit+sha256` 或「Reviewer 在指定 worktree 自行 `git diff`」。明确：语义正文进 Git 对象，context 只留定位符；示例加 `required:` 列表，避免子集被当成全集。

### P1-6　evidence ref 的读路径、fetch、合并后可见性未闭合

- **证据**：§4.4 正确指出：评审文件若提交到 source branch 会改变待合并 HEAD。但未规定：
  1. Reviewer 如何把 `.review.yml` + markdown **交到** Orchestrator（worktree 钉在 `checkpoint_ref`，不能在该 worktree 提交）；现行 §5.3 是 `macao send-message REVIEW_RESPONSE --review-file`，须写明收集后写入 evidence ref 的字节原样约束；
  2. `git clone` 默认不拉 `refs/macao/evidence/*` 的 fetch refspec、远程 push 失败时与 E4a 的关系（source 已合、evidence 未推 → 三层审计断）；
  3. 任务 `DONE` 后 `docs/reviews/` 是否合入主分支（人在 `main` 上能否看到申请/结论）。§7 把语义留痕放在 evidence ref，主线历史可能空白。
- **修正**：补「投递 → Orchestrator 提交 evidence ref → 归档 →（可选）DONE 后 docs 快照合入」时序；State Store 记 `evidence_commit`；远程双 ref 校验失败 fail-closed，不得只推 source。

### P1-7　`.macao/review_disposition.yml` 路径无 round，与现行归档模型冲突

- **证据**：提案 L101 固定文件名；PRD §3.4 归档是「复制到 `.macao/archive/<ref>/r<round>/` 后删除原位置」。多轮会覆盖未归档文件，或第二轮读到第一轮 disposition。
- **修正**：与 `.reviews/*.review.yml` 对齐，例如 `.macao/.reviews/r<round>.disposition.yml`，消费后按既有 archive 行追加语义归档。

### P1-8　`requires_disposition` / 覆盖范围在 REWORK 与 APPROVED 上不一致

- **证据**：L128：REWORK 必须覆盖全部 **BLOCKING**；`APPROVED + ADVISORY` 合并前覆盖全部 advisory。未规定：`REWORK_REQUIRED` 票面上同时存在其他专家的 ADVISORY 时是否必须处置；`NO_APPROVE` 但 issues 全是 ADVISORY 是否合法。
- **修正**：Schema `allOf`：存在 `BLOCKING` ⇒ `vote=NO_APPROVE`；`YES_APPROVE` ⇒ 不得含 `BLOCKING`。覆盖规则改成「本轮 `issues_index` 每一条在离开 `CONSENSUS_CHECK`/`REWORK` 前都有 disposition」，避免两条门禁。

### P1-9　§6.2 三个「2/3」未分开命名；weight_quorum 用配置总重 W 会导致高权超时后全体同意仍 Deadlock

- **SIM**：N=3、权重 `2,1,1`，高权 `ABSTAIN`、两低权均 `YES` → `weight_quorum`：有效权重 2 < `ceil(2W/3)=3` → **DEADLOCK**。这是条文可推出的，但 `policy_snapshot.threshold: "2/3"`（L148）看不出是席位法定、权重法定还是胜方占比。
- **修正**：快照分别记录 `seat_quorum`、`weight_quorum`、`decision_threshold`；§9.3 决策表必须包含「高权弃权 + 其余全赞成」这一行，并作为管理员已知行为（接受或改为分母用 effective W）。

---

## 四、P2 / P3（可延期，须登记）

| ID | 级 | 问题 |
|---|---|---|
| P2-1 | P2 | `init --new/--adopt-existing/--repair` 与 UC-1、UC-10 `doctor`、内部 `reconcile` 的命令面未画边界；§10 第 5 项应在回写 PRD 前定案 |
| P2-2 | P2 | 处置枚举 `ADOPTED_NOW/BACKLOG` 与 UC-6 `ADOPTED/DEFERRED` 词汇分裂，回写时统一 |
| P2-3 | P2 | P-1 允许「排序结构化字段」，UC-5 禁止对 `issues_index` 排序去重；须冻结拼接顺序（按 reviewer 配置序 × 原信封序）以免 JSON 哈希漂移 |
| P2-4 | P2 | §3.4 `vote_result` 示例缺 `votes`/`checkpoint_ref`/`version`，不能当 Schema 全集；回写 PRD 时用完整合法 JSON |
| P2-5 | P2 | 「可选 AI 诊断」须写明为编排器进程外 sidecar，避免 F-12 被读成「init 已接入模型」 |
| P2-6 | P2 | AEP 16KiB / 字段 2KiB 无实测；保持「PoC 后可调、收发同一版本化配置」即可，不要写进代码魔法数而不进 config |
| P3-1 | P3 | PRODUCT-FACTS F-5 悬空「见 F-8b」（既有瑕疵，非本提案引入） |
| P3-2 | P3 | 提案目标基线写「v2.3.1～v2.4」，权威文件标题仍是 v2.3.1；回写时一次升到 v2.5 并改文首版本 |

---

## 五、加权公式场景推演（SIM，非 TEST）

按 §6.2：`ceil(2N/3)` 席位法定、`ceil(2W/3)` 权重法定（分母为**配置总重 W**）、胜方占比整数 2/3、`minimum_winning_seats=2`。

| 配置 | 票面 | 结果 | 说明 |
|---|---|---|---|
| N=2 等权 | 2 YES | APPROVED | 与现行决策表一致 |
| N=2 等权 | 1:1 | DEADLOCK | 同现行 |
| N=2 权重 2:1 | 高 YES、低 NO | DEADLOCK | `min_win_seats` 生效；但该配置被现行独裁帽拒绝 |
| N=3 权重 2:1:1 | 高+一 YES、一 NO | APPROVED | 权重真正起作用的最小有意义例 |
| N=3 权重 2:1:1 | 高 ABSTAIN、两 YES | DEADLOCK | 权重法定 2<3；须在决策表公示 |
| N=1 权重 1 | YES | DEADLOCK | `min_win=2`；若坚持 PRD `N≥2` 则从验收场景删除 N=1 |

---

## 六、建议闭环顺序

1. **关闭 P0-1、P0-2**：E4c 布尔化或枚举切开；`BACKLOG` 与单任务 FSM 对齐。
2. **管理员当场裁定 §10 全部 6 项**，尤其第 1、2、6 项；裁定后改写 F-13/F-16/第三节（P1-1），不要留双真源。
3. **补 §3.3**：disposition HOLD 的 ping/超时/E7；BLOCKING 豁免；E6 覆盖守卫；disposition 路径带 round（P1-3/4/7/8）。
4. **重写 §6 示例与快照字段**；明确独裁帽与 `minimum_winning_seats` 关系；补整数公式与「高权弃权」行（P1-2/P1-9）。
5. **列完 review_context 必填引用**；补 evidence ref 投递/fetch/DONE 后可见性（P1-5/P1-6）。
6. 再评 L1：通过后按提案 §9.2 顺序改 Schema/代码；期间 v2.3.1 行为不变。

**本轮不建议**：把提案原文直接贴进 `MACAO_PRD_v2.md`，或把 PRODUCT-FACTS 标成 ACCEPTED 而不改陈述句。

---

## 七、Reviewer 自审

- 对照 GUIDELINES §9：P0/P1 均附路径+行号或 SIM 表；未把「方向正确」当成 L1。
- 未跑现有 84 测：对象是 DRAFT 提案，CODE/TEST 为 NOT_APPLICABLE。
- 加权 SIM 为本地按条文手写的确定性函数，不是仓库内测试；实现后须变成 §9.3 第 8 项的正式决策表测试。
