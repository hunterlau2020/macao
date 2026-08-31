# PRD v2.5 产品方案、技术设计同步与代码变更清单 评审结论（Design-Sync 定级复核）

- **评审日期**：2026-09-01
- **评审人**：kimi（独立评审）
- **被评审提交**：`0bc6247`（`docs: sync PRD v2.5 design, add code change inventory, and submit review request`； diff 基准 `99fe377`）
- **评审申请**：`docs/reviews/2026-09-01-review-request-PRD-v2.5-Design-Sync.md`
- **申请定级**：L1 DOC-ALIGNED / PG-0
- **对齐基准**：`docs/MACAO_PRD_v2.md`、`docs/PRD_CHANGE_PROPOSAL_v2.5.md`（DRAFT v0.3）、`docs/usercases/PRODUCT-FACTS.md` F-1～F-22、UC-1/UC-5/UC-6/UC-7/UC-8/UC-9、FAQ、SRSv1、`docs/schemas/`、本人上轮评审 `2026-09-01-review-result-PRD-v2.5-v0.2-kimi.md`
- **证据类型**：DOC / SPEC / SIM（跨文档交叉对账、git diff 全量比对、整数公式逐行重算、24 个 YAML/JSON 围栏块机解析、仓库模块树 `test -f` 级核对）
- **机器票**：`NO_APPROVE`（`BLOCKING` × 10：P0×1 + P1×9；`ADVISORY` × 13）

## 结论

**不授予 L1 DOC-ALIGNED / PG-0，不得据此进入 Phase 1～5 编码。**

架构方向（D-1～D-9、独立 `review_disposition`、加权纯整数五重门禁、Evidence Ref 隔离、`role_view` 投影）继续成立，§3.3 转移表、§2.2 三值票互锁、§14.2 投影、UC-5 计票主路径、FAQ Q15 已实质吸收上轮意见，本人上轮 P0/P1 的**提案侧**裁定（§4.2/§4.4/§4.5）均已落笔。

但申请所称「全量完成同步修改」「专家关切 100% 物理闭环」「状态机无歧义转移分支」**不成立**。核心问题不是设计缺失，而是**迁移执行不完整**：权威 PRD 内部至少三组互相否决的条文（§3.2 伪代码 / §3.3 转移表 / §3.4 场景三），两个规范章节（§14.5、第十五部分）被整体删除且留下 ≥7 处悬空引用，UC-7/UC-8/UC-9、`docs/schemas/` 机器契约、FAQ/PRODUCT-FACTS 多处仍为 v2.3.1/v2.4 口径，代码变更清单的目标路径与仓库实际模块树不符。两份针对本提交的独立评审（codex、grok）与本轮复核结论一致：本 commit 不能作为实施基线。

---

## 一、申请 §3 闭环核验表（逐条物理核验）

