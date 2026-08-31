# PRD 修改提案 v2.5（DRAFT v0.2）评审结论

- **评审日期**：2026-09-01
- **评审对象**：`docs/PRD_CHANGE_PROPOSAL_v2.5.md` DRAFT v0.2（工作区未提交版本，事实基线 `99fe377`；上一轮 DRAFT 为 commit `0042dc3`）
- **评审人**：kimi（独立评审）
- **对齐基准**：`docs/MACAO_PRD_v2.md`（现行 10 态 FSM / §2.2–2.4 / §3.3 / §5.2 / §6.1 / §11 / §14 / §16）、`docs/usercases/PRODUCT-FACTS.md` F-1～F-22（`99fe377`）、UC-1/UC-4/UC-5/UC-6、FAQ Q15、三份上轮评审（`2026-09-01-review-result-0042dc3-{gemini,glm,grok}.md`）
- **证据类型**：DOC / SPEC / SIM（跨文档交叉对账、整数公式逐行重算、状态机路径推演、代码块机解析）
- **机器票**：`NO_APPROVE`（`BLOCKING` × 1）
- **结论**：**REQUEST CHANGES（不建议原样批准）**。三份上轮评审的 P0/P1 已逐条实质闭环，架构方向（P-1～P-4、独立 disposition、evidence ref、五门禁加权）稳固；但存在 **1 项 P0**（E7「REWORK_REQUIRED→APPROVED」覆盖路径在 FSM 上无落位，内部矛盾）与 **3 项 P1**（E3 触发条件变更未迁移、DEADLOCK/override 与不可变 vote_result 的叠加契约缺失、NEEDS_ADMIN 的 issue 级回执通道未定义）。P0/P1 修订后可再评 L1。

---

## 一、已确认项（VERIFIED，实现时必须保持）

| # | 声明 | 判定依据 |
|---|---|---|
| V1 | 上轮 grok P0-1（语义推断改码）→ D-5 + §4.3 强制规则 3：`requires_new_checkpoint` 必填布尔、缺失失败关闭 | VERIFIED |
| V2 | 上轮 grok P0-2（BACKLOG 与单任务 FSM 互斥）→ D-4：`DEFERRED`、followup_task_id 可选不查库、DONE 后创建 | VERIFIED |
| V3 | 上轮 glm P0-1（未显式推翻 F-13/F-16）→ 事实基线已演进为 `99fe377`（F-13/F-16 不再含「汇总段」表述），D-2 正是 F-20 待定项要求的显式裁定，§9.2 列出 FAQ Q15/UC-1/UC-5/UC-6 废止迁移 | VERIFIED |
| V4 | 上轮 glm P1-1（显式 ABSTAIN 与已实现冲突）→ D-3 + §9.2（UC-4/Schema/代码保留显式弃权，区分 timeout 来源） | VERIFIED |
| V5 | 上轮 glm P1-2（遗漏 git 提交迁移点）→ §9.1 覆盖 L416/L833/L859/L1510 并有全量检索 catch-all；四处行号已逐一核对原文属实 | VERIFIED |
| V6 | 上轮 grok P1-3（HOLD 无协议边）→ §4.4 新增 `DISPOSITION_REQUIRED` + deadline/ping/超时升级 | VERIFIED |
| V7 | 上轮 grok P1-5/P1-6 → §5.2 九语义块逐项映射表（含首轮/后续轮）与 §5.4 投递/promotion/fetch/push/可见性闭环 | VERIFIED |
| V8 | 上轮 grok P1-8（覆盖范围不一致、NO_APPROVE 全 ADVISORY 合法性）→ §4.1 Schema 条件约束四条 + 强制规则 1 全 issue 精确覆盖 | VERIFIED |
| V9 | 上轮 grok P1-2/P1-9（2:1 示例、三个 2/3 未分名）→ §7.1 示例改 N=3 `2:1:1`、§7.2 五门禁分名定义、§7.3 含高权弃权 DEADLOCK 行 | VERIFIED |
| V10 | 上轮 glm P2-2（第三套术语）→ §6.3 采用 UC-1 既有 `role_view` 为唯一规范名，表内容与 UC-1 h2 逐行一致，且覆盖全部 10 态（PRD L846） | VERIFIED |
| V11 | 上轮 glm P3-1（E4c 命名混淆）→ §4.5 改 E5a 并显式说明不复用 E4a/E4b 编号 | VERIFIED |
| V12 | §7.2 整数公式与 §7.3 决策表六行逐行重算一致（N=2 等权 YES→APPROVED；1:1→DEADLOCK；2:1:1 三类组合；1:1:1 一 timeout 两 NO→REWORK_REQUIRED）；配置期 `3*w_i < 2*W` 与 `max_single_weight_share_exclusive: 2/3` 等价 | VERIFIED（SIM） |
| V13 | §5.4.1 自引用禁令（blob 不内嵌包含自身的 commit ID）与 §4.3/§4.4 示例一致：`full_document` 只写 `path+sha256`，仅引用已冻结前序产物（vote_result）时才带 `evidence_commit` | VERIFIED |
| V14 | 全部 5 个 YAML/JSON 代码块经 `yaml.safe_load`/`json.loads` 机解析通过 | VERIFIED（SIM） |
| V15 | 与 PRODUCT-FACTS F-1～F-22 逐条对账无冲突；F-22（权重不取消席位法定、单席不独决）由 `minimum_winning_seats≥2` + 双 quorum 闭合 | VERIFIED |

