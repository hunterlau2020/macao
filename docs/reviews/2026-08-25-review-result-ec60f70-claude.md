# MACAO 文档对齐评审结论（Claude 独立评审）

- 评审日期：2026-08-25
- 评审 commit：`ec60f70`（"对齐文档"，当前 `main` HEAD）
- 评审范围：`EXECUTIVE_SUMMARY.md`、`IMPROVEMENT_SUMMARY.md`、`MACAO_PRD_v2.md`、`SRSv1.md`
- 对齐基准：`MACAO_PRD_v2.md`（文档开头已明确自身为 v2.0 权威基准；`SRSv1.md` 为历史基线，不作为实现依据）
- 评审方法：本次评审依据本仓库新引入的 `docs/MACAO_REVIEW_GUIDELINES.md`（改编自第三方 `docs/REVIEW_METHODOLOGY.md`），逐条给出文件路径+行号证据，而非仅凭整体印象判断"是否一致"
- 参考对照：本仓库已有 `docs/reviews/2026-08-25-review-result-ec60f70-codex.md`、`docs/reviews/2026-08-25-review-result-ec60f70-gemini.md`（同一 commit 的另外两份独立评审）。本次评审为**独立通读四份文档后**给出的结论，随后与这两份文档做了交叉核对，详见文末"与既有评审的交叉核对"一节
- 结论（对照 `MACAO_REVIEW_GUIDELINES.md` §2.1）：**未达到 L1 DOC-ALIGNED / PG-0 与 PG-1 之间**。四份文档在产品定位、MVP 收敛方向、文档层级与三类核心产物的角色上已经一致；但状态识别、投票法定人数、Reviewer Context 载体、术语字段命名仍存在**互相矛盾**、无法从文档唯一推导实现行为的 P0 级问题，不建议在这些问题闭环前直接进入编码。

---

## 已对齐 / 已确认项

| 主题 | 证据 | 结论 |
|---|---|---|
| 文档层级声明 | `MACAO_PRD_v2.md:5,7-14`；`EXECUTIVE_SUMMARY.md:3-5`；`IMPROVEMENT_SUMMARY.md:5`；`SRSv1.md:3-15` | 四份文档均明确指向 PRD v2.0 为权威基准，SRS 为历史基线，一致 |
| MVP 范围与角色 | `MACAO_PRD_v2.md:21,644-657`；`EXECUTIVE_SUMMARY.md:59,234-256`；`IMPROVEMENT_SUMMARY.md:316-322` | 均收敛为本地单机、Claude Code（Executor）+ Codex/Kimi（Reviewer），远程 SSH/调度/Dashboard 延后，一致 |
| 主流程骨架 | `MACAO_PRD_v2.md:39-113`；`EXECUTIVE_SUMMARY.md:94-108`；`IMPROVEMENT_SUMMARY.md:39-46` | 开发检查点 → 评审请求 → Reviewer 意见 → 共识 → 合并/返工，四份文档主干一致 |
| 两 Reviewer 场景下 2/3 规则的解释 | `EXECUTIVE_SUMMARY.md:348` | 已补充"MVP 为 2 Reviewer 时需全票赞成，1:1 触发人工裁定"，与 PRD §2.3（`MACAO_PRD_v2.md:358-364`）一致；这是本次评审中确认**已经修复**的一处历史问题 |
| SRS 文档级历史标注 | `SRSv1.md:3-15` | 开头的 v1→v2 对照表清楚、准确，是四份文档中做得最完整的部分 |

---

## P0：必须先解决

### P0-1　状态识别：正文规则、伪代码、字段路径三者互相矛盾

**证据**：