| 申请声称闭环项 | 本轮判定 | 证据要点 |
|---|---|---|
| **Kimi P0-1**（E7 覆盖与豁免机制） | **PARTIALLY_VERIFIED** | 已落位：PRD §3.3 E7 行（L797）源状态含 `HOLD(CONSENSUS_CHECK 或 REWORK)`、五选项、`exempt_issue_ids`+`override_id`+独立 `admin_override.json`；提案 §4.2 第 1/3/4 条定义豁免守卫与不可变性。未闭环：§3.2 Layer 1c 伪代码（L735-747）仍按旧四分支运转、无 DEADLOCK 分支、APPROVED 无 disposition 守卫；§3.4 场景三（L855-863）仍为旧语义；UC-7 全文未迁移（见 P0-1/P1-1） |
| **Kimi P1-1**（E3 全席位 accounted） | **PARTIALLY_VERIFIED** | 已落位：§3.3 E3 行（L789）+ 超时行（L790）、§1.2 阶段表（L145）、UC-5 主流程与异常流 E2（L74）。未闭环：§3.2 Layer 1b（L725）仍 `count_valid >= minimum_quorum` 提前触发；§1.1 流程图（L90）、§16.2 阶段 4（L1543）、UC-5 前置条件 P2（L16）、§6.1 Reviewer 超时条目（L1078-1082）仍为旧口径（见 P1-2） |
| **Kimi P1-2**（DEADLOCK 即时落盘不可变） | **CONTRADICTED** | 新语义已写进 D-1、§2.3（L366）、§3.3 E3 行、UC-5（L43/L54/L85）；但 §3.4 场景三明确写「**不写 vote_result.json**」并由裁定「落盘终局 vote_result」（L855-859），与上述条文正反命题同存一节；UC-7 L44/L80、`docs/schemas/vote_result.schema.json` L51/L88-92 同为旧口径（见 P1-1） |
| **Kimi P1-3**（NEEDS_ADMIN 答复闭环） | **PARTIALLY_VERIFIED** | 流程级定义存在于提案 §4.2 末行与 §4.4（L211）、PRD §2.4 表注（L383）与 §14.2（L1499）；但申请声称的落点「PRD §6.1 与 UC-6」**均不含**该定义：§6.1 触发器列表（L1070-1107）无 NEEDS_ADMIN 条目，UC-6 无 `PENDING_ADMIN`/`artifact_revision`/issue 级结构化应答契约（见 P1-4） |
| **Grok P1-1**（disposition 超时 30m） | **CONTRADICTED**（落点失实） | 提案 §4.4（L207）与 PRD §1.2 超时列（L145，30m）已定义；但申请声称「在 PRD §6.1 中定义 `timeouts.review_disposition`」不成立——§6.1 无该条目，§13 `macao.yaml` 的 `timeouts` 块（L1434-1439）无 `review_disposition` 配置键 |
| **Grok P1-2**（`SHOULD_DISPOSE` 投影） | **VERIFIED**（附 P2 残留） | PRD §14.2（L1498）= 提案 §6.3（L374）= UC-1（h1 L132 / h2 L152），三处逐列一致。残留：FAQ Q12 表（L253-264）未含该行（见 P2-4） |
| **Qwen P1-1**（处置写者边界） | **VERIFIED**（主路径） | D-2/P-3/§16.1（L1513）/FAQ Q15（L289-312）/UC-5 c（L45-50）/UC-6 边界声明一致；`issues_summary` 双写在 PRD/UC/FAQ 全库零残留。残留：FAQ Q13（L275）「执行者汇总」含糊、UC-1 `adoption.yml` 旧方案（L80/L318）（见 P2-7/P2-8） |
| **Gemini P1-1**（纯整数加权） | **VERIFIED** | D-6 与 PRD §2.3（L355-366）、提案 §7.1/§7.2、UC-5 b（L30-43）三处同构；§7.2 决策表全部 8 行逐行重算正确（含本人上轮 P3-1 建议的 N=2 弃权行与高权+弃权+反对行，已补入）；`policy_snapshot` 已全整数对（本人上轮 P3-2 闭环） |

**核验小结**：8 项声称中 VERIFIED 3、PARTIALLY_VERIFIED 4、CONTRADICTED 1（另 1 项落点失实）。「100% 物理闭环」不成立。

---

## 二、已确认项（VERIFIED，后续修订必须保持）