## 二、P0：BLOCKING（不关闭不得 ACCEPTED）

### P0-1　E7「REWORK_REQUIRED → APPROVED」覆盖路径在 FSM 上无落位

- **证据（提案）**：
  - §4.2 表：`REWORK_REQUIRED` →「**立即进入 `REWORK`**」（无 HOLD 窗口）；HOLD 只列在「DEADLOCK、门禁失败或 NEEDS_ADMIN」一行。
  - §4.4：「E7 可选择 `APPROVED | REWORK | RETRY_REVIEW | CANCEL`。若从 `REWORK_REQUIRED` 覆盖成 `APPROVED`，E7 请求必须带 `exempt_issue_ids` 和 note…」。
  - §4.3：`EXEMPTED_BY_ADMIN`「仅在有效 E7 override 把 `REWORK_REQUIRED` 改为 `APPROVED` 时使用」。
  - §4.5：E7 源状态仅写「HOLD」；E4 源状态是 `CONSENSUS_CHECK`；全表无 `REWORK → MERGING` 边。
- **矛盾**：机器决策 `REWORK_REQUIRED` 后任务**立即**离开 `CONSENSUS_CHECK` 进入 `REWORK`（§4.4 超时条款亦确认「REWORK_REQUIRED 场景继续停在 REWORK」）。管理员要行使「覆盖成 APPROVED」时：(i) 没有任何定义的 HOLD 窗口可供介入——E5 是立即转移，管理员只能与机器转移竞速；(ii) 即使竞速成功或在 REWORK 中发起，E7 的源状态不含 `REWORK`，且不存在 `REWORK → MERGING` 的转移边，覆盖结果无路可走。
- **连带失效**：`EXEMPTED_BY_ADMIN` 枚举、`override_id` 生成契约、§10.3 验收场景 7（「E7 把拒绝覆盖为批准时，所有 `exempt_issue_ids` 都有 `EXEMPTED_BY_ADMIN + override_id`」）全部依赖这条无法落位的路径，实现者无法从条文唯一推出行为。
- **修正（三选一，必须写进 §4.2/§4.5 转移表）**：
  1. `REWORK_REQUIRED` 也在 `CONSENSUS_CHECK` 短暂 HOLD（等 disposition FINAL 或 override 窗口），E7 从该 HOLD 覆盖后走 E4；或
  2. E7 源状态显式包含 `REWORK`，并新增 `REWORK → MERGING` 边（守卫：FINAL disposition + 未修复 BLOCKING 全部 `EXEMPTED_BY_ADMIN + override_id`）；或
  3. 删除「REWORK_REQUIRED→APPROVED」覆盖选项（E7 仅覆盖 DEADLOCK/门禁类 HOLD），`EXEMPTED_BY_ADMIN` 改为仅适用于 DEADLOCK 覆盖场景。