- `MACAO_PRD_v2.md:548-554`（Layer 2 定义）："仅作辅助诊断" "不改变实际状态，仅用于日志"；
- 但 `MACAO_PRD_v2.md:598-621`（`recognize_agent_state` 伪代码）在没有 `.dev.yml`（`dev_checkpoint` 为空）时，函数末尾 `return dev_checkpoint.state if dev_checkpoint else inferred_state`（`MACAO_PRD_v2.md:621`）——**直接把 Layer 2 的推断结果作为函数返回值**，与"不改变实际状态"的正文承诺矛盾；
- 同一伪代码只读取 `.dev.yml`（`MACAO_PRD_v2.md:577`），未覆盖 §3.1/§3.3 中同样属于 Layer 1 显式信号的 `.review.yml`、`vote_result.json`（`MACAO_PRD_v2.md:542-544,628-634`）；
- `check_explicit_signal` 示例（`MACAO_PRD_v2.md:201-211`）从 `manifest['quality_metrics']['tests_passed']`、`manifest['git']['latest_commit']` 读取字段，但 `.dev.yml` 的 Schema 示例（`MACAO_PRD_v2.md:164-186`）中 `quality_metrics` 与 `git` 实际嵌套在 `development` 键之下，即正确路径应为 `manifest['development']['quality_metrics']...`。按文档给出的伪代码实现，该校验函数会因 `KeyError` 或恒为 `None` 而永远无法命中显式信号分支。

**影响**：不同实现者会分别选择"无显式信号时等待人工接管" "无显式信号时直接按推断结果继续" "校验函数报错退出" 三种互不相同的行为；`.review.yml`/`vote_result.json` 两类显式产物在状态识别入口完全未被处理。这与文档反复强调的"显式信号优先、Layer 2 仅辅助"的核心承诺直接冲突。

**建议**：在 PRD 中给出唯一的规范状态机（而不是并列一段文字描述 + 一段与文字矛盾的伪代码），明确三类显式产物各自的字段路径、校验规则与转移目标；伪代码字段路径需与 §2.1 的 Schema 逐字段一致，建议加自动化 Schema 校验或 doctest 保证二者不再漂移。

### P0-2　投票法定人数与"全部/多数 Reviewer 返回"的出口条件矛盾

**证据**：

- `MACAO_PRD_v2.md:360-364`（§2.3 共识规则）：明确"弃权不计入分母"，并说明 MVP 2 Reviewer 配置下 2/3 规则等价于"全票赞成"，1:1 触发人工裁定；
- 但阶段定义表 `MACAO_PRD_v2.md:117-125` 中 `REVIEW_REQUEST` 阶段的出口条件写的是"Reviewer 全部返回意见"（第 122 行），状态转换表 `MACAO_PRD_v2.md:631` 同样写"所有 Reviewer 返回 `.review.yml`"；
- 而降级策略 `MACAO_PRD_v2.md:861-863`（§6.2）描述"1 Reviewer unavailable → (2/3 Reviewers) → Consensus → Merge"，字面意思是**允许在未获得全部 Reviewer 响应的情况下继续**，与前两处"全部返回"矛盾；且该描述本身还隐含了一个从未在 MVP 范围声明过的"3 Reviewer 基数"（2 Reviewer 配置下不可能出现"2/3 Reviewers 继续"这种说法，因为总数本身就是 2）；
- `EXECUTIVE_SUMMARY.md:404-410` 补充了"Reviewer 超时可标记为弃权"，但未说明弃权后剩余的唯一一票能否单独决定 `APPROVED`/`REWORK`，与 PRD §2.3 的"有效票分母"公式如何交互也未给出。

**影响**：2 Reviewer 的 MVP 配置下，"一人超时 → 标记弃权 → 剩余 1 票是否可单方面通过或打回"是一个高频真实场景，但当前文档给不出唯一答案；"全部返回"与"2/3 继续"两种出口条件会导致不同实现在同一场景下走向不同状态。

**建议**：在 PRD §2.3 增加显式决策表，覆盖 `configured_reviewers ∈ {2,3}` × `{responded, abstain, timeout}` 的组合（至少含：2 人全同意、2 人 1:1、2 人 1 弃权+1 票、2 人全弃权、3 人 1:1:1、3 人 1 超时）；同时把 §1.2/§3.3 中的"全部返回"改为"达到法定人数判定条件或超时降级流程完成"，并让 §6.2 的措辞与 MVP 实际 Reviewer 基数一致。