| # | 声明 | 判定依据 |
|---|---|---|
| V1 | `weighted_2/3_v1` 五重纯整数门禁在 PRD §2.3、提案 §7、UC-5 b 三处同构；§7.2 决策表 8 行（N=2 三行、N=3 2:1:1 四行、1:1:1 timeout 行）逐行整数重算与条文一致 | SIM 复算 |
| V2 | 本轮 10 份交付物内全部 24 个 ```yaml/```json 围栏块经 `yaml.safe_load`/`json.loads` 机解析通过 | SIM |
| V3 | D-3 落地：§2.2 三值票 + 四条 `vote`↔`items` 条件互锁 + `abstain_reason` + 提案 §4.1 的 `source: manifest\|timeout` 区分定义 | DOC |
| V4 | E5a/E6/E7 新转移边与守卫在 §3.3 就位（L795-797），E7 豁免语义（提案 §4.2 第 1/3/4 条）方向正确 | DOC |
| V5 | 本人上轮 P2-3 闭环：提案 §5.4 第 4 条补上单机本地模式退化（跳过 `ls-remote`，本地 ref 存在 + SHA 等价校验） | DOC |
| V6 | 本人上轮 P3-1 闭环：§7.2 补入 N=2 一席弃权行与「胜方最少席位」DEADLOCK 行 | DOC |
| V7 | FAQ Q15 重写与五重门禁、双产物边界逐条一致；SRS 头部映射表（L7-16）申请声称的 5 条兑现 4 条（缺「单一任务 FSM」点名，另有 L5/L7 v2.0/v2.5 版本号混用） | DOC |
| V8 | §1.2 阶段表（L145）已更新为「全席位 accounted」+ disposition 30m 超时列；§2.2 写入约定（L272）明确「严禁直接提交到 source branch」 | DOC |
| V9 | UC-6 主干就位：五枚举、必填布尔（L55）、精确穷尽（L54）、E5a/E5/E6 守卫（L58-62）、A2 豁免路径（L69） | DOC |

---

## 三、P0：BLOCKING（不关闭不得 ACCEPTED）

### P0-1　权威 PRD 的 FSM 三处投影互相否决，无法唯一推出 v2.5 状态机

PRD §3.2 自称「状态识别的唯一规范入口」（L693），但其伪代码与 §3.3 转移表、§3.4 场景推演在三条主轴上互斥：