- **验收**：按选定方案补状态转移行，并把 §10.3 场景 7 改写为可在转移表上逐步重放的步骤序列。

## 三、P1：进入编码 / 回写 PRD 前应修正

### P1-1　E3 触发条件从「达到 quorum 即转移」改为「全部席位 accounted」，未列入迁移清单

- **证据**：现行 PRD L833 E3 触发 =「有效票 ≥ minimum_quorum」；UC-5 P2 行同口径。提案 §4.5 E3 新守卫 =「所有席位已响应或已被持久化 timeout 机制纳入 accounted 集合」。
- **评价**：该变更方向**必要且正确**——加权规则下有效权重分母 `E_W` 取决于弃权集合，提前点火会让决策依赖消息到达顺序。但 §9.1 的 §3.3 行只列了 disposition HOLD/E5a/E6/E7 字段，未声明 E3 触发条件变更；§9.2 未列 UC-5 P2 / UC-9 注入口径的同步。旧文残留会让实现者面对两个互斥触发条件。
- **要求**：§9.1 §3.3 行增列「E3 触发改为全席位 accounted」；§9.2 增列 UC-5 P2 与 UC-9 的同步改写；§10.3 增加验收场景「达到 quorum 但仍有席位未响应且未 timeout 时不得 E3」。

### P1-2　DEADLOCK/门禁失败时 vote_result 是否落盘未裁定，与不可变性 + E7 覆盖的叠加契约缺失

- **证据**：现行 PRD L833/L834 与 UC-5 A3、UC-5 验收 1 均为「DEADLOCK **不写** `vote_result.json`，随 E7 终局一并落盘（`resolution: human_override`）」。提案 D-1 要求 vote_result 不可变、§4.6 示例含 `resolution: AUTO_WEIGHTED_CONSENSUS`；但 §4.2 的 DEADLOCK 行只写 HOLD + `HUMAN_OVERRIDE_REQUEST`，未写 vote_result 是否生成；§5.4.2 第 6 步「生成 vote result …才能触发决策转移」也未覆盖无转移的 DEADLOCK 情形。
- **矛盾点**：若 DEADLOCK 落盘（机器决策即记录），则 E7 覆盖后终局决策的权威来源需要定义（override 记录优先于 `vote_result.decision`？两者经 `override_id` 如何链接？`resolution` 枚举取值集合是什么？），且 UC-5「DEADLOCK 不落盘（断言文件不存在）」的验收断言必须迁移——§9 未列。若 DEADLOCK 不落盘（沿旧），则须说明它与 D-1「保存机器决策」的边界，以及与 P0-1 所选覆盖方案下 vote_result 写入时点的一致性。
- **要求**：显式裁定二选一；定义 `resolution` 枚举全集与 override 记录 artifact 的写者/载体/链接；§9.2 增列 UC-5 A3 与验收 1 的迁移行；§10.3 增加对应验收场景。

### P1-3　`NEEDS_ADMIN` 的管理员回执是 issue 级，而 HUMAN_OVERRIDE_REQUEST/E7 是任务路径级，回执通道未定义

- **证据**：§4.3 定义 `NEEDS_ADMIN` → `status=PENDING_ADMIN`、当前状态 HOLD；§4.2 表将其与 DEADLOCK 合并走 `HUMAN_OVERRIDE_REQUEST` → E7。但 E7 选项（`APPROVED | REWORK | RETRY_REVIEW | CANCEL`）是**任务路径级**；当机器决策已是 `APPROVED`、仅某条 issue 为 `NEEDS_ADMIN` 时，管理员选「APPROVED」并不能回答「这条意见采纳还是拒绝、是否需要新 checkpoint」。`EXEMPTED_BY_ADMIN` 又仅适用于 REWORK_REQUIRED→APPROVED 覆盖（且见 P0-1）。
- **缺口**：管理员对单条意见的决定以什么结构化字段回传（映射到 `ADOPTED/REJECTED/DEFERRED` 哪个枚举、`requires_new_checkpoint` 取值）、由谁写入更高 `artifact_revision`（§4.3 规则 5 只说「写新版本」）、回执如何审计，均未规定。
- **要求**：定义 issue 级管理员回执契约（建议：override resolve 增加按 issue 的结构化应答字段，产出审计事件，Executor 据此写新 revision；或管理员直接指定该 item 的 decision+布尔，Orchestrator 仅校验结构）。补对应验收场景。