### P0-3　Reviewer Context 的代码变更载体在文档间三种说法并存

**证据**：

- `MACAO_PRD_v2.md:437`（AEP `REVIEW_REQUEST` payload）：`"diff": "git diff a1b2c3d^..a1b2c3d"` —— 值是一条 shell 命令字符串，不是 diff 内容本身；
- `MACAO_PRD_v2.md:723`（§5.2 详细 Context）：`detailed_diff: "git diff a1b2c3d^..a1b2c3d"  # 完整 diff` —— 同样是命令字符串，但注释写"完整 diff"，自相矛盾；
- `MACAO_PRD_v2.md:783-787`（§5.3 Reviewer 标准工作流）：`git apply /tmp/code_changes.patch` —— 要求 Reviewer 从一个文档中从未定义来源的本地文件 `/tmp/code_changes.patch` 读取并 `git apply`，与前两处的"命令字符串"/"diff 值"完全对不上，也没有说明该文件由谁、何时写入 `/tmp`；
- `IMPROVEMENT_SUMMARY.md:156,176`：分别描述为"code_changes（完整 diff）"和 `diff: "<完整的 git diff>"`，延续了"内容已经内联"的印象，进一步加深了与 PRD 实际给出的"命令字符串"示例的落差。

**影响**：实现者无法确定 AEP 消息里 `code_changes` 字段承载的到底是 diff 文本、shell 命令、还是文件路径；三个文档在这一点上给出的心智模型互不相同，会导致 Reviewer Adapter 和 MACAO 消息序列化两端各自实现出不兼容的接口。

**建议**：在 PRD 中二选一并写清楚：(a) 传输 `base_commit`/`head_commit`（或仓库 URI + ref），Reviewer 侧自行 `git diff`/`checkout`；(b) 传输 patch 内容本身（需说明编码、大小上限与截断策略）。选定后，`.dev.yml`、AEP payload 示例、§5.3 工作流、`IMPROVEMENT_SUMMARY.md` 的措辞需同步修订为同一种载体。

### P0-4　同一概念在四份文档中出现三个不同字段名（`checkpoint_ref` / `checkpoint_id` / `checkpoint`）

**证据**：

- `MACAO_PRD_v2.md:233`（`.review.yml`）与 `MACAO_PRD_v2.md:304`（`vote_result.json`）：字段名均为 `checkpoint_ref`；
- 但同一份 PRD 的 AEP 消息示例中，`MACAO_PRD_v2.md:427`（Type B）、`MACAO_PRD_v2.md:481`（Type C）、`MACAO_PRD_v2.md:511`（Type D）三处全部使用 `checkpoint_id`——即 **PRD 自身内部**已经在"产物文件字段"与"AEP 消息字段"之间使用了两个不同名字，且全文没有一处说明这是有意的分层命名还是笔误；
- `EXECUTIVE_SUMMARY.md:175` 的 `vote_result.json` 示例又用了第三个变体 `"checkpoint": "a1b2c3d"`，与 PRD 权威 Schema（`checkpoint_ref`）不一致。

**影响**：Schema 校验、消息路由和产物解析三处如果分别参照不同示例实现，会立刻出现字段找不到的问题；这类"一个概念三个名字"的漂移具体、低成本即可发现，但目前尚未在任何文档中被显式统一。

**建议**：在 `docs/MACAO_REVIEW_GUIDELINES.md` §5 建议的"产物-生成者-路径-字段"唯一对照表中固定一个名字（建议统一用 `checkpoint_ref`，因为它已经是产物 Schema 里的既有用法），批量修订 AEP 示例与执行摘要示例。

---

## P1：进入下一阶段前应修正