- **证据 A（E3 触发）**：§3.2 Layer 1b（L725）`if reviews.count_valid >= minimum_quorum(reviews.configured): return AgentState.CONSENSUS_CHECK` —— 仍是「达到 quorum 即转移」；§3.3 E3 行（L789）与 §1.2（L145）要求「所有配置席位 accounted」。超时合成的 ABSTAIN 没有 manifest 文件（提案 §4.1 L113），`count_valid` 只数文件，两个谓词在 N≥3 时产生可观测的不同行为（决策依赖消息到达顺序）。
- **证据 B（APPROVED 处置守卫）**：§3.2 Layer 1c（L736-737）`if result.decision == 'APPROVED': return AgentState.MERGING` —— 无 `requires_disposition` 判断、无 FINAL disposition 守卫、无 E5a 分支；§3.3 E4（L791）/E5a（L795）要求有 issue 时必须 FINAL 覆盖且按 `requires_new_checkpoint` 分流。按伪代码实现会直接绕过 disposition 闭环。
- **证据 C（DEADLOCK 落盘与终局写者）**：§3.2 L735 注释称「终局 decision 枚举包含 APPROVED | REWORK_REQUIRED | RETRY_REVIEW | CANCELLED（Schema 强制）」——无 `DEADLOCK`；而 D-1/§2.3（L366）/E3 行要求即时落盘 `decision: DEADLOCK`。若落盘，Layer 1c 四个分支无一命中、行为未定义；且 §3.4 场景三（L855-863）整体仍是旧方案：步骤 5「**不写 `vote_result.json**」、步骤 6a-6d 由人工裁定「落盘终局 vote_result（resolution: human_override）」、L862 声称「步骤 5 期间没有任何 vote_result.json 处于可被读走状态」——与同文件 E3 行「即时落盘不可变 vote_result.json（decision: DEADLOCK）」互为正反命题。

**推演（1:1 僵局）**：实现者信 E3 行 → 盘上立即有 `decision: DEADLOCK`；信场景三 → 盘上什么都没有；信 Layer 1c → 一旦出现 APPROVED 字样即进 MERGING（无论是否有未处置 BLOCKING issue）。三个合规实现产出三种磁盘状态与三种状态机走向。

**验收（须同时成立）**：
1. §3.2 Layer 1b 改为与 E3 同一谓词（`accounted == configured seats`），删除 `minimum_quorum` 提前返回；
2. §3.2 Layer 1c 补 DEADLOCK 分支（→ HOLD）与 APPROVED 的 disposition 守卫（等 FINAL → E4/E5a），decision 枚举注释与 Schema 对齐；E7 路径只读 `admin_override.json`，不把 RETRY_REVIEW/CANCELLED 写入 `vote_result.decision`；
3. §3.4 场景三步骤 5-6 改写为：即时落盘 DEADLOCK → E7 生成独立 `admin_override.json` → 有 issue 时仍须 FINAL disposition（含 EXEMPTED_BY_ADMIN 项）满足 E4 守卫；
4. 完成后 `grep -n "不写.*vote_result\|有效票 ≥ 法定人数\|minimum_quorum" docs/MACAO_PRD_v2.md` 零命中（历史注明除外）。

---

## 四、P1：进入编码前应修正

### P1-1　D-1 旧语义残留在 UC-7 与机器 Schema，迁移清单未登记

- UC-7（人工接管用例，E7 的消费方）全文未迁移：L6 关联仍写「PRD v2.4」；L44「裁定产生终局 `vote_result.json`（`resolution: human_override`）……DEADLOCK HOLD 期间**不存在**中间版 vote_result」；L80 验收 2 同口径；options 无 `EXTEND`、无 `exempt_issue_ids`。
- `docs/schemas/vote_result.schema.json`：L51 `decision` 枚举仍为 `APPROVED | REWORK_REQUIRED | RETRY_REVIEW | CANCELLED`（无 `DEADLOCK`）；L88-92 仍把 `resolution: human_override` 与人工终局决策绑定回写 vote_result。
- 提案 §9.2 声称「UC-2/UC-3/UC-7～UC-10 全量清理」与 §10.1 的 Schema 变更均未覆盖上述位置。
- **要求**：UC-7 按 D-1 重写（DEADLOCK 即时落盘 + 独立 admin_override.json + EXTEND + 豁免字段）；Schema 随本批迁移或显式标注「待 Phase 1 替换，现版本作废」；§9 增列 UC-7 与 Schema 行。

### P1-2　E3 旧触发口径在四处残留

- §1.1 流程图（L90）「达到法定人数或超时降级流程完成」；
- §16.2 阶段 4（L1543）「有效票 ≥ 法定人数（E3）」；
- UC-5 前置条件 P2（L16）「有效票 ≥ `minimum_quorum`（含超时 ABSTAIN 票）」——与同文件异常流 E2（L74「席位尚未全部 accounted → 不进 CONSENSUS_CHECK」）及决策表（L43「未达法定人数 → DEADLOCK」）自相矛盾：新模型下「全 accounted 但未达 quorum」应计票出 DEADLOCK，而非回到 UC-9 等待；
- §6.1 Reviewer 超时条目（L1078-1082）「ask user: 'Mark as abstain?'」——与 §3.3 超时行（L790）的确定性「记录超时弃权票据（source: timeout），计入 accounted 集合」冲突：一个等人工确认、一个自动持久化。
- **要求**：全体系区分 `responded` / `accounted` / `effective` 三集合（可写入统一术语表），E3 只看 accounted；超时票据由 scanner 确定性生成，删除「询问是否记弃权」。

### P1-3　§14.3/§14.5 与第十五部分被整体删除，≥7 处悬空规范引用，且未登记进 §9 迁移清单

- `git diff 99fe377..0bc6247` 确认：`### 14.3 日志与保留`、`### 14.4 升级与降级`、`### 14.5 Merge Policy（MERGING 状态内的合并流水线）` 与第十五部分全部小节（§15.1 产品边界 / §15.2 返工策略 / §15.3 安全边界 / §15.4 成本计量 / §15.5 评审质量评测计划）被删除，无替代小节新增。
- 悬空引用（现文档无这些章节）：E4 行（L791）与 L1433/L1469/L1483 → §14.5；E5 守卫注释（L740）→ §15.2；L1201/L1246/L1444 → 第十五部分。UC-8 L6 亦引用 §14.5/§15.1。
- 实际损失：合并流水线的权威五步定义（检出 → pre-merge evidence push → merge → CI gate → 人工签字 → push）与返工策略语义失去落点，仅剩 §5.4 两阶段 Seal（L1014-1015）与 §16.2 一行摘要（L1545）两个残片。
- 提案 §9.1 未登记该删除。
- **要求**：恢复或重写 §14.5 Merge Policy 与第十五部分（或将内容显式并入他节并修正全部引用）；§9 补登记删除项及理由。