## 四、P2：可延期，须登记

| ID | 问题 |
|---|---|
| P2-1 | REWORK 场景下 disposition 默认 30 分钟 deadline 与改码耗时的关系未定义：是先处置后改码，还是 disposition 与新 commit 一并到达？若后者，超时升级到 HUMAN_OVERRIDE_REQUEST 会在正常返工途中误报。建议写明时序预期，或拆分「处置超时」与「返工超时」两个配置。 |
| P2-2 | §9.1 catch-all 之外建议显式列出：PRD L862（「归档动作 = git 提交 → 复制到 archive → 删除原位置」）、L669（跨机 δ2「git 提交仍是存证」）、§16.4 C3 行（「M1 落盘并 git 提交留证」，约 L1643）；FAQ.md L116/L120 的超时 ABSTAIN 表述也需随 D-3 同步改写。 |
| P2-3 | §5.4.2 的「远程 push + `ls-remote` 验证」前置对纯本地单机部署（PRD 场景一，无 origin）的退化语义未写明；应给出本地模式的等价验证形式，否则单机实现无法通过该守卫。 |
| P2-4 | §6.3 role_view 表未携带 UC-1 h2 的 `artifact_status` 注记（`STALE` 不得显示为 `REVIEW_SUBMITTED`）；§9.2 称 UC-1 采用本提案唯一表，建议把该注记一并固化，避免回写后丢约束。 |

## 五、P3：备查

| ID | 问题 |
|---|---|
| P3-1 | §7.3 决策表建议补两行：N=2 一席弃权（DEADLOCK，席位 quorum 不足）；N=3 `2:1:1` 高权 YES + 一席 ABSTAIN + 一席 NO（`3*2 >= 2*3` 权重阈值恰满足但胜方席位=1 < 2 → DEADLOCK），直接固化「胜方最少席位」门禁语义。 |
| P3-2 | `policy_snapshot` 中比率字段为字符串（`max_single_weight_share_exclusive: "2/3"`）与整数对（`decision_threshold_numerator/denominator`）混排，建议统一整数对表示。 |

## 六、建议闭环顺序

1. **关闭 P0-1**：三选一裁定 E7 覆盖路径的状态落位，补转移边与验收步骤；
2. **P1-2 与 P0-1 联动裁定**：DEADLOCK/override 下 vote_result 的写入时点、不可变边界、`resolution` 枚举与 override 链接；
3. **P1-1 / P1-3**：E3 触发变更入迁移清单 + issue 级管理员回执契约；
4. P2/P3 随修订批处理；
5. 验收：修订版中 `grep -n "立即进入" / "EXEMPTED_BY_ADMIN"` 与新转移表一致；§9 清单与本评审 P1-1/P1-2/P2-2 点名位置逐条可对账；§10.3 增补场景 3 个（E3 等待、DEADLOCK 落盘、NEEDS_ADMIN 回执）。

## 七、Reviewer 自审

- P0/P1 均附提案节号与现行基线行号（PRD L833/L834/L840/L846/L862；UC-5 P2/A3/验收 1；UC-1 h2），可复现；
- 决策表核验为按提案 §7.2 条文手算的整数推演（SIM），非仓库内测试；YAML/JSON 机解析为本地只读校验；
- 未评审对象：代码、Schema 文件、真实执行（本提案为纯文档 DRAFT，CODE/TEST 为 NOT_APPLICABLE）。