| 编号 | 发现 | 证据 | 建议 |
|---|---|---|---|
| P1-1 | AEP 声称 7 类消息，但仅给出 1–4 的详细格式；`IMPROVEMENT_SUMMARY.md` 却称"补充 AEP Message **完整格式**" | `MACAO_PRD_v2.md:370-382`；`IMPROVEMENT_SUMMARY.md:231` | 要么补齐 5–7 类的最小 payload 示例，要么把"完整格式"改为"核心 4 类详细格式，5–7 类遵循统一信封" |
| P1-2 | AEP 信封中 `to` / `to_agent` / `to_agents` 三种路由字段并存，未定义何时用哪个 | `MACAO_PRD_v2.md:394,422,477` | 统一为信封级固定字段（如 `to: string \| string[]`），或在每种消息类型下明确声明该用哪个字段 |
| P1-3 | JSON 示例中混入 `#` 注释，不是合法 JSON | `MACAO_PRD_v2.md:429`（`# 核心 Context 包：...`） | 移出注释或改用 JSON5/带注释说明的 fenced block 并标注"非可执行示意" |
| P1-4 | `opinion.status`（APPROVED/CHANGES_REQUESTED/REJECTED）与 `vote`（YES_APPROVE/NO_APPROVE/ABSTAIN）是两套独立枚举，未定义映射关系或冲突校验规则 | `MACAO_PRD_v2.md:237,286` | 规定二者一一映射表，或只保留一个权威字段，另一个由系统派生 |
| P1-5 | PRD P0 交付清单全部勾选 `[x]`，但 §4.2 与"立即行动项"仍是尚未开始的未来计划；`EXECUTIVE_SUMMARY.md` 同一批条目又写成 `[ ]` | `MACAO_PRD_v2.md:644-651`（`[x]`）vs `MACAO_PRD_v2.md:955-959`；`EXECUTIVE_SUMMARY.md:236-246`（`[ ]`） | 统一改为 `[ ]`/"P0 scope（计划内）"，除非能给出对应交付证据；两份文档的勾选状态需一致 |
| P1-6 | "State Recognition Accuracy >95%" 的测量方式写成"自动化测试覆盖"，覆盖率≠准确率；确定性数字（99%/100%）与目标区间（>95%/>99%）混用 | `MACAO_PRD_v2.md:912-913`；`EXECUTIVE_SUMMARY.md:26,57,110`；`IMPROVEMENT_SUMMARY.md:16,219,434` | 分别定义准确率的样本集、分母、观察窗口；摘要类文档中的确定性断言统一改为"设计目标，待 PoC 验证" |
| P1-7 | `SRSv1.md` 正文（约 1100 行）除文档头部的对照表外，全文没有任何"历史内容/不得用于实现"的行内提示，读者跳读正文时容易直接采信 v1 术语（如 `TASK_ASSIGN`、4 CLI、远程 Agent 架构） | `SRSv1.md:3-15`（仅头部有提示）；全文 grep 未见其他历史标注 | 在每个与 v2.0 冲突的小节（AEP 消息命名、CLI 数量、Agent 架构图等）补充醒目提示并链接回 PRD 对应章节 |

## P2：可延期但需登记

| 编号 | 发现 | 证据 | 说明 |
|---|---|---|---|
| P2-1 | PRD（权威基准文档）AEP 示例中的项目名写死为 `"project": "washdb"`，`washdb` 是与 MACAO 无关的另一项目名（同名的第三方评审方法论 `docs/REVIEW_METHODOLOGY.md` 正是描述该项目），自 v1.0 起沿用至今 | `MACAO_PRD_v2.md:397,425,480,510`；`SRSv1.md:179,182,189,860` | 不影响协议本身正确性，但作为"权威基准"文档里的示例，容易让读者误以为 MACAO 与 washdb 项目存在耦合关系；建议替换为通用占位符（如 `"project": "<project_name>"`）或 MACAO 自身的示例项目名 |
| P2-2 | `.macao/.reviews/<reviewer_id>.review.yml` 路径未按 checkpoint/round 区分，第二轮返工时会覆盖第一轮文件；"可 git log 审计"的前提（是否原子提交、何时提交）未定义 | `MACAO_PRD_v2.md:219`；`IMPROVEMENT_SUMMARY.md:58-62` | 若能保证每次写入后立即原子提交，覆盖式路径仍可通过 git 历史审计；但目前文档未对提交时机做任何承诺，建议在实现前明确，或改为按 round 建目录 |