### P1-4　disposition / override 契约三方发散，NEEDS_ADMIN 与超时触发在权威文档无落位

- **字段三套并存**：提案 §4.3（L149-189）用 `status: FINAL | PENDING_ADMIN`、`items[]`、`decision`、`reason_ref`、`artifact_revision`；UC-6（L32）用 `disposition_status: DRAFT | FINAL`（无 `PENDING_ADMIN`、全文无 `artifact_revision`）；代码清单 §2.1（L64）用 `disposition_status`、`dispositions[]`、`disposition_type`、`rationale`。GUIDELINES 禁止同一实体多套字段名；`DRAFT` 与 `PENDING_ADMIN` 语义不等价（草稿 ≠ 等管理员），E4/E5a 守卫无法据以区分。
- **E4 守卫第三条款漂移**：「且无未豁免的 BLOCKING」只见于 UC-6（L58）与清单 §2.3，不见于 PRD §3.3 E4 行与提案 §4.5——同一条守卫两个版本。
- **NEEDS_ADMIN 闭环仍未结构化**（本人上轮 P1-3 的核心要求未兑现）：管理员的 issue 级应答以什么字段回传（映射到哪个 decision、`requires_new_checkpoint` 谁定）在 Type G payload（L639-644，仅 `trigger/context/options/deadline`）、`admin_override` Schema（清单 §2.1，任务级单 `decision`）与 UC-6 中均无定义；§6.1 触发器列表无 NEEDS_ADMIN 与 disposition 超时条目；§13 `macao.yaml` `timeouts` 块（L1434-1439）无 `review_disposition` 键（提案 §10.1 第 1 条声称已列入）。
- **写者边界自相矛盾**：提案 §4.2 第 1 条要求 Executor 产出 FINAL disposition，第 2 条又允许「管理员一并签署替代 FINAL disposition」——与 D-2/P-3/§16.1 的 Executor 单一写者冲突，且未定义替代产物的 Schema 与 E4 守卫校验对象。
- **`admin_override.json` 未登记**：提案 §5.1 权威产物表（L297-306）、PRD §3.4 生命周期表（L813-818）、§16.1 写者垄断表（L1512-1514）均无该产物——新 v2.5 产物没有写者/生命周期/权威位置注册。
- **要求**：裁定唯一信封字段集并写入 PRD §2.x，UC-6/清单/Schema 逐字段同名；固化 NEEDS_ADMIN 的 issue 级应答 Schema 与 revision 链；§6.1 与 §13 补齐触发器与超时键；裁定「管理员代签」是否合法及其产物形态；`admin_override.json` 入三张表。

### P1-5　`docs/schemas/` 机器契约未迁移，与 PRD §13「唯一校验依据」声明直接冲突

- PRD §13（L1454）声明三类产物与 AEP 信封「以 `docs/schemas/` 的版本化 Schema 为唯一校验依据」；申请 §4.1 声称「契约字段在 PRD、SRS、FAQ、UC 及 Schema 设计间实现 100% 命名与语义对齐」。
- 实际：`vote_result.schema.json` 为旧契约（见 P1-1）；`review_manifest.schema.json` 无三值票/`items`/`abstain_reason`/条件互锁；`macao_config.schema.json` 无 `vote_weight`/独裁帽/disposition 超时；`review_disposition.schema.json` 与 `admin_override.schema.json` 不存在；AEP Schema 仍为 1.0 七类。按现行 Schema 编码则不会实现 v2.5；按 PRD 编码则产物被「唯一校验依据」拒绝。
- **要求**：Schema 纳入本批迁移（可为「待实现」标注但字段契约必须唯一），或 PRD/申请显式声明现行 Schema 整体作废的时点与顺序；禁止两套互斥机器契约并存于实施基线。

### P1-6　E4a 硬校验与 `no_ff` 合并策略互斥

- E4a（L792）与清单 §2.4 要求「最终 push 对象 == `vote_result.checkpoint_ref` 硬校验」；§13（L1430）却允许 `merge.strategy: ff_only | no_ff`。`no_ff` 必然产生新 merge commit，目标 tip 按定义不可能等于被评审 checkpoint——该配置下 E4a 永不通过。
- **要求**：对 `ff_only` / `no_ff` 分别定义 source checkpoint、merge commit、remote tip 的校验关系（如 no_ff 下校验 merge commit 的第二父或 tree 等价），或 v2.5 禁用 `no_ff`。

### P1-7　`review_context` 存在两套互斥的权威字段路径

- §2.4 Type B 注（L513-517）声明 `code_changes.refs.{base_commit, head_commit}` 嵌套结构是「唯一权威路径……不允许扁平写法」，且要求与 §5.2 完全一致；§5.2 示例（L980-983）却使用扁平 `code_changes.base_commit / head_commit`。两处同称权威、结构互斥，Reviewer 取 diff 的字段路径不确定。
- **要求**：只保留一套 canonical 模型，统一 §2.4/§5.2/消费命令/Schema/fixtures，并明确 9 个语义块的 required/optional 划分。

### P1-8　代码变更清单不能作为实施准入图

- 清单目标路径与仓库实际模块树不符且未标「新建」：`src/macao/workflow/state.py`、`workflow/override.py` 不存在（实为 `fsm.py`/`state_engine.py`/`transitions.py`/`orchestrator.py`）；无 `src/macao/git/` 包（合并逻辑在 `src/macao/merge/`）；`cli/commands/` 包不存在。
- 清单 §2.1 的 disposition Schema 字段名同 P1-4 发散；`vote_result.schema.json` 的「重构」未把「`decision` 枚举删除 RETRY_REVIEW/CANCELLED、新增 DEADLOCK」列为破坏性迁移项。
- 清单亦未覆盖 P0-1（§3.2 伪代码/§3.4 场景）、P1-1（UC-7）、P1-3（§14.5/§15 恢复）所需的文档修复动作——若按清单施工，这些矛盾会被带进代码。
- **要求**：每行指向现存文件或显式标「新建」；字段名与唯一信封一致；补破坏性变更说明与文档修复项。

### P1-9　STATUS.md 票型登记错误，申请治理不合规

- STATUS L66 写「Gemini & Grok 批准实施」——`2026-09-01-review-2.5-2-grok.md` 机器票为 `NO_APPROVE`（BLOCKING×2），登记与原文相反；同行把本人上轮 `NO_APPROVE`（P0×1+P1×3）淡化为「提出加固项」。
- STATUS L65 初审轮登记同样失真：GLM 实为 NOT-ACCEPTED（P0×1+P1×2）、Grok 为 NO_APPROVE，均未登记为否决；Qwen 实际已对 v0.2 稿授予 L1，亦未如实登记。
- STATUS L66「所有专家关切已在 PRD v2.5 正式版中 100% 物理闭环」与本评审第一节核验结果（VERIFIED 3/8）及两份 `0bc6247` 评审（codex、grok 均 NO）直接冲突；该两份评审尚未纳入 STATUS 对账。
- 申请 §2 以可移动的 `origin/main` 指代被审基线，未冻结短 SHA，后续审计无法仅凭申请复现评审对象。
- **要求**：更正 L65/L66 票型与结论；登记全部 2026-09-01 评审（含两份 0bc6247 NO 票与本份）；申请与 STATUS 对被审对象一律使用冻结 commit SHA。

---

## 五、P2：可延期，须登记