---

## 交叉文档需做的文字修订

1. `IMPROVEMENT_SUMMARY.md:22` "单机+单 Reviewer 先行"应标注为 Week 1–2 PoC 阶段的范围，不是 MVP 最终配置——同文件 `IMPROVEMENT_SUMMARY.md:218` 与 PRD 一致写的是 Codex/Kimi 两个 Reviewer，两处并列容易让读者误解 MVP 到底是 1 个还是 2 个 Reviewer。
2. `EXECUTIVE_SUMMARY.md:21-24` "所有 CLI 必须生成三类 `.yml` 文件"应改为"三类标准产物（两类 YAML manifest 由 CLI 生成 + 一份 JSON 共识记录由 MACAO 生成）"，`vote_result.json` 示例字段按 P0-4 建议改为 `checkpoint_ref`。
3. 三份 v2 文档中"100% 可信" "99%+ 由显式信号驱动" 等结果性用语，除非能补充测量定义与实证来源，否则统一改为"设计目标/待 PoC 验证"。
4. `SRSv1.md` 保持作为历史基线本身没有问题，但按 P1-7 建议补充正文内的历史提示。

---

## 建议的闭环顺序与验收标准

1. 先在 PRD 内部解决 P0-1～P0-4（状态机唯一化、投票法定人数决策表、Context 载体二选一、字段命名统一），这四项都是"同一份权威文档自相矛盾"，优先级高于摘要类文档的回填。
2. 用 §P0-1 中提到的 Schema 逐字段核对 `.dev.yml`/`.review.yml`/`vote_result.json`/7 类 AEP 消息，建议产出可执行的 JSON Schema/YAML Schema 文件并加入 CI 校验，避免未来再次出现字段名漂移。
3. 回填 `EXECUTIVE_SUMMARY.md`、`IMPROVEMENT_SUMMARY.md` 中与 PRD 不一致的示例与勾选状态；`SRSv1.md` 只需补历史提示，不改写史实。
4. 验收标准（对照 `MACAO_REVIEW_GUIDELINES.md` §6 反例库）：全同意、1:1 僵局、1 人超时+1 弃权、全弃权、返工第二轮覆盖同名文件、进程崩溃重启后重复投票 —— 以上每个场景都必须能从文档唯一推出状态、责任人、产物路径与是否触发人工接管，且四份文档对该结论的描述互不矛盾。

在 P0 项全部闭环前，不建议把四份文档作为可直接开发的完整规格（对照 `MACAO_REVIEW_GUIDELINES.md` §2.2，当前处于 PG-0 允许 PoC，但未达 PG-1）。

---

## 与既有评审的交叉核对

本次评审在完成独立通读后，与 `docs/reviews/2026-08-25-review-result-ec60f70-codex.md`、`docs/reviews/2026-08-25-review-result-ec60f70-gemini.md` 两份同 commit 的独立评审做了交叉核对：

### 与 codex 评审

- **一致的核心发现**：两份评审独立命中了同一组 P0 问题——状态识别正文与伪代码矛盾（对应本报告 P0-1）、投票法定人数与"全部返回"出口条件矛盾（P0-2）、Reviewer Context 的 diff 载体三种说法并存（P0-3）、以及产物/术语命名漂移（P0-4，两份评审都指出了 `checkpoint` vs `checkpoint_ref` 的漂移；本报告额外确认了 PRD 内部 `checkpoint_ref`/`checkpoint_id` 两种命名并存）。两份评审在证据（具体行号）上相互印证，未发现事实性分歧。
- **本报告的增量发现**：P2-1（PRD 权威示例中残留 `washdb` 项目名）为本次独立评审新增，`codex` 评审未提及；此外 P0-4 中"PRD 内部 `checkpoint_ref` vs `checkpoint_id` 并存"这一层细化也是本报告独立补充的证据。
- **未发现需要推翻的结论**：未在 `codex` 评审中找到与本次通读结果相矛盾之处；两份评审可视为同一组 P0 问题的独立复现，增强了这些发现的可信度（对照 `MACAO_REVIEW_GUIDELINES.md` §8 "真理不等于投票"——本次是通过独立重新验证证据，而非直接采信另一份评审的结论）。