| ID | 问题 |
|---|---|
| P2-1 | AEP 节内不一致：L372 称 8 类消息，L390 称「全部 7 个消息类型」；Type A～G 无 `DISPOSITION_REQUIRED` 信封规格（v2.5 调度主通道只在表头出现）；E3 行（L789）把 `HUMAN_OVERRIDE_REQUEST` 误写为「Type H」（§2.4/§3.2/§3.4 均为 Type G）；全部示例 `protocol: "AEP/1.0"`（如 L631）与「AEP v1.1」标题冲突；Type G `options`（L642）缺 `EXTEND`，与 E7 五选项不一致。 |
| P2-2 | E7 行落边记法「APPROVED→E4」与 E4 行源状态仅 `CONSENSUS_CHECK` 不符：从 `REWORK` 覆盖时物理边是 `REWORK→MERGING`，表中未单列（提案 §4.2 第 3 条的文字描述是正确的，PRD 表记法需对齐）；提案 §4.5 E5 行守卫漏写 `round < max_rework_rounds`（PRD L794 有），提案与 PRD 条文漂移。 |
| P2-3 | HOLD 拟态未定义：L803 声明业务状态共 10 个且不含 HOLD，但 L1480 `macao pause`「进入 HOLD」、E7 源状态「HOLD（CONSENSUS_CHECK 或 REWORK）」均以 HOLD 为规范概念；State Store DDL（§11.4）无 paused/hold 字段。应定义为持久化标志/子状态并补 DDL，或禁止「进入 HOLD」作为状态措辞。 |
| P2-4 | 本人上轮 P2-4 未闭环：PRD §14.2 与提案 §6.3 的 role_view 表未固化 UC-1（L158）的 `artifact_status` 注记（`STALE` 不得显示为 `REVIEW_SUBMITTED`）；UC-1 h1 表（L130）缺 `WAITING_REVIEW（席位已提交有效产物）→ AWAIT_REMAINING_OR_TIMEOUT` 行；FAQ Q12 表（L253-264）为旧简表，无 SHOULD_DISPOSE 行——「唯一 role_view 表」声称被第三份词汇表削弱。 |
| P2-5 | PRD §4.1 MVP 范围未随 v2.5 更新：「不做 (P1+)」仍列「Multi-Reviewer Consensus 高级算法（2/3 投票先用）」（L886 附近），与加权五重门禁已成为实施基线矛盾；P0 清单未列 `review_disposition`、Evidence Ref、E7 override 等 v2.5 必做项。 |
| P2-6 | §16.4（跨机 v1.1 规划）残留「M1 落盘并 git 提交留证」（C3 行）、δ2「git 是存证」、δ3「M1 落盘提交」，未注明证据目标是 evidence ref 还是 source；§9.1 声称 §16.4 已「全面删除」该类表述，与实际不符。另：§9.1 引用的是旧文档行号（L416/L833 等），在新文档无法对账，建议改为节号引用。 |
| P2-7 | FAQ 同步未兑现一半：Q14（L284-285）/Q16（L319）仍只说 `docs/reviews/`，全文无 `refs/macao/evidence` 表述（申请 §3/提案 §9.2 声称已更新 Evidence Ref）；L116/L120 超时 ABSTAIN 未同步 `source: manifest\|timeout` 区分（本人上轮 P2-2 点名项）；Q13（L275）「执行者汇总问题清单、正文索引」与 Orchestrator 写 `issues_index` 的边界含糊。 |
| P2-8 | UC 文档版本与旧方案残留：UC-5 L6 关联「PRD v2.4」、§7 实现落点表 L97-100 重复两行；UC-1 L5 引用 v2.4、L80/L318 保留 `adoption.yml` 采纳清单旧方案（与 D-2 唯一 disposition 并存）、L242-246 与 L296-297 使用第二套 `next_action` 词汇（`WAIT_OR_NOTIFY_EXECUTOR` 等，与 h1/PRD 枚举不一致）；UC-8 L39「本轮全部产物……随 git 提交」、UC-9 L36「弃权随终局 vote_result 落盘」均为旧口径（两者关联行仍标 PRD v2.4）。 |
| P2-9 | PRODUCT-FACTS F-20（L47）仍为「待定」措辞，全集无 `ACCEPTED-FOR-V2.5-SPEC` 标记（提案 §9.2 声称已解析并标记，未兑现）；F-7（L21）「人可读语义证据必须在 docs/reviews/ 留下 Git 可追溯记录」与 evidence ref 方案的 git 归属需显式裁定。 |

## 六、P3：备查

| ID | 问题 |
|---|---|
| P3-1 | 结构机械残留：§5 内 5.2→5.4→5.3 乱序（L1007/L1020）；第十四部分后直跳第十六部分（十五已被删除，编号未收敛）；「附录：版本演进记录」（L1520）插在第十六部分内部。 |
| P3-2 | 示例时间戳混用 2024-01-15（§2.4 Type A～G）与 2026-09-01；不影响语义。 |
| P3-3 | 提案 §7.1 配置示例仍用字符串比率（`seat_quorum_ratio: "2/3"` 等）；`policy_snapshot` 已整数对化，配置侧建议统一整数对或注明解析规则。 |
| P3-4 | §16.2 阶段 5（L1544）「APPROVED / REWORK / Deadlock 转人工」未提 disposition/E5a 分流，摘要级表述建议补齐。 |

---

## 七、建议闭环顺序与验收标准

1. **先修 P0-1**（§3.2 伪代码 + §3.4 场景三 + E3 谓词三处同构），再修 P1-1/P1-2——这是同一组残留的不同切面。验收：手工推演「1:1 僵局」「APPROVED+ADVISORY 未处置」「REWORK 中 E7 豁免放行」三条路径，每步只能命中 §3.3 一行；全文检索不再出现作为现行规范的「DEADLOCK 不写 vote_result」「达到/有效票 ≥ 法定人数即 E3」。
2. **恢复或重写 §14.5 与第十五部分**（P1-3），消除全部悬空引用；§9 迁移清单补登记删除项，行号引用改为节号。
3. **裁定唯一 disposition/admin_override 信封**（P1-4）并回写 PRD §2.x、UC-6、清单、Schema；补齐 §6.1 触发器与 §13 `timeouts.review_disposition`；NEEDS_ADMIN issue 级应答字段化。
4. **迁移 `docs/schemas/`**（P1-5）或将现行 Schema 显式作废登记；把 PRD/UC 的每个规范示例作为 fixture 过对应 Schema。
5. **裁定 merge OID 关系**（P1-6）与 `review_context` 唯一模型（P1-7）。
6. **清单对齐仓库模块树**（P1-8）；**更正 STATUS 并冻结评审对象 SHA**（P1-9）。
7. P2/P3 随修订批处理，重点：AEP 第八类消息信封与版本号（P2-1）、HOLD 定义（P2-3）、FAQ/UC 残留（P2-4/P2-7/P2-8）、F-20 结案（P2-9）。
8. 以上闭合后以冻结 commit 重新申请 L1 DOC-ALIGNED / PG-0。

## 八、Reviewer 自审

- 本评审所有引用行号均在 `0bc6247` 工作树上逐一核对（含 `git diff 99fe377..0bc6247` 全量比对与 `git show 99fe377` 旧版对照）；整数决策表 8 行与示例为条文手算（SIM）；24 个 YAML/JSON 块机解析为本地只读校验。
- 与本轮 codex（`2026-09-01-review-result-0bc6247-codex.md`）、grok（`2026-09-01-review-result-0bc6247-grok.md`）的结论独立形成后比对：三方在 DEADLOCK 残留、E3 旧口径、§14.5/§15 悬空、disposition 契约发散、Schema 未迁移、清单路径不符、STATUS 误登记上结论一致；本评审未采纳任何未经自行核实的他方引用（UC-7/UC-8/UC-9、Schema 枚举、模块树、review_context 双路径均已自行复核原文）。
- 未评审对象：实现代码行为（清单为待实施计划，CODE/TEST 为 NOT_APPLICABLE）；`docs/schemas/` 仅核对枚举与字段存在性，未做全量 fixture 校验（codex 已做 10 错误级验证，结论可互证）。
- 机器票：`NO_APPROVE`；`BLOCKING` × 10（P0-1，P1-1～P1-9）；`ADVISORY` × 13（P2-1～P2-9，P3-1～P3-4）。