### 与 gemini 评审

`gemini` 评审的总体结论是"文档体系整体对齐良好"（各文档对评级 ⭐⭐⭐⭐/⭐⭐⭐⭐⭐），与本报告和 `codex` 报告的"未达 L1 DOC-ALIGNED，存在 P0 级冲突"结论**明显不同**。核对后判断：

- **gemini 找到的问题真实存在，但均为"摘要文档遗漏权威文档细节"类的完整性问题**，例如：`IMPROVEMENT_SUMMARY.md` 中 `.review.yml` 路径缺少 `.macao/` 前缀（其发现 D，经核对 `IMPROVEMENT_SUMMARY.md:53` 确实写的是 `.reviews/<reviewer_id>.review.yml`，与 PRD `MACAO_PRD_v2.md:219` 的 `.macao/.reviews/<reviewer_id>.review.yml` 不符，本报告与 `codex` 报告均未发现此项，予以采纳）；`EXECUTIVE_SUMMARY.md` 风险表缺少"Git Conflict"风险项（其发现 O，经核对属实）。这类问题本报告认可为有效的 **P2 级**补充发现。
- **gemini 评审未发现本报告与 `codex` 报告共同命中的四项 P0**（状态机伪代码自相矛盾、投票法定人数与"全部返回"矛盾、diff 载体三种说法并存、字段命名多处漂移）。原因推测：gemini 的评审方法以"逐主题跨文档对照摘要与 PRD 的表述是否一致"为主，没有深入检查 PRD **自身内部**（正文 vs 伪代码 vs 示例代码块）的一致性——而本报告与 codex 报告命中的 P0 恰恰都是 PRD 内部的自相矛盾，不是摘要文档对 PRD 的转述失真。
- **结论**：gemini 报告的具体发现（D、O 等）是有效的增量证据，已并入本报告的"P2：可延期但需登记"与"交叉文档需做的文字修订"；但其"整体对齐良好"的总体评级**不能反映 PRD 自身状态机/投票/Context 协议存在的 P0 级自相矛盾**，本报告维持"未达 L1 DOC-ALIGNED"的结论，不采纳 gemini 报告的总体评级。三份评审的分歧点本身也印证了 `MACAO_REVIEW_GUIDELINES.md` §8 的原则——评审结论应以可复现证据取胜，而非以评审数量或評分取多数。

### 综合后新增的 P2 发现（源自 gemini 报告核实）

| 编号 | 发现 | 证据 |
|---|---|---|
| P2-3 | `IMPROVEMENT_SUMMARY.md` 中 `.review.yml` 路径缺少 `.macao/` 前缀 | `IMPROVEMENT_SUMMARY.md:53` vs `MACAO_PRD_v2.md:219` |
| P2-4 | `EXECUTIVE_SUMMARY.md` 风险表缺少 PRD §9.1 的"Git Conflict 导致卡死"风险项 | `EXECUTIVE_SUMMARY.md:363-368` vs `MACAO_PRD_v2.md:935-941` |

---

## Reviewer 自审记录

按 `MACAO_REVIEW_GUIDELINES.md` §9 自检 checklist：本次评审为首次对该 commit 独立评审，暂无"连续漏审"记录需要登记。后续若在同一类盲点（字段路径/勾选状态/确定性用语/示例可解析性）上再次漏审，应在下一份评审文件的本节登记具体案例。
